"""Dedicated industrial product system for the Modulprof portfolio project."""

from collections.abc import Mapping

from ..components import escape_html
from ..models import ProjectSpec, ShotSpec
from .runtime import RenderedPage


_ASSETS_BY_ROUTE = {
    "cover": ("modular_building",),
    "catalog": ("factory_assembly",),
    "configurator": ("interior_module", "facade_detail"),
    "comparison": ("architect_portrait",),
    "projects": ("site_installation",),
}

_NAVIGATION = (
    ("cover", "Проекты", "/"),
    ("configurator", "Конфигуратор", "/konfigurator"),
    ("catalog", "Каталог", "/catalog/modulnye-zdaniya"),
    ("comparison", "Комплектации", "/sravnenie-komplektatsiy"),
    ("projects", "Производство", "/proekty"),
)


def _owned_assets(route: str, assets: Mapping[str, str]) -> dict[str, str]:
    try:
        keys = _ASSETS_BY_ROUTE[route]
    except KeyError as exc:
        raise ValueError(f"modulprof unknown route: {route}") from exc
    missing = [key for key in keys if key not in assets]
    if missing:
        raise KeyError(f"modulprof {route} missing assets: {', '.join(missing)}")
    return {key: escape_html(assets[key]) for key in keys}


def _header(active: str) -> str:
    links = "".join(
        f'<a href="{path}" class="{"is-active" if key == active else ""}">{label}</a>'
        for key, label, path in _NAVIGATION
    )
    return (
        '<header class="mp-header">'
        '<a class="mp-brand" href="/" aria-label="МодульПроф, главная">'
        '<strong>Модуль<span>Проф</span></strong>'
        '<small>модульные решения<br>для промышленности</small>'
        '</a>'
        f'<nav class="mp-nav" aria-label="Основная навигация">{links}</nav>'
        '<div class="mp-contact"><b>8 800 500-08-90</b><span>info@modulprof.ru</span></div>'
        '</header>'
    )


def _page_head(title: str, section: str, lead: str, metrics: tuple[tuple[str, str], ...]) -> str:
    metric_html = "".join(
        f'<div class="mp-head-metric"><span>{label}</span><b>{value}</b></div>'
        for label, value in metrics
    )
    return (
        '<section class="mp-page-head">'
        f'<div><p>{section}</p><h1>{title}</h1><span>{lead}</span></div>'
        f'<div class="mp-head-metrics">{metric_html}</div>'
        '</section>'
    )


def _cover(assets: Mapping[str, str]) -> str:
    purposes = (
        ("production", "Производство", True),
        ("office", "Офис", False),
        ("checkpoint", "КПП", False),
    )
    areas = (("72", "72 м²", False), ("108", "108 м²", True), ("144", "144 м²", False))
    purpose_buttons = "".join(
        f'<button type="button" data-selectable="building-purpose" data-value="{value}" '
        f'aria-pressed="{str(selected).lower()}">{label}</button>'
        for value, label, selected in purposes
    )
    area_buttons = "".join(
        f'<button type="button" data-selectable="building-area" data-value="{value}" '
        f'aria-pressed="{str(selected).lower()}">{label}</button>'
        for value, label, selected in areas
    )
    return (
        '<main class="mp-route mp-cover-route">'
        + _page_head(
            "Модульные здания под задачу производства",
            "ПРОЕКТНОЕ БЮРО / 24.08.2026",
            "Подбираем конструктив, инженерные системы и логистику в одном расчёте.",
            (("Произведено", "186 зданий"), ("Гарантия", "5 лет"), ("Монтаж", "от 8 дней")),
        )
        + '<section class="mp-work mp-cover-work">'
        '<aside class="mp-control-rail">'
        '<div class="mp-rail-index">01 / НАЗНАЧЕНИЕ</div>'
        '<h2>Исходные параметры</h2><p>Выберите функцию и полезную площадь здания.</p>'
        f'<div class="mp-segment mp-purpose-control">{purpose_buttons}</div>'
        '<label class="mp-label">Площадь комплекта</label>'
        f'<div class="mp-segment mp-area-control">{area_buttons}</div>'
        '<dl class="mp-proof-list"><div><dt>Каркас</dt><dd>Сталь С245</dd></div>'
        '<div><dt>Контроль</dt><dd>ОТК 4 этапа</dd></div><div><dt>Документы</dt><dd>КМ + КМД</dd></div></dl>'
        '</aside>'
        '<figure class="mp-building-stage">'
        f'<img src="{assets["modular_building"]}" alt="Производственное модульное здание МодульПроф">'
        '<figcaption><span>Сэндвич-панель 120 мм</span><span>Рама 6 000 мм</span><span>Ворота 4 000 × 4 500</span></figcaption>'
        '</figure>'
        '<aside class="mp-result-rail">'
        '<div class="mp-rail-index">Базовая спецификация</div>'
        '<span class="mp-result-code">MP / LIVE 04</span>'
        '<h2 data-cover-model>Производственный модуль MP-108</h2>'
        '<p data-cover-spec>108 м² · 18 × 6 м · холодный контур</p>'
        '<div class="mp-price" data-cover-price>2 160 000 ₽</div>'
        '<dl class="mp-result-list"><div><dt>Изготовление</dt><dd data-cover-term>30 рабочих дней</dd></div>'
        '<div><dt>Масса</dt><dd data-cover-weight>9 720 кг</dd></div><div><dt>Монтаж</dt><dd data-cover-install>8 дней</dd></div></dl>'
        '<a class="mp-primary-link" href="/konfigurator">Открыть конфигуратор →</a>'
        '</aside></section>'
        '<section class="mp-lower mp-cover-lower" data-lower-band="true">'
        '<div class="mp-lower-heading"><span>ЛИНЕЙКИ ЗДАНИЙ</span><h2>Серийный конструктив, проектная адаптация</h2></div>'
        '<div class="mp-family"><b>MP-A</b><strong>Административные</strong><span>36–360 м²</span><p>Офисы, штабы строительства, лаборатории.</p></div>'
        '<div class="mp-family"><b>MP-P</b><strong>Производственные</strong><span>72–1 440 м²</span><p>Цеха, ремонтные зоны, тёплые склады.</p></div>'
        '<div class="mp-family"><b>MP-C</b><strong>Контрольные</strong><span>18–144 м²</span><p>КПП, весовые и диспетчерские пункты.</p></div>'
        '<div class="mp-engineering-note"><b>12 узлов</b><span>проверены расчётом</span><p>Снеговой район I–V · СП 20.13330.2016</p></div>'
        '</section></main>'
    )


def _catalog(assets: Mapping[str, str]) -> str:
    return (
        '<main class="mp-route mp-catalog-route">'
        + _page_head(
            "Каталог модульных зданий",
            "ТИПОВЫЕ РЕШЕНИЯ / REV. 08",
            "Сравните серийные модели по назначению, площади и стадии готовности.",
            (("Серий", "24"), ("Регионов", "38"), ("Запуск", "от 24 дней")),
        )
        + '<section class="mp-work mp-catalog-work">'
        '<aside class="mp-filter-rail"><div class="mp-rail-index">Параметры поставки</div><h2>Фильтр решений</h2>'
        '<fieldset><legend>Назначение</legend>'
        '<label><input type="radio" name="catalog-purpose" data-catalog-purpose="office" checked> Офис</label>'
        '<label><input type="radio" name="catalog-purpose" data-catalog-purpose="warehouse"> Склад</label>'
        '<label><input type="radio" name="catalog-purpose" data-catalog-purpose="logistics"> Логистика</label></fieldset>'
        '<label class="mp-field">Площадь<select data-catalog-area><option value="all">Любая площадь</option>'
        '<option value="compact">До 100 м²</option><option value="large">От 200 м²</option></select></label>'
        '<label class="mp-field">Готовность<select data-catalog-readiness><option value="ready">С инженерией</option>'
        '<option value="shell">Контур</option><option value="turnkey">Под ключ</option></select></label>'
        '<div class="mp-filter-note"><b>Единая ведомость</b><p>Каркас, панели, инженерия и доставка в одной спецификации.</p></div></aside>'
        '<section class="mp-catalog-ledger"><header><div><span>РЕЗУЛЬТАТ ФИЛЬТРА</span><b data-building-count>9 решений</b></div>'
        '<p data-building-summary>Офисные модули · любая площадь · с инженерией</p></header>'
        '<div class="mp-building-rows">'
        '<article><span>MP-O72</span><b>Офис линейного персонала</b><i>72 м²</i><em>28 дней</em></article>'
        '<article><span>MP-O96</span><b>Административный блок</b><i>96 м²</i><em>32 дня</em></article>'
        '<article><span>MP-S180</span><b>Тёплый склад</b><i>180 м²</i><em>41 день</em></article>'
        '<article><span>MP-L240</span><b>Логистический терминал</b><i>240 м²</i><em>52 дня</em></article>'
        '<article><span>MP-L360</span><b>Зона комплектации</b><i>360 м²</i><em>58 дней</em></article>'
        '</div></section>'
        '<aside class="mp-building-detail">'
        f'<img src="{assets["factory_assembly"]}" alt="Сборка модульного здания на производственной линии">'
        '<div class="mp-detail-body"><span>ВЫБРАННАЯ МОДЕЛЬ</span><h2 data-selected-building>MP-O96 · административный блок</h2>'
        '<dl><div><dt>Каркас</dt><dd>С245 / 6 м</dd></div><div><dt>Готовность</dt><dd data-selected-readiness>С инженерией</dd></div>'
        '<div><dt>Поставка</dt><dd data-selected-delivery>32 дня</dd></div><div><dt>География</dt><dd data-selected-geography>ЦФО / ПФО</dd></div></dl></div></aside>'
        '</section>'
        '<section class="mp-lower mp-catalog-lower" data-lower-band="true">'
        '<div class="mp-lower-heading"><span>УСЛОВИЯ ЗАКУПКИ</span><h2>Поставка без скрытых позиций</h2><p>Стоимость фиксируется после обследования площадки.</p></div>'
        '<div class="mp-procurement"><b>01</b><strong>Проектирование</strong><p>АР, КР, КМ и привязка инженерных вводов.</p><span>7–12 дней</span></div>'
        '<div class="mp-procurement"><b>02</b><strong>Производство</strong><p>Заводская сборка и контроль геометрии.</p><span>24–45 дней</span></div>'
        '<div class="mp-procurement"><b>03</b><strong>Логистика</strong><p>Маршрут, разрешения и график монтажа.</p><span>1 документ</span></div>'
        '<div class="mp-procurement"><b>04</b><strong>Приёмка</strong><p>Паспорта материалов и исполнительная схема.</p><span>ОТК + ПНР</span></div>'
        '</section></main>'
    )


def _configurator(assets: Mapping[str, str]) -> str:
    part_rows = (
        ("Несущий каркас", "S = площадь × 10 000", "1 440 000 ₽"),
        ("Ограждающий контур", "панель 80 мм", "432 000 ₽"),
        ("Межэтажное усиление", "1 уровень", "0 ₽"),
        ("Отраслевая подготовка", "производство", "0 ₽"),
        ("Отопление", "не включено", "0 ₽"),
        ("Электроснабжение", "щиты + трассы", "270 000 ₽"),
        ("Водоснабжение", "не включено", "0 ₽"),
        ("Доставка", "базовый регион", "120 000 ₽"),
    )
    rows = "".join(
        f'<div class="mp-spec-row"><span>{index:02d}</span><b data-config-part-name>{name}</b>'
        f'<i data-config-part-note>{note}</i><strong data-config-part>{price}</strong></div>'
        for index, (name, note, price) in enumerate(part_rows, 1)
    )
    return (
        '<main class="mp-route mp-config-route">'
        + _page_head(
            "Конфигуратор здания",
            "РАСЧЁТ / ШАГ 2 ИЗ 5",
            "Все параметры сразу меняют площадь, массу, срок и состав комплекта.",
            (("Версия", "MP-CFG 3.4"), ("Расчёт", "онлайн"), ("Точность", "±7%")),
        )
        + '<section class="mp-work mp-config-work">'
        '<aside class="mp-config-controls"><div class="mp-rail-index">ИСХОДНЫЕ ДАННЫЕ</div>'
        '<label class="mp-field">Назначение<select data-config-purpose><option value="production">Производственный модуль</option>'
        '<option value="office">Административный модуль</option><option value="medical">Медицинский модуль</option></select></label>'
        '<div class="mp-dimension-grid"><label class="mp-field">Длина, м<input data-config-length type="number" min="6" max="30" value="12"></label>'
        '<label class="mp-field">Ширина, м<input data-config-width type="number" min="6" max="12" value="12"></label></div>'
        '<span class="mp-label">Этажность</span><div class="mp-segment"><button type="button" data-selectable="config-floor" data-value="1" aria-pressed="true">1 этаж</button>'
        '<button type="button" data-selectable="config-floor" data-value="2" aria-pressed="false">2 этажа</button></div>'
        '<span class="mp-label">Контур</span><div class="mp-segment"><button type="button" data-selectable="config-shell" data-value="cold" aria-pressed="true">Холодный</button>'
        '<button type="button" data-selectable="config-shell" data-value="warm" aria-pressed="false">Тёплый</button></div>'
        '<fieldset class="mp-system-list"><legend>Инженерные системы</legend>'
        '<label><input type="checkbox" data-config-option="heating"> Отопление</label>'
        '<label><input type="checkbox" data-config-option="electricity" checked> Электроснабжение</label>'
        '<label><input type="checkbox" data-config-option="plumbing"> Водоснабжение</label></fieldset>'
        '<label class="mp-field">Доставка<select data-config-delivery><option value="region">Базовый регион</option>'
        '<option value="pickup">Самовывоз</option><option value="north">Северная логистика</option></select></label></aside>'
        '<section class="mp-config-stage"><div class="mp-stage-tabs"><b>ВИЗУАЛИЗАЦИЯ</b><span>ПЛАНИРОВКА</span><span>УЗЛЫ</span></div>'
        '<div class="mp-stage-images"><figure><img src="' + assets["interior_module"] + '" alt="Интерьер модульного производственного помещения">'
        '<figcaption>Внутренний объём / инженерные трассы</figcaption></figure>'
        '<figure><img src="' + assets["facade_detail"] + '" alt="Фасадный узел модульного здания">'
        '<figcaption>Фасадный узел / панель 120 мм</figcaption></figure></div>'
        '<div class="mp-blueprint"><span>ОСИ 1–4</span><i></i><i></i><i></i><b>12 000</b><em>6 000</em></div></section>'
        '<aside class="mp-config-result"><div class="mp-rail-index">СОСТАВ КОМПЛЕКТА</div><span class="mp-result-code">РАСЧЁТ ОБНОВЛЁН</span>'
        '<h2 data-config-summary>144 м² · Производственный модуль · 1 этаж · Холодный контур · Базовый регион · 1 862 000 ₽</h2>'
        '<div class="mp-config-total" data-config-total>1 862 000 ₽</div>'
        '<dl class="mp-result-list"><div><dt>Срок</dt><dd data-config-term>31 рабочий день</dd></div>'
        '<div><dt>Масса</dt><dd data-config-weight>12 654 кг</dd></div><div><dt>Модулей</dt><dd data-config-modules>4 шт.</dd></div></dl>'
        '<div class="mp-system-state" data-config-systems>Электроснабжение · без отопления · без воды</div>'
        '<a class="mp-primary-link" href="/sravnenie-komplektatsiy">Сравнить комплектации →</a></aside>'
        '</section>'
        '<section class="mp-lower mp-config-lower" data-lower-band="true"><header><div><span>СПЕЦИФИКАЦИЯ / LIVE</span><h2>Состав комплекта</h2></div>'
        '<div><span>ИТОГО ПО ВЕДОМОСТИ</span><b data-config-ledger-total>1 862 000 ₽</b></div></header>'
        '<div class="mp-spec-head"><span>№</span><b>Позиция</b><i>Основание расчёта</i><strong>Стоимость</strong></div>'
        f'<div class="mp-spec-body">{rows}</div></section></main>'
    )


def _comparison(assets: Mapping[str, str]) -> str:
    features = (
        "Каркас С245",
        "Ограждающий контур",
        "Окна и двери",
        "Электроснабжение",
        "Отопление",
        "Водоснабжение",
        "Монтаж и ПНР",
    )
    rows = "".join(
        f'<div class="mp-compare-row" data-comparison-row data-included="{str(index < 6).lower()}">'
        f'<span>{feature}</span><b data-row-state>{"✓" if index < 6 else "—"}</b></div>'
        for index, feature in enumerate(features)
    )
    return (
        '<main class="mp-route mp-comparison-route">'
        + _page_head(
            "Сравнение комплектаций",
            "КОММЕРЧЕСКОЕ ПРЕДЛОЖЕНИЕ / 1187",
            "Три уровня готовности на единой конструктивной базе 216 м².",
            (("Основание", "216 м²"), ("Срок КП", "1 день"), ("Нормы", "7 документов")),
        )
        + '<section class="mp-work mp-compare-work">'
        '<aside class="mp-engineer-panel">'
        f'<img src="{assets["architect_portrait"]}" alt="Главный архитектор проекта МодульПроф">'
        '<span>ГЛАВНЫЙ АРХИТЕКТОР</span><h2>Анна Корнеева</h2><p>Проверяет планировочные ограничения и состав исходно-разрешительной документации.</p>'
        '<dl><div><dt>Стаж</dt><dd>14 лет</dd></div><div><dt>Проектов</dt><dd>68</dd></div></dl></aside>'
        '<section class="mp-package-matrix"><div class="mp-package-tabs">'
        '<button type="button" data-selectable="package" data-value="base" aria-pressed="false"><span>01</span><b>Базовая</b><i>3,24 млн ₽</i></button>'
        '<button type="button" data-selectable="package" data-value="engineering" aria-pressed="true"><span>02</span><b>Инженерная</b><i>4,68 млн ₽</i></button>'
        '<button type="button" data-selectable="package" data-value="turnkey" aria-pressed="false"><span>03</span><b>Под ключ</b><i>5,94 млн ₽</i></button>'
        f'</div><div class="mp-compare-rows">{rows}</div></section>'
        '<aside class="mp-package-result"><div class="mp-rail-index">АКТИВНАЯ КОМПЛЕКТАЦИЯ</div><span class="mp-result-code">MP-216 / E</span>'
        '<h2 data-package-summary>Инженерная · 6 из 7 позиций включено</h2><div class="mp-price" data-package-total>4 680 000 ₽</div>'
        '<dl class="mp-result-list"><div><dt>Производство</dt><dd data-package-term>42 дня</dd></div>'
        '<div><dt>Готовность</dt><dd data-package-compliance>6 из 7 · СП подтверждены</dd></div><div><dt>Гарантия</dt><dd>5 лет</dd></div></dl>'
        '<p data-package-note>Контур, электрика, отопление и заводская приёмка.</p><a class="mp-primary-link" href="/konfigurator">Изменить параметры →</a></aside>'
        '</section>'
        '<section class="mp-lower mp-comparison-lower" data-lower-band="true">'
        '<div class="mp-lower-heading"><span>Соответствие нормам</span><h2>Документы передаются вместе со зданием</h2></div>'
        '<div class="mp-standard"><b>СП 260.1325800.2016</b><span>Конструкции из тонкостенных профилей</span><i>В расчёте</i></div>'
        '<div class="mp-standard"><b>СП 20.13330.2016</b><span>Нагрузки и воздействия</span><i>Проверено</i></div>'
        '<div class="mp-standard"><b>СП 4.13130.2013</b><span>Ограничение распространения пожара</span><i>Учтено</i></div>'
        '<div class="mp-doc-ledger"><b>07</b><span>паспортов и схем</span><p>КМ · КМД · акты скрытых работ · паспорта материалов</p></div>'
        '</section></main>'
    )


def _projects(assets: Mapping[str, str]) -> str:
    rows = (
        ("industry", "central", "MP-2381", "Цех ремонта техники", "Калуга", "864 м²"),
        ("industry", "central", "MP-2390", "Сборочный корпус", "Тверь", "720 м²"),
        ("industry", "central", "MP-2401", "Лабораторный блок", "Обнинск", "360 м²"),
        ("industry", "volga", "MP-2414", "Линия упаковки", "Казань", "540 м²"),
        ("industry", "volga", "MP-2428", "Участок контроля", "Ижевск", "288 м²"),
        ("industry", "north", "MP-2442", "Ремонтная база", "Петрозаводск", "648 м²"),
        ("industry", "north", "MP-2455", "Энергетический модуль", "Выборг", "216 м²"),
        ("logistics", "central", "MP-2470", "Логистический терминал", "Тула", "1 080 м²"),
        ("logistics", "central", "MP-2476", "Кросс-докинг", "Подольск", "864 м²"),
        ("logistics", "central", "MP-2481", "Экспедиционный склад", "Орёл", "540 м²"),
        ("logistics", "volga", "MP-2484", "Зона комплектации", "Самара", "720 м²"),
        ("logistics", "volga", "MP-2488", "Терминал возвратов", "Саратов", "432 м²"),
        ("logistics", "north", "MP-2492", "Склад снабжения", "Мурманск", "720 м²"),
        ("logistics", "north", "MP-2498", "Арктический хаб", "Апатиты", "576 м²"),
        ("logistics", "north", "MP-2504", "Портовый склад", "Архангельск", "648 м²"),
        ("social", "north", "MP-2511", "Медицинский модуль", "Архангельск", "288 м²"),
        ("social", "north", "MP-2518", "Фельдшерский пункт", "Северодвинск", "144 м²"),
        ("social", "central", "MP-2522", "Учебный корпус", "Рязань", "432 м²"),
        ("social", "central", "MP-2529", "Спортивный блок", "Липецк", "360 м²"),
        ("social", "volga", "MP-2536", "Амбулатория", "Ульяновск", "216 м²"),
    )
    ledger = "".join(
        f'<article data-project-row data-sector="{sector}" data-region="{region}" data-visible="{str(sector == "logistics").lower()}">'
        f'<span>{code}</span><b>{name}</b><i>{city}</i><em>{area}</em><strong>Сдан</strong></article>'
        for sector, region, code, name, city, area in rows
    )
    return (
        '<main class="mp-route mp-projects-route">'
        + _page_head(
            "Реализованные проекты",
            "РЕЕСТР / 2024–2026",
            "Производственные, логистические и социальные объекты по всей России.",
            (("Сдано", "186"), ("В работе", "14"), ("Площадь", "94 800 м²")),
        )
        + '<section class="mp-work mp-project-work">'
        '<aside class="mp-project-filters"><div class="mp-rail-index">ФИЛЬТР РЕЕСТРА</div><h2>Отрасль проекта</h2>'
        '<div class="mp-sector-buttons"><button type="button" data-selectable="project-sector" data-value="industry" aria-pressed="false">Промышленность</button>'
        '<button type="button" data-selectable="project-sector" data-value="logistics" aria-pressed="true">Логистика</button>'
        '<button type="button" data-selectable="project-sector" data-value="social" aria-pressed="false">Социальные объекты</button></div>'
        '<label class="mp-field">Регион<select data-project-region><option value="all">Все регионы</option><option value="central">Центральный ФО</option>'
        '<option value="volga">Приволжский ФО</option><option value="north">Северо-Западный ФО</option></select></label>'
        '<div class="mp-project-count"><span>ВЫБРАНО</span><b data-project-count>8 проектов</b><p>Сданные объекты с исполнительной документацией.</p></div></aside>'
        '<section class="mp-project-ledger"><header><span>КОД</span><b>ОБЪЕКТ</b><i>ГОРОД</i><em>ПЛОЩАДЬ</em><strong>СТАТУС</strong></header>'
        f'<div>{ledger}</div></section>'
        '<aside class="mp-project-detail">'
        f'<img src="{assets["site_installation"]}" alt="Монтаж модульного здания на площадке заказчика">'
        '<div><span>ВЫБРАННЫЙ ОБЪЕКТ</span><h2 data-project-selection>Логистический терминал · Тула</h2>'
        '<dl><div><dt>Площадь</dt><dd data-project-area>1 080 м²</dd></div><div><dt>Монтаж</dt><dd data-project-install>18 дней</dd></div>'
        '<div><dt>Логистика</dt><dd data-project-logistics>420 км</dd></div><div><dt>Сдан</dt><dd data-project-date>июнь 2026</dd></div></dl></div></aside>'
        '</section>'
        '<section class="mp-lower mp-project-lower" data-lower-band="true">'
        '<div class="mp-lower-heading"><span>Производственный график</span><h2>От проекта до приёмки</h2><p>Контрольные точки закреплены в договоре поставки.</p></div>'
        '<div class="mp-timeline-step"><b>01</b><strong>Проектирование</strong><span>7–12 дней</span><i></i><p>Привязка и расчёты</p></div>'
        '<div class="mp-timeline-step"><b>02</b><strong>Комплектация</strong><span>5–8 дней</span><i></i><p>Материалы и карты ОТК</p></div>'
        '<div class="mp-timeline-step"><b>03</b><strong>Производство</strong><span>24–45 дней</span><i></i><p>Сборка и испытания</p></div>'
        '<div class="mp-timeline-step"><b>04</b><strong>Монтаж</strong><span>8–18 дней</span><i></i><p>ПНР и исполнительная схема</p></div>'
        '</section></main>'
    )


_CSS = r"""
.mp-page, .mp-page * { box-sizing: border-box; }
.mp-page { width: 1920px; height: 1120px; overflow: hidden; background: #e9ecee; color: #20262b; font-family: Arial, Helvetica, sans-serif; font-size: 14px; }
.mp-page button, .mp-page input, .mp-page select { font: inherit; color: inherit; }
.mp-header { width: 1834px; height: 72px; display: grid; grid-template-columns: 286px minmax(860px, 1fr) 254px; align-items: stretch; gap: 28px; padding: 0 34px; background: #20262b; color: #fff; border-bottom: 3px solid #ff6a1a; }
.mp-brand { display: flex; align-items: center; gap: 14px; color: #fff; text-decoration: none; min-width: 0; }
.mp-brand strong { font-size: 24px; white-space: nowrap; }
.mp-brand strong span { color: #ff6a1a; }
.mp-brand small { padding-left: 14px; border-left: 1px solid #69747c; color: #cbd1d5; font-size: 10px; line-height: 1.2; }
.mp-nav { min-width: 0; display: flex; align-items: stretch; justify-content: flex-start; overflow: hidden; }
.mp-nav a { display: flex; align-items: center; padding: 0 24px; color: #dfe3e6; text-decoration: none; white-space: nowrap; border-left: 1px solid #343b41; font-size: 13px; }
.mp-nav a:last-child { border-right: 1px solid #343b41; }
.mp-nav a.is-active { color: #fff; box-shadow: inset 0 -4px #ff6a1a; background: #2a3137; }
.mp-contact { display: flex; flex-direction: column; justify-content: center; align-items: flex-end; border-left: 1px solid #4a535a; line-height: 1.3; }
.mp-contact b { font-size: 16px; }.mp-contact span { color: #cbd1d5; font-size: 12px; }
.mp-route { width: 1834px; height: 1048px; min-height: 0; display: grid; grid-template-rows: 130px 600px 318px; overflow: hidden; background: #f4f5f6; }
.mp-page-head { display: flex; align-items: center; justify-content: space-between; padding: 22px 42px; background: #fff; border-bottom: 1px solid #c9cfd3; }
.mp-page-head > div:first-child { max-width: 960px; }.mp-page-head p { margin: 0 0 8px; color: #ff6a1a; font-size: 11px; font-weight: 700; }.mp-page-head h1 { margin: 0 0 6px; font-size: 30px; line-height: 1.05; }.mp-page-head > div > span { color: #69747c; font-size: 13px; }
.mp-head-metrics { display: flex; height: 70px; border: 1px solid #c9cfd3; }
.mp-head-metric { min-width: 150px; padding: 14px 18px; border-left: 1px solid #c9cfd3; display: flex; flex-direction: column; justify-content: center; }.mp-head-metric:first-child { border-left: 0; }.mp-head-metric span { color: #69747c; font-size: 11px; text-transform: uppercase; }.mp-head-metric b { margin-top: 6px; font-size: 18px; }
.mp-work { min-height: 0; border-bottom: 1px solid #aeb6bc; }.mp-work > * { min-width: 0; min-height: 0; }
.mp-control-rail, .mp-filter-rail, .mp-config-controls, .mp-result-rail, .mp-config-result, .mp-package-result, .mp-project-filters { padding: 24px; background: #fff; border-right: 1px solid #c9cfd3; overflow: hidden; }
.mp-result-rail, .mp-config-result, .mp-package-result { border-right: 0; border-left: 1px solid #c9cfd3; }
.mp-rail-index { color: #ff6a1a; font-size: 11px; font-weight: 700; letter-spacing: 0; }.mp-control-rail h2, .mp-filter-rail h2, .mp-project-filters h2 { margin: 12px 0 8px; font-size: 20px; }.mp-control-rail > p { margin: 0 0 20px; color: #69747c; line-height: 1.45; }
.mp-label { display: block; margin: 22px 0 8px; color: #69747c; font-size: 11px; font-weight: 700; text-transform: uppercase; }
.mp-segment { display: flex; border: 1px solid #aeb6bc; }.mp-segment button { flex: 1; height: 42px; border: 0; border-left: 1px solid #aeb6bc; background: #fff; cursor: pointer; font-size: 12px; }.mp-segment button:first-child { border-left: 0; }.mp-segment button[aria-pressed="true"] { background: #20262b; color: #fff; box-shadow: inset 0 -3px #ff6a1a; }
.mp-proof-list, .mp-result-list, .mp-building-detail dl, .mp-project-detail dl, .mp-engineer-panel dl { margin: 24px 0 0; border-top: 1px solid #d7dcdf; }.mp-proof-list div, .mp-result-list div, .mp-building-detail dl div, .mp-project-detail dl div, .mp-engineer-panel dl div { display: flex; justify-content: space-between; gap: 16px; padding: 10px 0; border-bottom: 1px solid #d7dcdf; }.mp-proof-list dt, .mp-result-list dt, .mp-building-detail dt, .mp-project-detail dt, .mp-engineer-panel dt { color: #69747c; }.mp-proof-list dd, .mp-result-list dd, .mp-building-detail dd, .mp-project-detail dd, .mp-engineer-panel dd { margin: 0; text-align: right; font-weight: 700; }
.mp-primary-link { display: flex; height: 46px; margin-top: 22px; align-items: center; justify-content: center; background: #ff6a1a; color: #fff; text-decoration: none; font-weight: 700; }
.mp-cover-work { display: grid; grid-template-columns: 330px 1fr 360px; }.mp-building-stage { position: relative; margin: 0; background: #20262b; overflow: hidden; }.mp-building-stage img { width: 100%; height: 100%; object-fit: cover; display: block; }.mp-building-stage figcaption { position: absolute; left: 0; right: 0; bottom: 0; height: 48px; display: flex; align-items: center; justify-content: space-around; background: #20262b; color: #fff; border-top: 3px solid #ff6a1a; font-size: 12px; }
.mp-result-code { display: block; margin-top: 18px; color: #1872c9; font-size: 12px; font-weight: 700; }.mp-result-rail h2, .mp-config-result h2, .mp-package-result h2 { margin: 10px 0 8px; font-size: 23px; line-height: 1.2; }.mp-result-rail > p { color: #69747c; line-height: 1.5; }.mp-price, .mp-config-total { margin: 24px 0 8px; color: #ff6a1a; font-size: 30px; font-weight: 700; }
.mp-lower { min-height: 0; background: #e9ecee; border-top: 5px solid #20262b; overflow: hidden; }.mp-cover-lower, .mp-catalog-lower, .mp-comparison-lower, .mp-project-lower { display: grid; grid-template-columns: 1.15fr repeat(3, 1fr) .95fr; }.mp-lower-heading { padding: 30px 32px; background: #20262b; color: #fff; }.mp-lower-heading > span { color: #ff6a1a; font-size: 11px; font-weight: 700; }.mp-lower-heading h2 { margin: 14px 0 10px; font-size: 22px; line-height: 1.2; }.mp-lower-heading p { color: #cbd1d5; line-height: 1.5; }
.mp-family, .mp-procurement, .mp-standard, .mp-engineering-note, .mp-doc-ledger { padding: 30px 26px; border-right: 1px solid #bdc5ca; background: #f4f5f6; }.mp-family > b, .mp-procurement > b { color: #ff6a1a; font-size: 28px; }.mp-family strong, .mp-procurement strong { display: block; margin: 18px 0 8px; font-size: 17px; }.mp-family span, .mp-procurement span { color: #1872c9; font-weight: 700; }.mp-family p, .mp-procurement p { color: #69747c; line-height: 1.5; }.mp-engineering-note, .mp-doc-ledger { background: #1872c9; color: #fff; border: 0; }.mp-engineering-note b, .mp-doc-ledger b { display: block; font-size: 44px; }.mp-engineering-note span, .mp-doc-ledger span { text-transform: uppercase; font-size: 11px; }.mp-engineering-note p, .mp-doc-ledger p { margin-top: 42px; line-height: 1.5; }
.mp-catalog-work { display: grid; grid-template-columns: 290px 1fr 410px; }.mp-filter-rail fieldset, .mp-system-list { margin: 18px 0; padding: 14px; border: 1px solid #c9cfd3; }.mp-filter-rail legend, .mp-system-list legend { padding: 0 6px; color: #69747c; font-size: 11px; font-weight: 700; }.mp-filter-rail fieldset label, .mp-system-list label { display: block; padding: 6px 0; }.mp-filter-rail input, .mp-system-list input { accent-color: #ff6a1a; }
.mp-field { display: block; margin: 14px 0; color: #69747c; font-size: 11px; font-weight: 700; text-transform: uppercase; }.mp-field select, .mp-field input { display: block; width: 100%; height: 42px; margin-top: 7px; padding: 0 12px; border: 1px solid #aeb6bc; background: #fff; text-transform: none; }.mp-filter-note { margin-top: 18px; padding: 14px; border-left: 4px solid #1872c9; background: #e9f1f8; }.mp-filter-note p { margin: 6px 0 0; color: #69747c; line-height: 1.4; }
.mp-catalog-ledger { padding: 22px; background: #e9ecee; }.mp-catalog-ledger header { height: 76px; display: flex; justify-content: space-between; align-items: center; padding: 0 18px; background: #20262b; color: #fff; }.mp-catalog-ledger header span { display: block; color: #ff6a1a; font-size: 10px; }.mp-catalog-ledger header b { display: block; margin-top: 5px; font-size: 22px; }.mp-catalog-ledger header p { max-width: 450px; text-align: right; color: #cbd1d5; }.mp-building-rows { background: #fff; border: 1px solid #c9cfd3; border-top: 0; }.mp-building-rows article { height: 88px; display: grid; grid-template-columns: 100px 1fr 110px 100px; align-items: center; gap: 12px; padding: 0 18px; border-bottom: 1px solid #d7dcdf; }.mp-building-rows article:last-child { border: 0; }.mp-building-rows article span { color: #1872c9; font-weight: 700; }.mp-building-rows article i, .mp-building-rows article em { color: #69747c; font-style: normal; text-align: right; }
.mp-building-detail { background: #fff; overflow: hidden; }.mp-building-detail > img { width: 100%; height: 270px; object-fit: cover; display: block; border-bottom: 4px solid #ff6a1a; }.mp-detail-body { padding: 20px 24px; }.mp-detail-body > span, .mp-project-detail > div > span { color: #ff6a1a; font-size: 10px; font-weight: 700; }.mp-detail-body h2 { margin: 8px 0; font-size: 20px; }.mp-building-detail dl { margin-top: 14px; }
.mp-catalog-lower { grid-template-columns: 1.2fr repeat(4, 1fr); }.mp-procurement:last-child { border-right: 0; }
.mp-config-work { display: grid; grid-template-columns: 330px 1fr 400px; }.mp-config-controls { padding: 18px 22px; }.mp-config-controls .mp-field { margin: 10px 0; }.mp-config-controls .mp-field select, .mp-config-controls .mp-field input { height: 36px; }.mp-dimension-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }.mp-config-controls .mp-label { margin: 12px 0 6px; }.mp-config-controls .mp-segment button { height: 34px; }.mp-system-list { display: grid; grid-template-columns: 1fr; gap: 0; margin: 12px 0; padding: 8px 12px; }.mp-system-list label { padding: 3px 0; font-size: 12px; }
.mp-config-stage { background: #d8dde0; display: grid; grid-template-rows: 48px 400px 152px; overflow: hidden; }.mp-stage-tabs { display: flex; align-items: stretch; background: #fff; border-bottom: 1px solid #aeb6bc; }.mp-stage-tabs > * { display: flex; align-items: center; padding: 0 22px; border-right: 1px solid #c9cfd3; font-size: 11px; font-style: normal; }.mp-stage-tabs b { color: #ff6a1a; box-shadow: inset 0 -3px #ff6a1a; }.mp-stage-images { display: grid; grid-template-columns: 1.45fr 1fr; gap: 2px; background: #20262b; }.mp-stage-images figure { position: relative; margin: 0; overflow: hidden; }.mp-stage-images img { width: 100%; height: 100%; object-fit: cover; display: block; }.mp-stage-images figcaption { position: absolute; left: 0; right: 0; bottom: 0; padding: 11px 14px; background: #20262b; color: #fff; border-top: 3px solid #ff6a1a; font-size: 11px; }
.mp-blueprint { position: relative; display: grid; grid-template-columns: 110px 1fr 1fr 1fr 80px; align-items: center; gap: 0; padding: 24px 28px; background: #fff; border-top: 1px solid #aeb6bc; }.mp-blueprint i { display: block; height: 70px; border-left: 2px solid #1872c9; border-right: 1px solid #69747c; }.mp-blueprint b { color: #1872c9; }.mp-blueprint em { position: absolute; left: 50%; bottom: 16px; font-style: normal; color: #69747c; }
.mp-config-result { padding: 24px; }.mp-config-result h2 { min-height: 112px; font-size: 18px; line-height: 1.45; }.mp-config-total { margin: 10px 0; }.mp-system-state { margin-top: 14px; padding: 12px; border-left: 4px solid #1872c9; background: #e9f1f8; color: #4d5961; line-height: 1.4; }
.mp-config-lower { display: grid; grid-template-rows: 68px 32px 1fr; padding: 0 24px 18px; background: #fff; }.mp-config-lower header { display: flex; justify-content: space-between; align-items: center; }.mp-config-lower header > div:last-child { text-align: right; }.mp-config-lower header span { display: block; color: #69747c; font-size: 10px; }.mp-config-lower header h2 { margin: 4px 0 0; font-size: 19px; }.mp-config-lower header b { display: block; margin-top: 5px; color: #ff6a1a; font-size: 20px; }.mp-spec-head, .mp-spec-row { display: grid; grid-template-columns: 54px 1.2fr 1.7fr 170px; align-items: center; }.mp-spec-head { padding: 0 12px; background: #20262b; color: #fff; font-size: 10px; }.mp-spec-head i, .mp-spec-row i { font-style: normal; }.mp-spec-head strong, .mp-spec-row strong { text-align: right; }.mp-spec-body { display: grid; grid-template-columns: 1fr 1fr; grid-auto-rows: 52px; border: 1px solid #c9cfd3; border-top: 0; }.mp-spec-row { padding: 0 12px; border-right: 1px solid #d7dcdf; border-bottom: 1px solid #d7dcdf; font-size: 12px; }.mp-spec-row:nth-child(even) { border-right: 0; }.mp-spec-row span, .mp-spec-row i { color: #69747c; }.mp-spec-row strong { color: #20262b; }
.mp-compare-work { display: grid; grid-template-columns: 300px 1fr 390px; }.mp-engineer-panel { padding: 0 24px 20px; background: #20262b; color: #fff; overflow: hidden; }.mp-engineer-panel img { width: calc(100% + 48px); height: 280px; margin-left: -24px; object-fit: cover; display: block; border-bottom: 4px solid #ff6a1a; }.mp-engineer-panel > span { display: block; margin-top: 20px; color: #ff6a1a; font-size: 10px; }.mp-engineer-panel h2 { margin: 8px 0; font-size: 22px; }.mp-engineer-panel p { color: #cbd1d5; line-height: 1.5; }.mp-engineer-panel dl { border-color: #4a535a; }.mp-engineer-panel dl div { border-color: #4a535a; }.mp-engineer-panel dt { color: #aeb6bc; }
.mp-package-matrix { padding: 22px; background: #e9ecee; }.mp-package-tabs { height: 112px; display: grid; grid-template-columns: repeat(3, 1fr); background: #fff; border: 1px solid #aeb6bc; }.mp-package-tabs button { display: grid; grid-template-columns: 46px 1fr; grid-template-rows: 1fr 1fr; align-items: center; padding: 14px; border: 0; border-left: 1px solid #aeb6bc; background: #fff; text-align: left; cursor: pointer; }.mp-package-tabs button:first-child { border-left: 0; }.mp-package-tabs button[aria-pressed="true"] { background: #20262b; color: #fff; box-shadow: inset 0 -4px #ff6a1a; }.mp-package-tabs button span { grid-row: 1 / 3; color: #ff6a1a; font-size: 22px; }.mp-package-tabs button b { font-size: 16px; }.mp-package-tabs button i { color: #69747c; font-style: normal; }.mp-package-tabs button[aria-pressed="true"] i { color: #cbd1d5; }
.mp-compare-rows { margin-top: 18px; background: #fff; border: 1px solid #aeb6bc; }.mp-compare-row { height: 58px; display: flex; justify-content: space-between; align-items: center; padding: 0 22px; border-bottom: 1px solid #d7dcdf; }.mp-compare-row:last-child { border: 0; }.mp-compare-row b { width: 32px; height: 32px; display: grid; place-items: center; border: 1px solid #aeb6bc; color: #69747c; }.mp-compare-row[data-included="true"] b { background: #1872c9; color: #fff; border-color: #1872c9; }.mp-package-result > p { min-height: 54px; color: #69747c; line-height: 1.5; }
.mp-comparison-lower { grid-template-columns: 1.25fr repeat(3, 1fr) .9fr; }.mp-standard b { display: block; color: #1872c9; }.mp-standard span { display: block; min-height: 64px; margin: 20px 0; line-height: 1.45; }.mp-standard i { padding-top: 12px; border-top: 1px solid #aeb6bc; color: #69747c; font-style: normal; }
.mp-project-work { display: grid; grid-template-columns: 290px 1fr 420px; }.mp-sector-buttons { margin-top: 16px; border: 1px solid #aeb6bc; }.mp-sector-buttons button { width: 100%; height: 48px; border: 0; border-bottom: 1px solid #aeb6bc; background: #fff; text-align: left; padding: 0 14px; cursor: pointer; }.mp-sector-buttons button:last-child { border: 0; }.mp-sector-buttons button[aria-pressed="true"] { background: #20262b; color: #fff; box-shadow: inset 4px 0 #ff6a1a; }.mp-project-count { margin-top: 22px; padding: 16px; background: #e9f1f8; border-left: 4px solid #1872c9; }.mp-project-count span { color: #69747c; font-size: 10px; }.mp-project-count b { display: block; margin-top: 5px; font-size: 22px; }.mp-project-count p { color: #69747c; line-height: 1.4; }
.mp-project-ledger { padding: 22px; background: #e9ecee; }.mp-project-ledger > header, .mp-project-ledger article { display: grid; grid-template-columns: 100px 1fr 120px 100px 80px; align-items: center; gap: 10px; }.mp-project-ledger > header { height: 48px; padding: 0 16px; background: #20262b; color: #fff; font-size: 10px; }.mp-project-ledger > header i, .mp-project-ledger > header em { font-style: normal; }.mp-project-ledger > div { background: #fff; border: 1px solid #c9cfd3; border-top: 0; }.mp-project-ledger article { height: 60px; padding: 0 16px; border-bottom: 1px solid #d7dcdf; }.mp-project-ledger article[data-visible="false"] { display: none; }.mp-project-ledger article span { color: #1872c9; font-weight: 700; }.mp-project-ledger article i, .mp-project-ledger article em { color: #69747c; font-style: normal; }.mp-project-ledger article strong { color: #207449; font-size: 11px; }
.mp-project-detail { background: #fff; overflow: hidden; border-left: 1px solid #c9cfd3; }.mp-project-detail > img { width: 100%; height: 330px; object-fit: cover; display: block; border-bottom: 4px solid #ff6a1a; }.mp-project-detail > div { padding: 20px 24px; }.mp-project-detail h2 { margin: 8px 0; font-size: 20px; }.mp-project-detail dl { margin-top: 14px; }
.mp-project-lower { grid-template-columns: 1.2fr repeat(4, 1fr); }.mp-timeline-step { position: relative; padding: 28px 24px; border-right: 1px solid #bdc5ca; background: #fff; }.mp-timeline-step > b { color: #ff6a1a; font-size: 26px; }.mp-timeline-step strong { display: block; margin: 20px 0 6px; font-size: 17px; }.mp-timeline-step span { color: #1872c9; font-weight: 700; }.mp-timeline-step i { display: block; width: 100%; height: 3px; margin: 22px 0; background: #20262b; }.mp-timeline-step p { color: #69747c; }
"""


_COVER_SCRIPT = r"""
(() => {
  const purposes = {
    production: { name: "Производственный модуль", code: "MP-P", unit: 20000, term: 0, install: 0 },
    office: { name: "Офисный модуль", code: "MP-O", unit: 18333.333333, term: 2, install: 1 },
    checkpoint: { name: "Контрольно-пропускной пункт", code: "MP-C", unit: 22500, term: 5, install: 0 }
  };
  const areas = { "72": { term: 24, weight: 6480, install: 6 }, "108": { term: 30, weight: 9720, install: 8 }, "144": { term: 30, weight: 12960, install: 10 } };
  let purpose = "production";
  let area = "108";
  const grouped = (value) => String(Math.round(value)).replace(/\B(?=(\d{3})+(?!\d))/g, " ");
  const update = () => {
    const profile = purposes[purpose];
    const dimensions = areas[area];
    document.querySelector("[data-cover-model]").textContent = `${profile.name} ${profile.code}-${area}`;
    document.querySelector("[data-cover-spec]").textContent = `${area} м² · ${Number(area) / 6} × 6 м · базовый конструктив`;
    document.querySelector("[data-cover-price]").textContent = `${grouped(Number(area) * profile.unit)} ₽`;
    document.querySelector("[data-cover-term]").textContent = `${dimensions.term + profile.term} рабочих дней`;
    document.querySelector("[data-cover-weight]").textContent = `${grouped(dimensions.weight)} кг`;
    document.querySelector("[data-cover-install]").textContent = `${dimensions.install + profile.install} дней`;
  };
  document.querySelectorAll('[data-selectable="building-purpose"]').forEach((button) => button.addEventListener("click", () => {
    purpose = button.dataset.value;
    document.querySelectorAll('[data-selectable="building-purpose"]').forEach((option) => option.setAttribute("aria-pressed", String(option === button)));
    update();
  }));
  document.querySelectorAll('[data-selectable="building-area"]').forEach((button) => button.addEventListener("click", () => {
    area = button.dataset.value;
    document.querySelectorAll('[data-selectable="building-area"]').forEach((option) => option.setAttribute("aria-pressed", String(option === button)));
    update();
  }));
})();
"""


_CATALOG_SCRIPT = r"""
(() => {
  const profiles = {
    office: { label: "Офисные модули", count: 9, model: "MP-O96 · административный блок", term: 32, geography: "ЦФО / ПФО" },
    warehouse: { label: "Здания под склад", count: 7, model: "MP-S180 · тёплый склад", term: 41, geography: "Россия / Казахстан" },
    logistics: { label: "Решения для логистики", count: 5, model: "MP-L240 · логистический терминал", term: 44, geography: "РФ / до 2 500 км" }
  };
  const areaProfiles = { all: { label: "любая площадь", adjustment: 0 }, compact: { label: "до 100 м²", adjustment: -2 }, large: { label: "от 200 м²", adjustment: -2 } };
  const readinessProfiles = { ready: { label: "с инженерией", adjustment: 0, term: 0 }, shell: { label: "контур", adjustment: 1, term: -8 }, turnkey: { label: "под ключ", adjustment: -1, term: 8 } };
  const area = document.querySelector("[data-catalog-area]");
  const readiness = document.querySelector("[data-catalog-readiness]");
  const activePurpose = () => document.querySelector("[data-catalog-purpose]:checked").dataset.catalogPurpose;
  const plural = (count) => count % 10 === 1 && count % 100 !== 11 ? "решение" : count % 10 >= 2 && count % 10 <= 4 && !(count % 100 >= 12 && count % 100 <= 14) ? "решения" : "решений";
  const update = () => {
    const profile = profiles[activePurpose()];
    const areaProfile = areaProfiles[area.value];
    const readinessProfile = readinessProfiles[readiness.value];
    const count = Math.max(1, profile.count + areaProfile.adjustment + readinessProfile.adjustment);
    document.querySelector("[data-building-count]").textContent = `${count} ${plural(count)}`;
    document.querySelector("[data-building-summary]").textContent = `${profile.label} · ${areaProfile.label} · ${readinessProfile.label}`;
    document.querySelector("[data-selected-building]").textContent = profile.model;
    document.querySelector("[data-selected-readiness]").textContent = readinessProfile.label[0].toUpperCase() + readinessProfile.label.slice(1);
    document.querySelector("[data-selected-delivery]").textContent = `${profile.term + readinessProfile.term} дня`;
    document.querySelector("[data-selected-geography]").textContent = profile.geography;
  };
  document.querySelectorAll("[data-catalog-purpose]").forEach((control) => control.addEventListener("change", update));
  area.addEventListener("change", update);
  readiness.addEventListener("change", update);
})();
"""


_CONFIG_SCRIPT = r"""
(() => {
  const purposeProfiles = {
    production: { label: "Производственный модуль", cost: 0 },
    office: { label: "Административный модуль", cost: 260000 },
    medical: { label: "Медицинский модуль", cost: 450000 }
  };
  const deliveryProfiles = {
    region: { label: "Базовый регион", cost: 120000 },
    pickup: { label: "Самовывоз", cost: 0 },
    north: { label: "Северная логистика", cost: 320000 }
  };
  const purpose = document.querySelector("[data-config-purpose]");
  const length = document.querySelector("[data-config-length]");
  const width = document.querySelector("[data-config-width]");
  const delivery = document.querySelector("[data-config-delivery]");
  const options = Object.fromEntries([...document.querySelectorAll("[data-config-option]")].map((control) => [control.dataset.configOption, control]));
  let floors = 1;
  let shell = "cold";
  const grouped = (value) => String(Math.round(value)).replace(/\B(?=(\d{3})+(?!\d))/g, " ");
  const numeric = (control, minimum, maximum) => Math.max(minimum, Math.min(maximum, Number.parseInt(control.value, 10) || minimum));
  const update = () => {
    const buildingLength = numeric(length, 6, 30);
    const buildingWidth = numeric(width, 6, 12);
    const area = buildingLength * buildingWidth * floors;
    const parts = [
      area * 10000,
      area * (shell === "warm" ? 6000 : 3000),
      floors === 2 ? area * 1800 : 0,
      purposeProfiles[purpose.value].cost,
      options.heating.checked ? 540000 : 0,
      options.electricity.checked ? 270000 : 0,
      options.plumbing.checked ? 360000 : 0,
      deliveryProfiles[delivery.value].cost
    ];
    const total = parts.reduce((sum, value) => sum + value, 0);
    const shellLabel = shell === "warm" ? "Тёплый контур" : "Холодный контур";
    const floorLabel = floors === 1 ? "1 этаж" : "2 этажа";
    const summary = `${area} м² · ${purposeProfiles[purpose.value].label} · ${floorLabel} · ${shellLabel} · ${deliveryProfiles[delivery.value].label} · ${grouped(total)} ₽`;
    document.querySelector("[data-config-summary]").textContent = summary;
    document.querySelector("[data-config-total]").textContent = `${grouped(total)} ₽`;
    document.querySelector("[data-config-ledger-total]").textContent = `${grouped(total)} ₽`;
    document.querySelector("[data-config-term]").textContent = `${24 + Math.ceil(area / 24) + (shell === "warm" ? 4 : 0) + (floors === 2 ? 6 : 0)} рабочих дней`;
    document.querySelector("[data-config-weight]").textContent = `${grouped(area * 86 + (options.heating.checked ? 270 : 0))} кг`;
    document.querySelector("[data-config-modules]").textContent = `${Math.ceil(area / 36)} шт.`;
    document.querySelector("[data-config-systems]").textContent = [
      options.electricity.checked ? "Электроснабжение" : "без электрики",
      options.heating.checked ? "Отопление" : "без отопления",
      options.plumbing.checked ? "Водоснабжение" : "без воды"
    ].join(" · ");
    const notes = [
      `S = ${area} м² × 10 000`,
      shell === "warm" ? "панель 120 мм" : "панель 80 мм",
      floors === 2 ? "усиление 2 уровня" : "1 уровень",
      purposeProfiles[purpose.value].label,
      options.heating.checked ? "радиаторы + ИТП" : "не включено",
      options.electricity.checked ? "щиты + трассы" : "не включено",
      options.plumbing.checked ? "вводы + разводка" : "не включено",
      deliveryProfiles[delivery.value].label
    ];
    document.querySelectorAll("[data-config-part]").forEach((node, index) => { node.textContent = `${grouped(parts[index])} ₽`; });
    document.querySelectorAll("[data-config-part-note]").forEach((node, index) => { node.textContent = notes[index]; });
  };
  [purpose, length, width, delivery, ...Object.values(options)].forEach((control) => control.addEventListener("input", update));
  document.querySelectorAll('[data-selectable="config-floor"]').forEach((button) => button.addEventListener("click", () => {
    floors = Number(button.dataset.value);
    document.querySelectorAll('[data-selectable="config-floor"]').forEach((option) => option.setAttribute("aria-pressed", String(option === button)));
    update();
  }));
  document.querySelectorAll('[data-selectable="config-shell"]').forEach((button) => button.addEventListener("click", () => {
    shell = button.dataset.value;
    document.querySelectorAll('[data-selectable="config-shell"]').forEach((option) => option.setAttribute("aria-pressed", String(option === button)));
    update();
  }));
  update();
})();
"""


_COMPARISON_SCRIPT = r"""
(() => {
  const profiles = {
    base: { name: "Базовая", total: 3240000, term: "30 дней", included: 4, code: "MP-216 / B", note: "Каркас, контур, окна и заводская приёмка." },
    engineering: { name: "Инженерная", total: 4680000, term: "42 дня", included: 6, code: "MP-216 / E", note: "Контур, электрика, отопление и заводская приёмка." },
    turnkey: { name: "Под ключ", total: 5940000, term: "55 дней", included: 7, code: "MP-216 / T", note: "Полная инженерия, монтаж, пусконаладка и исполнительная документация." }
  };
  const grouped = (value) => String(value).replace(/\B(?=(\d{3})+(?!\d))/g, " ");
  document.querySelectorAll('[data-selectable="package"]').forEach((button) => button.addEventListener("click", () => {
    const profile = profiles[button.dataset.value];
    document.querySelectorAll('[data-selectable="package"]').forEach((option) => option.setAttribute("aria-pressed", String(option === button)));
    document.querySelector(".mp-package-result .mp-result-code").textContent = profile.code;
    document.querySelector("[data-package-summary]").textContent = `${profile.name} · ${profile.included} из 7 позиций включено`;
    document.querySelector("[data-package-total]").textContent = `${grouped(profile.total)} ₽`;
    document.querySelector("[data-package-term]").textContent = profile.term;
    document.querySelector("[data-package-compliance]").textContent = `${profile.included} из 7 · СП подтверждены`;
    document.querySelector("[data-package-note]").textContent = profile.note;
    document.querySelectorAll("[data-comparison-row]").forEach((row, index) => {
      const included = index < profile.included;
      row.dataset.included = String(included);
      row.querySelector("[data-row-state]").textContent = included ? "✓" : "—";
    });
  }));
})();
"""


_PROJECTS_SCRIPT = r"""
(() => {
  const totals = {
    industry: { all: 12, central: 5, volga: 4, north: 3 },
    logistics: { all: 8, central: 3, volga: 2, north: 3 },
    social: { all: 5, central: 2, volga: 1, north: 2 }
  };
  const selections = {
    industry: {
      all: ["Цех ремонта техники", "Калуга", "864 м²", "14 дней", "180 км", "май 2026"],
      central: ["Цех ремонта техники", "Калуга", "864 м²", "14 дней", "180 км", "май 2026"],
      volga: ["Линия упаковки", "Казань", "540 м²", "12 дней", "820 км", "апрель 2026"],
      north: ["Ремонтная база", "Петрозаводск", "648 м²", "16 дней", "1 050 км", "февраль 2026"]
    },
    logistics: {
      all: ["Логистический терминал", "Тула", "1 080 м²", "18 дней", "420 км", "июнь 2026"],
      central: ["Логистический терминал", "Тула", "1 080 м²", "18 дней", "420 км", "июнь 2026"],
      volga: ["Зона комплектации", "Самара", "720 м²", "15 дней", "1 060 км", "март 2026"],
      north: ["Склад снабжения", "Мурманск", "720 м²", "17 дней", "1 880 км", "январь 2026"]
    },
    social: {
      all: ["Медицинский модуль", "Архангельск", "288 м²", "10 дней", "1 260 км", "июль 2026"],
      central: ["Учебный корпус", "Рязань", "432 м²", "11 дней", "310 км", "май 2026"],
      volga: ["ФАП", "Ульяновск", "216 м²", "9 дней", "890 км", "март 2026"],
      north: ["Медицинский модуль", "Архангельск", "288 м²", "10 дней", "1 260 км", "июль 2026"]
    }
  };
  const region = document.querySelector("[data-project-region]");
  let sector = "logistics";
  const plural = (count) => count % 10 === 1 && count % 100 !== 11 ? "проект" : count % 10 >= 2 && count % 10 <= 4 && !(count % 100 >= 12 && count % 100 <= 14) ? "проекта" : "проектов";
  const update = () => {
    const count = totals[sector][region.value];
    const facts = selections[sector][region.value];
    document.querySelector("[data-project-count]").textContent = `${count} ${plural(count)}`;
    document.querySelector("[data-project-selection]").textContent = `${facts[0]} · ${facts[1]}`;
    document.querySelector("[data-project-area]").textContent = facts[2];
    document.querySelector("[data-project-install]").textContent = facts[3];
    document.querySelector("[data-project-logistics]").textContent = facts[4];
    document.querySelector("[data-project-date]").textContent = facts[5];
    document.querySelectorAll("[data-project-row]").forEach((row) => {
      const visible = row.dataset.sector === sector && (region.value === "all" || row.dataset.region === region.value);
      row.dataset.visible = String(visible);
    });
  };
  document.querySelectorAll('[data-selectable="project-sector"]').forEach((button) => button.addEventListener("click", () => {
    sector = button.dataset.value;
    document.querySelectorAll('[data-selectable="project-sector"]').forEach((option) => option.setAttribute("aria-pressed", String(option === button)));
    update();
  }));
  region.addEventListener("change", update);
  update();
})();
"""


_BODY_RENDERERS = {
    "cover": _cover,
    "catalog": _catalog,
    "configurator": _configurator,
    "comparison": _comparison,
    "projects": _projects,
}

_ROUTE_SCRIPTS = {
    "cover": _COVER_SCRIPT,
    "catalog": _CATALOG_SCRIPT,
    "configurator": _CONFIG_SCRIPT,
    "comparison": _COMPARISON_SCRIPT,
    "projects": _PROJECTS_SCRIPT,
}


def render(
    project: ProjectSpec,
    shot: ShotSpec,
    assets: Mapping[str, str],
) -> RenderedPage:
    """Render one Modulprof route with project-owned industrial state."""
    if project.slug != "modulprof":
        raise KeyError(f"modulprof renderer does not support {project.slug}")
    try:
        body_renderer = _BODY_RENDERERS[shot.key]
    except KeyError as exc:
        raise ValueError(f"modulprof unknown route: {shot.key}") from exc

    owned = _owned_assets(shot.key, assets)
    html = (
        f'<div class="mp-page" data-site="modulprof" data-route="{escape_html(shot.key)}">'
        f'{_header(shot.key)}{body_renderer(owned)}</div>'
    )
    return RenderedPage(html=html, css=_CSS, scripts=_ROUTE_SCRIPTS[shot.key])
