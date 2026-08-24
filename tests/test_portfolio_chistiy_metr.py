import ast
from dataclasses import replace
from html import escape
from importlib import import_module
import inspect

import pytest
from playwright.sync_api import sync_playwright

from portfolio.kwork_pack.catalog import get_project, public_url
from portfolio.kwork_pack.shell import build_document
from portfolio.kwork_pack.sites.runtime import RenderedPage


_ROUTE_COPY = {
    "cover": (
        "Уборка после ремонта от 120 ₽ за м²",
        "Свободная бригада сегодня с 14:00",
        "Гарантия результата 24 часа",
    ),
    "after-renovation": (
        "Уборка после ремонта: контроль по зонам",
        "Состояние до выхода бригады",
        "Приёмка по 18 контрольным точкам",
    ),
    "calculator": (
        "Рассчитайте уборку без скрытых доплат",
        "Следующее окно: сегодня, 14:00",
        "В расчёт не входит вывоз строительного мусора",
    ),
    "checklist": (
        "Что входит в уборку после ремонта",
        "Зона: санузел",
        "Лист приёмки остаётся у заказчика",
    ),
    "reviews": (
        "Отзывы после реальных уборок",
        "Бригада Марины свободна завтра в 10:00",
        "4,9 из 5 по 286 проверенным оценкам",
    ),
}

_ASSETS_BY_ROUTE = {
    "cover": ("clean_kitchen",),
    "after-renovation": ("before_cleanup", "after_cleanup"),
    "calculator": ("equipment_case",),
    "checklist": ("bathroom_detail",),
    "reviews": ("cleaner_portrait",),
}


def _render(project, shot, assets):
    module = import_module("portfolio.kwork_pack.sites.chistiy_metr")
    return module.render(project, shot, assets)


def _assets(project):
    return {
        asset.key: f'/assets/{asset.filename}?project=chistiy-metr&mode="preview"'
        for asset in project.assets
    }


@pytest.fixture(scope="module")
def chrome_browser():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome", headless=True)
        try:
            yield browser
        finally:
            browser.close()


def _set_route(page, project, shot, assets):
    rendered = _render(project, shot, assets)
    page.set_content(
        build_document(
            project,
            shot,
            rendered.html,
            rendered.css,
            rendered.scripts,
        ),
        wait_until="load",
    )
    return rendered


def test_chistiy_metr_renders_five_distinct_routes_with_exact_russian_copy():
    project = get_project("chistiy-metr")
    pages = [_render(project, shot, _assets(project)) for shot in project.shots]

    assert all(isinstance(page, RenderedPage) for page in pages)
    assert [shot.key for shot in project.shots] == list(_ROUTE_COPY)
    assert len({page.html for page in pages}) == 5
    for shot, page in zip(project.shots, pages):
        assert 'data-site="chistiy-metr"' in page.html
        assert f'data-route="{shot.key}"' in page.html
        assert "Чистый метр" in page.html
        assert "клининговая служба" in page.html
        for fragment in _ROUTE_COPY[shot.key]:
            assert fragment in page.html


def test_chistiy_metr_uses_each_route_owned_asset_exactly_once():
    project = get_project("chistiy-metr")
    assets = _assets(project)
    pages = {
        shot.key: _render(project, shot, assets).html for shot in project.shots
    }

    for route, owned_keys in _ASSETS_BY_ROUTE.items():
        for key in owned_keys:
            source = escape(assets[key], quote=True)
            assert pages[route].count(source) == 1
            assert sum(page.count(source) for page in pages.values()) == 1


@pytest.mark.parametrize(("shot_key", "owned_keys"), _ASSETS_BY_ROUTE.items())
def test_chistiy_metr_reports_missing_route_owned_asset(shot_key, owned_keys):
    project = get_project("chistiy-metr")
    shot = next(item for item in project.shots if item.key == shot_key)
    assets = _assets(project)
    missing_key = owned_keys[0]
    assets.pop(missing_key)

    with pytest.raises(
        KeyError, match=rf"chistiy-metr.*{shot_key}.*{missing_key}"
    ):
        _render(project, shot, assets)


def test_chistiy_metr_rejects_other_projects_and_unknown_routes():
    project = get_project("chistiy-metr")
    other = get_project("kvadrat-remonta")

    with pytest.raises(KeyError, match="chistiy-metr renderer.*kvadrat-remonta"):
        _render(other, other.shots[0], _assets(project))

    unknown = replace(project.shots[0], key="unknown")
    with pytest.raises(ValueError, match="chistiy-metr.*unknown"):
        _render(project, unknown, _assets(project))


def test_chistiy_metr_has_stable_geometry_and_meaningful_lower_bands():
    project = get_project("chistiy-metr")
    pages = [_render(project, shot, _assets(project)) for shot in project.shots]
    combined = "\n".join(page.html + page.css for page in pages).casefold()

    for fragment in (
        "height: 1120px",
        ".cm-cover-proof",
        ".cm-after-handoff",
        ".cm-calculator-scope",
        ".cm-checklist-acceptance",
        ".cm-reviews-metrics",
    ):
        assert fragment.casefold() in combined
    for shot in project.shots:
        assert public_url(project, shot) == f"https://chistiy-metr.ru{shot.path}"
    for forbidden in ("gradient", "border-radius", "overlay", "localhost", "lorem"):
        assert forbidden not in combined


def test_chistiy_metr_calculators_update_dependent_summary_in_chrome(chrome_browser):
    project = get_project("chistiy-metr")
    assets = _assets(project)
    shots = {shot.key: shot for shot in project.shots}
    page = chrome_browser.new_page(viewport={"width": 1920, "height": 1280})
    try:
        _set_route(page, project, shots["cover"], assets)
        geometry = page.locator(".cm-page").bounding_box()
        page.locator("[data-cover-area]").fill("86")
        page.locator('[data-selectable="cover-service"]').nth(1).click()
        page.locator("[data-cover-windows]").check()
        quote = page.locator(".cm-cover-quote").inner_text()
        assert "86 м²" in quote
        assert "Генеральная после ремонта" in quote
        assert "15 380 ₽" in quote
        assert "Бригада из 3 человек" in quote
        assert page.locator(".cm-page").bounding_box() == geometry

        _set_route(page, project, shots["calculator"], assets)
        geometry = page.locator(".cm-page").bounding_box()
        room_types = page.locator('[data-selectable="calculator-room"]')
        assert room_types.count() == 3
        page.locator("[data-calculator-area]").fill("72")
        page.locator('[data-selectable="calculator-urgency"]').nth(1).click()
        page.locator("[data-calculator-oven]").check()
        summary = page.locator(".cm-calculator-summary").inner_text()
        scope = page.locator(".cm-calculator-scope").inner_text()
        assert "13 140 ₽" in summary
        assert "Завтра, 10:00" in summary
        assert "2 специалиста" in summary
        assert "Духовой шкаф внутри" in scope

        room_types.nth(2).click()
        assert room_types.nth(2).get_attribute("aria-pressed") == "true"
        summary = page.locator(".cm-calculator-summary").inner_text()
        scope = page.locator(".cm-calculator-scope").inner_text()
        assert "12 060 ₽" in summary
        assert "Офис после ремонта · 72 м²" in scope
        assert page.locator(".cm-page").bounding_box() == geometry
    finally:
        page.close()


def test_chistiy_metr_zone_and_review_controls_update_real_content_in_chrome(
    chrome_browser,
):
    project = get_project("chistiy-metr")
    assets = _assets(project)
    shots = {shot.key: shot for shot in project.shots}
    page = chrome_browser.new_page(viewport={"width": 1920, "height": 1280})
    try:
        _set_route(page, project, shots["checklist"], assets)
        geometry = page.locator(".cm-page").bounding_box()
        zones = page.locator('[data-selectable="cleaning-zone"]')
        zones.nth(2).click()
        assert zones.nth(2).get_attribute("aria-pressed") == "true"
        scope = page.locator(".cm-zone-summary").inner_text()
        assert "Спальня" in scope
        assert "6 задач включено" in scope
        assert "Химчистка матраса не входит" in scope
        assert page.locator(".cm-page").bounding_box() == geometry

        _set_route(page, project, shots["reviews"], assets)
        geometry = page.locator(".cm-page").bounding_box()
        filters = page.locator('[data-selectable="review-filter"]')
        filters.nth(1).click()
        assert filters.nth(1).get_attribute("aria-pressed") == "true"
        ledger = page.locator(".cm-review-ledger").inner_text()
        rating = page.locator(".cm-review-rating").inner_text()
        assert "Уборка после ремонта · 72 м²" in ledger
        assert "Акт принят без замечаний" in ledger
        assert "4,9 из 5 по 118 проверенным оценкам" in rating

        filters.nth(2).click()
        rating = page.locator(".cm-review-rating").inner_text()
        assert "5,0 из 5 по 76 проверенным оценкам" in rating
        assert page.locator(".cm-page").bounding_box() == geometry
    finally:
        page.close()


def test_chistiy_metr_text_is_at_least_12px_and_canvas_is_stable_in_chrome(
    chrome_browser,
):
    project = get_project("chistiy-metr")
    page = chrome_browser.new_page(viewport={"width": 1920, "height": 1280})
    try:
        for shot in project.shots:
            _set_route(page, project, shot, _assets(project))
            audit = page.locator(".cm-page").evaluate(
                """root => {
                  const box = root.getBoundingClientRect();
                  const small = [...root.querySelectorAll('*')].filter((node) => {
                    const style = getComputedStyle(node);
                    const hasText = [...node.childNodes].some(
                      (child) => child.nodeType === Node.TEXT_NODE && child.textContent.trim()
                    );
                    return hasText && style.display !== 'none' &&
                      style.visibility !== 'hidden' && parseFloat(style.fontSize) < 12;
                  });
                  return {width: box.width, height: box.height, scrollHeight: root.scrollHeight, small};
                }"""
            )
            assert audit["width"] == 1834
            assert audit["height"] == 1120
            assert audit["scrollHeight"] == 1120
            assert audit["small"] == []
    finally:
        page.close()


def test_chistiy_metr_module_is_isolated_from_other_site_renderers():
    project = get_project("chistiy-metr")
    renderer = import_module("portfolio.kwork_pack.sites.chistiy_metr").render
    _render(project, project.shots[0], _assets(project))
    source = inspect.getsource(inspect.getmodule(renderer))
    imported_modules = {
        alias.name
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module or ""
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.ImportFrom)
    }

    assert "def render" in source
    for foreign_prefix in ("da-", "vk-", "th-", "sh-", "kr-", "os-"):
        assert foreign_prefix not in source
    assert not any(
        name.endswith(
            (
                "dentalea",
                "ventkontur",
                "tochka_hoda",
                "syr_hleb",
                "kvadrat_remonta",
                "okna_sfera",
                "commercial",
                "leadgen",
                "complex",
            )
        )
        for name in imported_modules
    )
