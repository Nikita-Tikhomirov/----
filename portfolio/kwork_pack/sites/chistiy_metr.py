"""Dedicated service renderer for the Chistiy Metr cleaning website."""

from collections.abc import Mapping

from ..components import escape_html
from ..models import ProjectSpec, ShotSpec
from .runtime import RenderedPage


_ROUTE_ASSETS = {
    "cover": ("clean_kitchen",),
    "after-renovation": ("before_cleanup", "after_cleanup"),
    "calculator": ("equipment_case",),
    "checklist": ("bathroom_detail",),
    "reviews": ("cleaner_portrait",),
}


def _owned_assets(route: str, assets: Mapping[str, str]) -> dict[str, str]:
    resolved: dict[str, str] = {}
    for key in _ROUTE_ASSETS[route]:
        try:
            resolved[key] = escape_html(assets[key])
        except KeyError as exc:
            raise KeyError(f"chistiy-metr {route} missing asset {key}") from exc
    return resolved


def _header(active: str) -> str:
    routes = (
        ("after-renovation", "После ремонта"),
        ("calculator", "Калькулятор"),
        ("checklist", "Что входит"),
        ("reviews", "Отзывы"),
    )
    nav = "".join(
        f'<a href="#" class="{"is-active" if key == active else ""}">{label}</a>'
        for key, label in routes
    )
    return (
        '<header class="cm-header">'
        '<div class="cm-header-main"><div class="cm-brand">'
        '<span class="cm-brand-mark" aria-hidden="true"></span><div><strong>Чистый метр</strong>'
        '<small>клининговая служба</small></div></div>'
        '<p>Уборка после ремонта<br>в Москве и МО</p>'
        f'<nav aria-label="Услуги">{nav}<a href="#">Контакты</a></nav>'
        '<div class="cm-phone"><b>+7 (495) 125-50-35</b><span>ежедневно с 8:00 до 22:00</span></div>'
        '<button type="button" class="cm-coral-button">Заказать звонок</button></div>'
        '<div class="cm-header-proof"><b>Фиксируем состав работ до выезда</b>'
        '<span>Профессиональная химия и техника</span><span>Гарантия результата 24 часа</span>'
        '<span>Свободная бригада сегодня</span></div></header>'
    )


def _cover(assets: Mapping[str, str]) -> str:
    return (
        '<main class="cm-cover-route">'
        '<section class="cm-cover-main"><div class="cm-cover-copy"><span class="cm-eyebrow">Уборка после ремонта · Москва и МО</span>'
        '<h1 aria-label="Уборка после ремонта от 120 ₽ за м²">Уборка после ремонта<br>от <em>120 ₽</em> за м²</h1>'
        '<p class="cm-lead">Соберём строительную пыль, отмоем поверхности и передадим квартиру по листу приёмки.</p>'
        '<dl class="cm-cover-facts"><div><dt>Без доплат</dt><dd>смета до выезда</dd></div>'
        '<div><dt>2–4 человека</dt><dd>бригада под площадь</dd></div><div><dt>24 часа</dt><dd>гарантия результата</dd></div></dl>'
        '<section class="cm-cover-calculator" aria-label="Быстрый расчёт уборки"><div class="cm-calc-head"><b>Рассчитайте стоимость уборки</b><span>ответим за 5 минут</span></div>'
        '<div class="cm-cover-controls"><label>Площадь, м²<input data-cover-area type="number" min="20" max="300" value="64"></label>'
        '<fieldset><legend>Тип уборки</legend><button type="button" data-selectable="cover-service" data-rate="120" aria-pressed="true">После ремонта</button>'
        '<button type="button" data-selectable="cover-service" data-rate="160" aria-pressed="false">Генеральная после ремонта</button></fieldset>'
        '<label class="cm-check"><input data-cover-windows type="checkbox"> Окна и рамы после ремонта</label></div>'
        '<div class="cm-cover-quote"><div><span>Предварительная стоимость</span><strong data-cover-total>7 680 ₽</strong><small data-cover-scope>64 м² · после ремонта</small></div>'
        '<div><span>Свободная бригада</span><b data-cover-team>Свободная бригада сегодня с 14:00 · 2 человека</b><small data-cover-duration>5–6 часов на объекте</small></div>'
        '<button type="button" class="cm-coral-button">Заказать уборку</button></div></section>'
        '<section class="cm-cover-readiness"><div><span>На выезд</span><b>HEPA-пылесос и парогенератор</b><p>Техника приезжает с бригадой.</p></div><div><span>До начала</span><b>Согласуем зоны и расходники</b><p>Фото объекта достаточно для первого расчёта.</p></div><div><span>При передаче</span><b>Акт, фото и гарантийный контакт</b><p>Оставим у заказчика после обхода.</p></div></section></div>'
        '<figure class="cm-cover-media"><img src="' + assets["clean_kitchen"] + '" alt="Бригада клинеров работает в светлой кухне после ремонта">'
        '<figcaption><b>Гарантия результата 24 часа</b><span>Вернёмся и исправим замечания по листу приёмки.</span></figcaption></figure></section>'
        '<section class="cm-cover-proof"><article><span>01</span><b>Сначала защищаем чистовые поверхности</b><p>Согласуем зоны и материалы до начала работ.</p></article>'
        '<article><span>02</span><b>Пыль собираем техникой с HEPA-фильтром</b><p>Не разносим мелкую строительную пыль по квартире.</p></article>'
        '<article><span>03</span><b>Окна и сантехнику принимаем отдельно</b><p>Каждая зона отмечается в листе контроля.</p></article>'
        '<article><span>04</span><b>Передаём объект только после обхода</b><p>Оставляем акт, рекомендации и гарантийный контакт.</p></article></section></main>'
    )


def _after_renovation(assets: Mapping[str, str]) -> str:
    return (
        '<main class="cm-after-route"><section class="cm-route-title"><div><span>Объект № 241 · 68 м² · 1 день</span>'
        '<h1>Уборка после ремонта: контроль по зонам</h1></div><p>Фиксируем исходное состояние, планируем порядок работ и сдаём каждую комнату по отдельному листу.</p></section>'
        '<section class="cm-evidence"><div class="cm-evidence-head"><b>Состояние до выхода бригады</b><span>Пыль на полу, плёнка на окнах, следы затирки и строительный мусор в зоне кухни-гостиной.</span></div>'
        '<figure><img src="' + assets["before_cleanup"] + '" alt="Квартира до уборки после ремонта"><figcaption>До выхода бригады</figcaption></figure>'
        '<figure><img src="' + assets["after_cleanup"] + '" alt="Квартира после уборки после ремонта"><figcaption>После контроля качества</figcaption></figure>'
        '<aside><span>План бригады</span><ol><li><b>09:00</b> Защита чистовых зон и вынос упаковки</li><li><b>10:30</b> HEPA-пылесос и влажная обработка</li><li><b>13:00</b> Окна, сантехника, локальные следы</li><li><b>16:00</b> Совместная приёмка с заказчиком</li></ol><strong>2 специалиста · 7 часов</strong></aside></section>'
        '<section class="cm-after-handoff"><div><span>Контроль качества</span><b>Приёмка по 18 контрольным точкам</b><p>Полы, стекло, сантехника, плинтусы, розетки и труднодоступные зоны проверяем вместе.</p></div>'
        '<div><span>После работ</span><b>Акт и фото до/после</b><p>Отправим в день уборки, чтобы можно было принять квартиру удалённо.</p></div>'
        '<div><span>Гарантия</span><b>24 часа на замечания</b><p>Вернёмся без доплаты, если пункт из согласованного объёма не принят.</p></div>'
        '<button type="button" class="cm-coral-button">Запланировать</button></section></main>'
    )


def _calculator(assets: Mapping[str, str]) -> str:
    return (
        '<main class="cm-calculator-route"><section class="cm-route-title"><div><span>Калькулятор уборки · без звонка</span><h1>Рассчитайте уборку без скрытых доплат</h1></div>'
        '<p>Выберите площадь, срочность и дополнительные зоны. Итог сразу покажет состав бригады и ближайшее доступное окно.</p></section>'
        '<section class="cm-calculator-workspace"><div class="cm-calculator-form"><label>Площадь объекта, м²<input data-calculator-area type="number" min="20" max="300" value="54"></label>'
        '<fieldset class="cm-room-type"><legend>Тип помещения</legend><button type="button" data-selectable="calculator-room" data-rate="170" data-room="Квартира" aria-pressed="true">Квартира</button><button type="button" data-selectable="calculator-room" data-rate="190" data-room="Дом" aria-pressed="false">Дом</button><button type="button" data-selectable="calculator-room" data-rate="155" data-room="Офис" aria-pressed="false">Офис</button></fieldset>'
        '<fieldset class="cm-urgency"><legend>Срочность</legend><button type="button" data-selectable="calculator-urgency" data-urgency="today" aria-pressed="true">Сегодня</button><button type="button" data-selectable="calculator-urgency" data-urgency="tomorrow" aria-pressed="false">Завтра</button><button type="button" data-selectable="calculator-urgency" data-urgency="week" aria-pressed="false">На неделе</button></fieldset>'
        '<fieldset><legend>Дополнительно</legend><label class="cm-check"><input data-calculator-oven type="checkbox"> Духовой шкаф внутри</label><label class="cm-check"><input data-calculator-fridge type="checkbox"> Холодильник внутри</label><label class="cm-check"><input data-calculator-balcony type="checkbox"> Балкон и остекление</label></fieldset>'
        '<p class="cm-form-note">Менеджер сверит итог после просмотра фото или бесплатного выезда.</p></div>'
        '<section class="cm-calculator-summary"><span>Ваш расчёт</span><strong data-calculator-total>8 640 ₽</strong><b data-calculator-slot>Следующее окно: сегодня, 14:00</b><dl><div><dt>На объекте</dt><dd data-calculator-duration>5–6 часов</dd></div><div><dt>Состав</dt><dd data-calculator-team>2 специалиста</dd></div><div><dt>Гарантия</dt><dd>24 часа</dd></div></dl><button type="button" class="cm-coral-button">Закрепить время</button></section>'
        '<figure class="cm-equipment"><img src="' + assets["equipment_case"] + '" alt="Комплект техники и химии для уборки"><figcaption><b>Техника приезжает с бригадой</b><span>HEPA-пылесос, парогенератор, безопасная химия и расходники.</span></figcaption></figure></section>'
        '<section class="cm-calculator-scope"><div><span>Выбрано для расчёта</span><b data-scope-title>Квартира после ремонта · 54 м²</b><p data-scope-items>HEPA-пылесос, влажная обработка, сантехника и кухня снаружи.</p></div>'
        '<div><span>Включено всегда</span><b>Инвентарь и химия</b><p>Защита поверхностей, расходники, контрольный обход и акт.</p></div><div><span>Важно знать</span><b>Без строительного вывоза</b><p>В расчёт не входит вывоз строительного мусора и работа на высоте.</p></div></section></main>'
    )


def _checklist(assets: Mapping[str, str]) -> str:
    return (
        '<main class="cm-checklist-route"><section class="cm-route-title"><div><span>Прозрачный состав работ</span><h1>Что входит в уборку после ремонта</h1></div><p>Не прячем важные детали в примечаниях: каждая комната имеет свой перечень включённых и исключённых задач.</p></section>'
        '<section class="cm-checklist-workspace"><aside><figure><img src="' + assets["bathroom_detail"] + '" alt="Чистый санузел после профессиональной уборки"></figure><span>Профессиональная химия</span><b>Подбираем средства под материал</b><p>Для камня, стекла, дерева и сантехники используем отдельные составы.</p><small>Инвентарь маркируется для каждой зоны.</small></aside>'
        '<div class="cm-checklist-main"><nav aria-label="Зоны уборки"><button type="button" data-selectable="cleaning-zone" data-zone="kitchen" aria-pressed="false">Кухня</button><button type="button" data-selectable="cleaning-zone" data-zone="bathroom" aria-pressed="true">Санузел</button><button type="button" data-selectable="cleaning-zone" data-zone="bedroom" aria-pressed="false">Спальня</button><button type="button" data-selectable="cleaning-zone" data-zone="living" aria-pressed="false">Гостиная</button></nav>'
        '<div class="cm-zone-summary"><span>Зона: санузел</span><b>7 задач включено</b><p>Плитка, стекло, сантехника, вытяжка и пол после строительной пыли.</p><small>Удаление старого герметика и плесени не входит в стандартный состав.</small></div><ul data-zone-list><li>Удаляем следы затирки с плитки</li><li>Моем стекло душевой и фурнитуру</li><li>Очищаем ванну, раковину и смеситель</li><li>Протираем полотенцесушитель и выключатели</li><li>Моем пол и зону за унитазом</li></ul><p class="cm-exclusion" data-zone-exclusion>Удаление старого герметика и плесени не входит в стандартный состав.</p></div></section>'
        '<section class="cm-checklist-acceptance"><div><span>На объекте</span><b>Ответственный клинер отмечает зоны</b><p>Статус виден менеджеру до приезда заказчика.</p></div><div><span>При передаче</span><b>Лист приёмки остаётся у заказчика</b><p>В нём отмечены выполненные пункты и замечания, если они есть.</p></div><div><span>После</span><b>24 часа на гарантийный выезд</b><p>Контакт менеджера и номер объекта указаны в акте.</p></div></section></main>'
    )


def _reviews(assets: Mapping[str, str]) -> str:
    return (
        '<main class="cm-reviews-route"><section class="cm-route-title"><div><span>Проверенные оценки · август</span><h1>Отзывы после реальных уборок</h1></div><p>Публикуем площадь, вид работ и результат приёмки. В карточке нет анонимных историй без объекта.</p></section>'
        '<section class="cm-reviews-workspace"><div class="cm-reviews-ledger-wrap"><nav aria-label="Фильтр отзывов"><button type="button" data-selectable="review-filter" data-filter="all" aria-pressed="true">Все объекты</button><button type="button" data-selectable="review-filter" data-filter="repair" aria-pressed="false">После ремонта</button><button type="button" data-selectable="review-filter" data-filter="regular" aria-pressed="false">Регулярная уборка</button></nav>'
        '<div class="cm-review-ledger"><div class="cm-review-row"><span>14 августа</span><b>Уборка после ремонта · 72 м²</b><p>Акт принят без замечаний</p><strong>5,0</strong></div><div class="cm-review-row"><span>12 августа</span><b>Генеральная уборка · 58 м²</b><p>Добавили окна по согласованию</p><strong>5,0</strong></div><div class="cm-review-row"><span>09 августа</span><b>Уборка после ремонта · 44 м²</b><p>Передали ключи консьержу</p><strong>4,8</strong></div><div class="cm-review-row"><span>06 августа</span><b>Уборка после ремонта · 96 м²</b><p>Контрольный обход с дизайнером</p><strong>5,0</strong></div><div class="cm-review-row"><span>02 августа</span><b>Регулярная уборка · 83 м²</b><p>Без переноса визита</p><strong>5,0</strong></div></div><p class="cm-review-rating">4,9 из 5 по 286 проверенным оценкам</p></div>'
        '<aside class="cm-crew-profile"><figure><img src="' + assets["cleaner_portrait"] + '" alt="Марина, руководитель клининговой бригады"></figure><span>Бригада № 12</span><b>Марина Воронова</b><p>Руководитель смены, 6 лет в клининге после ремонта.</p><strong>Бригада Марины свободна завтра в 10:00</strong><button type="button" class="cm-coral-button">Выбрать бригаду</button></aside></section>'
        '<section class="cm-reviews-metrics"><div><span>7 лет</span><b>в клининге после ремонта</b></div><div><span>25 000+</span><b>объектов с листом приёмки</b></div><div><span>96%</span><b>объектов приняты с первого обхода</b></div><div><span>24 часа</span><b>на гарантийный выезд после работ</b></div></section></main>'
    )


_COVER_SCRIPT = r"""
(() => {
  const root = document.querySelector('.cm-page');
  const area = root.querySelector('[data-cover-area]');
  const windows = root.querySelector('[data-cover-windows]');
  const options = [...root.querySelectorAll('[data-selectable="cover-service"]')];
  const total = root.querySelector('[data-cover-total]');
  const scope = root.querySelector('[data-cover-scope]');
  const team = root.querySelector('[data-cover-team]');
  const duration = root.querySelector('[data-cover-duration]');
  let selected = options[0];
  const update = () => {
    const meters = Math.max(20, Number(area.value) || 20);
    const rate = Number(selected.dataset.rate);
    const extra = windows.checked ? 1620 : 0;
    const people = meters >= 80 ? 3 : 2;
    total.textContent = `${(meters * rate + extra).toLocaleString('ru-RU').replace(/\u00a0/g, ' ')} ₽`;
    scope.textContent = `${meters} м² · ${selected.textContent.trim()}`;
    team.textContent = `Сегодня с 14:00 · Бригада из ${people} человек`;
    duration.textContent = people === 3 ? '6–7 часов на объекте' : '5–6 часов на объекте';
  };
  options.forEach((option) => option.addEventListener('click', () => {
    selected = option;
    options.forEach((item) => item.setAttribute('aria-pressed', String(item === option)));
    update();
  }));
  area.addEventListener('input', update); windows.addEventListener('change', update);
})();
"""

_CALCULATOR_SCRIPT = r"""
(() => {
  const root = document.querySelector('.cm-page');
  const area = root.querySelector('[data-calculator-area]');
  const roomTypes = [...root.querySelectorAll('[data-selectable="calculator-room"]')];
  const urgency = [...root.querySelectorAll('[data-selectable="calculator-urgency"]')];
  const oven = root.querySelector('[data-calculator-oven]');
  const fridge = root.querySelector('[data-calculator-fridge]');
  const balcony = root.querySelector('[data-calculator-balcony]');
  const total = root.querySelector('[data-calculator-total]');
  const slot = root.querySelector('[data-calculator-slot]');
  const team = root.querySelector('[data-calculator-team]');
  const duration = root.querySelector('[data-calculator-duration]');
  const title = root.querySelector('[data-scope-title]');
  const items = root.querySelector('[data-scope-items]');
  let selectedRoom = roomTypes[0];
  let selected = urgency[0];
  const update = () => {
    const meters = Math.max(20, Number(area.value) || 20);
    const addOns = (oven.checked ? 900 : 0) + (fridge.checked ? 750 : 0) + (balcony.checked ? 1100 : 0);
    const labels = [];
    if (oven.checked) labels.push('Духовой шкаф внутри');
    if (fridge.checked) labels.push('холодильник внутри');
    if (balcony.checked) labels.push('балкон и остекление');
    total.textContent = `${(meters * Number(selectedRoom.dataset.rate) + addOns).toLocaleString('ru-RU').replace(/\u00a0/g, ' ')} ₽`;
    slot.textContent = selected.dataset.urgency === 'tomorrow' ? 'Следующее окно: Завтра, 10:00' : selected.dataset.urgency === 'week' ? 'Следующее окно: 28 августа, 12:00' : 'Следующее окно: сегодня, 14:00';
    team.textContent = meters >= 90 ? '3 специалиста' : '2 специалиста';
    duration.textContent = meters >= 90 ? '7–8 часов' : '5–6 часов';
    title.textContent = `${selectedRoom.dataset.room} после ремонта · ${meters} м²`;
    items.textContent = labels.length ? `HEPA-пылесос, влажная обработка, сантехника и кухня снаружи. ${labels.join(', ')}.` : 'HEPA-пылесос, влажная обработка, сантехника и кухня снаружи.';
  };
  urgency.forEach((option) => option.addEventListener('click', () => {
    selected = option;
    urgency.forEach((item) => item.setAttribute('aria-pressed', String(item === option)));
    update();
  }));
  roomTypes.forEach((option) => option.addEventListener('click', () => {
    selectedRoom = option;
    roomTypes.forEach((item) => item.setAttribute('aria-pressed', String(item === option)));
    update();
  }));
  [area, oven, fridge, balcony].forEach((control) => control.addEventListener(control === area ? 'input' : 'change', update));
})();
"""

_CHECKLIST_SCRIPT = r"""
(() => {
  const root = document.querySelector('.cm-page');
  const controls = [...root.querySelectorAll('[data-selectable="cleaning-zone"]')];
  const summary = root.querySelector('.cm-zone-summary');
  const list = root.querySelector('[data-zone-list]');
  const exclusion = root.querySelector('[data-zone-exclusion]');
  const zones = {
    kitchen: ['Кухня', '8 задач включено', 'Фасады, столешница, мойка, фартук, техника снаружи и пол.', ['Удаляем строительную пыль с фасадов и фартука', 'Моем столешницу, мойку и смеситель', 'Очищаем варочную панель и духовку снаружи', 'Протираем розетки, плинтусы и дверные ручки', 'Пылесосим и моем пол по периметру'], 'Внутренняя чистка холодильника и духовки добавляется отдельно.'],
    bathroom: ['Санузел', '7 задач включено', 'Плитка, стекло, сантехника, вытяжка и пол после строительной пыли.', ['Удаляем следы затирки с плитки', 'Моем стекло душевой и фурнитуру', 'Очищаем ванну, раковину и смеситель', 'Протираем полотенцесушитель и выключатели', 'Моем пол и зону за унитазом'], 'Удаление старого герметика и плесени не входит в стандартный состав.'],
    bedroom: ['Спальня', '6 задач включено', 'Пыль, плинтусы, двери, радиатор, пол и доступные поверхности.', ['Собираем мелкую строительную пыль HEPA-пылесосом', 'Протираем двери, ручки и выключатели', 'Очищаем подоконник и радиатор', 'Моем доступные горизонтальные поверхности', 'Моем пол без разводов'], 'Химчистка матраса не входит в стандартный состав.'],
    living: ['Гостиная', '7 задач включено', 'Финишная очистка всех доступных поверхностей и пола.', ['Собираем пыль с пола и плинтусов', 'Протираем розетки и выключатели', 'Очищаем двери и наличники', 'Моем панорамные окна изнутри', 'Проводим влажную уборку пола'], 'Мытьё люстр сложной конструкции согласуется отдельно.']
  };
  const update = (key) => {
    const [name, count, lead, tasks, note] = zones[key];
    summary.innerHTML = `<span>Зона: ${name}</span><b>${count}</b><p>${lead}</p><small>${note}</small>`;
    list.innerHTML = tasks.map((task) => `<li>${task}</li>`).join('');
    exclusion.textContent = note;
  };
  controls.forEach((control) => control.addEventListener('click', () => {
    controls.forEach((item) => item.setAttribute('aria-pressed', String(item === control)));
    update(control.dataset.zone);
  }));
})();
"""

_REVIEWS_SCRIPT = r"""
(() => {
  const root = document.querySelector('.cm-page');
  const controls = [...root.querySelectorAll('[data-selectable="review-filter"]')];
  const ledger = root.querySelector('.cm-review-ledger');
  const ratingTotal = root.querySelector('.cm-review-rating');
  const rows = {
    all: [['14 августа', 'Уборка после ремонта · 72 м²', 'Акт принят без замечаний', '5,0'], ['12 августа', 'Генеральная уборка · 58 м²', 'Добавили окна по согласованию', '5,0'], ['09 августа', 'Уборка после ремонта · 44 м²', 'Передали ключи консьержу', '4,8']],
    repair: [['14 августа', 'Уборка после ремонта · 72 м²', 'Акт принят без замечаний', '5,0'], ['09 августа', 'Уборка после ремонта · 44 м²', 'Передали ключи консьержу', '4,8'], ['05 августа', 'Уборка после ремонта · 96 м²', 'Контрольный обход с дизайнером', '5,0']],
    regular: [['12 августа', 'Регулярная уборка · 58 м²', 'Добавили окна по согласованию', '5,0'], ['06 августа', 'Регулярная уборка · 48 м²', 'Время согласовано за день', '4,9'], ['02 августа', 'Регулярная уборка · 83 м²', 'Без переноса визита', '5,0']]
  };
  const ratings = {
    all: '4,9 из 5 по 286 проверенным оценкам',
    repair: '4,9 из 5 по 118 проверенным оценкам',
    regular: '5,0 из 5 по 76 проверенным оценкам'
  };
  const update = (filter) => {
    ledger.innerHTML = rows[filter].map(([date, service, result, rating]) => `<div class="cm-review-row"><span>${date}</span><b>${service}</b><p>${result}</p><strong>${rating}</strong></div>`).join('');
    ratingTotal.textContent = ratings[filter];
  };
  controls.forEach((control) => control.addEventListener('click', () => {
    controls.forEach((item) => item.setAttribute('aria-pressed', String(item === control)));
    update(control.dataset.filter);
  }));
})();
"""

_CSS = r"""
.cm-page { width: 100%; height: 1120px; overflow: hidden; background: #fff; color: #173f3b; font-family: Arial, Helvetica, sans-serif; }
.cm-page * { box-sizing: border-box; }
.cm-page h1, .cm-page h2, .cm-page h3, .cm-page p, .cm-page figure, .cm-page dl { margin: 0; }
.cm-page main { min-height: 0; }
.cm-page button, .cm-page input { font: inherit; }
.cm-page button { cursor: pointer; }
.cm-header { height: 94px; background: #fff; }
.cm-header-main { height: 65px; padding: 0 42px; display: grid; grid-template-columns: 245px 230px 1fr 220px 166px; align-items: center; gap: 18px; }
.cm-brand { display: flex; align-items: center; gap: 10px; color: #173f3b; }
.cm-brand-mark { width: 28px; height: 28px; border: 4px solid #48c78e; position: relative; }
.cm-brand-mark::after { content: ''; position: absolute; width: 8px; height: 13px; border-right: 3px solid #48c78e; border-bottom: 3px solid #48c78e; left: 6px; top: 2px; transform: rotate(35deg); }
.cm-brand strong { display: block; font-size: 19px; line-height: 20px; letter-spacing: 0; }
.cm-brand small { display: block; margin-top: 2px; color: #58645f; font-size: 12px; }
.cm-header-main > p { color: #58645f; font-size: 12px; line-height: 16px; }
.cm-header nav { display: flex; justify-content: center; gap: 25px; }
.cm-header nav a { color: #173f3b; font-size: 13px; font-weight: 700; text-decoration: none; }
.cm-header nav a.is-active { color: #48a977; }
.cm-phone b, .cm-phone span { display: block; }
.cm-phone b { font-size: 15px; color: #173f3b; }
.cm-phone span { margin-top: 3px; color: #58645f; font-size: 12px; }
.cm-coral-button { min-height: 42px; border: 0; background: #f35d50; color: #fff; font-size: 13px; font-weight: 700; padding: 0 16px; }
.cm-header-proof { height: 29px; padding: 0 42px; display: grid; grid-template-columns: 1.35fr 1fr 1fr 1fr; align-items: center; background: #173f3b; color: #fff; }
.cm-header-proof b, .cm-header-proof span { padding-left: 12px; border-left: 1px solid #42615c; font-size: 12px; }
.cm-header-proof b { border-left: 0; color: #8ce0af; padding-left: 0; }
.cm-eyebrow, .cm-route-title span, .cm-evidence-head b, .cm-after-handoff span, .cm-calculator-summary > span, .cm-calculator-scope span, .cm-checklist-workspace aside > span, .cm-checklist-acceptance span, .cm-crew-profile > span { color: #359b6a; font-size: 12px; font-weight: 700; text-transform: uppercase; }
.cm-cover-main { height: 700px; display: grid; grid-template-columns: 53% 47%; }
.cm-cover-copy { padding: 46px 44px 24px 42px; background: #fff; }
.cm-cover-copy h1 { margin-top: 17px; color: #173f3b; font-size: 47px; line-height: 51px; letter-spacing: 0; }
.cm-cover-copy h1 em { color: #48c78e; font-style: normal; }
.cm-lead { max-width: 540px; margin-top: 17px !important; color: #58645f; font-size: 15px; line-height: 22px; }
.cm-cover-facts { margin-top: 22px; display: grid; grid-template-columns: repeat(3, 1fr); border-top: 1px solid #c6ddd1; border-bottom: 1px solid #c6ddd1; }
.cm-cover-facts div { padding: 12px 11px 12px 0; border-right: 1px solid #c6ddd1; }
.cm-cover-facts div + div { padding-left: 13px; }
.cm-cover-facts dt { color: #173f3b; font-size: 13px; font-weight: 700; }
.cm-cover-facts dd { margin: 4px 0 0; color: #58645f; font-size: 12px; }
.cm-cover-calculator { margin-top: 22px; padding: 17px 19px; background: #eaf8f1; border-top: 4px solid #48c78e; }
.cm-calc-head { display: flex; justify-content: space-between; align-items: baseline; }
.cm-calc-head b { font-size: 16px; color: #173f3b; }
.cm-calc-head span { color: #58645f; font-size: 12px; }
.cm-cover-controls { margin-top: 14px; display: grid; grid-template-columns: 135px 1fr 215px; gap: 12px; align-items: end; }
.cm-cover-controls label, .cm-calculator-form > label { display: grid; gap: 6px; color: #58645f; font-size: 12px; font-weight: 700; }
.cm-page input[type="number"] { height: 38px; padding: 0 10px; border: 1px solid #a8c7b7; background: #fff; color: #173f3b; font-size: 15px; font-weight: 700; }
.cm-page fieldset { min-width: 0; margin: 0; padding: 0; border: 0; }
.cm-page legend { margin-bottom: 6px; color: #58645f; font-size: 12px; font-weight: 700; }
.cm-cover-controls fieldset { display: grid; grid-template-columns: 1fr 1.45fr; }
.cm-cover-controls fieldset button, .cm-calculator-form fieldset button, .cm-checklist-main nav button, .cm-reviews-ledger-wrap nav button { min-height: 38px; border: 1px solid #a8c7b7; background: #fff; color: #173f3b; font-size: 12px; }
.cm-cover-controls fieldset button + button { border-left: 0; }
.cm-page button[aria-pressed="true"] { background: #173f3b; border-color: #173f3b; color: #fff; }
.cm-check { display: flex !important; align-items: center; gap: 7px; min-height: 38px; color: #173f3b !important; font-size: 12px !important; font-weight: 700; }
.cm-check input { width: 16px; height: 16px; accent-color: #48c78e; }
.cm-cover-quote { margin-top: 14px; padding-top: 13px; display: grid; grid-template-columns: 1.08fr 1.23fr 160px; align-items: end; border-top: 1px solid #b8d4c5; }
.cm-cover-quote span, .cm-cover-quote small { display: block; color: #58645f; font-size: 12px; line-height: 16px; }
.cm-cover-quote strong { display: block; margin-top: 4px; color: #173f3b; font-size: 27px; }
.cm-cover-quote b { display: block; margin: 5px 0 1px; color: #359b6a; font-size: 13px; line-height: 17px; }
.cm-cover-quote .cm-coral-button { width: 100%; }
.cm-cover-media { position: relative; background: #f1f3f1; overflow: hidden; }
.cm-cover-media img { width: 100%; height: 700px; object-fit: cover; }
.cm-cover-media figcaption { position: absolute; right: 0; bottom: 0; width: 340px; padding: 17px 21px; background: #eaf8f1; }
.cm-cover-media figcaption b, .cm-cover-media figcaption span { display: block; }
.cm-cover-media figcaption b { color: #173f3b; font-size: 14px; }
.cm-cover-media figcaption span { margin-top: 5px; color: #58645f; font-size: 12px; line-height: 16px; }
.cm-cover-readiness { margin-top: 18px; padding-top: 13px; display: grid; grid-template-columns: repeat(3, 1fr); border-top: 1px solid #c6ddd1; }
.cm-cover-readiness > div { padding-right: 13px; border-right: 1px solid #c6ddd1; }
.cm-cover-readiness > div + div { padding-left: 13px; }
.cm-cover-readiness > div:last-child { border: 0; }
.cm-cover-readiness span { color: #359b6a; font-size: 12px; font-weight: 700; text-transform: uppercase; }
.cm-cover-readiness b { display: block; margin-top: 5px; color: #173f3b; font-size: 13px; line-height: 17px; }
.cm-cover-readiness p { margin-top: 4px; color: #58645f; font-size: 12px; line-height: 16px; }
.cm-cover-proof { height: 326px; display: grid; grid-template-columns: repeat(4, 1fr); background: #173f3b; color: #fff; }
.cm-cover-proof article { padding: 39px 29px 24px 42px; border-right: 1px solid #45635d; }
.cm-cover-proof span { display: block; color: #8ce0af; font-size: 14px; font-weight: 700; }
.cm-cover-proof b { display: block; margin-top: 17px; font-size: 17px; line-height: 22px; }
.cm-cover-proof p { margin-top: 12px; color: #d0e4db; font-size: 12px; line-height: 18px; }
.cm-route-title { height: 132px; padding: 31px 42px 24px; display: grid; grid-template-columns: 1.2fr .8fr; align-items: end; border-bottom: 1px solid #c6ddd1; }
.cm-route-title h1 { margin-top: 9px; color: #173f3b; font-size: 34px; line-height: 38px; }
.cm-route-title > p { padding: 0 0 3px 22px; border-left: 3px solid #48c78e; color: #58645f; font-size: 13px; line-height: 19px; }
.cm-evidence { height: 610px; padding: 24px 42px; display: grid; grid-template-columns: 1fr 1fr 345px; grid-template-rows: 61px 477px; gap: 12px 18px; background: #f1f3f1; }
.cm-evidence-head { grid-column: 1 / -1; display: flex; align-items: center; gap: 27px; border-bottom: 1px solid #bdd5c8; }
.cm-evidence-head b { color: #359b6a; }
.cm-evidence-head span { max-width: 700px; color: #58645f; font-size: 13px; line-height: 18px; }
.cm-evidence figure { position: relative; height: 477px; overflow: hidden; background: #fff; }
.cm-evidence figure img { width: 100%; height: 477px; object-fit: cover; }
.cm-evidence figure figcaption { position: absolute; left: 0; bottom: 0; padding: 12px 16px; background: #173f3b; color: #fff; font-size: 12px; font-weight: 700; }
.cm-evidence aside { padding: 23px 24px; background: #fff; border-top: 4px solid #48c78e; }
.cm-evidence aside > span { color: #359b6a; font-size: 12px; font-weight: 700; text-transform: uppercase; }
.cm-evidence ol { margin: 14px 0 0; padding: 0; list-style: none; }
.cm-evidence li { padding: 11px 0; border-top: 1px solid #c6ddd1; color: #58645f; font-size: 12px; line-height: 17px; }
.cm-evidence li b { display: inline-block; width: 49px; color: #173f3b; font-size: 12px; }
.cm-evidence aside strong { display: block; margin-top: 16px; color: #173f3b; font-size: 14px; }
.cm-after-handoff { height: 278px; display: grid; grid-template-columns: 1.15fr 1fr 1fr 176px; background: #173f3b; color: #fff; }
.cm-after-handoff > div, .cm-after-handoff > button { margin: 34px 0; padding: 0 24px; border-right: 1px solid #42615c; }
.cm-after-handoff span { color: #8ce0af; }
.cm-after-handoff b { display: block; margin-top: 15px; font-size: 16px; line-height: 21px; }
.cm-after-handoff p { margin-top: 10px; color: #d0e4db; font-size: 12px; line-height: 17px; }
.cm-after-handoff > button { align-self: center; height: 48px; margin-right: 42px; padding: 0 12px; border: 0; }
.cm-calculator-workspace { height: 620px; padding: 25px 42px; display: grid; grid-template-columns: 390px 410px 1fr; gap: 20px; background: #eaf8f1; }
.cm-calculator-form { padding: 23px; background: #fff; border-top: 4px solid #48c78e; }
.cm-calculator-form > label { margin-bottom: 14px; }
.cm-calculator-form > label input { height: 46px; font-size: 20px; }
.cm-calculator-form fieldset + fieldset { margin-top: 13px; }
.cm-calculator-form .cm-room-type, .cm-calculator-form .cm-urgency { display: grid; grid-template-columns: repeat(3, 1fr); }
.cm-calculator-form .cm-room-type legend, .cm-calculator-form .cm-urgency legend { grid-column: 1 / -1; }
.cm-calculator-form .cm-room-type button + button, .cm-calculator-form .cm-urgency button + button { border-left: 0; }
.cm-calculator-form .cm-check { min-height: 30px; }
.cm-form-note { margin-top: 11px !important; padding-top: 10px; border-top: 1px solid #c6ddd1; color: #58645f; font-size: 12px; line-height: 17px; }
.cm-calculator-summary { padding: 29px; background: #173f3b; color: #fff; border-top: 5px solid #48c78e; }
.cm-calculator-summary > span { color: #8ce0af; }
.cm-calculator-summary > strong { display: block; margin-top: 12px; font-size: 42px; }
.cm-calculator-summary > b { display: block; margin-top: 10px; color: #8ce0af; font-size: 14px; }
.cm-calculator-summary dl { margin-top: 26px; border-top: 1px solid #50716b; }
.cm-calculator-summary dl div { padding: 14px 0; display: flex; justify-content: space-between; border-bottom: 1px solid #50716b; }
.cm-calculator-summary dt { color: #d0e4db; font-size: 12px; }
.cm-calculator-summary dd { margin: 0; font-size: 13px; font-weight: 700; }
.cm-calculator-summary .cm-coral-button { width: 100%; margin-top: 22px; }
.cm-equipment { height: 570px; background: #fff; }
.cm-equipment img { width: 100%; height: 475px; object-fit: cover; }
.cm-equipment figcaption { padding: 13px 16px; }
.cm-equipment figcaption b, .cm-equipment figcaption span { display: block; }
.cm-equipment figcaption b { font-size: 14px; }
.cm-equipment figcaption span { margin-top: 4px; color: #58645f; font-size: 12px; }
.cm-calculator-scope { height: 274px; padding: 30px 42px; display: grid; grid-template-columns: 1.2fr 1fr 1fr; gap: 28px; background: #f1f3f1; }
.cm-calculator-scope > div { padding-right: 22px; border-right: 1px solid #c7d9d0; }
.cm-calculator-scope > div:last-child { border: 0; }
.cm-calculator-scope b { display: block; margin-top: 14px; color: #173f3b; font-size: 16px; }
.cm-calculator-scope p { margin-top: 10px; color: #58645f; font-size: 12px; line-height: 18px; }
.cm-checklist-workspace { height: 620px; display: grid; grid-template-columns: 390px 1fr; }
.cm-checklist-workspace aside { padding: 26px 34px; background: #173f3b; color: #fff; }
.cm-checklist-workspace aside figure { height: 272px; margin-bottom: 19px; }
.cm-checklist-workspace aside img { width: 100%; height: 272px; object-fit: cover; }
.cm-checklist-workspace aside > span { color: #8ce0af; }
.cm-checklist-workspace aside b { display: block; margin-top: 12px; font-size: 18px; line-height: 23px; }
.cm-checklist-workspace aside p { margin-top: 9px; color: #d0e4db; font-size: 12px; line-height: 18px; }
.cm-checklist-workspace aside small { display: block; margin-top: 18px; color: #8ce0af; font-size: 12px; }
.cm-checklist-main { padding: 26px 42px; background: #fff; }
.cm-checklist-main nav { display: grid; grid-template-columns: repeat(4, 1fr); }
.cm-checklist-main nav button + button { border-left: 0; }
.cm-zone-summary { margin-top: 22px; padding: 18px 20px; display: grid; grid-template-columns: 250px 1fr; align-items: center; background: #eaf8f1; border-left: 5px solid #48c78e; }
.cm-zone-summary span { color: #359b6a; font-size: 12px; font-weight: 700; }
.cm-zone-summary b { color: #173f3b; font-size: 18px; }
.cm-zone-summary p { grid-column: 1 / -1; margin-top: 8px; color: #58645f; font-size: 12px; }
.cm-zone-summary small { grid-column: 1 / -1; margin-top: 4px; color: #58645f; font-size: 12px; }
.cm-checklist-main ul { margin: 14px 0 0; padding: 0; list-style: none; }
.cm-checklist-main li { padding: 10px 0 10px 19px; position: relative; border-bottom: 1px solid #c6ddd1; color: #173f3b; font-size: 13px; }
.cm-checklist-main li::before { content: ''; position: absolute; width: 8px; height: 8px; left: 0; top: 13px; background: #48c78e; }
.cm-exclusion { margin-top: 14px !important; padding: 10px 14px; background: #f1f3f1; color: #58645f; font-size: 12px; }
.cm-checklist-acceptance { height: 264px; padding: 31px 42px; display: grid; grid-template-columns: repeat(3, 1fr); background: #eaf8f1; }
.cm-checklist-acceptance > div { padding-right: 30px; border-right: 1px solid #c7d9d0; }
.cm-checklist-acceptance > div + div { padding-left: 30px; }
.cm-checklist-acceptance > div:last-child { border: 0; }
.cm-checklist-acceptance b { display: block; margin-top: 15px; font-size: 16px; line-height: 21px; }
.cm-checklist-acceptance p { margin-top: 10px; color: #58645f; font-size: 12px; line-height: 18px; }
.cm-reviews-workspace { height: 620px; padding: 25px 42px; display: grid; grid-template-columns: 1fr 405px; gap: 24px; background: #f1f3f1; }
.cm-reviews-ledger-wrap { background: #fff; border-top: 4px solid #48c78e; }
.cm-reviews-ledger-wrap nav { display: grid; grid-template-columns: repeat(3, 1fr); }
.cm-reviews-ledger-wrap nav button + button { border-left: 0; }
.cm-review-ledger { padding: 11px 23px 0; }
.cm-review-row { min-height: 88px; display: grid; grid-template-columns: 110px 1fr 1.2fr 54px; gap: 15px; align-items: center; border-bottom: 1px solid #c6ddd1; }
.cm-review-row span { color: #58645f; font-size: 12px; }
.cm-review-row b { color: #173f3b; font-size: 14px; }
.cm-review-row p { color: #58645f; font-size: 12px; line-height: 17px; }
.cm-review-row strong { color: #359b6a; font-size: 16px; text-align: right; }
.cm-review-rating { padding: 16px 23px; color: #173f3b; font-size: 14px; font-weight: 700; }
.cm-crew-profile { padding: 22px; background: #173f3b; color: #fff; border-top: 4px solid #48c78e; }
.cm-crew-profile figure { height: 293px; margin-bottom: 16px; }
.cm-crew-profile img { width: 100%; height: 293px; object-fit: cover; object-position: center top; }
.cm-crew-profile > span { color: #8ce0af; }
.cm-crew-profile > b { display: block; margin-top: 7px; font-size: 19px; }
.cm-crew-profile p { margin-top: 7px; color: #d0e4db; font-size: 12px; line-height: 17px; }
.cm-crew-profile > strong { display: block; margin-top: 13px; color: #8ce0af; font-size: 13px; line-height: 17px; }
.cm-crew-profile .cm-coral-button { width: 100%; margin-top: 15px; }
.cm-reviews-metrics { height: 264px; padding: 0 42px; display: grid; grid-template-columns: repeat(4, 1fr); background: #173f3b; color: #fff; }
.cm-reviews-metrics div { padding: 45px 28px 20px 0; border-right: 1px solid #42615c; }
.cm-reviews-metrics div + div { padding-left: 28px; }
.cm-reviews-metrics div:last-child { border: 0; }
.cm-reviews-metrics span { display: block; color: #8ce0af; font-size: 27px; font-weight: 700; }
.cm-reviews-metrics b { display: block; margin-top: 10px; font-size: 14px; line-height: 19px; }
"""

_BODY_RENDERERS = {
    "cover": _cover,
    "after-renovation": _after_renovation,
    "calculator": _calculator,
    "checklist": _checklist,
    "reviews": _reviews,
}

_ROUTE_SCRIPTS = {
    "cover": _COVER_SCRIPT,
    "after-renovation": "",
    "calculator": _CALCULATOR_SCRIPT,
    "checklist": _CHECKLIST_SCRIPT,
    "reviews": _REVIEWS_SCRIPT,
}


def render(
    project: ProjectSpec,
    shot: ShotSpec,
    assets: Mapping[str, str],
) -> RenderedPage:
    """Render one standalone Chistiy Metr route with owned local assets."""
    if project.slug != "chistiy-metr":
        raise KeyError(f"chistiy-metr renderer cannot render {project.slug}")
    try:
        body_renderer = _BODY_RENDERERS[shot.key]
    except KeyError as exc:
        raise ValueError(f"chistiy-metr unknown route: {shot.key}") from exc

    owned = _owned_assets(shot.key, assets)
    return RenderedPage(
        html=(
            f'<div class="cm-page" data-site="chistiy-metr" '
            f'data-route="{escape_html(shot.key)}">{_header(shot.key)}'
            f"{body_renderer(owned)}</div>"
        ),
        css=_CSS,
        scripts=_ROUTE_SCRIPTS[shot.key],
    )
