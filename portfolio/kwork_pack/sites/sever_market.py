"""Dedicated outdoor retail renderer for Sever Market."""

from collections.abc import Mapping

from ..components import escape_html
from ..icons import icon
from ..models import ProjectSpec, ShotSpec
from .runtime import RenderedPage


_ROUTE_ASSETS = {
    "cover": ("mountain_tent",),
    "catalog": ("hiking_backpack",),
    "tents": ("gear_closeup",),
    "cart": ("campfire_scene",),
    "delivery": ("guide_portrait", "winter_route"),
}


def _owned_assets(route: str, assets: Mapping[str, str]) -> dict[str, str]:
    """Resolve and escape only the bitmap sources assigned to one route."""
    resolved: dict[str, str] = {}
    for key in _ROUTE_ASSETS[route]:
        try:
            resolved[key] = escape_html(assets[key])
        except KeyError as exc:
            raise KeyError(f"sever-market {route} missing asset {key}") from exc
    return resolved


def _header(active: str) -> str:
    categories = (
        ("catalog", "Снаряжение"),
        ("tents", "Палатки"),
        ("backpacks", "Рюкзаки"),
        ("sleeping", "Спальники"),
        ("kitchen", "Горелки и кухня"),
        ("clothing", "Одежда"),
        ("delivery", "Доставка"),
    )
    navigation = "".join(
        f'<a href="#" class="{"is-active" if key == active else ""}">{label}</a>'
        for key, label in categories
    )
    cart_count = "1" if active == "cart" else "0"
    return (
        '<header class="sm-header">'
        '<div class="sm-utility">'
        '<b>Точки выдачи: Москва · Санкт-Петербург · Екатеринбург</b>'
        '<nav aria-label="Сервис магазина"><a href="#">Магазины</a>'
        '<a href="#">Клуб маршрутов</a><a href="#">Гарантия</a>'
        '<a href="#">8 800 550-41-28</a></nav></div>'
        '<div class="sm-shopbar">'
        '<a href="#" class="sm-brand" aria-label="Северный маршрут">'
        '<i aria-hidden="true"><span></span><span></span></i>'
        '<span><strong>СЕВЕРНЫЙ</strong><b>МАРШРУТ</b></span></a>'
        '<button type="button" class="sm-catalog-trigger">'
        f'{icon("filter", size=18)}<span>Каталог товаров</span></button>'
        '<div class="sm-search" role="search">'
        '<input type="search" aria-label="Поиск по каталогу" '
        'placeholder="Товар, категория или артикул">'
        '<button type="button" aria-label="Найти">'
        f'{icon("arrow-right", size=18)}</button></div>'
        f'<div class="sm-location">{icon("map-pin", size=19)}'
        '<span><b>Москва</b><small>доставка завтра</small></span></div>'
        f'<nav class="sm-category-nav" aria-label="Категории">{navigation}</nav>'
        '<button type="button" class="sm-cart-link" aria-label="Корзина">'
        f'{icon("shopping-cart", size=21)}<span>Корзина</span>'
        f'<b data-cart-count>{cart_count}</b></button>'
        '</div></header>'
    )


def _cover(assets: Mapping[str, str]) -> str:
    source = assets["mountain_tent"]
    return (
        '<main class="sm-route sm-cover">'
        '<section class="sm-cover-main">'
        '<div class="sm-cover-copy">'
        '<p class="sm-breadcrumb">Главная / Подбор комплекта</p>'
        '<h1>Снаряжение для маршрута, а не для витрины</h1>'
        '<p class="sm-lead">Собрали совместимый комплект для трёх дней '
        'в горах: без лишнего веса, с проверенным запасом по погоде.</p>'
        '<div class="sm-control-block"><b>Сезон маршрута</b>'
        '<div class="sm-segment" role="group" aria-label="Сезон маршрута">'
        '<button type="button" data-selectable="season" data-value="summer" aria-pressed="false">Лето</button>'
        '<button type="button" data-selectable="season" data-value="autumn" aria-pressed="true">Осень</button>'
        '<button type="button" data-selectable="season" data-value="winter" aria-pressed="false">Зима</button>'
        '</div></div>'
        '<dl class="sm-route-facts"><div><dt>Длительность</dt><dd data-kit-duration>3 дня</dd></div>'
        '<div><dt>Температура</dt><dd data-kit-temperature>−4…+12 °C</dd></div>'
        '<div><dt>Вес</dt><dd data-kit-weight>8,6 кг</dd></div></dl>'
        '</div>'
        '<figure class="sm-cover-photo"><img src="'
        f'{source}" alt="Палатка на северном горном маршруте">'
        '<figcaption><b>Проверено на Кольском</b><span>ветер 16 м/с · дождь 11 часов</span></figcaption></figure>'
        '<aside class="sm-kit-sheet"><span>ГОТОВЫЙ НАБОР · 7 ПОЗИЦИЙ</span>'
        '<h2 data-kit-name>Осенний маршрут</h2>'
        '<ul data-kit-items><li>Палатка Nord 2 Pro</li><li>Спальник −7 °C</li>'
        '<li>Рюкзак 65 л</li><li>Коврик R-value 4.2</li></ul>'
        '<div class="sm-kit-stock"><i></i><b data-kit-stock>12 комплектов в наличии</b>'
        '<span>Москва · отгрузка сегодня</span></div>'
        '<div class="sm-kit-total"><span>Цена комплекта</span>'
        '<strong data-kit-price>39 800 ₽</strong><small>выгода 4 260 ₽</small></div>'
        '<button type="button" class="sm-primary">Добавить комплект '
        f'{icon("shopping-cart", size=18)}</button>'
        '<p>Можно заменить любую позицию до оплаты.</p></aside>'
        '</section>'
        '<section class="sm-cover-lower" data-lower-band="true">'
        '<header><div><span>КОМПЛЕКТ МАРШРУТА</span><h2>Комплект маршрута</h2></div>'
        '<p>Сравнили вес, температурный режим и совместимость упаковки.</p></header>'
        '<div class="sm-assortment">'
        '<article><span>01</span><div><b>Укрытие</b><strong>2,7 кг</strong>'
        '<p>Палатка, футпринт, 12 штормовых оттяжек</p></div></article>'
        '<article><span>02</span><div><b>Сон</b><strong>2,1 кг</strong>'
        '<p>Спальник, коврик и гермомешок</p></div></article>'
        '<article><span>03</span><div><b>Кухня</b><strong>1,3 кг</strong>'
        '<p>Горелка, газ, котелок и ветрозащита</p></div></article>'
        '<article><span>04</span><div><b>Переноска</b><strong>2,5 кг</strong>'
        '<p>Рюкзак 65 л и чехол от дождя</p></div></article>'
        '</div><footer><b>Бесплатная примерка рюкзака</b><span>Возврат 30 дней</span>'
        '<span>Ремонт снаряжения</span><span>Поддержка инструктора</span>'
        '<strong>Собрано без дублирующих вещей</strong></footer>'
        '</section></main>'
    )


def _catalog(assets: Mapping[str, str]) -> str:
    source = assets["hiking_backpack"]
    return (
        '<main class="sm-route sm-catalog">'
        '<section class="sm-catalog-main">'
        '<header class="sm-route-head"><div><p>Каталог / Туризм и кемпинг</p>'
        '<h1>Туристическое снаряжение</h1></div>'
        '<div class="sm-result-tools"><b data-catalog-count>126 товаров</b>'
        '<label>Сортировка<select aria-label="Сортировка каталога"><option>По условиям маршрута</option>'
        '<option>Сначала легче</option><option>Сначала дешевле</option></select></label></div></header>'
        '<div class="sm-catalog-workspace">'
        '<aside class="sm-filter-rail"><h2>Условия похода</h2>'
        '<fieldset><legend>Сезон</legend>'
        '<label><input type="checkbox" checked> Лето <span>64</span></label>'
        '<label><input type="checkbox"> Межсезонье <span>52</span></label>'
        '<label><input type="checkbox" data-catalog-filter="winter"> Зима <span>38</span></label></fieldset>'
        '<fieldset><legend>Вес снаряжения</legend>'
        '<label><input type="checkbox"> Ультралёгкое <span>21</span></label>'
        '<label><input type="checkbox" checked> До 3 кг <span>73</span></label></fieldset>'
        '<fieldset><legend>Категория</legend><label><input type="checkbox" checked> Палатки</label>'
        '<label><input type="checkbox" checked> Рюкзаки</label><label><input type="checkbox"> Спальные системы</label></fieldset>'
        '<button type="button">Сбросить параметры</button></aside>'
        '<section class="sm-product-area"><div class="sm-catalog-summary" data-catalog-summary>'
        '<b>Подбор для летнего и межсезонного похода</b><span>Вес позиции до 3 кг · наличие в 7 городах</span></div>'
        '<div class="sm-product-matrix">'
        '<article class="sm-product-feature"><figure><img src="'
        f'{source}" alt="Походный рюкзак на каменистом маршруте"></figure>'
        '<div><span>ВЫБОР ЭКСПЕРТА</span><h3>Рюкзак Boreal 65</h3><p>65 л · 1,82 кг · спина 46–54 см</p>'
        '<div class="sm-rating"><b>4,9</b><span>★★★★★ · 48 отзывов</span></div>'
        '<strong>18 990 ₽</strong><small data-catalog-feature-stock>В наличии · 14 шт.</small></div></article>'
        '<article><span>ПАЛАТКИ</span><h3>Nord 2 Pro</h3><p>2 места · 2,7 кг · дуги DAC</p>'
        '<dl><div><dt>Ветер</dt><dd>до 20 м/с</dd></div><div><dt>Москва</dt><dd>8 шт.</dd></div></dl><strong>17 990 ₽</strong></article>'
        '<article><span>СПАЛЬНЫЕ СИСТЕМЫ</span><h3>Arctic Down −12</h3><p>Пух 700 FP · 1,28 кг</p>'
        '<dl><div><dt>Комфорт</dt><dd>−7 °C</dd></div><div><dt>СПб</dt><dd>11 шт.</dd></div></dl><strong>16 400 ₽</strong></article>'
        '<article><span>КУХНЯ</span><h3>Flame Solo</h3><p>2 800 Вт · пьезоподжиг · 91 г</p>'
        '<dl><div><dt>Кипячение</dt><dd>3:20</dd></div><div><dt>Казань</dt><dd>19 шт.</dd></div></dl><strong>5 490 ₽</strong></article>'
        '</div></section>'
        '<aside class="sm-stock-rail"><h2>Наличие по городам</h2>'
        '<dl><div><dt>Москва</dt><dd data-city-stock>52</dd></div><div><dt>Санкт-Петербург</dt><dd>41</dd></div>'
        '<div><dt>Екатеринбург</dt><dd>28</dd></div><div><dt>Казань</dt><dd>24</dd></div></dl>'
        '<p><b>Самовывоз сегодня</b> из 5 магазинов после подтверждения резерва.</p>'
        '<button type="button">Проверить свой город</button></aside>'
        '</div></section>'
        '<section class="sm-catalog-lower" data-lower-band="true">'
        '<header><div><span>ЭКСПЕРТНЫЙ ФИЛЬТР</span><h2>Подбор по условиям</h2></div>'
        '<p>Не по бренду, а по погоде, рельефу и допустимому весу.</p></header>'
        '<div class="sm-expert-strip"><article><b>Кольский полуостров</b><span>ветер · камень · влажность</span><strong>23 позиции</strong></article>'
        '<article><b>Алтай в сентябре</b><span>ночью до −6 °C · 6 дней</span><strong>31 позиция</strong></article>'
        '<article><b>Ладожские шхеры</b><span>вода · дождь · стоянки</span><strong>19 позиций</strong></article>'
        '<aside><b>Не уверены в совместимости?</b><p>Эксперт проверит комплект по весу и температуре.</p><button type="button">Отправить список</button></aside></div>'
        '<footer><span>47 товаров доступны сегодня</span><span>22 модели с ремонтом в РФ</span>'
        '<span>Все веса проверены на складе</span><b>Данные обновлены 24 августа, 09:40</b></footer>'
        '</section></main>'
    )


def _tents(assets: Mapping[str, str]) -> str:
    source = assets["gear_closeup"]
    return (
        '<main class="sm-route sm-tents">'
        '<section class="sm-tents-main">'
        '<header class="sm-route-head"><div><p>Каталог / Палатки / Экспедиционные</p>'
        '<h1>Палатки для ветра и дождя</h1></div>'
        '<div class="sm-cart-status">В сравнении <b>3</b><span>·</span> Корзина синхронизирована</div></header>'
        '<div class="sm-tent-workspace">'
        '<aside class="sm-tent-controls"><h2>Параметры группы</h2><b>Вместимость</b>'
        '<div class="sm-segment sm-capacity" role="group" aria-label="Вместимость палатки">'
        '<button type="button" data-selectable="tent-capacity" data-value="2" aria-pressed="true">2</button>'
        '<button type="button" data-selectable="tent-capacity" data-value="3" aria-pressed="false">3</button>'
        '<button type="button" data-selectable="tent-capacity" data-value="4" aria-pressed="false">4</button></div>'
        '<fieldset><legend>Погодный режим</legend><label><input type="checkbox" checked> Ветер от 15 м/с</label>'
        '<label><input type="checkbox" checked> Длительный дождь</label><label><input type="checkbox"> Снеговая юбка</label></fieldset>'
        '<figure><img src="'
        f'{source}" alt="Крупный план туристического снаряжения и фурнитуры">'
        '<figcaption>Швы проклеены лентой 20 мм</figcaption></figure></aside>'
        '<section class="sm-tent-comparison"><div class="sm-table-heading"><div><span>3 МОДЕЛИ</span>'
        '<h2>Сравнение палаток</h2></div><b data-tent-result>2 места · ветер до 22 м/с</b></div>'
        '<table><thead><tr><th>Модель</th><th>Мест</th><th>Вес</th><th>Тент</th><th>Ветер</th><th>Цена</th></tr></thead>'
        '<tbody><tr class="is-selected"><td><b>Nord Ridge 2</b><span>4 сезона</span></td><td data-tent-capacity-cell>2</td><td>2,86 кг</td><td>5 000 мм</td><td>22 м/с</td><td>17 990 ₽</td></tr>'
        '<tr><td><b>Boreal Storm</b><span>3 сезона</span></td><td>3</td><td>3,24 кг</td><td>4 000 мм</td><td>18 м/с</td><td>19 400 ₽</td></tr>'
        '<tr><td><b>Taiga Base</b><span>семейная</span></td><td>4</td><td>4,18 кг</td><td>6 000 мм</td><td>20 м/с</td><td>23 900 ₽</td></tr></tbody></table>'
        '<div class="sm-comparison-note"><b>Методика:</b><span>30 минут бокового ветра</span>'
        '<span>имитация дождя 60 л/м²</span><span>сборка в перчатках</span></div></section>'
        '<aside class="sm-selected-spec"><span>ВЫБРАНА</span><h2 data-selected-tent>Nord Ridge 2</h2>'
        '<dl><div><dt>Вместимость</dt><dd data-selected-capacity>2 человека</dd></div>'
        '<div><dt>Тамбур</dt><dd>0,9 м²</dd></div><div><dt>Дуги</dt><dd>DAC 9,5 мм</dd></div>'
        '<div><dt>Ремкомплект</dt><dd>в комплекте</dd></div></dl>'
        '<div class="sm-selected-stock"><i></i><b>8 шт. в Москве</b><span>резерв на 24 часа</span></div>'
        '<strong data-selected-tent-price>17 990 ₽</strong>'
        '<button type="button" class="sm-primary" data-add-tent>В корзину '
        f'{icon("shopping-cart", size=18)}</button><p data-tent-cart-state>Самовывоз сегодня с 16:00</p></aside>'
        '</div></section>'
        '<section class="sm-tents-lower" data-lower-band="true">'
        '<header><div><span>ПОЛЕВОЙ СПРАВОЧНИК</span><h2>Как палатка держит непогоду</h2></div>'
        '<p>Четыре узла, которые проверяем до включения модели в экспедиционный каталог.</p></header>'
        '<div class="sm-field-guide"><article><span>01</span><b>Геометрия дуг</b><p>Три пересечения распределяют боковую нагрузку.</p><strong>22 м/с</strong></article>'
        '<article><span>02</span><b>Шов дна</b><p>Поднят на 12 см выше мокрого грунта.</p><strong>10 000 мм</strong></article>'
        '<article><span>03</span><b>Вентиляция</b><p>Два верхних окна работают в дождь.</p><strong>2 канала</strong></article>'
        '<article><span>04</span><b>Полевой ремонт</b><p>Секция дуги и заплаты входят в набор.</p><strong>14 минут</strong></article></div>'
        '<footer><b>Испытание партии NR2-0826</b><span>дата: 18.08.2026</span><span>инструктор: А. Серов</span>'
        '<span>протокол доступен с товаром</span><strong>Результат: допущена к маршрутам</strong></footer>'
        '</section></main>'
    )


def _cart(assets: Mapping[str, str]) -> str:
    source = assets["campfire_scene"]
    return (
        '<main class="sm-route sm-cart">'
        '<section class="sm-cart-main">'
        '<header class="sm-route-head"><div><p>Главная / Корзина</p><h1>Корзина</h1></div>'
        '<div class="sm-reserve-clock">Резерв действует <b>23:41</b><span>до 19:00 сегодня</span></div></header>'
        '<div class="sm-cart-workspace"><section class="sm-cart-table">'
        '<div class="sm-cart-table-head"><span>ТОВАР</span><span>НАЛИЧИЕ</span><span>КОЛИЧЕСТВО</span><span>СУММА</span></div>'
        '<article><div><span>NORD / 2P / GREEN</span><h2>Палатка Nord Ridge 2</h2>'
        '<p>4 сезона · зелёная · ремкомплект включён</p></div>'
        '<div class="sm-stock-cell"><i></i><b>Москва · 8 шт.</b><span>зарезервировано на складе</span></div>'
        '<label class="sm-quantity">Количество<input type="number" min="1" max="4" value="1" data-cart-quantity></label>'
        '<strong data-cart-line-total>17 990 ₽</strong></article>'
        '<div class="sm-cart-support"><div><b>Нужна совместимость?</b><span>Проверим палатку, спальник и коврик перед оплатой.</span></div>'
        '<button type="button">Проверить комплект</button></div>'
        '<div class="sm-promo"><label>Промокод<input type="text" value="SEVER1500" aria-label="Промокод"></label>'
        '<button type="button">Применён</button><span>Скидка на комплект от двух единиц</span></div></section>'
        '<aside class="sm-order-sheet"><span>ЗАКАЗ · 1 ПОЗИЦИЯ</span><h2>Резерв товара</h2>'
        '<div class="sm-delivery-choice"><b>Получение</b>'
        '<button type="button" data-selectable="delivery-mode" data-value="pickup" aria-pressed="true">Самовывоз <span>0 ₽</span></button>'
        '<button type="button" data-selectable="delivery-mode" data-value="courier" aria-pressed="false">Курьер <span>1 300 ₽</span></button></div>'
        '<dl class="sm-order-parts"><div><dt>Товары</dt><dd data-cart-part>17 990 ₽</dd></div>'
        '<div><dt>Скидка комплекта</dt><dd data-cart-part>0 ₽</dd></div>'
        '<div><dt>Доставка</dt><dd data-cart-part>0 ₽</dd></div></dl>'
        '<div class="sm-order-total"><span>Итого</span><strong data-cart-total>17 990 ₽</strong></div>'
        '<button type="button" class="sm-primary">Перейти к оформлению '
        f'{icon("arrow-right", size=18)}</button><p>Оплата после подтверждения резерва.</p></aside></div>'
        '</section>'
        '<section class="sm-cart-lower" data-lower-band="true">'
        '<figure><img src="'
        f'{source}" alt="Снаряжение у костра после дневного перехода">'
        '<figcaption><b>Проверка перед выдачей</b><span>Комплектность · фурнитура · упаковка</span></figcaption></figure>'
        '<div class="sm-reserve-ledger"><header><span>СКЛАД МОСКВА-СЕВЕР</span><h2>Что происходит с заказом</h2></header>'
        '<ol><li><b>09:42</b><div><strong>Товар найден</strong><span>ячейка T-14 · упаковка без повреждений</span></div></li>'
        '<li><b>09:44</b><div><strong>Резерв подтверждён</strong><span>срок хранения до 19:00</span></div></li>'
        '<li><b>следующий шаг</b><div><strong>Проверка комплектности</strong><span>после выбора получения</span></div></li></ol></div>'
        '<aside><b>Возьмите на маршрут</b><p>Футпринт защищает дно палатки и экономит время сушки.</p>'
        '<div><span>Вес</span><strong>340 г</strong></div><div><span>К заказу</span><strong>2 190 ₽</strong></div>'
        '<button type="button">Добавить футпринт</button></aside>'
        '</section></main>'
    )


def _delivery(assets: Mapping[str, str]) -> str:
    guide = assets["guide_portrait"]
    route = assets["winter_route"]
    return (
        '<main class="sm-route sm-delivery">'
        '<section class="sm-delivery-main">'
        '<header class="sm-route-head"><div><p>Сервис / Доставка</p><h1>Доставка снаряжения</h1></div>'
        '<div class="sm-delivery-promise"><b>87 регионов</b><span>контроль упаковки и даты прибытия</span></div></header>'
        '<div class="sm-delivery-workspace"><section class="sm-delivery-controls"><span>РАСЧЁТ МАРШРУТА</span>'
        '<h2>Город и способ</h2><label>Город получения<select data-delivery-city>'
        '<option value="moscow">Москва</option><option value="kazan">Казань</option>'
        '<option value="ekaterinburg">Екатеринбург</option></select></label>'
        '<div class="sm-carrier-controls"><b>Перевозчик</b>'
        '<button type="button" data-selectable="carrier" data-value="standard" aria-pressed="true">Север Стандарт <span>2–4 дня</span></button>'
        '<button type="button" data-selectable="carrier" data-value="express" aria-pressed="false">Экспресс <span>1–2 дня</span></button></div>'
        '<label>Пункт выдачи<select data-pickup-point><option>Центральный магазин</option><option>ПВЗ рядом с метро</option></select></label></section>'
        '<section class="sm-route-board"><figure><img src="'
        f'{route}" alt="Зимний маршрут доставки снаряжения"></figure>'
        '<div class="sm-route-line" aria-label="Этапы маршрута"><i></i><span></span><i></i><span></span><i></i></div>'
        '<div class="sm-route-stops"><div><b>Москва-Север</b><span>упаковка · 24 августа</span></div>'
        '<div><b data-route-hub>Сортировочный центр</b><span data-route-transfer>контроль веса · 25 августа</span></div>'
        '<div><b data-route-city>Москва</b><span data-route-arrival>получение · 25 августа</span></div></div>'
        '<p data-route-note>Городская доставка без межрегиональной перегрузки.</p></section>'
        '<aside class="sm-delivery-result"><span>РАСЧЁТ ДЛЯ ЗАКАЗА № 1846</span><h2>Маршрут заказа</h2>'
        '<div data-delivery-summary><b>Москва · Север Стандарт</b><strong>25 августа · 490 ₽</strong>'
        '<p>Центральный магазин · хранение 3 дня</p></div>'
        '<dl><div><dt>Вес отправления</dt><dd>8,6 кг</dd></div><div><dt>Страхование</dt><dd>включено</dd></div>'
        '<div><dt>Упаковка</dt><dd>жёсткий короб</dd></div></dl>'
        '<button type="button" class="sm-primary">Выбрать доставку '
        f'{icon("arrow-right", size=18)}</button></aside></div>'
        '</section>'
        '<section class="sm-delivery-lower" data-lower-band="true">'
        '<figure class="sm-guide"><img src="'
        f'{guide}" alt="Инструктор Северного маршрута перед зимним выходом">'
        '<figcaption><span>ЭКСПЕДИЦИОННАЯ УПАКОВКА</span><b>Анна Серова</b><p>Проверяет дуги, горелки и температурные товары до отправки.</p></figcaption></figure>'
        '<section class="sm-coverage"><header><span>РЕГИОНАЛЬНАЯ МАТРИЦА</span><h2>Покрытие и сроки</h2></header>'
        '<table><thead><tr><th>Направление</th><th>Стандарт</th><th>Экспресс</th><th>Пунктов</th></tr></thead>'
        '<tbody><tr><td>Центральный округ</td><td>1–2 дня</td><td>следующий день</td><td>214</td></tr>'
        '<tr><td>Поволжье</td><td>3–4 дня</td><td>1–2 дня</td><td>96</td></tr>'
        '<tr><td>Урал</td><td>4–6 дней</td><td>2–3 дня</td><td>71</td></tr></tbody></table></section>'
        '<aside class="sm-packing-note"><b>Перед зимней отправкой</b><p>Газовые баллоны отправляем отдельно допустимым наземным маршрутом. Пуховые вещи не вакуумируем.</p>'
        '<dl><div><dt>Фото упаковки</dt><dd>в личном кабинете</dd></div><div><dt>Пломба</dt><dd>номер в заказе</dd></div></dl></aside>'
        '</section></main>'
    )


_CSS = r"""
.sm-page, .sm-page *, .sm-page *::before, .sm-page *::after { box-sizing: border-box; }
.sm-page { width: 1920px; height: 1120px; overflow: hidden; display: grid; grid-template-rows: 128px 992px; background: #FFFFFF; color: #172027; font-family: "Segoe UI", Arial, sans-serif; font-size: 14px; line-height: 1.35; letter-spacing: 0; }
.sm-page h1, .sm-page h2, .sm-page h3, .sm-page p, .sm-page figure, .sm-page dl, .sm-page dd, .sm-page ul, .sm-page ol { margin: 0; }
.sm-page button, .sm-page input, .sm-page select { font: inherit; letter-spacing: 0; color: inherit; }
.sm-page button, .sm-page select { cursor: pointer; }
.sm-page button { border: 0; }
.sm-page a { color: inherit; text-decoration: none; }
.sm-page img { width: 100%; height: 100%; display: block; object-fit: cover; }
.sm-page table { width: 100%; border-collapse: collapse; }
.sm-page .lucide-icon { flex: 0 0 auto; stroke-width: 1.7; }
.sm-header { width: 1834px; height: 128px; overflow: hidden; border-bottom: 1px solid #cfd7d3; }
.sm-utility { height: 40px; padding: 0 64px; display: flex; align-items: center; justify-content: space-between; background: #173F32; color: #FFFFFF; font-size: 12px; }
.sm-utility > b { font-weight: 600; }
.sm-utility nav { height: 100%; display: flex; align-items: center; }
.sm-utility nav a { height: 100%; padding: 0 22px; display: flex; align-items: center; border-left: 1px solid #3e6155; }
.sm-shopbar { height: 88px; padding: 0 64px; display: grid; grid-template-columns: 255px 184px 410px 164px 1fr 116px; gap: 18px; align-items: center; background: #FFFFFF; }
.sm-brand { height: 54px; display: flex; align-items: center; gap: 14px; color: #173F32; }
.sm-brand i { position: relative; width: 54px; height: 42px; border-bottom: 4px solid #E83B3B; overflow: hidden; }
.sm-brand i span { position: absolute; bottom: 0; width: 34px; height: 35px; background: #173F32; clip-path: polygon(50% 0, 100% 100%, 0 100%); }
.sm-brand i span:first-child { left: 0; }
.sm-brand i span:last-child { right: 0; height: 27px; background: #61776D; }
.sm-brand > span { display: grid; line-height: .95; }
.sm-brand strong, .sm-brand b { font-size: 20px; font-weight: 800; }
.sm-catalog-trigger { height: 46px; padding: 0 18px; display: flex; align-items: center; justify-content: center; gap: 10px; background: #173F32; color: #FFFFFF; font-weight: 700; }
.sm-page .sm-catalog-trigger { color: #FFFFFF; }
.sm-search { height: 46px; display: grid; grid-template-columns: 1fr 48px; border: 1px solid #aebbb5; background: #FFFFFF; }
.sm-search input { min-width: 0; padding: 0 16px; border: 0; outline: 0; }
.sm-search button { display: grid; place-items: center; background: #E83B3B; color: #FFFFFF; }
.sm-location { height: 46px; display: flex; align-items: center; gap: 9px; padding-left: 8px; color: #173F32; }
.sm-location span { display: grid; }
.sm-location small { color: #61776D; font-size: 12px; }
.sm-category-nav { min-width: 0; height: 88px; display: flex; align-items: center; justify-content: space-between; gap: 14px; font-size: 13px; font-weight: 600; white-space: nowrap; }
.sm-category-nav a { height: 88px; display: flex; align-items: center; border-bottom: 4px solid transparent; }
.sm-category-nav a.is-active { color: #173F32; border-color: #E83B3B; }
.sm-cart-link { height: 52px; display: grid; grid-template-columns: 24px 1fr 24px; align-items: center; gap: 7px; background: #EEF1EF; color: #173F32; font-weight: 700; }
.sm-cart-link b { width: 24px; height: 24px; display: grid; place-items: center; background: #E83B3B; color: #FFFFFF; font-size: 12px; }
.sm-route { width: 1834px; height: 992px; overflow: hidden; display: grid; grid-template-rows: 650px 342px; }
.sm-breadcrumb, .sm-route-head p { color: #61776D; font-size: 12px; font-weight: 600; }
.sm-lead { color: #46564f; font-size: 17px; line-height: 1.55; }
.sm-primary { min-height: 48px; padding: 0 20px; display: flex; align-items: center; justify-content: center; gap: 10px; background: #E83B3B; color: #FFFFFF; font-weight: 800; }
.sm-page .sm-primary { color: #FFFFFF; }
.sm-segment { display: grid; grid-auto-flow: column; grid-auto-columns: 1fr; border: 1px solid #9fb0a8; }
.sm-segment button { min-height: 42px; padding: 0 14px; background: #FFFFFF; border-right: 1px solid #9fb0a8; font-weight: 700; }
.sm-segment button:last-child { border-right: 0; }
.sm-segment button[aria-pressed="true"] { background: #173F32; color: #FFFFFF; }
.sm-cover-main { height: 650px; padding: 34px 64px 30px; display: grid; grid-template-columns: 640px 520px 482px; gap: 32px; background: #FFFFFF; }
.sm-cover-copy { padding-top: 6px; display: flex; flex-direction: column; }
.sm-cover-copy h1 { max-width: 660px; margin: 25px 0 18px; font-size: 46px; line-height: 1.03; font-weight: 800; color: #173F32; }
.sm-cover-copy .sm-lead { max-width: 620px; }
.sm-control-block { width: 440px; margin-top: 28px; }
.sm-control-block > b { display: block; margin-bottom: 10px; font-size: 12px; text-transform: uppercase; }
.sm-route-facts { margin-top: auto; display: grid; grid-template-columns: repeat(3, 1fr); border-top: 1px solid #aebbb5; border-bottom: 1px solid #aebbb5; }
.sm-route-facts div { min-height: 78px; padding: 15px 17px; border-right: 1px solid #aebbb5; }
.sm-route-facts div:last-child { border-right: 0; }
.sm-route-facts dt { color: #61776D; font-size: 12px; }
.sm-route-facts dd { margin-top: 5px; font-size: 17px; font-weight: 800; }
.sm-cover-photo { height: 586px; display: grid; grid-template-rows: 510px 76px; background: #173F32; }
.sm-cover-photo figcaption { padding: 0 20px; display: flex; align-items: center; justify-content: space-between; color: #FFFFFF; }
.sm-cover-photo figcaption span { color: #c9d5d0; font-size: 12px; }
.sm-kit-sheet { height: 586px; padding: 28px; border: 1px solid #aebbb5; display: flex; flex-direction: column; }
.sm-kit-sheet > span, .sm-cover-lower header span, .sm-catalog-lower header span, .sm-tents-lower header span, .sm-delivery-controls > span, .sm-delivery-result > span, .sm-delivery-lower header span { color: #E83B3B; font-size: 12px; font-weight: 800; }
.sm-kit-sheet h2 { margin: 11px 0 20px; color: #173F32; font-size: 30px; line-height: 1.1; }
.sm-kit-sheet ul { padding: 0; list-style: none; border-top: 1px solid #d7ddda; }
.sm-kit-sheet li { padding: 9px 0; border-bottom: 1px solid #d7ddda; font-weight: 600; }
.sm-kit-stock { margin-top: 17px; display: grid; grid-template-columns: 10px 1fr; gap: 2px 9px; align-items: center; }
.sm-kit-stock i, .sm-selected-stock i, .sm-stock-cell i { width: 9px; height: 9px; background: #2b8a57; }
.sm-kit-stock span { grid-column: 2; color: #61776D; font-size: 12px; }
.sm-kit-total { margin-top: auto; padding-top: 13px; border-top: 2px solid #173F32; display: grid; grid-template-columns: 1fr auto; align-items: end; }
.sm-kit-total span { font-weight: 700; }
.sm-kit-total strong { grid-row: span 2; font-size: 30px; color: #173F32; }
.sm-kit-total small { color: #E83B3B; font-size: 12px; }
.sm-kit-sheet .sm-primary { margin-top: 14px; }
.sm-kit-sheet > p { margin-top: 9px; color: #61776D; font-size: 12px; text-align: center; }
.sm-cover-lower, .sm-catalog-lower, .sm-tents-lower { height: 342px; padding: 24px 64px 0; background: #EEF1EF; }
.sm-cover-lower header, .sm-catalog-lower header, .sm-tents-lower header { height: 65px; display: flex; align-items: start; justify-content: space-between; }
.sm-cover-lower header div, .sm-catalog-lower header div, .sm-tents-lower header div { display: flex; align-items: baseline; gap: 18px; }
.sm-cover-lower h2, .sm-catalog-lower h2, .sm-tents-lower h2 { font-size: 25px; color: #173F32; }
.sm-cover-lower header p, .sm-catalog-lower header p, .sm-tents-lower header p { max-width: 570px; color: #61776D; }
.sm-assortment { height: 182px; display: grid; grid-template-columns: repeat(4, 1fr); border: 1px solid #b8c2bd; background: #FFFFFF; }
.sm-assortment article { padding: 24px; display: grid; grid-template-columns: 42px 1fr; gap: 16px; border-right: 1px solid #b8c2bd; }
.sm-assortment article:last-child { border-right: 0; }
.sm-assortment article > span { color: #E83B3B; font-weight: 800; }
.sm-assortment article div { display: grid; grid-template-columns: 1fr auto; align-content: start; gap: 10px; }
.sm-assortment article b { font-size: 18px; color: #173F32; }
.sm-assortment article strong { color: #61776D; }
.sm-assortment article p { grid-column: 1 / -1; line-height: 1.5; }
.sm-cover-lower footer, .sm-catalog-lower footer, .sm-tents-lower footer { height: 71px; display: flex; align-items: center; justify-content: space-between; border-top: 1px solid #b8c2bd; font-size: 12px; }
.sm-cover-lower footer b, .sm-cover-lower footer strong { color: #173F32; }
.sm-route-head { height: 86px; padding: 0 64px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #cfd7d3; }
.sm-route-head h1 { margin-top: 4px; color: #173F32; font-size: 31px; line-height: 1; }
.sm-result-tools { display: flex; align-items: center; gap: 28px; }
.sm-result-tools > b { min-width: 100px; color: #173F32; font-size: 17px; }
.sm-result-tools label { display: flex; align-items: center; gap: 10px; color: #61776D; }
.sm-result-tools select { height: 40px; min-width: 220px; padding: 0 36px 0 12px; border: 1px solid #aebbb5; background: #FFFFFF; }
.sm-catalog-workspace { height: 564px; padding: 18px 64px 24px; display: grid; grid-template-columns: 292px 1fr 276px; gap: 22px; }
.sm-filter-rail { height: 522px; padding-right: 22px; border-right: 1px solid #aebbb5; }
.sm-filter-rail h2, .sm-stock-rail h2 { font-size: 19px; color: #173F32; }
.sm-filter-rail fieldset { margin: 14px 0 0; padding: 12px 0 3px; border: 0; border-top: 1px solid #d7ddda; }
.sm-filter-rail legend { padding: 0; font-size: 12px; font-weight: 800; text-transform: uppercase; }
.sm-filter-rail label { min-height: 28px; display: grid; grid-template-columns: 18px 1fr auto; align-items: center; }
.sm-filter-rail input { width: 15px; height: 15px; accent-color: #173F32; }
.sm-filter-rail label span { color: #61776D; font-size: 12px; }
.sm-filter-rail > button { margin-top: 9px; padding: 0; background: transparent; color: #E83B3B; font-size: 12px; font-weight: 700; }
.sm-product-area { min-width: 0; }
.sm-catalog-summary { height: 46px; padding: 0 14px; display: flex; align-items: center; justify-content: space-between; background: #173F32; color: #FFFFFF; }
.sm-catalog-summary span { color: #c9d5d0; font-size: 12px; }
.sm-product-matrix { height: 476px; display: grid; grid-template-columns: repeat(2, 1fr); grid-template-rows: repeat(2, 238px); border-left: 1px solid #cfd7d3; }
.sm-product-matrix article { min-width: 0; padding: 19px; border-right: 1px solid #cfd7d3; border-bottom: 1px solid #cfd7d3; display: flex; flex-direction: column; }
.sm-product-matrix article > span, .sm-product-feature > div > span { color: #E83B3B; font-size: 12px; font-weight: 800; }
.sm-product-matrix h3 { margin: 9px 0 5px; color: #173F32; font-size: 19px; }
.sm-product-matrix p { color: #61776D; }
.sm-product-matrix article > strong { margin-top: auto; font-size: 19px; color: #173F32; }
.sm-product-matrix dl { margin-top: 18px; border-top: 1px solid #d7ddda; }
.sm-product-matrix dl div { padding: 6px 0; display: flex; justify-content: space-between; border-bottom: 1px solid #d7ddda; }
.sm-product-matrix dt { color: #61776D; }
.sm-product-feature { display: grid !important; grid-template-columns: 190px 1fr; gap: 18px; }
.sm-product-feature figure { min-width: 0; height: 199px; }
.sm-product-feature > div { min-width: 0; display: flex; flex-direction: column; }
.sm-product-feature > div > strong { margin-top: auto; font-size: 19px; color: #173F32; }
.sm-product-feature small { margin-top: 3px; color: #2b8a57; font-size: 12px; font-weight: 700; }
.sm-rating { margin-top: 14px; display: flex; align-items: center; gap: 9px; }
.sm-rating b { color: #F2A51A; }
.sm-rating span { color: #F2A51A; font-size: 12px; }
.sm-stock-rail { height: 522px; padding: 20px; border: 1px solid #aebbb5; }
.sm-stock-rail dl { margin-top: 16px; }
.sm-stock-rail dl div { padding: 10px 0; display: flex; justify-content: space-between; border-bottom: 1px solid #d7ddda; }
.sm-stock-rail dd { font-weight: 800; }
.sm-stock-rail p { margin-top: 24px; padding-top: 18px; border-top: 2px solid #173F32; line-height: 1.55; }
.sm-stock-rail p b { display: block; color: #173F32; }
.sm-stock-rail button { width: 100%; height: 42px; margin-top: 20px; background: #EEF1EF; color: #173F32; font-weight: 800; }
.sm-expert-strip { height: 195px; display: grid; grid-template-columns: repeat(3, 1fr) 1.25fr; border: 1px solid #b8c2bd; background: #FFFFFF; }
.sm-expert-strip article, .sm-expert-strip aside { padding: 22px; border-right: 1px solid #b8c2bd; display: flex; flex-direction: column; }
.sm-expert-strip aside { border-right: 0; background: #173F32; color: #FFFFFF; }
.sm-expert-strip article b, .sm-expert-strip aside b { font-size: 18px; }
.sm-expert-strip article span { margin-top: 8px; color: #61776D; }
.sm-expert-strip article strong { margin-top: auto; color: #E83B3B; }
.sm-expert-strip aside p { margin-top: 8px; color: #c9d5d0; }
.sm-expert-strip aside button { width: 170px; height: 40px; margin-top: auto; background: #E83B3B; color: #FFFFFF; font-weight: 800; }
.sm-catalog-lower footer b { color: #173F32; }
.sm-cart-status, .sm-delivery-promise { text-align: right; color: #61776D; }
.sm-cart-status b, .sm-cart-status strong, .sm-delivery-promise b { color: #173F32; font-size: 19px; }
.sm-cart-status span { margin: 0 10px; }
.sm-tent-workspace { height: 564px; padding: 18px 64px 24px; display: grid; grid-template-columns: 326px 1fr 348px; gap: 22px; }
.sm-tent-controls { padding-right: 22px; border-right: 1px solid #aebbb5; }
.sm-tent-controls h2 { margin-bottom: 15px; color: #173F32; font-size: 19px; }
.sm-tent-controls > b { font-size: 12px; text-transform: uppercase; }
.sm-capacity { margin-top: 8px; }
.sm-tent-controls fieldset { margin: 14px 0; padding: 12px 0; border: 0; border-top: 1px solid #d7ddda; border-bottom: 1px solid #d7ddda; }
.sm-tent-controls legend { padding: 0; font-size: 12px; font-weight: 800; text-transform: uppercase; }
.sm-tent-controls fieldset label { min-height: 27px; display: flex; align-items: center; gap: 8px; }
.sm-tent-controls fieldset input { width: 15px; height: 15px; accent-color: #173F32; }
.sm-tent-controls figure { height: 255px; display: grid; grid-template-rows: 221px 34px; background: #173F32; color: #FFFFFF; }
.sm-tent-controls figcaption { padding: 8px 12px; font-size: 12px; }
.sm-tent-comparison { border: 1px solid #aebbb5; }
.sm-table-heading { height: 78px; padding: 0 20px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #aebbb5; }
.sm-table-heading span, .sm-selected-spec > span { color: #E83B3B; font-size: 12px; font-weight: 800; }
.sm-table-heading h2 { color: #173F32; font-size: 21px; }
.sm-table-heading > b { color: #173F32; }
.sm-tent-comparison th, .sm-tent-comparison td { height: 74px; padding: 10px 13px; border-bottom: 1px solid #d7ddda; text-align: left; }
.sm-tent-comparison th { height: 42px; background: #EEF1EF; color: #61776D; font-size: 12px; }
.sm-tent-comparison td b, .sm-tent-comparison td span { display: block; }
.sm-tent-comparison td span { color: #61776D; font-size: 12px; }
.sm-tent-comparison tr.is-selected td:first-child { border-left: 5px solid #E83B3B; }
.sm-comparison-note { height: 64px; padding: 0 16px; display: flex; align-items: center; justify-content: space-between; color: #61776D; font-size: 12px; }
.sm-comparison-note b { color: #173F32; }
.sm-selected-spec { padding: 24px; border: 1px solid #aebbb5; display: flex; flex-direction: column; }
.sm-selected-spec h2 { margin: 8px 0 14px; color: #173F32; font-size: 26px; }
.sm-selected-spec dl { border-top: 1px solid #d7ddda; }
.sm-selected-spec dl div { padding: 8px 0; display: flex; justify-content: space-between; border-bottom: 1px solid #d7ddda; }
.sm-selected-spec dt { color: #61776D; }
.sm-selected-spec dd { font-weight: 700; }
.sm-selected-stock { margin-top: 16px; display: grid; grid-template-columns: 9px 1fr; gap: 2px 8px; align-items: center; }
.sm-selected-stock span { grid-column: 2; color: #61776D; font-size: 12px; }
.sm-selected-spec > strong { margin-top: auto; font-size: 26px; color: #173F32; }
.sm-selected-spec .sm-primary { margin-top: 10px; }
.sm-selected-spec > p { margin-top: 8px; color: #61776D; font-size: 12px; text-align: center; }
.sm-field-guide { height: 195px; display: grid; grid-template-columns: repeat(4, 1fr); border: 1px solid #b8c2bd; background: #FFFFFF; }
.sm-field-guide article { padding: 20px; display: grid; grid-template-columns: 42px 1fr; gap: 8px 10px; border-right: 1px solid #b8c2bd; }
.sm-field-guide article:last-child { border-right: 0; }
.sm-field-guide article > span { grid-row: span 3; color: #E83B3B; font-weight: 800; }
.sm-field-guide b { color: #173F32; font-size: 17px; }
.sm-field-guide p { line-height: 1.5; }
.sm-field-guide strong { margin-top: auto; color: #61776D; }
.sm-tents-lower footer b, .sm-tents-lower footer strong { color: #173F32; }
.sm-reserve-clock { min-width: 270px; text-align: right; color: #61776D; }
.sm-reserve-clock b { margin-left: 8px; color: #E83B3B; font-size: 20px; }
.sm-reserve-clock span { display: block; font-size: 12px; }
.sm-cart-workspace { height: 564px; padding: 18px 64px 24px; display: grid; grid-template-columns: 1fr 440px; gap: 28px; }
.sm-cart-table { border-top: 2px solid #173F32; }
.sm-cart-table-head { height: 38px; display: grid; grid-template-columns: 1fr 260px 170px 150px; align-items: center; border-bottom: 1px solid #aebbb5; color: #61776D; font-size: 12px; font-weight: 800; }
.sm-cart-table > article { height: 160px; display: grid; grid-template-columns: 1fr 260px 170px 150px; align-items: center; border-bottom: 1px solid #aebbb5; }
.sm-cart-table > article > div:first-child > span { color: #E83B3B; font-size: 12px; font-weight: 800; }
.sm-cart-table h2 { margin: 7px 0 5px; color: #173F32; font-size: 21px; }
.sm-cart-table p { color: #61776D; }
.sm-stock-cell { display: grid; grid-template-columns: 9px 1fr; gap: 2px 8px; align-items: center; }
.sm-stock-cell span { grid-column: 2; color: #61776D; font-size: 12px; }
.sm-quantity { color: #61776D; font-size: 12px; }
.sm-quantity input { width: 92px; height: 42px; margin-top: 6px; padding: 0 10px; border: 1px solid #aebbb5; display: block; font-size: 16px; font-weight: 800; }
.sm-cart-table > article > strong { font-size: 20px; color: #173F32; }
.sm-cart-support { height: 96px; padding: 0 18px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #aebbb5; background: #EEF1EF; }
.sm-cart-support div { display: grid; gap: 4px; }
.sm-cart-support span { color: #61776D; }
.sm-cart-support button, .sm-promo button { height: 40px; padding: 0 16px; background: #173F32; color: #FFFFFF; font-weight: 700; }
.sm-promo { height: 94px; display: flex; align-items: end; gap: 12px; border-bottom: 1px solid #aebbb5; padding-bottom: 16px; }
.sm-promo label { color: #61776D; font-size: 12px; }
.sm-promo input { width: 260px; height: 40px; margin-top: 5px; padding: 0 12px; border: 1px solid #aebbb5; display: block; text-transform: uppercase; }
.sm-promo > span { margin-left: auto; color: #61776D; font-size: 12px; }
.sm-order-sheet { height: 522px; padding: 24px; border: 1px solid #aebbb5; display: flex; flex-direction: column; }
.sm-order-sheet > span { color: #E83B3B; font-size: 12px; font-weight: 800; }
.sm-order-sheet h2 { margin: 8px 0 16px; color: #173F32; font-size: 26px; }
.sm-delivery-choice > b { display: block; margin-bottom: 7px; font-size: 12px; text-transform: uppercase; }
.sm-delivery-choice button { width: 100%; height: 42px; padding: 0 13px; display: flex; justify-content: space-between; align-items: center; border: 1px solid #aebbb5; border-bottom: 0; background: #FFFFFF; font-weight: 700; }
.sm-delivery-choice button:last-child { border-bottom: 1px solid #aebbb5; }
.sm-delivery-choice button[aria-pressed="true"] { background: #173F32; color: #FFFFFF; }
.sm-order-parts { margin-top: 16px; }
.sm-order-parts div { padding: 8px 0; display: flex; justify-content: space-between; border-bottom: 1px solid #d7ddda; }
.sm-order-parts dt { color: #61776D; }
.sm-order-parts dd { font-weight: 700; }
.sm-order-total { margin-top: 12px; padding-top: 11px; display: flex; align-items: end; justify-content: space-between; border-top: 2px solid #173F32; }
.sm-order-total span { font-weight: 800; }
.sm-order-total strong { color: #173F32; font-size: 27px; }
.sm-order-sheet .sm-primary { margin-top: auto; }
.sm-order-sheet > p { margin-top: 8px; color: #61776D; font-size: 12px; text-align: center; }
.sm-cart-lower { height: 342px; padding: 24px 64px; display: grid; grid-template-columns: 430px 1fr 356px; gap: 28px; background: #173F32; color: #FFFFFF; }
.sm-cart-lower > figure { height: 294px; display: grid; grid-template-rows: 230px 64px; background: #FFFFFF; color: #172027; }
.sm-cart-lower figcaption { padding: 0 16px; display: flex; align-items: center; justify-content: space-between; }
.sm-cart-lower figcaption span { color: #61776D; font-size: 12px; }
.sm-reserve-ledger { min-width: 0; }
.sm-reserve-ledger header span { color: #F2A51A; font-size: 12px; font-weight: 800; }
.sm-reserve-ledger h2 { margin-top: 5px; font-size: 24px; }
.sm-reserve-ledger ol { margin-top: 18px; padding: 0; list-style: none; border-top: 1px solid #61776D; }
.sm-reserve-ledger li { min-height: 65px; display: grid; grid-template-columns: 130px 1fr; align-items: center; border-bottom: 1px solid #61776D; }
.sm-reserve-ledger li > b { color: #F2A51A; font-size: 12px; text-transform: uppercase; }
.sm-reserve-ledger li div { display: grid; gap: 3px; }
.sm-reserve-ledger li span { color: #c9d5d0; font-size: 12px; }
.sm-cart-lower > aside { height: 294px; padding: 22px; border: 1px solid #61776D; display: flex; flex-direction: column; }
.sm-cart-lower > aside > b { font-size: 20px; }
.sm-cart-lower > aside > p { margin-top: 9px; color: #c9d5d0; line-height: 1.5; }
.sm-cart-lower > aside div { padding: 8px 0; display: flex; justify-content: space-between; border-bottom: 1px solid #61776D; }
.sm-cart-lower > aside button { height: 42px; margin-top: auto; background: #E83B3B; color: #FFFFFF; font-weight: 800; }
.sm-delivery-promise { display: grid; }
.sm-delivery-workspace { height: 564px; padding: 18px 64px 24px; display: grid; grid-template-columns: 394px 1fr 390px; gap: 24px; }
.sm-delivery-controls { padding: 22px; border: 1px solid #aebbb5; }
.sm-delivery-controls h2, .sm-delivery-result h2 { margin: 6px 0 17px; color: #173F32; font-size: 24px; }
.sm-delivery-controls label { display: block; color: #61776D; font-size: 12px; font-weight: 700; }
.sm-delivery-controls select { width: 100%; height: 42px; margin: 6px 0 14px; padding: 0 12px; border: 1px solid #aebbb5; background: #FFFFFF; }
.sm-carrier-controls > b { display: block; margin-bottom: 6px; font-size: 12px; text-transform: uppercase; }
.sm-carrier-controls button { width: 100%; height: 48px; padding: 0 12px; display: flex; align-items: center; justify-content: space-between; border: 1px solid #aebbb5; border-bottom: 0; background: #FFFFFF; font-weight: 700; }
.sm-carrier-controls button:last-child { border-bottom: 1px solid #aebbb5; }
.sm-carrier-controls button span { color: #61776D; font-size: 12px; }
.sm-carrier-controls button[aria-pressed="true"] { background: #173F32; color: #FFFFFF; }
.sm-carrier-controls button[aria-pressed="true"] span { color: #FFFFFF; }
.sm-route-board { min-width: 0; padding: 0 20px; border-top: 1px solid #aebbb5; border-bottom: 1px solid #aebbb5; }
.sm-route-board figure { height: 282px; margin: 18px 0 22px; }
.sm-route-line { height: 22px; display: grid; grid-template-columns: 18px 1fr 18px 1fr 18px; align-items: center; }
.sm-route-line i { width: 18px; height: 18px; border: 4px solid #173F32; background: #FFFFFF; }
.sm-route-line i:last-child { border-color: #E83B3B; }
.sm-route-line span { height: 3px; background: #173F32; }
.sm-route-stops { margin-top: 8px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px; }
.sm-route-stops div { display: grid; }
.sm-route-stops div:nth-child(2) { text-align: center; }
.sm-route-stops div:last-child { text-align: right; }
.sm-route-stops span, .sm-route-board > p { color: #61776D; font-size: 12px; }
.sm-route-board > p { margin-top: 20px; padding-top: 11px; border-top: 1px solid #d7ddda; }
.sm-delivery-result { padding: 22px; border: 1px solid #aebbb5; display: flex; flex-direction: column; }
.sm-delivery-result [data-delivery-summary] { padding: 16px; background: #EEF1EF; display: grid; gap: 6px; }
.sm-delivery-result [data-delivery-summary] b { color: #173F32; font-size: 16px; }
.sm-delivery-result [data-delivery-summary] strong { color: #E83B3B; font-size: 20px; }
.sm-delivery-result [data-delivery-summary] p { color: #61776D; font-size: 12px; }
.sm-delivery-result dl { margin-top: 14px; }
.sm-delivery-result dl div { padding: 8px 0; display: flex; justify-content: space-between; border-bottom: 1px solid #d7ddda; }
.sm-delivery-result dt { color: #61776D; }
.sm-delivery-result dd { font-weight: 700; }
.sm-delivery-result .sm-primary { margin-top: auto; }
.sm-delivery-lower { height: 342px; padding: 24px 64px; display: grid; grid-template-columns: 410px 1fr 390px; gap: 28px; background: #EEF1EF; }
.sm-guide { height: 294px; display: grid; grid-template-columns: 160px 1fr; background: #173F32; color: #FFFFFF; }
.sm-guide figcaption { padding: 24px 20px; display: flex; flex-direction: column; }
.sm-guide figcaption span { color: #F2A51A; font-size: 12px; font-weight: 800; }
.sm-guide figcaption b { margin-top: 14px; font-size: 21px; }
.sm-guide figcaption p { margin-top: 9px; color: #c9d5d0; line-height: 1.5; }
.sm-coverage { height: 294px; padding: 18px 20px; background: #FFFFFF; border: 1px solid #b8c2bd; }
.sm-coverage header { height: 51px; }
.sm-coverage h2 { margin-top: 3px; color: #173F32; font-size: 21px; }
.sm-coverage th, .sm-coverage td { height: 43px; padding: 0 10px; border-bottom: 1px solid #d7ddda; text-align: left; }
.sm-coverage th { background: #173F32; color: #FFFFFF; font-size: 12px; }
.sm-packing-note { height: 294px; padding: 24px; border: 1px solid #b8c2bd; background: #FFFFFF; }
.sm-packing-note > b { color: #173F32; font-size: 20px; }
.sm-packing-note > p { margin: 12px 0 20px; line-height: 1.55; }
.sm-packing-note dl { border-top: 2px solid #173F32; }
.sm-packing-note dl div { padding: 10px 0; display: flex; justify-content: space-between; border-bottom: 1px solid #d7ddda; }
.sm-packing-note dt { color: #61776D; }
.sm-packing-note dd { font-weight: 700; }
"""


_COVER_SCRIPT = r"""
(() => {
  const kits = {
    summer: {
      name: "Летний маршрут", price: "31 900 ₽", stock: "18 комплектов в наличии",
      duration: "4 дня", temperature: "+8…+24 °C", weight: "7,4 кг",
      items: ["Палатка Nord 2 Air", "Спальник +5 °C", "Рюкзак 58 л", "Коврик R-value 2.8"]
    },
    autumn: {
      name: "Осенний маршрут", price: "39 800 ₽", stock: "12 комплектов в наличии",
      duration: "3 дня", temperature: "−4…+12 °C", weight: "8,6 кг",
      items: ["Палатка Nord 2 Pro", "Спальник −7 °C", "Рюкзак 65 л", "Коврик R-value 4.2"]
    },
    winter: {
      name: "Зимний маршрут", price: "48 700 ₽", stock: "6 комплектов в наличии",
      duration: "3 дня", temperature: "−18…−4 °C", weight: "10,8 кг",
      items: ["Палатка Nord 2 Snow", "Спальник −20 °C", "Рюкзак 75 л", "Коврик R-value 6.4"]
    }
  };
  const update = (button) => {
    const kit = kits[button.dataset.value];
    document.querySelectorAll('[data-selectable="season"]').forEach((option) => {
      option.setAttribute("aria-pressed", String(option === button));
    });
    document.querySelector("[data-kit-name]").textContent = kit.name;
    document.querySelector("[data-kit-price]").textContent = kit.price;
    document.querySelector("[data-kit-stock]").textContent = kit.stock;
    document.querySelector("[data-kit-duration]").textContent = kit.duration;
    document.querySelector("[data-kit-temperature]").textContent = kit.temperature;
    document.querySelector("[data-kit-weight]").textContent = kit.weight;
    document.querySelector("[data-kit-items]").innerHTML = kit.items.map((item) => `<li>${item}</li>`).join("");
  };
  document.querySelectorAll('[data-selectable="season"]').forEach((button) => {
    button.addEventListener("click", () => update(button));
  });
})();
"""


_CATALOG_SCRIPT = r"""
(() => {
  const winter = document.querySelector('[data-catalog-filter="winter"]');
  const update = () => {
    const active = winter.checked;
    document.querySelector("[data-catalog-count]").textContent = active ? "38 товаров" : "126 товаров";
    document.querySelector("[data-catalog-summary]").innerHTML = active
      ? "<b>Подбор для зимнего похода</b><span>До −25 °C · ветер от 15 м/с · наличие в 5 городах</span>"
      : "<b>Подбор для летнего и межсезонного похода</b><span>Вес позиции до 3 кг · наличие в 7 городах</span>";
    document.querySelector("[data-city-stock]").textContent = active ? "18" : "52";
    document.querySelector("[data-catalog-feature-stock]").textContent = active
      ? "Зимняя серия · 6 шт." : "В наличии · 14 шт.";
  };
  winter.addEventListener("change", update);
})();
"""


_TENTS_SCRIPT = r"""
(() => {
  const profiles = {
    "2": { result: "2 места · ветер до 22 м/с", capacity: "2 человека", name: "Nord Ridge 2", price: "17 990 ₽" },
    "3": { result: "3 места · ветер до 20 м/с", capacity: "3 человека", name: "Boreal Storm 3", price: "19 400 ₽" },
    "4": { result: "4 места · ветер до 20 м/с", capacity: "4 человека", name: "Taiga Base 4", price: "23 900 ₽" }
  };
  document.querySelectorAll('[data-selectable="tent-capacity"]').forEach((button) => {
    button.addEventListener("click", () => {
      const profile = profiles[button.dataset.value];
      document.querySelectorAll('[data-selectable="tent-capacity"]').forEach((option) => {
        option.setAttribute("aria-pressed", String(option === button));
      });
      document.querySelector("[data-tent-result]").textContent = profile.result;
      document.querySelector("[data-selected-capacity]").textContent = profile.capacity;
      document.querySelector("[data-selected-tent]").textContent = profile.name;
      document.querySelector("[data-selected-tent-price]").textContent = profile.price;
      document.querySelector("[data-tent-capacity-cell]").textContent = button.dataset.value;
    });
  });
  document.querySelector("[data-add-tent]").addEventListener("click", () => {
    document.querySelector("[data-cart-count]").textContent = "1";
    document.querySelector("[data-tent-cart-state]").textContent = "Добавлено · резерв на 24 часа";
  });
})();
"""


_CART_SCRIPT = r"""
(() => {
  const quantity = document.querySelector("[data-cart-quantity]");
  const parts = document.querySelectorAll("[data-cart-part]");
  let delivery = "pickup";
  const grouped = (value) => String(value).replace(/\B(?=(\d{3})+(?!\d))/g, " ");
  const update = () => {
    const count = Math.max(1, Math.min(4, Number(quantity.value) || 1));
    const subtotal = 17990 * count;
    const discount = count >= 2 ? 1500 : 0;
    const deliveryCost = delivery === "courier" ? 1300 : 0;
    const total = subtotal - discount + deliveryCost;
    document.querySelector("[data-cart-line-total]").textContent = `${grouped(subtotal)} ₽`;
    parts[0].textContent = `${grouped(subtotal)} ₽`;
    parts[1].textContent = discount ? `−${grouped(discount)} ₽` : "0 ₽";
    parts[2].textContent = `${grouped(deliveryCost)} ₽`;
    document.querySelector("[data-cart-total]").textContent = `${grouped(total)} ₽`;
  };
  quantity.addEventListener("input", update);
  document.querySelectorAll('[data-selectable="delivery-mode"]').forEach((button) => {
    button.addEventListener("click", () => {
      delivery = button.dataset.value;
      document.querySelectorAll('[data-selectable="delivery-mode"]').forEach((option) => {
        option.setAttribute("aria-pressed", String(option === button));
      });
      update();
    });
  });
})();
"""


_DELIVERY_SCRIPT = r"""
(() => {
  const routes = {
    moscow: {
      city: "Москва", hub: "Городской терминал", transfer: "контроль веса · 24 августа",
      standard: { date: "25 августа", cost: "490 ₽", carrier: "Север Стандарт", note: "Городская доставка без межрегиональной перегрузки." },
      express: { date: "25 августа", cost: "790 ₽", carrier: "Экспресс", note: "Приоритетная городская линия до пункта выдачи." }
    },
    kazan: {
      city: "Казань", hub: "Хаб Нижний Новгород", transfer: "перегрузка · 27 августа",
      standard: { date: "30 августа", cost: "890 ₽", carrier: "Север Стандарт", note: "Наземный маршрут через Нижний Новгород, одна контрольная перегрузка." },
      express: { date: "29 августа", cost: "1 490 ₽", carrier: "Экспресс", note: "Приоритетный наземный маршрут до Казани с контролем пломбы." }
    },
    ekaterinburg: {
      city: "Екатеринбург", hub: "Хаб Пермь", transfer: "контроль пломбы · 29 августа",
      standard: { date: "1 сентября", cost: "1 190 ₽", carrier: "Север Стандарт", note: "Наземная линия через Пермь с температурным контролем." },
      express: { date: "30 августа", cost: "1 890 ₽", carrier: "Экспресс", note: "Ускоренная линия до Екатеринбурга без складского хранения." }
    }
  };
  const citySelect = document.querySelector("[data-delivery-city]");
  let carrier = "standard";
  const update = () => {
    const route = routes[citySelect.value];
    const service = route[carrier];
    document.querySelector("[data-delivery-summary]").innerHTML =
      `<b>${route.city} · ${service.carrier}</b><strong>${service.date} · ${service.cost}</strong><p>Центральный пункт · хранение 3 дня</p>`;
    document.querySelector("[data-route-hub]").textContent = route.hub;
    document.querySelector("[data-route-transfer]").textContent = route.transfer;
    document.querySelector("[data-route-city]").textContent = route.city;
    document.querySelector("[data-route-arrival]").textContent = `получение · ${service.date}`;
    document.querySelector("[data-route-note]").textContent = service.note;
  };
  citySelect.addEventListener("change", update);
  document.querySelectorAll('[data-selectable="carrier"]').forEach((button) => {
    button.addEventListener("click", () => {
      carrier = button.dataset.value;
      document.querySelectorAll('[data-selectable="carrier"]').forEach((option) => {
        option.setAttribute("aria-pressed", String(option === button));
      });
      update();
    });
  });
})();
"""


_BODY_RENDERERS = {
    "cover": _cover,
    "catalog": _catalog,
    "tents": _tents,
    "cart": _cart,
    "delivery": _delivery,
}

_ROUTE_SCRIPTS = {
    "cover": _COVER_SCRIPT,
    "catalog": _CATALOG_SCRIPT,
    "tents": _TENTS_SCRIPT,
    "cart": _CART_SCRIPT,
    "delivery": _DELIVERY_SCRIPT,
}


def render(
    project: ProjectSpec,
    shot: ShotSpec,
    assets: Mapping[str, str],
) -> RenderedPage:
    """Render one Sever Market route with its own retail state and assets."""
    if project.slug != "sever-market":
        raise KeyError(f"sever-market renderer does not support {project.slug}")
    try:
        body_renderer = _BODY_RENDERERS[shot.key]
    except KeyError as exc:
        raise ValueError(f"sever-market unknown route: {shot.key}") from exc

    owned = _owned_assets(shot.key, assets)
    html = (
        f'<div class="sm-page" data-site="sever-market" data-route="{escape_html(shot.key)}">'
        f'{_header(shot.key)}{body_renderer(owned)}</div>'
    )
    return RenderedPage(html=html, css=_CSS, scripts=_ROUTE_SCRIPTS[shot.key])
