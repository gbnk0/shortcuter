import asyncio
import hashlib
import logging
import mimetypes
import os
import re
from contextlib import asynccontextmanager
from pathlib import Path
from html.parser import HTMLParser
from time import time
from typing import Literal
from urllib.parse import urljoin, urlparse

import httpx
import yaml
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ValidationError, field_validator


BASE_DIR = Path(__file__).resolve().parent.parent
SHORTCUTS_PATHS = (
    Path("/shortcuts.yaml"),
    BASE_DIR.parent / "shortcuts.yaml",
    BASE_DIR / "shortcuts.yaml",
)
ICON_CACHE_DIR = BASE_DIR / "icon-cache"
UI_DIST_DIR = BASE_DIR.parent / "ui" / "dist"
ICON_CACHE_TTL = 3600
BUILTIN_ICON_CACHE_TTL = 6 * 3600
HOMARR_DASHBOARD_ICONS_TREE_URL = "https://api.github.com/repos/homarr-labs/dashboard-icons/git/trees/main?recursive=true"
HOMARR_DASHBOARD_ICONS_CDN = "https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons"
MAX_ICON_BYTES = 2 * 1024 * 1024
BUILTIN_ICON_DOWNLOAD_CONCURRENCY = 12
APP_VERSION = os.getenv("SHORTCUTER_VERSION", "dev")
ICON_EXTENSIONS = (".svg", ".png", ".webp", ".ico", ".jpg", ".jpeg", ".gif")
ICON_CACHE: dict[str, tuple[float, str]] = {}
BUILTIN_ICON_CACHE: tuple[float, list[dict[str, str]]] | None = None
LOGGER = logging.getLogger("shortcuter")


class IconLinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.icon_links: list[dict[str, str]] = []
        self.manifest_links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "link":
            return
        attr_map = {key.lower(): value or "" for key, value in attrs}
        rel = attr_map.get("rel", "").lower()
        href = attr_map.get("href", "")
        if href and "manifest" in rel:
            self.manifest_links.append(href)
        if href and ("icon" in rel or "apple-touch-icon" in rel):
            self.icon_links.append(
                {
                    "href": href,
                    "rel": rel,
                    "sizes": attr_map.get("sizes", ""),
                }
            )


class ShortcutBadge(BaseModel):
    icon: str = Field(min_length=1, max_length=120)
    tooltip: str = Field(default="", max_length=180)


class Shortcut(BaseModel):
    id: str = Field(min_length=1, max_length=120)
    page: str = Field(default="general", min_length=1, max_length=120)
    name: str = Field(min_length=1, max_length=120)
    url: str = Field(min_length=1, max_length=2048)
    description: str | None = Field(default=None, max_length=240)
    group: str = Field(default="Applications", max_length=80)
    icon_type: Literal["auto", "preset", "custom", "predefined"] = "auto"
    icon_value: str | None = Field(default=None, max_length=2048)
    badge: ShortcutBadge | None = None

    @field_validator("url")
    @classmethod
    def normalize_url(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("URL is required")
        parsed = urlparse(value)
        if not parsed.scheme:
            value = f"https://{value}"
            parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Invalid HTTP/HTTPS URL")
        return value


class ShortcutPage(BaseModel):
    id: str
    title: str
    subtitle: str = ""
    rubrique: str
    accent: str = "green"
    shortcuts: list[Shortcut] = Field(default_factory=list)


class PageConfig(BaseModel):
    title: str = "Shortcuter"
    subtitle: str = ""
    rubrique: str = "General"
    accent: str = "green"
    display_density: Literal["comfortable", "compact"] = "comfortable"
    language: str = Field(default="auto", max_length=16)
    logo: str = Field(default="/logo.png", max_length=2048)
    favicon: str = Field(default="", max_length=2048)
    favicon_png: str = Field(default="", max_length=2048)
    apple_touch_icon: str = Field(default="", max_length=2048)
    icon_192: str = Field(default="", max_length=2048)
    show_all_tab: bool = False
    all_tab_accent: str = ""
    show_footer: bool = True
    show_theme_toggle: bool = True
    show_density_toggle: bool = True
    add_tab_name_on_duplicate_app: bool = True


class ShortcutsResponse(BaseModel):
    page: PageConfig
    pages: list[ShortcutPage]
    shortcuts: list[Shortcut]


class BuiltinIconsResponse(BaseModel):
    icons: list[dict[str, str]]


class VersionResponse(BaseModel):
    version: str


def favicon_url(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}/favicon.ico"


def icon_cache_key(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


def icon_extension(url: str, content_type: str) -> str:
    parsed_suffix = Path(urlparse(url).path).suffix.lower()
    if parsed_suffix in {".ico", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}:
        return parsed_suffix
    if "svg" in content_type:
        return ".svg"
    guessed = mimetypes.guess_extension(content_type.split(";")[0].strip())
    if guessed in {".ico", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}:
        return guessed
    return ".ico"


def cached_icon_path(url: str) -> Path | None:
    key = icon_cache_key(url)
    for extension in ICON_EXTENSIONS:
        path = ICON_CACHE_DIR / f"{key}{extension}"
        if path.exists():
            return path
    return None


def icon_api_url(path: Path) -> str:
    return f"/icons/{path.name}"


def slugify(value: str, fallback: str = "item") -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or fallback


def generated_shortcut_id(item: dict, page_id: str) -> str:
    source = str(item.get("name") or urlparse(str(item.get("url") or "")).netloc or "shortcut")
    slug = re.sub(r"[^a-z0-9]+", "-", source.lower()).strip("-") or "shortcut"
    digest = hashlib.sha1(f"{page_id}:{item.get('url') or source}".encode("utf-8")).hexdigest()[:8]
    return f"{slug}-{digest}"


def largest_declared_size(sizes: str) -> int:
    largest = 0
    for size in sizes.split():
        if size.lower() == "any":
            largest = max(largest, 1024)
            continue
        dimensions = size.lower().split("x")
        for dimension in dimensions:
            if dimension.isdigit():
                largest = max(largest, int(dimension))
    return largest


def choose_best_icon(base_url: str, links: list[dict[str, str]], manifest_icons: list[dict[str, str]]) -> str | None:
    candidates: list[dict[str, str | int]] = []

    for icon in manifest_icons:
        src = icon.get("src", "")
        if not src:
            continue
        candidates.append(
            {
                "href": src,
                "source_score": 300,
                "size": largest_declared_size(icon.get("sizes", "")),
            }
        )

    for link in links:
        value = 0
        rel = link.get("rel", "")
        if "apple-touch-icon" in rel:
            value += 100
        if "shortcut icon" in rel:
            value += 40
        if "icon" in rel:
            value += 20
        candidates.append(
            {
                "href": link["href"],
                "source_score": value,
                "size": largest_declared_size(link.get("sizes", "")),
            }
        )

    if not candidates:
        return None
    best = max(candidates, key=lambda candidate: (candidate["size"], candidate["source_score"]))
    return urljoin(base_url, str(best["href"]))


async def detect_icon(url: str) -> str:
    cached = ICON_CACHE.get(url)
    if cached and time() - cached[0] < ICON_CACHE_TTL:
        return cached[1]

    fallback = favicon_url(url)
    parser = IconLinkParser()
    manifest_icons: list[dict[str, str]] = []
    headers = {
        "User-Agent": "Mozilla/5.0 shortcuter-icon-detector/1.0",
        "Accept": "text/html,application/xhtml+xml",
    }

    try:
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=True, verify=False) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            if "html" in response.headers.get("content-type", "") or response.text.lstrip().startswith("<"):
                parser.feed(response.text[:300_000])
            for manifest_href in parser.manifest_links[:2]:
                manifest_url = urljoin(str(response.url), manifest_href)
                manifest_response = await client.get(
                    manifest_url,
                    headers={"Accept": "application/manifest+json,application/json"},
                )
                if manifest_response.status_code >= 400:
                    continue
                manifest = manifest_response.json()
                icons = manifest.get("icons") or []
                manifest_icons.extend(
                    {
                        "src": icon.get("src", ""),
                        "sizes": icon.get("sizes", ""),
                    }
                    for icon in icons
                    if icon.get("src")
                )
            detected = choose_best_icon(str(response.url), parser.icon_links, manifest_icons) or fallback
    except (httpx.HTTPError, ValueError):
        detected = fallback

    ICON_CACHE[url] = (time(), detected)
    return detected


async def cache_icon_asset(icon_url: str) -> str | None:
    ICON_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    existing = cached_icon_path(icon_url)
    if existing:
        return icon_api_url(existing)

    try:
        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True, verify=False) as client:
            response = await client.get(
                icon_url,
                headers={
                    "User-Agent": "Mozilla/5.0 shortcuter-icon-cache/1.0",
                    "Accept": "image/*,*/*",
                },
            )
            response.raise_for_status()
            content = response.content
    except Exception as exc:
        LOGGER.debug("Icon cache failed for %s: %s", icon_url, exc)
        return None

    if not content or len(content) > MAX_ICON_BYTES:
        return None

    content_type = response.headers.get("content-type", "")
    extension = icon_extension(str(response.url), content_type)
    path = ICON_CACHE_DIR / f"{icon_cache_key(icon_url)}{extension}"
    path.write_bytes(content)
    return icon_api_url(path)


async def fetch_builtin_icons() -> list[dict[str, str]]:
    global BUILTIN_ICON_CACHE
    if BUILTIN_ICON_CACHE and time() - BUILTIN_ICON_CACHE[0] < BUILTIN_ICON_CACHE_TTL:
        return with_local_builtin_sources(BUILTIN_ICON_CACHE[1])

    priority = {".svg": 0, ".png": 1, ".webp": 2, ".ico": 3, ".jpg": 4, ".jpeg": 5}
    by_name: dict[str, tuple[int, dict[str, str]]] = {}
    try:
        async with httpx.AsyncClient(timeout=12.0, follow_redirects=True, verify=False) as client:
            response = await client.get(HOMARR_DASHBOARD_ICONS_TREE_URL)
            response.raise_for_status()
            payload = response.json()
    except (httpx.HTTPError, ValueError):
        return BUILTIN_ICON_CACHE[1] if BUILTIN_ICON_CACHE else []

    for item in payload.get("tree", []):
        path = item.get("path", "")
        suffix = Path(path).suffix.lower()
        if suffix not in priority or not path.startswith(("svg/", "png/", "webp/")):
            continue
        name = Path(path).stem
        cdn_src = f"{HOMARR_DASHBOARD_ICONS_CDN}/{path}"
        icon = {
            "key": f"homarr/{name}",
            "name": name.replace("-", " "),
            "src": cdn_src,
            "cdn_src": cdn_src,
        }
        local_path = cached_icon_path(cdn_src)
        if local_path:
            icon["src"] = icon_api_url(local_path)
        current = by_name.get(name)
        if current is None or priority[suffix] < current[0]:
            by_name[name] = (priority[suffix], icon)

    icons = sorted((icon for _, icon in by_name.values()), key=lambda icon: icon["key"])
    BUILTIN_ICON_CACHE = (time(), icons)
    return icons


def with_local_builtin_sources(icons: list[dict[str, str]]) -> list[dict[str, str]]:
    result = []
    for icon in icons:
        next_icon = dict(icon)
        cdn_src = next_icon.get("cdn_src") or next_icon.get("src", "")
        local_path = cached_icon_path(cdn_src)
        if local_path:
            next_icon["src"] = icon_api_url(local_path)
        result.append(next_icon)
    return result


def should_download_builtin_icons() -> bool:
    content = load_yaml()
    raw_general = content.get("general") or {}
    return bool(raw_general.get("download-icons"))


def configured_builtin_icon_keys() -> set[str]:
    content = load_yaml()
    keys: set[str] = set()

    def add_icon(raw_icon: object) -> None:
        icon = str(raw_icon or "").strip().lstrip("/")
        if "/" not in icon:
            return
        if icon.startswith("homarr/"):
            keys.add(icon.rsplit(".", 1)[0])

    for page in content.get("pages") or []:
        if not isinstance(page, dict):
            continue
        for item in page.get("shortcuts") or []:
            if isinstance(item, dict):
                add_icon(item.get("icon"))

    return keys


async def warm_builtin_icon_cache() -> None:
    global BUILTIN_ICON_CACHE
    wanted_keys = configured_builtin_icon_keys()
    if not wanted_keys:
        LOGGER.info("Builtin icon warm cache skipped: no configured Homarr icons")
        return

    icons = await fetch_builtin_icons()
    icons = [icon for icon in icons if icon.get("key") in wanted_keys]
    LOGGER.info("Builtin icon warm cache started: %s configured icons", len(icons))
    semaphore = asyncio.Semaphore(BUILTIN_ICON_DOWNLOAD_CONCURRENCY)
    downloaded = 0

    async def cache_one(icon: dict[str, str]) -> None:
        nonlocal downloaded
        src = icon.get("src", "")
        src = icon.get("cdn_src", src)
        if not src or src.startswith("/icons/"):
            return
        async with semaphore:
            if await cache_icon_asset(src):
                downloaded += 1

    await asyncio.gather(*(cache_one(icon) for icon in icons))
    BUILTIN_ICON_CACHE = None
    await fetch_builtin_icons()
    LOGGER.info("Builtin icon warm cache finished: %s cached", downloaded)


def shortcut_from_yaml(item: dict, default_page_id: str) -> Shortcut:
    icon = str(item.get("icon") or "auto").strip()
    url = item.get("url", "")
    icon_type = "auto"
    icon_value = None
    badge = None

    if icon and icon != "auto":
        if icon.startswith(("http://", "https://", "/")):
            icon_type = "custom"
            icon_value = icon
        elif "/" in icon:
            icon_type = "predefined"
            icon_value = icon.strip().lstrip("/")
        else:
            icon_type = "preset"
            icon_value = icon

    raw_badge = item.get("badge")
    if isinstance(raw_badge, dict) and raw_badge.get("icon"):
        badge = ShortcutBadge(
            icon=str(raw_badge.get("icon")),
            tooltip=str(raw_badge.get("tooltip") or ""),
        )

    shortcut = Shortcut(
        id=str(item.get("id") or generated_shortcut_id(item, default_page_id)),
        page=str(item.get("page") or default_page_id),
        name=item.get("name", ""),
        url=url,
        description=item.get("description"),
        group=item.get("group") or "Applications",
        icon_type=icon_type,
        icon_value=icon_value,
        badge=badge,
    )
    if shortcut.icon_type == "auto":
        shortcut.icon_value = favicon_url(shortcut.url)
    return shortcut


def shortcuts_path() -> Path:
    for path in SHORTCUTS_PATHS:
        if path.is_file():
            return path
    return SHORTCUTS_PATHS[-1]


def load_yaml() -> dict:
    path = shortcuts_path()
    if not path.is_file():
        return {}
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise HTTPException(status_code=500, detail=f"Invalid YAML: {exc}") from exc


def load_page(content: dict) -> PageConfig:
    raw_page = content.get("general") or {}
    if raw_page and not isinstance(raw_page, dict):
        raise HTTPException(status_code=500, detail="YAML field 'general' must be an object")
    display_density = str(raw_page.get("display_density") or "comfortable").strip().lower()
    if display_density not in {"comfortable", "compact"}:
        raise HTTPException(
            status_code=500,
            detail="YAML field 'general.display_density' must be 'comfortable' or 'compact'",
        )
    return PageConfig(
        title=str(raw_page.get("title") or "Shortcuter"),
        subtitle=str(raw_page.get("subtitle") or ""),
        rubrique=str(raw_page.get("rubrique") or "General"),
        accent=str(raw_page.get("accent") or "green"),
        display_density=display_density,
        language=str(raw_page.get("language") or "auto"),
        logo=str(raw_page.get("logo") or "/logo.png"),
        favicon=str(raw_page.get("favicon") or ""),
        favicon_png=str(raw_page.get("favicon_png") or ""),
        apple_touch_icon=str(raw_page.get("apple_touch_icon") or ""),
        icon_192=str(raw_page.get("icon_192") or ""),
        show_all_tab=bool(raw_page.get("show_all_tab")),
        all_tab_accent=str(raw_page.get("all_tab_accent") or ""),
        show_footer=raw_page.get("show_footer", True) is not False,
        show_theme_toggle=raw_page.get("show_theme_toggle", True) is not False,
        show_density_toggle=raw_page.get("show_density_toggle", True) is not False,
        add_tab_name_on_duplicate_app=raw_page.get("add_tab_name_on_duplicate_app", True) is not False,
    )


def shortcut_page_from_yaml(index: int, item: dict, default_page: PageConfig) -> dict:
    title = str(item.get("title") or f"Page {index + 1}")
    page_id = slugify(title, f"page-{index + 1}")
    return {
        "id": page_id,
        "title": title,
        "subtitle": str(item.get("subtitle") or ""),
        "rubrique": str(item.get("rubrique") or default_page.rubrique),
        "accent": str(item.get("accent") or default_page.accent),
        "shortcuts": [],
    }


def load_pages(content: dict, default_page: PageConfig) -> list[dict]:
    raw_pages = content.get("pages")
    if raw_pages is None:
        return [
            {
                "id": slugify(default_page.rubrique, "general"),
                "title": default_page.title,
                "subtitle": default_page.subtitle,
                "rubrique": default_page.rubrique,
                "accent": default_page.accent,
                "shortcuts": [],
            }
        ]
    if not isinstance(raw_pages, list):
        raise HTTPException(status_code=500, detail="YAML field 'pages' must be a list")

    pages = []
    for index, item in enumerate(raw_pages):
        if not isinstance(item, dict):
            raise HTTPException(status_code=500, detail=f"Page #{index + 1} is invalid")
        page = shortcut_page_from_yaml(index, item, default_page)
        raw_shortcuts = item.get("shortcuts") or []
        if not isinstance(raw_shortcuts, list):
            raise HTTPException(status_code=500, detail=f"YAML field 'pages[{index}].shortcuts' must be a list")
        for shortcut_index, shortcut_item in enumerate(raw_shortcuts):
            if not isinstance(shortcut_item, dict):
                raise HTTPException(status_code=500, detail=f"Shortcut #{shortcut_index + 1} on page {page['id']} is invalid")
            try:
                page["shortcuts"].append(shortcut_from_yaml(shortcut_item, page["id"]))
            except (ValueError, ValidationError) as exc:
                raise HTTPException(
                    status_code=500,
                    detail=f"Shortcut #{shortcut_index + 1} on page {page['id']}: {exc}",
                ) from exc
        pages.append(page)
    pages = pages or load_pages({}, default_page)
    if default_page.add_tab_name_on_duplicate_app:
        append_page_name_to_duplicate_shortcuts(pages)
    return pages


def duplicate_shortcut_key(shortcut: Shortcut) -> str:
    return shortcut.name.strip().casefold()


def append_page_name_to_duplicate_shortcuts(pages: list[dict]) -> None:
    page_titles = {
        page["id"]: page["title"]
        for page in pages
    }
    occurrences: dict[str, set[str]] = {}
    for page in pages:
        for shortcut in page["shortcuts"]:
            occurrences.setdefault(duplicate_shortcut_key(shortcut), set()).add(page["id"])

    duplicate_keys = {
        key
        for key, page_ids in occurrences.items()
        if key and len(page_ids) > 1
    }
    for page in pages:
        for shortcut in page["shortcuts"]:
            if duplicate_shortcut_key(shortcut) in duplicate_keys:
                shortcut.name = f"{shortcut.name} ({page_titles.get(shortcut.page, page['title'])})"


async def enrich_auto_icons(shortcuts: list[Shortcut]) -> list[Shortcut]:
    for shortcut in shortcuts:
        if shortcut.icon_type == "auto":
            detected_icon = await detect_icon(shortcut.url)
            shortcut.icon_value = await cache_icon_asset(detected_icon) or detected_icon
    return shortcuts


@asynccontextmanager
async def lifespan(app: FastAPI):
    if should_download_builtin_icons():
        LOGGER.info("Builtin icon warm cache enabled by YAML")
        asyncio.create_task(warm_builtin_icon_cache())
    else:
        LOGGER.info("Builtin icon warm cache disabled by YAML")
    yield


app = FastAPI(
    title="Shortcuter API",
    version="1.0.0",
    description="Read-only shortcuts API backed by a YAML file.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def force_cors_headers(request, call_next):
    if request.method == "OPTIONS":
        response = Response(status_code=204)
    else:
        response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, HEAD, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": APP_VERSION}


@app.get("/version", response_model=VersionResponse)
async def version() -> VersionResponse:
    return VersionResponse(version=APP_VERSION)


@app.get("/icons/{filename}")
async def cached_icon(filename: str) -> FileResponse:
    path = ICON_CACHE_DIR / filename
    if path.parent != ICON_CACHE_DIR or not path.exists():
        raise HTTPException(status_code=404, detail="Icon not found")
    return FileResponse(path)


@app.get("/builtin-icons", response_model=BuiltinIconsResponse)
async def builtin_icons() -> BuiltinIconsResponse:
    return BuiltinIconsResponse(icons=await fetch_builtin_icons())


@app.get("/shortcuts", response_model=ShortcutsResponse)
async def list_shortcuts() -> ShortcutsResponse:
    content = load_yaml()
    page = load_page(content)
    pages = load_pages(content, page)
    shortcuts = [shortcut for item in pages for shortcut in item["shortcuts"]]
    await enrich_auto_icons(shortcuts)
    return ShortcutsResponse(
        page=page,
        pages=pages,
        shortcuts=shortcuts,
    )


if UI_DIST_DIR.exists():
    app.mount("/assets", StaticFiles(directory=UI_DIST_DIR / "assets"), name="assets")


def ui_index() -> HTMLResponse:
    index_path = UI_DIST_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="UI build not found")
    return HTMLResponse(index_path.read_text(encoding="utf-8"))


@app.get("/", response_class=HTMLResponse)
async def serve_ui_root() -> HTMLResponse:
    return ui_index()


@app.api_route("/{path:path}", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def serve_ui_path(path: str):
    if "." in Path(path).name:
        asset_path = UI_DIST_DIR / path
        if asset_path.is_file() and asset_path.resolve().is_relative_to(UI_DIST_DIR.resolve()):
            return FileResponse(asset_path)
        raise HTTPException(status_code=404, detail="File not found")
    return ui_index()
