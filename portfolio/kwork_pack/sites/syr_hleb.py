"""Dedicated editorial storefront renderer for Syr Hleb."""

from collections.abc import Mapping

from ..components import escape_html
from ..icons import icon
from ..models import ProjectSpec, ShotSpec
from .runtime import RenderedPage


_ROUTE_ASSETS = {
    "cover": ("gift_box",),
    "gift-sets": ("cheese_counter",),
    "builder": ("tasting_table",),
    "cheese": ("farmer_portrait",),
    "delivery": ("artisan_bread", "delivery_basket"),
}


def _owned_assets(
    route: str, assets: Mapping[str, str]
) -> dict[str, str]:
    resolved: dict[str, str] = {}
    for key in _ROUTE_ASSETS[route]:
        try:
            resolved[key] = escape_html(assets[key])
        except KeyError as exc:
            raise KeyError(f"syr-hleb {route} missing asset {key}") from exc
    return resolved


def _header(active: str) -> str:
    routes = (
        ("gift-sets", "Подарочные наборы"),
        ("cheese", "Сыры"),
        ("builder", "Собрать набор"),
        ("delivery", "Доставка"),
    )
    nav = "".join(
        f'<a href="#" class="{"is-active" if key == active else ""}">'
        f"{label}</a>"
        for key, label in routes
    )
    return (
        '<header class="sh-editorial-header">'
        '<div class="sh-header-main">'
        '<div class="sh-wordmark"><strong>Сыр и Хлеб</strong>'
        '<span>сыроварня · пекарня</span></div>'
        '<p class="sh-header-promise">Сделано небольшими партиями<br>'
        'и собрано вручную в Москве</p>'
        '<div class="sh-header-contact"><b>8 (800) 555-15-25</b>'
        '<span>ежедневно с 9:00 до 20:00</span></div>'
        '<div class="sh-header-actions">'
        f'<button type="button" aria-label="Поиск">{icon("filter", size=19)}</button>'
        f'<button type="button" aria-label="Профиль">{icon("users", size=19)}</button>'
        f'<button type="button" aria-label="Корзина, 2 товара">{icon("shopping-cart", size=20)}'
        '<span>2</span></button></div>'
        '</div>'
        f'<nav class="sh-header-nav" aria-label="Каталог">{nav}'
        '<a href="#">О сыроварне</a><a href="#">Контакты</a>'
        '<b>Доставка сегодня при заказе до 14:00</b></nav>'
        '</header>'
    )


def _cover(assets: Mapping[str, str]) -> str:
    image = assets["gift_box"]
    return (
        '<main class="sh-route sh-cover">'
        '<section class="sh-cover-hero">'
        f'<img src="{image}" alt="Подарочный короб с сырами, хлебом и фруктами">'
        '<div class="sh-cover-copy"><span>Собрано сегодня</span>'
        '<h1>Подарки со вкусом</h1>'
        '<p>Сыры собственной сыроварни, ремесленный хлеб<br>'
        'и точные сочетания для важного повода.</p>'
        '<button type="button">Выбрать набор '
        f'{icon("arrow-right", size=18)}</button></div>'
        '<dl class="sh-cover-facts"><div><dt>24 часа</dt><dd>от заказа до вручения</dd></div>'
        '<div><dt>8 сыров</dt><dd>созревают в нашей камере</dd></div>'
        '<div><dt>0 замен</dt><dd>без согласования с вами</dd></div></dl>'
        '</section>'
        '<section class="sh-cover-assortment">'
        '<div class="sh-section-title"><div><span>Редакция сыровара</span>'
        '<h2>Четыре готовых жеста</h2></div><a href="#">Смотреть все 12 наборов</a></div>'
        '<div class="sh-cover-products">'
        '<article class="sh-product-surface"><span>01 · универсальный</span>'
        '<h3>Сырная классика</h3><p>Костромской, камамбер, тартин, мёд</p>'
        '<div><b>3 450 ₽</b><button type="button" aria-label="Добавить Сырную классику">'
        f'{icon("shopping-cart", size=18)}</button></div></article>'
        '<article class="sh-product-surface"><span>02 · к вину</span>'
        '<h3>Белая плесень</h3><p>Камамбер, бри, груша, орех, багет</p>'
        '<div><b>3 900 ₽</b><button type="button" aria-label="Добавить Белую плесень">'
        f'{icon("shopping-cart", size=18)}</button></div></article>'
        '<article class="sh-product-surface"><span>03 · выразительный</span>'
        '<h3>Синий вечер</h3><p>Горгонзола, инжир, мёд, ржаной хлеб</p>'
        '<div><b>4 250 ₽</b><button type="button" aria-label="Добавить Синий вечер">'
        f'{icon("shopping-cart", size=18)}</button></div></article>'
        '<article class="sh-product-surface"><span>04 · лёгкий</span>'
        '<h3>Тихое утро</h3><p>Шевр, сезонные ягоды, конфитюр, чиабатта</p>'
        '<div><b>2 900 ₽</b><button type="button" aria-label="Добавить Тихое утро">'
        f'{icon("shopping-cart", size=18)}</button></div></article>'
        '</div></section>'
        '<footer class="sh-cover-footer"><b>Собираем только после заказа</b>'
        '<span>Подпишем открытку от руки</span><span>Пришлём фото перед отправкой</span>'
        '<span>Заменим сочетание по вкусу</span></footer>'
        '</main>'
    )


def _gift_sets(assets: Mapping[str, str]) -> str:
    image = assets["cheese_counter"]
    return (
        '<main class="sh-route sh-gifts">'
        '<section class="sh-gifts-intro"><div><span>Каталог · 12 наборов</span>'
        '<h1>Подарочные наборы для важного повода</h1></div>'
        '<p>Каждый набор собирает сыровар. Учитываем повод, бюджет и вкусы '
        'получателя, сохраняем состав до вручения.</p></section>'
        '<section class="sh-gifts-workbench">'
        '<aside class="sh-gift-filters"><div><b>Повод</b>'
        '<button type="button" data-selectable="gift-occasion" data-value="Любой повод" aria-pressed="true">Любой повод</button>'
        '<button type="button" data-selectable="gift-occasion" data-value="День рождения" aria-pressed="false">День рождения</button>'
        '<button type="button" data-selectable="gift-occasion" data-value="Благодарность" aria-pressed="false">Благодарность</button></div>'
        '<div><b>Бюджет</b>'
        '<button type="button" data-selectable="gift-budget" data-value="до 3 000 ₽" aria-pressed="false">до 3 000 ₽</button>'
        '<button type="button" data-selectable="gift-budget" data-value="до 5 000 ₽" aria-pressed="false">до 5 000 ₽</button>'
        '<button type="button" data-selectable="gift-budget" data-value="любой бюджет" aria-pressed="true">Любой бюджет</button></div>'
        '<p>Нужен особый состав?<br><a href="#">Написать сыровару</a></p></aside>'
        '<div class="sh-gift-catalog">'
        '<div class="sh-gift-assortment-head"><span>Подборка сыровара</span>'
        '<h2 class="sh-gift-assortment-title">Ассортимент · Любой повод · любой бюджет</h2></div>'
        '<div class="sh-gift-products">'
        '<article><span>Набор 01</span><h3>Сырная классика</h3>'
        '<p>Костромской · камамбер · тартин · мёд</p><b>3 450 ₽</b></article>'
        '<article><span>Набор 02</span><h3>Синий вечер</h3>'
        '<p>Горгонзола · инжир · ржаной хлеб · орех</p><b>4 250 ₽</b></article>'
        '<article><span>Набор 03</span><h3>Тихое утро</h3>'
        '<p>Шевр · ягоды · конфитюр · чиабатта</p><b>2 900 ₽</b></article>'
        '</div></div>'
        '<figure class="sh-gift-editorial-photo">'
        f'<img src="{image}" alt="Прилавок сыроварни с созревающими сырами">'
        '<figcaption><b>Партия № 48</b><span>Сыры нарезаем утром в день доставки</span></figcaption>'
        '</figure></section>'
        '<section class="sh-gift-notes"><article><span>01</span><div><b>Состав без сюрпризов</b>'
        '<p>Подтверждаем каждый продукт и вес до оплаты.</p>'
        '<small>Вес · дата производства · срок хранения</small></div></article>'
        '<article><span>02</span><div><b>Холодовая упаковка</b>'
        '<p>Сохраняет температуру сыра до четырёх часов.</p>'
        '<small>+2…+6 °C · без конденсата</small></div></article>'
        '<article><span>03</span><div><b>Личная открытка</b>'
        '<p>Напишем ваш текст от руки на плотной бумаге.</p>'
        '<small>До 120 знаков · без логотипа магазина</small></div></article>'
        '<article><span>04</span><div><b>Фото перед выездом</b>'
        '<p>Покажем готовый набор и подпись курьера.</p>'
        '<small>Имя курьера · номер заказа · пломба</small></div></article></section>'
        '</main>'
    )


def _builder(assets: Mapping[str, str]) -> str:
    image = assets["tasting_table"]
    return (
        '<main class="sh-route sh-builder" data-widget="gift-builder">'
        '<section class="sh-builder-intro"><div><span>Конструктор · шаг 2 из 3</span>'
        '<h1>Соберите подарочный набор</h1></div>'
        '<p>Начните с четырёх проверенных сочетаний. Количество и упаковку '
        'можно менять — итог пересчитается сразу.</p></section>'
        '<section class="sh-builder-workspace">'
        '<figure class="sh-builder-photo">'
        f'<img src="{image}" alt="Дегустационный стол с сырами и хлебом">'
        '<figcaption><b>Логика сочетания</b><span>мягкий · выдержанный · хлеб · сладкий акцент</span></figcaption>'
        '</figure>'
        '<div class="sh-builder-items"><div class="sh-builder-column-title">'
        '<span>Состав</span><b>4 позиции</b></div>'
        '<article data-builder-row="aged-cheese"><div><b>Костромской выдержанный</b><span>200 г · 690 ₽</span></div>'
        '<div class="sh-stepper"><button type="button" aria-label="Уменьшить Костромской сыр" data-builder-action="minus" data-item="aged-cheese">−</button>'
        '<span data-quantity="aged-cheese">1</span><button type="button" aria-label="Добавить Костромской сыр" data-builder-action="plus" data-item="aged-cheese">+</button></div></article>'
        '<article data-builder-row="camembert"><div><b>Камамбер сливочный</b><span>180 г · 580 ₽</span></div>'
        '<div class="sh-stepper"><button type="button" aria-label="Уменьшить Камамбер" data-builder-action="minus" data-item="camembert">−</button>'
        '<span data-quantity="camembert">1</span><button type="button" aria-label="Добавить Камамбер" data-builder-action="plus" data-item="camembert">+</button></div></article>'
        '<article data-builder-row="bread"><div><b>Хлеб тартин</b><span>420 г · 360 ₽</span></div>'
        '<div class="sh-stepper"><button type="button" aria-label="Уменьшить Тартин" data-builder-action="minus" data-item="bread">−</button>'
        '<span data-quantity="bread">1</span><button type="button" aria-label="Добавить Тартин" data-builder-action="plus" data-item="bread">+</button></div></article>'
        '<article data-builder-row="honey"><div><b>Мёд липовый</b><span>200 г · 430 ₽</span></div>'
        '<div class="sh-stepper"><button type="button" aria-label="Уменьшить Мёд" data-builder-action="minus" data-item="honey">−</button>'
        '<span data-quantity="honey">1</span><button type="button" aria-label="Добавить Мёд" data-builder-action="plus" data-item="honey">+</button></div></article>'
        '</div>'
        '<aside class="sh-builder-summary"><span>Ваш набор</span>'
        '<h2>Вечер у камина</h2><div data-builder-lines>4 продукта · 1 000 г</div>'
        '<b data-builder-total>Итого 2 610 ₽</b><p data-builder-package>Льняная сумка · 550 ₽</p>'
        '<button type="button" class="sh-primary-action">Перейти к открытке '
        f'{icon("arrow-right", size=17)}</button><small>Сборка сегодня · доставка завтра</small></aside>'
        '</section>'
        '<section class="sh-builder-ledger"><div class="sh-package-title"><span>03 · упаковка</span>'
        '<h2>Как будет выглядеть подарок</h2></div>'
        '<div class="sh-package-options">'
        '<button type="button" data-selectable="builder-package" data-name="Крафтовый короб" data-price="350" aria-pressed="false"><b>Крафтовый короб</b><span>+350 ₽ · бумажный наполнитель</span></button>'
        '<button type="button" data-selectable="builder-package" data-name="Льняная сумка" data-price="550" aria-pressed="true"><b>Льняная сумка</b><span>+550 ₽ · многоразовая</span></button>'
        '<button type="button" data-selectable="builder-package" data-name="Деревянный короб" data-price="890" aria-pressed="false"><b>Деревянный короб</b><span>+890 ₽ · именная бирка</span></button>'
        '</div><dl><div><dt>Вес набора</dt><dd data-builder-weight>1 000 г</dd></div>'
        '<div><dt>Срок хранения</dt><dd>5 суток</dd></div><div><dt>Температура</dt><dd>+2…+6 °C</dd></div></dl>'
        '</section></main>'
    )


def _cheese(assets: Mapping[str, str]) -> str:
    image = assets["farmer_portrait"]
    return (
        '<main class="sh-route sh-cheese">'
        '<section class="sh-cheese-intro"><div><span>Коллекция · 8 сыров</span>'
        '<h1>Сыры с характером места</h1></div>'
        '<p>Выберите происхождение и профиль вкуса. Мы покажем партию, '
        'дегустационные ноты и хлеб, который раскроет сыр.</p></section>'
        '<section class="sh-cheese-story">'
        '<figure class="sh-maker-portrait">'
        f'<img src="{image}" alt="Сыровар Анна Лебедева в камере созревания">'
        '<figcaption><span>Сыровар</span><b>Анна Лебедева</b><p>«Вкус начинается с молока, времени и честной температуры»</p></figcaption>'
        '</figure>'
        '<div class="sh-cheese-selector"><div class="sh-selector-group"><b>Происхождение</b>'
        '<button type="button" data-selectable="cheese-origin" data-value="Костромская область" aria-pressed="true">Кострома</button>'
        '<button type="button" data-selectable="cheese-origin" data-value="Алтай" aria-pressed="false">Алтай</button>'
        '<button type="button" data-selectable="cheese-origin" data-value="Подмосковье" aria-pressed="false">Подмосковье</button></div>'
        '<div class="sh-selector-group"><b>Профиль вкуса</b>'
        '<button type="button" data-selectable="cheese-flavor" data-value="ореховый" aria-pressed="true">Ореховый</button>'
        '<button type="button" data-selectable="cheese-flavor" data-value="сливочный" aria-pressed="false">Сливочный</button>'
        '<button type="button" data-selectable="cheese-flavor" data-value="пикантный" aria-pressed="false">Пикантный</button></div>'
        '<article class="sh-cheese-notes"><span data-cheese-label>Костромская область · выдержанный</span>'
        '<h2 data-cheese-name>Костромской резерв</h2><p data-cheese-notes>Ореховый, сливочный, долгое послевкусие</p>'
        '<dl><div><dt>Выдержка</dt><dd data-cheese-age>8 месяцев</dd></div>'
        '<div><dt>Партия</dt><dd data-cheese-batch>№ 48 / 12 кг</dd></div>'
        '<div><dt>Пара</dt><dd data-cheese-pairing>Пшеничный тартин · липовый мёд</dd></div></dl>'
        '<div><b data-cheese-price>690 ₽ / 200 г</b><button type="button">Добавить 200 г</button></div></article>'
        '</div></section>'
        '<section class="sh-provenance-timeline"><div><span>01 · молоко</span><b>Утренняя дойка</b><p>Ферма в 42 км от сыроварни</p></div>'
        '<div><span>02 · варка</span><b>Медный котёл</b><p>Не более 160 литров за партию</p></div>'
        '<div><span>03 · созревание</span><b>Естественная корка</b><p>Переворачиваем каждую неделю</p></div>'
        '<div><span>04 · отбор</span><b>Проба сыровара</b><p>В продажу проходит 8 из 10 голов</p></div></section>'
        '</main>'
    )


def _delivery(assets: Mapping[str, str]) -> str:
    bread = assets["artisan_bread"]
    basket = assets["delivery_basket"]
    return (
        '<main class="sh-route sh-delivery">'
        '<section class="sh-delivery-intro"><div><span>Москва и до 20 км от МКАД</span>'
        '<h1>Доставка бережно и точно ко времени</h1></div>'
        '<p>Хлеб приезжает в день выпечки, сыр — в холодовом конверте. '
        'Курьер знает имя получателя и текст вашей открытки.</p></section>'
        '<section class="sh-delivery-flow">'
        '<div class="sh-delivery-controls"><div><span>01 · кому</span><h2>Получатель</h2>'
        '<button type="button" data-selectable="delivery-recipient" data-value="self" aria-pressed="true">Я получу заказ</button>'
        '<button type="button" data-selectable="delivery-recipient" data-value="gift" aria-pressed="false">Это подарок</button></div>'
        '<div><span>02 · когда</span><h2>Интервал</h2>'
        '<button type="button" data-selectable="delivery-slot" data-value="today" aria-pressed="true">Сегодня · 18:00–20:00</button>'
        '<button type="button" data-selectable="delivery-slot" data-value="morning" aria-pressed="false">Завтра · 10:00–12:00</button>'
        '<button type="button" data-selectable="delivery-slot" data-value="evening" aria-pressed="false">Завтра · 18:00–20:00</button></div></div>'
        '<div class="sh-delivery-gallery"><figure>'
        f'<img src="{bread}" alt="Ремесленный хлеб из утренней выпечки">'
        '<figcaption><b>Выпечка 07:40</b><span>Тартин остыл перед упаковкой</span></figcaption></figure>'
        '<figure>'
        f'<img src="{basket}" alt="Подарочный набор перед вручением">'
        '<figcaption><b>Контроль 14:20</b><span>Состав и открытка проверены</span></figcaption></figure></div>'
        '<aside class="sh-delivery-summary"><span>Ваше вручение</span><h2>Заказ № 1846</h2>'
        '<p data-delivery-recipient>Получатель: Я</p><p data-delivery-slot>Сегодня · 18:00–20:00</p>'
        '<p data-delivery-address>ул. Поварская, 18 · передать лично</p>'
        '<p data-delivery-card>Открытка: без подписи</p><dl><div><dt>Набор</dt><dd>Сырная классика</dd></div>'
        '<div><dt>Доставка</dt><dd>490 ₽</dd></div><div><dt>К оплате</dt><dd>3 940 ₽</dd></div></dl>'
        '<button type="button">Подтвердить доставку '
        f'{icon("arrow-right", size=17)}</button></aside>'
        '</section>'
        '<section class="sh-delivery-conditions"><article><span>Температура</span><b>+2…+6 °C</b>'
        '<p>Холодовой конверт остаётся у получателя.</p></article>'
        '<article><span>Точность</span><b>Интервал 2 часа</b><p>За 30 минут курьер позвонит.</p></article>'
        '<article><span>Приватность</span><b>Цена скрыта</b><p>В подарке нет чека и стоимости.</p></article>'
        '<article><span>Если не дома</span><b>Свяжемся с вами</b><p>Не передаём заказ третьим лицам.</p></article>'
        '<footer><b>Зона доставки</b><span>Москва · Химки · Красногорск · Одинцово · Реутов</span>'
        '<span>Бесплатно от 7 000 ₽</span></footer></section>'
        '</main>'
    )


_CSS = """
.sh-page, .sh-page * { box-sizing: border-box; }
.sh-page { width: 100%; height: 1120px; overflow: hidden; background: #fff; color: #20231f; font-family: Arial, Helvetica, sans-serif; font-size: 14px; letter-spacing: 0; }
.sh-page button, .sh-page a { font: inherit; letter-spacing: 0; }
.sh-page button { cursor: pointer; }
.sh-editorial-header { height: 112px; background: #fff; border-bottom: 1px solid #d8ddd8; }
.sh-header-main { height: 74px; padding: 0 48px; display: grid; grid-template-columns: 260px 1fr 230px 132px; align-items: center; gap: 28px; }
.sh-wordmark { display: flex; flex-direction: column; color: #173b28; }
.sh-wordmark strong { font: 34px Georgia, 'Times New Roman', serif; line-height: 32px; }
.sh-wordmark span { margin-top: 5px; font-size: 12px; text-transform: uppercase; }
.sh-header-promise { margin: 0; color: #5f675f; font-size: 12px; line-height: 17px; }
.sh-header-contact { display: flex; flex-direction: column; align-items: flex-end; }
.sh-header-contact b { color: #173b28; font-size: 16px; font-weight: 600; }
.sh-header-contact span { margin-top: 4px; color: #6d736d; font-size: 12px; }
.sh-header-actions { display: flex; justify-content: flex-end; gap: 8px; }
.sh-header-actions button { position: relative; width: 36px; height: 36px; display: grid; place-items: center; border: 0; border-left: 1px solid #d8ddd8; background: #fff; color: #173b28; }
.sh-header-actions button span { position: absolute; right: 0; top: 0; min-width: 16px; height: 16px; padding: 0 4px; background: #a92728; color: #fff; font-size: 12px; line-height: 16px; }
.sh-header-nav { height: 38px; padding: 0 48px; display: flex; align-items: center; gap: 32px; border-top: 1px solid #eef0ed; }
.sh-header-nav a { color: #20231f; font-size: 12px; text-decoration: none; text-transform: uppercase; }
.sh-header-nav a.is-active { color: #a92728; font-weight: 700; }
.sh-header-nav b { margin-left: auto; color: #173b28; font-size: 12px; font-weight: 600; }
.sh-page main.sh-route { height: 1008px; min-height: 0; overflow: hidden; }
.sh-route h1, .sh-route h2, .sh-route h3, .sh-route p, .sh-route figure, .sh-route dl { margin: 0; }
.sh-route h1, .sh-route h2, .sh-route h3 { font-family: Georgia, 'Times New Roman', serif; font-weight: 400; }
.sh-primary-action { border: 0; background: #a92728; color: #fff; }

.sh-cover-hero { position: relative; height: 520px; overflow: hidden; background: #173b28; }
.sh-cover-hero > img { width: 100%; height: 100%; display: block; object-fit: cover; object-position: center; }
.sh-cover-copy { position: absolute; left: 48px; top: 56px; width: 390px; color: #fff; }
.sh-cover-copy > span { font-size: 13px; text-transform: uppercase; }
.sh-cover-copy h1 { margin-top: 24px; font-size: 68px; line-height: 68px; }
.sh-cover-copy p { margin-top: 24px; font-size: 16px; line-height: 24px; }
.sh-cover-copy button { margin-top: 30px; min-width: 210px; height: 52px; padding: 0 22px; display: flex; align-items: center; justify-content: space-between; border: 1px solid #a92728; background: #a92728; color: #fff; font-weight: 700; text-transform: uppercase; }
.sh-cover-facts { position: absolute; right: 48px; bottom: 0; width: 600px; height: 80px; display: grid; grid-template-columns: repeat(3, 1fr); background: #fff; color: #20231f; }
.sh-cover-facts > div { padding: 17px 20px; border-left: 1px solid #d8ddd8; }
.sh-cover-facts dt { color: #173b28; font: 23px Georgia, 'Times New Roman', serif; }
.sh-cover-facts dd { margin: 5px 0 0; font-size: 12px; }
.sh-cover-assortment { height: 422px; padding: 24px 48px 22px; background: #fff; }
.sh-section-title { height: 70px; display: flex; align-items: flex-start; justify-content: space-between; }
.sh-section-title span { color: #a92728; font-size: 12px; text-transform: uppercase; }
.sh-section-title h2 { margin-top: 5px; color: #173b28; font-size: 27px; }
.sh-section-title a { margin-top: 18px; color: #173b28; font-size: 12px; text-transform: uppercase; }
.sh-cover-products { height: 306px; display: grid; grid-template-columns: repeat(4, 1fr); border-top: 1px solid #cfd5d0; border-left: 1px solid #cfd5d0; }
.sh-product-surface { min-width: 0; padding: 24px 20px; display: flex; flex-direction: column; border-right: 1px solid #cfd5d0; border-bottom: 1px solid #cfd5d0; background: #f4f1eb; }
.sh-product-surface > span { color: #a92728; font-size: 12px; text-transform: uppercase; }
.sh-product-surface h3 { margin-top: 22px; color: #173b28; font-size: 23px; }
.sh-product-surface p { margin-top: 12px; min-height: 66px; color: #5f675f; font-size: 13px; line-height: 19px; }
.sh-product-surface > div { margin-top: auto; display: flex; align-items: center; justify-content: space-between; }
.sh-product-surface > div b { font-size: 18px; }
.sh-product-surface button { width: 38px; height: 38px; display: grid; place-items: center; border: 1px solid #173b28; background: #fff; color: #173b28; }
.sh-cover-footer { height: 66px; padding: 0 48px; display: grid; grid-template-columns: 1.2fr repeat(3, 1fr); align-items: center; gap: 28px; background: #173b28; color: #fff; }
.sh-cover-footer b { font: 18px Georgia, 'Times New Roman', serif; }
.sh-cover-footer span { padding-left: 18px; border-left: 1px solid #55705f; font-size: 12px; }

.sh-gifts-intro, .sh-builder-intro, .sh-cheese-intro, .sh-delivery-intro { height: 154px; padding: 24px 48px; display: grid; grid-template-columns: 1.3fr 1fr; align-items: end; border-bottom: 1px solid #d8ddd8; background: #fff; }
.sh-gifts-intro span, .sh-builder-intro span, .sh-cheese-intro span, .sh-delivery-intro span { color: #a92728; font-size: 12px; text-transform: uppercase; }
.sh-gifts-intro h1, .sh-builder-intro h1, .sh-cheese-intro h1, .sh-delivery-intro h1 { margin-top: 8px; color: #173b28; font-size: 39px; line-height: 43px; }
.sh-gifts-intro > p, .sh-builder-intro > p, .sh-cheese-intro > p, .sh-delivery-intro > p { padding: 0 0 4px 42px; color: #5f675f; font-size: 14px; line-height: 21px; border-left: 1px solid #c6923d; }
.sh-gifts-workbench { height: 624px; padding: 26px 48px; display: grid; grid-template-columns: 190px 1fr 334px; gap: 26px; background: #fff; }
.sh-gift-filters { display: flex; flex-direction: column; border-top: 2px solid #173b28; }
.sh-gift-filters > div { padding: 17px 0 13px; border-bottom: 1px solid #d8ddd8; }
.sh-gift-filters > div > b { display: block; margin-bottom: 8px; color: #173b28; font-size: 12px; text-transform: uppercase; }
.sh-gift-filters button { width: 100%; padding: 6px 8px; border: 0; background: #fff; color: #5f675f; text-align: left; font-size: 12px; }
.sh-gift-filters button[aria-pressed="true"] { background: #173b28; color: #fff; }
.sh-gift-filters > p { margin-top: auto; color: #5f675f; font-size: 12px; line-height: 18px; }
.sh-gift-filters a { color: #a92728; }
.sh-gift-catalog { min-width: 0; border-top: 2px solid #173b28; }
.sh-gift-assortment-head { height: 96px; padding: 15px 0; }
.sh-gift-assortment-head span { color: #a92728; font-size: 12px; text-transform: uppercase; }
.sh-gift-assortment-head h2 { margin-top: 8px; color: #173b28; font-size: 22px; line-height: 27px; }
.sh-gift-products { height: 474px; display: grid; grid-template-rows: repeat(3, 1fr); border-top: 1px solid #cfd5d0; background: #f4f1eb; }
.sh-gift-products article { position: relative; padding: 18px 104px 16px 18px; border-bottom: 1px solid #cfd5d0; }
.sh-gift-products article > span { color: #a92728; font-size: 12px; text-transform: uppercase; }
.sh-gift-products h3 { margin-top: 7px; color: #173b28; font-size: 20px; }
.sh-gift-products p { margin-top: 7px; color: #5f675f; font-size: 12px; line-height: 17px; }
.sh-gift-products article > b { position: absolute; right: 18px; top: 62px; font-size: 16px; }
.sh-gift-editorial-photo { height: 572px; display: grid; grid-template-rows: 1fr 72px; border-top: 2px solid #173b28; overflow: hidden; }
.sh-gift-editorial-photo img { width: 100%; height: 100%; display: block; object-fit: cover; object-position: center; min-height: 0; }
.sh-gift-editorial-photo figcaption { padding: 14px 16px; display: flex; flex-direction: column; background: #173b28; color: #fff; }
.sh-gift-editorial-photo figcaption b { font: 17px Georgia, 'Times New Roman', serif; }
.sh-gift-editorial-photo figcaption span { margin-top: 5px; font-size: 12px; }
.sh-gift-notes { height: 230px; display: grid; grid-template-columns: repeat(4, 1fr); border-top: 1px solid #d8ddd8; background: #fff; }
.sh-gift-notes article { padding: 32px 26px 24px 48px; display: grid; grid-template-columns: 34px 1fr; gap: 14px; border-right: 1px solid #d8ddd8; }
.sh-gift-notes article > span { color: #c6923d; font: 22px Georgia, 'Times New Roman', serif; }
.sh-gift-notes article > div { display: flex; flex-direction: column; }
.sh-gift-notes b { color: #173b28; font: 18px Georgia, 'Times New Roman', serif; }
.sh-gift-notes p { margin-top: 10px; color: #5f675f; font-size: 12px; line-height: 18px; }
.sh-gift-notes small { margin-top: auto; padding-top: 14px; border-top: 1px solid #d8ddd8; color: #173b28; font-size: 12px; line-height: 17px; }

.sh-builder-intro { height: 138px; }
.sh-builder-workspace { height: 604px; padding: 26px 48px; display: grid; grid-template-columns: 360px 1fr 270px; gap: 24px; background: #fff; }
.sh-builder-photo { height: 552px; display: grid; grid-template-rows: 1fr 78px; overflow: hidden; }
.sh-builder-photo img { width: 100%; height: 100%; min-height: 0; display: block; object-fit: cover; object-position: 64% center; }
.sh-builder-photo figcaption { padding: 14px 18px; display: flex; flex-direction: column; background: #173b28; color: #fff; }
.sh-builder-photo figcaption b { font: 18px Georgia, 'Times New Roman', serif; }
.sh-builder-photo figcaption span { margin-top: 5px; font-size: 12px; }
.sh-builder-items { height: 552px; border-top: 2px solid #173b28; }
.sh-builder-column-title { height: 58px; display: flex; align-items: center; justify-content: space-between; }
.sh-builder-column-title span { color: #a92728; font-size: 12px; text-transform: uppercase; }
.sh-builder-column-title b { color: #173b28; font: 20px Georgia, 'Times New Roman', serif; }
.sh-builder-items article { height: 112px; padding: 18px 0; display: flex; align-items: center; justify-content: space-between; border-top: 1px solid #d8ddd8; }
.sh-builder-items article > div:first-child { display: flex; flex-direction: column; }
.sh-builder-items article b { color: #173b28; font-size: 13px; }
.sh-builder-items article span { margin-top: 7px; color: #687068; font-size: 12px; }
.sh-stepper { width: 94px; height: 36px; display: grid; grid-template-columns: 30px 34px 30px; align-items: center; border: 1px solid #173b28; }
.sh-stepper button { height: 34px; border: 0; background: #fff; color: #173b28; font-size: 18px; }
.sh-stepper span { margin: 0 !important; color: #20231f !important; text-align: center; font-size: 13px !important; }
.sh-builder-summary { height: 552px; padding: 24px 22px; display: flex; flex-direction: column; background: #f4f1eb; border-top: 4px solid #a92728; }
.sh-builder-summary > span { color: #a92728; font-size: 12px; text-transform: uppercase; }
.sh-builder-summary h2 { margin-top: 18px; color: #173b28; font-size: 28px; line-height: 32px; }
.sh-builder-summary > div { margin-top: 28px; padding: 16px 0; border-top: 1px solid #cbc8c1; border-bottom: 1px solid #cbc8c1; color: #5f675f; font-size: 13px; }
.sh-builder-summary > b { margin-top: 26px; color: #20231f; font: 25px Georgia, 'Times New Roman', serif; }
.sh-builder-summary > p { margin-top: 8px; color: #5f675f; font-size: 12px; }
.sh-builder-summary > button { margin-top: auto; height: 48px; padding: 0 16px; display: flex; align-items: center; justify-content: space-between; }
.sh-builder-summary > small { margin-top: 12px; color: #5f675f; font-size: 12px; }
.sh-builder-ledger { height: 266px; padding: 24px 48px; display: grid; grid-template-columns: 220px 1fr 270px; gap: 26px; border-top: 1px solid #d8ddd8; background: #fff; }
.sh-package-title span { color: #a92728; font-size: 12px; text-transform: uppercase; }
.sh-package-title h2 { margin-top: 10px; color: #173b28; font-size: 25px; line-height: 30px; }
.sh-package-options { height: 190px; display: grid; grid-template-columns: repeat(3, 1fr); border-left: 1px solid #cfd5d0; border-top: 1px solid #cfd5d0; }
.sh-package-options button { padding: 18px 14px; display: flex; flex-direction: column; align-items: flex-start; border: 0; border-right: 1px solid #cfd5d0; border-bottom: 1px solid #cfd5d0; background: #fff; color: #20231f; text-align: left; }
.sh-package-options button[aria-pressed="true"] { background: #173b28; color: #fff; }
.sh-package-options b { font: 17px Georgia, 'Times New Roman', serif; }
.sh-package-options span { margin-top: auto; font-size: 12px; line-height: 17px; }
.sh-builder-ledger dl { border-top: 2px solid #173b28; }
.sh-builder-ledger dl > div { height: 58px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #d8ddd8; }
.sh-builder-ledger dt { color: #687068; font-size: 12px; }
.sh-builder-ledger dd { margin: 0; color: #173b28; font-size: 13px; font-weight: 700; }

.sh-cheese-intro { height: 142px; }
.sh-cheese-story { height: 610px; padding: 26px 48px; display: grid; grid-template-columns: 430px 1fr; gap: 38px; background: #fff; }
.sh-maker-portrait { height: 558px; position: relative; overflow: hidden; }
.sh-maker-portrait img { width: 100%; height: 100%; display: block; object-fit: cover; object-position: 38% center; }
.sh-maker-portrait figcaption { position: absolute; left: 0; bottom: 0; width: 242px; min-height: 142px; padding: 18px; background: #173b28; color: #fff; }
.sh-maker-portrait figcaption span { font-size: 12px; text-transform: uppercase; }
.sh-maker-portrait figcaption b { display: block; margin-top: 7px; font: 21px Georgia, 'Times New Roman', serif; }
.sh-maker-portrait figcaption p { margin-top: 9px; font-size: 12px; line-height: 17px; }
.sh-cheese-selector { height: 558px; display: grid; grid-template-rows: 74px 74px 1fr; border-top: 2px solid #173b28; }
.sh-selector-group { display: grid; grid-template-columns: 140px repeat(3, 1fr); align-items: center; gap: 8px; border-bottom: 1px solid #d8ddd8; }
.sh-selector-group > b { color: #173b28; font-size: 12px; text-transform: uppercase; }
.sh-selector-group button { height: 36px; border: 1px solid #bfc7c0; background: #fff; color: #5f675f; font-size: 12px; }
.sh-selector-group button[aria-pressed="true"] { border-color: #173b28; background: #173b28; color: #fff; }
.sh-cheese-notes { margin-top: 20px; padding: 24px 26px; background: #f4f1eb; border-left: 4px solid #c6923d; }
.sh-cheese-notes > span { color: #a92728; font-size: 12px; }
.sh-cheese-notes h2 { margin-top: 8px; color: #173b28; font-size: 30px; }
.sh-cheese-notes > p { margin-top: 10px; color: #5f675f; font-size: 14px; }
.sh-cheese-notes dl { margin-top: 22px; display: grid; grid-template-columns: repeat(3, 1fr); border-top: 1px solid #cbc8c1; border-bottom: 1px solid #cbc8c1; }
.sh-cheese-notes dl > div { padding: 14px 12px 14px 0; }
.sh-cheese-notes dt { color: #747a74; font-size: 12px; }
.sh-cheese-notes dd { margin: 5px 0 0; color: #173b28; font-size: 12px; font-weight: 700; }
.sh-cheese-notes > div { margin-top: 22px; display: flex; align-items: center; justify-content: space-between; }
.sh-cheese-notes > div > b { font-size: 18px; }
.sh-cheese-notes > div > button { height: 42px; padding: 0 18px; border: 0; background: #a92728; color: #fff; font-weight: 700; }
.sh-provenance-timeline { height: 256px; padding: 30px 48px; display: grid; grid-template-columns: repeat(4, 1fr); background: #173b28; color: #fff; }
.sh-provenance-timeline > div { padding: 10px 28px 0 0; border-right: 1px solid #55705f; }
.sh-provenance-timeline > div + div { padding-left: 28px; }
.sh-provenance-timeline span { color: #dcb76f; font-size: 12px; text-transform: uppercase; }
.sh-provenance-timeline b { display: block; margin-top: 25px; font: 21px Georgia, 'Times New Roman', serif; }
.sh-provenance-timeline p { margin-top: 15px; font-size: 12px; line-height: 18px; color: #dce5df; }

.sh-delivery-intro { height: 158px; }
.sh-delivery-flow { height: 610px; padding: 26px 48px; display: grid; grid-template-columns: 260px 1fr 290px; gap: 24px; background: #fff; }
.sh-delivery-controls { height: 558px; border-top: 2px solid #173b28; }
.sh-delivery-controls > div { padding: 18px 0; border-bottom: 1px solid #d8ddd8; }
.sh-delivery-controls span { color: #a92728; font-size: 12px; text-transform: uppercase; }
.sh-delivery-controls h2 { margin: 7px 0 12px; color: #173b28; font-size: 22px; }
.sh-delivery-controls button { width: 100%; height: 39px; margin-top: 7px; padding: 0 11px; border: 1px solid #c3cac4; background: #fff; color: #5f675f; text-align: left; font-size: 12px; }
.sh-delivery-controls button[aria-pressed="true"] { border-color: #173b28; background: #173b28; color: #fff; }
.sh-delivery-gallery { height: 558px; display: grid; grid-template-rows: 1fr 1fr; gap: 14px; }
.sh-delivery-gallery figure { min-height: 0; display: grid; grid-template-columns: 1fr 142px; overflow: hidden; }
.sh-delivery-gallery img { width: 100%; height: 100%; min-width: 0; min-height: 0; display: block; object-fit: cover; object-position: center; }
.sh-delivery-gallery figcaption { padding: 18px 14px; display: flex; flex-direction: column; justify-content: flex-end; background: #173b28; color: #fff; }
.sh-delivery-gallery figcaption b { font: 17px Georgia, 'Times New Roman', serif; }
.sh-delivery-gallery figcaption span { margin-top: 8px; font-size: 12px; line-height: 17px; }
.sh-delivery-summary { height: 558px; padding: 24px 22px; display: flex; flex-direction: column; background: #f4f1eb; border-top: 4px solid #a92728; }
.sh-delivery-summary > span { color: #a92728; font-size: 12px; text-transform: uppercase; }
.sh-delivery-summary h2 { margin-top: 10px; color: #173b28; font-size: 28px; }
.sh-delivery-summary > p { margin-top: 14px; padding-bottom: 10px; border-bottom: 1px solid #cbc8c1; color: #3f463f; font-size: 12px; line-height: 17px; }
.sh-delivery-summary dl { margin-top: auto; border-top: 1px solid #cbc8c1; }
.sh-delivery-summary dl > div { height: 37px; display: flex; align-items: center; justify-content: space-between; }
.sh-delivery-summary dt, .sh-delivery-summary dd { font-size: 12px; }
.sh-delivery-summary dd { margin: 0; font-weight: 700; }
.sh-delivery-summary > button { height: 46px; padding: 0 14px; display: flex; align-items: center; justify-content: space-between; border: 0; background: #a92728; color: #fff; font-weight: 700; }
.sh-delivery-conditions { height: 240px; display: grid; grid-template-columns: repeat(4, 1fr); grid-template-rows: 174px 66px; border-top: 1px solid #d8ddd8; background: #fff; }
.sh-delivery-conditions article { padding: 26px 26px 18px 48px; border-right: 1px solid #d8ddd8; }
.sh-delivery-conditions article > span { color: #a92728; font-size: 12px; text-transform: uppercase; }
.sh-delivery-conditions article > b { display: block; margin-top: 13px; color: #173b28; font: 19px Georgia, 'Times New Roman', serif; }
.sh-delivery-conditions article > p { margin-top: 11px; color: #5f675f; font-size: 12px; line-height: 17px; }
.sh-delivery-conditions footer { grid-column: 1 / -1; padding: 0 48px; display: grid; grid-template-columns: 190px 1fr 200px; align-items: center; background: #173b28; color: #fff; }
.sh-delivery-conditions footer b { font: 18px Georgia, 'Times New Roman', serif; }
.sh-delivery-conditions footer span { font-size: 12px; }
.sh-delivery-conditions footer span:last-child { text-align: right; color: #dcb76f; }
"""


_GIFT_SETS_SCRIPT = r"""
(() => {
  const assortments = {
    "Любой повод|любой бюджет": [
      ["Сырная классика", "Костромской · камамбер · тартин · мёд", "3 450 ₽"],
      ["Синий вечер", "Горгонзола · инжир · ржаной хлеб · орех", "4 250 ₽"],
      ["Тихое утро", "Шевр · ягоды · конфитюр · чиабатта", "2 900 ₽"]
    ],
    "Благодарность|до 3 000 ₽": [
      ["Тёплое спасибо", "Качотта · тартин · липовый мёд", "2 750 ₽"],
      ["Добрый знак", "Шевр · груша · орех · багет", "2 650 ₽"],
      ["К чаю", "Молодой сыр · хлеб с изюмом · конфитюр", "2 300 ₽"]
    ],
    "День рождения|до 5 000 ₽": [
      ["Праздничный стол", "Камамбер · резерв · тартин · мёд", "4 850 ₽"],
      ["Вечер друзей", "Горгонзола · качотта · хлеб · инжир", "4 600 ₽"],
      ["Три молока", "Коровий · козий · овечий сыр · багет", "4 950 ₽"]
    ]
  };
  let occasion = "Любой повод";
  let budget = "любой бюджет";
  const fallback = assortments["Любой повод|любой бюджет"];
  const setPressed = (selector, active) => {
    document.querySelectorAll(selector).forEach((button) => {
      button.setAttribute("aria-pressed", String(button === active));
    });
  };
  const update = () => {
    document.querySelector(".sh-gift-assortment-title").textContent =
      `Ассортимент · ${occasion} · ${budget}`;
    const rows = assortments[`${occasion}|${budget}`] ||
      (budget === "до 3 000 ₽" ? assortments["Благодарность|до 3 000 ₽"] : fallback);
    document.querySelectorAll(".sh-gift-products article").forEach((row, index) => {
      const item = rows[index];
      row.innerHTML = `<span>Набор 0${index + 1}</span><h3>${item[0]}</h3>` +
        `<p>${item[1]}</p><b>${item[2]}</b>`;
    });
  };
  document.querySelectorAll('[data-selectable="gift-occasion"]').forEach((button) => {
    button.addEventListener("click", () => {
      occasion = button.dataset.value;
      setPressed('[data-selectable="gift-occasion"]', button);
      update();
    });
  });
  document.querySelectorAll('[data-selectable="gift-budget"]').forEach((button) => {
    button.addEventListener("click", () => {
      budget = button.dataset.value;
      setPressed('[data-selectable="gift-budget"]', button);
      update();
    });
  });
})();
"""


_BUILDER_SCRIPT = r"""
(() => {
  const items = {
    "aged-cheese": {price: 690, weight: 200, quantity: 1},
    "camembert": {price: 580, weight: 180, quantity: 1},
    "bread": {price: 360, weight: 420, quantity: 1},
    "honey": {price: 430, weight: 200, quantity: 1}
  };
  let packageName = "Льняная сумка";
  let packagePrice = 550;
  const grouped = (value) => value.toLocaleString("ru-RU").replace(/\u00a0/g, " ");
  const money = (value) => `${grouped(value)} ₽`;
  const update = () => {
    let total = packagePrice;
    let weight = 0;
    let lines = 0;
    Object.entries(items).forEach(([key, item]) => {
      document.querySelector(`[data-quantity="${key}"]`).textContent = item.quantity;
      total += item.price * item.quantity;
      weight += item.weight * item.quantity;
      if (item.quantity > 0) lines += 1;
    });
    document.querySelector("[data-builder-lines]").textContent =
      `${lines} продукта · ${grouped(weight)} г`;
    document.querySelector("[data-builder-total]").textContent = `Итого ${money(total)}`;
    document.querySelector("[data-builder-package]").textContent =
      `${packageName} · ${money(packagePrice)}`;
    document.querySelector("[data-builder-weight]").textContent =
      `${grouped(weight)} г`;
  };
  document.querySelectorAll("[data-builder-action]").forEach((button) => {
    button.addEventListener("click", () => {
      const item = items[button.dataset.item];
      const delta = button.dataset.builderAction === "plus" ? 1 : -1;
      item.quantity = Math.max(0, Math.min(3, item.quantity + delta));
      update();
    });
  });
  document.querySelectorAll('[data-selectable="builder-package"]').forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll('[data-selectable="builder-package"]').forEach((option) => {
        option.setAttribute("aria-pressed", String(option === button));
      });
      packageName = button.dataset.name;
      packagePrice = Number(button.dataset.price);
      update();
    });
  });
})();
"""


_CHEESE_SCRIPT = r"""
(() => {
  const profiles = {
    "Костромская область|ореховый": {
      label: "Костромская область · выдержанный",
      name: "Костромской резерв",
      notes: "Ореховый, сливочный, долгое послевкусие",
      age: "8 месяцев", batch: "№ 48 / 12 кг",
      pairing: "Пшеничный тартин · липовый мёд", price: "690 ₽ / 200 г"
    },
    "Алтай|пикантный": {
      label: "Алтай · пикантный", name: "Алтайский томм",
      notes: "Пряное зерно, сухофрукты, выразительный финал",
      age: "11 месяцев", batch: "№ 19 / 9 кг",
      pairing: "Ржаной тартин · сливовый конфитюр", price: "820 ₽ / 200 г"
    },
    "Подмосковье|сливочный": {
      label: "Подмосковье · сливочный", name: "Камамбер утренний",
      notes: "Сливки, шампиньон, мягкая солоноватость",
      age: "24 дня", batch: "№ 61 / 7 кг",
      pairing: "Французский багет · груша", price: "640 ₽ / 180 г"
    }
  };
  let origin = "Костромская область";
  let flavor = "ореховый";
  const setPressed = (selector, active) => {
    document.querySelectorAll(selector).forEach((button) => {
      button.setAttribute("aria-pressed", String(button === active));
    });
  };
  const update = () => {
    const profile = profiles[`${origin}|${flavor}`] || {
      label: `${origin} · ${flavor}`, name: "Сыроварская партия",
      notes: flavor === "пикантный" ? "Пряное зерно, сухофрукты, выразительный финал" :
        flavor === "сливочный" ? "Сливки, шампиньон, мягкая солоноватость" :
        "Ореховый, сливочный, долгое послевкусие",
      age: "6 месяцев", batch: "№ 52 / 10 кг",
      pairing: flavor === "пикантный" ? "Ржаной тартин · сливовый конфитюр" :
        "Пшеничный тартин · липовый мёд", price: "720 ₽ / 200 г"
    };
    Object.entries(profile).forEach(([key, value]) => {
      document.querySelector(`[data-cheese-${key}]`).textContent = value;
    });
  };
  document.querySelectorAll('[data-selectable="cheese-origin"]').forEach((button) => {
    button.addEventListener("click", () => {
      origin = button.dataset.value;
      setPressed('[data-selectable="cheese-origin"]', button);
      update();
    });
  });
  document.querySelectorAll('[data-selectable="cheese-flavor"]').forEach((button) => {
    button.addEventListener("click", () => {
      flavor = button.dataset.value;
      setPressed('[data-selectable="cheese-flavor"]', button);
      update();
    });
  });
})();
"""


_DELIVERY_SCRIPT = r"""
(() => {
  const recipients = {
    self: {
      recipient: "Получатель: Я",
      address: "ул. Поварская, 18 · передать лично",
      card: "Открытка: без подписи"
    },
    gift: {
      recipient: "Получатель: Мария Орлова",
      address: "ул. Остоженка, 7 · позвонить у подъезда",
      card: "Открытка: «Спасибо за вашу заботу»"
    }
  };
  const slots = {
    today: "Сегодня · 18:00–20:00",
    morning: "Завтра · 10:00–12:00",
    evening: "Завтра · 18:00–20:00"
  };
  let recipient = "self";
  let slot = "today";
  const setPressed = (selector, active) => {
    document.querySelectorAll(selector).forEach((button) => {
      button.setAttribute("aria-pressed", String(button === active));
    });
  };
  const update = () => {
    const person = recipients[recipient];
    document.querySelector("[data-delivery-recipient]").textContent = person.recipient;
    document.querySelector("[data-delivery-address]").textContent = person.address;
    document.querySelector("[data-delivery-card]").textContent = person.card;
    document.querySelector("[data-delivery-slot]").textContent = slots[slot];
  };
  document.querySelectorAll('[data-selectable="delivery-recipient"]').forEach((button) => {
    button.addEventListener("click", () => {
      recipient = button.dataset.value;
      setPressed('[data-selectable="delivery-recipient"]', button);
      update();
    });
  });
  document.querySelectorAll('[data-selectable="delivery-slot"]').forEach((button) => {
    button.addEventListener("click", () => {
      slot = button.dataset.value;
      setPressed('[data-selectable="delivery-slot"]', button);
      update();
    });
  });
})();
"""


_BODY_RENDERERS = {
    "cover": _cover,
    "gift-sets": _gift_sets,
    "builder": _builder,
    "cheese": _cheese,
    "delivery": _delivery,
}

_ROUTE_SCRIPTS = {
    "cover": "",
    "gift-sets": _GIFT_SETS_SCRIPT,
    "builder": _BUILDER_SCRIPT,
    "cheese": _CHEESE_SCRIPT,
    "delivery": _DELIVERY_SCRIPT,
}


def render(
    project: ProjectSpec,
    shot: ShotSpec,
    assets: Mapping[str, str],
) -> RenderedPage:
    """Render one Syr Hleb route with only its owned image sources."""
    if project.slug != "syr-hleb":
        raise KeyError(f"syr-hleb renderer does not support {project.slug}")
    try:
        body_renderer = _BODY_RENDERERS[shot.key]
    except KeyError as exc:
        raise ValueError(f"syr-hleb unknown route: {shot.key}") from exc

    owned = _owned_assets(shot.key, assets)
    html = (
        f'<div class="sh-page" data-site="syr-hleb" data-route="{escape_html(shot.key)}">'
        f"{_header(shot.key)}{body_renderer(owned)}</div>"
    )
    return RenderedPage(html=html, css=_CSS, scripts=_ROUTE_SCRIPTS[shot.key])
