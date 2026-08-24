import ast
from dataclasses import replace
from html import escape
from importlib import import_module
import inspect

import pytest
from playwright.sync_api import sync_playwright

from portfolio.kwork_pack.catalog import get_project
from portfolio.kwork_pack.shell import build_document
from portfolio.kwork_pack.sites.runtime import RenderedPage


_ROUTE_COPY = {
    "cover": (
        "Стоматология, где спокойно лечиться",
        "План лечения до начала работ",
        "Первичная консультация",
    ),
    "implantation": (
        "Имплантация с поэтапным планом",
        "Диагностика и 3D-планирование",
        "Рассрочка без переплат",
    ),
    "booking": (
        "Выберите удобное время приёма",
        "Анна Михайлова",
        "Подтвердить запись",
    ),
    "case-study": (
        "До и после: восстановили улыбку",
        "8 недель лечения",
        "Клинические показатели",
    ),
    "prices": (
        "Цены и свободные окна врачей",
        "Имплантация",
        "Ближайшая запись",
    ),
}

_ASSETS_BY_ROUTE = {
    "cover": ("consultation_room",),
    "implantation": ("treatment_detail",),
    "booking": ("clinic_exterior",),
    "case-study": ("smile_case_before", "smile_case_after"),
    "prices": ("doctor_portrait",),
}


def _render(project, shot, assets):
    module = import_module("portfolio.kwork_pack.sites.dentalea")
    return module.render(project, shot, assets)


def _assets(project):
    return {
        asset.key: f'/assets/{asset.filename}?project=dentalea&mode="preview"'
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


def test_dentalea_renders_five_distinct_routes_with_exact_clinical_copy():
    project = get_project("dentalea")
    pages = [_render(project, shot, _assets(project)) for shot in project.shots]

    assert all(isinstance(page, RenderedPage) for page in pages)
    assert [shot.key for shot in project.shots] == list(_ROUTE_COPY)
    assert len({page.html for page in pages}) == 5
    for shot, page in zip(project.shots, pages):
        assert 'data-site="dentalea"' in page.html
        assert f'data-route="{shot.key}"' in page.html
        assert "ДЕНТАЛЕЯ" in page.html
        assert "стоматологическая клиника" in page.html
        for fragment in _ROUTE_COPY[shot.key]:
            assert fragment in page.html


def test_dentalea_uses_each_owned_asset_once_on_its_assigned_route():
    project = get_project("dentalea")
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
def test_dentalea_reports_a_missing_route_owned_asset(shot_key, owned_keys):
    project = get_project("dentalea")
    shot = next(item for item in project.shots if item.key == shot_key)
    assets = _assets(project)
    missing_key = owned_keys[0]
    assets.pop(missing_key)

    with pytest.raises(KeyError, match=rf"dentalea.*{shot_key}.*{missing_key}"):
        _render(project, shot, assets)


def test_dentalea_rejects_other_projects_and_unknown_routes():
    project = get_project("dentalea")
    other = get_project("ventkontur")

    with pytest.raises(KeyError, match="dentalea renderer.*ventkontur"):
        _render(other, other.shots[0], _assets(project))

    unknown = replace(project.shots[0], key="unknown")
    with pytest.raises(ValueError, match="dentalea.*unknown"):
        _render(project, unknown, _assets(project))


def test_dentalea_has_stable_desktop_geometry_and_route_specific_structure():
    project = get_project("dentalea")
    pages = [_render(project, shot, _assets(project)) for shot in project.shots]
    combined = "\n".join(page.html + page.css for page in pages).casefold()

    for fragment in (
        "height: 1120px",
        ".da-header",
        ".da-cover-hero",
        ".da-implant-layout",
        ".da-booking-layout",
        ".da-case-evidence",
        ".da-price-matrix",
        "font-size: 12px",
    ):
        assert fragment.casefold() in combined
    for forbidden in ("linear-gradient", "localhost", "lorem", "demo", "никита тихомиров"):
        assert forbidden not in combined


def test_dentalea_booking_and_prices_fill_their_lower_viewport_with_real_detail():
    project = get_project("dentalea")
    pages = {
        shot.key: _render(project, shot, _assets(project)).html
        for shot in project.shots
    }

    assert 'class="da-booking-assurance"' in pages["booking"]
    assert "Что взять на приём" in pages["booking"]
    assert 'class="da-clinic-details"' in pages["booking"]
    assert 'class="da-prices-proof"' in pages["prices"]
    assert 'class="da-prices-proof-grid"' in pages["prices"]
    assert "Что входит в стоимость" in pages["prices"]
    assert "Срок ответа по плану" in pages["prices"]

    booking_css = _render(
        project,
        next(shot for shot in project.shots if shot.key == "booking"),
        _assets(project),
    ).css
    assert ".da-booking-main { display: flex; flex-direction: column; }" in booking_css


def test_dentalea_implantation_fills_open_bands_with_clinical_and_financing_detail():
    project = get_project("dentalea")
    shot = next(item for item in project.shots if item.key == "implantation")
    page = _render(project, shot, _assets(project))

    for fragment in (
        'class="da-implant-candidacy"',
        "Диагностические факты",
        "Что входит в план",
        "Риски, которые обсуждаем заранее",
        'class="da-implant-checkpoint"',
        "Клиническая контрольная точка",
        "Лист результата",
        'class="da-financing-comparison"',
        "260 000 ₽",
        "от 21 667 ₽ в месяц",
        "Первый платёж через 30 дней",
        'class="da-financing-cta"',
        "Рассчитать свой план",
    ):
        assert fragment in page.html


def test_dentalea_booking_reason_and_confirmation_update_summary_in_chrome(
    chrome_browser,
):
    project = get_project("dentalea")
    booking = next(item for item in project.shots if item.key == "booking")

    page = chrome_browser.new_page(viewport={"width": 1920, "height": 1280})
    try:
        booking_page = _render(project, booking, _assets(project))
        page.set_content(
            build_document(
                project,
                booking,
                booking_page.html,
                booking_page.css,
                booking_page.scripts,
            )
        )
        reasons = page.locator('[data-selectable="appointment-reason"]')
        methods = page.locator('[data-selectable="confirmation-method"]')
        assert reasons.count() == 4
        assert methods.count() == 2

        reasons.nth(2).click()
        methods.nth(1).click()
        assert reasons.nth(2).get_attribute("aria-pressed") == "true"
        assert methods.nth(1).get_attribute("aria-pressed") == "true"
        assert "Имплантация" in page.locator(".da-booking-summary-reason").inner_text()
        assert "SMS" in page.locator(".da-booking-summary-confirmation").inner_text()
        assert page.locator('[data-consent="appointment"]').is_checked()
    finally:
        page.close()


def test_dentalea_case_timeline_is_fully_inside_the_desktop_page_in_chrome(
    chrome_browser,
):
    project = get_project("dentalea")
    case_study = next(item for item in project.shots if item.key == "case-study")

    page = chrome_browser.new_page(viewport={"width": 1920, "height": 1280})
    try:
        rendered = _render(project, case_study, _assets(project))
        page.set_content(
            build_document(
                project,
                case_study,
                rendered.html,
                rendered.css,
                rendered.scripts,
            )
        )
        root = page.locator(".da-page").bounding_box()
        timeline = page.locator(".da-case-bottom").bounding_box()
        assert root is not None
        assert timeline is not None
        assert timeline["y"] + timeline["height"] <= root["y"] + root["height"]
        assert "Контроль состояния через 14 дней" in page.locator(
            ".da-case-bottom"
        ).inner_text()
    finally:
        page.close()


def test_dentalea_prices_conditions_fill_the_lower_desktop_page_in_chrome(
    chrome_browser,
):
    project = get_project("dentalea")
    prices = next(item for item in project.shots if item.key == "prices")

    page = chrome_browser.new_page(viewport={"width": 1920, "height": 1280})
    try:
        rendered = _render(project, prices, _assets(project))
        page.set_content(
            build_document(
                project,
                prices,
                rendered.html,
                rendered.css,
                rendered.scripts,
            )
        )
        root = page.locator(".da-page").bounding_box()
        conditions_locator = page.locator(".da-prices-proof")
        conditions = conditions_locator.bounding_box()
        assert root is not None
        assert conditions is not None
        assert conditions["y"] + conditions["height"] >= root["y"] + root["height"] - 24
        assert "До оплаты вы видите полную смету" in conditions_locator.inner_text()
        assert page.locator(".da-prices-proof-footer button").inner_text() == "Получить смету"
    finally:
        page.close()


def test_dentalea_semantic_controls_drive_booking_and_price_content_in_chrome(
    chrome_browser,
):
    project = get_project("dentalea")
    assets = _assets(project)
    booking = next(shot for shot in project.shots if shot.key == "booking")
    prices = next(shot for shot in project.shots if shot.key == "prices")

    page = chrome_browser.new_page(viewport={"width": 1920, "height": 1280})
    try:
        booking_page = _render(project, booking, assets)
        page.set_content(
            build_document(
                project,
                booking,
                booking_page.html,
                booking_page.css,
                booking_page.scripts,
            )
        )
        times = page.locator('[data-selectable="appointment-time"]')
        assert times.count() == 4
        times.nth(2).click()
        assert times.nth(2).get_attribute("aria-pressed") == "true"
        assert "16:30" in page.locator(".da-booking-summary-time").inner_text()
        assert "16:30" in page.locator(".da-booking-summary").inner_text()

        price_page = _render(project, prices, assets)
        page.set_content(
            build_document(
                project,
                prices,
                price_page.html,
                price_page.css,
                price_page.scripts,
            )
        )
        categories = page.locator('[data-selectable="price-category"]')
        assert categories.count() == 3
        assert page.locator(".da-price-matrix tbody tr").count() == 7
        assert page.locator(".da-availability-schedule li").count() == 3
        categories.nth(1).click()
        assert categories.nth(1).get_attribute("aria-pressed") == "true"
        assert "Хирургия" in page.locator(".da-price-matrix h2").inner_text()
        assert "Завтра, 11:30" in page.locator(".da-availability").inner_text()
        assert page.locator(".da-price-matrix tbody tr").count() == 7
        assert "Сегодня, 19:00" in page.locator(".da-availability-schedule").inner_text()
    finally:
        page.close()


def test_dentalea_module_is_isolated_from_other_site_renderers():
    project = get_project("dentalea")
    renderer = import_module("portfolio.kwork_pack.sites.dentalea").render
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
    assert not any(
        name.endswith(("tochka_hoda", "commercial", "leadgen", "complex"))
        for name in imported_modules
    )


_VENTKONTUR_ROUTE_COPY = {
    "cover": (
        "Промышленная вентиляция под параметры объекта",
        "Расчёт, поставка и ввод в эксплуатацию",
        "Оборудование в производстве",
    ),
    "catalog": (
        "Каталог вентиляционных установок",
        "Сравнение характеристик",
        "VK-AHU 45",
    ),
    "selection": (
        "Подбор по расходу и давлению",
        "Расчётная точка системы",
        "VK-AHU 45",
    ),
    "projects": (
        "Вентиляция цеха без остановки производства",
        "Подтверждённые показатели",
        "18% снижения энергопотребления",
    ),
    "service": (
        "Сервисная заявка VK-2481",
        "График обслуживания",
        "Инженер назначен",
    ),
}

_VENTKONTUR_ASSETS_BY_ROUTE = {
    "cover": ("air_handling_unit",),
    "catalog": ("factory_rooftop",),
    "selection": ("control_panel",),
    "projects": ("project_hall",),
    "service": ("engineer_portrait", "duct_installation"),
}


def _render_ventkontur(project, shot, assets):
    module = import_module("portfolio.kwork_pack.sites.ventkontur")
    return module.render(project, shot, assets)


def _ventkontur_assets(project):
    return {
        asset.key: f'/assets/{asset.filename}?project=ventkontur&mode="preview"'
        for asset in project.assets
    }


def test_ventkontur_renders_five_distinct_routes_with_exact_b2b_copy():
    project = get_project("ventkontur")
    pages = [
        _render_ventkontur(project, shot, _ventkontur_assets(project))
        for shot in project.shots
    ]

    assert all(isinstance(page, RenderedPage) for page in pages)
    assert [shot.key for shot in project.shots] == list(_VENTKONTUR_ROUTE_COPY)
    assert len({page.html for page in pages}) == 5
    for shot, page in zip(project.shots, pages):
        assert 'data-site="ventkontur"' in page.html
        assert f'data-route="{shot.key}"' in page.html
        assert "ВентКонтур" in page.html
        assert "промышленная вентиляция" in page.html
        for fragment in _VENTKONTUR_ROUTE_COPY[shot.key]:
            assert fragment in page.html


def test_ventkontur_uses_each_route_owned_asset_exactly_once():
    project = get_project("ventkontur")
    assets = _ventkontur_assets(project)
    pages = {
        shot.key: _render_ventkontur(project, shot, assets).html
        for shot in project.shots
    }

    for route, owned_keys in _VENTKONTUR_ASSETS_BY_ROUTE.items():
        for key in owned_keys:
            source = escape(assets[key], quote=True)
            assert pages[route].count(source) == 1
            assert sum(page.count(source) for page in pages.values()) == 1


@pytest.mark.parametrize(
    ("shot_key", "owned_keys"), _VENTKONTUR_ASSETS_BY_ROUTE.items()
)
def test_ventkontur_reports_a_missing_route_owned_asset(shot_key, owned_keys):
    project = get_project("ventkontur")
    shot = next(item for item in project.shots if item.key == shot_key)
    assets = _ventkontur_assets(project)
    missing_key = owned_keys[0]
    assets.pop(missing_key)

    with pytest.raises(KeyError, match=rf"ventkontur.*{shot_key}.*{missing_key}"):
        _render_ventkontur(project, shot, assets)


def test_ventkontur_rejects_other_projects_and_unknown_routes():
    project = get_project("ventkontur")
    other = get_project("dentalea")

    with pytest.raises(KeyError, match="ventkontur renderer.*dentalea"):
        _render_ventkontur(other, other.shots[0], _ventkontur_assets(project))

    unknown = replace(project.shots[0], key="unknown")
    with pytest.raises(ValueError, match="ventkontur.*unknown"):
        _render_ventkontur(project, unknown, _ventkontur_assets(project))


def test_ventkontur_has_industrial_geometry_and_meaningful_lower_bands():
    project = get_project("ventkontur")
    pages = {
        shot.key: _render_ventkontur(project, shot, _ventkontur_assets(project))
        for shot in project.shots
    }
    combined = "\n".join(page.html + page.css for page in pages.values()).casefold()

    for fragment in (
        "height: 1120px",
        ".vk-utility-header",
        ".vk-catalog-header",
        ".vk-cover-products",
        ".vk-catalog-comparison",
        ".vk-selection-result",
        ".vk-project-evidence",
        ".vk-service-dispatch",
    ):
        assert fragment.casefold() in combined
    for forbidden in (
        "gradient",
        "border-radius",
        "overlay",
        "localhost",
        "lorem",
        "никита тихомиров",
    ):
        assert forbidden not in combined


def test_ventkontur_semantic_workflows_update_dependent_content_in_chrome(
    chrome_browser,
):
    project = get_project("ventkontur")
    assets = _ventkontur_assets(project)
    shots = {shot.key: shot for shot in project.shots}
    page = chrome_browser.new_page(viewport={"width": 1920, "height": 1280})
    try:
        catalog = _render_ventkontur(project, shots["catalog"], assets)
        page.set_content(
            build_document(
                project,
                shots["catalog"],
                catalog.html,
                catalog.css,
                catalog.scripts,
            )
        )
        catalog_geometry = page.locator(".vk-page").bounding_box()
        sectors = page.locator('[data-selectable="catalog-sector"]')
        assert sectors.count() == 3
        sectors.nth(2).click()
        assert sectors.nth(2).get_attribute("aria-pressed") == "true"
        assert page.locator(
            '[data-selectable="catalog-sector"][aria-pressed="true"]'
        ).count() == 1
        assert "VK-HYG 30" in page.locator(".vk-catalog-table tbody").inner_text()
        assert "Пищевые производства" in page.locator(
            ".vk-catalog-comparison"
        ).inner_text()
        assert page.locator(".vk-page").bounding_box() == catalog_geometry

        selection = _render_ventkontur(project, shots["selection"], assets)
        page.set_content(
            build_document(
                project,
                shots["selection"],
                selection.html,
                selection.css,
                selection.scripts,
            )
        )
        selection_geometry = page.locator(".vk-page").bounding_box()
        duties = page.locator('[data-selectable="selection-duty"]')
        assert duties.count() == 3
        duties.nth(2).click()
        assert duties.nth(2).get_attribute("aria-pressed") == "true"
        page.locator("[data-airflow]").fill("26000")
        page.locator("[data-pressure]").fill("980")
        assert page.locator(".vk-selection-model").inner_text() == "VK-AHU 60"
        result_text = page.locator(".vk-selection-result").inner_text()
        assert "26 000 м³/ч" in result_text
        assert "980 Па" in result_text
        assert "Резерв по расходу 15%" in result_text
        assert page.locator(".vk-page").bounding_box() == selection_geometry

        projects = _render_ventkontur(project, shots["projects"], assets)
        page.set_content(
            build_document(
                project,
                shots["projects"],
                projects.html,
                projects.css,
                projects.scripts,
            )
        )
        sectors = page.locator('[data-selectable="project-sector"]')
        assert sectors.count() == 3
        sectors.nth(1).click()
        assert sectors.nth(1).get_attribute("aria-pressed") == "true"
        evidence = page.locator(".vk-project-evidence").inner_text()
        assert "Фармацевтический корпус" in evidence
        assert "ISO 8" in evidence
        assert "48 точек контроля" in evidence

        service = _render_ventkontur(project, shots["service"], assets)
        page.set_content(
            build_document(
                project,
                shots["service"],
                service.html,
                service.css,
                service.scripts,
            )
        )
        service_geometry = page.locator(".vk-page").bounding_box()
        priorities = page.locator('[data-selectable="ticket-priority"]')
        statuses = page.locator('[data-selectable="ticket-status"]')
        assert priorities.count() == 3
        assert statuses.count() == 3
        priorities.nth(2).click()
        statuses.nth(1).click()
        ticket = page.locator(".vk-ticket-summary").inner_text()
        dispatch = page.locator(".vk-service-dispatch").inner_text()
        assert "Аварийная" in ticket
        assert "SLA 2 часа" in ticket
        assert "Бригада выехала" in dispatch
        assert "ETA 14:30" in dispatch
        assert statuses.nth(1).get_attribute("aria-pressed") == "true"
        assert page.locator(".vk-page").bounding_box() == service_geometry
    finally:
        page.close()


def test_ventkontur_computed_text_is_at_least_12px_and_canvas_is_stable_in_chrome(
    chrome_browser,
):
    project = get_project("ventkontur")
    assets = _ventkontur_assets(project)
    page = chrome_browser.new_page(viewport={"width": 1920, "height": 1280})
    try:
        for shot in project.shots:
            rendered = _render_ventkontur(project, shot, assets)
            page.set_content(
                build_document(
                    project,
                    shot,
                    rendered.html,
                    rendered.css,
                    rendered.scripts,
                )
            )
            audit = page.locator(".vk-page").evaluate(
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
            assert audit["height"] == 1120
            assert audit["scrollHeight"] == 1120
            assert audit["small"] == []
    finally:
        page.close()


def test_ventkontur_module_is_isolated_from_all_other_site_renderers():
    project = get_project("ventkontur")
    renderer = import_module("portfolio.kwork_pack.sites.ventkontur").render
    _render_ventkontur(project, project.shots[0], _ventkontur_assets(project))
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
    assert "da-" not in source
    assert "th-" not in source
    assert not any(
        name.endswith(
            ("dentalea", "tochka_hoda", "commercial", "leadgen", "complex")
        )
        for name in imported_modules
    )
