from collections.abc import Callable, Mapping

from ..components import escape_html, panel
from ..icons import icon
from ..models import ProjectSpec, ShotSpec


COMPLEX_LAYOUTS = {
    "sever-market": ("expedition-storefront", "gear-catalog", "shopping-cart"),
    "modulprof": ("engineering-configurator", "building-specification", "building-comparison"),
    "doma-u-ozera": ("lakeside-search", "house-plans", "booking-calendar"),
    "praktika": ("learning-dashboard", "course-curriculum", "lesson-workspace"),
    "gruzcontrol": ("operations-overview", "route-register", "delivery-table"),
}

COMPLEX_STATES = {
    "sever-market": "cart-with-two-products-and-delivery-choice",
    "modulprof": "three-column-building-comparison",
    "doma-u-ozera": "calendar-with-selected-weekend-and-house",
    "praktika": "lesson-video-outline-and-completed-task",
    "gruzcontrol": "delivery-table-with-selected-detail-drawer",
}

_IMAGE_ALTS = {
    "sever-market": "Туристическое снаряжение для похода по северному маршруту",
    "modulprof": "Модульное здание инженерной комплектации",
    "doma-u-ozera": "Загородный дом с сауной на берегу озера",
    "praktika": "Рабочее место участника образовательной программы",
    "gruzcontrol": "Карта маршрутов текущих городских доставок",
}

_COMPLEX_CSS = """
.complex-page { width: 100%; min-height: 100%; overflow: hidden; background: var(--surface); color: var(--ink); }
.complex-page * { box-sizing: border-box; }
.complex-page a { color: inherit; text-decoration: none; }
.complex-page h1, .complex-page h2, .complex-page h3, .complex-page p { margin-top: 0; }
.complex-page h1 { margin-bottom: 22px; font-size: 58px; line-height: 1.03; letter-spacing: 0; }
.complex-page h2 { margin-bottom: 18px; font-size: 38px; line-height: 1.08; letter-spacing: 0; }
.complex-page h3 { margin-bottom: 8px; font-size: 19px; line-height: 1.25; letter-spacing: 0; }
.complex-page p { margin-bottom: 18px; color: var(--ink-muted); font-size: 17px; line-height: 1.48; }
.complex-nav { display: flex; align-items: center; justify-content: space-between; min-height: 76px; padding: 0 44px; border-bottom: 1px solid rgba(91, 105, 118, .18); background: #fff; }
.complex-brand { font-size: 22px; font-weight: 800; }
.complex-links { display: flex; align-items: center; gap: 28px; color: var(--ink-muted); font-size: 14px; font-weight: 650; }
.complex-actions { display: flex; align-items: center; gap: 10px; }
.complex-button { display: inline-flex; align-items: center; justify-content: center; gap: 9px; min-height: 44px; padding: 0 18px; border: 0; border-radius: 6px; background: var(--accent); color: #fff; font: inherit; font-size: 15px; font-weight: 750; }
.complex-button.secondary { border: 1px solid rgba(91, 105, 118, .28); background: #fff; color: var(--ink); }
.complex-label { margin-bottom: 12px; color: var(--accent-strong); font-size: 13px; font-weight: 800; text-transform: uppercase; }
.complex-image-slot { width: 100%; margin: 0; overflow: hidden; aspect-ratio: 16 / 10; background: var(--highlight); }
.complex-image-slot > .complex-hero-image { width: 100%; height: 100%; object-fit: cover; }
.complex-field { min-height: 48px; padding: 13px 15px; border: 1px solid rgba(91, 105, 118, .25); border-radius: 5px; background: #fff; font-size: 14px; }
.complex-tabs { display: flex; align-items: center; gap: 24px; border-bottom: 1px solid rgba(91, 105, 118, .18); }
.complex-tab { padding: 15px 2px 13px; color: var(--ink-muted); font-size: 14px; font-weight: 700; }
.complex-tab.active { border-bottom: 3px solid var(--accent); color: var(--ink); }
.complex-mobile { min-height: 920px; }
.complex-mobile .complex-nav { min-height: 64px; padding: 0 18px; }
.complex-mobile .complex-links, .complex-mobile .nav-secondary { display: none; }
.complex-mobile .complex-brand { font-size: 18px; }
.complex-mobile .complex-button { min-height: 42px; padding: 0 13px; font-size: 13px; }
.complex-mobile h1 { font-size: 37px; }
.complex-mobile h2 { font-size: 29px; }
.complex-mobile p { font-size: 15px; }

.sever-market .complex-brand { color: #234d40; }
.store-cover { display: grid; grid-template-columns: minmax(0, 1.18fr) minmax(420px, .82fr); background: #f4f6f3; }
.store-cover-media { position: relative; padding: 34px 34px 28px 44px; }
.store-cover-media .complex-image-slot { max-width: 980px; }
.store-route { position: absolute; left: 68px; bottom: 52px; display: flex; align-items: center; gap: 10px; padding: 13px 16px; background: #fff; box-shadow: 0 12px 28px rgba(20, 38, 30, .14); font-size: 14px; font-weight: 750; }
.store-cover-copy { display: flex; flex-direction: column; justify-content: center; padding: 54px 58px; background: #fff; }
.store-cover-copy h1 { max-width: 560px; }
.store-category-band { display: grid; grid-template-columns: repeat(4, 1fr); border-top: 1px solid rgba(91, 105, 118, .18); background: #fff; }
.store-category-band div { padding: 25px 30px; border-right: 1px solid rgba(91, 105, 118, .18); font-size: 16px; font-weight: 750; }
.gear-catalog-page { display: grid; grid-template-columns: 270px minmax(0, 1fr); min-height: 950px; }
.gear-filters { padding: 34px 26px; border-right: 1px solid rgba(91, 105, 118, .18); background: #f4f6f3; }
.gear-filter { padding: 18px 0; border-bottom: 1px solid rgba(91, 105, 118, .18); }
.gear-filter strong { display: block; margin-bottom: 9px; }
.gear-results { padding: 34px 42px; }
.gear-results-head { display: flex; align-items: end; justify-content: space-between; }
.gear-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 20px; }
.gear-product { border-bottom: 2px solid #2e6a58; padding-bottom: 18px; }
.gear-product .complex-image-slot { margin-bottom: 16px; }
.gear-price { display: flex; align-items: center; justify-content: space-between; font-weight: 800; }
.store-cart { display: grid; grid-template-columns: minmax(0, 1.45fr) minmax(360px, .55fr); gap: 36px; padding: 38px 46px; background: #f5f7f5; }
.cart-list, .cart-summary { background: #fff; }
.cart-list { padding: 30px; }
.cart-row { display: grid; grid-template-columns: 180px minmax(0, 1fr) 110px; gap: 22px; align-items: center; padding: 18px 0; border-top: 1px solid rgba(91, 105, 118, .18); }
.cart-row .complex-image-slot { max-width: 180px; }
.cart-row strong:last-child { text-align: right; }
.cart-summary { padding: 30px; border-top: 5px solid var(--accent); }
.delivery-choice { display: grid; gap: 10px; margin: 20px 0; }
.delivery-choice label { display: flex; gap: 10px; padding: 13px; border: 1px solid rgba(91, 105, 118, .22); }
.store-mobile-body { padding: 22px 18px 34px; }
.store-mobile-body .complex-image-slot { margin: 18px 0; }
.mobile-product-row { display: flex; align-items: center; justify-content: space-between; padding: 15px 0; border-top: 1px solid rgba(91, 105, 118, .18); font-weight: 750; }

.modulprof { background: #f1f3f5; }
.modulprof .complex-nav { background: #252b31; color: #fff; border-color: #3b434b; }
.modulprof .complex-links { color: #cfd5da; }
.module-cover { display: grid; grid-template-columns: minmax(0, 1.15fr) 520px; min-height: 850px; }
.module-visual { padding: 50px 54px; background: #30373e; color: #fff; }
.module-visual p { max-width: 720px; color: #d4d9de; }
.module-visual .complex-image-slot { max-width: 820px; margin-top: 34px; border: 1px solid #58616a; }
.module-config { padding: 44px 38px; background: #f2c84b; }
.module-config h2 { max-width: 390px; }
.module-config .complex-field { margin-bottom: 12px; border-color: rgba(27, 32, 37, .28); background: rgba(255, 255, 255, .72); }
.module-config .complex-button { width: 100%; margin-top: 8px; background: #283038; }
.module-spec-page { padding: 36px 46px; }
.module-spec-head { display: grid; grid-template-columns: minmax(0, 1fr) 510px; gap: 38px; align-items: center; }
.module-spec-head .complex-image-slot { max-width: 510px; }
.module-spec-table { width: 100%; margin-top: 28px; border-collapse: collapse; background: #fff; }
.module-spec-table th, .module-spec-table td { padding: 17px 20px; border: 1px solid #d8dde2; text-align: left; }
.module-spec-table th { width: 28%; background: #353c45; color: #fff; }
.module-compare { padding: 34px 44px; background: #eef1f4; }
.module-compare-head { display: grid; grid-template-columns: minmax(0, 1fr) 360px; gap: 32px; align-items: center; margin-bottom: 24px; }
.module-compare-head .complex-image-slot { max-width: 360px; }
.comparison-grid { display: grid; grid-template-columns: 230px repeat(3, minmax(0, 1fr)); border-top: 1px solid #cbd2d9; border-left: 1px solid #cbd2d9; background: #fff; }
.comparison-grid > div { min-height: 54px; padding: 14px 16px; border-right: 1px solid #cbd2d9; border-bottom: 1px solid #cbd2d9; }
.comparison-name { background: #f2c84b; font-weight: 800; }
.comparison-label { color: var(--ink-muted); font-size: 14px; }
.module-mobile-body { padding: 24px 18px; background: #eef1f4; }
.module-mobile-body .complex-image-slot { margin: 18px 0; }
.module-mobile-spec { display: grid; grid-template-columns: 1fr 1fr; border: 1px solid #cbd2d9; }
.module-mobile-spec div { padding: 14px; background: #fff; border: 1px solid #e0e4e8; }

.doma-u-ozera { background: #fff; }
.lake-cover { display: grid; grid-template-columns: minmax(0, 1.35fr) 500px; background: #14271f; }
.lake-media { position: relative; padding: 32px 0 32px 36px; }
.lake-media .complex-image-slot { max-width: 1050px; }
.lake-media .lake-caption { position: absolute; left: 64px; bottom: 58px; max-width: 410px; margin: 0; padding: 12px 14px; background: rgba(11, 31, 24, .86); border-left: 3px solid #d56b4d; color: #fff; font-size: 16px; }
.lake-search { display: flex; flex-direction: column; justify-content: center; padding: 42px 48px; background: #fff; }
.lake-search h1 { font-family: Georgia, serif; font-size: 52px; }
.lake-fields { display: grid; gap: 11px; margin: 12px 0 20px; }
.lake-next-band { display: flex; justify-content: space-between; padding: 25px 42px; background: #eaf1ed; font-weight: 750; }
.house-plan-page { display: grid; grid-template-columns: minmax(0, 1.2fr) 480px; gap: 42px; padding: 38px 46px; }
.house-plan-main .complex-image-slot { max-width: 980px; margin-bottom: 24px; }
.house-facts { display: grid; grid-template-columns: repeat(4, 1fr); border-top: 1px solid #cdd8d1; border-bottom: 1px solid #cdd8d1; }
.house-facts div { padding: 18px 12px; }
.house-facts strong { display: block; margin-bottom: 5px; font-size: 22px; }
.house-plan-aside { padding: 28px; background: #edf3ef; }
.plan-line { display: flex; justify-content: space-between; padding: 15px 0; border-bottom: 1px solid #cdd8d1; }
.booking-workspace { display: grid; grid-template-columns: minmax(0, 1.25fr) 440px; gap: 34px; padding: 36px 44px; background: #f3f6f4; }
.booking-calendar-panel { padding: 28px; background: #fff; }
.calendar-head { display: flex; align-items: center; justify-content: space-between; }
.calendar-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 7px; margin-top: 18px; }
.calendar-day { min-height: 62px; padding: 10px; border: 1px solid #d6ded9; background: #fff; text-align: center; }
.calendar-day.muted { color: #a0aaa4; background: #f5f7f5; }
.calendar-day.selected { border-color: var(--accent); background: var(--accent); color: #fff; font-weight: 800; }
.booking-summary { padding: 28px; background: #fff; }
.booking-summary .complex-image-slot { margin-bottom: 20px; }
.booking-price { display: flex; justify-content: space-between; padding: 16px 0; border-top: 1px solid #d6ded9; font-size: 18px; font-weight: 800; }
.lake-mobile-body { padding: 18px; }
.lake-mobile-body .complex-image-slot { margin-bottom: 20px; }
.mobile-date-strip { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin: 18px 0; }
.mobile-date-strip div { padding: 12px 8px; border: 1px solid #d6ded9; text-align: center; }
.mobile-date-strip .active { background: var(--accent); color: #fff; }

.praktika { background: #f7f7f6; }
.learning-shell { display: grid; grid-template-columns: 230px minmax(0, 1fr); min-height: 980px; }
.learning-sidebar { padding: 30px 22px; background: #171918; color: #fff; }
.learning-sidebar .complex-brand { display: block; margin-bottom: 42px; color: #fff; }
.learning-menu { display: grid; gap: 8px; }
.learning-menu a { padding: 13px 14px; color: #bfc5c2; }
.learning-menu a.active { background: #2d9ea0; color: #fff; }
.learning-main { padding: 34px 42px; }
.learning-topline { display: flex; align-items: center; justify-content: space-between; margin-bottom: 28px; }
.learning-hero { display: grid; grid-template-columns: minmax(0, 1fr) 470px; gap: 32px; align-items: center; padding: 32px; background: #fff; border-left: 7px solid #ea6d5f; }
.learning-hero .complex-image-slot { max-width: 470px; }
.progress-track { width: 100%; margin: 18px 0; background: #e6e8e7; }
.progress-track span { display: block; width: 62%; min-height: 8px; background: #2d9ea0; }
.learning-queue { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-top: 22px; }
.learning-queue article { padding: 18px; border-top: 3px solid #171918; background: #fff; }
.curriculum-page { display: grid; grid-template-columns: 330px minmax(0, 1fr); min-height: 980px; }
.curriculum-aside { padding: 32px 26px; background: #171918; color: #fff; }
.curriculum-aside .complex-image-slot { margin-top: 24px; }
.curriculum-main { padding: 34px 42px; }
.lesson-row { display: grid; grid-template-columns: 54px minmax(0, 1fr) 120px; align-items: center; padding: 20px 0; border-bottom: 1px solid #d8dcda; }
.lesson-row b { font-size: 20px; }
.lesson-row span:last-child { color: var(--ink-muted); text-align: right; }
.lesson-workspace { display: grid; grid-template-columns: 270px minmax(0, 1fr) 330px; min-height: 980px; background: #f2f3f2; }
.lesson-outline { padding: 26px 20px; background: #171918; color: #fff; }
.outline-item { padding: 13px 10px; border-bottom: 1px solid #353937; color: #bcc2bf; font-size: 14px; }
.outline-item.active { border-left: 3px solid #2d9ea0; background: #292d2b; color: #fff; }
.lesson-stage { padding: 28px; }
.lesson-video { position: relative; background: #111; }
.lesson-video .complex-image-slot { opacity: .76; }
.video-status { position: absolute; left: 22px; bottom: 20px; padding: 10px 13px; background: #fff; font-weight: 800; }
.lesson-notes { margin-top: 22px; padding: 24px; background: #fff; }
.task-panel { padding: 28px 22px; background: #fff; border-left: 1px solid #d8dcda; }
.task-complete { display: flex; align-items: center; gap: 9px; margin: 18px 0; padding: 14px; background: #e8f5f1; color: #176b56; font-weight: 800; }
.learning-mobile-body { padding: 22px 18px; }
.learning-mobile-body .complex-image-slot { margin: 16px 0; }
.mobile-progress { display: flex; justify-content: space-between; margin: 18px 0; font-weight: 750; }

.gruzcontrol { background: #eef1f3; color: #25313b; }
.ops-shell { display: grid; grid-template-columns: 210px minmax(0, 1fr); min-height: 1000px; }
.ops-sidebar { padding: 26px 18px; background: #26323a; color: #fff; }
.ops-sidebar .complex-brand { display: block; margin-bottom: 34px; }
.ops-menu { display: grid; gap: 5px; }
.ops-menu a { padding: 12px; color: #c6d0d6; font-size: 14px; }
.ops-menu a.active { background: #2f8c5d; color: #fff; }
.ops-main { padding: 26px 30px; }
.ops-head { display: flex; align-items: center; justify-content: space-between; }
.ops-head h1 { margin-bottom: 4px; font-size: 36px; }
.ops-metrics { display: grid; grid-template-columns: repeat(4, 1fr); margin: 22px 0; border: 1px solid #d1d8dc; background: #fff; }
.ops-metric { padding: 18px; border-right: 1px solid #d1d8dc; }
.ops-metric strong { display: block; font-size: 28px; }
.ops-board { display: grid; grid-template-columns: minmax(0, 1.3fr) 420px; gap: 20px; }
.ops-board .complex-image-slot { border: 1px solid #d1d8dc; }
.ops-feed { background: #fff; }
.ops-feed-row { display: grid; grid-template-columns: 95px minmax(0, 1fr) 105px; padding: 15px 18px; border-bottom: 1px solid #e0e4e7; font-size: 14px; }
.status-ok { color: #24784f; font-weight: 800; }
.status-warn { color: #a66a13; font-weight: 800; }
.route-register-page { padding: 28px 32px; }
.route-register-head { display: grid; grid-template-columns: minmax(0, 1fr) 390px; gap: 24px; align-items: center; margin-bottom: 20px; }
.route-register-head .complex-image-slot { max-width: 390px; }
.delivery-table { width: 100%; border-collapse: collapse; background: #fff; font-size: 14px; }
.delivery-table th, .delivery-table td { padding: 14px 16px; border-bottom: 1px solid #dbe1e4; text-align: left; }
.delivery-table th { background: #e7ebee; color: #53616b; font-size: 12px; text-transform: uppercase; }
.delivery-table tr.selected { background: #e8f3ed; }
.delivery-workspace { display: grid; grid-template-columns: minmax(0, 1fr) 380px; min-height: 980px; }
.delivery-list { padding: 26px 28px; }
.delivery-list .complex-tabs { margin-bottom: 18px; }
.delivery-map-strip { display: grid; grid-template-columns: 280px minmax(0, 1fr); gap: 20px; align-items: center; margin-bottom: 20px; }
.delivery-map-strip .complex-image-slot { max-width: 280px; }
.detail-drawer { padding: 28px 24px; border-left: 1px solid #cbd3d8; background: #fff; }
.detail-line { display: grid; grid-template-columns: 105px minmax(0, 1fr); gap: 12px; padding: 12px 0; border-bottom: 1px solid #e2e6e8; font-size: 14px; }
.detail-line span:first-child { color: #6a7680; }
.ops-mobile-body { padding: 20px 16px; background: #eef1f3; }
.ops-mobile-body .complex-image-slot { margin: 15px 0; }
.mobile-delivery { padding: 15px; border-bottom: 1px solid #d4dbdf; background: #fff; }
.mobile-delivery strong { display: flex; justify-content: space-between; }
"""


def _hero_image(project: ProjectSpec, assets: Mapping[str, str]) -> str:
    """Render the required image through one stable, escaped aspect-ratio boundary."""
    try:
        source = assets["hero"]
    except KeyError as exc:
        raise KeyError(f"Missing hero asset for complex project: {project.slug}") from exc
    return (
        '<figure class="complex-image-slot" style="aspect-ratio: 16 / 10;">'
        '<img class="complex-hero-image" '
        f'src="{escape_html(source)}" alt="{escape_html(_IMAGE_ALTS[project.slug])}" />'
        "</figure>"
    )


def _nav(
    project: ProjectSpec,
    links: tuple[str, ...],
    action: str,
    *,
    action_icon: str = "arrow-right",
    secondary: str = "",
) -> str:
    link_html = "".join(f'<a href="#">{escape_html(link)}</a>' for link in links)
    secondary_html = (
        f'<span class="nav-secondary">{escape_html(secondary)}</span>' if secondary else ""
    )
    return (
        '<header class="complex-nav">'
        f'<a class="complex-brand" href="#">{escape_html(project.brand)}</a>'
        f'<nav class="complex-links" aria-label="Основная навигация">{link_html}</nav>'
        '<div class="complex-actions">'
        f"{secondary_html}"
        f'<button class="complex-button">{icon(action_icon, size=17)}{escape_html(action)}</button>'
        "</div></header>"
    )


def _app_sidebar(project: ProjectSpec, links: tuple[str, ...], active: str, class_name: str) -> str:
    items = "".join(
        f'<a class="{"active" if link == active else ""}" href="#">{escape_html(link)}</a>'
        for link in links
    )
    return (
        f'<aside class="{escape_html(class_name)}">'
        f'<a class="complex-brand" href="#">{escape_html(project.brand)}</a>'
        f'<nav class="{escape_html(class_name.replace("sidebar", "menu"))}">{items}</nav>'
        "</aside>"
    )


def _widget(
    project: ProjectSpec,
    content: str,
    class_name: str,
    *,
    attrs: Mapping[str, str] | None = None,
) -> str:
    widget_attrs = dict(attrs or {})
    widget_attrs.update(
        {
            "data-widget": COMPLEX_LAYOUTS[project.slug][2],
            "data-state": COMPLEX_STATES[project.slug],
        }
    )
    return panel(
        "section",
        content,
        class_name=class_name,
        attrs=widget_attrs,
    )


def _page(project: ProjectSpec, shot: ShotSpec, layout: str, content: str) -> str:
    mobile_class = " complex-mobile" if shot.layout == "mobile" else ""
    return (
        f"<style>{_COMPLEX_CSS}</style>"
        f'<main class="complex-page {escape_html(project.palette)} {escape_html(project.slug)}{mobile_class}" '
        f'data-project="{escape_html(project.slug)}" data-layout="{escape_html(layout)}" '
        f'data-variant="{escape_html(shot.variant)}">{content}</main>'
    )


def _store_products(image: str) -> str:
    products = (
        ("Палатка Шторм 2", "2,4 кг · два входа", "18 900 ₽"),
        ("Рюкзак Тайга 65", "65 л · каркасная спина", "12 400 ₽"),
        ("Спальный мешок Полюс", "комфорт до −8 °C", "9 600 ₽"),
    )
    return "".join(
        f'<article class="gear-product">{image}<h3>{name}</h3><p>{description}</p>'
        f'<div class="gear-price"><span>{price}</span><button class="complex-button secondary">В корзину</button></div></article>'
        for name, description, price in products
    )


def _sever_market(project: ProjectSpec, shot: ShotSpec, assets: Mapping[str, str]) -> str:
    image = _hero_image(project, assets)
    nav = _nav(
        project,
        ("Каталог", "Подбор по маршруту", "Доставка", "Прокат"),
        "Корзина · 2",
        action_icon="shopping-cart",
        secondary="Москва",
    )
    if shot.variant == "cover":
        body = (
            f'{nav}<section class="store-cover"><div class="store-cover-media">{image}'
            f'<div class="store-route">{icon("map-pin")} Карелия · 6 дней · сентябрь</div></div>'
            '<div class="store-cover-copy"><div class="complex-label">Подбор по условиям похода</div>'
            '<h1>Снаряжение для маршрута</h1><p>Соберите комплект по погоде, длительности и весу рюкзака. '
            'Характеристики и наличие видны до заказа.</p>'
            f'<button class="complex-button">Подобрать комплект{icon("arrow-right")}</button></div></section>'
            '<section class="store-category-band"><div>Палатки</div><div>Рюкзаки</div><div>Спальные системы</div><div>Походная кухня</div></section>'
        )
        return _page(project, shot, COMPLEX_LAYOUTS[project.slug][0], body)
    if shot.variant == "content":
        filters = (
            '<aside class="gear-filters"><div class="complex-label">Фильтры каталога</div><h3>Условия маршрута</h3>'
            '<div class="gear-filter"><strong>Сезон</strong>Осень</div><div class="gear-filter"><strong>Температура</strong>до −8 °C</div>'
            '<div class="gear-filter"><strong>Вес</strong>до 3 кг</div><div class="gear-filter"><strong>Наличие</strong>В магазине</div>'
            f'<button class="complex-button">{icon("filter")}Применить</button></aside>'
        )
        results = (
            '<section class="gear-results"><div class="gear-results-head"><div><div class="complex-label">Каталог</div>'
            '<h2>Для автономного похода</h2></div><p>18 товаров · сначала лёгкие</p></div>'
            f'<div class="gear-grid">{_store_products(image)}</div></section>'
        )
        return _page(project, shot, COMPLEX_LAYOUTS[project.slug][1], f"{nav}<div class=\"gear-catalog-page\">{filters}{results}</div>")
    if shot.variant == "function":
        rows = (
            f'<article class="cart-row">{image}<div><h3>Палатка Шторм 2</h3><p>Оливковая · 1 шт.</p></div><strong>18 900 ₽</strong></article>'
            f'<article class="cart-row">{image}<div><h3>Спальный мешок Полюс</h3><p>Левый · 1 шт.</p></div><strong>9 600 ₽</strong></article>'
        )
        cart = f'<div class="cart-list" data-cart-count="2"><div class="complex-label">Ваш комплект</div><h2>Снаряжение для маршрута</h2>{rows}</div>'
        summary = (
            '<aside class="cart-summary"><div class="complex-label">Получение заказа</div><h3>Выберите доставку</h3>'
            '<div class="delivery-choice"><label><input type="radio" name="delivery" checked />Курьером · завтра</label>'
            '<label><input type="radio" name="delivery" />Самовывоз · сегодня</label></div>'
            '<p>Товары: 28 500 ₽<br />Доставка: 490 ₽</p><h2>28 990 ₽</h2>'
            f'<button class="complex-button">Оформить заказ{icon("arrow-right")}</button></aside>'
        )
        return _page(project, shot, COMPLEX_LAYOUTS[project.slug][2], f"{nav}{_widget(project, cart + summary, 'store-cart')}")
    body = (
        f'{nav}<section class="store-mobile-body"><div class="complex-label">Маршрутный набор</div>'
        f'<h1>Снаряжение для маршрута</h1>{image}<p>Карелия · 6 дней · до −8 °C</p>'
        '<div class="mobile-product-row"><span>Палатка Шторм 2</span><strong>18 900 ₽</strong></div>'
        '<div class="mobile-product-row"><span>Спальник Полюс</span><strong>9 600 ₽</strong></div>'
        f'<button class="complex-button">Открыть комплект{icon("shopping-cart")}</button></section>'
    )
    return _page(project, shot, "expedition-storefront-mobile", body)


def _modulprof(project: ProjectSpec, shot: ShotSpec, assets: Mapping[str, str]) -> str:
    image = _hero_image(project, assets)
    nav = _nav(project, ("Каталог", "Комплектации", "Проектирование", "Документы"), "Запросить расчёт")
    if shot.variant == "cover":
        visual = (
            '<section class="module-visual"><div class="complex-label">Модульные здания</div>'
            '<h1>Соберите объект по требованиям площадки</h1><p>Габариты, инженерные системы и отделка сведены '
            f'в одну конфигурацию для обсуждения с проектировщиком.</p>{image}</section>'
        )
        config = (
            '<aside class="module-config"><div class="complex-label">Конфигуратор</div><h2>Столовая на 48 мест</h2>'
            '<div class="complex-field">Назначение · Столовая</div><div class="complex-field">Площадь · 144 м²</div>'
            '<div class="complex-field">Климат · до −35 °C</div><div class="complex-field">Срок эксплуатации · 10 лет</div>'
            f'<button class="complex-button">Собрать спецификацию{icon("arrow-right")}</button></aside>'
        )
        return _page(project, shot, COMPLEX_LAYOUTS[project.slug][0], f"{nav}<div class=\"module-cover\">{visual}{config}</div>")
    if shot.variant == "content":
        rows = "".join(
            f"<tr><th>{label}</th><td>{value}</td><td>{note}</td></tr>"
            for label, value, note in (
                ("Каркас", "Сталь 3 мм", "Антикоррозийное покрытие"),
                ("Утепление", "150 мм", "Минеральная вата"),
                ("Электрика", "24 кВт", "Щит и кабельные трассы"),
                ("Вентиляция", "1 900 м³/ч", "Приточно-вытяжная"),
            )
        )
        head = f'<div class="module-spec-head"><div><div class="complex-label">МП-144</div><h2>Спецификация здания</h2><p>Каждая позиция связана с выбранной комплектацией и доступна для выгрузки.</p></div>{image}</div>'
        return _page(project, shot, COMPLEX_LAYOUTS[project.slug][1], f'{nav}<section class="module-spec-page">{head}<table class="module-spec-table"><tbody>{rows}</tbody></table></section>')
    if shot.variant == "function":
        head = f'<div class="module-compare-head"><div><div class="complex-label">Сравнение решений</div><h2>Комплектация без скрытых позиций</h2><p>Три уровня оснащения для одного контура здания.</p></div>{image}</div>'
        cells = (
            '<div class="comparison-label">Комплектация</div><div class="comparison-name">Базовая</div><div class="comparison-name">Инженерная</div><div class="comparison-name">Автономная</div>'
            '<div class="comparison-label">Отопление</div><div>Конвекторы</div><div>Водяной контур</div><div>Тепловой насос</div>'
            '<div class="comparison-label">Вентиляция</div><div>Естественная</div><div>Приточно-вытяжная</div><div>С рекуперацией</div>'
            '<div class="comparison-label">Электроснабжение</div><div>Щит 15 кВт</div><div>Щит 24 кВт</div><div>Щит + генератор</div>'
            f'<div class="comparison-label">Действие</div><div><button class="complex-button secondary">Выбрать</button></div><div><button class="complex-button">Выбрать</button></div><div><button class="complex-button secondary">Выбрать</button></div>'
        )
        comparison = f'{head}<div class="comparison-grid" data-comparison-columns="3">{cells}</div>'
        return _page(project, shot, COMPLEX_LAYOUTS[project.slug][2], f"{nav}{_widget(project, comparison, 'module-compare')}")
    body = (
        f'{nav}<section class="module-mobile-body"><div class="complex-label">МП-144</div><h1>Здание по вашей схеме</h1>{image}'
        '<div class="module-mobile-spec"><div><strong>144 м²</strong><br />площадь</div><div><strong>−35 °C</strong><br />климат</div>'
        '<div><strong>48 мест</strong><br />вместимость</div><div><strong>24 кВт</strong><br />мощность</div></div>'
        f'<button class="complex-button">Сравнить комплектации{icon("arrow-right")}</button></section>'
    )
    return _page(project, shot, "engineering-configurator-mobile", body)


def _calendar_days() -> str:
    days = []
    for number in range(19, 33):
        label = number if number <= 31 else number - 31
        classes = ["calendar-day"]
        attrs = ""
        if number > 31:
            classes.append("muted")
        if number in {24, 25, 26}:
            classes.append("selected")
            attrs = ' aria-selected="true"'
        days.append(f'<button class="{" ".join(classes)}"{attrs}>{label}</button>')
    return "".join(days)


def _doma_u_ozera(project: ProjectSpec, shot: ShotSpec, assets: Mapping[str, str]) -> str:
    image = _hero_image(project, assets)
    nav = _nav(project, ("Дома", "Чем заняться", "Как добраться", "Условия"), "Найти дом", action_icon="calendar")
    if shot.variant == "cover":
        media = f'<div class="lake-media">{image}<p class="lake-caption">Сосновый берег, собственная терраса и тропа к воде</p></div>'
        search = (
            '<aside class="lake-search"><div class="complex-label">Тихий выходной у воды</div><h1>Дом, в который хочется вернуться</h1>'
            '<p>Выберите даты и состав гостей — покажем только свободные дома без скрытых условий.</p>'
            '<div class="lake-fields"><div class="complex-field">24–26 августа</div><div class="complex-field">4 гостя · без питомцев</div></div>'
            f'<button class="complex-button">Проверить даты{icon("calendar")}</button></aside>'
        )
        next_band = '<section class="lake-next-band"><span>Дом с сауной · до 6 гостей</span><span>от 18 000 ₽ / ночь</span><span>Смотреть все дома →</span></section>'
        return _page(project, shot, COMPLEX_LAYOUTS[project.slug][0], f"{nav}<div class=\"lake-cover\">{media}{search}</div>{next_band}")
    if shot.variant == "content":
        facts = '<div class="house-facts"><div><strong>6</strong>гостей</div><div><strong>3</strong>спальни</div><div><strong>104 м²</strong>площадь</div><div><strong>40 м</strong>до воды</div></div>'
        main = f'<div class="house-plan-main"><div class="complex-label">Дом с сауной</div><h2>Пространство для длинного выходного</h2>{image}{facts}</div>'
        aside = (
            '<aside class="house-plan-aside"><h3>План дома</h3><div class="plan-line"><span>Первый этаж</span><strong>Кухня-гостиная · сауна</strong></div>'
            '<div class="plan-line"><span>Второй этаж</span><strong>3 спальни · ванная</strong></div><div class="plan-line"><span>На участке</span><strong>Терраса · костровая зона</strong></div>'
            '<h3>Условия</h3><p>Заезд после 16:00, выезд до 12:00. Возвратный залог указан до бронирования.</p>'
            f'<button class="complex-button">Проверить доступность{icon("arrow-right")}</button></aside>'
        )
        return _page(project, shot, COMPLEX_LAYOUTS[project.slug][1], f"{nav}<section class=\"house-plan-page\">{main}{aside}</section>")
    if shot.variant == "function":
        calendar = (
            '<div class="booking-calendar-panel"><div class="calendar-head"><div><div class="complex-label">Август</div><h2>Выберите свободные даты</h2></div>'
            f'<button class="complex-button secondary">{icon("calendar")}2026</button></div><div class="calendar-grid">{_calendar_days()}</div></div>'
        )
        summary = (
            f'<aside class="booking-summary">{image}<div class="complex-label">Выбранный дом</div><h3>Дом с сауной</h3>'
            '<p>24–26 августа · 2 ночи · 4 гостя</p><div class="booking-price"><span>Проживание</span><span>36 000 ₽</span></div>'
            '<div class="booking-price"><span>Итого</span><span>36 000 ₽</span></div>'
            f'<button class="complex-button">Перейти к бронированию{icon("arrow-right")}</button></aside>'
        )
        return _page(project, shot, COMPLEX_LAYOUTS[project.slug][2], f"{nav}{_widget(project, calendar + summary, 'booking-workspace')}")
    body = (
        f'{nav}<section class="lake-mobile-body">{image}<div class="complex-label">Дом с сауной</div><h1>Выходной у озера</h1>'
        '<p>24–26 августа · 4 гостя</p><div class="mobile-date-strip"><div>Пт<br />24</div><div class="active">Сб<br />25</div><div>Вс<br />26</div></div>'
        f'<button class="complex-button">Проверить даты{icon("calendar")}</button></section>'
    )
    return _page(project, shot, "lakeside-search-mobile", body)


def _learning_sidebar(project: ProjectSpec, active: str) -> str:
    return _app_sidebar(project, ("Мои программы", "Расписание", "Задания", "Материалы"), active, "learning-sidebar")


def _lesson_outline(project: ProjectSpec) -> str:
    links = "".join(
        f'<a class="{"active" if link == "Мои программы" else ""}" href="#">{link}</a>'
        for link in ("Мои программы", "Расписание", "Задания", "Материалы")
    )
    lessons = (
        '<div class="outline-item">01 Введение · 06:20</div>'
        '<div class="outline-item active">02 Разбор заметок · 18:40</div>'
        '<div class="outline-item">03 Группировка сигналов · 12:15</div>'
        '<div class="outline-item">04 Практика · 25 минут</div>'
    )
    return (
        '<aside class="lesson-outline">'
        f'<a class="complex-brand" href="#">{escape_html(project.brand)}</a>'
        f'<nav class="lesson-menu">{links}</nav>{lessons}</aside>'
    )


def _praktika(project: ProjectSpec, shot: ShotSpec, assets: Mapping[str, str]) -> str:
    image = _hero_image(project, assets)
    if shot.variant == "cover":
        hero = (
            '<section class="learning-hero"><div><div class="complex-label">Программа в работе</div><h1>Продолжить обучение</h1>'
            '<p>Исследование продукта · модуль 4 из 7</p><div class="progress-track" aria-label="Пройдено 62 процента"><span></span></div>'
            f'<button class="complex-button">Открыть урок{icon("arrow-right")}</button></div>{image}</section>'
        )
        queue = ''.join(
            f'<article><div class="complex-label">{state}</div><h3>{title}</h3><p>{copy}</p></article>'
            for state, title, copy in (
                ("Сегодня", "Интервью: разбор заметок", "18 минут · видео и конспект"),
                ("До пятницы", "Собрать карту сигналов", "Практическое задание"),
                ("Готово", "Сценарий интервью", "Проверено наставником"),
            )
        )
        main = f'<div class="learning-main"><div class="learning-topline"><div><div class="complex-label">Личный кабинет</div><h2>Добрый день, Ирина</h2></div><span>3 уведомления</span></div>{hero}<div class="learning-queue">{queue}</div></div>'
        return _page(project, shot, COMPLEX_LAYOUTS[project.slug][0], f'<div class="learning-shell">{_learning_sidebar(project, "Мои программы")}{main}</div>')
    if shot.variant == "content":
        aside = f'<aside class="curriculum-aside"><div class="complex-label">Программа</div><h2>Исследование продукта</h2><p>7 модулей · 28 уроков · практический проект</p>{image}</aside>'
        lessons = "".join(
            f'<article class="lesson-row"><b>{index}</b><div><h3>{title}</h3><p>{copy}</p></div><span>{status}</span></article>'
            for index, title, copy, status in (
                ("01", "Постановка задачи", "Как связать исследование с продуктовым решением.", "Пройдено"),
                ("02", "Сценарий интервью", "Вопросы, последовательность и нейтральные формулировки.", "Пройдено"),
                ("03", "Полевые заметки", "Фиксация наблюдений без ранних выводов.", "Пройдено"),
                ("04", "Карта сигналов", "Синтез повторяющихся тем и противоречий.", "В работе"),
            )
        )
        main = f'<section class="curriculum-main"><div class="complex-label">Содержание курса</div><h2>От вопроса к проверяемому выводу</h2>{lessons}</section>'
        return _page(project, shot, COMPLEX_LAYOUTS[project.slug][1], f'<div class="curriculum-page">{aside}{main}</div>')
    if shot.variant == "function":
        outline = _lesson_outline(project)
        stage = (
            '<section class="lesson-stage"><div class="complex-label">Модуль 4 · урок 2</div><h2>Продолжить обучение</h2>'
            f'<div class="lesson-video" data-video-state="paused">{image}<div class="video-status">Пауза · 08:14 / 18:40</div></div>'
            '<div class="lesson-notes"><h3>Конспект урока</h3><p>Отделяйте дословные наблюдения от интерпретаций. '
            'Сначала соберите повторяющиеся сигналы, затем сформулируйте гипотезу.</p></div></section>'
        )
        task = (
            '<aside class="task-panel"><div class="complex-label">Практическое задание</div><h3>Карта сигналов</h3>'
            '<p>12 наблюдений распределены по четырём темам.</p>'
            f'<div class="task-complete" data-task-status="completed">{icon("check")}Задание выполнено</div>'
            '<div class="complex-field">Комментарий наставника · структура ясная</div>'
            '<button class="complex-button secondary">Открыть работу</button></aside>'
        )
        return _page(project, shot, COMPLEX_LAYOUTS[project.slug][2], _widget(project, outline + stage + task, "lesson-workspace"))
    nav = _nav(project, ("Программа", "Задания"), "Профиль", secondary="62% пройдено")
    body = (
        f'{nav}<section class="learning-mobile-body"><div class="complex-label">Модуль 4 · урок 2</div><h1>Интервью: разбор заметок</h1>{image}'
        '<div class="mobile-progress"><span>08:14</span><span>18:40</span></div><p>Следующий шаг — собрать карту повторяющихся сигналов.</p>'
        f'<button class="complex-button">Продолжить обучение{icon("arrow-right")}</button></section>'
    )
    return _page(project, shot, "learning-dashboard-mobile", body)


def _delivery_rows(selected: bool = False) -> str:
    deliveries = (
        ("GC-1842", "Химки → Тверская", "10:40–11:20", "В пути", "status-ok"),
        ("GC-1847", "Мытищи → Арбат", "11:30–12:10", "Погрузка", "status-warn"),
        ("GC-1851", "Люберцы → Сокол", "12:15–13:00", "Назначена", ""),
        ("GC-1856", "Подольск → Хамовники", "13:20–14:10", "Назначена", ""),
    )
    return "".join(
        f'<tr class="{"selected" if selected and code == "GC-1842" else ""}"><td><strong>{code}</strong></td>'
        f'<td>{route}</td><td>{window}</td><td class="{status_class}">{status}</td><td>Газель · 1,5 т</td></tr>'
        for code, route, window, status, status_class in deliveries
    )


def _delivery_table(selected: bool = False) -> str:
    return (
        '<table class="delivery-table"><thead><tr><th>Доставка</th><th>Маршрут</th><th>Окно</th><th>Статус</th><th>Машина</th></tr></thead>'
        f'<tbody>{_delivery_rows(selected)}</tbody></table>'
    )


def _ops_sidebar(project: ProjectSpec, active: str) -> str:
    return _app_sidebar(project, ("Обзор", "Доставки", "Маршруты", "Водители", "Отчёты"), active, "ops-sidebar")


def _gruzcontrol(project: ProjectSpec, shot: ShotSpec, assets: Mapping[str, str]) -> str:
    image = _hero_image(project, assets)
    if shot.variant == "cover":
        metrics = ''.join(
            f'<div class="ops-metric"><strong>{value}</strong><span>{label}</span></div>'
            for value, label in (("24", "доставки сегодня"), ("17", "в пути"), ("5", "на погрузке"), ("2", "требуют внимания"))
        )
        feed = (
            '<div class="ops-feed"><div class="ops-feed-row"><strong>GC-1842</strong><span>Химки → Тверская</span><span class="status-ok">В пути</span></div>'
            '<div class="ops-feed-row"><strong>GC-1847</strong><span>Мытищи → Арбат</span><span class="status-warn">Погрузка +12 мин</span></div>'
            '<div class="ops-feed-row"><strong>GC-1851</strong><span>Люберцы → Сокол</span><span>Назначена</span></div></div>'
        )
        main = (
            '<div class="ops-main"><header class="ops-head"><div><h1>Доставки сегодня</h1><p>Воскресенье, 23 августа</p></div>'
            '<button class="complex-button">Добавить доставку</button></header>'
            f'<section class="ops-metrics">{metrics}</section><div class="ops-board">{image}{feed}</div></div>'
        )
        return _page(project, shot, COMPLEX_LAYOUTS[project.slug][0], f'<div class="ops-shell">{_ops_sidebar(project, "Обзор")}{main}</div>')
    if shot.variant == "content":
        head = f'<div class="route-register-head"><div><div class="complex-label">Реестр</div><h2>Маршруты на 23 августа</h2><p>Фильтры по зоне, временному окну и текущему статусу.</p><div class="complex-tabs"><span class="complex-tab active">Все · 24</span><span class="complex-tab">В пути · 17</span><span class="complex-tab">Внимание · 2</span></div></div>{image}</div>'
        main = f'<section class="route-register-page">{head}{_delivery_table()}</section>'
        return _page(project, shot, COMPLEX_LAYOUTS[project.slug][1], f'<div class="ops-shell">{_ops_sidebar(project, "Доставки")}{main}</div>')
    if shot.variant == "function":
        table_area = (
            '<section class="delivery-list"><header class="ops-head"><div><div class="complex-label">Оперативный контроль</div><h2>Доставки сегодня</h2></div>'
            '<button class="complex-button secondary">Фильтры · 2</button></header>'
            '<div class="complex-tabs"><span class="complex-tab active">Все</span><span class="complex-tab">Опаздывают</span><span class="complex-tab">Без водителя</span></div>'
            f'<div class="delivery-map-strip">{image}<p>Выбрана доставка GC-1842. Курьер движется по маршруту, следующее событие — прибытие к получателю.</p></div>{_delivery_table(selected=True)}</section>'
        )
        drawer = (
            '<aside class="detail-drawer"><div class="complex-label">Карточка доставки</div><h2>GC-1842</h2><p class="status-ok">В пути · по графику</p>'
            '<div class="detail-line"><span>Маршрут</span><strong>Химки → Тверская</strong></div><div class="detail-line"><span>Окно</span><strong>10:40–11:20</strong></div>'
            '<div class="detail-line"><span>Водитель</span><strong>Илья Воронцов</strong></div><div class="detail-line"><span>Машина</span><strong>Газель · А412КХ</strong></div>'
            '<div class="detail-line"><span>Груз</span><strong>6 мест · 420 кг</strong></div><button class="complex-button secondary">Связаться с водителем</button></aside>'
        )
        widget = _widget(
            project,
            table_area + drawer,
            "delivery-workspace",
            attrs={"data-selected-delivery": "GC-1842"},
        )
        return _page(project, shot, COMPLEX_LAYOUTS[project.slug][2], f'<div class="ops-shell">{_ops_sidebar(project, "Доставки")}{widget}</div>')
    nav = _nav(project, ("Доставки", "Маршруты"), "Фильтры", action_icon="filter", secondary="24 сегодня")
    body = (
        f'{nav}<section class="ops-mobile-body"><div class="complex-label">Оперативный контроль</div><h1>Доставки сегодня</h1>{image}'
        '<article class="mobile-delivery"><strong><span>GC-1842</span><span class="status-ok">В пути</span></strong><p>Химки → Тверская · 10:40</p></article>'
        '<article class="mobile-delivery"><strong><span>GC-1847</span><span class="status-warn">Погрузка</span></strong><p>Мытищи → Арбат · 11:30</p></article>'
        '<article class="mobile-delivery"><strong><span>GC-1851</span><span>Назначена</span></strong><p>Люберцы → Сокол · 12:15</p></article></section>'
    )
    return _page(project, shot, "operations-overview-mobile", body)


_RENDERERS: dict[str, Callable[[ProjectSpec, ShotSpec, Mapping[str, str]], str]] = {
    "sever-market": _sever_market,
    "modulprof": _modulprof,
    "doma-u-ozera": _doma_u_ozera,
    "praktika": _praktika,
    "gruzcontrol": _gruzcontrol,
}


def render_complex(project: ProjectSpec, shot: ShotSpec, assets: dict[str, str]) -> str:
    """Render one complex portfolio concept for a declared shot variant."""
    try:
        renderer = _RENDERERS[project.slug]
    except KeyError as exc:
        raise KeyError(f"Unknown complex project: {project.slug}") from exc
    if shot.variant not in {"cover", "content", "function", "mobile"}:
        raise ValueError(f"Unknown complex shot variant: {shot.variant}")
    return renderer(project, shot, assets)
