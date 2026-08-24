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


_OKNA_ROUTE_COPY = {
    "cover": (
        "Пластиковые окна от производителя",
        "Расчёт за 1 минуту",
        "Качество в каждой детали",
    ),
    "windows": (
        "Выберите окно для вашей комнаты",
        "Сравнение стандартных конфигураций",
        "Тепло и тишина в цифрах",
    ),
    "calculator": (
        "Рассчитайте окно по вашим размерам",
        "Конфигурация заказа",
        "Что входит в стоимость",
    ),
    "profiles": (
        "Профиль определяет комфорт на годы",
        "Техническое сравнение профилей",
        "Паспорт материалов",
    ),
    "installation": (
        "Монтаж по ГОСТ без скрытых работ",
        "Выберите дату монтажа",
        "Акт приёмки и гарантия",
    ),
}

_OKNA_ASSETS_BY_ROUTE = {
    "cover": ("installer_portrait",),
    "windows": ("window_facade",),
    "calculator": ("bright_kitchen",),
    "profiles": ("profile_closeup",),
    "installation": ("glazing_process", "balcony_view"),
}


def _render_okna(project, shot, assets):
    module = import_module("portfolio.kwork_pack.sites.okna_sfera")
    return module.render(project, shot, assets)


def _okna_assets(project):
    return {
        asset.key: f'/assets/{asset.filename}?project=okna-sfera&mode="preview"'
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
    rendered = _render_okna(project, shot, assets)
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


def test_okna_sfera_renders_five_distinct_routes_with_exact_window_copy():
    project = get_project("okna-sfera")
    pages = [
        _render_okna(project, shot, _okna_assets(project))
        for shot in project.shots
    ]

    assert all(isinstance(page, RenderedPage) for page in pages)
    assert [shot.key for shot in project.shots] == list(_OKNA_ROUTE_COPY)
    assert len({page.html for page in pages}) == 5
    for shot, page in zip(project.shots, pages):
        assert 'data-site="okna-sfera"' in page.html
        assert f'data-route="{shot.key}"' in page.html
        assert "Окна Сфера" in page.html
        assert "Качество в каждой детали" in page.html
        for fragment in _OKNA_ROUTE_COPY[shot.key]:
            assert fragment in page.html


def test_okna_sfera_uses_each_route_owned_asset_exactly_once():
    project = get_project("okna-sfera")
    assets = _okna_assets(project)
    pages = {
        shot.key: _render_okna(project, shot, assets).html
        for shot in project.shots
    }

    for route, owned_keys in _OKNA_ASSETS_BY_ROUTE.items():
        for key in owned_keys:
            source = escape(assets[key], quote=True)
            assert pages[route].count(source) == 1
            assert sum(page.count(source) for page in pages.values()) == 1


@pytest.mark.parametrize(("shot_key", "owned_keys"), _OKNA_ASSETS_BY_ROUTE.items())
def test_okna_sfera_reports_a_missing_route_owned_asset(shot_key, owned_keys):
    project = get_project("okna-sfera")
    shot = next(item for item in project.shots if item.key == shot_key)
    assets = _okna_assets(project)
    missing_key = owned_keys[0]
    assets.pop(missing_key)

    with pytest.raises(
        KeyError, match=rf"okna-sfera.*{shot_key}.*{missing_key}"
    ):
        _render_okna(project, shot, assets)


def test_okna_sfera_rejects_other_projects_and_unknown_routes():
    project = get_project("okna-sfera")
    other = get_project("kvadrat-remonta")

    with pytest.raises(KeyError, match="okna-sfera renderer.*kvadrat-remonta"):
        _render_okna(other, other.shots[0], _okna_assets(project))

    unknown = replace(project.shots[0], key="unknown")
    with pytest.raises(ValueError, match="okna-sfera.*unknown"):
        _render_okna(project, unknown, _okna_assets(project))


def test_okna_sfera_has_stable_geometry_meaningful_lower_bands_and_urls():
    project = get_project("okna-sfera")
    pages = {
        shot.key: _render_okna(project, shot, _okna_assets(project))
        for shot in project.shots
    }
    combined = "\n".join(page.html + page.css for page in pages.values()).casefold()

    for fragment in (
        "height: 1120px",
        ".os-utility-header",
        ".os-cover-quality",
        ".os-windows-performance",
        ".os-calculator-included",
        ".os-profiles-passport",
        ".os-installation-handover",
    ):
        assert fragment.casefold() in combined
    for shot in project.shots:
        assert public_url(project, shot) == (
            f"https://okna-sfera.ru{shot.path}"
        )
    for forbidden in (
        "gradient",
        "border-radius",
        "overlay",
        "localhost",
        "lorem",
        "никита тихомиров",
    ):
        assert forbidden not in combined


def test_okna_sfera_cover_and_windows_controls_update_dependent_content(
    chrome_browser,
):
    project = get_project("okna-sfera")
    assets = _okna_assets(project)
    shots = {shot.key: shot for shot in project.shots}
    page = chrome_browser.new_page(viewport={"width": 1920, "height": 1280})
    try:
        _set_route(page, project, shots["cover"], assets)
        geometry = page.locator(".os-page").bounding_box()
        sashes = page.locator('[data-selectable="cover-sash"]')
        assert sashes.count() == 4
        sashes.nth(2).click()
        assert sashes.nth(2).get_attribute("aria-pressed") == "true"
        summary = page.locator(".os-cover-quote").inner_text()
        assert "Трёхстворчатое окно" in summary
        assert "2100 × 1400 мм" in summary
        assert "от 31 900 ₽" in summary
        assert "7 рабочих дней" in summary
        assert page.locator(".os-page").bounding_box() == geometry

        _set_route(page, project, shots["windows"], assets)
        geometry = page.locator(".os-page").bounding_box()
        rooms = page.locator('[data-selectable="window-room"]')
        openings = page.locator('[data-selectable="window-opening"]')
        rooms.nth(2).click()
        openings.nth(2).click()
        assert rooms.nth(2).get_attribute("aria-pressed") == "true"
        assert openings.nth(2).get_attribute("aria-pressed") == "true"
        specification = page.locator(".os-window-specification").inner_text()
        assert "Балкон" in specification
        assert "Поворотно-откидное" in specification
        assert "70 мм" in specification
        assert "40 дБ" in specification
        assert "от 28 600 ₽" in specification
        assert page.locator(".os-window-table tbody tr").count() == 3
        assert page.locator(".os-page").bounding_box() == geometry
    finally:
        page.close()


def test_okna_sfera_calculator_updates_price_term_and_materials(chrome_browser):
    project = get_project("okna-sfera")
    shot = next(item for item in project.shots if item.key == "calculator")
    page = chrome_browser.new_page(viewport={"width": 1920, "height": 1280})
    try:
        _set_route(page, project, shot, _okna_assets(project))
        geometry = page.locator(".os-page").bounding_box()
        openings = page.locator('[data-selectable="calculator-opening"]')
        profiles = page.locator('[data-selectable="calculator-profile"]')
        glazing = page.locator('[data-selectable="calculator-glazing"]')
        openings.nth(2).click()
        page.locator("[data-calculator-width]").fill("2100")
        page.locator("[data-calculator-height]").fill("1500")
        profiles.nth(2).click()
        glazing.nth(2).click()
        page.locator("[data-calculator-installation]").check()

        assert openings.nth(2).get_attribute("aria-pressed") == "true"
        assert profiles.nth(2).get_attribute("aria-pressed") == "true"
        assert glazing.nth(2).get_attribute("aria-pressed") == "true"
        result = page.locator(".os-calculator-summary").inner_text()
        included = page.locator(".os-calculator-included").inner_text()
        assert "86 300 ₽" in result
        assert "13 рабочих дней" in result
        assert "Sfera 82 · 7 камер" in result
        assert "52 мм · 46 дБ" in result
        assert "Анкерные пластины · 18 шт." in included
        assert "Монтажная пена · 3 баллона" in included
        assert "Подоконник · 2100 мм" in included
        assert page.locator(".os-page").bounding_box() == geometry
    finally:
        page.close()


def test_okna_sfera_profiles_and_installation_update_engineering_summaries(
    chrome_browser,
):
    project = get_project("okna-sfera")
    assets = _okna_assets(project)
    shots = {shot.key: shot for shot in project.shots}
    page = chrome_browser.new_page(viewport={"width": 1920, "height": 1280})
    try:
        _set_route(page, project, shots["profiles"], assets)
        geometry = page.locator(".os-page").bounding_box()
        profiles = page.locator('[data-selectable="profile-model"]')
        profiles.nth(2).click()
        assert profiles.nth(2).get_attribute("aria-pressed") == "true"
        passport = page.locator(".os-profiles-passport").inner_text()
        assert "Sfera 82" in passport
        assert "7 камер" in passport
        assert "Стеклопакет до 52 мм" in passport
        assert "0,92 м²·°C/Вт" in passport
        assert "46 дБ" in passport
        assert page.locator(".os-page").bounding_box() == geometry

        _set_route(page, project, shots["installation"], assets)
        geometry = page.locator(".os-page").bounding_box()
        dates = page.locator('[data-selectable="installation-date"]')
        times = page.locator('[data-selectable="installation-time"]')
        dates.nth(2).click()
        times.nth(2).click()
        assert dates.nth(2).get_attribute("aria-pressed") == "true"
        assert times.nth(2).get_attribute("aria-pressed") == "true"
        visit = page.locator(".os-installation-visit").inner_text()
        assert "29 августа · 15:00–18:00" in visit
        assert "Бригада № 4" in visit
        assert "5–6 часов" in visit
        assert "Слот закреплён на 15 минут" in visit
        assert page.locator(".os-page").bounding_box() == geometry
    finally:
        page.close()


def test_okna_sfera_text_is_at_least_12px_and_canvas_is_stable_in_chrome(
    chrome_browser,
):
    project = get_project("okna-sfera")
    assets = _okna_assets(project)
    page = chrome_browser.new_page(viewport={"width": 1920, "height": 1280})
    try:
        for shot in project.shots:
            _set_route(page, project, shot, assets)
            audit = page.locator(".os-page").evaluate(
                """root => {
                  const box = root.getBoundingClientRect();
                  const small = [...root.querySelectorAll('*')].filter((node) => {
                    const style = getComputedStyle(node);
                    const hasText = [...node.childNodes].some(
                      (child) => child.nodeType === Node.TEXT_NODE && child.textContent.trim()
                    );
                    return hasText && style.display !== 'none' &&
                      style.visibility !== 'hidden' && parseFloat(style.fontSize) < 12;
                  }).map((node) => ({text: node.textContent.trim(), size: getComputedStyle(node).fontSize}));
                  return {
                    width: box.width,
                    height: box.height,
                    scrollHeight: root.scrollHeight,
                    small,
                  };
                }"""
            )
            assert audit["width"] == 1834
            assert audit["height"] == 1120
            assert audit["scrollHeight"] == 1120
            assert audit["small"] == []
    finally:
        page.close()


def test_okna_sfera_module_is_isolated_from_all_other_site_renderers():
    project = get_project("okna-sfera")
    renderer = import_module("portfolio.kwork_pack.sites.okna_sfera").render
    _render_okna(project, project.shots[0], _okna_assets(project))
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
    for foreign_prefix in ("da-", "vk-", "th-", "sh-", "kr-"):
        for marker in (f".{foreign_prefix}", f'"{foreign_prefix}', f" {foreign_prefix}"):
            assert marker not in source
    assert not any(
        name.endswith(
            (
                "dentalea",
                "ventkontur",
                "tochka_hoda",
                "syr_hleb",
                "kvadrat_remonta",
                "commercial",
                "leadgen",
                "complex",
            )
        )
        for name in imported_modules
    )
