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
        "Переезд квартиры без суеты и повреждений",
        "Предварительная стоимость",
        "Пять шагов до новой квартиры",
    ),
    "apartment-moving": (
        "Квартирный переезд с ответственностью за каждую вещь",
        "Опись комнаты",
        "План переезда по времени",
    ),
    "calculator": (
        "Рассчитайте переезд до приезда оценщика",
        "Состав расчёта",
        "Ближайшее окно погрузки",
    ),
    "packing": (
        "Упакуем вещи по описи, а не на глаз",
        "Маркировка коробки",
        "Ответственность за упаковку",
    ),
    "route": (
        "Маршрут переезда без сюрпризов во дворе",
        "Контрольные точки маршрута",
        "Подтверждение прибытия",
    ),
}

_ASSETS_BY_ROUTE = {
    "cover": ("moving_van",),
    "apartment-moving": ("packed_living_room",),
    "calculator": ("boxes_detail",),
    "packing": ("packer_portrait",),
    "route": ("route_map_photo", "new_home"),
}


def _render(project, shot, assets):
    module = import_module("portfolio.kwork_pack.sites.pereezd_prosto")
    return module.render(project, shot, assets)


def _assets(project):
    return {
        asset.key: f'/assets/{asset.filename}?project=pereezd-prosto&mode="preview"'
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


def test_pereezd_renders_five_distinct_routes_with_exact_moving_copy():
    project = get_project("pereezd-prosto")
    pages = [_render(project, shot, _assets(project)) for shot in project.shots]

    assert all(isinstance(page, RenderedPage) for page in pages)
    assert [shot.key for shot in project.shots] == list(_ROUTE_COPY)
    assert len({page.html for page in pages}) == 5
    for shot, page in zip(project.shots, pages):
        assert 'data-site="pereezd-prosto"' in page.html
        assert f'data-route="{shot.key}"' in page.html
        assert "Бережный" in page.html
        assert "переезд" in page.html.lower()
        for fragment in _ROUTE_COPY[shot.key]:
            assert fragment in page.html


def test_pereezd_uses_each_route_owned_asset_exactly_once():
    project = get_project("pereezd-prosto")
    assets = _assets(project)
    pages = {
        shot.key: _render(project, shot, assets).html for shot in project.shots
    }
    for route, owned_keys in _ASSETS_BY_ROUTE.items():
        for key in owned_keys:
            source = escape(assets[key], quote=True)
            assert pages[route].count(source) == 1
            assert sum(page.count(source) for page in pages.values()) == 1


def test_pereezd_renderer_is_isolated_and_avoids_template_shortcuts():
    module = import_module("portfolio.kwork_pack.sites.pereezd_prosto")
    source = inspect.getsource(module)
    tree = ast.parse(source)
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imports.update(
        node.module or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    )
    assert not any("portfolio.kwork_pack.sites." in name for name in imports)
    assert "linear-gradient" not in source
    assert "radial-gradient" not in source
    assert "backdrop-filter" not in source
    assert "travel" not in source.lower()


def test_pereezd_css_locks_canvas_and_readable_type():
    project = get_project("pereezd-prosto")
    page = _render(project, project.shots[0], _assets(project))
    assert "height: 1120px" in page.css
    assert "overflow: hidden" in page.css
    assert "letter-spacing: 0" in page.css
    sizes = [int(value) for value in re.findall(r"font-size:\s*(\d+)px", page.css)]
    assert sizes and min(sizes) >= 12


def test_pereezd_real_canvas_has_no_hidden_overflow(chrome_browser):
    project = get_project("pereezd-prosto")
    page = chrome_browser.new_page(viewport={"width": 1920, "height": 1280})
    try:
        for shot in project.shots:
            rendered = _render(project, shot, _assets(project))
            page.set_content(build_document(project, shot, rendered.html, rendered.css, rendered.scripts))
            canvas = page.locator(".bp-page").evaluate(
                "root => ({height: root.getBoundingClientRect().height, scrollHeight: root.scrollHeight})"
            )
            assert canvas == {"height": 1120, "scrollHeight": 1120}
    finally:
        page.close()


def test_pereezd_cover_mode_updates_quote_and_vehicle(chrome_browser):
    project = get_project("pereezd-prosto")
    shot = next(shot for shot in project.shots if shot.key == "cover")
    rendered = _render(project, shot, _assets(project))
    page = chrome_browser.new_page(viewport={"width": 1920, "height": 1280})
    try:
        page.set_content(build_document(project, shot, rendered.html, rendered.css, rendered.scripts))
        geometry = page.locator(".bp-page").bounding_box()
        page.locator('[data-selectable="cover-mode"][data-value="volume"]').click()
        summary = page.locator("[data-cover-quote]").inner_text()
        assert "14 м³" in summary
        assert "Газель 4 м" in summary
        assert "от 18 700 ₽" in summary
        assert page.locator(".bp-page").bounding_box() == geometry
    finally:
        page.close()


def test_pereezd_package_updates_assigned_crew_without_contradictions(chrome_browser):
    project = get_project("pereezd-prosto")
    shot = next(shot for shot in project.shots if shot.key == "apartment-moving")
    rendered = _render(project, shot, _assets(project))
    page = chrome_browser.new_page(viewport={"width": 1920, "height": 1280})
    try:
        page.set_content(build_document(project, shot, rendered.html, rendered.css, rendered.scripts))
        geometry = page.locator(".bp-page").bounding_box()
        default_state = page.locator(".bp-apartment-work").inner_text()
        assert "Переезд · 2 грузчика + Газель 3 м" in default_state
        assert page.locator("[data-package-crew]").inner_text() == "2"
        assert page.locator("[data-package-truck]").inner_text() == "Газель 3 м"

        page.locator('[data-selectable="move-package"][data-value="full"]').click()
        state = page.locator(".bp-apartment-work").inner_text()
        assert "Под ключ · 4 специалиста + Газель 5 м" in state
        assert page.locator("[data-package-crew]").inner_text() == "4"
        assert page.locator("[data-package-truck]").inner_text() == "Газель 5 м"
        assert page.locator(".bp-page").bounding_box() == geometry
    finally:
        page.close()


def test_pereezd_calculator_updates_full_operational_summary(chrome_browser):
    project = get_project("pereezd-prosto")
    shot = next(shot for shot in project.shots if shot.key == "calculator")
    rendered = _render(project, shot, _assets(project))
    page = chrome_browser.new_page(viewport={"width": 1920, "height": 1280})
    try:
        page.set_content(build_document(project, shot, rendered.html, rendered.css, rendered.scripts))
        geometry = page.locator(".bp-page").bounding_box()
        page.locator('[data-stepper="rooms"] [data-action="plus"]').click()
        page.locator('[data-selectable="lift"][data-value="none"]').click()
        page.locator('[data-extra="packing"]').check()
        summary = page.locator("[data-move-summary]").inner_text()
        assert "3 комнаты" in summary
        assert "3 грузчика" in summary
        assert "Газель 5 м" in summary
        assert "5–6 часов" in summary
        assert "24 900 ₽" in summary
        assert page.locator(".bp-page").bounding_box() == geometry
    finally:
        page.close()


def test_pereezd_calculator_keeps_summary_clear_and_declines_five_rooms(chrome_browser):
    project = get_project("pereezd-prosto")
    shot = next(shot for shot in project.shots if shot.key == "calculator")
    rendered = _render(project, shot, _assets(project))
    page = chrome_browser.new_page(viewport={"width": 1920, "height": 1280})
    try:
        page.set_content(build_document(project, shot, rendered.html, rendered.css, rendered.scripts))
        for _ in range(3):
            page.locator('[data-stepper="rooms"] [data-action="plus"]').click()

        assert "5 комнат" in page.locator("[data-summary-title]").inner_text()
        summary = page.locator("[data-move-summary]").bounding_box()
        breakdown = page.locator(".bp-breakdown").bounding_box()
        assert summary["y"] + summary["height"] <= breakdown["y"]
    finally:
        page.close()


def test_pereezd_calculator_uses_every_input_and_reconciles_breakdown(chrome_browser):
    project = get_project("pereezd-prosto")
    shot = next(shot for shot in project.shots if shot.key == "calculator")
    rendered = _render(project, shot, _assets(project))
    page = chrome_browser.new_page(viewport={"width": 1920, "height": 1280})
    try:
        page.set_content(build_document(project, shot, rendered.html, rendered.css, rendered.scripts))
        geometry = page.locator(".bp-page").bounding_box()
        page.locator('[data-selectable="calc-mode"][data-value="volume"]').click()
        page.locator("[data-distance]").fill("35")
        page.locator("[data-origin-floor]").fill("15")
        page.locator("[data-destination-floor]").fill("20")
        page.locator("[data-move-date]").fill("30 августа")
        page.locator('[data-selectable="lift"][data-value="none"]').click()
        page.locator('[data-extra="packing"]').check()

        summary = page.locator("[data-move-summary]").inner_text()
        assert "14 м³ · 35 км" in summary
        assert "3 грузчика" in summary
        assert "Газель 4 м" in summary
        assert "30 августа · 16:30" in summary
        assert page.locator("[data-distance-label]").inner_text() == "35 км"

        parts = page.locator("[data-breakdown-value]").all_inner_texts()
        assert len(parts) == 3
        part_total = sum(int(re.sub(r"\D", "", value)) for value in parts)
        summary_total = int(
            re.sub(r"\D", "", page.locator("[data-summary-price]").inner_text())
        )
        assert part_total == summary_total
        assert page.locator(".bp-page").bounding_box() == geometry
    finally:
        page.close()


def test_pereezd_packing_updates_materials_and_inventory(chrome_browser):
    project = get_project("pereezd-prosto")
    shot = next(shot for shot in project.shots if shot.key == "packing")
    rendered = _render(project, shot, _assets(project))
    page = chrome_browser.new_page(viewport={"width": 1920, "height": 1280})
    try:
        page.set_content(build_document(project, shot, rendered.html, rendered.css, rendered.scripts))
        geometry = page.locator(".bp-page").bounding_box()
        page.locator('[data-fragile="dishes"]').check()
        page.locator('[data-fragile="art"]').check()
        summary = page.locator("[data-packing-summary]").inner_text()
        assert "24 коробки" in summary
        assert "7 хрупких мест" in summary
        assert "Пломбы: 7" in summary
        assert page.locator(".bp-page").bounding_box() == geometry
    finally:
        page.close()


def test_pereezd_route_updates_checkpoint_and_arrival(chrome_browser):
    project = get_project("pereezd-prosto")
    shot = next(shot for shot in project.shots if shot.key == "route")
    rendered = _render(project, shot, _assets(project))
    page = chrome_browser.new_page(viewport={"width": 1920, "height": 1280})
    try:
        page.set_content(build_document(project, shot, rendered.html, rendered.css, rendered.scripts))
        geometry = page.locator(".bp-page").bounding_box()
        page.locator('[data-checkpoint="parking"]').check()
        page.locator('[data-selectable="route-slot"][data-value="11:30"]').click()
        summary = page.locator("[data-route-summary]").inner_text()
        assert "Парковка согласована" in summary
        assert "Прибытие к новому адресу" in summary
        assert page.locator("[data-arrival]").inner_text() == "11:30"
        assert page.locator("[data-timeline-time]").inner_text() == "11:30"
        assert "Прибытие и парковка" == page.locator("[data-timeline-arrival]").inner_text()
        arrival_label = page.locator("[data-arrival-row] span").bounding_box()
        arrival_value = page.locator("[data-arrival]").bounding_box()
        assert arrival_label["x"] + arrival_label["width"] < arrival_value["x"]
        assert "Газель 5 м · бригада 3 человека" in summary

        page.locator('[data-checkpoint="elevator"]').uncheck()
        page.locator('[data-checkpoint="arch"]').uncheck()
        summary = page.locator("[data-route-summary]").inner_text()
        route = page.locator(".bp-address-sheet").inner_text()
        assert "Лифт требует подтверждения" in summary
        assert "Арка требует проверки" in summary
        assert "18 км · 62 минуты в пути" in route

        page.locator('[data-checkpoint="arch"]').check()
        route = page.locator(".bp-address-sheet").inner_text()
        assert "18 км · 56 минут в пути" in route
        assert page.locator(".bp-page").bounding_box() == geometry
    finally:
        page.close()
