"""Dedicated premium desktop renderer for the Dentalea dental clinic."""

from collections.abc import Mapping

from ..components import escape_html
from ..icons import icon
from ..models import ProjectSpec, ShotSpec
from .runtime import RenderedPage


_ROUTE_ASSETS = {
    "cover": ("consultation_room",),
    "implantation": ("treatment_detail",),
    "booking": ("clinic_exterior",),
    "case-study": ("smile_case_before", "smile_case_after"),
    "prices": ("doctor_portrait",),
}


def _asset(
    project: ProjectSpec, shot: ShotSpec, assets: Mapping[str, str], key: str
) -> str:
    try:
        return escape_html(assets[key])
    except KeyError as exc:
        raise KeyError(
            f"dentalea renderer {project.slug}/{shot.key} is missing asset {key}"
        ) from exc


def _header(active: str) -> str:
    nav = (
        ("Лечение", "implantation"),
        ("Врачи", "prices"),
        ("Клиника", "cover"),
        ("Пациентам", "booking"),
    )
    links = "".join(
        f'<span class="da-nav-item{" da-nav-active" if route == active else ""}">{label}</span>'
        for label, route in nav
    )
    return (
        '<header class="da-header">'
        '<div class="da-brand"><span>ДЕНТАЛЕЯ</span><small>стоматологическая клиника</small></div>'
        f'<nav class="da-nav" aria-label="Основная навигация">{links}</nav>'
        '<div class="da-header-contact"><b>+7 (495) 120-00-20</b><small>Москва, ул. Тверская, 12</small></div>'
        f'<button type="button" class="da-header-action">{icon("calendar", size=17)}Записаться на приём</button>'
        "</header>"
    )


def _cover(project: ProjectSpec, shot: ShotSpec, assets: Mapping[str, str]) -> str:
    source = _asset(project, shot, assets, "consultation_room")
    return (
        f'{_header("cover")}'
        '<section class="da-cover-hero">'
        '<div class="da-cover-copy">'
        '<p class="da-section-label">Бережная стоматология для взрослых</p>'
        '<h1>Стоматология, где спокойно лечиться</h1>'
        '<p class="da-lead">Начинаем с диагностики, объясняем варианты и составляем план лечения до начала работ.</p>'
        '<div class="da-cover-actions"><button type="button" class="da-primary">Первичная консультация</button><button type="button" class="da-text-button">Как проходит первый приём</button></div>'
        '<div class="da-cover-facts"><span>60 минут на знакомство с планом</span><span>Без навязанных процедур</span></div>'
        "</div>"
        '<div class="da-cover-media"><img src="'
        f'{source}" alt="Врач обсуждает лечение с пациентом" />'
        '<div class="da-cover-note"><b>План лечения до начала работ</b><span>Стоимость, сроки и приоритеты в одной карте.</span></div>'
        "</div>"
        "</section>"
        '<section class="da-trust-strip">'
        '<div><b>12 лет</b><span>работаем с клиническими протоколами</span></div>'
        '<div><b>4.9 / 5</b><span>средняя оценка пациентов</span></div>'
        '<div><b>1 клиника</b><span>всё лечение в одном месте</span></div>'
        '<div><b>3D-диагностика</b><span>до начала любого сложного лечения</span></div>'
        "</section>"
        '<section class="da-cover-bottom"><div><p class="da-section-label">Подход клиники</p><h2>Видеть лечение целиком, а не отдельную процедуру</h2></div><ol><li><b>01</b><span>Осмотр и снимки</span></li><li><b>02</b><span>Понятные варианты</span></li><li><b>03</b><span>Контроль результата</span></li></ol></section>'
    )


def _implantation(project: ProjectSpec, shot: ShotSpec, assets: Mapping[str, str]) -> str:
    source = _asset(project, shot, assets, "treatment_detail")
    stages = "".join(
        f'<li><span>{number}</span><div><b>{title}</b><p>{copy}</p></div></li>'
        for number, title, copy in (
            ("01", "Диагностика и 3D-планирование", "Снимки, фотопротокол и цифровой макет будущей улыбки."),
            ("02", "Подготовка и установка", "Согласуем этапы, работаем с анестезией и контролируем приживление."),
            ("03", "Постоянная конструкция", "Проверяем посадку, прикус и даём план дальнейшего наблюдения."),
        )
    )
    return (
        f'{_header("implantation")}'
        '<section class="da-implant-layout">'
        '<aside class="da-implant-aside"><p class="da-section-label">Имплантация зубов</p><h1>Имплантация с поэтапным планом</h1><p>Никаких решений в кресле: сначала оцениваем ткани, риски и сроки восстановления.</p><div class="da-implant-stat"><b>2-4 визита</b><span>до постоянной коронки по клиническому плану</span></div><section class="da-implant-candidacy"><p>Диагностические факты</p><ul><li>КТ показывает объём кости и положение пазух.</li><li>Осмотр тканей помогает выбрать срок нагрузки.</li></ul><div class="da-implant-aside-details"><div><b>Что входит в план</b><span>Снимки, шаблон и контроль приживления.</span></div><div><b>Риски, которые обсуждаем заранее</b><span>Дефицит кости, сроки заживления и альтернативы.</span></div></div></section></aside>'
        '<div class="da-implant-main">'
        f'<img class="da-treatment-media" src="{source}" alt="Цифровое планирование имплантации" />'
        '<div class="da-implant-content"><div><h2>План лечения строится вокруг вашей ситуации</h2><p>Врач показывает снимки, объясняет альтернативы и выдаёт план с последовательностью процедур.</p></div><ol class="da-stage-list">'
        f"{stages}</ol></div>"
        '<section class="da-implant-checkpoint"><div><p class="da-section-label">Клиническая контрольная точка</p><h3>Лист результата</h3></div><div><b>До установки</b><span>Проверяем положение импланта по КТ.</span></div><div><b>Перед коронкой</b><span>Сверяем прикус и нагрузку на ткани.</span></div></section>'
        "</div>"
        "</section>"
        '<section class="da-financing"><div class="da-financing-intro"><p class="da-section-label">Оплата лечения</p><h2>Рассрочка без переплат</h2><span>Сумму и порядок платежей фиксируем в плане.</span></div><div class="da-financing-comparison"><div><b>6 месяцев</b><strong>260 000 ₽</strong><span>от 43 334 ₽ в месяц</span><small>Первый платёж через 30 дней</small></div><div><b>12 месяцев</b><strong>260 000 ₽</strong><span>от 21 667 ₽ в месяц</span><small>0% при одобрении банка-партнёра</small></div></div><div class="da-financing-cta"><p>Условия: паспорт, решение банка и возможность досрочного погашения без комиссии.</p><button type="button" class="da-primary">Рассчитать свой план</button></div></section>'
    )


def _booking(project: ProjectSpec, shot: ShotSpec, assets: Mapping[str, str]) -> str:
    source = _asset(project, shot, assets, "clinic_exterior")
    days = "".join(
        f'<button type="button" class="da-date-choice{" active" if index == 1 else ""}" data-selectable="appointment-date" data-date="{date}" aria-pressed="{"true" if index == 1 else "false"}"><span>{weekday}</span><b>{day}</b></button>'
        for index, weekday, day, date in (
            (0, "Пн", "26", "Понедельник, 26 августа"),
            (1, "Вт", "27", "Вторник, 27 августа"),
            (2, "Ср", "28", "Среда, 28 августа"),
            (3, "Чт", "29", "Четверг, 29 августа"),
            (4, "Пт", "30", "Пятница, 30 августа"),
        )
    )
    times = "".join(
        f'<button type="button" class="da-time-choice{" active" if index == 0 else ""}" data-selectable="appointment-time" data-time="{time}" aria-pressed="{"true" if index == 0 else "false"}">{time}</button>'
        for index, time in enumerate(("10:00", "12:30", "16:30", "18:00"))
    )
    reasons = "".join(
        f'<button type="button" class="da-reason-choice{" active" if index == 0 else ""}" data-selectable="appointment-reason" data-reason="{reason}" aria-pressed="{"true" if index == 0 else "false"}">{reason}</button>'
        for index, reason in enumerate(
            ("Консультация", "Острая боль", "Имплантация", "Профилактика")
        )
    )
    return (
        f'{_header("booking")}'
        '<section class="da-booking-layout">'
        '<div class="da-booking-main"><p class="da-section-label">Запись на консультацию</p><h1>Выберите удобное время приёма</h1><p class="da-booking-lead">Первичная консультация занимает 60 минут: врач изучит ситуацию, покажет варианты и ответит на вопросы.</p>'
        '<div class="da-booking-step"><div class="da-step-number">1</div><div><b>Дата приёма</b><div class="da-date-grid">'
        f"{days}</div></div></div>"
        '<div class="da-booking-step"><div class="da-step-number">2</div><div><b>Время</b><div class="da-time-grid">'
        f"{times}</div></div></div>"
        '<div class="da-booking-step da-service-step"><div class="da-step-number">3</div><div><b>Причина обращения</b><div class="da-reason-grid" role="group" aria-label="Причина обращения">'
        f"{reasons}</div><div class=\"da-confirmation-row\"><span>Подтверждение</span><div role=\"group\" aria-label=\"Способ подтверждения\"><button type=\"button\" class=\"da-confirmation-choice active\" data-selectable=\"confirmation-method\" data-confirmation=\"Звонок\" aria-pressed=\"true\">Звонок</button><button type=\"button\" class=\"da-confirmation-choice\" data-selectable=\"confirmation-method\" data-confirmation=\"SMS\" aria-pressed=\"false\">SMS</button></div><label class=\"da-consent\"><input type=\"checkbox\" data-consent=\"appointment\" checked />Согласие на связь по записи</label></div></div></div>"
        '<div class="da-booking-step da-contact-step"><div class="da-step-number">4</div><div><b>Контакт для подтверждения</b><div class="da-contact-form"><label>Имя<input value="Мария" aria-label="Имя пациента" /></label><label>Телефон<input value="+7 999 123-45-67" aria-label="Телефон пациента" /></label><button type="button" class="da-primary">Подтвердить запись</button></div></div></div>'
        '<section class="da-visit-includes"><div><p class="da-section-label">60 минут у врача</p><h2>Что входит в первичную консультацию</h2></div><ul><li>Осмотр и разговор о жалобах</li><li>Снимки при клинической необходимости</li><li>Варианты лечения и порядок этапов</li><li>Расчёт сроков и следующих действий</li></ul></section>'
        '<section class="da-booking-assurance"><div><b>Что взять на приём</b><span>Паспорт и прежние снимки, если они есть.</span></div><div><b>До консультации</b><span>Не нужно соблюдать специальную подготовку.</span></div><div><b>После приёма</b><span>Получите понятный план и расчёт этапов.</span></div></section>'
        "</div>"
        '<aside class="da-booking-side">'
        f'<img src="{source}" alt="Вход в клинику Денталея" />'
        '<div class="da-booking-summary"><p>Ваш приём</p><h2>Анна Михайлова</h2><span>Стоматолог-терапевт</span><dl><div><dt>Дата</dt><dd class="da-booking-summary-date">Вторник, 27 августа</dd></div><div><dt>Время</dt><dd class="da-booking-summary-time">10:00</dd></div><div><dt>Причина</dt><dd class="da-booking-summary-reason">Консультация</dd></div><div><dt>Связь</dt><dd class="da-booking-summary-confirmation">Звонок</dd></div><div><dt>Адрес</dt><dd>Москва, ул. Тверская, 12</dd></div></dl><small>60 минут: осмотр, снимки при необходимости, ответы врача и следующий шаг в плане.</small></div>'
        '<div class="da-clinic-details"><b>Клиника на Тверской</b><span>5 минут от метро · вход с улицы</span><span>Пн-Сб, 9:00-21:00</span></div>'
        "</aside>"
        "</section>"
    )


def _case_study(project: ProjectSpec, shot: ShotSpec, assets: Mapping[str, str]) -> str:
    before = _asset(project, shot, assets, "smile_case_before")
    after = _asset(project, shot, assets, "smile_case_after")
    return (
        f'{_header("cover")}'
        '<section class="da-case-header"><div><p class="da-section-label">Клинический случай</p><h1>До и после: восстановили улыбку</h1><p>Мягкая коррекция цвета и формы с сохранением естественных пропорций лица.</p></div><dl><div><dt>Пациент</dt><dd>38 лет</dd></div><div><dt>Срок</dt><dd>8 недель лечения</dd></div><div><dt>Врач</dt><dd>Елена Фролова</dd></div></dl></section>'
        '<section class="da-case-evidence"><figure><img src="'
        f'{before}" alt="Улыбка до лечения" /><figcaption><b>До</b><span>Исходный оттенок и рельеф эмали</span></figcaption></figure>'
        '<figure><img src="'
        f'{after}" alt="Улыбка после лечения" /><figcaption><b>После</b><span>Ровный оттенок и естественный блеск</span></figcaption></figure>'
        '<aside><p class="da-section-label">Клинические показатели</p><h2>Детали, которые согласовали заранее</h2><ul><li><b>1.5 тона</b><span>мягкое осветление без эффекта белой маски</span></li><li><b>0.3 мм</b><span>точечная коррекция края без лишней обработки</span></li><li><b>2 контроля</b><span>для проверки оттенка и комфорта</span></li></ul></aside></section>'
        '<section class="da-case-bottom"><div><b>01</b><span>Фотопротокол и оттеночная карта</span></div><div><b>02</b><span>Согласование результата до процедуры</span></div><div><b>03</b><span>Контроль состояния через 14 дней</span></div></section>'
    )


def _prices(project: ProjectSpec, shot: ShotSpec, assets: Mapping[str, str]) -> str:
    source = _asset(project, shot, assets, "doctor_portrait")
    categories = "".join(
        f'<button type="button" class="da-price-category{" active" if index == 0 else ""}" data-selectable="price-category" data-title="{title}" data-availability="{availability}" data-doctor="{doctor}" data-schedule="{schedule}" data-rows="{rows}" aria-pressed="{"true" if index == 0 else "false"}">{label}</button>'
        for index, label, title, availability, rows, doctor, schedule in (
            (0, "Терапия", "Терапия", "Сегодня, 17:00", "Консультация|2 500 ₽|60 минут;Лечение кариеса|от 6 900 ₽|90 минут;Лечение каналов|от 12 500 ₽|120 минут;Замена пломбы|от 5 400 ₽|60 минут;Профессиональная гигиена|8 500 ₽|60 минут;Отбеливание|от 24 000 ₽|90 минут;Реставрация зуба|от 9 800 ₽|90 минут", "Анна Михайлова · терапевт", "17:00|Анна Михайлова;18:30|Ирина Громова;20:00|Анна Михайлова"),
            (1, "Хирургия", "Хирургия", "Завтра, 11:30", "Удаление зуба|от 5 800 ₽|45 минут;Имплантация|от 49 000 ₽|90 минут;Костная пластика|от 32 000 ₽|120 минут;Синус-лифтинг|от 38 000 ₽|120 минут;Установка формирователя|от 12 500 ₽|45 минут;Удаление восьмёрки|от 9 500 ₽|60 минут;Консультация хирурга|3 500 ₽|60 минут", "Михаил Савельев · хирург", "11:30|Михаил Савельев;15:00|Олег Воронцов;Сегодня, 19:00|Михаил Савельев"),
            (2, "Ортодонтия", "Ортодонтия", "Пятница, 14:00", "Консультация ортодонта|3 500 ₽|60 минут;Элайнеры|от 210 000 ₽|по плану;Брекет-система|от 185 000 ₽|по плану;Диагностика прикуса|от 8 900 ₽|90 минут;Ретейнер|от 12 000 ₽|45 минут;Активация системы|от 4 500 ₽|30 минут;Снятие брекетов|от 18 000 ₽|90 минут", "Елена Фролова · ортодонт", "14:00|Елена Фролова;16:30|София Назарова;18:00|Елена Фролова"),
        )
    )
    rows = "".join(
        f"<tr><td>{service}</td><td>{price}</td><td>{duration}</td></tr>"
        for service, price, duration in (
            ("Консультация", "2 500 ₽", "60 минут"),
            ("Лечение кариеса", "от 6 900 ₽", "90 минут"),
            ("Лечение каналов", "от 12 500 ₽", "120 минут"),
            ("Замена пломбы", "от 5 400 ₽", "60 минут"),
            ("Профессиональная гигиена", "8 500 ₽", "60 минут"),
            ("Отбеливание", "от 24 000 ₽", "90 минут"),
            ("Реставрация зуба", "от 9 800 ₽", "90 минут"),
        )
    )
    return (
        f'{_header("prices")}'
        '<section class="da-prices-layout"><div class="da-prices-head"><div><p class="da-section-label">Прозрачная стоимость</p><h1>Цены и свободные окна врачей</h1></div><p class="da-prices-copy">В плане лечения цена фиксируется до старта. При необходимости разбиваем лечение на этапы.</p></div>'
        '<div class="da-price-controls" role="group" aria-label="Категория услуг">'
        f"{categories}</div>"
        '<div class="da-price-content"><section class="da-price-matrix"><div class="da-matrix-heading"><h2>Терапия</h2><span>Стоимость за один этап</span></div><table><thead><tr><th>Услуга</th><th>Стоимость</th><th>Длительность</th></tr></thead><tbody>'
        f'{rows}</tbody></table><div class="da-finance-line"><b>Рассрочка 0%</b><span>на комплексные планы от 80 000 ₽, первый платёж через 30 дней</span><button type="button">Узнать условия</button></div></section>'
        '<aside class="da-doctor-availability"><img src="'
        f'{source}" alt="Стоматолог Денталея" /><div class="da-availability"><p>Ближайшая запись</p><h2>Сегодня, 17:00</h2><span class="da-availability-doctor">Анна Михайлова · терапевт</span><ul class="da-availability-schedule"><li><b>17:00</b><span>Анна Михайлова</span></li><li><b>18:30</b><span>Ирина Громова</span></li><li><b>20:00</b><span>Анна Михайлова</span></li></ul><button type="button" class="da-primary">Выбрать время</button></div></aside></div>'
        '<section class="da-prices-proof"><div class="da-prices-proof-intro"><p class="da-section-label">Условия до начала лечения</p><h2>Стоимость связана с планом, а не с неожиданностями</h2><span>После консультации вы получаете подробную карту этапов, сроки и способ оплаты.</span></div><div class="da-prices-proof-grid"><div><b>Что входит в стоимость</b><ul><li>Работа врача и ассистента</li><li>Расходные материалы</li><li>Контроль результата</li></ul></div><div><b>Порядок оплаты</b><ul><li>Смета до начала лечения</li><li>Оплата по этапам</li><li>0% на планы от 80 000 ₽</li></ul></div><div><b>Срок ответа по плану</b><ul><li>Снимки и фотопротокол</li><li>Расчёт этапов лечения</li><li>Письменный план за 24 часа</li></ul></div></div><div class="da-prices-proof-footer"><span>До оплаты вы видите полную смету, график этапов и условия рассрочки.</span><b>План без скрытых позиций</b><button type="button">Получить смету</button></div></section>'
        "</section>"
    )


_CSS = """
.da-page { width: 100%; height: 1120px; overflow: hidden; background: #ffffff; color: #242832; font-family: "Segoe UI", Arial, sans-serif; }
.da-page *, .da-page *::before, .da-page *::after { box-sizing: border-box; }
.da-page h1, .da-page h2, .da-page h3, .da-page p { margin: 0; }
.da-page button, .da-page input { font: inherit; }
.da-page button { cursor: pointer; }
.da-header { height: 104px; display: grid; grid-template-columns: 280px 1fr 240px 230px; align-items: center; gap: 24px; padding: 0 58px; border-bottom: 1px solid #dbe6e7; background: #ffffff; }
.da-brand { display: grid; gap: 3px; color: #075866; }
.da-brand span { font-size: 28px; font-weight: 800; line-height: 1; }
.da-brand small, .da-header-contact small { color: #737b86; font-size: 12px; line-height: 1.25; }
.da-nav { display: flex; align-items: center; gap: 34px; height: 100%; }
.da-nav-item { height: 100%; display: inline-flex; align-items: center; border-bottom: 3px solid transparent; color: #4d5661; font-size: 14px; font-weight: 650; }
.da-nav-active { border-color: #ff7662; color: #075866; }
.da-header-contact { display: grid; gap: 4px; justify-items: end; }
.da-header-contact b { font-size: 14px; }
.da-header-action, .da-primary { min-height: 44px; display: inline-flex; align-items: center; justify-content: center; gap: 8px; border: 1px solid #ff7662; background: #ff7662; color: #ffffff; font-size: 14px; font-weight: 750; padding: 0 18px; }
.da-header-action { justify-self: end; }
.da-section-label { color: #075866; font-size: 12px; font-weight: 800; line-height: 1.3; text-transform: uppercase; }
.da-cover-hero { height: 655px; display: grid; grid-template-columns: 51% 49%; overflow: hidden; }
.da-cover-copy { padding: 88px 48px 50px 90px; display: flex; flex-direction: column; align-items: flex-start; }
.da-cover-copy h1 { max-width: 610px; margin-top: 18px; font-size: 54px; line-height: 1.02; font-weight: 750; }
.da-lead { max-width: 545px; margin-top: 24px !important; color: #5f6973; font-size: 18px; line-height: 1.48; }
.da-cover-actions { display: flex; gap: 24px; align-items: center; margin-top: 32px; }
.da-text-button { min-height: 44px; border: 0; border-bottom: 1px solid #075866; background: #ffffff; color: #075866; font-size: 14px; font-weight: 700; }
.da-cover-facts { display: flex; gap: 28px; margin-top: auto; color: #5f6973; font-size: 12px; font-weight: 650; }
.da-cover-facts span { max-width: 175px; padding-left: 14px; border-left: 2px solid #ff7662; }
.da-cover-media { position: relative; height: 655px; overflow: hidden; background: #edf8f8; }
.da-cover-media img { width: 100%; height: 100%; object-fit: cover; object-position: 70% center; }
.da-cover-note { position: absolute; right: 32px; bottom: 32px; width: 278px; padding: 18px 20px; background: #ffffff; border-top: 3px solid #ff7662; box-shadow: 0 10px 24px rgba(7, 88, 102, .12); }
.da-cover-note b { display: block; font-size: 16px; line-height: 1.25; }
.da-cover-note span { display: block; margin-top: 8px; color: #737b86; font-size: 12px; line-height: 1.4; }
.da-trust-strip { height: 128px; display: grid; grid-template-columns: repeat(4, 1fr); border-top: 1px solid #dbe6e7; border-bottom: 1px solid #dbe6e7; }
.da-trust-strip div { padding: 26px 28px 22px; border-right: 1px solid #dbe6e7; }
.da-trust-strip div:last-child { border-right: 0; }
.da-trust-strip b { display: block; color: #075866; font-size: 23px; line-height: 1; }
.da-trust-strip span { display: block; max-width: 205px; margin-top: 9px; color: #737b86; font-size: 12px; line-height: 1.35; }
.da-cover-bottom { height: 233px; display: grid; grid-template-columns: 1fr 1.2fr; gap: 80px; padding: 30px 90px; background: #edf8f8; }
.da-cover-bottom h2 { max-width: 510px; margin-top: 10px; color: #075866; font-size: 24px; line-height: 1.16; }
.da-cover-bottom ol { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin: 0; padding: 30px 0 0; list-style: none; }
.da-cover-bottom li { display: grid; gap: 7px; padding-top: 10px; border-top: 1px solid #a9d4d3; }
.da-cover-bottom li b { color: #ff7662; font-size: 16px; }
.da-cover-bottom li span { font-size: 13px; line-height: 1.4; }
.da-implant-layout { height: 744px; display: grid; grid-template-columns: 34% 66%; }
.da-implant-aside { padding: 52px 38px 34px 76px; background: #edf8f8; }
.da-implant-aside h1 { margin-top: 18px; color: #075866; font-size: 42px; line-height: 1.04; }
.da-implant-aside > p:not(.da-section-label) { margin-top: 20px; color: #5f6973; font-size: 16px; line-height: 1.5; }
.da-implant-stat { margin-top: 30px; padding-top: 18px; border-top: 1px solid #9ccacb; }
.da-implant-stat b { display: block; color: #ff7662; font-size: 28px; }
.da-implant-stat span { display: block; margin-top: 8px; font-size: 12px; line-height: 1.4; }
.da-implant-candidacy { display: grid; gap: 10px; margin-top: 22px; padding-top: 16px; border-top: 1px solid #9ccacb; }
.da-implant-candidacy > p { color: #075866; font-size: 13px; font-weight: 800; }
.da-implant-candidacy ul { display: grid; gap: 7px; margin: 0; padding: 0; list-style: none; }
.da-implant-candidacy li { padding-left: 12px; color: #5f6973; font-size: 12px; line-height: 1.35; position: relative; }
.da-implant-candidacy li::before { content: ""; position: absolute; top: 6px; left: 0; width: 4px; height: 4px; background: #ff7662; }
.da-implant-aside-details { display: grid; gap: 9px; margin-top: 3px; }
.da-implant-aside-details div { display: grid; gap: 4px; padding-top: 9px; border-top: 1px solid #c4dfdf; }
.da-implant-aside-details b { color: #075866; font-size: 12px; }
.da-implant-aside-details span { color: #5f6973; font-size: 12px; line-height: 1.32; }
.da-implant-main { padding: 30px 58px 28px; }
.da-treatment-media { width: 100%; height: 260px; object-fit: cover; }
.da-implant-content { display: grid; grid-template-columns: .85fr 1.15fr; gap: 48px; padding-top: 24px; }
.da-implant-content h2 { color: #075866; font-size: 28px; line-height: 1.12; }
.da-implant-content p { margin-top: 14px; color: #737b86; font-size: 14px; line-height: 1.45; }
.da-stage-list { display: grid; gap: 0; margin: 0; padding: 0; list-style: none; }
.da-stage-list li { display: grid; grid-template-columns: 42px 1fr; gap: 16px; padding: 0 0 10px; margin-bottom: 10px; border-bottom: 1px solid #dbe6e7; }
.da-stage-list li:last-child { margin-bottom: 0; }
.da-stage-list li > span { color: #ff7662; font-size: 14px; font-weight: 800; }
.da-stage-list b { font-size: 15px; }
.da-stage-list p { margin-top: 5px; font-size: 12px; }
.da-implant-checkpoint { display: grid; grid-template-columns: 1.1fr 1fr 1fr; gap: 20px; margin-top: 18px; padding: 15px 0 0; border-top: 1px solid #dbe6e7; }
.da-implant-checkpoint h3 { margin-top: 6px; color: #075866; font-size: 18px; }
.da-implant-checkpoint > div:not(:first-child) { display: grid; gap: 5px; padding-left: 16px; border-left: 1px solid #dbe6e7; }
.da-implant-checkpoint b { font-size: 12px; }
.da-implant-checkpoint span { color: #737b86; font-size: 12px; line-height: 1.35; }
.da-financing { height: 272px; display: grid; grid-template-columns: .78fr 1.72fr; grid-template-rows: 1fr 56px; column-gap: 38px; padding: 30px 88px 20px; border-top: 1px solid #dbe6e7; }
.da-financing h2 { margin-top: 9px; color: #075866; font-size: 25px; line-height: 1.15; }
.da-financing-intro > span { display: block; margin-top: 11px; color: #737b86; font-size: 12px; line-height: 1.38; }
.da-financing-comparison { display: grid; grid-template-columns: 1fr 1fr; }
.da-financing-comparison > div { display: grid; align-content: start; gap: 7px; padding: 5px 22px; border-left: 1px solid #dbe6e7; }
.da-financing-comparison b { color: #075866; font-size: 13px; }
.da-financing-comparison strong { color: #242832; font-size: 20px; }
.da-financing-comparison span { color: #ff7662; font-size: 13px; font-weight: 800; }
.da-financing-comparison small { color: #737b86; font-size: 12px; line-height: 1.3; }
.da-financing-cta { grid-column: 1 / -1; display: flex; align-items: center; justify-content: space-between; gap: 26px; padding-top: 14px; border-top: 1px solid #dbe6e7; }
.da-financing-cta p { max-width: 800px; color: #737b86; font-size: 12px; line-height: 1.35; }
.da-financing-cta .da-primary { flex: 0 0 auto; min-height: 38px; font-size: 12px; }
.da-booking-layout { height: 1016px; display: grid; grid-template-columns: 1fr 420px; gap: 56px; padding: 46px 88px 38px; }
.da-booking-main { display: flex; flex-direction: column; }
.da-booking-main h1, .da-prices-head h1, .da-case-header h1 { margin-top: 14px; color: #075866; font-size: 40px; line-height: 1.06; }
.da-booking-lead { max-width: 640px; margin-top: 15px !important; color: #737b86; font-size: 15px; line-height: 1.45; }
.da-booking-step { display: grid; grid-template-columns: 34px 1fr; gap: 18px; padding: 18px 0; border-bottom: 1px solid #dbe6e7; }
.da-step-number { width: 28px; height: 28px; display: grid; place-items: center; background: #edf8f8; color: #075866; font-size: 13px; font-weight: 800; }
.da-booking-step b { font-size: 15px; }
.da-date-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; margin-top: 15px; }
.da-date-choice { min-height: 64px; display: grid; place-content: center; gap: 5px; border: 1px solid #dbe6e7; background: #ffffff; color: #737b86; }
.da-date-choice span { font-size: 12px; }
.da-date-choice b { color: #242832; font-size: 19px; }
.da-date-choice.active { border-color: #075866; background: #edf8f8; }
.da-time-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-top: 15px; }
.da-time-choice { min-height: 40px; border: 1px solid #dbe6e7; background: #ffffff; color: #242832; font-size: 13px; font-weight: 700; }
.da-time-choice.active { border-color: #075866; background: #075866; color: #ffffff; }
.da-reason-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; margin-top: 13px; }
.da-reason-choice { min-height: 38px; border: 1px solid #dbe6e7; background: #ffffff; color: #242832; font-size: 13px; font-weight: 700; text-align: left; padding: 0 13px; }
.da-reason-choice.active { border-color: #075866; background: #edf8f8; color: #075866; }
.da-confirmation-row { display: grid; grid-template-columns: 116px auto 1fr; align-items: center; gap: 12px; margin-top: 12px; color: #737b86; font-size: 12px; }
.da-confirmation-row > div { display: flex; }
.da-confirmation-choice { min-height: 32px; padding: 0 11px; border: 1px solid #dbe6e7; background: #ffffff; color: #5f6973; font-size: 12px; }
.da-confirmation-choice + .da-confirmation-choice { border-left: 0; }
.da-confirmation-choice.active { border-color: #075866; background: #075866; color: #ffffff; }
.da-consent { display: inline-flex; align-items: center; gap: 6px; color: #737b86; font-size: 12px; }
.da-consent input { width: 14px; height: 14px; accent-color: #075866; }
.da-contact-form { display: grid; grid-template-columns: 1fr 1fr auto; gap: 12px; margin-top: 15px; align-items: end; }
.da-contact-form label { display: grid; gap: 6px; color: #737b86; font-size: 12px; }
.da-contact-form input { height: 40px; min-width: 0; padding: 0 12px; border: 1px solid #dbe6e7; color: #242832; font-size: 13px; }
.da-contact-form .da-primary { min-height: 40px; white-space: nowrap; }
.da-visit-includes { display: grid; grid-template-columns: 250px 1fr; gap: 25px; margin: 20px 0 0 52px; padding: 16px 0; border-top: 1px solid #a9d4d3; border-bottom: 1px solid #a9d4d3; }
.da-visit-includes h2 { margin-top: 7px; color: #075866; font-size: 18px; line-height: 1.2; }
.da-visit-includes ul { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px 18px; margin: 0; padding: 0; list-style: none; }
.da-visit-includes li { padding-left: 12px; color: #5f6973; font-size: 12px; line-height: 1.32; position: relative; }
.da-visit-includes li::before { content: ""; position: absolute; top: 6px; left: 0; width: 4px; height: 4px; background: #ff7662; }
.da-booking-assurance { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin: 0 0 0 52px; padding: 14px 0; border-bottom: 1px solid #dbe6e7; }
.da-booking-assurance div { display: grid; gap: 6px; padding-right: 16px; border-right: 1px solid #dbe6e7; }
.da-booking-assurance div:last-child { border-right: 0; }
.da-booking-assurance b { color: #075866; font-size: 12px; }
.da-booking-assurance span { color: #737b86; font-size: 12px; line-height: 1.35; }
.da-booking-side { display: grid; grid-template-rows: 240px 1fr 134px; align-self: stretch; border-left: 1px solid #dbe6e7; }
.da-booking-side > img { width: 100%; height: 240px; object-fit: cover; }
.da-booking-summary { padding: 28px 28px 20px; background: #edf8f8; }
.da-booking-summary > p { color: #075866; font-size: 12px; font-weight: 800; text-transform: uppercase; }
.da-booking-summary h2 { margin-top: 12px; font-size: 26px; line-height: 1.1; }
.da-booking-summary > span { display: block; margin-top: 6px; color: #737b86; font-size: 13px; }
.da-booking-summary dl { display: grid; gap: 9px; margin: 22px 0 16px; }
.da-booking-summary dl div { display: grid; grid-template-columns: 72px 1fr; gap: 12px; padding-bottom: 7px; border-bottom: 1px solid #c4dfdf; }
.da-booking-summary dt { color: #737b86; font-size: 12px; }
.da-booking-summary dd { margin: 0; color: #242832; font-size: 13px; font-weight: 700; }
.da-booking-summary small { color: #737b86; font-size: 12px; line-height: 1.4; }
.da-clinic-details { display: grid; gap: 7px; padding: 18px 28px; border-top: 1px solid #a9d4d3; background: #075866; color: #ffffff; }
.da-clinic-details b { font-size: 13px; }
.da-clinic-details span { color: #c7e6e7; font-size: 12px; }
.da-case-header { height: 224px; display: grid; grid-template-columns: 1fr 500px; gap: 60px; padding: 34px 88px 24px; border-bottom: 1px solid #dbe6e7; }
.da-case-header h1 { font-size: 38px; }
.da-case-header > div > p:not(.da-section-label) { max-width: 620px; margin-top: 14px; color: #737b86; font-size: 15px; line-height: 1.45; }
.da-case-header dl { display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px; align-self: end; margin: 0; }
.da-case-header dl div { padding-top: 12px; border-top: 2px solid #ff7662; }
.da-case-header dt { color: #737b86; font-size: 12px; }
.da-case-header dd { margin: 7px 0 0; font-size: 14px; font-weight: 750; }
.da-case-evidence { height: 572px; display: grid; grid-template-columns: 1fr 1fr 350px; gap: 20px; padding: 24px 88px; }
.da-case-evidence figure { display: grid; grid-template-rows: 368px 1fr; margin: 0; border: 1px solid #dbe6e7; }
.da-case-evidence figure img { width: 100%; height: 368px; object-fit: cover; }
.da-case-evidence figcaption { display: grid; gap: 5px; padding: 16px 18px; }
.da-case-evidence figcaption b { color: #075866; font-size: 16px; }
.da-case-evidence figcaption span { color: #737b86; font-size: 12px; }
.da-case-evidence aside { padding: 22px; background: #edf8f8; }
.da-case-evidence aside h2 { margin-top: 12px; color: #075866; font-size: 24px; line-height: 1.15; }
.da-case-evidence ul { display: grid; gap: 13px; margin: 20px 0 0; padding: 0; list-style: none; }
.da-case-evidence li { display: grid; gap: 5px; padding-top: 10px; border-top: 1px solid #a9d4d3; }
.da-case-evidence li b { color: #ff7662; font-size: 20px; }
.da-case-evidence li span { color: #5f6973; font-size: 12px; line-height: 1.35; }
.da-case-bottom { height: 220px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 36px; padding: 34px 88px; background: #075866; color: #ffffff; }
.da-case-bottom div { display: grid; gap: 10px; padding-left: 18px; border-left: 1px solid #79b5b7; }
.da-case-bottom b { color: #ff9b8d; font-size: 16px; }
.da-case-bottom span { max-width: 240px; font-size: 15px; line-height: 1.35; }
.da-prices-layout { height: 1016px; padding: 32px 88px 24px; }
.da-prices-head { display: grid; grid-template-columns: 1fr 420px; gap: 70px; align-items: end; }
.da-prices-copy { color: #737b86; font-size: 15px; line-height: 1.45; }
.da-price-controls { display: flex; gap: 10px; margin-top: 20px; border-bottom: 1px solid #dbe6e7; }
.da-price-category { min-height: 44px; padding: 0 20px; border: 0; border-bottom: 3px solid transparent; background: #ffffff; color: #737b86; font-size: 14px; font-weight: 750; }
.da-price-category.active { border-color: #ff7662; color: #075866; }
.da-price-content { display: grid; grid-template-columns: 1fr 400px; gap: 32px; margin-top: 18px; }
.da-price-matrix { border-top: 3px solid #075866; }
.da-matrix-heading { display: flex; align-items: baseline; justify-content: space-between; padding: 13px 0; }
.da-matrix-heading h2 { color: #075866; font-size: 28px; }
.da-matrix-heading span { color: #737b86; font-size: 12px; }
.da-price-matrix table { width: 100%; border-collapse: collapse; font-size: 13px; }
.da-price-matrix th { padding: 9px 12px; border-top: 1px solid #dbe6e7; border-bottom: 1px solid #dbe6e7; color: #737b86; font-size: 12px; font-weight: 700; text-align: left; }
.da-price-matrix td { padding: 9px 12px; border-bottom: 1px solid #dbe6e7; }
.da-price-matrix td:nth-child(2) { color: #075866; font-weight: 800; }
.da-finance-line { display: grid; grid-template-columns: auto 1fr auto; gap: 18px; align-items: center; margin-top: 15px; padding: 13px 16px; background: #edf8f8; }
.da-finance-line b { color: #075866; font-size: 14px; }
.da-finance-line span { color: #737b86; font-size: 12px; }
.da-finance-line button { min-height: 36px; border: 1px solid #075866; background: #ffffff; color: #075866; font-size: 12px; font-weight: 750; }
.da-doctor-availability { display: grid; grid-template-rows: 178px 1fr; border-left: 1px solid #dbe6e7; }
.da-doctor-availability > img { width: 100%; height: 178px; object-fit: cover; object-position: center top; }
.da-availability { padding: 20px 26px; background: #edf8f8; }
.da-availability p { color: #075866; font-size: 12px; font-weight: 800; text-transform: uppercase; }
.da-availability h2 { margin-top: 8px; font-size: 23px; }
.da-availability span { display: block; margin-top: 8px; color: #737b86; font-size: 13px; }
.da-availability-schedule { display: grid; gap: 7px; margin: 16px 0 0; padding: 0; list-style: none; }
.da-availability-schedule li { display: grid; grid-template-columns: 72px 1fr; gap: 8px; padding-bottom: 6px; border-bottom: 1px solid #c4dfdf; }
.da-availability-schedule b { color: #075866; font-size: 12px; }
.da-availability-schedule span { margin: 0; color: #5f6973; font-size: 12px; }
.da-availability .da-primary { width: 100%; min-height: 38px; margin-top: 16px; font-size: 12px; }
.da-prices-proof { display: grid; grid-template-columns: 300px 1fr; grid-template-rows: 1fr auto; gap: 24px 42px; min-height: 340px; margin-top: 18px; padding: 24px; border-top: 1px solid #a9d4d3; background: #edf8f8; }
.da-prices-proof-intro { display: grid; align-content: start; gap: 10px; }
.da-prices-proof-intro h2 { color: #075866; font-size: 21px; line-height: 1.16; }
.da-prices-proof-intro span { color: #5f6973; font-size: 12px; line-height: 1.38; }
.da-prices-proof-grid { display: grid; grid-template-columns: repeat(3, 1fr); }
.da-prices-proof-grid > div { padding: 0 20px; border-left: 1px solid #c4dfdf; }
.da-prices-proof-grid b { color: #075866; font-size: 13px; }
.da-prices-proof-grid ul { display: grid; gap: 9px; margin: 15px 0 0; padding: 0; list-style: none; }
.da-prices-proof-grid li { padding-left: 12px; color: #5f6973; font-size: 12px; line-height: 1.3; position: relative; }
.da-prices-proof-grid li::before { content: ""; position: absolute; top: 6px; left: 0; width: 4px; height: 4px; background: #ff7662; }
.da-prices-proof-footer { grid-column: 1 / -1; display: grid; grid-template-columns: 1fr auto auto; align-items: center; gap: 26px; padding-top: 16px; border-top: 1px solid #a9d4d3; }
.da-prices-proof-footer span { color: #5f6973; font-size: 12px; }
.da-prices-proof-footer b { color: #075866; font-size: 13px; }
.da-prices-proof-footer button { min-height: 36px; border: 1px solid #075866; background: #ffffff; color: #075866; font-size: 12px; font-weight: 750; padding: 0 14px; }
"""


_SCRIPTS = """
(() => {
  const choose = (group, button) => {
    document.querySelectorAll(`[data-selectable="${group}"]`).forEach((item) => {
      const selected = item === button;
      item.classList.toggle("active", selected);
      item.setAttribute("aria-pressed", String(selected));
    });
  };
  document.querySelectorAll('[data-selectable="appointment-date"]').forEach((button) => {
    button.addEventListener("click", () => {
      choose("appointment-date", button);
      const target = document.querySelector(".da-booking-summary-date");
      if (target) target.textContent = button.dataset.date;
    });
  });
  document.querySelectorAll('[data-selectable="appointment-time"]').forEach((button) => {
    button.addEventListener("click", () => {
      choose("appointment-time", button);
      const target = document.querySelector(".da-booking-summary-time");
      if (target) target.textContent = button.dataset.time;
    });
  });
  document.querySelectorAll('[data-selectable="appointment-reason"]').forEach((button) => {
    button.addEventListener("click", () => {
      choose("appointment-reason", button);
      const target = document.querySelector(".da-booking-summary-reason");
      if (target) target.textContent = button.dataset.reason;
    });
  });
  document.querySelectorAll('[data-selectable="confirmation-method"]').forEach((button) => {
    button.addEventListener("click", () => {
      choose("confirmation-method", button);
      const target = document.querySelector(".da-booking-summary-confirmation");
      if (target) target.textContent = button.dataset.confirmation;
    });
  });
  document.querySelectorAll('[data-selectable="price-category"]').forEach((button) => {
    button.addEventListener("click", () => {
      choose("price-category", button);
      const heading = document.querySelector(".da-price-matrix h2");
      const availability = document.querySelector(".da-availability h2");
      const doctor = document.querySelector(".da-availability-doctor");
      const schedule = document.querySelector(".da-availability-schedule");
      const body = document.querySelector(".da-price-matrix tbody");
      if (heading) heading.textContent = button.dataset.title;
      if (availability) availability.textContent = button.dataset.availability;
      if (doctor) doctor.textContent = button.dataset.doctor;
      if (schedule) {
        schedule.replaceChildren(...button.dataset.schedule.split(";").map((row) => {
          const [time, clinician] = row.split("|");
          const entry = document.createElement("li");
          const timeCell = document.createElement("b");
          const clinicianCell = document.createElement("span");
          timeCell.textContent = time;
          clinicianCell.textContent = clinician;
          entry.append(timeCell, clinicianCell);
          return entry;
        }));
      }
      if (body) {
        body.replaceChildren(...button.dataset.rows.split(";").map((row) => {
          const entry = document.createElement("tr");
          row.split("|").forEach((value) => {
            const cell = document.createElement("td");
            cell.textContent = value;
            entry.append(cell);
          });
          return entry;
        }));
      }
    });
  });
})();
"""


def render(
    project: ProjectSpec, shot: ShotSpec, assets: Mapping[str, str]
) -> RenderedPage:
    """Render one route of the standalone Dentalea clinical site."""
    if project.slug != "dentalea":
        raise KeyError(f"dentalea renderer cannot render project {project.slug}")
    try:
        page_builder = {
            "cover": _cover,
            "implantation": _implantation,
            "booking": _booking,
            "case-study": _case_study,
            "prices": _prices,
        }[shot.key]
    except KeyError as exc:
        raise ValueError(f"dentalea renderer does not support route {shot.key}") from exc
    return RenderedPage(
        html=(
            f'<main class="da-page da-{shot.key}" data-site="dentalea" '
            f'data-route="{shot.key}">{page_builder(project, shot, assets)}</main>'
        ),
        css=_CSS,
        scripts=_SCRIPTS if shot.key in {"booking", "prices"} else "",
    )
