import ast
from html import escape
from importlib import import_module
import inspect
import re

import pytest
from playwright.sync_api import sync_playwright

from portfolio.kwork_pack.catalog import get_project
from portfolio.kwork_pack.shell import build_document
from portfolio.kwork_pack.sites.runtime import RenderedPage


_ROUTE_COPY = {
    "cover": (
        "Ремонт газовых котлов в день обращения",
        "Мастер будет в течение 45 минут",
        "Опишите неисправность",
    ),
    "boiler-repair": (
        "Ремонтируем котёл по результатам диагностики",
        "Матрица неисправностей",
        "Гарантия на работы и детали",
    ),
    "diagnostics": (
        "Сначала находим причину, потом называем цену",
        "Протокол диагностики",
        "Диагностика — 1 500 ₽",
    ),
    "prices": (
        "Стоимость работ без скрытых доплат",
        "Выезд и диагностика",
        "Гарантия до 12 месяцев",
    ),
    "request": (
        "Вызвать мастера на удобное время",
        "Назначенный специалист",
        "Подтверждение выезда",
    ),
}

_ASSETS_BY_ROUTE = {
    "cover": ("repair_process",),
    "boiler-repair": ("boiler_room",),
    "diagnostics": ("diagnostic_tool",),
    "prices": ("burner_closeup",),
    "request": ("technician_portrait", "warm_home"),
}


def _render(project, shot, assets):
    module = import_module("portfolio.kwork_pack.sites.teplodom")
    return module.render(project, shot, assets)


def _assets(project):
    return {
        asset.key: f'/assets/{asset.filename}?project=teplodom&mode="preview"'
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


def test_teplodom_renders_five_distinct_routes_with_exact_service_copy():
    project = get_project("teplodom")
    pages = [_render(project, shot, _assets(project)) for shot in project.shots]

    assert all(isinstance(page, RenderedPage) for page in pages)
    assert [shot.key for shot in project.shots] == list(_ROUTE_COPY)
    assert len({page.html for page in pages}) == 5
    for shot, page in zip(project.shots, pages):
        assert 'data-site="teplodom"' in page.html
        assert f'data-route="{shot.key}"' in page.html
        assert "ТеплоДом" in page.html
        assert "Ремонт газовых котлов" in page.html
        for fragment in _ROUTE_COPY[shot.key]:
            assert fragment in page.html


def test_teplodom_uses_each_route_owned_asset_exactly_once():
    project = get_project("teplodom")
    assets = _assets(project)
    pages = {
        shot.key: _render(project, shot, assets).html for shot in project.shots
    }

    for route, owned_keys in _ASSETS_BY_ROUTE.items():
        for key in owned_keys:
            source = escape(assets[key], quote=True)
            assert pages[route].count(source) == 1
            assert sum(page.count(source) for page in pages.values()) == 1


def test_teplodom_renderer_is_isolated_and_has_no_template_shortcuts():
    module = import_module("portfolio.kwork_pack.sites.teplodom")
    source = inspect.getsource(module)
    tree = ast.parse(source)
    imported_modules = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported_modules.update(
        node.module or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    )

    assert not any("portfolio.kwork_pack.sites." in name for name in imported_modules)
    assert "linear-gradient" not in source
    assert "radial-gradient" not in source
    assert "backdrop-filter" not in source
    assert "teplodom-service" not in source


def test_teplodom_css_locks_canvas_and_readable_type():
    project = get_project("teplodom")
    page = _render(project, project.shots[0], _assets(project))

    assert "height: 1120px" in page.css
    assert "overflow: hidden" in page.css
    assert "letter-spacing: 0" in page.css
    sizes = [int(value) for value in re.findall(r"font-size:\s*(\d+)px", page.css)]
    assert sizes
    assert min(sizes) >= 12


def test_teplodom_real_canvas_has_no_hidden_overflow(chrome_browser):
    project = get_project("teplodom")
    page = chrome_browser.new_page(viewport={"width": 1920, "height": 1280})
    try:
        for shot in project.shots:
            rendered = _render(project, shot, _assets(project))
            page.set_content(
                build_document(
                    project, shot, rendered.html, rendered.css, rendered.scripts
                )
            )
            canvas = page.locator(".td-page").evaluate(
                "root => ({height: root.getBoundingClientRect().height, scrollHeight: root.scrollHeight})"
            )
            assert canvas == {"height": 1120, "scrollHeight": 1120}
    finally:
        page.close()


def test_teplodom_diagnostics_updates_path_fee_and_safety(chrome_browser):
    project = get_project("teplodom")
    shot = next(shot for shot in project.shots if shot.key == "diagnostics")
    rendered = _render(project, shot, _assets(project))
    page = chrome_browser.new_page(viewport={"width": 1920, "height": 1280})
    try:
        page.set_content(
            build_document(
                project, shot, rendered.html, rendered.css, rendered.scripts
            )
        )
        geometry = page.locator(".td-page").bounding_box()
        choices = page.locator('[data-selectable="symptom"]')
        assert choices.count() == 4
        choices.nth(2).click()
        assert choices.nth(2).get_attribute("aria-pressed") == "true"
        result = page.locator("[data-diagnostic-result]").inner_text()
        assert "Датчик давления и насос" in result
        assert "1 500 ₽" in result
        assert "До проверки котёл не включать" in result
        assert page.locator(".td-page").bounding_box() == geometry
    finally:
        page.close()


def test_teplodom_prices_selects_service_and_updates_total(chrome_browser):
    project = get_project("teplodom")
    shot = next(shot for shot in project.shots if shot.key == "prices")
    rendered = _render(project, shot, _assets(project))
    page = chrome_browser.new_page(viewport={"width": 1920, "height": 1280})
    try:
        page.set_content(
            build_document(
                project, shot, rendered.html, rendered.css, rendered.scripts
            )
        )
        geometry = page.locator(".td-page").bounding_box()
        rows = page.locator('[data-selectable="price-service"]')
        assert rows.count() == 4
        rows.nth(3).click()
        assert rows.nth(3).get_attribute("aria-pressed") == "true"
        summary = page.locator("[data-price-summary]").inner_text()
        assert "Замена насоса" in summary
        assert "от 6 900 ₽" in summary
        assert "деталь согласуем отдельно" in summary
        assert page.locator(".td-page").bounding_box() == geometry
    finally:
        page.close()


def test_teplodom_request_updates_urgency_slot_and_master(chrome_browser):
    project = get_project("teplodom")
    shot = next(shot for shot in project.shots if shot.key == "request")
    rendered = _render(project, shot, _assets(project))
    page = chrome_browser.new_page(viewport={"width": 1920, "height": 1280})
    try:
        page.set_content(
            build_document(
                project, shot, rendered.html, rendered.css, rendered.scripts
            )
        )
        geometry = page.locator(".td-page").bounding_box()
        page.locator('[data-selectable="urgency"][data-value="today"]').click()
        page.locator('[data-selectable="slot"][data-value="18:00–20:00"]').click()
        summary = page.locator("[data-dispatch-summary]").inner_text()
        assert "Сегодня, 18:00–20:00" in summary
        assert "Алексей Мельников" in summary
        assert "Диагностика 1 500 ₽" in summary
        assert page.locator(".td-page").bounding_box() == geometry
    finally:
        page.close()
