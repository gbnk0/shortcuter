import pytest
from fastapi import HTTPException

from app.main import load_page, load_pages, parse_yaml_config


def test_general_options_are_parsed():
    content = {
        "general": {
            "title": "Links",
            "app_title": "Company Links",
            "display_density": "compact",
            "language": "fr",
            "logo": "brand.png",
            "show_footer": False,
            "show_theme_toggle": False,
            "show_density_toggle": False,
        }
    }

    page = load_page(content)

    assert page.title == "Links"
    assert page.app_title == "Company Links"
    assert page.display_density == "compact"
    assert page.language == "fr"
    assert page.logo == "brand.png"
    assert page.favicon == ""
    assert page.show_footer is False
    assert page.show_theme_toggle is False
    assert page.show_density_toggle is False


def test_app_title_defaults_to_page_title_and_accepts_legacy_alias():
    assert load_page({"general": {"title": "Team Links"}}).app_title == "Team Links"
    assert load_page({"general": {"title": "Team Links", "apptitle": "Browser Links"}}).app_title == "Browser Links"


def test_invalid_display_density_has_clear_location():
    with pytest.raises(HTTPException) as exc:
        parse_yaml_config({"general": {"display_density": "wide"}})

    assert exc.value.status_code == 500
    assert "general.display_density" in exc.value.detail


def test_invalid_shortcut_has_clear_location():
    with pytest.raises(HTTPException) as exc:
        parse_yaml_config({"pages": [{"title": "Ops", "shortcuts": [{"name": "Grafana"}]}]})

    assert exc.value.status_code == 500
    assert "pages.0.shortcuts.0.url" in exc.value.detail


def test_duplicate_shortcut_names_include_page_name():
    content = {
        "general": {"show_all_tab": True, "add_tab_name_on_duplicate_app": True},
        "pages": [
            {
                "title": "Ops",
                "shortcuts": [{"name": "Grafana", "url": "https://ops.example.test"}],
            },
            {
                "title": "Data",
                "shortcuts": [{"name": "Grafana", "url": "https://data.example.test"}],
            },
        ],
    }

    page = load_page(content)
    pages = load_pages(content, page)

    assert pages[0]["shortcuts"][0].name == "Grafana (Ops)"
    assert pages[1]["shortcuts"][0].name == "Grafana (Data)"


def test_duplicate_shortcut_names_can_stay_unchanged():
    content = {
        "general": {"add_tab_name_on_duplicate_app": False},
        "pages": [
            {
                "title": "Ops",
                "shortcuts": [{"name": "Grafana", "url": "https://ops.example.test"}],
            },
            {
                "title": "Data",
                "shortcuts": [{"name": "Grafana", "url": "https://data.example.test"}],
            },
        ],
    }

    page = load_page(content)
    pages = load_pages(content, page)

    assert pages[0]["shortcuts"][0].name == "Grafana"
    assert pages[1]["shortcuts"][0].name == "Grafana"
