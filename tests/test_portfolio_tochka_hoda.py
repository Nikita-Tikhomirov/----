import ast
from dataclasses import replace
from html import escape
import inspect

import pytest
from playwright.sync_api import sync_playwright

from portfolio.kwork_pack.catalog import get_project
from portfolio.kwork_pack.shell import build_document
from portfolio.kwork_pack.sites.runtime import RenderedPage
from portfolio.kwork_pack.sites.tochka_hoda import render


_ROUTE_COPY = {
    "cover": (
        "Техническое обслуживание",
        "41 параметр",
        "Что мы делаем",
    ),
    "diagnostics": (
        "Диагностика автомобиля",
        "Базовая",
        "Что входит в диагностику",
    ),
    "booking": (
        "Запись на диагностику",
        "BMW X5",
        "Подтвердить запись",
    ),
    "case-study": (
        "BMW X5: устранили стук в ходовой",
        "89 420 км",
        "Что обнаружили",
    ),
    "prices": (
        "Цены на услуги",
        "Компьютерная диагностика",
        "Цена фиксируется до начала работ",
    ),
}

_ASSETS_BY_ROUTE = {
    "cover": ("workshop_hero",),
    "diagnostics": ("diagnostic_closeup",),
    "booking": ("service_lounge",),
    "case-study": ("bmw_before", "bmw_after"),
    "prices": ("mechanic_portrait", "engine_inspection"),
}


def _assets(project):
    return {
        asset.key: f'/assets/{asset.filename}?project=tochka&mode="preview"'
        for asset in project.assets
    }


def test_flagship_renders_five_distinct_real_pages_with_exact_story_copy():
    project = get_project("tochka-hoda")
    pages = [render(project, shot, _assets(project)) for shot in project.shots]

    assert all(isinstance(page, RenderedPage) for page in pages)
    assert len({page.html for page in pages}) == 5
    assert [shot.key for shot in project.shots] == list(_ROUTE_COPY)
    for shot, page in zip(project.shots, pages):
        assert 'data-site="tochka-hoda"' in page.html
        assert f'data-route="{shot.key}"' in page.html
        assert "ТОЧКА" in page.html
        assert "ХОДА" in page.html
        for fragment in _ROUTE_COPY[shot.key]:
            assert fragment in page.html


def test_flagship_uses_every_photo_once_and_only_on_its_owned_route():
    project = get_project("tochka-hoda")
    assets = _assets(project)
    pages = {
        shot.key: render(project, shot, assets).html for shot in project.shots
    }

    for route, owned_keys in _ASSETS_BY_ROUTE.items():
        for key in owned_keys:
            escaped_source = escape(assets[key], quote=True)
            assert pages[route].count(escaped_source) == 1
            assert sum(page.count(escaped_source) for page in pages.values()) == 1


@pytest.mark.parametrize(("shot_key", "required_keys"), _ASSETS_BY_ROUTE.items())
def test_flagship_reports_the_missing_route_owned_asset(shot_key, required_keys):
    project = get_project("tochka-hoda")
    shot = next(item for item in project.shots if item.key == shot_key)
    assets = _assets(project)
    missing_key = required_keys[0]
    assets.pop(missing_key)

    with pytest.raises(KeyError, match=rf"tochka-hoda.*{shot_key}.*{missing_key}"):
        render(project, shot, assets)


def test_flagship_rejects_other_projects_and_unknown_routes():
    flagship = get_project("tochka-hoda")
    other = get_project("dentalea")
    with pytest.raises(KeyError, match="tochka-hoda renderer.*dentalea"):
        render(other, other.shots[0], _assets(flagship))

    unknown = replace(flagship.shots[0], key="unknown")
    with pytest.raises(ValueError, match="tochka-hoda.*unknown"):
        render(flagship, unknown, _assets(flagship))


def test_flagship_has_stable_desktop_geometry_and_no_forbidden_copy():
    project = get_project("tochka-hoda")
    pages = [render(project, shot, _assets(project)) for shot in project.shots]
    combined = "\n".join(page.html + page.css for page in pages).casefold()

    for fragment in (
        "height: 1120px",
        ".th-header",
        ".th-booking-grid",
        ".th-calendar",
        ".th-price-table",
        ".th-case-grid",
    ):
        assert fragment.casefold() in combined
    for forbidden in ("localhost", "lorem", "demo", "никита тихомиров"):
        assert forbidden not in combined


def test_flagship_detail_routes_keep_the_premium_information_density():
    project = get_project("tochka-hoda")
    pages = {
        shot.key: render(project, shot, _assets(project))
        for shot in project.shots
    }

    diagnostics = pages["diagnostics"].html
    assert '<span class="th-check-count">9</span>' in diagnostics
    assert "Система вентиляции картера" in diagnostics
    assert "Турбонаддув / наддув" in diagnostics

    case_study = pages["case-study"].html
    assert 'class="th-finding-copy"' in case_study
    assert 'class="th-repair-proof"' in case_study
    assert "Контрольный замер" in case_study

    prices_css = pages["prices"].css
    assert ".th-prices-title { height: 132px;" in prices_css
    assert ".th-prices-main" in prices_css
    assert "height: 590px" in prices_css


def test_flagship_interactive_choices_change_selected_state_in_chrome():
    project = get_project("tochka-hoda")
    scenarios = (
        ("diagnostics", 'package', 1),
        ("booking", 'time', 2),
        ("prices", 'category', 3),
    )

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": 1920, "height": 1280})
        try:
            for shot_key, group, selected_index in scenarios:
                shot = next(item for item in project.shots if item.key == shot_key)
                rendered = render(project, shot, _assets(project))
                page.set_content(
                    build_document(
                        project,
                        shot,
                        rendered.html,
                        rendered.css,
                        rendered.scripts,
                    )
                )
                choices = page.locator(f'[data-selectable="{group}"]')
                choices.nth(selected_index).click()

                assert "active" in (choices.nth(selected_index).get_attribute("class") or "")
                assert sum(
                    "active" in (choices.nth(index).get_attribute("class") or "")
                    for index in range(choices.count())
                ) == 1
        finally:
            page.close()
            browser.close()


def test_flagship_module_is_isolated_from_other_site_renderers():
    source = inspect.getsource(render)
    module_source = inspect.getsource(inspect.getmodule(render))
    tree = ast.parse(module_source)
    imported_modules = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }

    assert "def render" in source
    assert not any(
        name.endswith(("commercial", "leadgen", "complex"))
        for name in imported_modules
    )
