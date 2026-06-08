# Shortcuter

Read-only Vue.js + FastAPI app for displaying shortcuts defined in YAML.

## YAML

Edit shortcuts in:

```text
api/shortcuts.yaml
```

This file is intentionally ignored by Git. To start from the bundled example:

```bash
cp api/shortcuts.example.yaml api/shortcuts.yaml
```

With Docker, the file can also be mounted at the container root:

```text
/shortcuts.yaml
```

Format:

```yaml
general:
  title: Shortcuter
  subtitle: Internal apps and services
  rubrique: Links
  accent: green
  download-icons: true
  show_all_tab: true
  all_tab_accent: slate

pages:
  - title: General
    subtitle: Daily quick access
    rubrique: Home
    accent: green
    shortcuts:
      - name: Kibana
        url: https://kibana.example.lan
        group: Monitoring
        description: Dashboards and metrics
        icon: homarr/kibana

  - title: Infrastructure
    subtitle: Infrastructure services
    rubrique: Operations
    accent: blue
    shortcuts: []
```

`icon` accepts:

- `auto` or a missing field: automatic detection through HTML/manifest, with `https://host/favicon.ico` as fallback;
- a Material Design Icons class, for example `mdi-server`;
- a live Homarr Labs icon, for example `homarr/kibana`;
- an image URL, for example `https://assets.example.lan/icon.png`.

A shortcut can display a small overlaid badge with a tooltip:

```yaml
badge:
  icon: mdi-hammer-wrench
  tooltip: Maintenance in progress
```

Do not define `id` values in YAML: the API generates stable IDs for pages and shortcuts.

Shortcuts are defined directly in `pages[].shortcuts`.

`accent` accepts a named color: `green`, `blue`, `orange`, `purple`, `pink`, `red`, `cyan`, `yellow`, `slate`. Hex values such as `#16807a` are also accepted.

In `auto` mode, the API ignores TLS certificate validation while fetching icons, selects the largest declared size, then stores the image in `api/icon-cache`. The frontend uses the local icon served by the API instead of fetching it on every page load.

With `general.download-icons: true`, the API downloads configured Homarr Labs icons into the local `api/icon-cache` at startup. HTTP startup is not blocked by the download; icons switch to `/icons/...` as the cache is populated.

With `general.show_all_tab: true`, the UI adds an `All` tab that displays shortcuts from every page.

`general.all_tab_accent` sets the `All` tab color. If omitted, it falls back to `general.accent`.

## API

```bash
cd raccourcis/api
python3.13 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The project uses pinned FastAPI/Pydantic versions from `requirements.txt`.
On macOS with Homebrew, use `python3.13`: Python 3.14 is too recent for these dependencies.

Endpoints:

- `GET /health`
- `GET /shortcuts`
- `GET /builtin-icons`

UI routes:

- `/page/<generated-id>` for a shortcuts page;
- `/icons` for available icons.

## Docker

The Docker image serves both the API and the Vue build on port `8000`.

```bash
docker build -t shortcuter .
docker run --rm -p 8000:8000 \
  -v "$PWD/api/shortcuts.example.yaml:/shortcuts.yaml:ro" \
  -v shortcuter-icon-cache:/app/api/icon-cache \
  shortcuter
```

A standard Compose file is provided:

```bash
docker compose up -d --build
```

By default, `docker-compose.yml` mounts `api/shortcuts.example.yaml` so the project starts immediately after cloning.
To use a private local configuration, copy the example and replace the volume in `docker-compose.yml` with the commented line:

```bash
cp api/shortcuts.example.yaml shortcuts.yaml
```

Without a `/shortcuts.yaml` mount, the image also uses `api/shortcuts.example.yaml` as its default configuration.

### Publish to Docker Hub

The repository includes a GitHub Actions workflow that builds and pushes the image to Docker Hub.

Create these repository secrets in GitHub:

```text
DOCKERHUB_USERNAME
DOCKERHUB_TOKEN
```

The workflow runs on pushes to `main`, on tags matching `v*`, and manually through `workflow_dispatch`.

Published tags:

- `latest` for the default branch;
- the Git tag, for example `v0.4.0`;
- semantic version aliases, for example `0.4.0` and `0.4`;
- a commit SHA tag, for example `sha-abc1234`.

## UI

```bash
cd raccourcis/ui
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

The frontend calls the API on the same host at port `8000`.

Example: if the page is opened at `http://localhost:5173`, API calls go to `http://localhost:8000`.

To force a different API address:

```bash
VITE_API_URL=http://api.example.lan:8000 npm run dev -- --host 0.0.0.0 --port 5173
```
