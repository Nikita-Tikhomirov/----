"""Dedicated window-manufacturer renderer for Okna Sfera."""

from collections.abc import Mapping

from ..components import escape_html
from ..icons import icon
from ..models import ProjectSpec, ShotSpec
from .runtime import RenderedPage


_ROUTE_ASSETS = {
    "cover": ("installer_portrait",),
    "windows": ("window_facade",),
    "calculator": ("bright_kitchen",),
    "profiles": ("profile_closeup",),
    "installation": ("glazing_process", "balcony_view"),
}


def _owned_assets(route: str, assets: Mapping[str, str]) -> dict[str, str]:
    resolved: dict[str, str] = {}
    for key in _ROUTE_ASSETS[route]:
        try:
            resolved[key] = escape_html(assets[key])
        except KeyError as exc:
            raise KeyError(f"okna-sfera {route} missing asset {key}") from exc
    return resolved


def _brand() -> str:
    return (
        '<a class="os-brand" href="#" aria-label="Окна Сфера">'
        '<span class="os-brand-mark" aria-hidden="true">'
        '<svg viewBox="0 0 48 48" width="42" height="42" fill="none" '
        'xmlns="http://www.w3.org/2000/svg">'
        '<circle cx="24" cy="24" r="18" stroke="currentColor" stroke-width="6"/>'
        '<path d="M24 6L34.5 16.5L30 31.5L13.5 32L8 17.5L24 6Z" '
        'stroke="currentColor" stroke-width="4" stroke-linejoin="miter"/>'
        '<circle cx="24" cy="24" r="6" fill="currentColor"/></svg></span>'
        '<span><b>Окна Сфера</b><small>Качество в каждой детали</small></span></a>'
    )


def _header(active: str) -> str:
    links = (
        ("windows", "Пластиковые окна"),
        ("profiles", "Профили"),
        ("calculator", "Калькулятор"),
        ("installation", "Монтаж"),
    )
    nav = "".join(
        f'<a href="#" class="{"is-active" if key == active else ""}">{label}</a>'
        for key, label in links
    )
    return (
        '<header class="os-header"><div class="os-utility-header">'
        '<span>Собственное производство · Москва и область</span>'
        '<span>Замер сегодня до 21:00</span><span>Гарантия до 10 лет</span></div>'
        '<div class="os-main-header">'
        f'{_brand()}<nav aria-label="Основная навигация">{nav}'
        '<a href="#">Проекты</a><a href="#">Контакты</a></nav>'
        '<div class="os-contact"><b>+7 (495) 215-12-15</b><small>ежедневно 9:00–21:00</small></div>'
        '<button type="button" class="os-outline-action">Перезвоните мне</button>'
        '</div></header>'
    )


def _cover(assets: Mapping[str, str]) -> str:
    return (
        '<main class="os-route os-cover"><section class="os-cover-hero">'
        '<div class="os-cover-copy"><span class="os-kicker">Окна напрямую с производства</span>'
        '<h1>Пластиковые окна от производителя</h1>'
        '<p>Точный замер, профиль с паспортом и монтаж по ГОСТ. Цена фиксируется до запуска заказа.</p>'
        '<div class="os-cover-benefits"><span><b>7 дней</b> производство</span>'
        '<span><b>10 лет</b> гарантия</span><span><b>0 ₽</b> замер</span></div>'
        '<div class="os-cover-config"><div><span>Выберите конструкцию</span>'
        '<div class="os-sash-buttons">'
        '<button type="button" data-selectable="cover-sash" data-value="one" aria-pressed="false">1 створка</button>'
        '<button type="button" data-selectable="cover-sash" data-value="two" aria-pressed="true">2 створки</button>'
        '<button type="button" data-selectable="cover-sash" data-value="three" aria-pressed="false">3 створки</button>'
        '<button type="button" data-selectable="cover-sash" data-value="balcony" aria-pressed="false">Балконный блок</button>'
        '</div></div><aside class="os-cover-quote"><span>Расчёт за 1 минуту</span>'
        '<h2 data-cover-title>Двухстворчатое окно</h2><p data-cover-size>1450 × 1400 мм</p>'
        '<dl><div><dt>Цена с монтажом</dt><dd data-cover-price>от 23 700 ₽</dd></div>'
        '<div><dt>Готовность</dt><dd data-cover-term>6 рабочих дней</dd></div></dl>'
        '<button type="button">Получить точный расчёт '
        f'{icon("arrow-right", size=18)}</button></aside></div></div>'
        '<figure class="os-cover-photo"><img src="'
        f'{assets["installer_portrait"]}" alt="Мастер Окна Сфера выполняет замер">'
        '<figcaption><b>Алексей Громов · инженер-замерщик</b><span>Проверит проём и монтажные узлы на месте</span></figcaption></figure>'
        '</section><section class="os-review-strip"><span>Независимые отзывы</span>'
        '<b>4,9 / 5</b><span>Яндекс Карты · 286 оценок</span><span>2ГИС · 174 оценки</span>'
        '<span>97% клиентов рекомендуют монтаж</span></section>'
        '<section class="os-cover-quality"><div><span>Качество в каждой детали</span>'
        '<h2>ОКНО СОБИРАЕТСЯ ПОД КОНКРЕТНЫЙ ПРОЁМ</h2></div>'
        '<article><b>01 · профиль</b><strong>70–82 мм</strong><p>Армирование от 1,5 мм и сварные углы под контролем ОТК.</p></article>'
        '<article><b>02 · стеклопакет</b><strong>до 52 мм</strong><p>Энергосбережение, солнцезащита или защита от шума.</p></article>'
        '<article><b>03 · монтаж</b><strong>ГОСТ 30971</strong><p>Три слоя шва, защита откосов и акт скрытых работ.</p></article>'
        '</section></main>'
    )


def _windows(assets: Mapping[str, str]) -> str:
    rows = (
        ("Одностворчатое", "700 × 1400", "1", "от 17 400 ₽"),
        ("Двухстворчатое", "1450 × 1400", "2", "от 23 700 ₽"),
        ("Трёхстворчатое", "2100 × 1400", "3", "от 31 900 ₽"),
    )
    table = "".join(
        f'<tr><td><b>{name}</b></td><td>{size} мм</td><td>{sashes}</td><td>{price}</td><td><button type="button">В расчёт</button></td></tr>'
        for name, size, sashes, price in rows
    )
    return (
        '<main class="os-route os-windows"><section class="os-windows-intro">'
        '<div><span class="os-kicker">Каталог стандартных решений</span><h1>Выберите окно для вашей комнаты</h1>'
        '<p>Сравните размеры, створки и базовую стоимость. Инженер адаптирует конструкцию к вашему проёму.</p></div>'
        f'<img src="{assets["window_facade"]}" alt="Дом с остеклением Окна Сфера"></section>'
        '<section class="os-windows-workspace"><aside class="os-filter-rail"><span>Помещение</span>'
        '<div><button type="button" data-selectable="window-room" data-value="kitchen" aria-pressed="true">Кухня</button>'
        '<button type="button" data-selectable="window-room" data-value="living" aria-pressed="false">Гостиная</button>'
        '<button type="button" data-selectable="window-room" data-value="balcony" aria-pressed="false">Балкон</button></div>'
        '<span>Открывание</span><div><button type="button" data-selectable="window-opening" data-value="fixed" aria-pressed="false">Глухое</button>'
        '<button type="button" data-selectable="window-opening" data-value="swing" aria-pressed="true">Поворотное</button>'
        '<button type="button" data-selectable="window-opening" data-value="tilt" aria-pressed="false">Поворотно-откидное</button></div>'
        '<p>Все цены включают профиль, стеклопакет и фурнитуру.</p></aside>'
        '<div class="os-window-comparison"><div class="os-section-heading"><span>Подходящие решения</span>'
        '<h2>Сравнение стандартных конфигураций</h2></div>'
        '<table class="os-window-table"><thead><tr><th>Конструкция</th><th>Размер</th><th>Створки</th><th>Цена</th><th></th></tr></thead>'
        f'<tbody>{table}</tbody></table></div>'
        '<aside class="os-window-specification"><span>Спецификация выбора</span><h2 data-window-room>Кухня</h2>'
        '<p data-window-opening>Поворотное</p><dl><div><dt>Монтажная глубина</dt><dd data-window-depth>60 мм</dd></div>'
        '<div><dt>Шумоизоляция</dt><dd data-window-noise>34 дБ</dd></div><div><dt>Срок</dt><dd data-window-term>6 дней</dd></div></dl>'
        '<strong data-window-price>от 21 900 ₽</strong><button type="button">Запросить спецификацию</button></aside></section>'
        '<section class="os-windows-performance"><div><span>Тепло и тишина в цифрах</span><h2>ПРОВЕРЕННЫЕ ПОКАЗАТЕЛИ</h2></div>'
        '<article><b>Температура у рамы</b><strong>+20,4 °C</strong><p>При −20 °C снаружи по протоколу испытаний.</p></article>'
        '<article><b>Снижение шума</b><strong>до 46 дБ</strong><p>Стеклопакет с разной толщиной стёкол.</p></article>'
        '<article><b>Воздухопроницаемость</b><strong>класс А</strong><p>Контур уплотнения проверяется после монтажа.</p></article>'
        '<article><b>Гарантия</b><strong>10 лет</strong><p>Паспорт изделия и номер заказа у клиента.</p></article></section></main>'
    )


def _calculator(assets: Mapping[str, str]) -> str:
    return (
        '<main class="os-route os-calculator"><section class="os-route-heading"><div><span class="os-kicker">Точный предварительный расчёт</span>'
        '<h1>Рассчитайте окно по вашим размерам</h1></div><p>Цена меняется вместе с размером, профилем, стеклопакетом и монтажом. Все параметры останутся в заявке.</p></section>'
        '<section class="os-calculator-workspace"><div class="os-calculator-controls">'
        '<fieldset><legend>01 · тип открывания</legend><div class="os-opening-buttons">'
        '<button type="button" data-selectable="calculator-opening" data-value="one" data-factor="1.15" data-days="0" aria-pressed="false">1 створка</button>'
        '<button type="button" data-selectable="calculator-opening" data-value="two" data-factor="1.35" data-days="1" aria-pressed="true">2 створки</button>'
        '<button type="button" data-selectable="calculator-opening" data-value="three" data-factor="1.7" data-days="2" aria-pressed="false">3 створки</button></div></fieldset>'
        '<fieldset><legend>02 · размеры проёма</legend><div class="os-dimensions"><label>Ширина, мм<input type="number" min="500" max="3200" value="1450" data-calculator-width></label>'
        '<span>×</span><label>Высота, мм<input type="number" min="500" max="2600" value="1400" data-calculator-height></label></div></fieldset>'
        '<fieldset><legend>03 · профиль</legend><div class="os-profile-buttons">'
        '<button type="button" data-selectable="calculator-profile" data-name="Sfera 60" data-chambers="3" data-rate="9000" data-heat="0,64" data-days="6" aria-pressed="false">Sfera 60 <b>3 камеры</b></button>'
        '<button type="button" data-selectable="calculator-profile" data-name="Sfera 70" data-chambers="5" data-rate="11000" data-heat="0,78" data-days="7" aria-pressed="true">Sfera 70 <b>5 камер</b></button>'
        '<button type="button" data-selectable="calculator-profile" data-name="Sfera 82" data-chambers="7" data-rate="13500" data-heat="0,92" data-days="9" aria-pressed="false">Sfera 82 <b>7 камер</b></button></div></fieldset>'
        '<fieldset><legend>04 · стеклопакет</legend><div class="os-glazing-buttons">'
        '<button type="button" data-selectable="calculator-glazing" data-name="32 мм" data-noise="34" data-fee="0" data-days="0" aria-pressed="false">Стандарт <b>32 мм</b></button>'
        '<button type="button" data-selectable="calculator-glazing" data-name="40 мм" data-noise="40" data-fee="3000" data-days="1" aria-pressed="true">Тепло <b>40 мм</b></button>'
        '<button type="button" data-selectable="calculator-glazing" data-name="52 мм" data-noise="46" data-fee="6000" data-days="2" aria-pressed="false">Тишина <b>52 мм</b></button></div></fieldset>'
        '<label class="os-install-check"><input type="checkbox" data-calculator-installation> Монтаж по ГОСТ и вывоз старой рамы <b>+8 000 ₽</b></label></div>'
        f'<figure class="os-calculator-photo"><img src="{assets["bright_kitchen"]}" alt="Светлая кухня с новым окном">'
        '<figcaption>Естественный свет без холодной зоны у рамы</figcaption></figure>'
        '<aside class="os-calculator-summary" aria-live="polite"><span>Конфигурация заказа</span><h2 data-calculator-total>34 200 ₽</h2>'
        '<p data-calculator-term>8 рабочих дней</p><dl><div><dt>Профиль</dt><dd data-calculator-profile>Sfera 70 · 5 камер</dd></div>'
        '<div><dt>Стеклопакет</dt><dd data-calculator-glazing>40 мм · 40 дБ</dd></div><div><dt>Сопротивление теплу</dt><dd data-calculator-heat>0,78 м²·°C/Вт</dd></div>'
        '<div><dt>Размер</dt><dd data-calculator-size>1450 × 1400 мм</dd></div></dl><button type="button">Зафиксировать расчёт '
        f'{icon("arrow-right", size=18)}</button><small>Замер бесплатно, без обязательств</small></aside></section>'
        '<section class="os-calculator-included"><div><span>Что входит в стоимость</span><h2>МОНТАЖНЫЙ КОМПЛЕКТ</h2></div>'
        '<article><b data-included-plates>Анкерные пластины · 12 шт.</b><p>По материалу стены и карте креплений.</p></article>'
        '<article><b data-included-foam>Монтажная пена · 2 баллона</b><p>Сезонный состав с паспортом партии.</p></article>'
        '<article><b data-included-sill>Подоконник · 1450 мм</b><p>Глубина уточняется при замере.</p></article>'
        '<article><b>Пароизоляционные ленты</b><p>Внутренний и наружный контур шва.</p></article></section></main>'
    )


def _profiles(assets: Mapping[str, str]) -> str:
    return (
        '<main class="os-route os-profiles"><section class="os-profiles-hero"><div><span class="os-kicker">Инженерная основа окна</span>'
        '<h1>Профиль определяет комфорт на годы</h1><p>Сравнивайте не название серии, а монтажную глубину, армирование, уплотнение и допустимый стеклопакет.</p>'
        '<div class="os-profile-models"><button type="button" data-selectable="profile-model" data-value="60" aria-pressed="false">Sfera 60</button>'
        '<button type="button" data-selectable="profile-model" data-value="70" aria-pressed="true">Sfera 70</button>'
        '<button type="button" data-selectable="profile-model" data-value="82" aria-pressed="false">Sfera 82</button></div></div>'
        f'<img src="{assets["profile_closeup"]}" alt="Разрез оконного профиля и стеклопакета"></section>'
        '<section class="os-profile-comparison"><div class="os-section-heading"><span>Лабораторные данные</span><h2>Техническое сравнение профилей</h2></div>'
        '<table><thead><tr><th>Параметр</th><th>Sfera 60</th><th>Sfera 70</th><th>Sfera 82</th></tr></thead><tbody>'
        '<tr><td>Монтажная глубина</td><td>60 мм</td><td>70 мм</td><td>82 мм</td></tr>'
        '<tr><td>Количество камер</td><td>3</td><td>5</td><td>7</td></tr>'
        '<tr><td>Стеклопакет</td><td>до 32 мм</td><td>до 40 мм</td><td>до 52 мм</td></tr>'
        '<tr><td>Теплосопротивление</td><td>0,64</td><td>0,78</td><td>0,92 м²·°C/Вт</td></tr>'
        '<tr><td>Снижение шума</td><td>34 дБ</td><td>40 дБ</td><td>46 дБ</td></tr></tbody></table></section>'
        '<section class="os-profiles-passport"><div><span>Паспорт материалов</span><h2 data-passport-name>Sfera 70</h2><p data-passport-use>Для городских квартир и отапливаемых лоджий.</p></div>'
        '<dl><div><dt>Камеры</dt><dd data-passport-chambers>5 камер</dd></div><div><dt>Стеклопакет</dt><dd data-passport-glazing>Стеклопакет до 40 мм</dd></div>'
        '<div><dt>Тепло</dt><dd data-passport-heat>0,78 м²·°C/Вт</dd></div><div><dt>Шум</dt><dd data-passport-noise>40 дБ</dd></div>'
        '<div><dt>Армирование</dt><dd data-passport-steel>Сталь 1,5 мм</dd></div></dl><button type="button">Скачать паспорт профиля</button></section></main>'
    )


def _installation(assets: Mapping[str, str]) -> str:
    return (
        '<main class="os-route os-installation"><section class="os-route-heading"><div><span class="os-kicker">Установка с актами скрытых работ</span>'
        '<h1>Монтаж по ГОСТ без скрытых работ</h1></div><p>Проём защищаем до демонтажа. Каждый слой монтажного шва фотографируем до откосов и прикладываем к акту.</p></section>'
        '<section class="os-installation-workspace"><div class="os-installation-sequence"><span>Порядок работ</span>'
        '<ol><li><b>01</b><div><strong>Защита помещения</strong><p>Пол, мебель и проход к окну закрываются плёнкой.</p></div></li>'
        '<li><b>02</b><div><strong>Демонтаж и подготовка</strong><p>Очищаем четверть, восстанавливаем основание.</p></div></li>'
        '<li><b>03</b><div><strong>Крепление и шов</strong><p>Выставляем раму, формируем три слоя примыкания.</p></div></li>'
        '<li><b>04</b><div><strong>Регулировка и приёмка</strong><p>Проверяем створки, продувание и геометрию.</p></div></li></ol></div>'
        f'<figure class="os-installation-photo"><img src="{assets["glazing_process"]}" alt="Монтажники выставляют оконную конструкцию">'
        '<figcaption><b>Бригада № 4</b><span>Монтажники с допуском ОТК · стаж 8 лет</span></figcaption></figure>'
        '<aside class="os-installation-visit"><span>Выберите дату монтажа</span><div class="os-date-buttons">'
        '<button type="button" data-selectable="installation-date" data-value="27 августа" aria-pressed="true"><b>27</b> ЧТ</button>'
        '<button type="button" data-selectable="installation-date" data-value="28 августа" aria-pressed="false"><b>28</b> ПТ</button>'
        '<button type="button" data-selectable="installation-date" data-value="29 августа" aria-pressed="false"><b>29</b> СБ</button></div>'
        '<div class="os-time-buttons"><button type="button" data-selectable="installation-time" data-value="09:00–12:00" aria-pressed="true">09:00–12:00</button>'
        '<button type="button" data-selectable="installation-time" data-value="12:00–15:00" aria-pressed="false">12:00–15:00</button>'
        '<button type="button" data-selectable="installation-time" data-value="15:00–18:00" aria-pressed="false">15:00–18:00</button></div>'
        '<h2 data-visit-slot>27 августа · 09:00–12:00</h2><dl><div><dt>Исполнитель</dt><dd>Бригада № 4</dd></div><div><dt>Длительность</dt><dd data-visit-duration>4–5 часов</dd></div>'
        '<div><dt>Статус</dt><dd>Слот закреплён на 15 минут</dd></div></dl><button type="button">Подтвердить визит</button></aside></section>'
        '<section class="os-installation-handover"><div><span>Акт приёмки и гарантия</span><h2>КЛИЕНТ ПРИНИМАЕТ КАЖДЫЙ УЗЕЛ</h2>'
        '<ul><li>Рама выставлена по уровню, диагонали записаны</li><li>Створки работают без заеданий</li><li>Шов защищён от влаги и пара</li><li>Мусор вывезен, поверхности очищены</li></ul></div>'
        f'<figure><img src="{assets["balcony_view"]}" alt="Готовое остекление балкона">'
        '<figcaption>Гарантия на монтаж 5 лет · сервисный выезд в течение 48 часов</figcaption></figure></section></main>'
    )


_CSS = r"""
.os-page, .os-page * { box-sizing: border-box; }
.os-page { width: 100%; height: 1120px; overflow: hidden; background: #fff; color: #171b21; font-family: Arial, Helvetica, sans-serif; font-size: 14px; line-height: 1.35; letter-spacing: 0; }
.os-page button, .os-page input { font: inherit; letter-spacing: 0; }
.os-page button { cursor: pointer; }
.os-page small { font-size: 12px; }
.os-header { height: 116px; background: #fff; border-bottom: 1px solid #d9e4ec; }
.os-utility-header { height: 32px; padding: 0 42px; display: flex; align-items: center; justify-content: space-between; background: #0b4f88; color: #fff; font-size: 12px; }
.os-main-header { height: 84px; padding: 0 42px; display: grid; grid-template-columns: 245px 1fr 205px 166px; gap: 28px; align-items: center; }
.os-brand { color: #171b21; text-decoration: none; display: flex; gap: 12px; align-items: center; }
.os-brand-mark { width: 44px; height: 44px; color: #1d7fd1; display: grid; place-items: center; }
.os-brand b { display: block; font-size: 22px; line-height: 1; }
.os-brand small { display: block; margin-top: 5px; color: #697784; }
.os-main-header nav { display: flex; justify-content: center; gap: 32px; }
.os-main-header nav a { color: #171b21; text-decoration: none; padding: 30px 0 27px; border-bottom: 3px solid transparent; font-size: 13px; white-space: nowrap; }
.os-main-header nav a.is-active { color: #0b4f88; border-bottom-color: #1d7fd1; }
.os-contact { text-align: right; }
.os-contact b { display: block; font-size: 16px; font-variant-numeric: tabular-nums; }
.os-contact small { color: #697784; }
.os-outline-action { height: 44px; border: 1px solid #1d7fd1; background: #fff; color: #0b4f88; font-weight: 700; }
.os-route { height: 1004px; min-height: 0; overflow: hidden; }
.os-kicker, .os-section-heading > span { display: block; color: #0b4f88; font-size: 12px; font-weight: 700; text-transform: uppercase; }
.os-page h1, .os-page h2, .os-page p, .os-page figure, .os-page dl { margin: 0; }
.os-page h1 { margin-top: 14px; font-size: 48px; line-height: 1.04; max-width: 690px; }
.os-page h2 { font-size: 25px; line-height: 1.12; }
.os-page img { display: block; width: 100%; height: 100%; object-fit: cover; }
.os-page fieldset { margin: 0; padding: 0; border: 0; }
.os-page legend { width: 100%; margin-bottom: 10px; color: #0b4f88; font-size: 12px; font-weight: 700; text-transform: uppercase; }

.os-cover-hero { height: 586px; display: grid; grid-template-columns: 54% 46%; border-bottom: 1px solid #d9e4ec; }
.os-cover-copy { padding: 46px 40px 28px 54px; }
.os-cover-copy > p { margin-top: 18px; max-width: 620px; color: #566571; font-size: 17px; }
.os-cover-benefits { margin-top: 24px; display: flex; gap: 32px; }
.os-cover-benefits span { padding-right: 30px; border-right: 1px solid #cddae3; color: #697784; }
.os-cover-benefits span:last-child { border: 0; }
.os-cover-benefits b { display: block; color: #171b21; font-size: 20px; }
.os-cover-config { margin-top: 28px; display: grid; grid-template-columns: 1fr 285px; gap: 20px; border-top: 1px solid #cddae3; padding-top: 18px; }
.os-cover-config > div > span, .os-cover-quote > span { color: #0b4f88; font-size: 12px; font-weight: 700; text-transform: uppercase; }
.os-sash-buttons { margin-top: 12px; display: grid; grid-template-columns: 1fr 1fr; }
.os-sash-buttons button { height: 46px; border: 1px solid #c6d2db; background: #fff; color: #171b21; margin: -1px 0 0 -1px; }
.os-sash-buttons button[aria-pressed="true"] { border-color: #f7b500; background: #f7b500; font-weight: 700; position: relative; }
.os-cover-quote { padding: 14px 16px; border-left: 3px solid #f7b500; background: #eaf5fd; }
.os-cover-quote h2 { margin-top: 7px; font-size: 19px; }
.os-cover-quote > p { color: #697784; font-variant-numeric: tabular-nums; }
.os-cover-quote dl { margin-top: 9px; display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.os-cover-quote dt { color: #697784; font-size: 12px; }
.os-cover-quote dd { margin: 2px 0 0; font-weight: 800; font-variant-numeric: tabular-nums; }
.os-cover-quote button, .os-calculator-summary button { width: 100%; height: 40px; margin-top: 10px; border: 0; background: #f7b500; color: #171b21; font-weight: 800; display: flex; align-items: center; justify-content: center; gap: 10px; }
.os-cover-photo { position: relative; min-width: 0; }
.os-cover-photo figcaption { position: absolute; left: 0; bottom: 0; width: 410px; padding: 17px 20px; background: #fff; border-top: 4px solid #1d7fd1; }
.os-cover-photo figcaption b, .os-cover-photo figcaption span { display: block; }
.os-cover-photo figcaption span { color: #697784; margin-top: 4px; }
.os-review-strip { height: 76px; padding: 0 54px; display: grid; grid-template-columns: 180px 130px 1fr 1fr 1.2fr; align-items: center; border-bottom: 1px solid #d9e4ec; color: #697784; }
.os-review-strip b { color: #171b21; font-size: 20px; }
.os-cover-quality { height: 342px; display: grid; grid-template-columns: 1.35fr repeat(3, 1fr); background: #eaf5fd; }
.os-cover-quality > * { padding: 40px 34px; border-right: 1px solid #c7dce9; }
.os-cover-quality > div { padding-left: 54px; background: #0b4f88; color: #fff; }
.os-cover-quality > div span { color: #a9d9f7; font-weight: 700; }
.os-cover-quality > div h2 { margin-top: 20px; font-size: 31px; }
.os-cover-quality article b { display: block; color: #0b4f88; text-transform: uppercase; }
.os-cover-quality article strong { display: block; margin: 27px 0 12px; font-size: 29px; }
.os-cover-quality article p { color: #566571; }

.os-windows-intro { height: 235px; min-height: 0; overflow: hidden; display: grid; grid-template-columns: 63% 37%; border-bottom: 1px solid #d9e4ec; }
.os-windows-intro > * { min-height: 0; }
.os-windows-intro > div { padding: 38px 54px; }
.os-windows-intro h1 { font-size: 42px; }
.os-windows-intro p { margin-top: 14px; max-width: 740px; color: #697784; font-size: 16px; }
.os-windows-intro img { min-height: 0; object-position: center 54%; }
.os-windows-workspace { height: 485px; display: grid; grid-template-columns: 220px 1fr 305px; border-bottom: 1px solid #d9e4ec; }
.os-filter-rail { padding: 26px 22px 22px 42px; background: #eaf5fd; }
.os-filter-rail > span { display: block; margin: 0 0 9px; color: #0b4f88; font-size: 12px; font-weight: 700; text-transform: uppercase; }
.os-filter-rail > div { margin-bottom: 24px; display: grid; }
.os-filter-rail button { min-height: 38px; padding: 7px 10px; text-align: left; border: 1px solid #c5d8e5; background: #fff; margin-top: -1px; }
.os-filter-rail button[aria-pressed="true"] { background: #0b4f88; color: #fff; border-color: #0b4f88; }
.os-filter-rail p { color: #697784; font-size: 12px; }
.os-window-comparison { padding: 25px 28px; min-width: 0; }
.os-section-heading h2 { margin-top: 5px; }
.os-window-table, .os-profile-comparison table { width: 100%; margin-top: 22px; border-collapse: collapse; }
.os-window-table th, .os-window-table td, .os-profile-comparison th, .os-profile-comparison td { padding: 14px 10px; border-bottom: 1px solid #cfd9e0; text-align: left; font-size: 13px; }
.os-window-table th, .os-profile-comparison th { background: #eaf5fd; color: #0b4f88; font-size: 12px; text-transform: uppercase; }
.os-window-table button { height: 32px; padding: 0 12px; border: 1px solid #1d7fd1; color: #0b4f88; background: #fff; font-size: 12px; }
.os-window-specification { padding: 27px 28px; border-left: 1px solid #d9e4ec; }
.os-window-specification > span { color: #0b4f88; font-size: 12px; font-weight: 700; text-transform: uppercase; }
.os-window-specification h2 { margin-top: 18px; font-size: 30px; }
.os-window-specification > p { color: #697784; font-weight: 700; }
.os-window-specification dl { margin-top: 24px; }
.os-window-specification dl div { padding: 10px 0; display: flex; justify-content: space-between; border-bottom: 1px solid #d9e4ec; }
.os-window-specification dt { color: #697784; }
.os-window-specification dd { margin: 0; font-weight: 800; }
.os-window-specification strong { display: block; margin-top: 22px; color: #0b4f88; font-size: 25px; }
.os-window-specification button { width: 100%; height: 42px; margin-top: 14px; border: 0; background: #f7b500; font-weight: 800; }
.os-windows-performance { height: 284px; display: grid; grid-template-columns: 1.25fr repeat(4, 1fr); }
.os-windows-performance > * { padding: 35px 28px; border-right: 1px solid #d9e4ec; }
.os-windows-performance > div { padding-left: 54px; background: #171b21; color: #fff; }
.os-windows-performance > div span { color: #8ec9f2; }
.os-windows-performance > div h2 { margin-top: 14px; }
.os-windows-performance article b { display: block; color: #697784; }
.os-windows-performance article strong { display: block; margin: 25px 0 8px; color: #0b4f88; font-size: 25px; }
.os-windows-performance article p { color: #697784; font-size: 12px; }

.os-route-heading { height: 154px; padding: 27px 54px; display: grid; grid-template-columns: 1.5fr 1fr; align-items: end; border-bottom: 1px solid #d9e4ec; }
.os-route-heading h1 { font-size: 39px; }
.os-route-heading > p { padding-bottom: 5px; color: #697784; font-size: 15px; }
.os-calculator-workspace { height: 598px; display: grid; grid-template-columns: 1.35fr .82fr .72fr; border-bottom: 1px solid #d9e4ec; }
.os-calculator-controls { padding: 24px 30px 20px 54px; }
.os-calculator-controls fieldset { margin-bottom: 18px; }
.os-opening-buttons, .os-profile-buttons, .os-glazing-buttons { display: grid; grid-template-columns: repeat(3, 1fr); }
.os-opening-buttons button, .os-profile-buttons button, .os-glazing-buttons button { min-height: 44px; padding: 8px 10px; border: 1px solid #c7d4dc; background: #fff; margin-left: -1px; }
.os-profile-buttons button b, .os-glazing-buttons button b { display: block; color: #697784; font-size: 12px; }
.os-calculator-controls button[aria-pressed="true"] { position: relative; background: #0b4f88; border-color: #0b4f88; color: #fff; }
.os-calculator-controls button[aria-pressed="true"] b { color: #b6dff8; }
.os-dimensions { display: grid; grid-template-columns: 1fr 30px 1fr; align-items: end; }
.os-dimensions label { color: #697784; font-size: 12px; }
.os-dimensions input { display: block; width: 100%; height: 42px; margin-top: 5px; padding: 0 12px; border: 1px solid #aebfca; color: #171b21; font-size: 16px; font-variant-numeric: tabular-nums; }
.os-dimensions > span { padding-bottom: 10px; text-align: center; color: #697784; }
.os-install-check { min-height: 43px; padding: 11px 12px; display: flex; align-items: center; gap: 9px; background: #eaf5fd; }
.os-install-check input { width: 17px; height: 17px; accent-color: #1d7fd1; }
.os-install-check b { margin-left: auto; }
.os-calculator-photo { position: relative; min-width: 0; }
.os-calculator-photo figcaption { position: absolute; left: 0; right: 0; bottom: 0; padding: 16px 18px; background: #fff; border-top: 3px solid #1d7fd1; font-weight: 700; }
.os-calculator-summary { padding: 28px 27px; background: #171b21; color: #fff; }
.os-calculator-summary > span { color: #91cff6; font-size: 12px; font-weight: 700; text-transform: uppercase; }
.os-calculator-summary h2 { margin-top: 18px; color: #f7b500; font-size: 38px; font-variant-numeric: tabular-nums; }
.os-calculator-summary > p { margin-top: 3px; color: #c9d0d5; }
.os-calculator-summary dl { margin-top: 23px; }
.os-calculator-summary dl div { padding: 10px 0; display: flex; justify-content: space-between; gap: 12px; border-bottom: 1px solid #394149; }
.os-calculator-summary dt { color: #aeb8bf; }
.os-calculator-summary dd { margin: 0; text-align: right; font-weight: 700; }
.os-calculator-summary small { display: block; margin-top: 8px; color: #aeb8bf; text-align: center; }
.os-calculator-included { height: 252px; display: grid; grid-template-columns: 1.2fr repeat(4, 1fr); background: #eaf5fd; }
.os-calculator-included > * { padding: 35px 27px; border-right: 1px solid #c8dae6; }
.os-calculator-included > div { padding-left: 54px; background: #0b4f88; color: #fff; }
.os-calculator-included > div span { color: #addbf7; font-weight: 700; }
.os-calculator-included > div h2 { margin-top: 14px; }
.os-calculator-included article b { display: block; min-height: 40px; color: #0b4f88; }
.os-calculator-included article p { color: #697784; font-size: 12px; }

.os-profiles-hero { height: 315px; min-height: 0; overflow: hidden; display: grid; grid-template-columns: 55% 45%; border-bottom: 1px solid #d9e4ec; }
.os-profiles-hero > * { min-height: 0; }
.os-profiles-hero > div { padding: 44px 54px; }
.os-profiles-hero h1 { font-size: 42px; }
.os-profiles-hero p { margin-top: 16px; max-width: 760px; color: #697784; font-size: 16px; }
.os-profile-models { margin-top: 25px; display: flex; }
.os-profile-models button { width: 145px; height: 42px; border: 1px solid #b9c9d4; background: #fff; margin-left: -1px; }
.os-profile-models button[aria-pressed="true"] { background: #f7b500; border-color: #f7b500; font-weight: 800; position: relative; }
.os-profiles-hero img { min-height: 0; object-position: center 58%; }
.os-profile-comparison { height: 423px; padding: 27px 54px; }
.os-profile-comparison table { margin-top: 16px; }
.os-profile-comparison th:not(:first-child), .os-profile-comparison td:not(:first-child) { text-align: center; font-variant-numeric: tabular-nums; }
.os-profile-comparison td:first-child { font-weight: 700; }
.os-profiles-passport { height: 266px; display: grid; grid-template-columns: 1.25fr 2.5fr 220px; align-items: center; background: #171b21; color: #fff; }
.os-profiles-passport > div { padding: 34px 24px 34px 54px; }
.os-profiles-passport > div > span { color: #8fcef5; font-size: 12px; font-weight: 700; text-transform: uppercase; }
.os-profiles-passport h2 { margin-top: 12px; font-size: 34px; }
.os-profiles-passport p { margin-top: 8px; color: #b8c2c9; }
.os-profiles-passport dl { height: 100%; display: grid; grid-template-columns: repeat(5, 1fr); }
.os-profiles-passport dl div { padding: 66px 16px 20px; border-left: 1px solid #394149; }
.os-profiles-passport dt { min-height: 36px; color: #aeb8bf; }
.os-profiles-passport dd { margin: 12px 0 0; color: #f7b500; font-size: 17px; font-weight: 800; }
.os-profiles-passport > button { width: 180px; height: 48px; border: 0; background: #f7b500; font-weight: 800; }

.os-installation-workspace { height: 538px; min-height: 0; overflow: hidden; display: grid; grid-template-columns: 330px 1fr 350px; border-bottom: 1px solid #d9e4ec; }
.os-installation-workspace > * { min-height: 0; overflow: hidden; }
.os-installation-sequence { padding: 25px 22px 20px 42px; background: #eaf5fd; }
.os-installation-sequence > span, .os-installation-visit > span { color: #0b4f88; font-size: 12px; font-weight: 700; text-transform: uppercase; }
.os-installation-sequence ol { margin: 18px 0 0; padding: 0; list-style: none; }
.os-installation-sequence li { padding: 10px 0; display: grid; grid-template-columns: 38px 1fr; border-bottom: 1px solid #c5d9e6; }
.os-installation-sequence li > b { color: #1d7fd1; }
.os-installation-sequence strong { display: block; }
.os-installation-sequence p { margin-top: 2px; color: #697784; font-size: 12px; }
.os-installation-photo { position: relative; min-width: 0; min-height: 0; }
.os-installation-photo figcaption { position: absolute; left: 0; bottom: 0; padding: 16px 20px; background: #fff; border-top: 4px solid #1d7fd1; }
.os-installation-photo figcaption b, .os-installation-photo figcaption span { display: block; }
.os-installation-photo figcaption span { margin-top: 4px; color: #697784; }
.os-installation-visit { padding: 27px 26px; }
.os-date-buttons { margin-top: 17px; display: grid; grid-template-columns: repeat(3, 1fr); }
.os-date-buttons button { height: 65px; border: 1px solid #c4d1da; background: #fff; margin-left: -1px; font-size: 12px; }
.os-date-buttons b { display: block; font-size: 22px; }
.os-time-buttons { margin-top: 12px; display: grid; }
.os-time-buttons button { height: 35px; border: 1px solid #c4d1da; background: #fff; margin-top: -1px; }
.os-installation-visit button[aria-pressed="true"] { background: #0b4f88; border-color: #0b4f88; color: #fff; position: relative; }
.os-installation-visit h2 { margin-top: 18px; font-size: 23px; }
.os-installation-visit dl { margin-top: 13px; }
.os-installation-visit dl div { padding: 7px 0; display: flex; justify-content: space-between; border-bottom: 1px solid #d9e4ec; }
.os-installation-visit dt { color: #697784; }
.os-installation-visit dd { margin: 0; text-align: right; font-weight: 700; }
.os-installation-visit > button { width: 100%; height: 42px; margin-top: 16px; border: 0; background: #f7b500; font-weight: 800; }
.os-installation-handover { height: 312px; display: grid; grid-template-columns: 58% 42%; background: #171b21; color: #fff; }
.os-installation-handover > div { padding: 34px 54px; }
.os-installation-handover > div > span { color: #8fcef5; font-weight: 700; }
.os-installation-handover h2 { margin-top: 10px; }
.os-installation-handover ul { margin: 24px 0 0; padding: 0; display: grid; grid-template-columns: 1fr 1fr; gap: 13px 28px; list-style: none; }
.os-installation-handover li { padding: 8px 0 8px 17px; border-left: 3px solid #f7b500; }
.os-installation-handover figure { position: relative; }
.os-installation-handover figcaption { position: absolute; left: 0; right: 0; bottom: 0; padding: 15px 18px; background: #0b4f88; color: #fff; font-weight: 700; }
"""


_COVER_SCRIPT = r"""
(() => {
  const options = {
    one: {title: "Одностворчатое окно", size: "700 × 1400 мм", price: "от 17 400 ₽", term: "5 рабочих дней"},
    two: {title: "Двухстворчатое окно", size: "1450 × 1400 мм", price: "от 23 700 ₽", term: "6 рабочих дней"},
    three: {title: "Трёхстворчатое окно", size: "2100 × 1400 мм", price: "от 31 900 ₽", term: "7 рабочих дней"},
    balcony: {title: "Балконный блок", size: "2050 × 2150 мм", price: "от 42 600 ₽", term: "8 рабочих дней"}
  };
  document.querySelectorAll('[data-selectable="cover-sash"]').forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll('[data-selectable="cover-sash"]').forEach((item) => item.setAttribute("aria-pressed", String(item === button)));
      const option = options[button.dataset.value];
      document.querySelector("[data-cover-title]").textContent = option.title;
      document.querySelector("[data-cover-size]").textContent = option.size;
      document.querySelector("[data-cover-price]").textContent = option.price;
      document.querySelector("[data-cover-term]").textContent = option.term;
    });
  });
})();
"""


_WINDOWS_SCRIPT = r"""
(() => {
  const rooms = {
    kitchen: {name: "Кухня", depth: "60 мм", noise: "34 дБ", price: "от 21 900 ₽", term: "6 дней"},
    living: {name: "Гостиная", depth: "70 мм", noise: "40 дБ", price: "от 26 400 ₽", term: "7 дней"},
    balcony: {name: "Балкон", depth: "70 мм", noise: "40 дБ", price: "от 28 600 ₽", term: "7 дней"}
  };
  const openings = {fixed: "Глухое", swing: "Поворотное", tilt: "Поворотно-откидное"};
  let room = "kitchen";
  let opening = "swing";
  const update = () => {
    const item = rooms[room];
    document.querySelector("[data-window-room]").textContent = item.name;
    document.querySelector("[data-window-opening]").textContent = openings[opening];
    document.querySelector("[data-window-depth]").textContent = item.depth;
    document.querySelector("[data-window-noise]").textContent = item.noise;
    document.querySelector("[data-window-term]").textContent = item.term;
    document.querySelector("[data-window-price]").textContent = item.price;
  };
  document.querySelectorAll('[data-selectable="window-room"]').forEach((button) => button.addEventListener("click", () => {
    document.querySelectorAll('[data-selectable="window-room"]').forEach((item) => item.setAttribute("aria-pressed", String(item === button)));
    room = button.dataset.value;
    update();
  }));
  document.querySelectorAll('[data-selectable="window-opening"]').forEach((button) => button.addEventListener("click", () => {
    document.querySelectorAll('[data-selectable="window-opening"]').forEach((item) => item.setAttribute("aria-pressed", String(item === button)));
    opening = button.dataset.value;
    update();
  }));
})();
"""


_CALCULATOR_SCRIPT = r"""
(() => {
  let opening = {factor: 1.35, days: 1};
  let profile = {name: "Sfera 70", chambers: "5", rate: 11000, heat: "0,78", days: 7};
  let glazing = {name: "40 мм", noise: "40", fee: 3000, days: 1};
  const grouped = (value) => Math.round(value).toLocaleString("ru-RU").replace(/\u00a0/g, " ");
  const update = () => {
    const width = Math.max(500, Math.min(3200, Number(document.querySelector("[data-calculator-width]").value) || 500));
    const height = Math.max(500, Math.min(2600, Number(document.querySelector("[data-calculator-height]").value) || 500));
    const installation = document.querySelector("[data-calculator-installation]").checked;
    const area = width * height / 1000000;
    const total = Math.round((area * profile.rate * opening.factor + glazing.fee + (installation ? 8000 : 0)) / 100) * 100;
    const days = profile.days + opening.days + glazing.days;
    document.querySelector("[data-calculator-total]").textContent = `${grouped(total)} ₽`;
    document.querySelector("[data-calculator-term]").textContent = `${days} рабочих дней`;
    document.querySelector("[data-calculator-profile]").textContent = `${profile.name} · ${profile.chambers} камер`;
    document.querySelector("[data-calculator-glazing]").textContent = `${glazing.name} · ${glazing.noise} дБ`;
    document.querySelector("[data-calculator-heat]").textContent = `${profile.heat} м²·°C/Вт`;
    document.querySelector("[data-calculator-size]").textContent = `${width} × ${height} мм`;
    document.querySelector("[data-included-plates]").textContent = `Анкерные пластины · ${Math.round(width / 120)} шт.`;
    document.querySelector("[data-included-foam]").textContent = `Монтажная пена · ${Math.ceil(area / 1.2)} баллона`;
    document.querySelector("[data-included-sill]").textContent = `Подоконник · ${width} мм`;
  };
  document.querySelectorAll('[data-selectable="calculator-opening"]').forEach((button) => button.addEventListener("click", () => {
    document.querySelectorAll('[data-selectable="calculator-opening"]').forEach((item) => item.setAttribute("aria-pressed", String(item === button)));
    opening = {factor: Number(button.dataset.factor), days: Number(button.dataset.days)};
    update();
  }));
  document.querySelectorAll('[data-selectable="calculator-profile"]').forEach((button) => button.addEventListener("click", () => {
    document.querySelectorAll('[data-selectable="calculator-profile"]').forEach((item) => item.setAttribute("aria-pressed", String(item === button)));
    profile = {name: button.dataset.name, chambers: button.dataset.chambers, rate: Number(button.dataset.rate), heat: button.dataset.heat, days: Number(button.dataset.days)};
    update();
  }));
  document.querySelectorAll('[data-selectable="calculator-glazing"]').forEach((button) => button.addEventListener("click", () => {
    document.querySelectorAll('[data-selectable="calculator-glazing"]').forEach((item) => item.setAttribute("aria-pressed", String(item === button)));
    glazing = {name: button.dataset.name, noise: button.dataset.noise, fee: Number(button.dataset.fee), days: Number(button.dataset.days)};
    update();
  }));
  document.querySelectorAll("[data-calculator-width], [data-calculator-height], [data-calculator-installation]").forEach((control) => control.addEventListener("input", update));
})();
"""


_PROFILES_SCRIPT = r"""
(() => {
  const profiles = {
    "60": {name: "Sfera 60", chambers: "3 камеры", glazing: "Стеклопакет до 32 мм", heat: "0,64 м²·°C/Вт", noise: "34 дБ", steel: "Сталь 1,2 мм", use: "Для дач, нежилых балконов и сезонных помещений."},
    "70": {name: "Sfera 70", chambers: "5 камер", glazing: "Стеклопакет до 40 мм", heat: "0,78 м²·°C/Вт", noise: "40 дБ", steel: "Сталь 1,5 мм", use: "Для городских квартир и отапливаемых лоджий."},
    "82": {name: "Sfera 82", chambers: "7 камер", glazing: "Стеклопакет до 52 мм", heat: "0,92 м²·°C/Вт", noise: "46 дБ", steel: "Сталь 1,5 мм", use: "Для тихих спален, загородных домов и панорамного остекления."}
  };
  document.querySelectorAll('[data-selectable="profile-model"]').forEach((button) => button.addEventListener("click", () => {
    document.querySelectorAll('[data-selectable="profile-model"]').forEach((item) => item.setAttribute("aria-pressed", String(item === button)));
    const item = profiles[button.dataset.value];
    document.querySelector("[data-passport-name]").textContent = item.name;
    document.querySelector("[data-passport-use]").textContent = item.use;
    document.querySelector("[data-passport-chambers]").textContent = item.chambers;
    document.querySelector("[data-passport-glazing]").textContent = item.glazing;
    document.querySelector("[data-passport-heat]").textContent = item.heat;
    document.querySelector("[data-passport-noise]").textContent = item.noise;
    document.querySelector("[data-passport-steel]").textContent = item.steel;
  }));
})();
"""


_INSTALLATION_SCRIPT = r"""
(() => {
  let date = "27 августа";
  let time = "09:00–12:00";
  const update = () => {
    document.querySelector("[data-visit-slot]").textContent = `${date} · ${time}`;
    document.querySelector("[data-visit-duration]").textContent = time === "15:00–18:00" ? "5–6 часов" : "4–5 часов";
  };
  document.querySelectorAll('[data-selectable="installation-date"]').forEach((button) => button.addEventListener("click", () => {
    document.querySelectorAll('[data-selectable="installation-date"]').forEach((item) => item.setAttribute("aria-pressed", String(item === button)));
    date = button.dataset.value;
    update();
  }));
  document.querySelectorAll('[data-selectable="installation-time"]').forEach((button) => button.addEventListener("click", () => {
    document.querySelectorAll('[data-selectable="installation-time"]').forEach((item) => item.setAttribute("aria-pressed", String(item === button)));
    time = button.dataset.value;
    update();
  }));
})();
"""


_BODY_RENDERERS = {
    "cover": _cover,
    "windows": _windows,
    "calculator": _calculator,
    "profiles": _profiles,
    "installation": _installation,
}

_ROUTE_SCRIPTS = {
    "cover": _COVER_SCRIPT,
    "windows": _WINDOWS_SCRIPT,
    "calculator": _CALCULATOR_SCRIPT,
    "profiles": _PROFILES_SCRIPT,
    "installation": _INSTALLATION_SCRIPT,
}


def render(
    project: ProjectSpec,
    shot: ShotSpec,
    assets: Mapping[str, str],
) -> RenderedPage:
    """Render one Okna Sfera route with only its route-owned bitmaps."""
    if project.slug != "okna-sfera":
        raise KeyError(f"okna-sfera renderer does not support {project.slug}")
    try:
        body_renderer = _BODY_RENDERERS[shot.key]
    except KeyError as exc:
        raise ValueError(f"okna-sfera unknown route: {shot.key}") from exc

    owned = _owned_assets(shot.key, assets)
    html = (
        '<div class="os-page" data-site="okna-sfera" data-project="okna-sfera" '
        f'data-route="{escape_html(shot.key)}">'
        f"{_header(shot.key)}{body_renderer(owned)}</div>"
    )
    return RenderedPage(html=html, css=_CSS, scripts=_ROUTE_SCRIPTS[shot.key])
