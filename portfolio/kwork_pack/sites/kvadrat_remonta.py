"""Dedicated geometric renovation renderer for Kvadrat Remonta."""

from collections.abc import Mapping

from ..components import escape_html
from ..icons import icon
from ..models import ProjectSpec, ShotSpec
from .runtime import RenderedPage


_ROUTE_ASSETS = {
    "cover": ("living_room_after",),
    "renovation": ("material_samples",),
    "portfolio": ("living_room_before", "kitchen_detail"),
    "calculator": ("designer_portrait",),
    "stages": ("renovation_team",),
}


def _owned_assets(route: str, assets: Mapping[str, str]) -> dict[str, str]:
    resolved: dict[str, str] = {}
    for key in _ROUTE_ASSETS[route]:
        try:
            resolved[key] = escape_html(assets[key])
        except KeyError as exc:
            raise KeyError(f"kvadrat-remonta {route} missing asset {key}") from exc
    return resolved


def _brand_mark() -> str:
    return (
        '<span class="kr-brand-mark" aria-hidden="true">'
        '<i></i><i></i><i></i></span>'
    )


def _header(active: str) -> str:
    links = (
        ("renovation", "Услуги"),
        ("calculator", "Калькулятор"),
        ("portfolio", "Проекты"),
        ("stages", "Этапы"),
    )
    nav = "".join(
        f'<a href="#" class="{"is-active" if key == active else ""}">{label}</a>'
        for key, label in links
    )
    return (
        '<header class="kr-geometric-header">'
        '<div class="kr-header-main"><div class="kr-brand">'
        f'{_brand_mark()}<div><b>КВАДРАТ</b><b>РЕМОНТА</b></div></div>'
        '<button type="button" class="kr-location">Санкт-Петербург '
        f'{icon("chevron-down", size=16)}</button>'
        f'<nav aria-label="Основная навигация">{nav}'
        '<a href="#">О компании</a><a href="#">Контакты</a></nav>'
        '<div class="kr-phone"><b>+7 (812) 604-43-63</b><span>ежедневно с 9:00 до 21:00</span></div>'
        '<button type="button" class="kr-call">Заказать звонок</button></div>'
        '<div class="kr-header-proof"><b>Работаем по договору с фиксированной сметой</b>'
        '<span>Технический надзор на каждом этапе</span>'
        '<span>Гарантия 3 года</span><span>Выезд инженера бесплатно</span></div>'
        '</header>'
    )


def _cover(assets: Mapping[str, str]) -> str:
    image = assets["living_room_after"]
    return (
        '<main class="kr-route kr-cover">'
        '<section class="kr-cover-main">'
        '<div class="kr-cover-copy"><span>Санкт-Петербург · ремонт по договору</span>'
        '<h1>РЕМОНТ КВАРТИР ПОД КЛЮЧ</h1>'
        '<div class="kr-cover-line"></div>'
        '<dl class="kr-cover-cost"><div><dt>от 9 500 ₽/м²</dt><dd>честная цена без скрытых платежей</dd></div>'
        '<div><dt>от 45 дней</dt><dd>срок ремонта закреплён в договоре</dd></div></dl>'
        '<div class="kr-cover-estimator"><b>Быстрый расчёт</b>'
        '<div><span>55 м²</span><span>Капитальный ремонт</span></div>'
        '<strong>522 500 ₽</strong><button type="button">Получить точную смету '
        f'{icon("arrow-right", size=18)}</button><small>Замер инженера — бесплатно</small></div>'
        '</div><figure class="kr-cover-photo">'
        f'<img src="{image}" alt="Гостиная после комплексного ремонта">'
        '<figcaption><b>ЖК ЦДС Московский · 55 м²</b><span>Сдано за 48 дней · акт подписан без замечаний</span></figcaption>'
        '</figure></section>'
        '<section class="kr-cover-proof"><article><span>01</span><div><b>Смета фиксируется в договоре</b>'
        '<p>Доплаты возможны только после письменного согласования.</p></div></article>'
        '<article><span>02</span><div><b>Срок под финансовой ответственностью</b>'
        '<p>Пени за каждый день просрочки указаны в договоре.</p></div></article>'
        '<article><span>03</span><div><b>Технадзор отдельно от прораба</b>'
        '<p>Инженер принимает скрытые работы до закрытия.</p></div></article>'
        '<article><span>04</span><div><b>Материалы по оптовой цене</b>'
        '<p>Чеки и накладные доступны в личном кабинете.</p></div></article></section>'
        '<section class="kr-cover-projects"><div><span>Последние сдачи</span>'
        '<h2>3 ОБЪЕКТА · 182 М²</h2></div>'
        '<article><b>ЖК Приморский квартал</b><span>62 м² · капитальный</span><strong>827 900 ₽</strong></article>'
        '<article><b>ЖК Галактика</b><span>75 м² · дизайнерский</span><strong>1 230 500 ₽</strong></article>'
        '<article><b>ЖК Чёрная речка</b><span>45 м² · косметический</span><strong>435 700 ₽</strong></article>'
        '</section></main>'
    )


def _renovation(assets: Mapping[str, str]) -> str:
    image = assets["material_samples"]
    rows = (
        ("Демонтаж и вывоз", "55 м²", "132 000 ₽"),
        ("Электрика и щит", "42 точки", "184 000 ₽"),
        ("Сантехника", "8 точек", "146 000 ₽"),
        ("Выравнивание стен", "168 м²", "252 000 ₽"),
        ("Стяжка и напольные работы", "55 м²", "198 000 ₽"),
        ("Чистовая отделка", "комплект", "286 000 ₽"),
        ("Технадзор и уборка", "8 актов", "86 000 ₽"),
    )
    table_rows = "".join(
        f'<tr><td>{name}</td><td>{quantity}</td><td>{price}</td></tr>'
        for name, quantity, price in rows
    )
    return (
        '<main class="kr-route kr-renovation">'
        '<section class="kr-route-intro"><div><span>Услуга · квартира 55 м²</span>'
        '<h1>КОМПЛЕКСНЫЙ РЕМОНТ БЕЗ СКРЫТЫХ РАБОТ</h1></div>'
        '<p>Сначала обмер и техническое задание. Затем фиксируем состав, '
        'материалы, сроки и каждую контрольную точку.</p></section>'
        '<section class="kr-renovation-workspace">'
        '<figure class="kr-material-photo">'
        f'<img src="{image}" alt="Образцы материалов и рабочий чертёж">'
        '<figcaption><b>Ведомость материалов</b><span>24 позиции согласованы до начала работ</span></figcaption></figure>'
        '<div class="kr-package-scope"><span>Выберите пакет</span>'
        '<div class="kr-package-buttons">'
        '<button type="button" data-selectable="renovation-package" data-value="cosmetic" aria-pressed="false">Косметический</button>'
        '<button type="button" data-selectable="renovation-package" data-value="capital" aria-pressed="true">Капитальный</button>'
        '<button type="button" data-selectable="renovation-package" data-value="designer" aria-pressed="false">Дизайнерский</button></div>'
        '<h2 data-package-title>Пакет · Капитальный</h2><p data-package-lead>Полная инженерная подготовка и чистовая отделка.</p>'
        '<ul data-package-scope><li>Рабочий проект электрики и сантехники</li>'
        '<li>Выравнивание стен по маякам</li><li>Стяжка пола с картой уровней</li>'
        '<li>Технадзор скрытых работ</li><li>Исполнительная документация</li></ul>'
        '<dl><div><dt>Срок</dt><dd data-package-time>78 дней</dd></div>'
        '<div><dt>Гарантия</dt><dd data-package-warranty>3 года</dd></div></dl></div>'
        '<aside class="kr-renovation-estimate"><span>Смета KR-055</span>'
        '<h2 data-estimate-package>Пакет · Капитальный</h2>'
        '<p data-estimate-highlight>Технадзор скрытых работ включён</p>'
        '<table class="kr-estimate-table"><thead><tr><th>Работы</th><th>Объём</th><th>Стоимость</th></tr></thead>'
        f'<tbody>{table_rows}</tbody></table>'
        '<div><span>Материалы оплачиваются по накладным</span><b data-estimate-total>Итого 1 284 000 ₽</b></div></aside>'
        '</section>'
        '<section class="kr-renovation-lower"><div><span>01 · до старта</span><b>Обмерный план</b><p>32 размера и карта инженерных выводов.</p></div>'
        '<div><span>02 · каждую неделю</span><b>Фотоотчёт по пятницам</b><p>Объём, фактический расход и план на 7 дней.</p></div>'
        '<div><span>03 · до закрытия</span><b>Акты скрытых работ</b><p>Электрика, трубы, гидроизоляция, стяжка.</p></div>'
        '<div><span>04 · при сдаче</span><b>Исполнительная папка</b><p>Схемы, чеки, гарантии и паспорта материалов.</p></div></section>'
        '</main>'
    )


def _portfolio(assets: Mapping[str, str]) -> str:
    before = assets["living_room_before"]
    after = assets["kitchen_detail"]
    return (
        '<main class="kr-route kr-portfolio">'
        '<section class="kr-portfolio-title"><div><span>Проект № 38 · 55 м² · 48 дней</span>'
        '<h1>ДНЕВНИК РЕМОНТА: ЖК ЦДС МОСКОВСКИЙ</h1></div>'
        '<div class="kr-viewer-controls" aria-label="Этап проекта">'
        '<button type="button" data-selectable="portfolio-state" data-value="before" aria-pressed="true">Черновой этап</button>'
        '<button type="button" data-selectable="portfolio-state" data-value="after" aria-pressed="false">Готовая кухня</button></div></section>'
        '<section class="kr-portfolio-workspace"><figure class="kr-project-viewer">'
        f'<img class="kr-viewer-image is-visible" data-viewer-state="before" src="{before}" alt="Гостиная на черновом этапе ремонта">'
        f'<img class="kr-viewer-image" data-viewer-state="after" src="{after}" alt="Готовая кухня после приёмки">'
        '<figcaption><span data-viewer-label>Черновой этап · гостиная</span>'
        '<b data-viewer-caption>Инженерные выводы готовы, геометрия помещения зафиксирована</b></figcaption></figure>'
        '<aside class="kr-portfolio-evidence"><span data-portfolio-state>Черновой этап · акт обследования</span>'
        '<h2 data-portfolio-title>Что приняли в работу</h2><p data-portfolio-lead>Зафиксировали основание, 32 размера и 12 инженерных выводов.</p>'
        '<dl><div><dt>Площадь</dt><dd>55 м²</dd></div><div><dt>Срок</dt><dd>48 дней</dd></div>'
        '<div><dt>Смета</dt><dd>522 500 ₽</dd></div><div><dt>Изменение</dt><dd>0 ₽</dd></div></dl>'
        '<ul data-portfolio-points><li>32 размера занесено в обмерный план</li>'
        '<li>12 выводов проверено до монтажа</li><li>Основание принято прорабом и технадзором</li></ul>'
        '<button type="button">Получить смету проекта '
        f'{icon("arrow-right", size=18)}</button></aside></section>'
        '<section class="kr-portfolio-matrix"><div><span>Комната</span><b>Кухня-гостиная · 27 м²</b><p>Единая линия пола без порогов.</p></div>'
        '<div><span>Геометрия</span><b>1,5 мм / 2 м</b><p>Максимальное отклонение плоскостей.</p></div>'
        '<div><span>Электрика</span><b>42 точки</b><p>Маркировка и исполнительная схема.</p></div>'
        '<div><span>Приёмка</span><b>18 / 18</b><p>Контрольные точки закрыты заказчиком.</p></div>'
        '<div><span>Гарантия</span><b>до 24.08.2029</b><p>На работы по договору KR-204.</p></div></section>'
        '</main>'
    )


def _calculator(assets: Mapping[str, str]) -> str:
    image = assets["designer_portrait"]
    return (
        '<main class="kr-route kr-calculator">'
        '<section class="kr-route-intro kr-calculator-intro"><div><span>Расчёт за 60 секунд</span>'
        '<h1>РАССЧИТАЙТЕ СТОИМОСТЬ РЕМОНТА</h1></div>'
        '<p>Расчёт показывает порядок бюджета и материалов. Точная смета '
        'формируется после бесплатного замера инженера.</p></section>'
        '<section class="kr-calculator-workspace">'
        '<div class="kr-calculator-controls"><div><span>01 · тип квартиры</span>'
        '<div class="kr-room-buttons"><button type="button" data-selectable="calculator-room" data-value="Студия" data-rooms="1" aria-pressed="false">Студия</button>'
        '<button type="button" data-selectable="calculator-room" data-value="2-комнатная" data-rooms="2" aria-pressed="true">2 комнаты</button>'
        '<button type="button" data-selectable="calculator-room" data-value="3-комнатная" data-rooms="3" aria-pressed="false">3 комнаты</button></div></div>'
        '<label><span>02 · площадь</span><div><input type="number" min="20" max="180" value="55" data-calculator-area aria-label="Площадь квартиры"><b>м²</b></div></label>'
        '<div><span>03 · уровень материалов</span><div class="kr-tier-buttons">'
        '<button type="button" data-selectable="calculator-tier" data-value="Базовый" data-rate="8200" aria-pressed="false">Базовый <b>8 200 ₽/м²</b></button>'
        '<button type="button" data-selectable="calculator-tier" data-value="Комфорт" data-rate="9500" aria-pressed="true">Комфорт <b>9 500 ₽/м²</b></button>'
        '<button type="button" data-selectable="calculator-tier" data-value="Дизайнерский" data-rate="16800" aria-pressed="false">Дизайнерский <b>16 800 ₽/м²</b></button></div></div></div>'
        '<article class="kr-calculator-result"><span>Предварительная смета</span>'
        '<h2 data-calculator-total>522 500 ₽</h2><p data-calculator-summary>55 м² · 2-комнатная · Комфорт</p>'
        '<dl><div><dt>Работы</dt><dd data-calculator-work>339 625 ₽</dd></div>'
        '<div><dt>Черновые материалы</dt><dd data-calculator-rough>104 500 ₽</dd></div>'
        '<div><dt>Чистовые материалы</dt><dd data-calculator-finish>78 375 ₽</dd></div>'
        '<div><dt>Срок</dt><dd data-calculator-days>45 дней</dd></div></dl>'
        '<button type="button">Зафиксировать расчёт '
        f'{icon("arrow-right", size=18)}</button><small>Отправим PDF и список допущений</small></article>'
        '<figure class="kr-designer-photo">'
        f'<img src="{image}" alt="Дизайнер Марина Воронцова в студии материалов">'
        '<figcaption><b>Марина Воронцова</b><span>Проверит планировку и ведомость материалов</span></figcaption></figure>'
        '</section>'
        '<section class="kr-calculator-schedule"><div><span>Ведомость для расчёта</span><h2>ОБЪЁМЫ МАТЕРИАЛОВ</h2></div>'
        '<table><thead><tr><th>Позиция</th><th>Расчётный объём</th><th>Запас</th><th>Контроль</th></tr></thead><tbody>'
        '<tr><td>Розетки</td><td data-quantity-outlets>Розетки · 32 шт.</td><td>2 шт.</td><td>по плану электрики</td></tr>'
        '<tr><td>Краска для стен</td><td data-quantity-paint>Краска · 73 л</td><td>10%</td><td>2 слоя</td></tr>'
        '<tr><td>Ламинат</td><td data-quantity-floor>Ламинат · 61 м²</td><td>11%</td><td>единый контур</td></tr>'
        '<tr><td>Плинтус</td><td data-quantity-baseboard>68 пог. м</td><td>6%</td><td>с подрезкой</td></tr></tbody></table></section>'
        '</main>'
    )


def _stages(assets: Mapping[str, str]) -> str:
    image = assets["renovation_team"]
    return (
        '<main class="kr-route kr-stages">'
        '<section class="kr-route-intro kr-stages-intro"><div><span>Договор KR-204 · готовность 78%</span>'
        '<h1>ЭТАПЫ РАБОТ И ПРИЁМКА</h1></div><p>Следующий этап начинается только после акта. '
        'Заказчик видит фактический объём, фото и замечания технадзора.</p></section>'
        '<section class="kr-stages-workspace">'
        '<aside class="kr-stage-index"><span>Маршрут объекта</span>'
        '<button type="button" data-selectable="stage-checkpoint" data-value="survey" aria-pressed="false"><b>01</b><span>Обмер и проект</span><small>принято · 6 дней</small></button>'
        '<button type="button" data-selectable="stage-checkpoint" data-value="engineering" aria-pressed="false"><b>02</b><span>Инженерные работы</span><small>принято · 21 день</small></button>'
        '<button type="button" data-selectable="stage-checkpoint" data-value="finishing" aria-pressed="true"><b>03</b><span>Чистовая отделка</span><small>проверка · 18 день</small></button>'
        '<button type="button" data-selectable="stage-checkpoint" data-value="handover" aria-pressed="false"><b>04</b><span>Сдача объекта</span><small>план · 3 дня</small></button></aside>'
        '<figure class="kr-team-photo">'
        f'<img src="{image}" alt="Бригада проверяет отделочные работы">'
        '<figcaption><div><span>Бригада № 7</span><b>Прораб Алексей Логинов</b></div>'
        '<dl><div><dt>На объекте</dt><dd>5 специалистов</dd></div><div><dt>Следующая проверка</dt><dd>26 августа · 11:00</dd></div></dl></figcaption></figure>'
        '<div class="kr-stage-log"><span>Журнал этапа</span><h2 data-stage-title>03 · Чистовая отделка</h2>'
        '<p data-stage-lead>Проверяем плоскости, примыкания и чистовой монтаж.</p>'
        '<ol data-stage-log><li>Стены окрашены · 168 м²</li><li>Ламинат уложен · 55 м²</li>'
        '<li>Розетки установлены · 42 шт.</li><li>Замечания технадзора · 2 открыто</li></ol>'
        '<footer><span>Готовность этапа</span><b data-stage-progress>86%</b></footer></div>'
        '</section>'
        '<section class="kr-stages-acceptance"><div class="kr-acceptance-status"><span>Статус приёмки</span>'
        '<div><button type="button" data-selectable="acceptance-status" data-value="work" aria-pressed="false">В работе</button>'
        '<button type="button" data-selectable="acceptance-status" data-value="review" aria-pressed="true">На проверке</button>'
        '<button type="button" data-selectable="acceptance-status" data-value="accepted" aria-pressed="false">Принято</button></div></div>'
        '<article><span data-acceptance-stage>03 · Чистовая отделка</span><h2 data-acceptance-title>На проверке технадзора</h2>'
        '<p data-acceptance-lead>Открыто 2 замечания: примыкание плинтуса и регулировка двери.</p></article>'
        '<dl><div><dt>Документ</dt><dd data-acceptance-document>Лист замечаний № 03-18</dd></div>'
        '<div><dt>Результат</dt><dd data-acceptance-result>16 из 18 точек принято</dd></div>'
        '<div><dt>Гарантия</dt><dd data-acceptance-warranty>Активируется после сдачи</dd></div></dl>'
        '<button type="button">Открыть акт этапа '
        f'{icon("arrow-right", size=18)}</button></section>'
        '</main>'
    )


_CSS = """
.kr-page, .kr-page * { box-sizing: border-box; }
.kr-page { width: 100%; height: 1120px; overflow: hidden; background: #fff; color: #08090b; font-family: Arial, Helvetica, sans-serif; font-size: 14px; letter-spacing: 0; }
.kr-page button, .kr-page a, .kr-page input { font: inherit; letter-spacing: 0; }
.kr-page button { cursor: pointer; }
.kr-geometric-header { height: 112px; background: #fff; border-bottom: 1px solid #cdd1d6; }
.kr-header-main { height: 76px; padding: 0 42px; display: grid; grid-template-columns: 230px 150px 1fr 220px 166px; gap: 24px; align-items: center; }
.kr-brand { display: flex; align-items: center; gap: 15px; }
.kr-brand-mark { position: relative; width: 48px; height: 48px; display: block; }
.kr-brand-mark i { position: absolute; display: block; width: 31px; height: 31px; border: 6px solid #08090b; }
.kr-brand-mark i:nth-child(1) { left: 0; top: 0; }
.kr-brand-mark i:nth-child(2) { right: 0; bottom: 0; border-color: #183ee7; }
.kr-brand-mark i:nth-child(3) { left: 9px; top: 9px; width: 30px; height: 30px; border: 1px solid #646a73; }
.kr-brand > div { display: flex; flex-direction: column; line-height: 17px; }
.kr-brand b { font-size: 17px; letter-spacing: 0; }
.kr-location { height: 36px; padding: 0; display: flex; align-items: center; gap: 7px; border: 0; background: #fff; color: #08090b; font-size: 12px; }
.kr-header-main nav { display: flex; align-items: center; justify-content: center; gap: 31px; }
.kr-header-main nav a { color: #08090b; font-size: 12px; font-weight: 700; text-decoration: none; }
.kr-header-main nav a.is-active { color: #183ee7; }
.kr-phone { display: flex; flex-direction: column; align-items: flex-end; }
.kr-phone b { font-size: 17px; }
.kr-phone span { margin-top: 4px; color: #646a73; font-size: 12px; }
.kr-call { height: 44px; border: 0; background: #183ee7; color: #fff; font-size: 12px; font-weight: 700; }
.kr-header-proof { height: 36px; padding: 0 42px; display: grid; grid-template-columns: 1.4fr repeat(3, 1fr); align-items: center; background: #08090b; color: #fff; }
.kr-header-proof b, .kr-header-proof span { padding-left: 18px; border-left: 1px solid #373a3f; font-size: 12px; }
.kr-header-proof b { padding-left: 0; border-left: 0; color: #b7ee22; }
.kr-page main.kr-route { height: 1008px; min-height: 0; overflow: hidden; }
.kr-route h1, .kr-route h2, .kr-route p, .kr-route figure, .kr-route dl { margin: 0; }
.kr-route h1, .kr-route h2 { font-weight: 800; }
.kr-route-intro { height: 144px; padding: 25px 42px; display: grid; grid-template-columns: 1.3fr 1fr; align-items: end; border-bottom: 1px solid #cdd1d6; background: #fff; }
.kr-route-intro span, .kr-portfolio-title span { color: #183ee7; font-size: 12px; font-weight: 700; text-transform: uppercase; }
.kr-route-intro h1 { margin-top: 8px; max-width: 940px; font-size: 34px; line-height: 37px; }
.kr-route-intro > p { padding: 0 0 5px 34px; border-left: 3px solid #b7ee22; color: #646a73; font-size: 13px; line-height: 20px; }

.kr-cover-main { height: 650px; display: grid; grid-template-columns: 42% 58%; background: #fff; }
.kr-cover-copy { padding: 48px 42px 34px; }
.kr-cover-copy > span { color: #183ee7; font-size: 12px; font-weight: 700; text-transform: uppercase; }
.kr-cover-copy h1 { margin: 25px 0 0; max-width: 570px; font-size: 56px; line-height: 60px; }
.kr-cover-line { width: 122px; height: 5px; margin-top: 22px; background: #b7ee22; }
.kr-cover-cost { margin-top: 22px; display: grid; grid-template-columns: 1fr 1fr; border-top: 1px solid #08090b; border-bottom: 1px solid #cdd1d6; }
.kr-cover-cost > div { padding: 17px 20px 15px 0; }
.kr-cover-cost > div + div { padding-left: 22px; border-left: 1px solid #cdd1d6; }
.kr-cover-cost dt { font-size: 27px; font-weight: 800; }
.kr-cover-cost dd { margin: 7px 0 0; color: #646a73; font-size: 12px; }
.kr-cover-estimator { margin-top: 20px; padding: 15px 17px; display: grid; grid-template-columns: 1fr 190px; gap: 9px 16px; border: 1px solid #9da3aa; }
.kr-cover-estimator > b { grid-column: 1 / -1; font-size: 12px; text-transform: uppercase; }
.kr-cover-estimator > div { display: grid; grid-template-columns: 90px 1fr; gap: 8px; }
.kr-cover-estimator > div span { height: 34px; padding: 0 10px; display: flex; align-items: center; border: 1px solid #cdd1d6; font-size: 12px; }
.kr-cover-estimator > strong { font-size: 25px; color: #183ee7; }
.kr-cover-estimator button { grid-row: 3 / 5; grid-column: 2; padding: 0 14px; display: flex; align-items: center; justify-content: space-between; border: 0; background: #183ee7; color: #fff; font-size: 12px; font-weight: 700; }
.kr-cover-estimator small { font-size: 12px; color: #646a73; }
.kr-cover-photo { position: relative; overflow: hidden; }
.kr-cover-photo img { width: 100%; height: 100%; display: block; object-fit: cover; object-position: center; }
.kr-cover-photo figcaption { position: absolute; right: 0; bottom: 0; width: 360px; min-height: 84px; padding: 16px 20px; display: flex; flex-direction: column; background: #b7ee22; color: #08090b; }
.kr-cover-photo figcaption b { font-size: 14px; }
.kr-cover-photo figcaption span { margin-top: 7px; font-size: 12px; }
.kr-cover-proof { height: 148px; display: grid; grid-template-columns: repeat(4, 1fr); border-top: 1px solid #cdd1d6; border-bottom: 1px solid #cdd1d6; }
.kr-cover-proof article { padding: 27px 24px 22px 42px; display: grid; grid-template-columns: 34px 1fr; gap: 14px; border-right: 1px solid #cdd1d6; }
.kr-cover-proof article > span { color: #183ee7; font-size: 23px; font-weight: 800; }
.kr-cover-proof b { font-size: 13px; text-transform: uppercase; }
.kr-cover-proof p { margin-top: 10px; color: #646a73; font-size: 12px; line-height: 17px; }
.kr-cover-projects { height: 210px; padding: 24px 42px; display: grid; grid-template-columns: 260px repeat(3, 1fr); gap: 0; background: #eef0f4; }
.kr-cover-projects > div { padding-right: 26px; }
.kr-cover-projects > div span { color: #183ee7; font-size: 12px; font-weight: 700; text-transform: uppercase; }
.kr-cover-projects h2 { margin-top: 17px; font-size: 25px; }
.kr-cover-projects article { padding: 17px 24px; display: flex; flex-direction: column; border-left: 1px solid #bfc5cc; }
.kr-cover-projects article b { font-size: 14px; }
.kr-cover-projects article span { margin-top: 15px; color: #646a73; font-size: 12px; }
.kr-cover-projects article strong { margin-top: auto; font-size: 20px; }

.kr-renovation-workspace { height: 616px; padding: 26px 42px; display: grid; grid-template-columns: 350px 1fr 490px; gap: 24px; background: #fff; }
.kr-material-photo { height: 564px; display: grid; grid-template-rows: 1fr 76px; overflow: hidden; }
.kr-material-photo img { width: 100%; height: 100%; min-height: 0; display: block; object-fit: cover; }
.kr-material-photo figcaption { padding: 14px 17px; display: flex; flex-direction: column; background: #08090b; color: #fff; }
.kr-material-photo figcaption b { font-size: 14px; text-transform: uppercase; }
.kr-material-photo figcaption span { margin-top: 6px; font-size: 12px; }
.kr-package-scope { min-width: 0; border-top: 4px solid #183ee7; }
.kr-package-scope > span { display: block; margin-top: 13px; color: #183ee7; font-size: 12px; font-weight: 700; text-transform: uppercase; }
.kr-package-buttons { margin-top: 11px; display: grid; grid-template-columns: repeat(3, 1fr); }
.kr-package-buttons button { height: 40px; border: 1px solid #bfc5cc; border-right: 0; background: #fff; color: #646a73; font-size: 12px; }
.kr-package-buttons button:last-child { border-right: 1px solid #bfc5cc; }
.kr-package-buttons button[aria-pressed="true"] { background: #183ee7; color: #fff; border-color: #183ee7; }
.kr-package-scope h2 { margin-top: 22px; font-size: 25px; }
.kr-package-scope > p { margin-top: 10px; color: #646a73; font-size: 12px; line-height: 18px; }
.kr-package-scope ul { margin: 19px 0 0; padding: 0; list-style: none; border-top: 1px solid #cdd1d6; }
.kr-package-scope li { min-height: 45px; padding: 13px 8px 10px 20px; border-bottom: 1px solid #cdd1d6; font-size: 12px; position: relative; }
.kr-package-scope li::before { content: ''; position: absolute; left: 0; top: 17px; width: 8px; height: 8px; background: #b7ee22; }
.kr-package-scope dl { margin-top: 17px; display: grid; grid-template-columns: 1fr 1fr; }
.kr-package-scope dl > div { padding: 0 12px; border-left: 2px solid #08090b; }
.kr-package-scope dt { color: #646a73; font-size: 12px; }
.kr-package-scope dd { margin: 5px 0 0; font-size: 14px; font-weight: 800; }
.kr-renovation-estimate { height: 564px; padding: 20px 22px; background: #eef0f4; border-top: 4px solid #08090b; }
.kr-renovation-estimate > span { color: #183ee7; font-size: 12px; font-weight: 700; text-transform: uppercase; }
.kr-renovation-estimate h2 { margin-top: 9px; font-size: 22px; }
.kr-renovation-estimate > p { margin-top: 6px; color: #183ee7; font-size: 12px; font-weight: 700; }
.kr-estimate-table { width: 100%; margin-top: 10px; border-collapse: collapse; table-layout: fixed; }
.kr-estimate-table th, .kr-estimate-table td { height: 45px; padding: 6px 5px; border-bottom: 1px solid #bdc3ca; text-align: left; font-size: 12px; }
.kr-estimate-table th { color: #646a73; font-weight: 400; }
.kr-estimate-table th:nth-child(2), .kr-estimate-table td:nth-child(2) { width: 82px; }
.kr-estimate-table th:last-child, .kr-estimate-table td:last-child { width: 100px; text-align: right; }
.kr-renovation-estimate > div { margin-top: 15px; display: flex; align-items: flex-end; justify-content: space-between; }
.kr-renovation-estimate > div span { max-width: 180px; color: #646a73; font-size: 12px; line-height: 17px; }
.kr-renovation-estimate > div b { font-size: 20px; }
.kr-renovation-lower { height: 248px; display: grid; grid-template-columns: repeat(4, 1fr); background: #08090b; color: #fff; }
.kr-renovation-lower > div { padding: 31px 31px 24px 42px; border-right: 1px solid #393d43; }
.kr-renovation-lower span { color: #b7ee22; font-size: 12px; font-weight: 700; text-transform: uppercase; }
.kr-renovation-lower b { display: block; margin-top: 25px; font-size: 16px; text-transform: uppercase; }
.kr-renovation-lower p { margin-top: 15px; color: #c7cbd0; font-size: 12px; line-height: 18px; }

.kr-portfolio-title { height: 126px; padding: 24px 42px; display: flex; align-items: flex-end; justify-content: space-between; border-bottom: 1px solid #cdd1d6; }
.kr-portfolio-title h1 { margin: 8px 0 0; font-size: 35px; }
.kr-viewer-controls { display: grid; grid-template-columns: 130px 130px; }
.kr-viewer-controls button { height: 42px; border: 1px solid #aeb4bb; background: #fff; color: #646a73; font-size: 12px; }
.kr-viewer-controls button + button { border-left: 0; }
.kr-viewer-controls button[aria-pressed="true"] { background: #08090b; color: #fff; border-color: #08090b; }
.kr-portfolio-workspace { height: 618px; padding: 26px 42px; display: grid; grid-template-columns: 1fr 430px; gap: 24px; background: #fff; }
.kr-project-viewer { position: relative; height: 566px; overflow: hidden; background: #eef0f4; }
.kr-viewer-image { width: 100%; height: 100%; display: none; object-fit: cover; object-position: center; }
.kr-viewer-image.is-visible { display: block; }
.kr-project-viewer figcaption { position: absolute; left: 0; bottom: 0; width: 470px; min-height: 78px; padding: 15px 18px; display: flex; flex-direction: column; background: #08090b; color: #fff; }
.kr-project-viewer figcaption span { color: #b7ee22; font-size: 12px; font-weight: 700; text-transform: uppercase; }
.kr-project-viewer figcaption b { margin-top: 6px; font-size: 12px; line-height: 17px; }
.kr-portfolio-evidence { height: 566px; padding: 24px 24px; display: flex; flex-direction: column; background: #eef0f4; border-top: 4px solid #183ee7; }
.kr-portfolio-evidence > span { color: #183ee7; font-size: 12px; font-weight: 700; }
.kr-portfolio-evidence h2 { margin-top: 13px; font-size: 27px; }
.kr-portfolio-evidence > p { margin-top: 11px; color: #646a73; font-size: 12px; line-height: 18px; }
.kr-portfolio-evidence dl { margin-top: 20px; display: grid; grid-template-columns: 1fr 1fr; border-top: 1px solid #bdc3ca; }
.kr-portfolio-evidence dl > div { padding: 14px 0; border-bottom: 1px solid #bdc3ca; }
.kr-portfolio-evidence dt { color: #646a73; font-size: 12px; }
.kr-portfolio-evidence dd { margin: 5px 0 0; font-size: 14px; font-weight: 800; }
.kr-portfolio-evidence ul { margin: 18px 0 0; padding: 0; list-style: none; }
.kr-portfolio-evidence li { padding: 8px 0 8px 17px; border-bottom: 1px solid #cdd1d6; font-size: 12px; position: relative; }
.kr-portfolio-evidence li::before { content: ''; position: absolute; left: 0; top: 12px; width: 8px; height: 8px; background: #b7ee22; }
.kr-portfolio-evidence > button { margin-top: auto; height: 44px; padding: 0 14px; display: flex; align-items: center; justify-content: space-between; border: 0; background: #183ee7; color: #fff; font-size: 12px; font-weight: 700; }
.kr-portfolio-matrix { height: 264px; display: grid; grid-template-columns: repeat(5, 1fr); background: #08090b; color: #fff; }
.kr-portfolio-matrix > div { padding: 35px 28px 24px 42px; border-right: 1px solid #393d43; }
.kr-portfolio-matrix span { color: #b7ee22; font-size: 12px; font-weight: 700; text-transform: uppercase; }
.kr-portfolio-matrix b { display: block; margin-top: 25px; font-size: 17px; }
.kr-portfolio-matrix p { margin-top: 15px; color: #c7cbd0; font-size: 12px; line-height: 18px; }

.kr-calculator-intro { height: 138px; }
.kr-calculator-workspace { height: 604px; padding: 26px 42px; display: grid; grid-template-columns: 360px 390px 1fr; gap: 24px; background: #fff; }
.kr-calculator-controls { height: 552px; border-top: 4px solid #08090b; }
.kr-calculator-controls > div, .kr-calculator-controls > label { display: block; padding: 18px 0; border-bottom: 1px solid #cdd1d6; }
.kr-calculator-controls span { color: #183ee7; font-size: 12px; font-weight: 700; text-transform: uppercase; }
.kr-room-buttons { margin-top: 12px; display: grid; grid-template-columns: repeat(3, 1fr); }
.kr-room-buttons button { height: 42px; border: 1px solid #bfc5cc; border-right: 0; background: #fff; font-size: 12px; }
.kr-room-buttons button:last-child { border-right: 1px solid #bfc5cc; }
.kr-room-buttons button[aria-pressed="true"] { background: #08090b; color: #fff; }
.kr-calculator-controls label > div { height: 58px; margin-top: 12px; display: grid; grid-template-columns: 1fr 50px; border: 1px solid #9da3aa; }
.kr-calculator-controls input { min-width: 0; padding: 0 16px; border: 0; color: #08090b; font-size: 28px; font-weight: 800; }
.kr-calculator-controls label b { display: grid; place-items: center; background: #eef0f4; font-size: 16px; }
.kr-tier-buttons { margin-top: 12px; display: grid; grid-template-rows: repeat(3, 54px); }
.kr-tier-buttons button { padding: 0 12px; display: flex; align-items: center; justify-content: space-between; border: 1px solid #bfc5cc; border-bottom: 0; background: #fff; font-size: 12px; }
.kr-tier-buttons button:last-child { border-bottom: 1px solid #bfc5cc; }
.kr-tier-buttons button[aria-pressed="true"] { border-color: #183ee7; background: #183ee7; color: #fff; }
.kr-tier-buttons b { font-size: 12px; }
.kr-calculator-result { height: 552px; padding: 25px 26px; display: flex; flex-direction: column; background: #08090b; color: #fff; border-top: 4px solid #b7ee22; }
.kr-calculator-result > span { color: #b7ee22; font-size: 12px; font-weight: 700; text-transform: uppercase; }
.kr-calculator-result h2 { margin-top: 15px; font-size: 44px; color: #fff; }
.kr-calculator-result > p { margin-top: 9px; color: #c7cbd0; font-size: 12px; }
.kr-calculator-result dl { margin-top: 25px; border-top: 1px solid #3f4349; }
.kr-calculator-result dl > div { height: 49px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #3f4349; }
.kr-calculator-result dt { color: #c7cbd0; font-size: 12px; }
.kr-calculator-result dd { margin: 0; font-size: 13px; font-weight: 800; }
.kr-calculator-result > button { margin-top: auto; height: 48px; padding: 0 15px; display: flex; align-items: center; justify-content: space-between; border: 0; background: #183ee7; color: #fff; font-size: 12px; font-weight: 700; }
.kr-calculator-result > small { margin-top: 11px; color: #c7cbd0; font-size: 12px; }
.kr-designer-photo { height: 552px; display: grid; grid-template-rows: 1fr 76px; overflow: hidden; }
.kr-designer-photo img { width: 100%; height: 100%; min-height: 0; display: block; object-fit: cover; object-position: center; }
.kr-designer-photo figcaption { padding: 14px 17px; display: flex; flex-direction: column; background: #eef0f4; border-bottom: 1px solid #bfc5cc; }
.kr-designer-photo figcaption b { font-size: 14px; }
.kr-designer-photo figcaption span { margin-top: 5px; color: #646a73; font-size: 12px; }
.kr-calculator-schedule { height: 266px; padding: 22px 42px; display: grid; grid-template-columns: 260px 1fr; gap: 30px; border-top: 1px solid #cdd1d6; background: #eef0f4; }
.kr-calculator-schedule > div span { color: #183ee7; font-size: 12px; font-weight: 700; text-transform: uppercase; }
.kr-calculator-schedule h2 { margin-top: 14px; font-size: 24px; }
.kr-calculator-schedule table { width: 100%; border-collapse: collapse; table-layout: fixed; }
.kr-calculator-schedule th, .kr-calculator-schedule td { height: 47px; padding: 7px 12px; border-bottom: 1px solid #bcc2c9; text-align: left; font-size: 12px; }
.kr-calculator-schedule th { color: #646a73; font-weight: 400; }
.kr-calculator-schedule td:nth-child(2) { font-weight: 800; }

.kr-stages-intro { height: 136px; }
.kr-stages-workspace { height: 602px; padding: 26px 42px; display: grid; grid-template-columns: 310px 1fr 360px; gap: 24px; background: #fff; }
.kr-stage-index { height: 550px; border-top: 4px solid #183ee7; }
.kr-stage-index > span { height: 52px; display: flex; align-items: center; color: #183ee7; font-size: 12px; font-weight: 700; text-transform: uppercase; }
.kr-stage-index button { width: 100%; height: 119px; padding: 16px; display: grid; grid-template-columns: 38px 1fr; grid-template-rows: 1fr 1fr; border: 0; border-top: 1px solid #cdd1d6; background: #fff; color: #08090b; text-align: left; }
.kr-stage-index button > b { grid-row: 1 / 3; color: #183ee7; font-size: 23px; }
.kr-stage-index button > span { font-size: 13px; font-weight: 800; text-transform: uppercase; }
.kr-stage-index button > small { color: #646a73; font-size: 12px; }
.kr-stage-index button[aria-pressed="true"] { background: #08090b; color: #fff; }
.kr-stage-index button[aria-pressed="true"] > b { color: #b7ee22; }
.kr-stage-index button[aria-pressed="true"] > small { color: #c7cbd0; }
.kr-team-photo { height: 550px; display: grid; grid-template-rows: 1fr 92px; overflow: hidden; }
.kr-team-photo img { width: 100%; height: 100%; min-height: 0; display: block; object-fit: cover; object-position: center; }
.kr-team-photo figcaption { padding: 14px 17px; display: grid; grid-template-columns: 1fr 1.3fr; gap: 20px; background: #08090b; color: #fff; }
.kr-team-photo figcaption > div { display: flex; flex-direction: column; }
.kr-team-photo figcaption span { color: #b7ee22; font-size: 12px; text-transform: uppercase; }
.kr-team-photo figcaption b { margin-top: 6px; font-size: 13px; }
.kr-team-photo dl { display: grid; grid-template-columns: 1fr 1fr; }
.kr-team-photo dt { color: #aeb4bb; font-size: 12px; }
.kr-team-photo dd { margin: 5px 0 0; font-size: 12px; font-weight: 700; }
.kr-stage-log { height: 550px; padding: 22px 22px; display: flex; flex-direction: column; background: #eef0f4; border-top: 4px solid #08090b; }
.kr-stage-log > span { color: #183ee7; font-size: 12px; font-weight: 700; text-transform: uppercase; }
.kr-stage-log h2 { margin-top: 11px; font-size: 24px; }
.kr-stage-log > p { margin-top: 9px; color: #646a73; font-size: 12px; line-height: 18px; }
.kr-stage-log ol { margin: 20px 0 0; padding: 0; list-style: none; border-top: 1px solid #bdc3ca; }
.kr-stage-log li { min-height: 54px; padding: 17px 8px; border-bottom: 1px solid #bdc3ca; font-size: 12px; }
.kr-stage-log footer { margin-top: auto; height: 68px; display: flex; align-items: flex-end; justify-content: space-between; border-top: 1px solid #08090b; }
.kr-stage-log footer span { font-size: 12px; text-transform: uppercase; }
.kr-stage-log footer b { font-size: 33px; }
.kr-stages-acceptance { height: 270px; padding: 25px 42px; display: grid; grid-template-columns: 300px 1fr 460px 190px; gap: 28px; background: #08090b; color: #fff; }
.kr-acceptance-status > span { color: #b7ee22; font-size: 12px; font-weight: 700; text-transform: uppercase; }
.kr-acceptance-status > div { margin-top: 18px; display: grid; grid-template-columns: repeat(3, 1fr); }
.kr-acceptance-status button { height: 44px; border: 1px solid #555a61; border-right: 0; background: #08090b; color: #c7cbd0; font-size: 12px; }
.kr-acceptance-status button:last-child { border-right: 1px solid #555a61; }
.kr-acceptance-status button[aria-pressed="true"] { background: #b7ee22; color: #08090b; border-color: #b7ee22; }
.kr-stages-acceptance article > span { color: #b7ee22; font-size: 12px; font-weight: 700; }
.kr-stages-acceptance article h2 { margin-top: 15px; font-size: 25px; }
.kr-stages-acceptance article p { margin-top: 12px; color: #c7cbd0; font-size: 12px; line-height: 18px; }
.kr-stages-acceptance dl { border-top: 1px solid #45494f; }
.kr-stages-acceptance dl > div { min-height: 58px; padding: 12px 0; border-bottom: 1px solid #45494f; }
.kr-stages-acceptance dt { color: #aeb4bb; font-size: 12px; }
.kr-stages-acceptance dd { margin: 5px 0 0; font-size: 12px; font-weight: 700; }
.kr-stages-acceptance > button { height: 48px; padding: 0 13px; display: flex; align-items: center; justify-content: space-between; border: 0; background: #183ee7; color: #fff; font-size: 12px; font-weight: 700; }
"""


_RENOVATION_SCRIPT = r"""
(() => {
  const packages = {
    cosmetic: {
      title: "Пакет · Косметический", lead: "Обновление чистовых поверхностей без переноса инженерии.",
      scope: ["Подготовка и окраска стен", "Замена напольного покрытия", "Монтаж плинтуса", "Чистовой монтаж электрики", "Финальная уборка"],
      time: "35 дней", warranty: "2 года", total: "Итого 792 000 ₽", highlight: "Финальная уборка включена"
    },
    capital: {
      title: "Пакет · Капитальный", lead: "Полная инженерная подготовка и чистовая отделка.",
      scope: ["Рабочий проект электрики и сантехники", "Выравнивание стен по маякам", "Стяжка пола с картой уровней", "Технадзор скрытых работ", "Исполнительная документация"],
      time: "78 дней", warranty: "3 года", total: "Итого 1 284 000 ₽", highlight: "Технадзор скрытых работ включён"
    },
    designer: {
      title: "Пакет · Дизайнерский", lead: "Реализация проекта с нестандартными узлами и авторским контролем.",
      scope: ["Авторский надзор", "Индивидуальные узлы и раскладки", "Заказные столярные изделия", "Комплектация чистовыми материалами", "Еженедельный совет проекта"],
      time: "96 дней", warranty: "3 года", total: "Итого 1 764 000 ₽", highlight: "Авторский надзор включён"
    }
  };
  const update = (key) => {
    const item = packages[key];
    document.querySelector("[data-package-title]").textContent = item.title;
    document.querySelector("[data-estimate-package]").textContent = item.title;
    document.querySelector("[data-package-lead]").textContent = item.lead;
    document.querySelector("[data-package-scope]").innerHTML = item.scope.map((line) => `<li>${line}</li>`).join("");
    document.querySelector("[data-package-time]").textContent = item.time;
    document.querySelector("[data-package-warranty]").textContent = item.warranty;
    document.querySelector("[data-estimate-total]").textContent = item.total;
    document.querySelector("[data-estimate-highlight]").textContent = item.highlight;
  };
  document.querySelectorAll('[data-selectable="renovation-package"]').forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll('[data-selectable="renovation-package"]').forEach((option) => {
        option.setAttribute("aria-pressed", String(option === button));
      });
      update(button.dataset.value);
    });
  });
})();
"""


_PORTFOLIO_SCRIPT = r"""
(() => {
  const states = {
    before: {
      label: "Черновой этап · гостиная",
      caption: "Инженерные выводы готовы, геометрия помещения зафиксирована",
      state: "Черновой этап · акт обследования", title: "Что приняли в работу",
      lead: "Зафиксировали основание, 32 размера и 12 инженерных выводов.",
      points: ["32 размера занесено в обмерный план", "12 выводов проверено до монтажа", "Основание принято прорабом и технадзором"]
    },
    after: {
      label: "Готовая кухня · приёмка", caption: "Чистовой монтаж завершён по рабочим чертежам",
      state: "Готовая кухня · принято заказчиком", title: "Результат без расхождений",
      lead: "18 контрольных точек закрыто, итоговая смета не изменилась.",
      points: ["18 контрольных точек закрыто", "Отклонение плоскостей не более 1,5 мм", "Исполнительная схема передана заказчику"]
    }
  };
  const update = (key) => {
    const state = states[key];
    document.querySelectorAll(".kr-viewer-image").forEach((image) => {
      image.classList.toggle("is-visible", image.dataset.viewerState === key);
    });
    document.querySelector("[data-viewer-label]").textContent = state.label;
    document.querySelector("[data-viewer-caption]").textContent = state.caption;
    document.querySelector("[data-portfolio-state]").textContent = state.state;
    document.querySelector("[data-portfolio-title]").textContent = state.title;
    document.querySelector("[data-portfolio-lead]").textContent = state.lead;
    document.querySelector("[data-portfolio-points]").innerHTML = state.points.map((line) => `<li>${line}</li>`).join("");
  };
  document.querySelectorAll('[data-selectable="portfolio-state"]').forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll('[data-selectable="portfolio-state"]').forEach((option) => {
        option.setAttribute("aria-pressed", String(option === button));
      });
      update(button.dataset.value);
    });
  });
})();
"""


_CALCULATOR_SCRIPT = r"""
(() => {
  let roomName = "2-комнатная";
  let rooms = 2;
  let tierName = "Комфорт";
  let rate = 9500;
  const grouped = (value) => Math.round(value).toLocaleString("ru-RU").replace(/\u00a0/g, " ");
  const update = () => {
    const area = Math.max(20, Math.min(180, Number(document.querySelector("[data-calculator-area]").value) || 20));
    const total = area * rate;
    document.querySelector("[data-calculator-total]").textContent = `${grouped(total)} ₽`;
    document.querySelector("[data-calculator-summary]").textContent = `${area} м² · ${roomName} · ${tierName}`;
    document.querySelector("[data-calculator-work]").textContent = `${grouped(total * 0.65)} ₽`;
    document.querySelector("[data-calculator-rough]").textContent = `${grouped(total * 0.20)} ₽`;
    document.querySelector("[data-calculator-finish]").textContent = `${grouped(total * 0.15)} ₽`;
    document.querySelector("[data-calculator-days]").textContent = `${Math.round(area * 0.82)} дней`;
    document.querySelector("[data-quantity-outlets]").textContent = `Розетки · ${Math.round(area / 2) + rooms * 2} шт.`;
    document.querySelector("[data-quantity-paint]").textContent = `Краска · ${Math.round(area * 4 / 3)} л`;
    document.querySelector("[data-quantity-floor]").textContent = `Ламинат · ${Math.round(area * 1.11)} м²`;
    document.querySelector("[data-quantity-baseboard]").textContent = `${Math.round(area * 1.24)} пог. м`;
  };
  document.querySelectorAll('[data-selectable="calculator-room"]').forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll('[data-selectable="calculator-room"]').forEach((option) => option.setAttribute("aria-pressed", String(option === button)));
      roomName = button.dataset.value;
      rooms = Number(button.dataset.rooms);
      update();
    });
  });
  document.querySelectorAll('[data-selectable="calculator-tier"]').forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll('[data-selectable="calculator-tier"]').forEach((option) => option.setAttribute("aria-pressed", String(option === button)));
      tierName = button.dataset.value;
      rate = Number(button.dataset.rate);
      update();
    });
  });
  document.querySelector("[data-calculator-area]").addEventListener("input", update);
})();
"""


_STAGES_SCRIPT = r"""
(() => {
  const stages = {
    survey: {title: "01 · Обмер и проект", lead: "Фиксируем геометрию и выпускаем рабочие схемы.", progress: "100%", log: ["32 размера проверено", "План электрики согласован", "Развёртки стен подписаны", "Акт этапа закрыт"]},
    engineering: {title: "02 · Инженерные работы", lead: "Проверяем трассы до закрытия отделкой.", progress: "100%", log: ["Кабельные линии промаркированы", "Опрессовка труб выполнена", "Гидроизоляция испытана", "4 акта скрытых работ"]},
    finishing: {title: "03 · Чистовая отделка", lead: "Проверяем плоскости, примыкания и чистовой монтаж.", progress: "86%", log: ["Стены окрашены · 168 м²", "Ламинат уложен · 55 м²", "Розетки установлены · 42 шт.", "Замечания технадзора · 2 открыто"]},
    handover: {title: "04 · Сдача объекта", lead: "Фиксируем итог, документы и гарантийные обязательства.", progress: "96%", log: ["Генеральная уборка выполнена", "Исполнительная папка собрана", "Ключи и доступы проверены", "Акт готов к подписанию"]}
  };
  const acceptance = {
    work: {title: "Этап в работе", lead: "Бригада устраняет замечания по журналу.", document: "Журнал производства работ", result: "Текущий объём 78%", warranty: "Активируется после сдачи"},
    review: {title: "На проверке технадзора", lead: "Открыто 2 замечания: примыкание плинтуса и регулировка двери.", document: "Лист замечаний № 03-18", result: "16 из 18 точек принято", warranty: "Активируется после сдачи"},
    accepted: {title: "Акт № KR-204 подписан", lead: "Заказчик и технадзор подтвердили комплектность и качество.", document: "Акт № KR-204 подписан", result: "100% работ принято", warranty: "Гарантия до 24.08.2029"}
  };
  let stageKey = "finishing";
  const updateStage = () => {
    const stage = stages[stageKey];
    document.querySelector("[data-stage-title]").textContent = stage.title;
    document.querySelector("[data-stage-lead]").textContent = stage.lead;
    document.querySelector("[data-stage-progress]").textContent = stage.progress;
    document.querySelector("[data-stage-log]").innerHTML = stage.log.map((line) => `<li>${line}</li>`).join("");
    document.querySelector("[data-acceptance-stage]").textContent = stage.title;
  };
  const updateAcceptance = (key) => {
    const item = acceptance[key];
    document.querySelector("[data-acceptance-title]").textContent = item.title;
    document.querySelector("[data-acceptance-lead]").textContent = item.lead;
    document.querySelector("[data-acceptance-document]").textContent = item.document;
    document.querySelector("[data-acceptance-result]").textContent = item.result;
    document.querySelector("[data-acceptance-warranty]").textContent = item.warranty;
  };
  document.querySelectorAll('[data-selectable="stage-checkpoint"]').forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll('[data-selectable="stage-checkpoint"]').forEach((option) => option.setAttribute("aria-pressed", String(option === button)));
      stageKey = button.dataset.value;
      updateStage();
    });
  });
  document.querySelectorAll('[data-selectable="acceptance-status"]').forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll('[data-selectable="acceptance-status"]').forEach((option) => option.setAttribute("aria-pressed", String(option === button)));
      updateAcceptance(button.dataset.value);
    });
  });
})();
"""


_BODY_RENDERERS = {
    "cover": _cover,
    "renovation": _renovation,
    "portfolio": _portfolio,
    "calculator": _calculator,
    "stages": _stages,
}

_ROUTE_SCRIPTS = {
    "cover": "",
    "renovation": _RENOVATION_SCRIPT,
    "portfolio": _PORTFOLIO_SCRIPT,
    "calculator": _CALCULATOR_SCRIPT,
    "stages": _STAGES_SCRIPT,
}


def render(
    project: ProjectSpec,
    shot: ShotSpec,
    assets: Mapping[str, str],
) -> RenderedPage:
    """Render one Kvadrat Remonta route with only its owned image sources."""
    if project.slug != "kvadrat-remonta":
        raise KeyError(
            f"kvadrat-remonta renderer does not support {project.slug}"
        )
    try:
        body_renderer = _BODY_RENDERERS[shot.key]
    except KeyError as exc:
        raise ValueError(f"kvadrat-remonta unknown route: {shot.key}") from exc

    owned = _owned_assets(shot.key, assets)
    html = (
        '<div class="kr-page" data-site="kvadrat-remonta" '
        f'data-route="{escape_html(shot.key)}">'
        f"{_header(shot.key)}{body_renderer(owned)}</div>"
    )
    return RenderedPage(html=html, css=_CSS, scripts=_ROUTE_SCRIPTS[shot.key])
