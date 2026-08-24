"""Dedicated renderer for the Berezhny Pereezd portfolio concept."""

from collections.abc import Mapping
from html import escape

from ..icons import icon
from ..models import ProjectSpec, ShotSpec
from .runtime import RenderedPage


def _header(active: str) -> str:
    links = (
        ("apartment-moving", "Квартирный переезд"),
        ("calculator", "Калькулятор"),
        ("packing", "Упаковка"),
        ("route", "Маршрут"),
    )
    nav = "".join(
        f'<a href="#" class="{"is-active" if key == active else ""}">{label}</a>'
        for key, label in links
    )
    return (
        '<header class="bp-header"><div class="bp-header-main">'
        '<a class="bp-brand" href="#"><span class="bp-box-mark"><i></i></span>'
        '<span><strong>Бережный</strong><b>переезд</b><small>переезды по Москве и области</small></span></a>'
        f'<nav>{nav}</nav><div class="bp-today"><span>Свободное окно сегодня</span><b>16:30</b></div>'
        '<div class="bp-phone"><b>+7 (495) 120-62-20</b><span>расчёт и диспетчерская</span></div>'
        '<button class="bp-header-cta" type="button">Рассчитать переезд</button></div>'
        '<div class="bp-trust"><b>Фиксируем стоимость до погрузки</b><span>Материальная ответственность по договору</span>'
        '<span>Оплата после расстановки мебели</span><span>Бригады со стажем от 5 лет</span></div></header>'
    )


def _cover(assets: Mapping[str, str]) -> str:
    photo = assets["moving_van"]
    return (
        '<main class="bp-route bp-cover">'
        '<section class="bp-cover-grid"><div class="bp-cover-copy">'
        '<span class="bp-open-slot">Сегодня есть окно на 16:30</span>'
        '<h1>Переезд квартиры без суеты и повреждений</h1>'
        '<p>Приедем вовремя, защитим мебель, подпишем опись и расставим всё в новой квартире.</p>'
        '<div class="bp-cover-points"><span>Цена известна заранее</span><span>Коробки привезём</span><span>Ответим за вещи</span></div>'
        '<button class="bp-primary" type="button">Получить точный расчёт '
        f'{icon("arrow-right", size=19)}</button></div>'
        '<figure class="bp-cover-photo"><img src="'
        f'{photo}" alt="Грузчики загружают мебель в фирменный фургон">'
        '<figcaption><b>Машина и бригада закрепляются за заказом</b><span>Не объединяем несколько переездов в один рейс</span></figcaption></figure>'
        '<aside class="bp-cover-quote"><span>БЫСТРЫЙ РАСЧЁТ</span><h2>Что перевозим?</h2>'
        '<div class="bp-mode" aria-label="Способ расчёта">'
        '<button type="button" data-selectable="cover-mode" data-value="rooms" aria-pressed="true">По комнатам</button>'
        '<button type="button" data-selectable="cover-mode" data-value="volume" aria-pressed="false">По объёму</button></div>'
        '<div class="bp-quote-fields"><label>Откуда<input type="text" value="ул. Новаторов, 18"></label>'
        '<label>Куда<input type="text" value="Ленинский пр-т, 96"></label>'
        '<label>Дата<input type="text" value="26 августа"></label><label>Этажи<input type="text" value="8 → 12"></label></div>'
        '<div class="bp-cover-result" data-cover-quote><span>Предварительная стоимость</span><b data-cover-price>от 15 900 ₽</b>'
        '<dl><div><dt>Объём</dt><dd data-cover-volume>2 комнаты</dd></div><div><dt>Машина</dt><dd data-cover-truck>Газель 3 м</dd></div>'
        '<div><dt>Бригада</dt><dd data-cover-team>2 грузчика</dd></div><div><dt>Погрузка</dt><dd>16:30–17:00</dd></div></dl></div>'
        '<button class="bp-orange" type="button">Зафиксировать расчёт</button><small>Точную цену подтвердим после короткой описи.</small></aside></section>'
        '<section class="bp-five-steps"><div><span>01</span><b>Опись</b><p>Фиксируем мебель, коробки и хрупкие места.</p></div>'
        '<div><span>02</span><b>Упаковка</b><p>Защищаем углы, фасады, стекло и технику.</p></div><div><span>03</span><b>Погрузка</b><p>Маркируем места по комнатам новой квартиры.</p></div>'
        '<div><span>04</span><b>Маршрут</b><p>Заранее проверяем парковку и подъезды.</p></div><div><span>05</span><b>Расстановка</b><p>Собираем мебель и сверяем опись.</p></div></section>'
        '<section class="bp-cover-bottom"><div><span>Пять шагов до новой квартиры</span><h2>Один координатор от заявки до последней коробки</h2></div>'
        '<p><b>Стоимость не меняется,</b> если состав вещей и адреса совпадают с описью.</p>'
        '<p><b>Повреждение фиксируем сразу:</b> акт, фото и компенсация по договору.</p></section>'
        '</main>'
    )


def _apartment(assets: Mapping[str, str]) -> str:
    photo = assets["packed_living_room"]
    return (
        '<main class="bp-route bp-apartment">'
        '<section class="bp-apartment-intro"><div><span>ПЕРЕЕЗД ПОД КЛЮЧ</span>'
        '<h1>Квартирный переезд с ответственностью за каждую вещь</h1>'
        '<p>Составляем опись, закрепляем машину и выдаём старшему бригады маршрутный лист.</p></div>'
        f'<img src="{photo}" alt="Гостиная с аккуратно упакованной мебелью и коробками"></section>'
        '<section class="bp-apartment-work"><aside class="bp-package-list"><h2>Выберите пакет</h2>'
        '<button type="button" data-selectable="move-package" data-value="base" aria-pressed="true"><b>Переезд</b><span>Машина + грузчики</span><strong>от 15 900 ₽</strong></button>'
        '<button type="button" data-selectable="move-package" data-value="care" aria-pressed="false"><b>С упаковкой</b><span>Материалы и опись</span><strong>от 24 900 ₽</strong></button>'
        '<button type="button" data-selectable="move-package" data-value="full" aria-pressed="false"><b>Под ключ</b><span>Разборка и расстановка</span><strong>от 36 800 ₽</strong></button></aside>'
        '<div class="bp-inventory"><div class="bp-section-head"><span>Опись комнаты</span><b>Кухня-гостиная · 18 мест</b></div>'
        '<div class="bp-inventory-row"><b>Диван и кресло</b><span>2 места · защитный чехол</span><strong>в описи</strong></div>'
        '<div class="bp-inventory-row"><b>Телевизор 55″</b><span>1 место · жёсткий короб</span><strong>хрупкое</strong></div>'
        '<div class="bp-inventory-row"><b>Стол и 4 стула</b><span>5 мест · разборка</span><strong>маркировка</strong></div>'
        '<div class="bp-inventory-row"><b>Коробки</b><span>10 мест · комнаты А/Б</span><strong>пломбы</strong></div>'
        '<div class="bp-inventory-total"><span>Выбранный пакет</span><b data-package-name>Переезд · 2 грузчика + Газель 3 м</b>'
        '<p data-package-scope>Погрузка, перевозка и расстановка по комнатам.</p></div></div>'
        '<aside class="bp-crew"><span>ЗАКРЕПЛЁННАЯ БРИГАДА</span><h2>Экипаж № 12</h2><p>Старший: Илья Воронцов · 7 лет в переездах</p>'
        '<dl><div><dt>Грузчики</dt><dd data-package-crew>2</dd></div><div><dt>Машина</dt><dd data-package-truck>Газель 3 м</dd></div><div><dt>Страховка</dt><dd>300 000 ₽</dd></div></dl>'
        '<button class="bp-primary" type="button">Получить маршрутный лист</button></aside></section>'
        '<section class="bp-day-timeline"><div><span>План переезда по времени</span><h2>26 августа · без второго рейса</h2></div>'
        '<ol><li><b>09:00</b><span>Бригада и упаковка</span></li><li><b>10:30</b><span>Погрузка по описи</span></li>'
        '<li><b>12:20</b><span>Маршрут 18 км</span></li><li><b>13:10</b><span>Подъём и расстановка</span></li><li><b>15:30</b><span>Приёмка по описи</span></li></ol></section>'
        '</main>'
    )


def _calculator(assets: Mapping[str, str]) -> str:
    photo = assets["boxes_detail"]
    return (
        '<main class="bp-route bp-calculator">'
        '<section class="bp-calc-intro"><div><span>РАСЧЁТ БЕЗ ТЕЛЕФОНА</span><h1>Рассчитайте переезд до приезда оценщика</h1>'
        '<p>Комнаты, этажи, лифт и упаковка сразу влияют на бригаду, машину и время.</p></div>'
        f'<img src="{photo}" alt="Промаркированные коробки и защитные материалы для переезда"></section>'
        '<section class="bp-calc-work"><div class="bp-calc-controls"><div class="bp-calc-mode"><span>Способ расчёта</span>'
        '<button type="button" data-selectable="calc-mode" data-value="rooms" aria-pressed="true">По комнатам</button><button type="button" data-selectable="calc-mode" data-value="volume" aria-pressed="false">По объёму</button></div>'
        '<div class="bp-control-grid"><div class="bp-stepper" data-stepper="rooms"><span data-stepper-label>Комнаты</span><div><button type="button" data-action="minus">−</button><b data-room-count>2</b><button type="button" data-action="plus">+</button></div></div>'
        '<label>Расстояние<input data-distance type="range" min="5" max="40" value="18"><b data-distance-label>18 км</b></label>'
        '<label>Этаж отправления<input data-origin-floor type="number" min="1" max="60" value="8"></label><label>Этаж назначения<input data-destination-floor type="number" min="1" max="60" value="12"></label></div>'
        '<fieldset><legend>Лифт на адресах</legend><div class="bp-segments">'
        '<button type="button" data-selectable="lift" data-value="both" aria-pressed="true">Есть на обоих</button><button type="button" data-selectable="lift" data-value="one" aria-pressed="false">Только на одном</button>'
        '<button type="button" data-selectable="lift" data-value="none" aria-pressed="false">Лифта нет</button></div></fieldset>'
        '<div class="bp-extra-list"><label><input type="checkbox" data-extra="packing"> Упаковка вещей</label><label><input type="checkbox" data-extra="assembly"> Разборка мебели</label>'
        '<label><input type="checkbox" data-extra="fragile"> Отдельная упаковка стекла</label></div>'
        '<div class="bp-route-fields"><label>Откуда<input data-origin-address type="text" value="Москва, Новаторы"></label><label>Куда<input data-destination-address type="text" value="Москва, Ленинский"></label><label>Дата<input data-move-date type="text" value="26 августа"></label></div></div>'
        '<aside class="bp-move-summary" data-move-summary><span>ВАШ ПЕРЕЕЗД</span><h2 data-summary-title>2 комнаты · 18 км</h2>'
        '<b data-summary-price>17 900 ₽</b><dl><div><dt>Бригада</dt><dd data-summary-team>2 грузчика</dd></div><div><dt>Машина</dt><dd data-summary-truck>Газель 3 м</dd></div>'
        '<div><dt>Время</dt><dd data-summary-duration>4–5 часов</dd></div><div><dt>Погрузка</dt><dd>16:30–17:00</dd></div></dl>'
        '<div class="bp-slot"><span>Ближайшее окно погрузки</span><span data-summary-route>Новаторы → Ленинский</span><b data-summary-slot>26 августа · 16:30</b></div><button class="bp-orange" type="button">Закрепить расчёт</button>'
        '<small>Цена не изменится при совпадении с описью.</small></aside></section>'
        '<section class="bp-breakdown"><div><span>Состав расчёта</span><h2>Платите за понятные операции</h2></div>'
        '<div><b>Машина и подача</b><strong data-breakdown-value="vehicle">6 500 ₽</strong><p data-breakdown-route>Газель, топливо, 18 км маршрута.</p></div><div><b>Работа бригады</b><strong data-breakdown-value="crew">9 400 ₽</strong><p>Погрузка, перевозка, расстановка.</p></div>'
        '<div><b>Доступ и резерв</b><strong data-breakdown-value="access">2 000 ₽</strong><p data-breakdown-access>30 минут на парковку и лифты.</p></div></section>'
        '</main>'
    )


def _packing(assets: Mapping[str, str]) -> str:
    photo = assets["packer_portrait"]
    return (
        '<main class="bp-route bp-packing">'
        '<section class="bp-packing-intro"><div><span>УПАКОВКА С ОПИСЬЮ</span><h1>Упакуем вещи по описи, а не на глаз</h1>'
        '<p>Каждое хрупкое место получает номер, фотографию и пломбу до погрузки.</p></div>'
        f'<img src="{photo}" alt="Специалист по упаковке готовит вещи к переезду"></section>'
        '<section class="bp-packing-work"><aside class="bp-materials"><h2>Материалы на 2 комнаты</h2>'
        '<div><span>Коробка 60×40</span><b>20 шт.</b></div><div><span>Пузырчатая плёнка</span><b>25 м</b></div><div><span>Стрейч-плёнка</span><b>4 рулона</b></div>'
        '<div><span>Уголки и чехлы</span><b>12 комплектов</b></div><button class="bp-primary" type="button">Добавить материалы</button></aside>'
        '<div class="bp-fragile"><div class="bp-section-head"><span>Что требует отдельной защиты?</span><b>Выберите хрупкие группы</b></div>'
        '<label><input type="checkbox" data-fragile="dishes"> Посуда и стекло <span>+4 места</span></label><label><input type="checkbox" data-fragile="art"> Картины и зеркала <span>+3 места</span></label>'
        '<label><input type="checkbox" data-fragile="tech"> Техника и мониторы <span>+2 места</span></label><label><input type="checkbox" data-fragile="plants"> Растения <span>+3 места</span></label>'
        '<div class="bp-packing-summary" data-packing-summary><span>Итог упаковки</span><b data-boxes>20 коробок</b><strong data-fragile-count>0 хрупких мест</strong><p data-seals>Пломбы: 0</p></div></div>'
        '<aside class="bp-label-example"><span>Маркировка коробки</span><div class="bp-label-paper"><b>№ A-14</b><strong>КУХНЯ</strong><p>Посуда · верх</p><i>ХРУПКОЕ</i></div>'
        '<p>Номер совпадает с описью и местом в машине.</p></aside></section>'
        '<section class="bp-packing-sequence"><div><span>01</span><b>Фото и опись</b><p>Состояние до упаковки.</p></div><div><span>02</span><b>Защита по типу</b><p>Короб, плёнка или жёсткий каркас.</p></div>'
        '<div><span>03</span><b>Номер и пломба</b><p>Место попадает в маршрутный лист.</p></div><div><span>04</span><b>Приёмка</b><p>Сверка номера и состояния.</p></div></section>'
        '<section class="bp-responsibility"><div><span>Ответственность за упаковку</span><h2>Мы отвечаем за вещи, которые упаковали</h2></div>'
        '<p><b>Фото до погрузки</b><span>прикладывается к электронной описи.</span></p><p><b>Компенсация по договору</b><span>без спора о том, кто упаковывал.</span></p></section>'
        '</main>'
    )


def _route(assets: Mapping[str, str]) -> str:
    map_photo = assets["route_map_photo"]
    new_home = assets["new_home"]
    return (
        '<main class="bp-route bp-route-page">'
        '<section class="bp-route-intro"><div><span>МАРШРУТНЫЙ ЛИСТ № 2841</span><h1>Маршрут переезда без сюрпризов во дворе</h1>'
        '<p>Проверяем парковку, лифты и время въезда до того, как машина выйдет на линию.</p></div>'
        f'<img src="{map_photo}" alt="Карта маршрута и документы для квартирного переезда"></section>'
        '<section class="bp-route-work"><div class="bp-address-sheet"><div><span>ТОЧКА А · ПОГРУЗКА</span><h2>ул. Новаторов, 18</h2><p>8 этаж · грузовой лифт · въезд со двора</p></div>'
        '<div><span>ТОЧКА Б · РАЗГРУЗКА</span><h2>Ленинский проспект, 96</h2><p>12 этаж · лифт по записи · 18 км</p></div>'
        '<div class="bp-route-line"><i></i><b data-route-distance>18 км · 42 минуты в пути</b><strong>Газель 5 м</strong></div></div>'
        '<aside class="bp-checkpoints"><h2>Контрольные точки маршрута</h2>'
        '<label><input type="checkbox" data-checkpoint="parking"> Парковка у нового дома согласована</label><label><input type="checkbox" data-checkpoint="elevator" checked> Грузовой лифт забронирован</label>'
        '<label><input type="checkbox" data-checkpoint="arch" checked> Высота арки проверена</label><label><input type="checkbox" data-checkpoint="concierge" checked> Телефон консьержа получен</label>'
        '<fieldset><legend>Плановое прибытие</legend><div class="bp-route-slots"><button type="button" data-selectable="route-slot" data-value="11:00" aria-pressed="true">11:00</button>'
        '<button type="button" data-selectable="route-slot" data-value="11:30" aria-pressed="false">11:30</button><button type="button" data-selectable="route-slot" data-value="12:00" aria-pressed="false">12:00</button></div></fieldset></aside>'
        '<aside class="bp-route-summary" data-route-summary><span>МАШИНА НАЗНАЧЕНА</span><h2>Экипаж № 12</h2><b>Газель 5 м · бригада 3 человека</b>'
        '<p data-parking-status>Парковка требует подтверждения</p><div><span>Подача</span><strong>09:00</strong></div><div data-arrival-row><span>Прибытие к новому адресу</span><strong data-arrival>11:00</strong></div>'
        '<button class="bp-orange" type="button">Подтвердить маршрут</button></aside></section>'
        '<section class="bp-arrival-band"><figure>'
        f'<img src="{new_home}" alt="Светлая новая квартира после завершённого переезда"></figure>'
        '<div><span>Подтверждение прибытия</span><h2>Новая квартира готова к разгрузке</h2><p>Координатор сверит доступ и отправит заказчику сообщение за 30 минут.</p></div>'
        '<ol><li><b>09:00</b><span>Подача машины</span></li><li><b>10:20</b><span>Выезд по описи</span></li><li><b data-timeline-time>11:00</b><span data-timeline-arrival>Прибытие и парковка</span></li><li><b>13:30</b><span>Приёмка вещей</span></li></ol></section>'
        '</main>'
    )


_CSS = r"""
.bp-page, .bp-page * { box-sizing: border-box; }
.bp-page { width: 100%; height: 1120px; overflow: hidden; background: #fff; color: #202833; font-family: Arial, Helvetica, sans-serif; font-size: 14px; letter-spacing: 0; }
.bp-page button, .bp-page input, .bp-page select { font: inherit; letter-spacing: 0; }
.bp-page button { cursor: pointer; }
.bp-page h1, .bp-page h2, .bp-page p, .bp-page figure, .bp-page dl, .bp-page fieldset { margin: 0; }
.bp-page h1, .bp-page h2 { font-weight: 800; }
.bp-header { height: 116px; background: #fff; border-bottom: 1px solid #d5dce3; }
.bp-header-main { height: 80px; padding: 0 42px; display: grid; grid-template-columns: 250px 1fr 160px 230px 180px; gap: 22px; align-items: center; }
.bp-brand { display: flex; align-items: center; gap: 12px; text-decoration: none; }
.bp-box-mark { width: 48px; height: 42px; position: relative; display: block; border: 4px solid #1768cf; border-top: 0; }
.bp-box-mark::before { content: ""; position: absolute; width: 31px; height: 31px; left: 4px; top: -16px; border-left: 5px solid #ff7a18; border-top: 5px solid #ff7a18; transform: rotate(45deg); }
.bp-box-mark i { position: absolute; width: 14px; height: 20px; right: 5px; bottom: 0; background: #ff7a18; }
.bp-brand strong, .bp-brand b, .bp-brand small { display: block; }
.bp-brand strong { color: #1768cf; font-size: 20px; line-height: 18px; }
.bp-brand b { color: #ff7a18; font-size: 20px; line-height: 20px; }
.bp-brand small { color: #63707d; font-size: 12px; margin-top: 3px; }
.bp-header nav { display: flex; justify-content: center; gap: 30px; }
.bp-header nav a { padding: 28px 0 25px; border-bottom: 3px solid transparent; color: #273441; text-decoration: none; font-size: 13px; font-weight: 700; }
.bp-header nav a.is-active { color: #1768cf; border-bottom-color: #ff7a18; }
.bp-today, .bp-phone { display: flex; flex-direction: column; gap: 4px; }
.bp-today span, .bp-phone span { color: #63707d; font-size: 12px; }
.bp-today b { color: #15834d; font-size: 16px; }
.bp-phone b { color: #17345e; font-size: 18px; }
.bp-header-cta, .bp-primary, .bp-orange { border: 0; display: inline-flex; align-items: center; justify-content: center; gap: 8px; font-weight: 800; }
.bp-header-cta { height: 46px; color: #fff; background: #1768cf; }
.bp-trust { height: 36px; padding: 0 42px; display: grid; grid-template-columns: 1.25fr 1fr 1fr .8fr; align-items: center; background: #17345e; color: #fff; font-size: 12px; }
.bp-trust b { color: #ffb575; }
.bp-trust span { padding-left: 24px; border-left: 1px solid #527096; }
.bp-route { height: 1004px; min-height: 0; overflow: hidden; }
.bp-primary { min-height: 48px; padding: 0 22px; color: #fff; background: #1768cf; }
.bp-orange { min-height: 48px; padding: 0 22px; color: #fff; background: #ff7a18; }
.bp-open-slot { display: inline-block; padding-left: 15px; border-left: 4px solid #15834d; color: #15834d; font-size: 13px; font-weight: 800; }

.bp-cover-grid { height: 570px; display: grid; grid-template-columns: 1fr .9fr .72fr; background: #fff; }
.bp-cover-copy { padding: 52px 36px 40px 42px; }
.bp-cover-copy h1 { margin: 22px 0 18px; color: #17345e; font-size: 44px; line-height: 1.06; }
.bp-cover-copy > p { max-width: 560px; color: #5d6873; font-size: 17px; line-height: 1.5; }
.bp-cover-points { margin: 28px 0; display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.bp-cover-points span { padding: 10px 0 10px 24px; position: relative; border-bottom: 1px solid #d5dce3; font-size: 13px; font-weight: 700; }
.bp-cover-points span::before { content: "✓"; position: absolute; left: 0; color: #15834d; }
.bp-cover-photo { position: relative; overflow: hidden; background: #dbe2e7; }
.bp-cover-photo img { width: 100%; height: 100%; object-fit: cover; }
.bp-cover-photo figcaption { position: absolute; left: 0; right: 0; bottom: 0; padding: 17px 20px; background: #fff; border-top: 4px solid #ff7a18; }
.bp-cover-photo figcaption b, .bp-cover-photo figcaption span { display: block; }
.bp-cover-photo figcaption span { margin-top: 5px; color: #63707d; font-size: 12px; }
.bp-cover-quote { padding: 30px 28px; background: #eef5fd; border-left: 1px solid #cbd9e7; }
.bp-cover-quote > span { color: #1768cf; font-size: 12px; font-weight: 800; }
.bp-cover-quote h2 { margin: 9px 0 15px; font-size: 24px; color: #17345e; }
.bp-mode { display: grid; grid-template-columns: 1fr 1fr; }
.bp-mode button { min-height: 41px; border: 1px solid #9eb6ce; background: #fff; color: #405268; font-size: 12px; }
.bp-mode button[aria-pressed="true"] { color: #fff; background: #1768cf; border-color: #1768cf; }
.bp-quote-fields { margin-top: 13px; display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.bp-quote-fields label { color: #586778; font-size: 12px; }
.bp-quote-fields input { width: 100%; height: 39px; margin-top: 5px; padding: 0 9px; border: 1px solid #a8bacb; background: #fff; }
.bp-cover-result { margin-top: 16px; padding: 15px; background: #fff; border-left: 4px solid #ff7a18; }
.bp-cover-result > span { color: #63707d; font-size: 12px; }
.bp-cover-result > b { display: block; margin-top: 3px; color: #17345e; font-size: 26px; }
.bp-cover-result dl { margin-top: 11px; display: grid; grid-template-columns: 1fr 1fr; }
.bp-cover-result dl div { padding: 8px 0; border-top: 1px solid #d5dce3; }
.bp-cover-result dt { color: #63707d; font-size: 12px; }
.bp-cover-result dd { margin: 4px 0 0; font-weight: 800; }
.bp-cover-quote .bp-orange { width: 100%; margin-top: 14px; }
.bp-cover-quote small { display: block; margin-top: 8px; color: #63707d; font-size: 12px; }
.bp-five-steps { height: 250px; display: grid; grid-template-columns: repeat(5, 1fr); background: #fff; border-top: 1px solid #d5dce3; border-bottom: 1px solid #d5dce3; }
.bp-five-steps div { padding: 35px 28px 24px 42px; border-right: 1px solid #d5dce3; }
.bp-five-steps span { color: #ff7a18; font-size: 12px; font-weight: 800; }
.bp-five-steps b { display: block; margin: 13px 0 10px; color: #1768cf; font-size: 18px; }
.bp-five-steps p { color: #63707d; line-height: 1.45; }
.bp-cover-bottom { height: 184px; padding: 0 42px; display: grid; grid-template-columns: 1.25fr 1fr 1fr; align-items: center; background: #17345e; color: #fff; }
.bp-cover-bottom > div, .bp-cover-bottom > p { padding-right: 30px; }
.bp-cover-bottom > div span { color: #ffb575; font-size: 12px; font-weight: 800; }
.bp-cover-bottom h2 { margin-top: 8px; font-size: 24px; }
.bp-cover-bottom > p { padding: 22px 30px; border-left: 1px solid #557093; color: #dbe5f0; line-height: 1.5; }
.bp-cover-bottom > p b { color: #fff; }

.bp-apartment-intro { height: 220px; min-height: 0; overflow: hidden; display: grid; grid-template-columns: minmax(0, 1fr) 530px; background: #eef5fd; border-bottom: 1px solid #cdd9e5; }
.bp-apartment-intro > div, .bp-calc-intro > div, .bp-packing-intro > div, .bp-route-intro > div { padding: 36px 42px; }
.bp-apartment-intro span, .bp-calc-intro span, .bp-packing-intro span, .bp-route-intro span { color: #ff7a18; font-size: 12px; font-weight: 800; }
.bp-apartment-intro h1, .bp-calc-intro h1, .bp-packing-intro h1, .bp-route-intro h1 { margin: 10px 0; color: #17345e; font-size: 34px; line-height: 1.1; }
.bp-apartment-intro p, .bp-calc-intro p, .bp-packing-intro p, .bp-route-intro p { color: #5e6975; font-size: 15px; line-height: 1.45; }
.bp-apartment-intro img { display: block; width: 100%; height: 220px; min-height: 0; max-height: 220px; object-fit: cover; }
.bp-calc-intro img, .bp-packing-intro img, .bp-route-intro img { display: block; width: 100%; height: 190px; min-height: 0; max-height: 190px; object-fit: cover; }
.bp-apartment-work { height: 540px; display: grid; grid-template-columns: 315px 1fr 350px; background: #fff; }
.bp-package-list { padding: 28px 25px 24px 42px; background: #f4e6d6; }
.bp-package-list h2 { margin-bottom: 15px; font-size: 20px; }
.bp-package-list button { width: 100%; min-height: 120px; padding: 15px; border: 0; border-top: 1px solid #ceb99f; background: transparent; color: #253444; text-align: left; }
.bp-package-list button b, .bp-package-list button span, .bp-package-list button strong { display: block; }
.bp-package-list button b { font-size: 16px; }
.bp-package-list button span { margin-top: 6px; color: #63707d; font-size: 12px; }
.bp-package-list button strong { margin-top: 9px; color: #1768cf; }
.bp-package-list button[aria-pressed="true"] { background: #1768cf; color: #fff; }
.bp-package-list button[aria-pressed="true"] span, .bp-package-list button[aria-pressed="true"] strong { color: #dbeafa; }
.bp-inventory { padding: 28px 32px; }
.bp-section-head { display: flex; justify-content: space-between; align-items: end; padding-bottom: 15px; border-bottom: 3px solid #17345e; }
.bp-section-head span { color: #63707d; font-size: 12px; }
.bp-section-head b { color: #1768cf; font-size: 18px; }
.bp-inventory-row { min-height: 72px; display: grid; grid-template-columns: 1fr 1.2fr 100px; gap: 15px; align-items: center; border-bottom: 1px solid #d5dce3; }
.bp-inventory-row span { color: #63707d; font-size: 12px; }
.bp-inventory-row strong { color: #15834d; font-size: 12px; text-align: right; }
.bp-inventory-total { margin-top: 16px; padding: 14px 17px; background: #eef5fd; border-left: 4px solid #1768cf; }
.bp-inventory-total span { color: #63707d; font-size: 12px; }
.bp-inventory-total b { display: block; margin: 5px 0; color: #17345e; }
.bp-crew { padding: 32px 30px; background: #17345e; color: #fff; }
.bp-crew > span { color: #ffb575; font-size: 12px; font-weight: 800; }
.bp-crew h2 { margin: 10px 0 8px; font-size: 26px; }
.bp-crew > p { color: #cbd9e7; line-height: 1.4; }
.bp-crew dl { margin: 25px 0; border-top: 1px solid #557093; }
.bp-crew dl div { min-height: 54px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #557093; }
.bp-crew dt { color: #b7c9dc; }
.bp-crew dd { margin: 0; font-weight: 800; }
.bp-crew .bp-primary { width: 100%; background: #ff7a18; }
.bp-day-timeline { height: 244px; padding: 0 42px; display: grid; grid-template-columns: 1.35fr 3fr; background: #202833; color: #fff; }
.bp-day-timeline > div { padding: 40px 30px 25px 0; border-right: 1px solid #4d5964; }
.bp-day-timeline > div span { color: #ffb575; font-size: 12px; font-weight: 800; }
.bp-day-timeline h2 { margin-top: 10px; font-size: 25px; }
.bp-day-timeline ol { list-style: none; padding: 0; margin: 0; display: grid; grid-template-columns: repeat(5, 1fr); }
.bp-day-timeline li { padding: 42px 22px; border-right: 1px solid #4d5964; }
.bp-day-timeline li b, .bp-day-timeline li span { display: block; }
.bp-day-timeline li b { color: #ff7a18; font-size: 17px; }
.bp-day-timeline li span { margin-top: 14px; line-height: 1.4; }

.bp-calc-intro, .bp-packing-intro, .bp-route-intro { height: 190px; min-height: 0; overflow: hidden; display: grid; grid-template-columns: minmax(0, 1fr) 470px; background: #fff; border-bottom: 1px solid #d5dce3; }
.bp-calc-work { height: 580px; display: grid; grid-template-columns: 1fr 410px; background: #eef5fd; }
.bp-calc-controls { padding: 27px 36px 22px 42px; }
.bp-calc-mode { display: grid; grid-template-columns: 160px 1fr 1fr; align-items: center; }
.bp-calc-mode > span { color: #5f6c79; font-size: 12px; font-weight: 700; }
.bp-calc-mode button { min-height: 40px; border: 1px solid #a9b9ca; background: #fff; }
.bp-calc-mode button[aria-pressed="true"] { color: #fff; background: #1768cf; border-color: #1768cf; }
.bp-control-grid { margin-top: 18px; display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; }
.bp-control-grid > div, .bp-control-grid > label { min-height: 95px; padding: 14px; background: #fff; border-top: 3px solid #1768cf; color: #5d6975; font-size: 12px; }
.bp-stepper > span { display: block; margin-bottom: 11px; }
.bp-stepper > div { display: grid; grid-template-columns: 38px 1fr 38px; align-items: center; }
.bp-stepper button { height: 34px; border: 1px solid #a9b9ca; background: #fff; font-size: 18px; }
.bp-stepper b { text-align: center; color: #17345e; font-size: 20px; }
.bp-control-grid input[type="range"] { width: 100%; margin: 9px 0 4px; }
.bp-control-grid input[type="number"] { width: 100%; height: 36px; margin-top: 10px; padding: 0 8px; border: 1px solid #a9b9ca; }
.bp-calc-controls fieldset { padding: 0; margin-top: 18px; border: 0; }
.bp-calc-controls legend { margin-bottom: 8px; color: #5d6975; font-size: 12px; font-weight: 700; }
.bp-segments { display: grid; grid-template-columns: repeat(3, 1fr); }
.bp-segments button { min-height: 42px; border: 1px solid #a9b9ca; background: #fff; }
.bp-segments button[aria-pressed="true"] { color: #fff; background: #17345e; border-color: #17345e; }
.bp-extra-list { margin-top: 18px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
.bp-extra-list label { padding: 13px; background: #fff; border: 1px solid #c6d3df; font-size: 12px; }
.bp-extra-list input { width: 16px; height: 16px; vertical-align: middle; margin-right: 7px; }
.bp-route-fields { margin-top: 18px; display: grid; grid-template-columns: 1fr 1fr .7fr; gap: 12px; }
.bp-route-fields label { color: #5d6975; font-size: 12px; }
.bp-route-fields input { width: 100%; height: 40px; margin-top: 6px; padding: 0 9px; border: 1px solid #a9b9ca; }
.bp-move-summary { padding: 26px 30px; background: #17345e; color: #fff; }
.bp-move-summary > span { color: #ffb575; font-size: 12px; font-weight: 800; }
.bp-move-summary h2 { min-height: 44px; margin: 7px 0 4px; font-size: 24px; }
.bp-move-summary > b { display: block; color: #fff; font-size: 32px; }
.bp-move-summary dl { margin: 14px 0; border-top: 1px solid #557093; }
.bp-move-summary dl div { min-height: 48px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #557093; }
.bp-move-summary dt { color: #bdcde0; }
.bp-move-summary dd { margin: 0; font-weight: 800; }
.bp-slot { padding: 14px; background: #234771; border-left: 4px solid #ff7a18; }
.bp-slot span, .bp-slot b { display: block; }
.bp-slot span { color: #c3d3e5; font-size: 12px; }
.bp-slot b { margin-top: 5px; }
.bp-move-summary .bp-orange { width: 100%; margin-top: 14px; }
.bp-move-summary small { display: block; margin-top: 9px; color: #b8cadc; font-size: 12px; }
.bp-breakdown { height: 234px; padding: 0 42px; display: grid; grid-template-columns: 1.25fr 1fr 1fr 1fr; background: #fff; }
.bp-breakdown > div { padding: 39px 28px; border-right: 1px solid #d5dce3; }
.bp-breakdown span { color: #ff7a18; font-size: 12px; font-weight: 800; }
.bp-breakdown h2 { margin-top: 9px; color: #17345e; font-size: 25px; }
.bp-breakdown b { color: #17345e; }
.bp-breakdown strong { display: block; margin-top: 8px; color: #1768cf; font-size: 18px; }
.bp-breakdown p { margin-top: 10px; color: #63707d; line-height: 1.4; }

.bp-packing-intro { background: #f4e6d6; }
.bp-packing-work { height: 500px; display: grid; grid-template-columns: 340px 1fr 350px; background: #fff; }
.bp-materials { padding: 28px 25px 24px 42px; background: #eef5fd; }
.bp-materials h2 { margin-bottom: 15px; color: #17345e; font-size: 20px; }
.bp-materials > div { min-height: 66px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #cbd9e5; }
.bp-materials > div span { color: #5d6975; }
.bp-materials > div b { color: #1768cf; }
.bp-materials .bp-primary { width: 100%; margin-top: 20px; }
.bp-fragile { padding: 27px 32px; }
.bp-fragile > label { min-height: 58px; display: grid; grid-template-columns: 28px 1fr auto; align-items: center; border-bottom: 1px solid #d5dce3; font-weight: 700; }
.bp-fragile > label input { width: 17px; height: 17px; }
.bp-fragile > label span { color: #63707d; font-size: 12px; }
.bp-packing-summary { margin-top: 14px; padding: 14px 17px; display: grid; grid-template-columns: 1.2fr 1fr 1fr 1fr; align-items: center; background: #17345e; color: #fff; }
.bp-packing-summary span { color: #bcd0e4; font-size: 12px; }
.bp-packing-summary strong { color: #ffb575; }
.bp-label-example { padding: 30px; background: #202833; color: #fff; }
.bp-label-example > span { color: #ffb575; font-size: 12px; font-weight: 800; }
.bp-label-paper { height: 270px; margin-top: 18px; padding: 25px; background: #fff; color: #202833; border: 5px solid #ff7a18; }
.bp-label-paper b, .bp-label-paper strong, .bp-label-paper p, .bp-label-paper i { display: block; }
.bp-label-paper b { color: #1768cf; font-size: 30px; }
.bp-label-paper strong { margin-top: 25px; font-size: 28px; }
.bp-label-paper p { margin-top: 12px; color: #5d6975; }
.bp-label-paper i { margin-top: 30px; padding: 10px; border: 3px solid #ff7a18; color: #ff7a18; font-style: normal; font-weight: 800; text-align: center; }
.bp-label-example > p { margin-top: 16px; color: #c3cbd3; line-height: 1.4; }
.bp-packing-sequence { height: 145px; display: grid; grid-template-columns: repeat(4, 1fr); background: #fff; border-top: 1px solid #d5dce3; }
.bp-packing-sequence div { padding: 25px 35px 20px 42px; border-right: 1px solid #d5dce3; }
.bp-packing-sequence span { color: #ff7a18; font-size: 12px; font-weight: 800; }
.bp-packing-sequence b { display: block; margin: 7px 0; color: #1768cf; }
.bp-packing-sequence p { color: #63707d; }
.bp-responsibility { height: 169px; padding: 0 42px; display: grid; grid-template-columns: 1.35fr 1fr 1fr; align-items: center; background: #17345e; color: #fff; }
.bp-responsibility > div span { color: #ffb575; font-size: 12px; font-weight: 800; }
.bp-responsibility h2 { margin-top: 8px; font-size: 24px; }
.bp-responsibility > p { padding: 24px 30px; border-left: 1px solid #557093; }
.bp-responsibility > p b, .bp-responsibility > p span { display: block; }
.bp-responsibility > p span { margin-top: 7px; color: #c2d2e2; }

.bp-route-intro { height: 190px; grid-template-columns: 1fr 500px; background: #eef5fd; }
.bp-route-work { height: 550px; display: grid; grid-template-columns: 1fr 390px 350px; background: #fff; }
.bp-address-sheet { padding: 28px 32px 24px 42px; }
.bp-address-sheet > div { min-height: 145px; padding: 20px 0; border-bottom: 1px solid #d5dce3; }
.bp-address-sheet > div span { color: #1768cf; font-size: 12px; font-weight: 800; }
.bp-address-sheet h2 { margin: 8px 0; color: #17345e; font-size: 23px; }
.bp-address-sheet p { color: #63707d; }
.bp-route-line { position: relative; display: grid !important; grid-template-columns: 1fr auto; align-items: center; }
.bp-route-line i { position: absolute; left: 0; right: 0; top: 30px; height: 4px; background: #1768cf; }
.bp-route-line b, .bp-route-line strong { position: relative; padding-top: 25px; background: #fff; color: #17345e; }
.bp-route-line b { padding-right: 15px; }
.bp-route-line strong { padding-left: 15px; }
.bp-checkpoints { padding: 28px 25px; background: #f4e6d6; }
.bp-checkpoints h2 { margin-bottom: 14px; font-size: 20px; }
.bp-checkpoints > label { min-height: 57px; display: flex; align-items: center; gap: 10px; border-bottom: 1px solid #cbb69d; font-size: 13px; }
.bp-checkpoints input { width: 17px; height: 17px; }
.bp-checkpoints fieldset { padding: 0; margin-top: 19px; border: 0; }
.bp-checkpoints legend { margin-bottom: 9px; color: #5d6975; font-size: 12px; font-weight: 700; }
.bp-route-slots { display: grid; grid-template-columns: repeat(3, 1fr); }
.bp-route-slots button { min-height: 41px; border: 1px solid #aa947c; background: #fff; }
.bp-route-slots button[aria-pressed="true"] { color: #fff; background: #1768cf; border-color: #1768cf; }
.bp-route-summary { padding: 32px 28px; background: #17345e; color: #fff; }
.bp-route-summary > span { color: #ffb575; font-size: 12px; font-weight: 800; }
.bp-route-summary h2 { margin: 8px 0; font-size: 25px; }
.bp-route-summary > b { display: block; min-height: 46px; color: #d8e7f4; line-height: 1.4; }
.bp-route-summary > p { min-height: 52px; margin: 18px 0; padding: 14px; background: #234771; border-left: 4px solid #ff7a18; }
.bp-route-summary > div { min-height: 55px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #557093; }
.bp-route-summary > div span { color: #bdd0e2; }
.bp-route-summary > div[data-arrival-row] { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 14px; }
.bp-route-summary > div[data-arrival-row] strong { white-space: nowrap; }
.bp-route-summary .bp-orange { width: 100%; margin-top: 20px; }
.bp-arrival-band { height: 264px; display: grid; grid-template-columns: 380px 420px 1fr; background: #202833; color: #fff; }
.bp-arrival-band figure { overflow: hidden; }
.bp-arrival-band img { width: 100%; height: 264px; object-fit: cover; }
.bp-arrival-band > div { padding: 43px 35px; border-right: 1px solid #4f5a65; }
.bp-arrival-band > div span { color: #ffb575; font-size: 12px; font-weight: 800; }
.bp-arrival-band h2 { margin: 9px 0 12px; font-size: 24px; }
.bp-arrival-band > div p { color: #c4cdd5; line-height: 1.5; }
.bp-arrival-band ol { list-style: none; padding: 24px 36px; margin: 0; display: grid; grid-template-columns: 1fr 1fr; }
.bp-arrival-band li { padding: 17px; border-bottom: 1px solid #4f5a65; }
.bp-arrival-band li:nth-child(odd) { border-right: 1px solid #4f5a65; }
.bp-arrival-band li b, .bp-arrival-band li span { display: block; }
.bp-arrival-band li b { color: #ff7a18; font-size: 12px; }
.bp-arrival-band li span { margin-top: 7px; }
"""


_COVER_SCRIPT = r"""
(() => {
  const quotes = {
    rooms: ["от 15 900 ₽", "2 комнаты", "Газель 3 м", "2 грузчика"],
    volume: ["от 18 700 ₽", "14 м³", "Газель 4 м", "3 грузчика"]
  };
  document.querySelectorAll('[data-selectable="cover-mode"]').forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll('[data-selectable="cover-mode"]').forEach((option) => option.setAttribute("aria-pressed", String(option === button)));
      const quote = quotes[button.dataset.value];
      document.querySelector("[data-cover-price]").textContent = quote[0];
      document.querySelector("[data-cover-volume]").textContent = quote[1];
      document.querySelector("[data-cover-truck]").textContent = quote[2];
      document.querySelector("[data-cover-team]").textContent = quote[3];
    });
  });
})();
"""


_APARTMENT_SCRIPT = r"""
(() => {
  const packages = {
    base: ["Переезд · 2 грузчика + Газель 3 м", "Погрузка, перевозка и расстановка по комнатам.", "2", "Газель 3 м"],
    care: ["С упаковкой · 3 грузчика + Газель 5 м", "Материалы, опись, упаковка, перевозка и расстановка.", "3", "Газель 5 м"],
    full: ["Под ключ · 4 специалиста + Газель 5 м", "Упаковка, разборка, перевозка, сборка и приёмка по описи.", "4", "Газель 5 м"]
  };
  document.querySelectorAll('[data-selectable="move-package"]').forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll('[data-selectable="move-package"]').forEach((option) => option.setAttribute("aria-pressed", String(option === button)));
      const value = packages[button.dataset.value];
      document.querySelector("[data-package-name]").textContent = value[0];
      document.querySelector("[data-package-scope]").textContent = value[1];
      document.querySelector("[data-package-crew]").textContent = value[2];
      document.querySelector("[data-package-truck]").textContent = value[3];
    });
  });
})();
"""


_CALCULATOR_SCRIPT = r"""
(() => {
  let mode = "rooms";
  let rooms = 2;
  let volume = 14;
  let lift = "both";
  const root = document.querySelector(".bp-page");
  const distanceInput = root.querySelector("[data-distance]");
  const originFloorInput = root.querySelector("[data-origin-floor]");
  const destinationFloorInput = root.querySelector("[data-destination-floor]");
  const dateInput = root.querySelector("[data-move-date]");
  const originInput = root.querySelector("[data-origin-address]");
  const destinationInput = root.querySelector("[data-destination-address]");
  const money = (value) => `${value.toLocaleString("ru-RU").replace(/\u00a0/g, " ")} ₽`;
  const shortAddress = (value) => value.split(",").slice(-1)[0].trim();
  const update = () => {
    const distance = Number(distanceInput.value) || 18;
    const originFloor = Math.max(1, Number(originFloorInput.value) || 1);
    const destinationFloor = Math.max(1, Number(destinationFloorInput.value) || 1);
    const packing = document.querySelector('[data-extra="packing"]').checked;
    const assembly = document.querySelector('[data-extra="assembly"]').checked;
    const fragile = document.querySelector('[data-extra="fragile"]').checked;
    const vehicle = 4700 + distance * 100;
    const extraWork = (packing ? 2500 : 0) + (assembly ? 1800 : 0) + (fragile ? 1200 : 0);
    const crew = mode === "rooms" ? 9400 + Math.max(0, rooms - 2) * 3000 + extraWork : 10200 + Math.max(0, volume - 14) * 450 + extraWork;
    const floorLoad = Math.max(0, originFloor + destinationFloor - 20) * 40;
    const liftLoad = lift === "one" ? 700 : lift === "none" ? 1500 : 0;
    const access = 2000 + floorLoad + liftLoad;
    const total = vehicle + crew + access;
    const amount = mode === "rooms" ? rooms : volume;
    const roomWord = rooms === 1 ? "комната" : rooms >= 2 && rooms <= 4 ? "комнаты" : "комнат";
    const amountLabel = mode === "rooms" ? `${rooms} ${roomWord}` : `${volume} м³`;
    const largeMove = mode === "rooms" ? rooms >= 3 : volume >= 14;
    root.querySelector("[data-room-count]").textContent = amount;
    root.querySelector("[data-stepper-label]").textContent = mode === "rooms" ? "Комнаты" : "Объём, м³";
    root.querySelector("[data-distance-label]").textContent = `${distance} км`;
    root.querySelector("[data-summary-title]").textContent = `${amountLabel} · ${distance} км`;
    root.querySelector("[data-summary-team]").textContent = largeMove ? "3 грузчика" : "2 грузчика";
    root.querySelector("[data-summary-truck]").textContent = mode === "volume" ? "Газель 4 м" : largeMove ? "Газель 5 м" : "Газель 3 м";
    root.querySelector("[data-summary-duration]").textContent = largeMove ? "5–6 часов" : "4–5 часов";
    root.querySelector("[data-summary-price]").textContent = money(total);
    root.querySelector("[data-summary-route]").textContent = `${shortAddress(originInput.value)} → ${shortAddress(destinationInput.value)}`;
    root.querySelector("[data-summary-slot]").textContent = `${dateInput.value.trim() || "Дата уточняется"} · 16:30`;
    root.querySelector('[data-breakdown-value="vehicle"]').textContent = money(vehicle);
    root.querySelector('[data-breakdown-value="crew"]').textContent = money(crew);
    root.querySelector('[data-breakdown-value="access"]').textContent = money(access);
    root.querySelector("[data-breakdown-route]").textContent = `${root.querySelector("[data-summary-truck]").textContent}, топливо, ${distance} км маршрута.`;
    root.querySelector("[data-breakdown-access]").textContent = lift === "none" ? "Подъём без лифта и резерв на доступ." : lift === "one" ? "Один адрес без лифта и резерв времени." : "Парковка и лифты на обоих адресах.";
  };
  root.querySelector('[data-stepper="rooms"] [data-action="plus"]').addEventListener("click", () => { if (mode === "rooms") rooms = Math.min(5, rooms + 1); else volume = Math.min(30, volume + 2); update(); });
  root.querySelector('[data-stepper="rooms"] [data-action="minus"]').addEventListener("click", () => { if (mode === "rooms") rooms = Math.max(1, rooms - 1); else volume = Math.max(6, volume - 2); update(); });
  root.querySelectorAll('[data-selectable="calc-mode"]').forEach((button) => button.addEventListener("click", () => {
    root.querySelectorAll('[data-selectable="calc-mode"]').forEach((option) => option.setAttribute("aria-pressed", String(option === button)));
    mode = button.dataset.value; update();
  }));
  root.querySelectorAll('[data-selectable="lift"]').forEach((button) => button.addEventListener("click", () => {
    root.querySelectorAll('[data-selectable="lift"]').forEach((option) => option.setAttribute("aria-pressed", String(option === button)));
    lift = button.dataset.value; update();
  }));
  root.querySelectorAll("[data-extra]").forEach((input) => input.addEventListener("change", update));
  [distanceInput, originFloorInput, destinationFloorInput, dateInput, originInput, destinationInput].forEach((input) => input.addEventListener("input", update));
})();
"""


_PACKING_SCRIPT = r"""
(() => {
  const weights = {dishes: 4, art: 3, tech: 2, plants: 3};
  const update = () => {
    const active = Array.from(document.querySelectorAll("[data-fragile]:checked"));
    const fragile = active.reduce((sum, input) => sum + weights[input.dataset.fragile], 0);
    const boxes = 20 + active.length * 2;
    document.querySelector("[data-boxes]").textContent = `${boxes} коробки`;
    document.querySelector("[data-fragile-count]").textContent = `${fragile} хрупких мест`;
    document.querySelector("[data-seals]").textContent = `Пломбы: ${fragile}`;
  };
  document.querySelectorAll("[data-fragile]").forEach((input) => input.addEventListener("change", update));
})();
"""


_ROUTE_SCRIPT = r"""
(() => {
  const root = document.querySelector(".bp-page");
  const checkpoints = {
    parking: root.querySelector('[data-checkpoint="parking"]'),
    elevator: root.querySelector('[data-checkpoint="elevator"]'),
    arch: root.querySelector('[data-checkpoint="arch"]'),
    concierge: root.querySelector('[data-checkpoint="concierge"]')
  };
  const status = root.querySelector("[data-parking-status]");
  const minuteWord = (value) => {
    const lastTwo = value % 100;
    const last = value % 10;
    if (lastTwo >= 11 && lastTwo <= 14) return "минут";
    if (last === 1) return "минута";
    if (last >= 2 && last <= 4) return "минуты";
    return "минут";
  };
  const updateCheckpoints = () => {
    const routeMinutes = 42 + (checkpoints.elevator.checked ? 0 : 14) + (checkpoints.arch.checked ? 0 : 6);
    root.querySelector("[data-route-distance]").textContent = `18 км · ${routeMinutes} ${minuteWord(routeMinutes)} в пути`;
    status.textContent = [
      checkpoints.parking.checked ? "Парковка согласована" : "Парковка требует подтверждения",
      checkpoints.elevator.checked ? "Лифт забронирован" : "Лифт требует подтверждения",
      checkpoints.arch.checked ? "Арка проверена" : "Арка требует проверки",
      checkpoints.concierge.checked ? "Консьерж на связи" : "Контакт консьержа не получен"
    ].join(" · ");
  };
  Object.values(checkpoints).forEach((input) => input.addEventListener("change", updateCheckpoints));
  document.querySelectorAll('[data-selectable="route-slot"]').forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll('[data-selectable="route-slot"]').forEach((option) => option.setAttribute("aria-pressed", String(option === button)));
      document.querySelector("[data-arrival]").textContent = button.dataset.value;
      document.querySelector("[data-timeline-time]").textContent = button.dataset.value;
      document.querySelector("[data-timeline-arrival]").textContent = "Прибытие и парковка";
    });
  });
  updateCheckpoints();
})();
"""


_ROUTES = {
    "cover": (_cover, _COVER_SCRIPT),
    "apartment-moving": (_apartment, _APARTMENT_SCRIPT),
    "calculator": (_calculator, _CALCULATOR_SCRIPT),
    "packing": (_packing, _PACKING_SCRIPT),
    "route": (_route, _ROUTE_SCRIPT),
}


def render(
    project: ProjectSpec, shot: ShotSpec, assets: Mapping[str, str]
) -> RenderedPage:
    """Render one Berezhny Pereezd page and its dependent workflow."""
    if project.slug != "pereezd-prosto":
        raise ValueError(f"Pereezd renderer received project {project.slug}")
    try:
        route_renderer, scripts = _ROUTES[shot.key]
    except KeyError as exc:
        raise KeyError(f"Unknown Pereezd route: {shot.key}") from exc
    safe_assets = {key: escape(value, quote=True) for key, value in assets.items()}
    html = (
        f'<div class="bp-page" data-site="pereezd-prosto" data-route="{escape(shot.key, quote=True)}">'
        f'{_header(shot.key)}{route_renderer(safe_assets)}</div>'
    )
    return RenderedPage(html=html, css=_CSS, scripts=scripts)
