import inspect
from html import escape
from importlib import import_module

import pytest
from playwright.sync_api import sync_playwright

from portfolio.kwork_pack.catalog import get_project, public_url
from portfolio.kwork_pack.shell import build_document
from portfolio.kwork_pack.sites.runtime import RenderedPage


PROJECTS = (
    "sever-market",
    "modulprof",
    "doma-u-ozera",
    "praktika",
    "gruzcontrol",
)

ROUTE_COPY = {
    "sever-market": {
        "cover": ("Снаряжение для маршрута, а не для витрины", "Комплект маршрута"),
        "catalog": ("Туристическое снаряжение", "Подбор по условиям"),
        "tents": ("Палатки для ветра и дождя", "Сравнение палаток"),
        "cart": ("Корзина", "Резерв товара"),
        "delivery": ("Доставка снаряжения", "Маршрут заказа"),
    },
    "modulprof": {
        "cover": ("Модульные здания под задачу производства", "Базовая спецификация"),
        "catalog": ("Каталог модульных зданий", "Параметры поставки"),
        "configurator": ("Конфигуратор здания", "Состав комплекта"),
        "comparison": ("Сравнение комплектаций", "Соответствие нормам"),
        "projects": ("Реализованные проекты", "Производственный график"),
    },
    "doma-u-ozera": {
        "cover": ("Выходные у озера", "Найден дом на ваши даты"),
        "sauna-house": ("Дом с сауной", "Что входит в проживание"),
        "search": ("Найдите дом для своей компании", "Найдено домов"),
        "calendar": ("Свободные даты", "Выбранные даты"),
        "booking": ("Бронирование", "К оплате сейчас"),
    },
    "praktika": {
        "cover": ("Учитесь на реальных проектах", "Следующее занятие"),
        "courses": ("Мои курсы", "Ближайшие проверки"),
        "curriculum": ("Программа курса", "Прогноз завершения"),
        "lesson": ("Урок 4", "Задание к уроку"),
        "progress": ("Прогресс", "История проверок"),
    },
    "gruzcontrol": {
        "cover": ("Операционная сводка", "Передача смены"),
        "deliveries": ("Доставки", "Документы по доставке"),
        "dispatch": ("Диспетчерская", "Назначение экипажа"),
        "route": ("GC-1842", "История маршрута"),
        "analytics": ("Аналитика доставки", "Причины задержек"),
    },
}

ASSETS_BY_ROUTE = {
    "sever-market": {
        "cover": ("mountain_tent",),
        "catalog": ("hiking_backpack",),
        "tents": ("gear_closeup",),
        "cart": ("campfire_scene",),
        "delivery": ("guide_portrait", "winter_route"),
    },
    "modulprof": {
        "cover": ("modular_building",),
        "catalog": ("factory_assembly",),
        "configurator": ("interior_module", "facade_detail"),
        "comparison": ("architect_portrait",),
        "projects": ("site_installation",),
    },
    "doma-u-ozera": {
        "cover": ("lakeside_house",),
        "sauna-house": ("sauna_interior", "terrace_view"),
        "search": ("bedroom_detail",),
        "calendar": ("evening_pier",),
        "booking": ("host_portrait",),
    },
    "praktika": {
        "cover": ("student_workspace",),
        "courses": ("design_board",),
        "curriculum": ("lesson_notebook",),
        "lesson": ("mentor_portrait", "team_review"),
        "progress": ("graduation_scene",),
    },
    "gruzcontrol": {
        "cover": ("logistics_terminal",),
        "deliveries": ("truck_fleet",),
        "dispatch": ("dispatcher_portrait",),
        "route": ("delivery_driver", "route_overview"),
        "analytics": ("warehouse_scan",),
    },
}

PAGE_SELECTORS = {
    "sever-market": ".sm-page",
    "modulprof": ".mp-page",
    "doma-u-ozera": ".du-page",
    "praktika": ".pk-page",
    "gruzcontrol": ".gc-page",
}


@pytest.fixture(scope="module")
def chrome_browser():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome", headless=True)
        try:
            yield browser
        finally:
            browser.close()


def _assets(project):
    return {
        asset.key: f"/assets/{project.slug}/{asset.filename}"
        for asset in project.assets
    }


def _render(project, shot):
    module = import_module(project.renderer_module)
    return module.render(project, shot, _assets(project))


def _open(page, project, shot):
    rendered = _render(project, shot)
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


@pytest.mark.parametrize("slug", PROJECTS)
def test_product_system_has_five_distinct_dedicated_routes(slug):
    project = get_project(slug)
    pages = [_render(project, shot) for shot in project.shots]

    assert len(pages) == 5
    assert len({page.html for page in pages}) == 5
    assert all(isinstance(page, RenderedPage) for page in pages)
    assert [shot.key for shot in project.shots] == list(ROUTE_COPY[slug])
    assert project.renderer_module.endswith(slug.replace("-", "_"))

    for shot, page in zip(project.shots, pages):
        assert f'data-site="{slug}"' in page.html
        assert f'data-route="{shot.key}"' in page.html
        assert project.brand in page.html
        assert 'data-lower-band="true"' in page.html
        for fragment in ROUTE_COPY[slug][shot.key]:
            assert fragment in page.html
        assert public_url(project, shot) == f"https://{project.domain}{shot.path}"


@pytest.mark.parametrize("slug", PROJECTS)
def test_product_system_uses_every_owned_bitmap_exactly_once(slug):
    project = get_project(slug)
    assets = _assets(project)
    pages = {shot.key: _render(project, shot).html for shot in project.shots}

    for route, owned_keys in ASSETS_BY_ROUTE[slug].items():
        for key in owned_keys:
            source = escape(assets[key], quote=True)
            assert pages[route].count(source) == 1
            assert sum(page.count(source) for page in pages.values()) == 1


@pytest.mark.parametrize("slug", PROJECTS)
def test_product_system_is_independent_and_avoids_failed_template_patterns(slug):
    project = get_project(slug)
    module = import_module(project.renderer_module)
    source = inspect.getsource(module).casefold()
    pages = [_render(project, shot) for shot in project.shots]
    combined = "\n".join(page.html + page.css + page.scripts for page in pages).casefold()

    for forbidden_import in (
        "sites.commercial",
        "sites.leadgen",
        "sites.complex",
        "from .commercial",
        "from .leadgen",
        "from .complex",
    ):
        assert forbidden_import not in source
    for forbidden in (
        "gradient",
        "backdrop-filter",
        "border-radius",
        "lorem",
        "localhost",
        "никита тихомиров",
    ):
        assert forbidden not in combined
    assert "height: 1120px" in combined


@pytest.mark.parametrize("slug", PROJECTS)
def test_product_system_routes_fit_canvas_and_reach_lower_quarter(slug, chrome_browser):
    project = get_project(slug)
    page = chrome_browser.new_page(viewport={"width": 1920, "height": 1280})
    try:
        for shot in project.shots:
            _open(page, project, shot)
            root = page.locator(PAGE_SELECTORS[slug])
            box = root.bounding_box()
            lower = page.locator('[data-lower-band="true"]').bounding_box()
            assert round(box["width"]) == 1920
            assert round(box["height"]) == 1120
            assert page.evaluate("el => el.scrollHeight", root.element_handle()) == 1120
            assert page.evaluate("el => el.scrollWidth", root.element_handle()) == 1920
            assert lower["y"] >= box["y"] + 760
            assert lower["y"] + lower["height"] <= box["y"] + box["height"] + 1
            assert lower["y"] + lower["height"] >= box["y"] + box["height"] - 40
    finally:
        page.close()


def test_sever_market_workflows_update_real_product_and_order_state(chrome_browser):
    project = get_project("sever-market")
    shots = {shot.key: shot for shot in project.shots}
    page = chrome_browser.new_page(viewport={"width": 1920, "height": 1280})
    try:
        _open(page, project, shots["cover"])
        geometry = page.locator(".sm-page").bounding_box()
        page.locator('[data-selectable="season"][data-value="winter"]').click()
        assert "Зимний маршрут" in page.locator("[data-kit-name]").inner_text()
        assert "48 700 ₽" in page.locator("[data-kit-price]").inner_text()
        assert "6 комплектов" in page.locator("[data-kit-stock]").inner_text()
        assert page.locator(".sm-page").bounding_box() == geometry

        _open(page, project, shots["catalog"])
        page.locator('[data-catalog-filter="winter"]').check()
        assert page.locator("[data-catalog-count]").inner_text() == "38 товаров"
        assert "зимнего похода" in page.locator("[data-catalog-summary]").inner_text()

        _open(page, project, shots["tents"])
        page.locator('[data-selectable="tent-capacity"][data-value="4"]').click()
        assert "4 места" in page.locator("[data-tent-result]").inner_text()
        page.locator("[data-add-tent]").click()
        assert page.locator("[data-cart-count]").inner_text() == "1"

        _open(page, project, shots["cart"])
        page.locator("[data-cart-quantity]").fill("2")
        page.locator('[data-selectable="delivery-mode"][data-value="courier"]').click()
        assert page.locator("[data-cart-total]").inner_text() == "35 780 ₽"
        parts = page.locator("[data-cart-part]").all_inner_texts()
        assert parts == ["35 980 ₽", "−1 500 ₽", "1 300 ₽"]

        _open(page, project, shots["delivery"])
        page.locator("[data-delivery-city]").select_option("kazan")
        page.locator('[data-selectable="carrier"][data-value="express"]').click()
        summary = page.locator("[data-delivery-summary]").inner_text()
        assert "Казань" in summary
        assert "29 августа" in summary
        assert "1 490 ₽" in summary
    finally:
        page.close()


def test_sever_market_cover_and_catalog_controls_update_dependent_state(chrome_browser):
    project = get_project("sever-market")
    shots = {shot.key: shot for shot in project.shots}
    page = chrome_browser.new_page(viewport={"width": 1920, "height": 1280})
    try:
        _open(page, project, shots["cover"])
        geometry = page.locator(".sm-page").bounding_box()
        page.locator("[data-add-kit]").click()
        assert page.locator("[data-cart-count]").inner_text() == "1"
        assert "Осенний маршрут добавлен" in page.locator("[data-kit-cart-state]").inner_text()
        assert page.locator(".sm-page").bounding_box() == geometry

        _open(page, project, shots["catalog"])
        geometry = page.locator(".sm-page").bounding_box()
        summer = page.locator('[data-catalog-filter="summer"]')
        shoulder = page.locator('[data-catalog-filter="shoulder"]')
        winter = page.locator('[data-catalog-filter="winter"]')
        ultralight = page.locator('[data-catalog-filter="ultralight"]')
        light = page.locator('[data-catalog-filter="light"]')
        tents = page.locator('[data-catalog-filter="tents"]')
        backpacks = page.locator('[data-catalog-filter="backpacks"]')
        sleeping = page.locator('[data-catalog-filter="sleeping"]')

        winter.check()
        assert not summer.is_checked()
        assert not shoulder.is_checked()
        assert page.locator("[data-catalog-count]").inner_text() == "38 товаров"

        shoulder.check()
        assert not summer.is_checked()
        assert not winter.is_checked()
        assert "межсезонного похода" in page.locator("[data-catalog-summary]").inner_text()

        ultralight.check()
        assert "до 1,5 кг" in page.locator("[data-catalog-summary]").inner_text()
        light.uncheck()
        assert "только ультралёгкое" in page.locator("[data-catalog-summary]").inner_text()

        sleeping.check()
        assert "спальные системы" in page.locator("[data-catalog-summary]").inner_text()
        backpacks.uncheck()
        assert "без рюкзаков" in page.locator("[data-catalog-summary]").inner_text()
        tents.uncheck()
        assert "только спальные системы" in page.locator("[data-catalog-summary]").inner_text()

        summer.check()
        assert not shoulder.is_checked()
        assert not winter.is_checked()
        assert "летнего похода" in page.locator("[data-catalog-summary]").inner_text()

        page.locator('[aria-label="Сортировка каталога"]').select_option("weight")
        assert page.locator("[data-product-key]").first.get_attribute("data-product-key") == "stove"
        assert "Сначала легче" in page.locator("[data-catalog-sort-state]").inner_text()

        page.locator("[data-check-city]").click()
        assert "Москва · 52 позиции" in page.locator("[data-stock-state]").inner_text()
        page.locator("[data-send-list]").click()
        assert "отправлен эксперту" in page.locator("[data-expert-state]").inner_text()

        page.locator("[data-catalog-reset]").click()
        assert page.locator("[data-catalog-count]").inner_text() == "126 товаров"
        assert summer.is_checked()
        assert not shoulder.is_checked()
        assert not winter.is_checked()
        assert not ultralight.is_checked()
        assert light.is_checked()
        assert tents.is_checked()
        assert backpacks.is_checked()
        assert not sleeping.is_checked()
        assert page.locator("[data-product-key]").first.get_attribute("data-product-key") == "backpack"
        assert page.locator(".sm-page").bounding_box() == geometry
    finally:
        page.close()


def test_sever_market_tent_capacity_weather_and_cart_state_stay_consistent(chrome_browser):
    project = get_project("sever-market")
    shots = {shot.key: shot for shot in project.shots}
    page = chrome_browser.new_page(viewport={"width": 1920, "height": 1280})
    try:
        _open(page, project, shots["tents"])
        geometry = page.locator(".sm-page").bounding_box()
        page.locator('[data-selectable="tent-capacity"][data-value="4"]').click()

        selected_row = page.locator(".sm-tent-comparison tbody tr.is-selected")
        assert selected_row.get_attribute("data-tent-row") == "4"
        assert "Taiga Base 4" in selected_row.inner_text()
        assert "4" in selected_row.locator("td").nth(1).inner_text()
        assert "23 900 ₽" in selected_row.inner_text()
        assert page.locator("[data-selected-tent]").inner_text() == "Taiga Base 4"
        assert page.locator("[data-selected-capacity]").inner_text() == "4 человека"
        assert page.locator("[data-selected-tent-price]").inner_text() == "23 900 ₽"

        wind = page.locator('[data-tent-weather="wind"]')
        rain = page.locator('[data-tent-weather="rain"]')
        snow = page.locator('[data-tent-weather="snow"]')
        wind.uncheck()
        assert "умеренный ветер" in page.locator("[data-tent-weather-state]").inner_text()
        rain.uncheck()
        assert "краткий дождь" in page.locator("[data-tent-weather-state]").inner_text()
        snow.check()
        assert "снеговая юбка" in page.locator("[data-tent-weather-state]").inner_text()

        page.locator("[data-add-tent]").click()
        cart_state = page.locator("[data-tent-cart-state]").inner_text()
        assert "Taiga Base 4" in cart_state
        assert "23 900 ₽" in cart_state
        assert page.locator("[data-cart-count]").inner_text() == "1"
        assert page.locator(".sm-page").bounding_box() == geometry
    finally:
        page.close()


def test_sever_market_cart_normalizes_quantity_promos_and_next_actions(chrome_browser):
    project = get_project("sever-market")
    shots = {shot.key: shot for shot in project.shots}
    page = chrome_browser.new_page(viewport={"width": 1920, "height": 1280})
    try:
        _open(page, project, shots["cart"])
        geometry = page.locator(".sm-page").bounding_box()
        quantity = page.locator("[data-cart-quantity]")

        quantity.fill("0")
        assert quantity.input_value() == "1"
        assert page.locator("[data-cart-total]").inner_text() == "17 990 ₽"

        quantity.fill("5")
        assert quantity.input_value() == "4"
        assert page.locator("[data-cart-part]").all_inner_texts() == [
            "71 960 ₽",
            "−1 500 ₽",
            "0 ₽",
        ]
        assert page.locator("[data-cart-total]").inner_text() == "70 460 ₽"

        page.locator('[data-selectable="delivery-mode"][data-value="courier"]').click()
        assert page.locator("[data-cart-total]").inner_text() == "71 760 ₽"

        promo = page.locator("[data-cart-promo]")
        promo.fill("BADCODE")
        page.locator("[data-apply-promo]").click()
        assert page.locator("[data-promo-state]").inner_text() == "Промокод не найден"
        assert page.locator("[data-cart-part]").all_inner_texts() == [
            "71 960 ₽",
            "0 ₽",
            "1 300 ₽",
        ]
        assert page.locator("[data-cart-total]").inner_text() == "73 260 ₽"

        promo.fill("sever1500")
        page.locator("[data-apply-promo]").click()
        assert promo.input_value() == "SEVER1500"
        assert page.locator("[data-promo-state]").inner_text() == "Скидка 1 500 ₽ применена"
        assert page.locator("[data-cart-total]").inner_text() == "71 760 ₽"

        page.locator("[data-check-compatibility]").click()
        assert "Совместимость подтверждена" in page.locator("[data-compatibility-state]").inner_text()

        page.locator("[data-add-footprint]").click()
        assert page.locator("[data-cart-count]").inner_text() == "2"
        assert "Футпринт добавлен" in page.locator("[data-footprint-state]").inner_text()
        assert page.locator("[data-cart-part]").all_inner_texts() == [
            "74 150 ₽",
            "−1 500 ₽",
            "1 300 ₽",
        ]
        assert page.locator("[data-cart-total]").inner_text() == "73 950 ₽"

        page.locator("[data-checkout]").click()
        assert "Шаг 2 из 3" in page.locator("[data-checkout-state]").inner_text()
        assert page.locator(".sm-page").bounding_box() == geometry
    finally:
        page.close()


def test_sever_market_delivery_pickup_and_confirmation_update_order_route(chrome_browser):
    project = get_project("sever-market")
    shots = {shot.key: shot for shot in project.shots}
    page = chrome_browser.new_page(viewport={"width": 1920, "height": 1280})
    try:
        _open(page, project, shots["delivery"])
        geometry = page.locator(".sm-page").bounding_box()

        page.locator("[data-pickup-point]").select_option("pvz")
        summary = page.locator("[data-delivery-summary]").inner_text()
        assert "ПВЗ рядом с метро" in summary
        assert "390 ₽" in summary
        assert "последняя миля" in page.locator("[data-route-note]").inner_text()

        page.locator("[data-confirm-delivery]").click()
        assert "Доставка выбрана" in page.locator("[data-delivery-choice-state]").inner_text()
        assert "390 ₽" in page.locator("[data-delivery-choice-state]").inner_text()

        page.locator("[data-delivery-city]").select_option("kazan")
        page.locator('[data-selectable="carrier"][data-value="express"]').click()
        summary = page.locator("[data-delivery-summary]").inner_text()
        assert "Казань" in summary
        assert "29 августа" in summary
        assert "1 390 ₽" in summary
        assert "ПВЗ рядом с метро" in summary
        assert page.locator(".sm-page").bounding_box() == geometry
    finally:
        page.close()


def test_sever_market_header_navigation_has_no_internal_overlap(chrome_browser):
    project = get_project("sever-market")
    page = chrome_browser.new_page(viewport={"width": 1920, "height": 1280})
    try:
        for shot in project.shots:
            _open(page, project, shot)
            navigation = page.locator(".sm-category-nav")
            navigation_size = navigation.evaluate(
                "el => ({clientWidth: el.clientWidth, scrollWidth: el.scrollWidth})"
            )
            delivery_box = navigation.locator("a").last.bounding_box()
            cart_box = page.locator(".sm-cart-link").bounding_box()
            shopbar_box = page.locator(".sm-shopbar").bounding_box()

            assert navigation_size["scrollWidth"] <= navigation_size["clientWidth"]
            assert delivery_box["x"] + delivery_box["width"] <= cart_box["x"]
            assert cart_box["x"] + cart_box["width"] <= shopbar_box["x"] + shopbar_box["width"]
    finally:
        page.close()


def test_modulprof_workflows_recalculate_specification_and_procurement(chrome_browser):
    project = get_project("modulprof")
    shots = {shot.key: shot for shot in project.shots}
    page = chrome_browser.new_page(viewport={"width": 1920, "height": 1280})
    try:
        _open(page, project, shots["cover"])
        page.locator('[data-selectable="building-purpose"][data-value="office"]').click()
        assert "Офисный модуль" in page.locator("[data-cover-model]").inner_text()
        assert "1 980 000 ₽" in page.locator("[data-cover-price]").inner_text()

        _open(page, project, shots["catalog"])
        page.locator('[data-catalog-purpose="warehouse"]').check()
        assert page.locator("[data-building-count]").inner_text() == "7 решений"
        assert "склад" in page.locator("[data-building-summary]").inner_text().casefold()

        _open(page, project, shots["configurator"])
        geometry = page.locator(".mp-page").bounding_box()
        page.locator("[data-config-length]").fill("18")
        page.locator('[data-config-option="heating"]').check()
        page.locator('[data-selectable="config-shell"][data-value="warm"]').click()
        summary = page.locator("[data-config-summary]").inner_text()
        assert "216 м²" in summary
        assert "Тёплый контур" in summary
        assert "4 386 000 ₽" in summary
        parts = page.locator("[data-config-part]").all_inner_texts()
        assert sum(int("".join(filter(str.isdigit, value))) for value in parts) == 4386000
        assert page.locator(".mp-page").bounding_box() == geometry

        _open(page, project, shots["comparison"])
        page.locator('[data-selectable="package"][data-value="turnkey"]').click()
        assert "Под ключ" in page.locator("[data-package-summary]").inner_text()
        assert "5 940 000 ₽" in page.locator("[data-package-total]").inner_text()

        _open(page, project, shots["projects"])
        page.locator('[data-selectable="project-sector"][data-value="logistics"]').click()
        assert "Логистический терминал" in page.locator("[data-project-selection]").inner_text()
        assert page.locator("[data-project-count]").inner_text() == "8 проектов"
    finally:
        page.close()


def test_doma_u_ozera_workflows_keep_availability_and_totals_consistent(chrome_browser):
    project = get_project("doma-u-ozera")
    shots = {shot.key: shot for shot in project.shots}
    page = chrome_browser.new_page(viewport={"width": 1920, "height": 1280})
    try:
        _open(page, project, shots["cover"])
        page.locator('[data-selectable="guest-count"][data-value="6"]').click()
        assert "Дом «Сосны»" in page.locator("[data-cover-house]").inner_text()
        assert "43 200 ₽" in page.locator("[data-cover-total]").inner_text()

        _open(page, project, shots["sauna-house"])
        page.locator('[data-selectable="stay-package"][data-value="sauna-plus"]').click()
        assert "Сауна без ограничений" in page.locator("[data-stay-summary]").inner_text()
        assert "52 800 ₽" in page.locator("[data-stay-total]").inner_text()

        _open(page, project, shots["search"])
        page.locator('[data-search-filter="pets"]').check()
        page.locator("[data-search-guests]").fill("6")
        assert page.locator("[data-search-count]").inner_text() == "3 дома"
        assert "с питомцем" in page.locator("[data-search-summary]").inner_text()

        _open(page, project, shots["calendar"])
        page.locator('[data-calendar-date="2026-09-11"]').click()
        page.locator('[data-calendar-date="2026-09-13"]').click()
        selection = page.locator("[data-calendar-summary]").inner_text()
        assert "11–13 сентября" in selection
        assert "2 ночи" in selection
        assert "43 200 ₽" in selection

        _open(page, project, shots["booking"])
        geometry = page.locator(".du-page").bounding_box()
        page.locator('[data-booking-extra="sauna"]').check()
        page.locator("[data-booking-guests]").fill("6")
        summary = page.locator("[data-booking-summary]").inner_text()
        assert "6 гостей" in summary
        assert "Сауна" in summary
        assert "48 000 ₽" in page.locator("[data-booking-total]").inner_text()
        assert "14 400 ₽" in page.locator("[data-booking-deposit]").inner_text()
        assert page.locator(".du-page").bounding_box() == geometry
    finally:
        page.close()


def test_praktika_workflows_update_learning_plan_and_completion(chrome_browser):
    project = get_project("praktika")
    shots = {shot.key: shot for shot in project.shots}
    page = chrome_browser.new_page(viewport={"width": 1920, "height": 1280})
    try:
        _open(page, project, shots["cover"])
        page.locator('[data-selectable="weekly-plan"][data-value="intensive"]').click()
        assert "2 урока до пятницы" in page.locator("[data-next-lesson]").inner_text()
        assert "28 августа" in page.locator("[data-next-deadline]").inner_text()

        _open(page, project, shots["courses"])
        page.locator('[data-selectable="course-filter"][data-value="active"]').click()
        page.locator('[data-selectable="course-load"][data-value="8"]').click()
        assert page.locator("[data-course-count]").inner_text() == "3 активных курса"
        assert "8 часов в неделю" in page.locator("[data-course-plan]").inner_text()

        _open(page, project, shots["curriculum"])
        page.locator('[data-selectable="pace"][data-value="fast"]').click()
        assert "18 сентября" in page.locator("[data-curriculum-forecast]").inner_text()
        assert "3 занятия в неделю" in page.locator("[data-curriculum-load]").inner_text()

        _open(page, project, shots["lesson"])
        geometry = page.locator(".pk-page").bounding_box()
        page.locator('[data-selectable="lesson-tab"][data-value="materials"]').click()
        assert "Файл сетки и чек-лист" in page.locator("[data-lesson-content]").inner_text()
        page.locator('[data-lesson-task="states"]').check()
        page.locator('[data-lesson-task="logic"]').check()
        page.locator('[data-lesson-task="testing"]').check()
        assert "Задание готово к отправке" in page.locator("[data-lesson-status]").inner_text()
        assert page.locator(".pk-page").bounding_box() == geometry

        _open(page, project, shots["progress"])
        page.locator('[data-selectable="progress-period"][data-value="quarter"]').click()
        page.locator('[data-selectable="skill-target"][data-value="portfolio"]').click()
        assert "74%" in page.locator("[data-progress-value]").inner_text()
        assert "2 проекта до цели" in page.locator("[data-progress-forecast]").inner_text()
    finally:
        page.close()


def test_gruzcontrol_workflows_update_operational_state_not_only_selection(chrome_browser):
    project = get_project("gruzcontrol")
    shots = {shot.key: shot for shot in project.shots}
    page = chrome_browser.new_page(viewport={"width": 1920, "height": 1280})
    try:
        _open(page, project, shots["cover"])
        page.locator('[data-queue-row="delay-7"]').click()
        assert "Д-260824-017" in page.locator("[data-overview-detail]").inner_text()
        assert "Задержка 38 минут" in page.locator("[data-overview-detail]").inner_text()

        _open(page, project, shots["deliveries"])
        page.locator("[data-delivery-status]").select_option("delayed")
        assert page.locator("[data-delivery-count]").inner_text() == "9 доставок"
        assert "Д-260824-017" in page.locator("[data-delivery-detail]").inner_text()

        _open(page, project, shots["dispatch"])
        geometry = page.locator(".gc-page").bounding_box()
        page.locator('[data-dispatch-job="GC-1851"]').click()
        page.locator('[data-selectable="dispatch-truck"][data-value="A123BC"]').click()
        page.locator('[data-selectable="dispatch-driver"][data-value="ivanov"]').click()
        page.locator("[data-assign-dispatch]").click()
        summary = page.locator("[data-dispatch-summary]").inner_text()
        assert "GC-1851" in summary
        assert "A123BC 799" in summary
        assert "Иванов С. П." in summary
        assert "Назначена" in summary
        assert page.locator(".gc-page").bounding_box() == geometry

        _open(page, project, shots["route"])
        page.locator('[data-selectable="checkpoint"][data-value="loaded"]').click()
        assert "Груз принят" in page.locator("[data-route-status]").inner_text()
        assert "11:25" in page.locator("[data-route-eta]").inner_text()
        assert "Статус обновлён" in page.locator("[data-route-history]").inner_text()

        _open(page, project, shots["analytics"])
        page.locator('[data-selectable="analytics-period"][data-value="month"]').click()
        page.locator("[data-analytics-service]").select_option("express")
        assert "96,4%" in page.locator("[data-analytics-sla]").inner_text()
        assert "Экспресс · август" in page.locator("[data-analytics-context]").inner_text()
        assert "Ожидание на складе" in page.locator("[data-delay-reason]").inner_text()
    finally:
        page.close()
