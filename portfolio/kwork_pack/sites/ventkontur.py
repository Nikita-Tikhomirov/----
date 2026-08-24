"""Dedicated premium desktop renderer for Ventkontur industrial ventilation."""

from collections.abc import Mapping

from ..components import escape_html
from ..icons import icon
from ..models import ProjectSpec, ShotSpec
from .runtime import RenderedPage


_ROUTE_ASSETS = {
    "cover": ("air_handling_unit",),
    "catalog": ("factory_rooftop",),
    "selection": ("control_panel",),
    "projects": ("project_hall",),
    "service": ("engineer_portrait", "duct_installation"),
}


def _asset(
    project: ProjectSpec, shot: ShotSpec, assets: Mapping[str, str], key: str
) -> str:
    try:
        return escape_html(assets[key])
    except KeyError as exc:
        raise KeyError(
            f"ventkontur renderer {project.slug}/{shot.key} is missing asset {key}"
        ) from exc


def _header(active: str) -> str:
    navigation = (
        ("Оборудование", "catalog"),
        ("Подбор", "selection"),
        ("Проекты", "projects"),
        ("Сервис", "service"),
        ("Документация", "docs"),
    )
    links = "".join(
        f'<span class="vk-nav-item{" active" if route == active else ""}">{label}</span>'
        for label, route in navigation
    )
    return (
        '<header class="vk-utility-header">'
        '<div class="vk-brand"><i><span></span><span></span></i><div><b>ВентКонтур</b><small>промышленная вентиляция</small></div></div>'
        '<p class="vk-utility-copy">Проектирование, производство и поставка<br />промышленного вентиляционного оборудования</p>'
        '<div class="vk-contact"><b>8 800 555-19-68</b><small>Инженерная линия · 08:00-20:00</small></div>'
        '<button type="button" class="vk-outline-action">Запросить расчёт</button>'
        '<div class="vk-account">'
        f'{icon("users", size=17)}<span>Кабинет заказчика</span>'
        "</div></header>"
        '<div class="vk-catalog-header">'
        '<div class="vk-catalog-trigger">'
        f'{icon("settings", size=18)}<b>КАТАЛОГ ОБОРУДОВАНИЯ</b></div>'
        f'<nav aria-label="Разделы промышленного сайта">{links}</nav>'
        '<label class="vk-search">'
        f'{icon("filter", size=16)}<input aria-label="Поиск по каталогу" placeholder="Артикул, серия или параметр" /></label>'
        '<div class="vk-header-tools">'
        f'{icon("shopping-cart", size=18)}<b>Смета</b><span>3</span></div>'
        "</div>"
    )


def _cover(project: ProjectSpec, shot: ShotSpec, assets: Mapping[str, str]) -> str:
    source = _asset(project, shot, assets, "air_handling_unit")
    products = "".join(
        f'<tr><td><b>{model}</b><span>{purpose}</span></td><td>{flow}</td><td>{pressure}</td><td>{power}</td><td><strong>{status}</strong></td><td>{lead}</td></tr>'
        for model, purpose, flow, pressure, power, status, lead in (
            ("VK-AHU 30", "Цеха до 4 000 м²", "12 000 м³/ч", "650 Па", "18 кВт", "На складе", "5 дней"),
            ("VK-AHU 45", "Производственные линии", "18 000 м³/ч", "780 Па", "22 кВт", "В производстве", "14 дней"),
            ("VK-AHU 60", "Высоконапорные системы", "30 000 м³/ч", "1 050 Па", "37 кВт", "Под проект", "21 день"),
        )
    )
    return (
        f'{_header("cover")}<section class="vk-cover-body">'
        '<div class="vk-cover-hero"><div class="vk-cover-copy">'
        '<p class="vk-kicker">ИНЖЕНЕРНЫЕ СИСТЕМЫ ДЛЯ ПРОИЗВОДСТВА</p>'
        '<h1>Промышленная вентиляция под параметры объекта</h1>'
        '<p class="vk-lead">Расчёт, поставка и ввод в эксплуатацию. Фиксируем расход, давление, шум и энергопотребление до производства.</p>'
        '<div class="vk-cover-actions"><button type="button" class="vk-primary">Получить инженерный расчёт</button><button type="button" class="vk-link-action">Смотреть типовые решения</button></div>'
        '<dl class="vk-cover-specs"><div><dt>18 000</dt><dd>м³/ч расчётный расход</dd></div><div><dt>780</dt><dd>Па рабочее давление</dd></div><div><dt>14 дней</dt><dd>срок производства серии VK</dd></div></dl>'
        '</div><figure class="vk-cover-media"><img src="'
        f'{source}" alt="Промышленная приточно-вытяжная установка ВентКонтур" /></figure></div>'
        '<section class="vk-cover-products"><div class="vk-cover-products-head"><div><p class="vk-kicker">СЕРИЙНОЕ ОБОРУДОВАНИЕ</p><h2>Оборудование в производстве</h2></div><p>Параметры проверены на стенде. Паспорт, схема автоматики и протокол испытаний входят в поставку.</p><button type="button" class="vk-compact-action">Открыть каталог</button></div>'
        '<table><thead><tr><th>Серия и назначение</th><th>Расход</th><th>Давление</th><th>Мощность</th><th>Статус</th><th>Отгрузка</th></tr></thead><tbody>'
        f'{products}</tbody></table><div class="vk-procurement-line"><b>Комплект поставки:</b><span>установка</span><span>автоматика</span><span>паспорт изделия</span><span>шеф-монтаж</span><strong>Гарантия 24 месяца</strong></div></section>'
        "</section>"
    )


def _catalog(project: ProjectSpec, shot: ShotSpec, assets: Mapping[str, str]) -> str:
    source = _asset(project, shot, assets, "factory_rooftop")
    rows = "".join(
        f'<tr><td><b>{model}</b><span>{purpose}</span></td><td>{flow}</td><td>{pressure}</td><td>{heat}</td><td>{stock}</td><td>{price}</td></tr>'
        for model, purpose, flow, pressure, heat, stock, price in (
            ("VK-AHU 30", "Общеобменная", "12 000", "650", "96", "12 шт.", "от 1 680 000 ₽"),
            ("VK-AHU 45", "Приточно-вытяжная", "18 000", "780", "142", "8 шт.", "от 2 350 000 ₽"),
            ("VK-AHU 60", "Высоконапорная", "30 000", "1 050", "210", "Под заказ", "от 3 480 000 ₽"),
            ("VK-REC 40", "С рекуперацией", "16 500", "720", "118", "5 шт.", "от 2 720 000 ₽"),
            ("VK-EX 25", "Вытяжная", "9 000", "540", "—", "17 шт.", "от 980 000 ₽"),
        )
    )
    category_buttons = (
        '<button type="button" class="vk-selector active" data-selectable="catalog-sector" data-sector-title="Промышленные объекты" data-rows="VK-AHU 30|Общеобменная|12 000|650|96|12 шт.|от 1 680 000 ₽;VK-AHU 45|Приточно-вытяжная|18 000|780|142|8 шт.|от 2 350 000 ₽;VK-AHU 60|Высоконапорная|30 000|1 050|210|Под заказ|от 3 480 000 ₽;VK-REC 40|С рекуперацией|16 500|720|118|5 шт.|от 2 720 000 ₽;VK-EX 25|Вытяжная|9 000|540|—|17 шт.|от 980 000 ₽" aria-pressed="true">Промышленность</button>'
        '<button type="button" class="vk-selector" data-selectable="catalog-sector" data-sector-title="Складские комплексы" data-rows="VK-WH 20|Склад до 8 000 м²|8 500|500|72|9 шт.|от 1 120 000 ₽;VK-WH 35|Высотное хранение|14 000|680|110|6 шт.|от 1 890 000 ₽;VK-REC 40|Рекуперация тепла|16 500|720|118|5 шт.|от 2 720 000 ₽;VK-SM 18|Дымоудаление|7 500|900|—|Под заказ|от 1 460 000 ₽" aria-pressed="false">Склады</button>'
        '<button type="button" class="vk-selector" data-selectable="catalog-sector" data-sector-title="Пищевые производства" data-rows="VK-HYG 30|Моечное исполнение|11 500|740|105|4 шт.|от 2 180 000 ₽;VK-HYG 45|Нержавеющие секции|18 000|820|155|Под заказ|от 3 260 000 ₽;VK-REC-H 35|Гигиенический рекуператор|14 500|760|126|3 шт.|от 2 940 000 ₽;VK-EX-H 22|Вытяжка влажных зон|8 200|620|—|7 шт.|от 1 340 000 ₽" aria-pressed="false">Пищевые</button>'
    )
    return (
        f'{_header("catalog")}<section class="vk-catalog-body">'
        '<header class="vk-route-head"><div><p class="vk-kicker">СКЛАДСКАЯ ПРОГРАММА · 42 ПОЗИЦИИ</p><h1>Каталог вентиляционных установок</h1></div><div class="vk-route-controls" role="group" aria-label="Отрасль каталога">'
        f'{category_buttons}</div></header>'
        '<div class="vk-catalog-main"><aside class="vk-filter-panel"><div class="vk-filter-title">'
        f'{icon("filter", size=17)}<b>ПАРАМЕТРЫ ПОДБОРА</b></div>'
        '<label>Расход, м³/ч<div><input value="8 000" aria-label="Расход от" /><input value="35 000" aria-label="Расход до" /></div></label>'
        '<label>Статическое давление, Па<div><input value="450" aria-label="Давление от" /><input value="1 100" aria-label="Давление до" /></div></label>'
        '<fieldset><legend>Исполнение</legend><label><input type="checkbox" checked /> Уличное</label><label><input type="checkbox" checked /> Внутреннее</label><label><input type="checkbox" /> Гигиеническое</label></fieldset>'
        '<button type="button" class="vk-yellow-action">Применить параметры</button><p>Показаны установки с резервом по расходу не менее 10%.</p></aside>'
        '<section class="vk-catalog-table"><div class="vk-table-title"><b>Приточно-вытяжные установки</b><span>цены с НДС · данные на 24.08.2026</span></div><table><thead><tr><th>Серия</th><th>м³/ч</th><th>Па</th><th>Нагрев, кВт</th><th>Наличие</th><th>Цена</th></tr></thead><tbody>'
        f'{rows}</tbody></table><div class="vk-table-note"><b>Паспортная точность:</b><span>расход ±3%</span><span>давление ±20 Па</span><span>шум по ГОСТ 12.1.003</span></div></section>'
        '<aside class="vk-catalog-site"><img src="'
        f'{source}" alt="Вентиляционное оборудование на кровле промышленного объекта" /><div><p class="vk-kicker">ИНЖЕНЕРНАЯ ПРОВЕРКА</p><h2>Совместимость с объектом</h2><dl><div><dt>Температура</dt><dd>−42…+45 °C</dd></div><div><dt>Коррозия</dt><dd>C3 / C4</dd></div><div><dt>Монтаж</dt><dd>рама или кровля</dd></div></dl><button type="button" class="vk-outline-action">Запросить BIM</button></div></aside></div>'
        '<section class="vk-catalog-comparison"><div><p class="vk-kicker">ТЕХНИЧЕСКАЯ СВЕРКА</p><h2>Сравнение характеристик · Промышленные объекты</h2></div><div class="vk-comparison-body"><table><thead><tr><th>Критерий</th><th>VK-AHU 30</th><th>VK-AHU 45</th><th>VK-AHU 60</th></tr></thead><tbody><tr><td>Рабочая точка</td><td>12 000 / 650</td><td>18 000 / 780</td><td>30 000 / 1 050</td></tr><tr><td>Класс фильтра</td><td>ePM10 60%</td><td>ePM1 55%</td><td>ePM1 70%</td></tr><tr><td>Автоматика</td><td>VK-Basic</td><td>VK-Pro</td><td>VK-Pro+</td></tr><tr><td>Срок производства</td><td>10 дней</td><td>14 дней</td><td>21 день</td></tr></tbody></table></div><div class="vk-compare-decision"><b>Рекомендуемая серия</b><strong>VK-AHU 45</strong><span>резерв 14% по расходу</span><button type="button" class="vk-primary">В спецификацию</button></div></section>'
        "</section>"
    )


def _selection(project: ProjectSpec, shot: ShotSpec, assets: Mapping[str, str]) -> str:
    source = _asset(project, shot, assets, "control_panel")
    return (
        f'{_header("selection")}<section class="vk-selection-body">'
        '<header class="vk-route-head"><div><p class="vk-kicker">ИНЖЕНЕРНЫЙ WORKSHEET · ШАГ 2 ИЗ 4</p><h1>Подбор по расходу и давлению</h1></div><p>Введите расчётную точку. Модель и рабочая зона пересчитываются в браузере без изменения геометрии листа.</p></header>'
        '<div class="vk-selection-main"><section class="vk-worksheet"><div class="vk-worksheet-head"><b>Исходные данные системы</b><span>VK-CALC / REV.04</span></div>'
        '<div class="vk-duty-presets" role="group" aria-label="Расчётный режим"><button type="button" class="vk-selector" data-selectable="selection-duty" data-airflow-value="9000" data-pressure-value="560" aria-pressed="false">Склад</button><button type="button" class="vk-selector active" data-selectable="selection-duty" data-airflow-value="18000" data-pressure-value="780" aria-pressed="true">Производство</button><button type="button" class="vk-selector" data-selectable="selection-duty" data-airflow-value="26000" data-pressure-value="980" aria-pressed="false">Высокое давление</button></div>'
        '<div class="vk-input-grid"><label><span>Расход воздуха</span><input type="number" value="18000" min="3000" max="60000" step="500" data-airflow /><b>м³/ч</b></label><label><span>Статическое давление</span><input type="number" value="780" min="200" max="1600" step="10" data-pressure /><b>Па</b></label><label><span>Температура наружного воздуха</span><input type="number" value="-28" /><b>°C</b></label><label><span>Температура подачи</span><input type="number" value="18" /><b>°C</b></label></div>'
        '<table class="vk-loss-table"><thead><tr><th>Участок</th><th>Скорость</th><th>Потери</th><th>Запас</th></tr></thead><tbody><tr><td>Фильтр ePM1</td><td>2.4 м/с</td><td>210 Па</td><td>15%</td></tr><tr><td>Нагреватель</td><td>2.2 м/с</td><td>165 Па</td><td>12%</td></tr><tr><td>Сеть воздуховодов</td><td>—</td><td>405 Па</td><td>10%</td></tr></tbody></table>'
        '<div class="vk-engineering-check"><b>Проверка диапазона</b><span>Рабочая точка находится внутри устойчивой зоны вентилятора.</span><strong>PASS</strong></div></section>'
        '<aside class="vk-selection-result"><img src="'
        f'{source}" alt="Проверка шкафа автоматики вентиляционной установки" /><div class="vk-result-sheet"><p class="vk-kicker">РЕЗУЛЬТАТ ПОДБОРА</p><h2 class="vk-selection-model">VK-AHU 45</h2><dl><div><dt>Расчётная точка системы</dt><dd><span class="vk-result-airflow">18 000 м³/ч</span> · <span class="vk-result-pressure">780 Па</span></dd></div><div><dt>Резерв по расходу</dt><dd class="vk-result-reserve">Резерв по расходу 15%</dd></div><div><dt>Электродвигатель</dt><dd class="vk-result-motor">22 кВт · IE4</dd></div><div><dt>Шкаф автоматики</dt><dd>VK-Pro / Modbus TCP</dd></div></dl><button type="button" class="vk-primary">Сформировать лист подбора</button></div></aside></div>'
        '<section class="vk-selection-comparison"><div><p class="vk-kicker">РАСЧЁТНАЯ МАТРИЦА</p><h2>Три исполнения для одной рабочей точки</h2><span>Сравнение учитывает 15% резерв и круглосуточный режим.</span></div><table><thead><tr><th>Исполнение</th><th>Расчётный расход</th><th>Давление</th><th>Вентилятор</th><th>Годовое потребление</th><th>Статус</th></tr></thead><tbody><tr><td><b>VK-AHU 45 Standard</b></td><td class="vk-computed-flow">18 000 м³/ч</td><td class="vk-computed-pressure">780 Па</td><td>EC / 22 кВт</td><td>128 МВт·ч</td><td>Базовый</td></tr><tr><td><b>VK-AHU 45 Recovery</b></td><td>18 000 м³/ч</td><td>820 Па</td><td>EC / 24 кВт</td><td>94 МВт·ч</td><td>−27% энергии</td></tr><tr><td><b>VK-AHU 60 Reserve</b></td><td>26 000 м³/ч</td><td>980 Па</td><td>EC / 37 кВт</td><td>161 МВт·ч</td><td>Резерв линии</td></tr></tbody></table></section>'
        "</section>"
    )


def _projects(project: ProjectSpec, shot: ShotSpec, assets: Mapping[str, str]) -> str:
    source = _asset(project, shot, assets, "project_hall")
    controls = (
        '<button type="button" class="vk-selector active" data-selectable="project-sector" data-title="Производственный цех · Тула" data-standard="ГОСТ 12.1.005" data-controls="32 точки контроля" data-airflow="186 000 м³/ч" data-effect="18% снижения энергопотребления" aria-pressed="true">Машиностроение</button>'
        '<button type="button" class="vk-selector" data-selectable="project-sector" data-title="Фармацевтический корпус" data-standard="ISO 8" data-controls="48 точек контроля" data-airflow="214 000 м³/ч" data-effect="22% экономии тепла" aria-pressed="false">Фармацевтика</button>'
        '<button type="button" class="vk-selector" data-selectable="project-sector" data-title="Холодный склад · Домодедово" data-standard="СП 60.13330" data-controls="24 точки контроля" data-airflow="142 000 м³/ч" data-effect="16% снижения нагрузки" aria-pressed="false">Логистика</button>'
    )
    return (
        f'{_header("projects")}<section class="vk-projects-body">'
        '<section class="vk-project-hero"><img src="'
        f'{source}" alt="Система вентиляции завершённого промышленного цеха" /><div><p class="vk-kicker">ЗАВЕРШЁННЫЙ ПРОЕКТ · 18 600 М²</p><h1>Вентиляция цеха без остановки производства</h1><p>Разделили монтаж на четыре технологических окна, провели балансировку по работающим линиям и передали цифровой журнал параметров.</p><dl><div><dt>14 недель</dt><dd>проектирование и монтаж</dd></div><div><dt>186 000 м³/ч</dt><dd>суммарный расход</dd></div><div><dt>0 часов</dt><dd>остановки производства</dd></div></dl></div></section>'
        '<section class="vk-project-evidence"><header><div><p class="vk-kicker">Подтверждённые показатели</p><h2>Производственный цех · Тула</h2></div><div class="vk-route-controls" role="group" aria-label="Отрасль проекта">'
        f'{controls}</div></header><div class="vk-project-kpis"><div><span>Фактический расход</span><b class="vk-project-airflow">186 000 м³/ч</b><small>проект: 184 500 м³/ч</small></div><div><span>Класс чистоты / норматив</span><b class="vk-project-standard">ГОСТ 12.1.005</b><small>протокол № VK-771</small></div><div><span>Энергетический эффект</span><b class="vk-project-effect">18% снижения энергопотребления</b><small>по данным за 90 дней</small></div><div><span>Автоматизация</span><b class="vk-project-controls">32 точки контроля</b><small>SCADA заказчика</small></div></div>'
        '<table><thead><tr><th>Контрольная зона</th><th>Расход проект</th><th>Расход факт</th><th>Давление</th><th>Шум</th><th>Результат</th></tr></thead><tbody><tr><td>Линия механической обработки</td><td>62 000</td><td>62 840</td><td>810 Па</td><td>74 дБ</td><td>PASS</td></tr><tr><td>Сборочный участок</td><td>48 500</td><td>49 120</td><td>690 Па</td><td>68 дБ</td><td>PASS</td></tr><tr><td>Покрасочная камера</td><td>74 000</td><td>74 210</td><td>940 Па</td><td>72 дБ</td><td>PASS</td></tr></tbody></table></section>'
        '<section class="vk-project-log"><div><b>01 / ОБСЛЕДОВАНИЕ</b><span>Аэродинамика сети и тепловыделения оборудования</span></div><div><b>02 / МОНТАЖНЫЕ ОКНА</b><span>Четыре смены без остановки технологических линий</span></div><div><b>03 / ПУСКОНАЛАДКА</b><span>Балансировка 32 зон и интеграция с SCADA</span></div><div><b>04 / ДОКАЗАТЕЛЬСТВО</b><span>90 дней мониторинга после ввода объекта</span></div></section>'
        "</section>"
    )


def _service(project: ProjectSpec, shot: ShotSpec, assets: Mapping[str, str]) -> str:
    engineer = _asset(project, shot, assets, "engineer_portrait")
    installation = _asset(project, shot, assets, "duct_installation")
    return (
        f'{_header("service")}<section class="vk-service-body">'
        '<section class="vk-service-top"><div class="vk-ticket-intro"><p class="vk-kicker">СЕРВИСНЫЙ ЦЕНТР · МОСКВА</p><h1>Сервисная заявка VK-2481</h1><p>Объект: логистический комплекс «Север». Установка VK-AHU 45, серийный номер 45-0826.</p><div class="vk-ticket-fields"><div><span>Симптом</span><b>Рост перепада на фильтре</b></div><div><span>Последнее ТО</span><b>18.07.2026</b></div><div><span>Контакт объекта</span><b>Илья Власов · главный инженер</b></div></div><div class="vk-priority-controls" role="group" aria-label="Приоритет заявки"><button type="button" class="vk-selector" data-selectable="ticket-priority" data-priority="Плановая" data-sla="SLA 24 часа" aria-pressed="false">Плановая</button><button type="button" class="vk-selector active" data-selectable="ticket-priority" data-priority="Приоритетная" data-sla="SLA 8 часов" aria-pressed="true">Приоритетная</button><button type="button" class="vk-selector" data-selectable="ticket-priority" data-priority="Аварийная" data-sla="SLA 2 часа" aria-pressed="false">Аварийная</button></div></div>'
        '<div class="vk-service-visuals"><figure><img src="'
        f'{engineer}" alt="Сервисный инженер ВентКонтур" /><figcaption><b>Алексей Горин</b><span>ведущий сервисный инженер</span></figcaption></figure><figure><img src="'
        f'{installation}" alt="Монтаж воздуховодов на промышленном объекте" /><figcaption><b>Бригада №4</b><span>допуск на высотные работы</span></figcaption></figure></div></section>'
        '<div class="vk-service-main"><section class="vk-ticket-summary"><div class="vk-section-heading"><div><p class="vk-kicker">КАРТА ЗАЯВКИ</p><h2>Диагностика и комплект работ</h2></div><b class="vk-ticket-priority-value">Приоритетная</b></div><table><thead><tr><th>Операция</th><th>Норматив</th><th>Исполнитель</th><th>Материал</th></tr></thead><tbody><tr><td>Замер перепада давления</td><td>45 мин</td><td>А. Горин</td><td>Манометр VK-M2</td></tr><tr><td>Замена фильтра ePM1</td><td>60 мин</td><td>Бригада №4</td><td>2 кассеты F7</td></tr><tr><td>Балансировка секции</td><td>90 мин</td><td>А. Горин</td><td>Протокол VK-BAL</td></tr></tbody></table><div class="vk-ticket-sla"><span>Обязательство по реакции</span><b class="vk-ticket-sla-value">SLA 8 часов</b><strong>Запчасти зарезервированы</strong></div></section>'
        '<section class="vk-service-dispatch"><div class="vk-section-heading"><div><p class="vk-kicker">ДИСПЕТЧЕРИЗАЦИЯ</p><h2 class="vk-dispatch-status">Инженер назначен</h2></div><b class="vk-dispatch-eta">ETA 16:10</b></div><div class="vk-status-controls" role="group" aria-label="Статус выезда"><button type="button" class="vk-selector active" data-selectable="ticket-status" data-status="Инженер назначен" data-eta="ETA 16:10" aria-pressed="true">Назначен</button><button type="button" class="vk-selector" data-selectable="ticket-status" data-status="Бригада выехала" data-eta="ETA 14:30" aria-pressed="false">В пути</button><button type="button" class="vk-selector" data-selectable="ticket-status" data-status="Работы на объекте" data-eta="Завершение 18:00" aria-pressed="false">На объекте</button></div><ol><li><b>12:08</b><span>Заявка принята диспетчером</span></li><li><b>12:21</b><span>Параметры проверены удалённо</span></li><li><b>12:34</b><span class="vk-current-log">Инженер и комплект назначены</span></li></ol><div class="vk-dispatch-contact"><b>Диспетчер: Марина Лебедева</b><span>+7 (495) 221-18-44 · линия 24/7</span></div></section></div>'
        '<section class="vk-service-schedule"><div><p class="vk-kicker">ПЛАНОВОЕ ОБСЛУЖИВАНИЕ</p><h2>График обслуживания</h2><span>Интервалы пересчитаны по фактическим моточасам.</span></div><table><thead><tr><th>Узел</th><th>Последняя работа</th><th>Следующая дата</th><th>Моточасы</th><th>Состояние</th><th>Документ</th></tr></thead><tbody><tr><td><b>Фильтровальная секция</b></td><td>18.07.2026</td><td>24.08.2026</td><td>4 120</td><td>Требует замены</td><td>ТО-2481/1</td></tr><tr><td><b>Вентиляторный блок</b></td><td>12.06.2026</td><td>12.09.2026</td><td>3 840</td><td>Норма</td><td>ТО-2314/3</td></tr><tr><td><b>Шкаф автоматики</b></td><td>12.06.2026</td><td>12.12.2026</td><td>3 840</td><td>Норма</td><td>ЭЛ-2314/4</td></tr><tr><td><b>Теплообменник</b></td><td>04.04.2026</td><td>04.10.2026</td><td>3 110</td><td>Промывка по графику</td><td>ТО-2118/2</td></tr></tbody></table><div class="vk-maintenance-footer"><b>История объекта: 14 выездов · 97% закрыто в SLA</b><span>Следующий полный аудит: 12.09.2026</span><button type="button" class="vk-outline-action">Скачать журнал</button></div></section>'
        "</section>"
    )


_CSS = """
.vk-page { width: 100%; height: 1120px; overflow: hidden; background: #ffffff; color: #151816; font-family: "Arial Narrow", "Roboto Condensed", "Segoe UI", Arial, sans-serif; font-size: 14px; letter-spacing: 0; }
.vk-page *, .vk-page *::before, .vk-page *::after { box-sizing: border-box; }
.vk-page h1, .vk-page h2, .vk-page h3, .vk-page p, .vk-page figure, .vk-page dl, .vk-page dd { margin: 0; }
.vk-page button, .vk-page input { font: inherit; letter-spacing: 0; }
.vk-page button { cursor: pointer; }
.vk-page table { border-collapse: collapse; }
.vk-page img { display: block; }
.vk-page .lucide-icon { flex: 0 0 auto; stroke-width: 1.5; }
.vk-utility-header { height: 68px; display: grid; grid-template-columns: 310px 1fr 250px 180px 174px; align-items: center; gap: 24px; padding: 0 48px; border-bottom: 1px solid #cfd4d1; background: #ffffff; }
.vk-brand { display: flex; align-items: center; gap: 12px; }
.vk-brand i { width: 38px; height: 38px; display: grid; grid-template-columns: 1fr 1fr; gap: 7px; padding: 6px; border: 3px solid #078d2f; }
.vk-brand i span { background: #078d2f; }
.vk-brand i span:first-child { align-self: end; height: 7px; }
.vk-brand i span:last-child { align-self: start; height: 7px; }
.vk-brand div { display: grid; gap: 1px; }
.vk-brand b { font-size: 25px; line-height: 1; }
.vk-brand small, .vk-contact small { color: #68716b; font-size: 12px; line-height: 1.2; }
.vk-utility-copy { color: #68716b; font-size: 12px; line-height: 1.35; }
.vk-contact { display: grid; gap: 3px; justify-items: end; }
.vk-contact b { font-size: 15px; }
.vk-outline-action { min-height: 38px; padding: 0 15px; border: 1px solid #078d2f; background: #ffffff; color: #078d2f; font-size: 12px; font-weight: 800; text-transform: uppercase; }
.vk-account { display: flex; align-items: center; justify-content: end; gap: 8px; font-size: 12px; font-weight: 700; }
.vk-catalog-header { height: 54px; display: grid; grid-template-columns: 280px 1fr 320px 105px; align-items: stretch; border-bottom: 1px solid #cfd4d1; background: #eef0ef; }
.vk-catalog-trigger { display: flex; align-items: center; gap: 12px; padding: 0 24px 0 48px; background: #078d2f; color: #ffffff; font-size: 13px; }
.vk-catalog-header nav { display: flex; align-items: stretch; padding-left: 18px; }
.vk-nav-item { min-width: 112px; display: inline-flex; align-items: center; justify-content: center; border-bottom: 3px solid transparent; font-size: 12px; font-weight: 800; text-transform: uppercase; }
.vk-nav-item.active { border-color: #ffc400; background: #ffffff; color: #078d2f; }
.vk-search { height: 36px; align-self: center; display: flex; align-items: center; gap: 8px; padding: 0 10px; border: 1px solid #bfc6c1; background: #ffffff; }
.vk-search input { width: 100%; border: 0; outline: 0; font-size: 12px; }
.vk-header-tools { display: flex; align-items: center; justify-content: center; gap: 6px; font-size: 12px; }
.vk-header-tools span { width: 20px; height: 20px; display: grid; place-items: center; background: #ffc400; font-weight: 900; }
.vk-kicker { color: #078d2f; font-size: 12px; font-weight: 900; line-height: 1.25; text-transform: uppercase; }
.vk-primary { min-height: 42px; padding: 0 18px; border: 1px solid #078d2f; background: #078d2f; color: #ffffff; font-size: 13px; font-weight: 850; text-transform: uppercase; }
.vk-link-action { min-height: 42px; padding: 0; border: 0; border-bottom: 2px solid #151816; background: #ffffff; color: #151816; font-size: 13px; font-weight: 800; }
.vk-compact-action { min-height: 36px; padding: 0 14px; border: 1px solid #151816; background: #ffffff; color: #151816; font-size: 12px; font-weight: 800; text-transform: uppercase; }
.vk-yellow-action { min-height: 40px; border: 1px solid #ffc400; background: #ffc400; color: #151816; font-size: 12px; font-weight: 900; text-transform: uppercase; }
.vk-selector { min-height: 38px; padding: 0 14px; border: 1px solid #aeb6b0; background: #ffffff; color: #4e5751; font-size: 12px; font-weight: 800; }
.vk-selector.active { border-color: #078d2f; background: #078d2f; color: #ffffff; }
.vk-cover-body { height: 998px; display: grid; grid-template-rows: 590px 408px; }
.vk-cover-hero { display: grid; grid-template-columns: 44% 56%; }
.vk-cover-copy { display: flex; flex-direction: column; align-items: flex-start; padding: 62px 54px 38px 76px; }
.vk-cover-copy h1 { max-width: 660px; margin-top: 17px; font-size: 51px; line-height: 1.02; font-weight: 900; }
.vk-lead { max-width: 600px; margin-top: 22px !important; color: #68716b; font-size: 16px; line-height: 1.45; }
.vk-cover-actions { display: flex; gap: 24px; margin-top: 28px; }
.vk-cover-specs { width: 100%; display: grid; grid-template-columns: repeat(3, 1fr); margin-top: auto; border-top: 1px solid #bfc6c1; }
.vk-cover-specs div { padding: 18px 14px 0 0; border-right: 1px solid #cfd4d1; }
.vk-cover-specs div + div { padding-left: 18px; }
.vk-cover-specs dt { font-size: 24px; font-weight: 900; }
.vk-cover-specs dd { margin-top: 5px; color: #68716b; font-size: 12px; }
.vk-cover-media { overflow: hidden; background: #eef0ef; }
.vk-cover-media img { width: 100%; height: 100%; object-fit: cover; object-position: center; }
.vk-cover-products { padding: 24px 58px 0; border-top: 5px solid #ffc400; background: #ffffff; }
.vk-cover-products-head { height: 72px; display: grid; grid-template-columns: 390px 1fr auto; align-items: center; gap: 34px; }
.vk-cover-products-head h2 { margin-top: 4px; font-size: 24px; }
.vk-cover-products-head > p { color: #68716b; font-size: 12px; line-height: 1.35; }
.vk-cover-products table { width: 100%; font-size: 12px; }
.vk-cover-products th { height: 34px; border-top: 1px solid #cfd4d1; border-bottom: 1px solid #cfd4d1; color: #68716b; text-align: left; text-transform: uppercase; }
.vk-cover-products td { height: 62px; border-bottom: 1px solid #d9ddda; }
.vk-cover-products td:first-child { width: 310px; }
.vk-cover-products td b, .vk-cover-products td span { display: block; }
.vk-cover-products td b { color: #078d2f; font-size: 14px; }
.vk-cover-products td span { margin-top: 3px; color: #68716b; }
.vk-cover-products td strong { color: #078d2f; }
.vk-procurement-line { height: 56px; display: flex; align-items: center; gap: 28px; font-size: 12px; }
.vk-procurement-line span { padding-left: 12px; border-left: 3px solid #ffc400; }
.vk-procurement-line strong { margin-left: auto; color: #078d2f; }
.vk-route-head { display: grid; grid-template-columns: 1fr auto; align-items: end; gap: 36px; }
.vk-route-head h1 { margin-top: 7px; font-size: 36px; line-height: 1.05; }
.vk-route-head > p { max-width: 610px; color: #68716b; font-size: 13px; line-height: 1.4; }
.vk-route-controls { display: flex; align-items: center; }
.vk-route-controls .vk-selector + .vk-selector { border-left: 0; }
.vk-catalog-body { height: 998px; display: grid; grid-template-rows: 82px 540px 1fr; gap: 14px; padding: 20px 50px; }
.vk-catalog-main { display: grid; grid-template-columns: 230px 1fr 315px; gap: 18px; min-height: 0; }
.vk-filter-panel { padding: 17px; border: 1px solid #cfd4d1; background: #eef0ef; }
.vk-filter-title { display: flex; align-items: center; gap: 8px; padding-bottom: 12px; border-bottom: 2px solid #151816; font-size: 12px; }
.vk-filter-panel > label { display: grid; gap: 7px; margin-top: 14px; color: #4e5751; font-size: 12px; font-weight: 800; }
.vk-filter-panel > label div { display: grid; grid-template-columns: 1fr 1fr; gap: 7px; }
.vk-filter-panel input { width: 100%; height: 34px; padding: 0 8px; border: 1px solid #bfc6c1; background: #ffffff; font-size: 12px; }
.vk-filter-panel fieldset { display: grid; gap: 8px; margin: 16px 0; padding: 12px 0; border: 0; border-top: 1px solid #bfc6c1; border-bottom: 1px solid #bfc6c1; }
.vk-filter-panel legend { padding: 0 0 8px; font-size: 12px; font-weight: 900; }
.vk-filter-panel fieldset label { font-size: 12px; }
.vk-filter-panel .vk-yellow-action { width: 100%; }
.vk-filter-panel > p { margin-top: 12px; color: #68716b; font-size: 12px; line-height: 1.35; }
.vk-catalog-table { min-width: 0; border-top: 4px solid #078d2f; }
.vk-table-title { height: 54px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #cfd4d1; }
.vk-table-title b { font-size: 16px; }
.vk-table-title span { color: #68716b; font-size: 12px; }
.vk-catalog-table table { width: 100%; table-layout: fixed; font-size: 12px; }
.vk-catalog-table th { height: 36px; border-bottom: 1px solid #cfd4d1; color: #68716b; text-align: left; }
.vk-catalog-table td { height: 66px; border-bottom: 1px solid #d9ddda; }
.vk-catalog-table td:first-child { width: 205px; }
.vk-catalog-table td b, .vk-catalog-table td span { display: block; }
.vk-catalog-table td b { color: #078d2f; font-size: 13px; }
.vk-catalog-table td span { margin-top: 3px; color: #68716b; }
.vk-table-note { height: 46px; display: flex; align-items: center; gap: 22px; padding: 0 12px; background: #eef0ef; font-size: 12px; }
.vk-catalog-site { display: grid; grid-template-rows: 205px 1fr; background: #151816; color: #ffffff; }
.vk-catalog-site img { width: 100%; height: 205px; object-fit: cover; }
.vk-catalog-site > div { padding: 20px; }
.vk-catalog-site h2 { margin-top: 6px; font-size: 22px; }
.vk-catalog-site dl { display: grid; gap: 7px; margin-top: 17px; }
.vk-catalog-site dl div { display: flex; justify-content: space-between; padding-bottom: 6px; border-bottom: 1px solid #465048; font-size: 12px; }
.vk-catalog-site dt { color: #bfc6c1; }
.vk-catalog-site .vk-outline-action { width: 100%; margin-top: 15px; background: #151816; color: #ffffff; border-color: #ffffff; }
.vk-catalog-comparison { display: grid; grid-template-columns: 300px 1fr 230px; gap: 26px; padding: 22px; border-top: 4px solid #ffc400; background: #eef0ef; }
.vk-catalog-comparison h2 { margin-top: 7px; font-size: 23px; line-height: 1.12; }
.vk-comparison-body table { width: 100%; font-size: 12px; }
.vk-comparison-body th, .vk-comparison-body td { height: 38px; padding: 0 12px; border-bottom: 1px solid #c3c9c5; text-align: left; }
.vk-comparison-body th { color: #68716b; }
.vk-comparison-body td:first-child { font-weight: 800; }
.vk-compare-decision { display: flex; flex-direction: column; align-items: flex-start; padding-left: 20px; border-left: 1px solid #bfc6c1; }
.vk-compare-decision b { font-size: 12px; text-transform: uppercase; }
.vk-compare-decision strong { margin-top: 10px; color: #078d2f; font-size: 28px; }
.vk-compare-decision span { margin-top: 5px; color: #68716b; font-size: 12px; }
.vk-compare-decision .vk-primary { width: 100%; margin-top: auto; }
.vk-selection-body { height: 998px; display: grid; grid-template-rows: 82px 552px 1fr; gap: 16px; padding: 24px 54px; }
.vk-selection-main { display: grid; grid-template-columns: 1fr 520px; gap: 22px; min-height: 0; }
.vk-worksheet { border: 1px solid #cfd4d1; }
.vk-worksheet-head { height: 48px; display: flex; align-items: center; justify-content: space-between; padding: 0 18px; background: #151816; color: #ffffff; font-size: 12px; }
.vk-duty-presets { display: flex; padding: 14px 18px 0; }
.vk-duty-presets .vk-selector + .vk-selector { border-left: 0; }
.vk-input-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px 14px; padding: 16px 18px; }
.vk-input-grid label { display: grid; grid-template-columns: 1fr 120px 45px; align-items: center; min-height: 42px; border-bottom: 1px solid #d9ddda; font-size: 12px; }
.vk-input-grid label span { font-weight: 800; }
.vk-input-grid input { height: 34px; padding: 0 9px; border: 1px solid #aeb6b0; font-size: 13px; font-weight: 800; text-align: right; }
.vk-input-grid label b { padding-left: 9px; font-size: 12px; }
.vk-loss-table { width: calc(100% - 36px); margin: 0 18px; font-size: 12px; }
.vk-loss-table th, .vk-loss-table td { height: 34px; padding: 0 10px; border-bottom: 1px solid #d9ddda; text-align: left; }
.vk-loss-table th { background: #eef0ef; }
.vk-engineering-check { height: 51px; display: grid; grid-template-columns: 180px 1fr auto; align-items: center; gap: 15px; margin: 15px 18px 0; padding: 0 14px; border-left: 5px solid #078d2f; background: #eef0ef; font-size: 12px; }
.vk-engineering-check strong { color: #078d2f; font-size: 15px; }
.vk-selection-result { display: grid; grid-template-rows: 238px 1fr; border: 1px solid #cfd4d1; }
.vk-selection-result > img { width: 100%; height: 238px; object-fit: cover; object-position: center 42%; }
.vk-result-sheet { padding: 19px 24px; background: #eef0ef; }
.vk-result-sheet h2 { margin-top: 5px; font-size: 30px; }
.vk-result-sheet dl { display: grid; gap: 7px; margin-top: 13px; }
.vk-result-sheet dl div { display: grid; grid-template-columns: 155px 1fr; gap: 12px; padding-bottom: 6px; border-bottom: 1px solid #c3c9c5; font-size: 12px; }
.vk-result-sheet dt { color: #68716b; }
.vk-result-sheet dd { font-weight: 800; }
.vk-result-sheet .vk-primary { width: 100%; min-height: 38px; margin-top: 12px; }
.vk-selection-comparison { display: grid; grid-template-columns: 300px 1fr; gap: 28px; padding: 22px; border-top: 4px solid #078d2f; background: #eef0ef; }
.vk-selection-comparison h2 { margin-top: 7px; font-size: 23px; line-height: 1.12; }
.vk-selection-comparison > div > span { display: block; margin-top: 9px; color: #68716b; font-size: 12px; line-height: 1.35; }
.vk-selection-comparison table { width: 100%; font-size: 12px; }
.vk-selection-comparison th, .vk-selection-comparison td { height: 48px; padding: 0 12px; border-bottom: 1px solid #c3c9c5; text-align: left; }
.vk-selection-comparison th { color: #68716b; }
.vk-selection-comparison td:first-child { color: #078d2f; }
.vk-projects-body { height: 998px; display: grid; grid-template-rows: 420px 366px 212px; }
.vk-project-hero { display: grid; grid-template-columns: 58% 42%; }
.vk-project-hero > img { width: 100%; height: 420px; object-fit: cover; }
.vk-project-hero > div { padding: 52px 58px; background: #eef0ef; }
.vk-project-hero h1 { max-width: 600px; margin-top: 12px; font-size: 39px; line-height: 1.04; }
.vk-project-hero p:not(.vk-kicker) { margin-top: 19px; color: #68716b; font-size: 14px; line-height: 1.45; }
.vk-project-hero dl { display: grid; grid-template-columns: repeat(3, 1fr); margin-top: 34px; border-top: 1px solid #bfc6c1; }
.vk-project-hero dl div { padding: 18px 12px 0 0; }
.vk-project-hero dt { font-size: 20px; font-weight: 900; }
.vk-project-hero dd { margin-top: 5px; color: #68716b; font-size: 12px; }
.vk-project-evidence { padding: 20px 54px; }
.vk-project-evidence > header { display: flex; align-items: end; justify-content: space-between; }
.vk-project-evidence h2 { margin-top: 5px; font-size: 25px; }
.vk-project-kpis { display: grid; grid-template-columns: repeat(4, 1fr); margin-top: 16px; border-top: 4px solid #ffc400; border-bottom: 1px solid #cfd4d1; }
.vk-project-kpis div { display: grid; gap: 5px; padding: 12px 16px; border-right: 1px solid #cfd4d1; }
.vk-project-kpis span, .vk-project-kpis small { color: #68716b; font-size: 12px; }
.vk-project-kpis b { font-size: 15px; }
.vk-project-evidence table { width: 100%; margin-top: 10px; font-size: 12px; }
.vk-project-evidence th, .vk-project-evidence td { height: 36px; padding: 0 12px; border-bottom: 1px solid #d9ddda; text-align: left; }
.vk-project-evidence th { color: #68716b; }
.vk-project-evidence td:last-child { color: #078d2f; font-weight: 900; }
.vk-project-log { display: grid; grid-template-columns: repeat(4, 1fr); padding: 28px 54px; background: #151816; color: #ffffff; }
.vk-project-log div { display: grid; align-content: start; gap: 16px; padding: 12px 24px; border-left: 1px solid #68716b; }
.vk-project-log b { color: #ffc400; font-size: 12px; }
.vk-project-log span { max-width: 270px; font-size: 14px; line-height: 1.4; }
.vk-service-body { height: 998px; display: grid; grid-template-rows: 330px 392px 276px; }
.vk-service-top { display: grid; grid-template-columns: 1fr 680px; border-bottom: 1px solid #cfd4d1; }
.vk-ticket-intro { padding: 34px 50px; }
.vk-ticket-intro h1 { margin-top: 8px; font-size: 37px; }
.vk-ticket-intro > p:not(.vk-kicker) { margin-top: 12px; color: #68716b; font-size: 13px; }
.vk-ticket-fields { display: grid; grid-template-columns: 1fr 150px 1.2fr; gap: 14px; margin-top: 24px; border-top: 1px solid #cfd4d1; }
.vk-ticket-fields div { display: grid; gap: 5px; padding-top: 12px; font-size: 12px; }
.vk-ticket-fields span { color: #68716b; }
.vk-priority-controls { display: flex; margin-top: 20px; }
.vk-priority-controls .vk-selector + .vk-selector { border-left: 0; }
.vk-service-visuals { display: grid; grid-template-columns: 1fr 1fr; }
.vk-service-visuals figure { display: grid; grid-template-rows: 260px 70px; border-left: 1px solid #ffffff; background: #151816; color: #ffffff; }
.vk-service-visuals img { width: 100%; height: 260px; object-fit: cover; }
.vk-service-visuals figure:first-child img { object-position: center 35%; }
.vk-service-visuals figcaption { display: grid; align-content: center; gap: 4px; padding: 0 16px; }
.vk-service-visuals figcaption b { font-size: 14px; }
.vk-service-visuals figcaption span { color: #bfc6c1; font-size: 12px; }
.vk-service-main { display: grid; grid-template-columns: 1fr 520px; gap: 22px; padding: 22px 50px; }
.vk-ticket-summary, .vk-service-dispatch { border-top: 4px solid #078d2f; }
.vk-section-heading { height: 64px; display: flex; align-items: center; justify-content: space-between; }
.vk-section-heading h2 { margin-top: 4px; font-size: 22px; }
.vk-section-heading > b { padding: 8px 11px; background: #ffc400; font-size: 12px; }
.vk-ticket-summary table { width: 100%; font-size: 12px; }
.vk-ticket-summary th, .vk-ticket-summary td { height: 43px; padding: 0 12px; border-bottom: 1px solid #d9ddda; text-align: left; }
.vk-ticket-summary th { background: #eef0ef; color: #68716b; }
.vk-ticket-sla { height: 48px; display: grid; grid-template-columns: 1fr auto auto; align-items: center; gap: 25px; padding: 0 13px; background: #eef0ef; font-size: 12px; }
.vk-ticket-sla b { color: #078d2f; font-size: 15px; }
.vk-service-dispatch { padding-left: 20px; border-left: 1px solid #cfd4d1; }
.vk-status-controls { display: flex; }
.vk-status-controls .vk-selector { flex: 1; }
.vk-status-controls .vk-selector + .vk-selector { border-left: 0; }
.vk-service-dispatch ol { display: grid; gap: 0; margin: 14px 0 0; padding: 0; list-style: none; }
.vk-service-dispatch li { display: grid; grid-template-columns: 60px 1fr; gap: 12px; padding: 9px 0; border-bottom: 1px solid #d9ddda; font-size: 12px; }
.vk-service-dispatch li b { color: #078d2f; }
.vk-dispatch-contact { display: flex; justify-content: space-between; margin-top: 12px; font-size: 12px; }
.vk-dispatch-contact span { color: #68716b; }
.vk-service-schedule { display: grid; grid-template-columns: 290px 1fr; grid-template-rows: 1fr 48px; gap: 0 26px; padding: 22px 50px 16px; border-top: 5px solid #ffc400; background: #eef0ef; }
.vk-service-schedule h2 { margin-top: 6px; font-size: 24px; }
.vk-service-schedule > div:first-child > span { display: block; margin-top: 9px; color: #68716b; font-size: 12px; line-height: 1.4; }
.vk-service-schedule table { width: 100%; font-size: 12px; }
.vk-service-schedule th, .vk-service-schedule td { height: 38px; padding: 0 10px; border-bottom: 1px solid #c3c9c5; text-align: left; }
.vk-service-schedule th { color: #68716b; }
.vk-maintenance-footer { grid-column: 1 / -1; display: grid; grid-template-columns: 1fr auto auto; align-items: center; gap: 26px; border-top: 1px solid #bfc6c1; font-size: 12px; }
.vk-maintenance-footer span { color: #68716b; }
"""


_SCRIPTS = r"""
(() => {
  const choose = (group, button) => {
    document.querySelectorAll(`[data-selectable="${group}"]`).forEach((item) => {
      const selected = item === button;
      item.classList.toggle("active", selected);
      item.setAttribute("aria-pressed", String(selected));
    });
  };
  const makeRow = (values) => {
    const row = document.createElement("tr");
    values.forEach((value, index) => {
      const cell = document.createElement("td");
      if (index === 0) {
        const parts = value.split("~");
        const model = document.createElement("b");
        model.textContent = parts[0];
        cell.append(model);
        if (parts[1]) {
          const purpose = document.createElement("span");
          purpose.textContent = parts[1];
          cell.append(purpose);
        }
      } else {
        cell.textContent = value;
      }
      row.append(cell);
    });
    return row;
  };
  document.querySelectorAll('[data-selectable="catalog-sector"]').forEach((button) => {
    button.addEventListener("click", () => {
      choose("catalog-sector", button);
      const body = document.querySelector(".vk-catalog-table tbody");
      const heading = document.querySelector(".vk-catalog-comparison h2");
      if (body) {
        body.replaceChildren(...button.dataset.rows.split(";").map((entry) => {
          const values = entry.split("|");
          values[0] = `${values[0]}~${values[1]}`;
          values.splice(1, 1);
          return makeRow(values);
        }));
      }
      if (heading) heading.textContent = `Сравнение характеристик · ${button.dataset.sectorTitle}`;
    });
  });
  const formatNumber = (value) => Math.round(value).toString().replace(/\B(?=(\d{3})+(?!\d))/g, " ");
  const updateSelection = () => {
    const airflowInput = document.querySelector("[data-airflow]");
    const pressureInput = document.querySelector("[data-pressure]");
    if (!airflowInput || !pressureInput) return;
    const airflow = Number(airflowInput.value) || 0;
    const pressure = Number(pressureInput.value) || 0;
    const model = airflow >= 24000 || pressure >= 900 ? "VK-AHU 60" : airflow >= 14000 ? "VK-AHU 45" : "VK-AHU 30";
    const motor = model === "VK-AHU 60" ? "37 кВт · IE4" : model === "VK-AHU 45" ? "22 кВт · IE4" : "18 кВт · IE4";
    const write = (selector, value) => {
      const target = document.querySelector(selector);
      if (target) target.textContent = value;
    };
    write(".vk-selection-model", model);
    write(".vk-result-airflow", `${formatNumber(airflow)} м³/ч`);
    write(".vk-result-pressure", `${formatNumber(pressure)} Па`);
    write(".vk-result-reserve", "Резерв по расходу 15%");
    write(".vk-result-motor", motor);
    write(".vk-computed-flow", `${formatNumber(airflow)} м³/ч`);
    write(".vk-computed-pressure", `${formatNumber(pressure)} Па`);
  };
  document.querySelectorAll('[data-selectable="selection-duty"]').forEach((button) => {
    button.addEventListener("click", () => {
      choose("selection-duty", button);
      const airflow = document.querySelector("[data-airflow]");
      const pressure = document.querySelector("[data-pressure]");
      if (airflow) airflow.value = button.dataset.airflowValue;
      if (pressure) pressure.value = button.dataset.pressureValue;
      updateSelection();
    });
  });
  document.querySelectorAll("[data-airflow], [data-pressure]").forEach((input) => {
    input.addEventListener("input", updateSelection);
  });
  document.querySelectorAll('[data-selectable="project-sector"]').forEach((button) => {
    button.addEventListener("click", () => {
      choose("project-sector", button);
      const values = {
        ".vk-project-evidence h2": button.dataset.title,
        ".vk-project-standard": button.dataset.standard,
        ".vk-project-controls": button.dataset.controls,
        ".vk-project-airflow": button.dataset.airflow,
        ".vk-project-effect": button.dataset.effect,
      };
      Object.entries(values).forEach(([selector, value]) => {
        const target = document.querySelector(selector);
        if (target) target.textContent = value;
      });
    });
  });
  document.querySelectorAll('[data-selectable="ticket-priority"]').forEach((button) => {
    button.addEventListener("click", () => {
      choose("ticket-priority", button);
      const priority = document.querySelector(".vk-ticket-priority-value");
      const sla = document.querySelector(".vk-ticket-sla-value");
      if (priority) priority.textContent = button.dataset.priority;
      if (sla) sla.textContent = button.dataset.sla;
    });
  });
  document.querySelectorAll('[data-selectable="ticket-status"]').forEach((button) => {
    button.addEventListener("click", () => {
      choose("ticket-status", button);
      const status = document.querySelector(".vk-dispatch-status");
      const eta = document.querySelector(".vk-dispatch-eta");
      const log = document.querySelector(".vk-current-log");
      if (status) status.textContent = button.dataset.status;
      if (eta) eta.textContent = button.dataset.eta;
      if (log) log.textContent = `${button.dataset.status} · ${button.dataset.eta}`;
    });
  });
})();
"""


def render(
    project: ProjectSpec, shot: ShotSpec, assets: Mapping[str, str]
) -> RenderedPage:
    """Render one route of the standalone Ventkontur industrial site."""
    if project.slug != "ventkontur":
        raise KeyError(f"ventkontur renderer cannot render project {project.slug}")
    try:
        page_builder = {
            "cover": _cover,
            "catalog": _catalog,
            "selection": _selection,
            "projects": _projects,
            "service": _service,
        }[shot.key]
    except KeyError as exc:
        raise ValueError(
            f"ventkontur renderer does not support route {shot.key}"
        ) from exc
    return RenderedPage(
        html=(
            f'<main class="vk-page vk-{shot.key}" data-site="ventkontur" '
            f'data-route="{shot.key}">{page_builder(project, shot, assets)}</main>'
        ),
        css=_CSS,
        scripts=_SCRIPTS if shot.key in {"catalog", "selection", "projects", "service"} else "",
    )
