"""Dedicated portfolio renderer for the TeploDom boiler-service concept."""

from collections.abc import Mapping
from html import escape

from ..icons import icon
from ..models import ProjectSpec, ShotSpec
from .runtime import RenderedPage


def _header(active: str) -> str:
    links = (
        ("boiler-repair", "Ремонт котлов"),
        ("diagnostics", "Диагностика"),
        ("prices", "Цены"),
        ("request", "Вызвать мастера"),
    )
    nav = "".join(
        f'<a href="#" class="{"is-active" if key == active else ""}">{label}</a>'
        for key, label in links
    )
    return (
        '<header class="td-header">'
        '<div class="td-header-main"><a class="td-brand" href="#">'
        '<span class="td-brand-mark"><i></i><b></b></span>'
        '<span><strong>ТеплоДом</strong><small>Ремонт газовых котлов</small></span></a>'
        f'<nav>{nav}</nav>'
        '<div class="td-availability"><span>Сегодня на линии</span><b>7 мастеров</b></div>'
        '<div class="td-phone"><b>+7 (495) 128-84-42</b><span>круглосуточная диспетчерская</span></div>'
        '<button class="td-header-call" type="button">'
        f'{icon("phone", size=18)} Срочный вызов</button></div>'
        '<div class="td-safety-strip"><b>Допуск СРО и аттестация по газовому оборудованию</b>'
        '<span>Выезд по Москве и области</span><span>Диагностика фиксированно 1 500 ₽</span>'
        '<span>Гарантия до 12 месяцев</span></div></header>'
    )


def _cover(assets: Mapping[str, str]) -> str:
    photo = assets["repair_process"]
    return (
        '<main class="td-route td-cover">'
        '<section class="td-cover-grid"><div class="td-cover-copy">'
        '<span class="td-live"><i></i> Дежурный мастер свободен</span>'
        '<h1>Ремонт газовых котлов в день обращения</h1>'
        '<p>Находим причину на месте, согласуем стоимость до ремонта и проверяем безопасность запуска.</p>'
        '<div class="td-cover-proof"><div><b>45 минут</b><span>среднее время прибытия</span></div>'
        '<div><b>1 500 ₽</b><span>фиксированная диагностика</span></div>'
        '<div><b>12 месяцев</b><span>гарантия на работы</span></div></div>'
        '<button class="td-primary" type="button">Вызвать мастера '
        f'{icon("arrow-right", size=19)}</button></div>'
        '<figure class="td-cover-photo"><img src="'
        f'{photo}" alt="Мастер ремонтирует настенный газовый котёл">'
        '<figcaption><b>Работаем с газовым оборудованием безопасно</b>'
        '<span>Проверка тяги, герметичности и автоматики входит в запуск</span></figcaption></figure>'
        '<form class="td-request-sheet"><span class="td-sheet-index">ЗАЯВКА 24/7</span>'
        '<h2>Опишите неисправность</h2><p>Диспетчер передаст мастеру симптомы до выезда.</p>'
        '<label>Что происходит<select><option>Котёл не включается</option><option>Нет горячей воды</option>'
        '<option>Падает давление</option><option>Показывает ошибку</option></select></label>'
        '<label>Марка котла<input type="text" value="Baxi" aria-label="Марка котла"></label>'
        '<div class="td-slot-group" aria-label="Время приезда">'
        '<button type="button" data-selectable="cover-slot" data-value="45 минут" aria-pressed="true">Как можно скорее</button>'
        '<button type="button" data-selectable="cover-slot" data-value="после 18:00" aria-pressed="false">После 18:00</button></div>'
        '<div class="td-arrival" data-cover-arrival aria-label="Мастер будет в течение 45 минут"><span>Мастер будет в течение</span><b>45 минут</b></div>'
        '<button class="td-orange" type="button">Передать заявку</button>'
        '<small>Стоимость работ мастер назовёт после диагностики.</small></form></section>'
        '<section class="td-fault-strip"><div><span>НЕ ЗАПУСКАЕТСЯ</span><b>Питание, плата, розжиг</b>'
        '<p>Проверяем цепь по протоколу, без замены деталей наугад.</p></div>'
        '<div><span>ТЕРЯЕТ ДАВЛЕНИЕ</span><b>Контур, бак, клапан</b><p>Находим утечку и проверяем расширительный бак.</p></div>'
        '<div><span>ШУМИТ ИЛИ ГРЕЕТ РЫВКАМИ</span><b>Насос, теплообменник</b><p>Замеряем циркуляцию и температуру по контурам.</p></div>'
        '<div><span>КОД ОШИБКИ</span><b>Диагностика автоматики</b><p>Расшифровываем код с учётом марки и модели.</p></div></section>'
        '<section class="td-brand-band"><div><span>Официальные регламенты</span><b>BAXI</b><b>Vaillant</b><b>Protherm</b><b>Buderus</b><b>Viessmann</b></div>'
        '<p><strong>После ремонта:</strong> протокол проверки, акт выполненных работ и гарантийный талон.</p></section>'
        '</main>'
    )


def _boiler_repair(assets: Mapping[str, str]) -> str:
    photo = assets["boiler_room"]
    return (
        '<main class="td-route td-repair">'
        '<section class="td-repair-intro"><div><span>РЕМОНТ ПО РЕГЛАМЕНТУ ПРОИЗВОДИТЕЛЯ</span>'
        '<h1>Ремонтируем котёл по результатам диагностики</h1>'
        '<p>Не меняем узлы «на всякий случай». Показываем причину, стоимость детали и срок гарантии до начала работ.</p></div>'
        f'<img src="{photo}" alt="Котельная с настенным газовым оборудованием"></section>'
        '<section class="td-repair-work"><aside class="td-brand-rail"><h2>Выберите марку</h2>'
        '<button type="button" data-selectable="boiler-brand" data-value="Baxi" aria-pressed="true">Baxi <span>на складе 46 деталей</span></button>'
        '<button type="button" data-selectable="boiler-brand" data-value="Vaillant" aria-pressed="false">Vaillant <span>на складе 31 деталь</span></button>'
        '<button type="button" data-selectable="boiler-brand" data-value="Protherm" aria-pressed="false">Protherm <span>на складе 27 деталей</span></button>'
        '<button type="button" data-selectable="boiler-brand" data-value="Buderus" aria-pressed="false">Buderus <span>доставка за 2 часа</span></button></aside>'
        '<div class="td-fault-matrix"><div class="td-matrix-head"><span>Матрица неисправностей</span>'
        '<b data-brand-title>Baxi · типовые работы</b></div>'
        '<div class="td-matrix-row"><b>Нет розжига</b><span>Электрод, газовый клапан, плата</span><strong>от 2 900 ₽</strong></div>'
        '<div class="td-matrix-row"><b>Падает давление</b><span>Бак, клапан, утечка контура</span><strong>от 3 200 ₽</strong></div>'
        '<div class="td-matrix-row"><b>Нет горячей воды</b><span>Датчик протока, теплообменник</span><strong>от 3 600 ₽</strong></div>'
        '<div class="td-matrix-row"><b>Ошибка автоматики</b><span>Диагностика цепи и платы</span><strong>от 4 800 ₽</strong></div>'
        '<div class="td-brand-result"><span>Для выбранной марки</span><b data-brand-stock>46 деталей в машине и на складе</b>'
        '<p data-brand-sla>Большинство ремонтов Baxi закрываем за один выезд.</p></div></div>'
        '<aside class="td-repair-route"><h2>Как проходит ремонт</h2>'
        '<ol><li><b>01</b><span>Замеры и код ошибки</span></li><li><b>02</b><span>Согласование цены</span></li>'
        '<li><b>03</b><span>Ремонт и настройка</span></li><li><b>04</b><span>Безопасный запуск</span></li></ol>'
        '<button class="td-primary" type="button">Проверить свободное время</button></aside></section>'
        '<section class="td-guarantee-band"><div><span>Гарантия на работы и детали</span><h2>Ответственность фиксируем в акте</h2></div>'
        '<div><b>До 12 месяцев</b><p>Срок зависит от узла и производителя детали.</p></div>'
        '<div><b>Старая деталь остаётся у вас</b><p>Показываем заменённый узел и причину отказа.</p></div>'
        '<div><b>Повторный выезд — 0 ₽</b><p>Если неисправность повторилась в гарантийный срок.</p></div></section>'
        '</main>'
    )


def _diagnostics(assets: Mapping[str, str]) -> str:
    photo = assets["diagnostic_tool"]
    return (
        '<main class="td-route td-diagnostics">'
        '<section class="td-diagnostic-intro"><div><span>Диагностика — 1 500 ₽ · фиксированная стоимость</span>'
        '<h1>Сначала находим причину, потом называем цену</h1>'
        '<p>Диагностика оплачивается отдельно и не превращается в обязательный ремонт.</p></div>'
        f'<img src="{photo}" alt="Диагностический прибор для проверки газового котла"></section>'
        '<section class="td-diagnostic-work"><aside class="td-symptoms"><h2>Выберите симптом</h2>'
        '<button type="button" data-selectable="symptom" data-value="ignition" aria-pressed="true">Не запускается<span>питание и розжиг</span></button>'
        '<button type="button" data-selectable="symptom" data-value="water" aria-pressed="false">Нет горячей воды<span>проток и теплообменник</span></button>'
        '<button type="button" data-selectable="symptom" data-value="pressure" aria-pressed="false">Падает давление<span>контур и насос</span></button>'
        '<button type="button" data-selectable="symptom" data-value="noise" aria-pressed="false">Котёл шумит<span>циркуляция и накипь</span></button></aside>'
        '<div class="td-protocol"><div class="td-protocol-head"><span>Протокол диагностики</span><b>7 обязательных проверок</b></div>'
        '<ol><li><b>01</b><span>Тяга и приток воздуха</span><strong>норма / риск</strong></li>'
        '<li><b>02</b><span>Герметичность соединений</span><strong>газоанализатор</strong></li>'
        '<li><b>03</b><span>Давление в контурах</span><strong>в динамике</strong></li>'
        '<li><b>04</b><span>Сигналы датчиков</span><strong>по сервисному меню</strong></li>'
        '<li><b>05</b><span>Розжиг и модуляция</span><strong>под нагрузкой</strong></li></ol></div>'
        '<aside class="td-diagnostic-result" data-diagnostic-result><span>ВЕРОЯТНЫЙ УЗЕЛ ПРОВЕРКИ</span>'
        '<h2 data-diagnostic-title>Цепь розжига и электрод</h2><p data-diagnostic-copy>Проверим питание, искру и ток ионизации до разбора котла.</p>'
        '<dl><div><dt>Диагностика</dt><dd>1 500 ₽</dd></div><div><dt>Время</dt><dd data-diagnostic-time>35–50 минут</dd></div></dl>'
        '<div class="td-warning" data-diagnostic-warning>До проверки не перезапускайте котёл больше двух раз.</div>'
        '<button class="td-orange" type="button">Записать симптомы</button></aside></section>'
        '<section class="td-safety-decision"><div><span>РЕЗУЛЬТАТ ВЫЕЗДА</span><h2>Решение выдаём письменно</h2></div>'
        '<div><b>Можно эксплуатировать</b><p>Настройки восстановлены, рисков нет.</p></div>'
        '<div><b>Нужен ремонт</b><p>Перечень работ, деталей и цена до начала.</p></div>'
        '<div><b>Эксплуатацию остановить</b><p>Причина, безопасное состояние и следующий шаг.</p></div></section>'
        '</main>'
    )


def _prices(assets: Mapping[str, str]) -> str:
    photo = assets["burner_closeup"]
    return (
        '<main class="td-route td-prices">'
        '<section class="td-prices-intro"><div><span>ПРАЙС ОБНОВЛЁН 24.08.2026</span>'
        '<h1>Стоимость работ без скрытых доплат</h1>'
        '<p>Выезд и диагностика считаются отдельно. Детали покупаем только после согласования.</p></div>'
        f'<img src="{photo}" alt="Горелка газового котла крупным планом">'
        '<aside><b>1 500 ₽</b><span>выезд и диагностика в пределах МКАД</span><p>При ремонте в тот же день диагностика остаётся отдельной строкой в акте.</p></aside></section>'
        '<section class="td-price-work"><div class="td-price-table"><div class="td-price-head"><span>Работа</span><span>Что входит</span><span>Цена</span></div>'
        '<button type="button" data-selectable="price-service" data-value="clean" aria-pressed="true"><b>Чистка теплообменника</b><span>Разбор, промывка, сборка</span><strong>от 3 800 ₽</strong></button>'
        '<button type="button" data-selectable="price-service" data-value="valve" aria-pressed="false"><b>Замена трёхходового клапана</b><span>Снятие, установка, настройка</span><strong>от 5 400 ₽</strong></button>'
        '<button type="button" data-selectable="price-service" data-value="board" aria-pressed="false"><b>Ремонт платы управления</b><span>Диагностика компонентов</span><strong>от 7 500 ₽</strong></button>'
        '<button type="button" data-selectable="price-service" data-value="pump" aria-pressed="false"><b>Замена насоса</b><span>Монтаж и проверка циркуляции</span><strong>от 6 900 ₽</strong></button>'
        '<div class="td-price-note"><b>Важно:</b><span>окончательная цена зависит от модели и доступности узла, но не меняется после согласования.</span></div></div>'
        '<aside class="td-price-summary" data-price-summary><span>ВЫБРАННАЯ РАБОТА</span><h2 data-price-name>Чистка теплообменника</h2>'
        '<b data-price-total>от 3 800 ₽</b><p data-price-detail>Химия и уплотнения согласуются по состоянию узла.</p>'
        '<dl><div><dt>Диагностика</dt><dd>1 500 ₽</dd></div><div><dt>Работа</dt><dd data-price-work>от 3 800 ₽</dd></div>'
        '<div><dt>Деталь</dt><dd data-price-part>не требуется</dd></div></dl><button class="td-primary" type="button">Выбрать время</button></aside></section>'
        '<section class="td-payment-band"><div><span>Гарантия до 12 месяцев</span><h2>Оплата после проверки запуска</h2></div>'
        '<div><b>Наличными или картой</b><p>Кассовый чек и акт выдаёт мастер.</p></div><div><b>Без аванса</b><p>Оплата после выполнения и проверки.</p></div>'
        '<div><b>Цена фиксируется</b><p>Все дополнительные работы — только с согласия.</p></div></section>'
        '</main>'
    )


def _request(assets: Mapping[str, str]) -> str:
    portrait = assets["technician_portrait"]
    home = assets["warm_home"]
    return (
        '<main class="td-route td-callout">'
        '<section class="td-callout-grid"><form class="td-callout-form">'
        '<span>ЗАЯВКА В ДИСПЕТЧЕРСКУЮ</span><h1>Вызвать мастера на удобное время</h1>'
        '<div class="td-field-row"><label>Адрес<input type="text" value="Москва, ул. Новаторов, 18"></label>'
        '<label>Марка<select><option>Baxi</option><option>Vaillant</option><option>Protherm</option><option>Buderus</option></select></label></div>'
        '<label>Что происходит<textarea>Котёл показывает ошибку и перестал греть воду</textarea></label>'
        '<fieldset><legend>Срочность</legend><div class="td-segments">'
        '<button type="button" data-selectable="urgency" data-value="now" aria-pressed="true">Сейчас · 45–70 минут</button>'
        '<button type="button" data-selectable="urgency" data-value="today" aria-pressed="false">Сегодня по времени</button></div></fieldset>'
        '<fieldset><legend>Интервал приезда</legend><div class="td-slots">'
        '<button type="button" data-selectable="slot" data-value="14:00–16:00" aria-pressed="true">14:00–16:00</button>'
        '<button type="button" data-selectable="slot" data-value="16:00–18:00" aria-pressed="false">16:00–18:00</button>'
        '<button type="button" data-selectable="slot" data-value="18:00–20:00" aria-pressed="false">18:00–20:00</button></div></fieldset>'
        '<label class="td-consent"><input type="checkbox" checked> Разрешаю связаться для подтверждения выезда</label>'
        '<button class="td-orange" type="button">Подтвердить заявку</button></form>'
        '<aside class="td-master"><div class="td-master-photo">'
        f'<img src="{portrait}" alt="Мастер по ремонту газовых котлов Алексей Мельников"></div>'
        '<span>Назначенный специалист</span><h2>Алексей Мельников</h2><p>Инженер по газовому оборудованию · стаж 12 лет</p>'
        '<div class="td-master-facts"><div><b>4,9 / 5</b><span>оценка клиентов</span></div><div><b>1 840</b><span>выполненных выездов</span></div></div>'
        '<div class="td-dispatch-summary" data-dispatch-summary><span>Подтверждение выезда</span><b data-dispatch-time>Сейчас, 45–70 минут</b>'
        '<p>Алексей Мельников · Диагностика 1 500 ₽</p></div></aside></section>'
        '<section class="td-dispatch-band"><figure>'
        f'<img src="{home}" alt="Тёплый загородный дом после запуска отопления"></figure>'
        '<div><span>ПЕРЕД ВЫЕЗДОМ</span><h2>Подготовьте доступ к котлу</h2><p>Мастер привезёт измерительное оборудование и ходовые детали выбранной марки.</p></div>'
        '<ol><li><b>01</b><span>Диспетчер подтвердит адрес и симптом</span></li><li><b>02</b><span>Мастер позвонит за 20 минут</span></li>'
        '<li><b>03</b><span>Диагностика и цена до ремонта</span></li><li><b>04</b><span>Акт и безопасный запуск</span></li></ol></section>'
        '</main>'
    )


_CSS = r"""
.td-page, .td-page * { box-sizing: border-box; }
.td-page { width: 100%; height: 1120px; overflow: hidden; background: #f7f7f4; color: #1d252c; font-family: Arial, Helvetica, sans-serif; font-size: 14px; letter-spacing: 0; }
.td-page button, .td-page input, .td-page select, .td-page textarea { font: inherit; letter-spacing: 0; }
.td-page button { cursor: pointer; }
.td-page h1, .td-page h2, .td-page p, .td-page figure, .td-page dl, .td-page fieldset { margin: 0; }
.td-page h1, .td-page h2 { font-weight: 800; }
.td-header { height: 120px; background: #fff; border-bottom: 1px solid #cdd3d6; }
.td-header-main { height: 84px; padding: 0 42px; display: grid; grid-template-columns: 235px 1fr 130px 235px 170px; gap: 22px; align-items: center; }
.td-brand { display: flex; align-items: center; gap: 12px; color: #0b4c8c; text-decoration: none; }
.td-brand-mark { position: relative; width: 48px; height: 43px; display: block; border: 4px solid #0b4c8c; border-top: 0; margin-top: 8px; }
.td-brand-mark::before { content: ""; position: absolute; width: 31px; height: 31px; left: 4px; top: -15px; border-left: 5px solid #f47a20; border-top: 5px solid #f47a20; transform: rotate(45deg); }
.td-brand-mark i, .td-brand-mark b { position: absolute; bottom: 7px; width: 5px; background: #f47a20; border-radius: 4px; }
.td-brand-mark i { height: 17px; left: 14px; }
.td-brand-mark b { height: 25px; left: 25px; }
.td-brand strong { display: block; font-size: 24px; line-height: 24px; }
.td-brand small { display: block; color: #5e6870; font-size: 12px; margin-top: 4px; }
.td-header nav { display: flex; justify-content: center; gap: 28px; }
.td-header nav a { color: #26343f; text-decoration: none; font-size: 13px; font-weight: 700; padding: 30px 0 27px; border-bottom: 3px solid transparent; }
.td-header nav a.is-active { color: #0b4c8c; border-bottom-color: #f47a20; }
.td-availability, .td-phone { display: flex; flex-direction: column; gap: 4px; }
.td-availability span, .td-phone span { color: #69747c; font-size: 12px; }
.td-availability b { color: #16833c; font-size: 15px; }
.td-phone b { font-size: 18px; color: #0b4c8c; }
.td-header-call, .td-primary, .td-orange { border: 0; display: inline-flex; align-items: center; justify-content: center; gap: 9px; font-weight: 800; }
.td-header-call { height: 46px; background: #0b4c8c; color: #fff; }
.td-safety-strip { height: 36px; padding: 0 42px; display: grid; grid-template-columns: 1.5fr 1fr 1fr .8fr; align-items: center; background: #1d252c; color: #fff; font-size: 12px; }
.td-safety-strip b { color: #f6a15e; }
.td-safety-strip span { padding-left: 24px; border-left: 1px solid #485159; }
.td-route { height: 1000px; min-height: 0; overflow: hidden; }
.td-live { display: inline-flex; align-items: center; gap: 8px; color: #16833c; font-weight: 800; font-size: 13px; }
.td-live i { width: 9px; height: 9px; background: #16833c; border-radius: 50%; }
.td-primary { min-height: 48px; padding: 0 22px; background: #0b4c8c; color: #fff; }
.td-orange { min-height: 48px; padding: 0 22px; background: #f47a20; color: #fff; }

.td-cover-grid { height: 590px; display: grid; grid-template-columns: 1.06fr .9fr .74fr; background: #fff; }
.td-cover-copy { padding: 58px 40px 42px 42px; }
.td-cover-copy h1 { margin: 22px 0 18px; font-size: 46px; line-height: 1.06; color: #15232e; }
.td-cover-copy > p { max-width: 570px; font-size: 17px; line-height: 1.55; color: #5e6870; }
.td-cover-proof { margin: 30px 0 28px; display: grid; grid-template-columns: repeat(3, 1fr); border-top: 1px solid #d8dddf; border-bottom: 1px solid #d8dddf; }
.td-cover-proof div { padding: 17px 16px 17px 0; border-right: 1px solid #d8dddf; }
.td-cover-proof div:last-child { border: 0; padding-left: 15px; }
.td-cover-proof b, .td-cover-proof span { display: block; }
.td-cover-proof b { color: #0b4c8c; font-size: 21px; }
.td-cover-proof span { margin-top: 5px; font-size: 12px; color: #69747c; }
.td-cover-photo { position: relative; overflow: hidden; background: #dfe5e6; }
.td-cover-photo img { width: 100%; height: 100%; object-fit: cover; }
.td-cover-photo figcaption { position: absolute; left: 0; right: 0; bottom: 0; padding: 18px 22px; background: #fff; border-top: 4px solid #f47a20; }
.td-cover-photo figcaption b, .td-cover-photo figcaption span { display: block; }
.td-cover-photo figcaption b { font-size: 15px; }
.td-cover-photo figcaption span { margin-top: 5px; color: #5e6870; font-size: 12px; }
.td-request-sheet { padding: 34px 30px; background: #1d252c; color: #fff; }
.td-sheet-index { color: #f6a15e; font-size: 12px; font-weight: 800; }
.td-request-sheet h2 { margin: 10px 0 8px; font-size: 25px; }
.td-request-sheet > p { color: #bfc7cc; line-height: 1.45; }
.td-request-sheet label { display: block; margin-top: 18px; font-size: 12px; color: #d7dcdf; }
.td-request-sheet select, .td-request-sheet input { width: 100%; height: 44px; margin-top: 7px; padding: 0 11px; border: 1px solid #667078; background: #fff; color: #1d252c; }
.td-slot-group { margin: 18px 0 15px; display: grid; grid-template-columns: 1fr 1fr; }
.td-slot-group button { min-height: 42px; border: 1px solid #68737b; background: transparent; color: #fff; font-size: 12px; }
.td-slot-group button[aria-pressed="true"] { background: #0b4c8c; border-color: #63a1d5; }
.td-arrival { padding: 13px 15px; border-left: 4px solid #16833c; background: #26323a; }
.td-arrival span, .td-arrival b { display: block; }
.td-arrival span { color: #bfc7cc; font-size: 12px; }
.td-arrival b { margin-top: 4px; font-size: 18px; }
.td-request-sheet .td-orange { width: 100%; margin-top: 16px; }
.td-request-sheet small { display: block; margin-top: 11px; color: #aeb8be; font-size: 12px; }
.td-fault-strip { height: 245px; display: grid; grid-template-columns: repeat(4, 1fr); background: #f7f7f4; border-bottom: 1px solid #d0d5d7; }
.td-fault-strip div { padding: 35px 30px 28px 42px; border-right: 1px solid #d0d5d7; }
.td-fault-strip span { color: #f47a20; font-size: 12px; font-weight: 800; }
.td-fault-strip b { display: block; margin: 14px 0 10px; color: #0b4c8c; font-size: 18px; }
.td-fault-strip p { color: #5e6870; line-height: 1.5; }
.td-brand-band { height: 165px; padding: 28px 42px; display: grid; grid-template-columns: 1.65fr 1fr; align-items: center; background: #fff; }
.td-brand-band > div { display: grid; grid-template-columns: 1.35fr repeat(5, 1fr); align-items: center; gap: 16px; }
.td-brand-band span { color: #5e6870; font-size: 12px; }
.td-brand-band b { font-size: 17px; color: #273640; }
.td-brand-band p { padding: 20px 0 20px 30px; border-left: 4px solid #16833c; line-height: 1.5; }

.td-repair-intro { height: 220px; display: grid; grid-template-columns: 1fr 530px; background: #fff; border-bottom: 1px solid #cfd5d7; }
.td-repair-intro > div { padding: 38px 42px; }
.td-repair-intro span, .td-diagnostic-intro span, .td-prices-intro > div > span { color: #f47a20; font-size: 12px; font-weight: 800; }
.td-repair-intro h1, .td-diagnostic-intro h1, .td-prices-intro h1 { margin: 11px 0 10px; font-size: 34px; line-height: 1.1; color: #142630; }
.td-repair-intro p, .td-diagnostic-intro p, .td-prices-intro p { color: #5e6870; font-size: 15px; line-height: 1.5; }
.td-repair-intro img { width: 100%; height: 220px; object-fit: cover; }
.td-repair-work { height: 540px; display: grid; grid-template-columns: 320px 1fr 330px; background: #fff; }
.td-brand-rail, .td-repair-route { padding: 30px 28px 25px 42px; background: #f2e7d9; }
.td-brand-rail h2, .td-repair-route h2 { font-size: 20px; margin-bottom: 18px; }
.td-brand-rail button { width: 100%; min-height: 82px; padding: 14px 15px; border: 0; border-top: 1px solid #cdbca8; background: transparent; color: #26343f; text-align: left; font-weight: 800; }
.td-brand-rail button span { display: block; margin-top: 6px; color: #69747c; font-size: 12px; font-weight: 400; }
.td-brand-rail button[aria-pressed="true"] { background: #0b4c8c; color: #fff; }
.td-brand-rail button[aria-pressed="true"] span { color: #d7e9f7; }
.td-fault-matrix { padding: 28px 32px; }
.td-matrix-head { display: flex; justify-content: space-between; align-items: end; padding-bottom: 17px; border-bottom: 3px solid #1d252c; }
.td-matrix-head span { color: #69747c; font-size: 12px; }
.td-matrix-head b { color: #0b4c8c; font-size: 19px; }
.td-matrix-row { min-height: 69px; display: grid; grid-template-columns: 1fr 1.35fr 115px; align-items: center; gap: 16px; border-bottom: 1px solid #d8dddf; }
.td-matrix-row b { font-size: 14px; }
.td-matrix-row span { color: #5e6870; font-size: 12px; }
.td-matrix-row strong { color: #f47a20; text-align: right; }
.td-brand-result { margin-top: 18px; padding: 15px 18px; border-left: 4px solid #16833c; background: #eef5f0; }
.td-brand-result span { font-size: 12px; color: #5e6870; }
.td-brand-result b { display: block; margin: 5px 0; color: #16833c; }
.td-repair-route { background: #1d252c; color: #fff; padding-left: 30px; }
.td-repair-route ol { list-style: none; padding: 0; margin: 0 0 24px; }
.td-repair-route li { min-height: 70px; display: grid; grid-template-columns: 42px 1fr; align-items: center; border-bottom: 1px solid #46515a; }
.td-repair-route li b { color: #f6a15e; }
.td-repair-route li span { font-size: 13px; }
.td-repair-route .td-primary { width: 100%; }
.td-guarantee-band { height: 240px; padding: 0 42px; display: grid; grid-template-columns: 1.35fr 1fr 1.1fr 1fr; background: #0b4c8c; color: #fff; }
.td-guarantee-band > div { padding: 42px 28px 30px; border-right: 1px solid #4278a7; }
.td-guarantee-band span { color: #f6a15e; font-size: 12px; font-weight: 800; }
.td-guarantee-band h2 { margin-top: 12px; font-size: 27px; line-height: 1.15; }
.td-guarantee-band b { font-size: 17px; }
.td-guarantee-band p { margin-top: 12px; color: #d8e7f2; line-height: 1.5; }

.td-diagnostic-intro { height: 205px; display: grid; grid-template-columns: 1fr 490px; background: #f7f7f4; border-bottom: 1px solid #cfd5d7; }
.td-diagnostic-intro > div { padding: 34px 42px; }
.td-diagnostic-intro img { width: 100%; height: 205px; object-fit: cover; }
.td-diagnostic-work { height: 565px; display: grid; grid-template-columns: 310px 1fr 390px; background: #fff; }
.td-symptoms { padding: 26px 24px 24px 42px; border-right: 1px solid #d5dade; }
.td-symptoms h2 { font-size: 19px; margin-bottom: 14px; }
.td-symptoms button { width: 100%; min-height: 101px; padding: 15px; border: 0; border-top: 1px solid #cfd5d7; background: #fff; color: #24333e; text-align: left; font-weight: 800; }
.td-symptoms button span { display: block; margin-top: 7px; color: #69747c; font-size: 12px; font-weight: 400; }
.td-symptoms button[aria-pressed="true"] { background: #f2e7d9; border-left: 4px solid #f47a20; }
.td-protocol { padding: 28px 30px; }
.td-protocol-head { padding-bottom: 17px; border-bottom: 3px solid #1d252c; display: flex; justify-content: space-between; }
.td-protocol-head span { font-size: 12px; color: #69747c; }
.td-protocol-head b { color: #0b4c8c; }
.td-protocol ol { list-style: none; padding: 0; margin: 0; }
.td-protocol li { min-height: 80px; display: grid; grid-template-columns: 42px 1fr 125px; gap: 12px; align-items: center; border-bottom: 1px solid #d6dbde; }
.td-protocol li b { color: #f47a20; font-size: 12px; }
.td-protocol li span { font-weight: 700; }
.td-protocol li strong { color: #5e6870; font-size: 12px; text-align: right; }
.td-diagnostic-result { padding: 32px 30px; background: #1d252c; color: #fff; border-top: 6px solid #f47a20; }
.td-diagnostic-result > span { color: #f6a15e; font-size: 12px; font-weight: 800; }
.td-diagnostic-result h2 { min-height: 58px; margin: 11px 0 10px; font-size: 23px; line-height: 1.2; }
.td-diagnostic-result > p { min-height: 58px; color: #c8d0d5; line-height: 1.5; }
.td-diagnostic-result dl { margin-top: 20px; display: grid; grid-template-columns: 1fr 1fr; border-top: 1px solid #4c565d; border-bottom: 1px solid #4c565d; }
.td-diagnostic-result dl div { padding: 15px 0; }
.td-diagnostic-result dt { color: #aeb8be; font-size: 12px; }
.td-diagnostic-result dd { margin: 6px 0 0; font-weight: 800; }
.td-warning { min-height: 58px; margin-top: 20px; padding: 12px 14px; background: #46382f; border-left: 4px solid #f47a20; line-height: 1.4; }
.td-diagnostic-result .td-orange { width: 100%; margin-top: 20px; }
.td-safety-decision { height: 230px; display: grid; grid-template-columns: 1.35fr 1fr 1fr 1fr; padding: 0 42px; background: #f2e7d9; }
.td-safety-decision > div { padding: 39px 28px 25px; border-right: 1px solid #cebba5; }
.td-safety-decision span { color: #f47a20; font-size: 12px; font-weight: 800; }
.td-safety-decision h2 { margin-top: 10px; font-size: 26px; }
.td-safety-decision b { color: #0b4c8c; }
.td-safety-decision p { margin-top: 12px; color: #5e6870; line-height: 1.5; }

.td-prices-intro { height: 225px; display: grid; grid-template-columns: 1fr 430px 330px; background: #fff; }
.td-prices-intro > div { padding: 36px 42px; }
.td-prices-intro img { width: 100%; height: 225px; object-fit: cover; }
.td-prices-intro aside { padding: 38px 30px; background: #0b4c8c; color: #fff; }
.td-prices-intro aside b { display: block; font-size: 34px; color: #fff; }
.td-prices-intro aside span { display: block; margin: 8px 0 16px; color: #f6c294; }
.td-prices-intro aside p { color: #d5e4f0; line-height: 1.5; }
.td-price-work { height: 545px; display: grid; grid-template-columns: 1fr 400px; background: #fff; }
.td-price-table { padding: 28px 34px 22px 42px; }
.td-price-head, .td-price-table > button { display: grid; grid-template-columns: 1.05fr 1.25fr 130px; gap: 22px; align-items: center; }
.td-price-head { height: 40px; padding: 0 14px; background: #1d252c; color: #fff; font-size: 12px; }
.td-price-table > button { width: 100%; min-height: 85px; padding: 14px; border: 0; border-bottom: 1px solid #d4dade; background: #fff; color: #1d252c; text-align: left; }
.td-price-table > button b { font-size: 14px; }
.td-price-table > button span { color: #5e6870; font-size: 12px; }
.td-price-table > button strong { color: #0b4c8c; text-align: right; }
.td-price-table > button[aria-pressed="true"] { background: #eef4f8; border-left: 4px solid #f47a20; }
.td-price-note { min-height: 58px; padding: 14px; display: flex; gap: 10px; background: #f2e7d9; }
.td-price-note b { color: #f47a20; }
.td-price-note span { line-height: 1.4; }
.td-price-summary { padding: 34px 30px; background: #f7f7f4; border-left: 1px solid #cfd5d7; }
.td-price-summary > span { color: #f47a20; font-size: 12px; font-weight: 800; }
.td-price-summary h2 { min-height: 58px; margin: 10px 0 6px; font-size: 23px; }
.td-price-summary > b { display: block; color: #0b4c8c; font-size: 30px; }
.td-price-summary > p { min-height: 55px; margin-top: 12px; color: #5e6870; line-height: 1.4; }
.td-price-summary dl { margin: 20px 0; border-top: 1px solid #cfd5d7; }
.td-price-summary dl div { min-height: 50px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #cfd5d7; }
.td-price-summary dt { color: #69747c; }
.td-price-summary dd { margin: 0; font-weight: 800; }
.td-price-summary .td-primary { width: 100%; }
.td-payment-band { height: 230px; padding: 0 42px; display: grid; grid-template-columns: 1.35fr 1fr 1fr 1fr; background: #1d252c; color: #fff; }
.td-payment-band > div { padding: 40px 28px 25px; border-right: 1px solid #4a545b; }
.td-payment-band span { color: #f6a15e; font-size: 12px; font-weight: 800; }
.td-payment-band h2 { margin-top: 10px; font-size: 27px; }
.td-payment-band b { color: #fff; font-size: 17px; }
.td-payment-band p { margin-top: 12px; color: #bac3c8; line-height: 1.5; }

.td-callout-grid { height: 700px; display: grid; grid-template-columns: 1fr 430px; background: #fff; }
.td-callout-form { padding: 34px 50px 28px 42px; }
.td-callout-form > span { color: #f47a20; font-size: 12px; font-weight: 800; }
.td-callout-form h1 { margin: 9px 0 22px; font-size: 35px; }
.td-callout-form label { display: block; margin-top: 14px; font-size: 12px; font-weight: 700; color: #49565f; }
.td-field-row { display: grid; grid-template-columns: 1.3fr .7fr; gap: 18px; }
.td-callout-form input[type="text"], .td-callout-form select, .td-callout-form textarea { width: 100%; margin-top: 7px; padding: 0 12px; border: 1px solid #aeb7bd; background: #fff; color: #1d252c; }
.td-callout-form input[type="text"], .td-callout-form select { height: 43px; }
.td-callout-form textarea { height: 64px; padding-top: 11px; resize: none; }
.td-callout-form fieldset { padding: 0; margin-top: 16px; border: 0; }
.td-callout-form legend { margin-bottom: 8px; color: #49565f; font-size: 12px; font-weight: 700; }
.td-segments, .td-slots { display: grid; }
.td-segments { grid-template-columns: 1fr 1fr; }
.td-slots { grid-template-columns: repeat(3, 1fr); }
.td-segments button, .td-slots button { min-height: 44px; border: 1px solid #aeb7bd; background: #fff; color: #394750; }
.td-segments button[aria-pressed="true"], .td-slots button[aria-pressed="true"] { background: #0b4c8c; color: #fff; border-color: #0b4c8c; }
.td-consent { display: flex !important; align-items: center; gap: 10px; font-weight: 400 !important; }
.td-consent input { width: 17px; height: 17px; }
.td-callout-form .td-orange { margin-top: 18px; min-width: 260px; }
.td-master { padding: 0 30px 26px; background: #1d252c; color: #fff; }
.td-master-photo { height: 280px; margin: 0 -30px 25px; overflow: hidden; }
.td-master-photo img { width: 100%; height: 100%; object-fit: cover; object-position: center 25%; }
.td-master > span { color: #f6a15e; font-size: 12px; font-weight: 800; }
.td-master h2 { margin-top: 8px; font-size: 25px; }
.td-master > p { margin-top: 7px; color: #c1c9ce; }
.td-master-facts { margin-top: 19px; display: grid; grid-template-columns: 1fr 1fr; border-top: 1px solid #4c565d; border-bottom: 1px solid #4c565d; }
.td-master-facts div { padding: 14px 0; }
.td-master-facts b, .td-master-facts span { display: block; }
.td-master-facts b { font-size: 18px; }
.td-master-facts span { margin-top: 4px; color: #aeb8be; font-size: 12px; }
.td-dispatch-summary { margin-top: 18px; padding: 15px; background: #26333b; border-left: 4px solid #16833c; }
.td-dispatch-summary span, .td-dispatch-summary b, .td-dispatch-summary p { display: block; }
.td-dispatch-summary span { color: #9fcab0; font-size: 12px; }
.td-dispatch-summary b { margin-top: 5px; font-size: 17px; }
.td-dispatch-summary p { margin-top: 7px; color: #c7d0d5; }
.td-dispatch-band { height: 300px; display: grid; grid-template-columns: 380px 420px 1fr; background: #f2e7d9; }
.td-dispatch-band figure { overflow: hidden; }
.td-dispatch-band img { width: 100%; height: 300px; object-fit: cover; }
.td-dispatch-band > div { padding: 47px 38px; border-right: 1px solid #cfbda8; }
.td-dispatch-band > div span { color: #f47a20; font-size: 12px; font-weight: 800; }
.td-dispatch-band > div h2 { margin: 10px 0 12px; font-size: 25px; }
.td-dispatch-band > div p { color: #5e6870; line-height: 1.5; }
.td-dispatch-band ol { list-style: none; margin: 0; padding: 27px 42px; display: grid; grid-template-columns: 1fr 1fr; }
.td-dispatch-band li { min-height: 108px; padding: 18px; border-bottom: 1px solid #cfbda8; }
.td-dispatch-band li:nth-child(odd) { border-right: 1px solid #cfbda8; }
.td-dispatch-band li b { display: block; color: #0b4c8c; font-size: 12px; margin-bottom: 8px; }
.td-dispatch-band li span { line-height: 1.4; font-weight: 700; }
"""


_COVER_SCRIPT = r"""
(() => {
  document.querySelectorAll('[data-selectable="cover-slot"]').forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll('[data-selectable="cover-slot"]').forEach((option) => {
        option.setAttribute("aria-pressed", String(option === button));
      });
      document.querySelector("[data-cover-arrival] b").textContent = button.dataset.value;
    });
  });
})();
"""


_REPAIR_SCRIPT = r"""
(() => {
  const brands = {
    Baxi: ["46 деталей в машине и на складе", "Большинство ремонтов Baxi закрываем за один выезд."],
    Vaillant: ["31 оригинальная и совместимая деталь", "По Vaillant заранее сверяем шильдик и поколение котла."],
    Protherm: ["27 ходовых деталей на складе", "Для Protherm привозим датчики и клапаны по модели."],
    Buderus: ["Доставка редких деталей за 2 часа", "По Buderus сначала подтверждаем код узла у поставщика."]
  };
  document.querySelectorAll('[data-selectable="boiler-brand"]').forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll('[data-selectable="boiler-brand"]').forEach((option) => option.setAttribute("aria-pressed", String(option === button)));
      const name = button.dataset.value;
      document.querySelector("[data-brand-title]").textContent = `${name} · типовые работы`;
      document.querySelector("[data-brand-stock]").textContent = brands[name][0];
      document.querySelector("[data-brand-sla]").textContent = brands[name][1];
    });
  });
})();
"""


_DIAGNOSTIC_SCRIPT = r"""
(() => {
  const symptoms = {
    ignition: ["Цепь розжига и электрод", "Проверим питание, искру и ток ионизации до разбора котла.", "35–50 минут", "До проверки не перезапускайте котёл больше двух раз."],
    water: ["Датчик протока и теплообменник", "Сравним температуру входа и выхода, проверим проток и трёхходовой клапан.", "45–60 минут", "Не повышайте температуру вручную до проверки датчиков."],
    pressure: ["Датчик давления и насос", "Проверим контур, расширительный бак и работу насоса в динамике.", "40–65 минут", "До проверки котёл не включать: возможна работа без циркуляции."],
    noise: ["Насос и первичный теплообменник", "Замерим циркуляцию и перепад температуры, оценим накипь без разборки.", "50–70 минут", "При резком металлическом шуме остановите котёл кнопкой питания."]
  };
  document.querySelectorAll('[data-selectable="symptom"]').forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll('[data-selectable="symptom"]').forEach((option) => option.setAttribute("aria-pressed", String(option === button)));
      const value = symptoms[button.dataset.value];
      document.querySelector("[data-diagnostic-title]").textContent = value[0];
      document.querySelector("[data-diagnostic-copy]").textContent = value[1];
      document.querySelector("[data-diagnostic-time]").textContent = value[2];
      document.querySelector("[data-diagnostic-warning]").textContent = value[3];
    });
  });
})();
"""


_PRICE_SCRIPT = r"""
(() => {
  const services = {
    clean: ["Чистка теплообменника", "от 3 800 ₽", "Химия и уплотнения согласуются по состоянию узла.", "от 3 800 ₽", "не требуется"],
    valve: ["Замена трёхходового клапана", "от 5 400 ₽", "Новый клапан подбираем по модели и серийному номеру.", "от 5 400 ₽", "согласуем отдельно"],
    board: ["Ремонт платы управления", "от 7 500 ₽", "Компоненты и целесообразность ремонта подтверждаем после стендовой проверки.", "от 7 500 ₽", "компоненты включены"],
    pump: ["Замена насоса", "от 6 900 ₽", "Монтаж, развоздушивание и проверка циркуляции; деталь согласуем отдельно.", "от 6 900 ₽", "деталь согласуем отдельно"]
  };
  document.querySelectorAll('[data-selectable="price-service"]').forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll('[data-selectable="price-service"]').forEach((option) => option.setAttribute("aria-pressed", String(option === button)));
      const value = services[button.dataset.value];
      document.querySelector("[data-price-name]").textContent = value[0];
      document.querySelector("[data-price-total]").textContent = value[1];
      document.querySelector("[data-price-detail]").textContent = value[2];
      document.querySelector("[data-price-work]").textContent = value[3];
      document.querySelector("[data-price-part]").textContent = value[4];
    });
  });
})();
"""


_REQUEST_SCRIPT = r"""
(() => {
  let urgency = "now";
  let slot = "14:00–16:00";
  const update = () => {
    document.querySelector("[data-dispatch-time]").textContent = urgency === "now" ? "Сейчас, 45–70 минут" : `Сегодня, ${slot}`;
  };
  document.querySelectorAll('[data-selectable="urgency"]').forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll('[data-selectable="urgency"]').forEach((option) => option.setAttribute("aria-pressed", String(option === button)));
      urgency = button.dataset.value;
      update();
    });
  });
  document.querySelectorAll('[data-selectable="slot"]').forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll('[data-selectable="slot"]').forEach((option) => option.setAttribute("aria-pressed", String(option === button)));
      slot = button.dataset.value;
      update();
    });
  });
})();
"""


_ROUTES = {
    "cover": (_cover, _COVER_SCRIPT),
    "boiler-repair": (_boiler_repair, _REPAIR_SCRIPT),
    "diagnostics": (_diagnostics, _DIAGNOSTIC_SCRIPT),
    "prices": (_prices, _PRICE_SCRIPT),
    "request": (_request, _REQUEST_SCRIPT),
}


def render(
    project: ProjectSpec, shot: ShotSpec, assets: Mapping[str, str]
) -> RenderedPage:
    """Render one TeploDom route with route-owned assets and interactions."""
    if project.slug != "teplodom":
        raise ValueError(f"TeploDom renderer received project {project.slug}")
    try:
        route_renderer, scripts = _ROUTES[shot.key]
    except KeyError as exc:
        raise KeyError(f"Unknown TeploDom route: {shot.key}") from exc
    safe_assets = {key: escape(value, quote=True) for key, value in assets.items()}
    body = route_renderer(safe_assets)
    html = (
        f'<div class="td-page" data-site="teplodom" data-route="{escape(shot.key, quote=True)}">'
        f'{_header(shot.key)}{body}</div>'
    )
    return RenderedPage(html=html, css=_CSS, scripts=scripts)
