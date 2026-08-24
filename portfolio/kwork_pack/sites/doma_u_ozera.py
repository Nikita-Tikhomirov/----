"""Direct-booking hospitality system for the Doma u Ozera portfolio project."""

from collections.abc import Mapping

from ..components import escape_html
from ..models import ProjectSpec, ShotSpec
from .runtime import RenderedPage


_ASSETS_BY_ROUTE = {
    "cover": ("lakeside_house",),
    "sauna-house": ("sauna_interior", "terrace_view"),
    "search": ("bedroom_detail",),
    "calendar": ("evening_pier",),
    "booking": ("host_portrait",),
}

_NAVIGATION = (
    ("cover", "Главная", "/"),
    ("search", "Дома", "/poisk-domov"),
    ("sauna-house", "Дом с сауной", "/booking/dom-s-saunoy"),
    ("calendar", "Свободные даты", "/svobodnye-daty"),
    ("booking", "Бронирование", "/bronirovanie"),
)


def _owned_assets(route: str, assets: Mapping[str, str]) -> dict[str, str]:
    try:
        keys = _ASSETS_BY_ROUTE[route]
    except KeyError as exc:
        raise ValueError(f"doma-u-ozera unknown route: {route}") from exc
    missing = [key for key in keys if key not in assets]
    if missing:
        raise KeyError(f"doma-u-ozera {route} missing assets: {', '.join(missing)}")
    return {key: escape_html(assets[key]) for key in keys}


def _header(active: str) -> str:
    links = "".join(
        f'<a href="{path}" class="{"is-active" if key == active else ""}">{label}</a>'
        for key, label, path in _NAVIGATION
    )
    return (
        '<header class="du-header">'
        '<a class="du-brand" href="/" aria-label="Дома у озера, главная">'
        '<i aria-hidden="true"><span></span><span></span><span></span></i>'
        '<span><strong>Дома у озера</strong><small>тихий берег · прямое бронирование</small></span>'
        '</a>'
        f'<nav class="du-nav" aria-label="Основная навигация">{links}</nav>'
        '<div class="du-direct"><span>Без комиссии сервисов</span><b>+7 921 440-18-22</b></div>'
        '</header>'
    )


def _cover(assets: Mapping[str, str]) -> str:
    guest_buttons = "".join(
        f'<button type="button" data-selectable="guest-count" data-value="{value}" '
        f'aria-pressed="{str(value == 4).lower()}">{value}</button>'
        for value in (2, 4, 6, 8)
    )
    return (
        '<main class="du-route du-cover-route">'
        '<section class="du-work du-cover-work">'
        '<aside class="du-cover-search" data-primary-rail>'
        '<p class="du-breadcrumb">Карелия · берег озера Сямозеро</p>'
        '<h1>Выходные у озера</h1>'
        '<p class="du-lead">Дом, тишина и свой спуск к воде. Бронируйте напрямую у хозяев.</p>'
        '<div class="du-date-pair"><label>Заезд<input type="date" value="2026-09-11" data-cover-arrival></label>'
        '<label>Выезд<input type="date" value="2026-09-13" data-cover-departure></label></div>'
        '<div class="du-control-label">Гостей</div>'
        f'<div class="du-segment" role="group" aria-label="Количество гостей">{guest_buttons}</div>'
        '<p class="du-field-state" data-cover-date-state>Доступность проверена напрямую</p>'
        '<button class="du-primary" type="button" data-cover-search>Проверить свободные дома</button>'
        '</aside>'
        '<section class="du-cover-content" data-primary-content>'
        '<figure class="du-cover-photo">'
        f'<img src="{assets["lakeside_house"]}" alt="Дом на лесном берегу озера с террасой">'
        '<figcaption><b>18 метров до воды</b><span>свой пирс · лодка · костровое место</span></figcaption>'
        '</figure>'
        '<aside class="du-cover-result" aria-live="polite">'
        '<span class="du-section-label">Найден дом на ваши даты</span>'
        '<h2 data-cover-house>Дом «Тихий берег»</h2>'
        '<p data-cover-summary>11–13 сентября · 2 ночи · 4 гостя</p>'
        '<dl class="du-price-breakdown"><div><dt>За ночь</dt><dd data-cover-nightly>18 600 ₽</dd></div>'
        '<div><dt>Проживание</dt><dd data-cover-stay>37 200 ₽</dd></div>'
        '<div><dt>Комиссия сервиса</dt><dd>0 ₽</dd></div></dl>'
        '<div class="du-total"><span>Итого за проживание</span><strong data-cover-total>37 200 ₽</strong></div>'
        '<p data-cover-result-state>Свободен · подтверждение хозяина не требуется</p>'
        '<a class="du-action-link" href="/bronirovanie">Перейти к бронированию</a>'
        '</aside></section></section>'
        '<section class="du-lower du-cover-lower" data-lower-band="true">'
        '<header><div><span>ПРЯМОЕ БРОНИРОВАНИЕ</span><h2>Дом для каждого ритма</h2></div>'
        '<p>Одна цена до оплаты, поддержка хозяина и понятные правила заезда.</p></header>'
        '<div class="du-house-assortment"><article><b>«Берёзы»</b><span>до 2 гостей</span><strong>14 400 ₽ / ночь</strong><p>Компактный дом для двоих.</p></article>'
        '<article><b>«Тихий берег»</b><span>до 4 гостей</span><strong>18 600 ₽ / ночь</strong><p>Терраса и спальня у леса.</p></article>'
        '<article><b>«Сосны»</b><span>до 6 гостей</span><strong>21 600 ₽ / ночь</strong><p>Три спальни и свой пирс.</p></article>'
        '<article><b>«Большая вода»</b><span>до 8 гостей</span><strong>26 400 ₽ / ночь</strong><p>Дом для большой компании.</p></article></div>'
        '<div class="du-direct-note"><b>30%</b><span>предоплата</span><p>Остаток при заселении. Возврат без штрафа за 7 дней.</p></div>'
        '</section></main>'
    )


def _sauna_house(assets: Mapping[str, str]) -> str:
    packages = (
        ("quiet", "Тихие будни", "43 200 ₽"),
        ("base", "Дом и сауна", "48 000 ₽"),
        ("sauna-plus", "Без ограничений", "52 800 ₽"),
    )
    controls = "".join(
        f'<button type="button" data-selectable="stay-package" data-value="{value}" '
        f'aria-pressed="{str(value == "base").lower()}"><span>{label}</span><b>{price}</b></button>'
        for value, label, price in packages
    )
    return (
        '<main class="du-route du-sauna-route">'
        '<section class="du-work du-sauna-work">'
        '<aside class="du-house-intro" data-primary-rail>'
        '<p class="du-breadcrumb">Дома / Дом с сауной</p><h1>Дом с сауной</h1>'
        '<p class="du-lead">Тёплый дом у воды для спокойного отдыха компанией до шести человек.</p>'
        '<dl class="du-house-facts"><div><dt>Спальных мест</dt><dd>6</dd></div><div><dt>Спален</dt><dd>3</dd></div>'
        '<div><dt>До воды</dt><dd>24 м</dd></div><div><dt>Заезд</dt><dd>после 16:00</dd></div></dl>'
        '<label class="du-number-field">Гостей<input type="number" min="1" max="6" value="4" data-stay-guests></label>'
        '<p class="du-field-state" data-stay-guest-state>Вместимость выбранного пакета: 6 гостей</p>'
        '<div class="du-amenities"><span>Дровяная сауна</span><span>Камин</span><span>Лодка</span><span>Мангал</span></div>'
        '</aside>'
        '<section class="du-sauna-content" data-primary-content>'
        '<div class="du-sauna-gallery"><figure>'
        f'<img src="{assets["sauna_interior"]}" alt="Светлая деревянная сауна в доме">'
        '<figcaption>Сауна внутри дома · готова к приезду</figcaption></figure><figure>'
        f'<img src="{assets["terrace_view"]}" alt="Терраса дома с видом на озеро">'
        '<figcaption>Терраса на шесть мест · вид на воду</figcaption></figure></div>'
        '<aside class="du-package-sheet"><span class="du-section-label">Выберите формат проживания</span>'
        f'<div class="du-package-controls">{controls}</div>'
        '<div class="du-package-result" aria-live="polite"><h2 data-stay-summary>Дом и сауна · 4 гостя</h2>'
        '<p data-stay-capacity>Пакет рассчитан на 6 гостей</p><p data-stay-sauna>Сауна 6 часов</p>'
        '<div class="du-total"><span>2 ночи · весь дом</span><strong data-stay-total>48 000 ₽</strong></div>'
        '<p>Дрова, полотенца и уборка включены.</p></div></aside>'
        '</section></section>'
        '<section class="du-lower du-sauna-lower" data-lower-band="true">'
        '<header><div><span>СОСТАВ ПРОЖИВАНИЯ</span><h2>Что входит в проживание</h2></div>'
        '<p>Без скрытых доплат после выбора пакета.</p></header>'
        '<div class="du-included-ledger"><div><b>Дом</b><span>3 спальни · кухня · камин</span><strong>включено</strong></div>'
        '<div><b>Сауна</b><span data-stay-lower-sauna>6 часов за выходные</span><strong>включено</strong></div>'
        '<div><b>У берега</b><span>лодка · пирс · мангал</span><strong>включено</strong></div>'
        '<div><b>Выезд</b><span>до 12:00 · уборка дома</span><strong>включено</strong></div></div>'
        '<aside class="du-rules"><b>Правила дома</b><p>Тишина после 23:00. Курение только на улице. Питомцы по согласованию.</p></aside>'
        '</section></main>'
    )


def _search(assets: Mapping[str, str]) -> str:
    houses = (
        ("berezy", "Дом «Берёзы»", 2, 1, False, True, 14400),
        ("tihiy", "Дом «Тихий берег»", 4, 2, False, True, 18600),
        ("sosny", "Дом «Сосны»", 6, 3, True, True, 21600),
        ("prichal", "Дом «Причал»", 6, 3, False, True, 19800),
        ("sauna", "Дом с сауной", 6, 2, True, False, 24000),
        ("water", "Дом «Большая вода»", 8, 4, True, True, 26400),
    )
    rows = "".join(
        f'<article data-house-row data-key="{key}" data-capacity="{capacity}" '
        f'data-bedrooms="{bedrooms}" data-sauna="{str(sauna).lower()}" '
        f'data-pets="{str(pets).lower()}" data-nightly="{nightly}" data-visible="true">'
        f'<span>{name}</span><b>{capacity} гостей · {bedrooms} спальни</b>'
        f'<i>{"сауна" if sauna else "у воды"} · {"питомцы да" if pets else "без питомцев"}</i>'
        f'<em>{nightly:,} ₽ / ночь</em><strong><span data-row-total>{nightly * 2:,} ₽</span><small data-row-nights>/ 2 ночи</small></strong></article>'.replace(",", " ")
        for key, name, capacity, bedrooms, sauna, pets, nightly in houses
    )
    return (
        '<main class="du-route du-search-route">'
        '<section class="du-work du-search-work">'
        '<aside class="du-search-filters" data-primary-rail>'
        '<p class="du-breadcrumb">Поиск домов</p><h1>Найдите дом для своей компании</h1>'
        '<div class="du-date-pair"><label>Заезд<input type="date" value="2026-09-11" data-search-arrival></label>'
        '<label>Выезд<input type="date" value="2026-09-13" data-search-departure></label></div>'
        '<label class="du-number-field">Гостей<input type="number" min="1" max="8" value="2" data-search-guests></label>'
        '<label class="du-select-field">Спален<select data-search-bedrooms><option value="all">Не важно</option>'
        '<option value="2">От 2 спален</option><option value="3">От 3 спален</option></select></label>'
        '<fieldset><legend>Удобства</legend><label><input type="checkbox" data-search-filter="sauna"> Сауна в доме</label>'
        '<label><input type="checkbox" data-search-filter="pets"> Можно с питомцем</label></fieldset>'
        '<p class="du-field-state" data-search-date-state>Цены рассчитаны на весь срок</p>'
        '</aside>'
        '<section class="du-search-content" data-primary-content>'
        '<div class="du-result-ledger"><header><div><span>ДОСТУПНО НА ВАШИ ДАТЫ</span><h2 data-search-count>6 домов</h2></div>'
        '<p data-search-summary>11–13 сентября · 2 ночи · 2 гостя</p></header>'
        f'<div class="du-house-rows">{rows}</div></div>'
        '<aside class="du-search-detail">'
        f'<img src="{assets["bedroom_detail"]}" alt="Спальня гостевого дома у озера">'
        '<span>БЛИЖАЙШИЙ ВАРИАНТ</span><h2 data-selected-house>Дом «Берёзы»</h2>'
        '<p data-selected-house-facts>2 гостя · 1 спальня · можно с питомцем</p>'
        '<strong data-selected-house-price>28 800 ₽ за 2 ночи</strong>'
        '<p>Предоплата 30%. Бесплатная отмена за 7 дней.</p></aside>'
        '</section></section>'
        '<section class="du-lower du-search-lower" data-lower-band="true">'
        '<header><div><span>КАК СЧИТАЕТСЯ ЦЕНА</span><h2>Никаких сборов в последнем шаге</h2></div>'
        '<p>В строке дома показана цена за весь выбранный срок, рядом — ставка за ночь.</p></header>'
        '<div class="du-search-proof"><div><b>01</b><span>Вы выбираете даты</span><p>Показываем только доступные дома.</p></div>'
        '<div><b>02</b><span>Фильтруете условия</span><p>Вместимость и правила уже учтены.</p></div>'
        '<div><b>03</b><span>Вносите 30%</span><p>Остаток оплачивается при заезде.</p></div></div>'
        '<aside class="du-search-policy"><b>Нужен совет?</b><p>Хозяин подскажет, какой дом подойдёт детям, питомцу или тихой компании.</p></aside>'
        '</section></main>'
    )


def _calendar(assets: Mapping[str, str]) -> str:
    blocked = {5, 6, 19, 20, 27}
    cells = '<span class="du-calendar-blank"></span>'
    for day in range(1, 31):
        is_blocked = day in blocked
        status = "занято" if is_blocked else ("мин. 2 ночи" if day in (11, 12, 13, 14, 15, 16) else "свободно")
        cells += (
            f'<button type="button" data-calendar-date="2026-09-{day:02d}" '
            f'data-day="{day}" {"disabled" if is_blocked else ""}><b>{day}</b><span>{status}</span></button>'
        )
    return (
        '<main class="du-route du-calendar-route">'
        '<section class="du-work du-calendar-work">'
        '<aside class="du-calendar-intro" data-primary-rail>'
        '<p class="du-breadcrumb">Бронирование / Сентябрь</p><h1>Свободные даты</h1>'
        '<p class="du-lead">Сравните доступность домов и выберите даты прямо в календаре.</p>'
        '<label class="du-select-field">Дом<select data-calendar-house><option value="sosny">Дом «Сосны»</option>'
        '<option value="sauna">Дом с сауной</option><option value="prichal">Дом «Причал»</option></select></label>'
        '<div class="du-calendar-legend"><span><i class="is-free"></i>Свободно</span><span><i class="is-min"></i>Минимум 2 ночи</span>'
        '<span><i class="is-busy"></i>Занято</span></div>'
        '<p class="du-field-state" data-calendar-state>Выбран диапазон на 2 ночи</p>'
        '<p class="du-iso-state" data-calendar-iso-state>Последняя выбранная дата: 2026-09-13</p>'
        f'<img src="{assets["evening_pier"]}" alt="Вечерний пирс у гостевых домов">'
        '</aside>'
        '<section class="du-calendar-content" data-primary-content>'
        '<div class="du-month"><header><button type="button" data-calendar-month="previous" aria-label="Предыдущий месяц">←</button>'
        '<div><span>2026</span><h2>Сентябрь</h2></div><button type="button" data-calendar-month="next" aria-label="Следующий месяц">→</button></header>'
        '<div class="du-weekdays"><span>Пн</span><span>Вт</span><span>Ср</span><span>Чт</span><span>Пт</span><span>Сб</span><span>Вс</span></div>'
        f'<div class="du-calendar-grid">{cells}</div></div>'
        '<aside class="du-calendar-result"><span class="du-section-label">Выбранные даты</span>'
        '<h2 data-calendar-summary>Дом «Сосны»<br>11–13 сентября · 2 ночи<br>43 200 ₽</h2>'
        '<dl><div><dt>Ставка</dt><dd data-calendar-nightly>21 600 ₽ / ночь</dd></div>'
        '<div><dt>Предоплата</dt><dd data-calendar-deposit>12 960 ₽</dd></div><div><dt>Остаток</dt><dd data-calendar-balance>30 240 ₽</dd></div></dl>'
        '<a class="du-action-link" href="/bronirovanie">Продолжить бронирование</a></aside>'
        '</section></section>'
        '<section class="du-lower du-calendar-lower" data-lower-band="true">'
        '<header><div><span>СПРОС НА СЕНТЯБРЬ</span><h2>Выходные разбирают раньше</h2></div>'
        '<p>В будни доступно больше домов, а стоимость остаётся такой же.</p></header>'
        '<div class="du-demand"><div><b>1–10 сентября</b><strong>спокойно</strong><span>12 свободных заездов</span></div>'
        '<div><b>11–20 сентября</b><strong>высокий спрос</strong><span>6 свободных заездов</span></div>'
        '<div><b>21–30 сентября</b><strong>средний спрос</strong><span>9 свободных заездов</span></div></div>'
        '<aside class="du-calendar-note"><b>Минимальный срок</b><p>В пятницу и субботу — 2 ночи. В будни можно приехать на одну ночь.</p></aside>'
        '</section></main>'
    )


def _booking(assets: Mapping[str, str]) -> str:
    return (
        '<main class="du-route du-booking-route">'
        '<section class="du-work du-booking-work">'
        '<form class="du-booking-form" data-primary-rail>'
        '<p class="du-breadcrumb">Шаг 1 из 2</p><h1>Бронирование</h1>'
        '<label class="du-select-field">Дом<select data-booking-house><option value="sosny">Дом «Сосны»</option>'
        '<option value="sauna">Дом с сауной</option><option value="prichal">Дом «Причал»</option></select></label>'
        '<div class="du-date-pair"><label>Заезд<input type="date" value="2026-09-11" data-booking-arrival></label>'
        '<label>Выезд<input type="date" value="2026-09-13" data-booking-departure></label></div>'
        '<label class="du-number-field">Гостей<input type="number" min="1" max="6" value="4" data-booking-guests></label>'
        '<p class="du-field-state" data-booking-date-state>2 ночи · даты доступны</p>'
        '<div class="du-contact-grid"><label>Имя<input type="text" data-booking-name placeholder="Как к вам обращаться"></label>'
        '<label>Телефон<input type="tel" data-booking-phone placeholder="+7 900 000-00-00"></label>'
        '<label>Email<input type="email" data-booking-email placeholder="mail@example.ru"></label></div>'
        '<p class="du-field-state" data-contact-state>Заполните имя, телефон и email</p>'
        '</form>'
        '<section class="du-booking-content" data-primary-content>'
        '<div class="du-booking-sheet"><span class="du-section-label">ВАША ПОЕЗДКА</span>'
        '<h2 data-booking-summary>Дом «Сосны» · 11–13 сентября · 2 ночи · 4 гостя</h2>'
        '<div class="du-extra-list"><label><input type="checkbox" data-booking-extra="sauna"><span><b>Сауна</b><small>подготовим к 18:00</small></span>'
        '<strong data-booking-extra-part="sauna">4 800 ₽</strong></label>'
        '<label><input type="checkbox" data-booking-extra="breakfast"><span><b>Завтрак</b><small>корзина местных продуктов</small></span>'
        '<strong data-booking-extra-part="breakfast">2 400 ₽</strong></label>'
        '<label><input type="checkbox" data-booking-extra="canoe"><span><b>Каноэ</b><small>на весь срок проживания</small></span>'
        '<strong data-booking-extra-part="canoe">1 200 ₽</strong></label></div>'
        '<dl class="du-booking-parts"><div><dt>Проживание</dt><dd data-booking-stay>43 200 ₽</dd></div>'
        '<div><dt>Дополнительно</dt><dd data-booking-extras>0 ₽</dd></div><div><dt>Итого</dt><dd data-booking-total>43 200 ₽</dd></div></dl>'
        '<div class="du-deposit"><span>К оплате сейчас · 30%</span><strong data-booking-deposit>12 960 ₽</strong><p>Остаток при заселении</p></div>'
        '<label class="du-consent"><input type="checkbox" data-booking-consent><span>Согласен с правилами дома и условиями отмены</span></label>'
        '<p class="du-field-state" data-consent-state>Нужно согласие для перехода к оплате</p>'
        '<button type="button" class="du-primary" data-booking-submit disabled>Подтвердить и перейти к оплате</button>'
        '<p data-booking-result>Бронь сохраняется на 20 минут после подтверждения.</p></div>'
        '<aside class="du-host">'
        f'<img src="{assets["host_portrait"]}" alt="Хозяин домов Алексей готовит дом к приезду гостей">'
        '<span>ХОЗЯИН ДОМОВ</span><h2>Алексей</h2><p>Отвечу про дорогу, баню и отдых с детьми.</p>'
        '<b>+7 921 440-18-22</b><small>обычно отвечает за 7 минут</small></aside>'
        '</section></section>'
        '<section class="du-lower du-booking-lower" data-lower-band="true">'
        '<header><div><span>УСЛОВИЯ БРОНИ</span><h2>Понятно до оплаты</h2></div>'
        '<p>Предоплата, отмена и правила дома зафиксированы в подтверждении.</p></header>'
        '<div class="du-policy-ledger"><div><b>Предоплата</b><span>30% сейчас</span><p>Остаток при заселении.</p></div>'
        '<div><b>Отмена</b><span>без штрафа за 7 дней</span><p>Позже — удержание предоплаты.</p></div>'
        '<div><b>Заезд</b><span>16:00–21:00</span><p>Поздний заезд по звонку.</p></div>'
        '<div><b>Тишина</b><span>после 23:00</span><p>Берег общий для всех гостей.</p></div></div>'
        '<aside class="du-booking-proof"><b data-booking-lower-total>43 200 ₽</b><span>итого за поездку</span><p>Цена закрепится после подтверждения.</p></aside>'
        '</section></main>'
    )


_CSS = """
.browser-window { width: 1920px; border-left: 0; border-right: 0; transform: translateX(-42px); }
.du-page, .du-page * { box-sizing: border-box; }
.du-page { width: 1920px; height: 1120px; overflow: hidden; background: #fff; color: #17312a; font-family: Arial, Helvetica, sans-serif; font-size: 14px; line-height: 1.35; }
.du-page button, .du-page input, .du-page select { font: inherit; letter-spacing: 0; }
.du-header { height: 96px; display: grid; grid-template-columns: 420px 1fr 310px; align-items: stretch; padding: 0 56px; background: #0d513e; color: #fff; border-bottom: 6px solid #c99a48; }
.du-brand { display: flex; gap: 17px; align-items: center; color: #fff; text-decoration: none; }
.du-brand > i { width: 54px; height: 45px; position: relative; border-bottom: 2px solid #fff; }
.du-brand > i span { position: absolute; bottom: 0; width: 18px; height: 34px; border: 2px solid #fff; border-bottom: 0; transform: skew(-20deg); }
.du-brand > i span:nth-child(1) { left: 2px; height: 29px; }.du-brand > i span:nth-child(2) { left: 18px; height: 42px; }.du-brand > i span:nth-child(3) { left: 34px; height: 32px; }
.du-brand strong { display: block; font-family: Georgia, serif; font-size: 25px; font-weight: 600; }.du-brand small { display: block; margin-top: 2px; font-size: 12px; color: #dcecf1; }
.du-nav { min-width: 0; display: flex; justify-content: center; align-items: stretch; overflow: hidden; }
.du-nav a { min-width: 120px; display: flex; align-items: center; justify-content: center; padding: 0 17px; color: #dcecf1; text-decoration: none; border-bottom: 4px solid transparent; white-space: nowrap; }
.du-nav a.is-active { color: #fff; border-bottom-color: #fff; }.du-direct { align-self: center; text-align: right; }.du-direct span, .du-direct b { display: block; }.du-direct span { color: #dcecf1; font-size: 12px; }.du-direct b { margin-top: 4px; font-size: 18px; }
.du-route { width: 1920px; height: 1024px; display: grid; grid-template-rows: 704px 320px; overflow: hidden; }
.du-work { min-width: 0; min-height: 0; display: grid; background: #fff; }.du-work > * { min-width: 0; min-height: 0; }
.du-cover-work { grid-template-columns: 480px 1440px; }.du-cover-content { display: grid; grid-template-columns: 900px 540px; }
.du-sauna-work { grid-template-columns: 490px 1430px; }.du-sauna-content { display: grid; grid-template-columns: 850px 580px; }
.du-search-work { grid-template-columns: 400px 1520px; }.du-search-content { display: grid; grid-template-columns: 970px 550px; }
.du-calendar-work { grid-template-columns: 380px 1540px; }.du-calendar-content { display: grid; grid-template-columns: 990px 550px; }
.du-booking-work { grid-template-columns: 500px 1420px; }.du-booking-content { display: grid; grid-template-columns: 850px 570px; }
.du-breadcrumb, .du-section-label, .du-lower header span, .du-result-ledger header span, .du-search-detail > span, .du-host > span { margin: 0; color: #b83d4b; font-size: 12px; font-weight: 700; text-transform: uppercase; }
.du-page h1, .du-page h2, .du-page p, .du-page figure, .du-page dl { margin-top: 0; }.du-page h1 { margin-bottom: 18px; font-family: Georgia, serif; font-size: 44px; line-height: 1.05; font-weight: 500; }.du-page h2 { font-family: Georgia, serif; font-weight: 500; }.du-lead { font-size: 18px; line-height: 1.5; color: #48645c; }
.du-cover-search, .du-house-intro, .du-search-filters, .du-calendar-intro, .du-booking-form { padding: 42px 38px 30px 56px; border-right: 1px solid #ccd8d2; background: #eff1ed; }
.du-date-pair { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 27px 0 20px; }.du-date-pair label, .du-contact-grid label { display: grid; gap: 7px; font-size: 12px; font-weight: 700; }
.du-page input, .du-page select { width: 100%; height: 46px; padding: 0 12px; color: #17312a; background: #fff; border: 1px solid #96aaa1; outline: 0; }.du-page input:focus, .du-page select:focus { border-color: #0d513e; box-shadow: inset 0 0 0 1px #0d513e; }
.du-control-label { margin: 0 0 8px; font-size: 12px; font-weight: 700; }.du-segment { display: grid; grid-template-columns: repeat(4, 1fr); }.du-segment button { height: 44px; border: 1px solid #96aaa1; border-right: 0; background: #fff; color: #17312a; }.du-segment button:last-child { border-right: 1px solid #96aaa1; }.du-segment button[aria-pressed="true"] { background: #0d513e; color: #fff; }
.du-primary { width: 100%; min-height: 48px; border: 0; background: #b83d4b; color: #fff; font-weight: 700; cursor: pointer; }.du-primary:disabled { background: #9ba8a3; cursor: default; }.du-field-state { min-height: 36px; margin: 12px 0; color: #61776d; font-size: 12px; }.du-action-link { display: flex; min-height: 48px; align-items: center; justify-content: center; background: #0d513e; color: #fff; text-decoration: none; font-weight: 700; }
.du-cover-photo { position: relative; height: 704px; margin: 0; border-right: 1px solid #ccd8d2; }.du-cover-photo img { width: 100%; height: 650px; display: block; object-fit: cover; }.du-cover-photo figcaption { height: 54px; display: flex; justify-content: space-between; align-items: center; padding: 0 28px; background: #dcecf1; }.du-cover-photo figcaption span { color: #48645c; }
.du-cover-result { padding: 48px 52px; }.du-cover-result h2 { margin: 20px 0 10px; font-size: 34px; }.du-cover-result > p { color: #61776d; }.du-price-breakdown { margin: 34px 0 18px; border-top: 1px solid #ccd8d2; }.du-price-breakdown div, .du-calendar-result dl div, .du-booking-parts div { display: flex; justify-content: space-between; padding: 15px 0; border-bottom: 1px solid #ccd8d2; }.du-price-breakdown dd, .du-calendar-result dd, .du-booking-parts dd { margin: 0; font-weight: 700; }.du-total { margin: 20px 0; padding: 18px; background: #dcecf1; border-left: 4px solid #0d513e; }.du-total span, .du-total strong { display: block; }.du-total strong { margin-top: 6px; font-family: Georgia, serif; font-size: 31px; color: #0d513e; }
.du-lower { min-width: 0; height: 320px; display: grid; align-content: stretch; border-top: 1px solid #ccd8d2; background: #fff; }.du-lower header { padding: 30px 42px 20px 56px; background: #0d513e; color: #fff; }.du-lower header span { color: #dcecf1; }.du-lower header h2 { margin: 8px 0; font-size: 28px; }.du-lower header p { margin: 0; color: #dcecf1; }
.du-cover-lower { grid-template-columns: 390px 1fr 260px; }.du-house-assortment { display: grid; grid-template-columns: repeat(4, 1fr); }.du-house-assortment article { padding: 30px 24px; border-right: 1px solid #ccd8d2; }.du-house-assortment b, .du-house-assortment span, .du-house-assortment strong { display: block; }.du-house-assortment b { font-family: Georgia, serif; font-size: 22px; }.du-house-assortment span { margin: 8px 0; color: #61776d; }.du-house-assortment strong { color: #b83d4b; }.du-direct-note, .du-rules, .du-search-policy, .du-calendar-note, .du-booking-proof { padding: 34px 28px; background: #dcecf1; }.du-direct-note b { display: block; font-family: Georgia, serif; font-size: 46px; color: #b83d4b; }.du-direct-note span { font-weight: 700; }
.du-house-facts { display: grid; grid-template-columns: 1fr 1fr; margin: 26px 0 20px; border-top: 1px solid #ccd8d2; }.du-house-facts div { padding: 12px 0; border-bottom: 1px solid #ccd8d2; }.du-house-facts dt { color: #61776d; font-size: 12px; }.du-house-facts dd { margin: 4px 0 0; font-weight: 700; }.du-number-field, .du-select-field { display: grid; gap: 7px; margin: 16px 0; font-size: 12px; font-weight: 700; }.du-amenities { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }.du-amenities span { padding: 8px; border-left: 3px solid #c99a48; background: #fff; }
.du-sauna-gallery { display: grid; grid-template-columns: 1.2fr .8fr; grid-template-rows: 704px; }.du-sauna-gallery figure { min-width: 0; margin: 0; position: relative; border-right: 1px solid #fff; }.du-sauna-gallery img { width: 100%; height: 650px; display: block; object-fit: cover; }.du-sauna-gallery figcaption { height: 54px; display: flex; align-items: center; padding: 0 20px; background: #dcecf1; font-size: 12px; }.du-package-sheet { padding: 42px 44px; }.du-package-controls { margin: 17px 0; }.du-package-controls button { width: 100%; min-height: 63px; display: flex; justify-content: space-between; align-items: center; padding: 0 16px; border: 1px solid #ccd8d2; border-bottom: 0; background: #fff; color: #17312a; }.du-package-controls button:last-child { border-bottom: 1px solid #ccd8d2; }.du-package-controls button[aria-pressed="true"] { background: #0d513e; color: #fff; }.du-package-result h2 { margin: 20px 0 8px; font-size: 25px; }.du-package-result > p { margin-bottom: 7px; color: #61776d; }
.du-sauna-lower { grid-template-columns: 390px 1fr 330px; }.du-included-ledger { display: grid; grid-template-columns: 1fr 1fr; }.du-included-ledger div { min-width: 0; display: grid; grid-template-columns: 100px 1fr 86px; align-items: center; gap: 12px; padding: 20px 24px; border-right: 1px solid #ccd8d2; border-bottom: 1px solid #ccd8d2; }.du-included-ledger span { color: #61776d; }.du-included-ledger strong { color: #0d513e; font-size: 12px; }.du-rules b, .du-search-policy b, .du-calendar-note b, .du-booking-proof b { font-family: Georgia, serif; font-size: 24px; }
.du-search-filters h1 { font-size: 38px; }.du-search-filters fieldset { margin: 18px 0; padding: 14px; border: 1px solid #96aaa1; }.du-search-filters legend { font-size: 12px; font-weight: 700; }.du-search-filters fieldset label { display: block; margin: 10px 0; }.du-search-filters input[type="checkbox"], .du-extra-list input, .du-consent input { width: 18px; height: 18px; accent-color: #0d513e; vertical-align: middle; }
.du-result-ledger { padding: 34px 28px 24px 34px; }.du-result-ledger header { height: 72px; display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 2px solid #0d513e; }.du-result-ledger header h2 { margin: 5px 0 0; font-size: 28px; }.du-result-ledger header p { margin: 24px 0 0; color: #61776d; }.du-house-rows { height: 565px; overflow: hidden; }.du-house-rows article { height: 86px; display: grid; grid-template-columns: 220px 160px 170px 135px 150px; gap: 12px; align-items: center; padding: 0 14px; border-bottom: 1px solid #ccd8d2; }.du-house-rows article[data-visible="false"] { display: none; }.du-house-rows article > span { font-family: Georgia, serif; font-size: 17px; }.du-house-rows article i, .du-house-rows article em { color: #61776d; font-style: normal; }.du-house-rows article strong { color: #b83d4b; text-align: right; }.du-house-rows article strong span, .du-house-rows article strong small { display: block; }.du-house-rows article strong small { margin-top: 3px; color: #61776d; font-size: 12px; }
.du-search-detail { padding: 34px 42px; border-left: 1px solid #ccd8d2; background: #eff1ed; }.du-search-detail img { width: 100%; height: 310px; display: block; margin-bottom: 24px; object-fit: cover; }.du-search-detail h2 { margin: 10px 0; font-size: 27px; }.du-search-detail > strong { display: block; margin: 25px 0 12px; font-family: Georgia, serif; font-size: 27px; color: #b83d4b; }.du-search-detail p { color: #61776d; }
.du-search-lower { grid-template-columns: 390px 1fr 330px; }.du-search-proof { display: grid; grid-template-columns: repeat(3, 1fr); }.du-search-proof > div { padding: 34px 28px; border-right: 1px solid #ccd8d2; }.du-search-proof b { display: block; color: #c99a48; font-size: 18px; }.du-search-proof span { display: block; margin: 10px 0; font-weight: 700; font-size: 17px; }.du-search-proof p { color: #61776d; }
.du-calendar-intro img { width: 100%; height: 215px; display: block; margin-top: 18px; object-fit: cover; }.du-calendar-legend { display: grid; gap: 8px; margin: 20px 0; }.du-calendar-legend span { display: flex; align-items: center; gap: 9px; }.du-calendar-legend i { width: 13px; height: 13px; border: 1px solid #96aaa1; }.du-calendar-legend .is-free { background: #fff; }.du-calendar-legend .is-min { background: #dcecf1; border-color: #0d513e; }.du-calendar-legend .is-busy { background: #ccd8d2; }.du-iso-state { min-height: 20px; color: #61776d; font-size: 12px; }
.du-month { padding: 30px 34px; }.du-month > header { height: 70px; display: grid; grid-template-columns: 46px 1fr 46px; align-items: center; text-align: center; }.du-month > header button { width: 42px; height: 42px; border: 1px solid #96aaa1; background: #fff; color: #0d513e; font-size: 22px; }.du-month > header h2 { margin: 1px 0; font-size: 27px; }.du-month > header span { color: #61776d; font-size: 12px; }.du-weekdays, .du-calendar-grid { display: grid; grid-template-columns: repeat(7, 1fr); }.du-weekdays span { height: 30px; text-align: center; color: #61776d; font-size: 12px; }.du-calendar-grid { border-top: 1px solid #ccd8d2; border-left: 1px solid #ccd8d2; }.du-calendar-grid button, .du-calendar-blank { height: 100px; display: flex; flex-direction: column; align-items: flex-start; padding: 11px; border: 0; border-right: 1px solid #ccd8d2; border-bottom: 1px solid #ccd8d2; background: #fff; color: #17312a; text-align: left; }.du-calendar-grid button b { font-family: Georgia, serif; font-size: 19px; }.du-calendar-grid button span { margin-top: auto; color: #61776d; font-size: 12px; }.du-calendar-grid button[disabled] { background: #eff1ed; color: #9ba8a3; }.du-calendar-grid button[aria-pressed="true"] { background: #dcecf1; box-shadow: inset 0 0 0 2px #0d513e; }.du-calendar-blank { background: #eff1ed; }
.du-calendar-result { padding: 42px 46px; border-left: 1px solid #ccd8d2; background: #eff1ed; }.du-calendar-result h2 { min-height: 120px; margin: 20px 0; font-size: 27px; line-height: 1.45; }.du-calendar-result dl { margin: 0 0 24px; }.du-calendar-lower { grid-template-columns: 390px 1fr 350px; }.du-demand { display: grid; grid-template-columns: repeat(3, 1fr); }.du-demand div { padding: 42px 30px; border-right: 1px solid #ccd8d2; }.du-demand b, .du-demand strong, .du-demand span { display: block; }.du-demand strong { margin: 14px 0; color: #b83d4b; font-size: 18px; }.du-demand span { color: #61776d; }
.du-booking-form h1 { margin-bottom: 12px; }.du-contact-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }.du-contact-grid label:last-child { grid-column: 1 / -1; }.du-booking-sheet { padding: 34px 42px; }.du-booking-sheet > h2 { min-height: 56px; margin: 10px 0 14px; font-size: 23px; }.du-extra-list { border-top: 1px solid #ccd8d2; }.du-extra-list label { min-height: 60px; display: grid; grid-template-columns: 24px 1fr 100px; gap: 12px; align-items: center; border-bottom: 1px solid #ccd8d2; }.du-extra-list span b, .du-extra-list span small { display: block; }.du-extra-list span small { color: #61776d; font-size: 12px; }.du-extra-list strong { text-align: right; }.du-booking-parts { margin: 10px 0; }.du-booking-parts div { padding: 9px 0; }.du-deposit { padding: 13px 17px; background: #dcecf1; border-left: 4px solid #b83d4b; }.du-deposit span, .du-deposit strong { display: block; }.du-deposit strong { margin: 2px 0; font-family: Georgia, serif; font-size: 29px; color: #b83d4b; }.du-deposit p { margin: 0; font-size: 12px; }.du-consent { min-height: 44px; display: flex; align-items: center; gap: 12px; }.du-booking-sheet > [data-booking-result] { min-height: 20px; margin: 8px 0 0; color: #61776d; font-size: 12px; }
.du-host { padding: 34px 46px; border-left: 1px solid #ccd8d2; background: #eff1ed; }.du-host img { width: 100%; height: 360px; display: block; margin-bottom: 22px; object-fit: cover; object-position: center 30%; }.du-host h2 { margin: 8px 0; font-size: 28px; }.du-host p { color: #61776d; }.du-host b, .du-host small { display: block; }.du-host b { margin-top: 24px; font-size: 19px; }.du-host small { margin-top: 5px; color: #61776d; font-size: 12px; }
.du-booking-lower { grid-template-columns: 390px 1fr 310px; }.du-policy-ledger { display: grid; grid-template-columns: repeat(4, 1fr); }.du-policy-ledger div { padding: 34px 24px; border-right: 1px solid #ccd8d2; }.du-policy-ledger b, .du-policy-ledger span { display: block; }.du-policy-ledger span { margin: 12px 0; color: #b83d4b; font-weight: 700; }.du-policy-ledger p { color: #61776d; }.du-booking-proof b { display: block; font-size: 32px; color: #b83d4b; }.du-booking-proof span { font-weight: 700; }
"""


_COMMON_SCRIPT = r"""
const duMoney = (value) => new Intl.NumberFormat('ru-RU').format(value).replace(/\u00a0/g, ' ') + ' ₽';
const duDate = (value) => new Date(value + 'T12:00:00');
const duIso = (date) => date.toISOString().slice(0, 10);
const duAddDays = (value, days) => { const date = duDate(value); date.setDate(date.getDate() + days); return duIso(date); };
const duNights = (arrival, departure) => Math.max(1, Math.round((duDate(departure) - duDate(arrival)) / 86400000));
const duNightWord = (count) => count === 1 ? 'ночь' : (count >= 2 && count <= 4 ? 'ночи' : 'ночей');
const duGuestWord = (count) => count === 1 ? 'гость' : (count >= 2 && count <= 4 ? 'гостя' : 'гостей');
const duRange = (arrival, departure) => {
  const months = ['января','февраля','марта','апреля','мая','июня','июля','августа','сентября','октября','ноября','декабря'];
  const start = duDate(arrival); const end = duDate(departure);
  if (start.getMonth() === end.getMonth()) return `${start.getDate()}–${end.getDate()} ${months[end.getMonth()]}`;
  return `${start.getDate()} ${months[start.getMonth()]} – ${end.getDate()} ${months[end.getMonth()]}`;
};
const duNormalizeNumber = (input, minimum, maximum) => {
  const parsed = Number.parseInt(input.value, 10);
  const value = Number.isFinite(parsed) ? Math.min(maximum, Math.max(minimum, parsed)) : minimum;
  input.value = String(value); return value;
};
const duNormalizeDates = (arrival, departure) => {
  if (!arrival.value) arrival.value = '2026-09-11';
  let corrected = false;
  if (!departure.value || duDate(departure.value) <= duDate(arrival.value)) {
    departure.value = duAddDays(arrival.value, 1); corrected = true;
  }
  return { arrival: arrival.value, departure: departure.value, corrected };
};
const duSelect = (buttons, selected) => buttons.forEach((button) => button.setAttribute('aria-pressed', String(button === selected)));
"""


def _scoped_script(body: str) -> str:
    return f"(() => {{\n{_COMMON_SCRIPT}\n{body}\n}})();"


_COVER_SCRIPT = _scoped_script(r"""
(() => {
  const root = document.querySelector('.du-page');
  const arrival = root.querySelector('[data-cover-arrival]');
  const departure = root.querySelector('[data-cover-departure]');
  const buttons = [...root.querySelectorAll('[data-selectable="guest-count"]')];
  const offers = {2: ['Дом «Берёзы»', 14400], 4: ['Дом «Тихий берег»', 18600], 6: ['Дом «Сосны»', 21600], 8: ['Дом «Большая вода»', 26400]};
  let guests = 4;
  const update = () => {
    const dates = duNormalizeDates(arrival, departure); const nights = duNights(dates.arrival, dates.departure);
    const [house, nightly] = offers[guests];
    root.querySelector('[data-cover-house]').textContent = house;
    root.querySelector('[data-cover-summary]').textContent = `${duRange(dates.arrival, dates.departure)} · ${nights} ${duNightWord(nights)} · ${guests} ${duGuestWord(guests)}`;
    root.querySelector('[data-cover-nightly]').textContent = duMoney(nightly);
    root.querySelector('[data-cover-stay]').textContent = duMoney(nightly * nights);
    root.querySelector('[data-cover-total]').textContent = duMoney(nightly * nights);
    root.querySelector('[data-cover-date-state]').textContent = dates.corrected ? 'Дата выезда исправлена: минимум одна ночь' : 'Доступность проверена напрямую';
  };
  buttons.forEach((button) => button.addEventListener('click', () => { guests = Number(button.dataset.value); duSelect(buttons, button); update(); }));
  [arrival, departure].forEach((input) => input.addEventListener('input', update));
  root.querySelector('[data-cover-search]').addEventListener('click', () => { update(); root.querySelector('[data-cover-result-state]').textContent = 'Поиск обновлён · дом можно забронировать сразу'; });
  update();
})();
""")


_SAUNA_SCRIPT = _scoped_script(r"""
(() => {
  const root = document.querySelector('.du-page'); const guestInput = root.querySelector('[data-stay-guests]');
  const buttons = [...root.querySelectorAll('[data-selectable="stay-package"]')];
  const packages = {
    quiet: {name: 'Тихие будни', capacity: 4, total: 43200, sauna: 'Сауна 3 часа', lower: '3 часа за выходные'},
    base: {name: 'Дом и сауна', capacity: 6, total: 48000, sauna: 'Сауна 6 часов', lower: '6 часов за выходные'},
    'sauna-plus': {name: 'Сауна без ограничений', capacity: 6, total: 52800, sauna: 'Сауна без ограничений', lower: 'без ограничений по времени'},
  };
  let selected = 'base';
  const update = (requested) => {
    const item = packages[selected]; const parsed = Number.parseInt(guestInput.value, 10);
    const wasLimited = Number.isFinite(parsed) && parsed > item.capacity;
    const guests = duNormalizeNumber(guestInput, 1, item.capacity);
    root.querySelector('[data-stay-summary]').textContent = `${item.name} · ${guests} ${duGuestWord(guests)}`;
    root.querySelector('[data-stay-capacity]').textContent = `Пакет рассчитан на ${item.capacity} ${duGuestWord(item.capacity)}`;
    root.querySelector('[data-stay-sauna]').textContent = item.sauna;
    root.querySelector('[data-stay-total]').textContent = duMoney(item.total);
    root.querySelector('[data-stay-lower-sauna]').textContent = item.lower;
    root.querySelector('[data-stay-guest-state]').textContent = wasLimited ? 'Ограничено вместимостью пакета' : `Вместимость выбранного пакета: ${item.capacity} ${duGuestWord(item.capacity)}`;
  };
  buttons.forEach((button) => button.addEventListener('click', () => { selected = button.dataset.value; duSelect(buttons, button); update(true); }));
  guestInput.addEventListener('input', () => update(false)); update(false);
})();
""")


_SEARCH_SCRIPT = _scoped_script(r"""
(() => {
  const root = document.querySelector('.du-page'); const arrival = root.querySelector('[data-search-arrival]');
  const departure = root.querySelector('[data-search-departure]'); const guestsInput = root.querySelector('[data-search-guests]');
  const bedrooms = root.querySelector('[data-search-bedrooms]'); const sauna = root.querySelector('[data-search-filter="sauna"]');
  const pets = root.querySelector('[data-search-filter="pets"]'); const rows = [...root.querySelectorAll('[data-house-row]')];
  const houseWord = (count) => count === 1 ? 'дом' : (count >= 2 && count <= 4 ? 'дома' : 'домов');
  const update = () => {
    const dates = duNormalizeDates(arrival, departure); const nights = duNights(dates.arrival, dates.departure);
    const guests = duNormalizeNumber(guestsInput, 1, 8); const bedroomsValue = bedrooms.value;
    const visible = rows.filter((row) => Number(row.dataset.capacity) >= guests
      && (bedroomsValue === 'all' || Number(row.dataset.bedrooms) >= Number(bedroomsValue))
      && (!sauna.checked || row.dataset.sauna === 'true') && (!pets.checked || row.dataset.pets === 'true'));
    rows.forEach((row) => {
      const shown = visible.includes(row); row.dataset.visible = String(shown);
      row.querySelector('[data-row-total]').textContent = duMoney(Number(row.dataset.nightly) * nights);
      row.querySelector('[data-row-nights]').textContent = `/ ${nights} ${duNightWord(nights)}`;
    });
    root.querySelector('[data-search-count]').textContent = `${visible.length} ${houseWord(visible.length)}`;
    const terms = [`${duRange(dates.arrival, dates.departure)}`, `${nights} ${duNightWord(nights)}`, `${guests} ${duGuestWord(guests)}`];
    if (bedroomsValue !== 'all') terms.push(`от ${bedroomsValue} спален`); if (sauna.checked) terms.push('с сауной'); if (pets.checked) terms.push('с питомцем');
    root.querySelector('[data-search-summary]').textContent = terms.join(' · ');
    root.querySelector('[data-search-date-state]').textContent = dates.corrected ? 'Порядок дат исправлен: минимум одна ночь' : 'Цены рассчитаны на весь срок';
    const selected = visible[0];
    if (selected) {
      root.querySelector('[data-selected-house]').textContent = selected.querySelector('span').textContent;
      root.querySelector('[data-selected-house-facts]').textContent = `${selected.dataset.capacity} гостей · ${selected.dataset.bedrooms} спальни · ${selected.dataset.pets === 'true' ? 'можно с питомцем' : 'без питомцев'}`;
      root.querySelector('[data-selected-house-price]').textContent = `${duMoney(Number(selected.dataset.nightly) * nights)} за ${nights} ${duNightWord(nights)}`;
    }
  };
  [arrival, departure, guestsInput].forEach((input) => input.addEventListener('input', update));
  [bedrooms, sauna, pets].forEach((control) => control.addEventListener('change', update)); update();
})();
""")


_CALENDAR_SCRIPT = _scoped_script(r"""
(() => {
  const root = document.querySelector('.du-page'); const houseSelect = root.querySelector('[data-calendar-house]');
  const buttons = [...root.querySelectorAll('[data-calendar-date]')];
  const houses = {
    sosny: {name: 'Дом «Сосны»', nightly: 21600, blocked: [5,6,19,20,27]},
    sauna: {name: 'Дом с сауной', nightly: 24000, blocked: [7,8,18,19,26]},
    prichal: {name: 'Дом «Причал»', nightly: 19800, blocked: [3,4,21,22,29]},
  };
  let start = '2026-09-11'; let end = '2026-09-13';
  const paint = () => {
    const house = houses[houseSelect.value];
    buttons.forEach((button) => {
      const blocked = house.blocked.includes(Number(button.dataset.day)); button.disabled = blocked;
      button.setAttribute('aria-pressed', String(button.dataset.calendarDate === start || button.dataset.calendarDate === end));
      button.querySelector('span').textContent = blocked ? 'занято' : ([11,12,13,14,15,16].includes(Number(button.dataset.day)) ? 'мин. 2 ночи' : 'свободно');
    });
    if (!end) {
      root.querySelector('[data-calendar-summary]').innerHTML = `${house.name}<br>${start} · выберите дату выезда`;
      return;
    }
    const nights = duNights(start, end); const total = house.nightly * nights; const deposit = Math.round(total * .3);
    root.querySelector('[data-calendar-summary]').innerHTML = `${house.name}<br>${duRange(start, end)} · ${nights} ${duNightWord(nights)}<br>${duMoney(total)}`;
    root.querySelector('[data-calendar-nightly]').textContent = `${duMoney(house.nightly)} / ночь`;
    root.querySelector('[data-calendar-deposit]').textContent = duMoney(deposit); root.querySelector('[data-calendar-balance]').textContent = duMoney(total - deposit);
  };
  buttons.forEach((button) => button.addEventListener('click', () => {
    const value = button.dataset.calendarDate; root.querySelector('[data-calendar-iso-state]').textContent = `Последняя выбранная дата: ${value}`;
    if (end) { start = value; end = null; root.querySelector('[data-calendar-state]').textContent = 'Выберите дату выезда'; paint(); return; }
    if (duDate(value) <= duDate(start)) { end = start; start = value; root.querySelector('[data-calendar-state]').textContent = 'Порядок дат исправлен'; }
    else { end = value; root.querySelector('[data-calendar-state]').textContent = `Выбран диапазон на ${duNights(start, end)} ${duNightWord(duNights(start, end))}`; }
    paint();
  }));
  houseSelect.addEventListener('change', () => { root.querySelector('[data-calendar-state]').textContent = `Доступность обновлена: ${houses[houseSelect.value].name}`; paint(); });
  root.querySelector('[data-calendar-month="previous"]').addEventListener('click', () => { root.querySelector('[data-calendar-state]').textContent = 'Август закрыт для новых бронирований'; });
  root.querySelector('[data-calendar-month="next"]').addEventListener('click', () => { root.querySelector('[data-calendar-state]').textContent = 'Октябрь откроется после подтверждения хозяина'; });
  paint();
})();
""")


_BOOKING_SCRIPT = _scoped_script(r"""
(() => {
  const root = document.querySelector('.du-page'); const houseSelect = root.querySelector('[data-booking-house]');
  const arrival = root.querySelector('[data-booking-arrival]'); const departure = root.querySelector('[data-booking-departure]');
  const guestsInput = root.querySelector('[data-booking-guests]'); const consent = root.querySelector('[data-booking-consent]');
  const name = root.querySelector('[data-booking-name]'); const phone = root.querySelector('[data-booking-phone]'); const email = root.querySelector('[data-booking-email]');
  const submit = root.querySelector('[data-booking-submit]'); const extras = [...root.querySelectorAll('[data-booking-extra]')];
  const houses = {sosny: {name: 'Дом «Сосны»', nightly: 21600, capacity: 6}, sauna: {name: 'Дом с сауной', nightly: 24000, capacity: 6}, prichal: {name: 'Дом «Причал»', nightly: 19800, capacity: 6}};
  const extraPrices = {sauna: 4800, breakfast: 2400, canoe: 1200};
  const contactsValid = () => name.value.trim().length >= 2 && phone.value.replace(/\D/g, '').length >= 11 && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value.trim());
  const update = () => {
    const house = houses[houseSelect.value]; const dates = duNormalizeDates(arrival, departure); const nights = duNights(dates.arrival, dates.departure);
    const guests = duNormalizeNumber(guestsInput, 1, house.capacity); const stay = house.nightly * nights;
    const extrasTotal = extras.reduce((sum, input) => sum + (input.checked ? extraPrices[input.dataset.bookingExtra] : 0), 0); const total = stay + extrasTotal;
    root.querySelector('[data-booking-summary]').textContent = `${house.name} · ${duRange(dates.arrival, dates.departure)} · ${nights} ${duNightWord(nights)} · ${guests} ${duGuestWord(guests)}` + (extras.filter((item) => item.checked).length ? ` · ${extras.filter((item) => item.checked).map((item) => item.parentElement.querySelector('b').textContent).join(', ')}` : '');
    root.querySelector('[data-booking-stay]').textContent = duMoney(stay); root.querySelector('[data-booking-extras]').textContent = duMoney(extrasTotal);
    root.querySelector('[data-booking-total]').textContent = duMoney(total); root.querySelector('[data-booking-deposit]').textContent = duMoney(Math.round(total * .3)); root.querySelector('[data-booking-lower-total]').textContent = duMoney(total);
    root.querySelector('[data-booking-date-state]').textContent = dates.corrected ? 'Порядок дат исправлен: минимум одна ночь' : `${nights} ${duNightWord(nights)} · даты доступны`;
    const valid = contactsValid(); root.querySelector('[data-contact-state]').textContent = valid ? 'Контакты заполнены' : 'Заполните имя, телефон и email';
    root.querySelector('[data-consent-state]').textContent = consent.checked ? 'Согласие получено' : 'Нужно согласие для перехода к оплате'; submit.disabled = !(valid && consent.checked);
  };
  [houseSelect, consent, ...extras].forEach((control) => control.addEventListener('change', update));
  [arrival, departure, guestsInput, name, phone, email].forEach((input) => input.addEventListener('input', update));
  submit.addEventListener('click', () => { if (!submit.disabled) root.querySelector('[data-booking-result]').textContent = 'Бронь готова к оплате · цена и дом закреплены на 20 минут'; }); update();
})();
""")


_ROUTE_BUILDERS = {
    "cover": _cover,
    "sauna-house": _sauna_house,
    "search": _search,
    "calendar": _calendar,
    "booking": _booking,
}

_ROUTE_SCRIPTS = {
    "cover": _COVER_SCRIPT,
    "sauna-house": _SAUNA_SCRIPT,
    "search": _SEARCH_SCRIPT,
    "calendar": _CALENDAR_SCRIPT,
    "booking": _BOOKING_SCRIPT,
}


def render(
    project: ProjectSpec,
    shot: ShotSpec,
    assets: Mapping[str, str],
) -> RenderedPage:
    """Render one independent hospitality booking route."""
    try:
        builder = _ROUTE_BUILDERS[shot.key]
        scripts = _ROUTE_SCRIPTS[shot.key]
    except KeyError as exc:
        raise ValueError(f"doma-u-ozera unknown route: {shot.key}") from exc
    route_assets = _owned_assets(shot.key, assets)
    html = (
        f'<div class="du-page" data-site="{escape_html(project.slug)}" '
        f'data-route="{escape_html(shot.key)}">'
        f'{_header(shot.key)}{builder(route_assets)}</div>'
    )
    return RenderedPage(html=html, css=_CSS, scripts=scripts)
