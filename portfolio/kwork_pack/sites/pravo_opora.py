"""Dedicated renderer for the Pravovaya Opora legal portfolio concept."""

from collections.abc import Mapping
from html import escape

from ..icons import icon
from ..models import ProjectSpec, ShotSpec
from .runtime import RenderedPage


def _header(active: str) -> str:
    links = (
        ("developer-disputes", "Споры с застройщиками"),
        ("assessment", "Оценка дела"),
        ("practice", "Практика"),
        ("consultation", "Консультация"),
    )
    nav = "".join(
        f'<a href="#" class="{"is-active" if key == active else ""}">{label}</a>'
        for key, label in links
    )
    return (
        '<header class="po-header"><div class="po-header-main">'
        '<a class="po-brand" href="#"><span class="po-shield">ПО</span><span><strong>ПРАВОВАЯ ОПОРА</strong>'
        '<small>ЮРИДИЧЕСКОЕ БЮРО</small></span></a>'
        f'<nav>{nav}</nav><div class="po-confidential"><span>Конфиденциально</span><b>Адвокатская тайна</b></div>'
        '<div class="po-phone"><b>+7 (495) 118-42-07</b><span>будни 9:00–20:00</span></div>'
        '<button class="po-header-cta" type="button">Оценить дело</button></div>'
        '<div class="po-trust"><b>Честно оцениваем перспективу до договора</b><span>Юристы с судебной практикой</span>'
        '<span>Стоимость фиксируется в соглашении</span><span>Документы храним защищённо</span></div></header>'
    )


def _cover(assets: Mapping[str, str]) -> str:
    photo = assets["consultation_table"]
    return (
        '<main class="po-route po-cover">'
        '<section class="po-cover-grid"><div class="po-cover-copy">'
        '<span class="po-case-note">ПОТРЕБИТЕЛЬСКИЕ И ИМУЩЕСТВЕННЫЕ СПОРЫ</span>'
        '<h1>Защищаем права в споре, а не продаём обещания</h1>'
        '<p>Разбираем документы, называем риски и строим путь от претензии до фактического взыскания.</p>'
        '<div class="po-cover-proof"><div><b>Письменный вывод</b><span>правовой путь, риски и следующие действия</span></div>'
        '<div><b>По документам</b><span>сроки называем после проверки оснований</span></div><div><b>Без обещаний результата</b><span>честно отмечаем слабые места позиции</span></div></div>'
        '<button class="po-primary" type="button">Получить оценку юриста '
        f'{icon("arrow-right", size=19)}</button></div>'
        '<figure class="po-cover-photo"><img src="'
        f'{photo}" alt="Юрист и клиент разбирают документы на консультации">'
        '<figcaption><b>Вы говорите с юристом, который ведёт дело</b><span>Без передачи между менеджером и исполнителем</span></figcaption></figure>'
        '<aside class="po-quick-assessment"><span>Оценка дела за одну минуту</span><h2>С чем связан спор?</h2>'
        '<div class="po-quick-options"><button type="button" data-selectable="quick-issue" data-value="developer" aria-pressed="true">Застройщик</button>'
        '<button type="button" data-selectable="quick-issue" data-value="consumer" aria-pressed="false">Покупка или услуга</button><button type="button" data-selectable="quick-issue" data-value="insurance" aria-pressed="false">Страховая</button>'
        '<button type="button" data-selectable="quick-issue" data-value="property" aria-pressed="false">Недвижимость</button></div>'
        '<label>Есть договор?<select><option>Да, на руках</option><option>Есть только переписка</option><option>Нет</option></select></label>'
        '<label>Кратко опишите ситуацию<textarea>Застройщик нарушил срок передачи квартиры</textarea></label>'
        '<div class="po-quick-result"><span>Первичный путь</span><b data-quick-path>Претензия → расчёт неустойки → иск</b><p data-quick-copy>Точный вывод после проверки договора и сроков.</p></div>'
        '<button class="po-gold" type="button">Передать документы</button><small>Не отправляем данные третьим лицам.</small></aside></section>'
        '<section class="po-outcomes"><div><span>ДЕЛО № 428</span><b>2 140 000 ₽</b><p>Взыскано с застройщика, включая штраф и расходы.</p></div>'
        '<div><span>ДЕЛО № 391</span><b>Замена товара</b><p>Техника заменена до суда после правовой претензии.</p></div>'
        '<div><span>ДЕЛО № 367</span><b>1 380 000 ₽</b><p>Страховое возмещение и неустойка.</p></div><div><span>КОНФИДЕНЦИАЛЬНОСТЬ</span><b>Данные обезличены</b><p>Публикуем только правовой результат.</p></div></section>'
        '<section class="po-cover-steps"><div><span>Четыре шага до результата</span><h2>Понятный статус на каждом этапе</h2></div>'
        '<ol><li><b>01</b><span>Проверяем документы и сроки</span></li><li><b>02</b><span>Фиксируем правовой путь и бюджет</span></li>'
        '<li><b>03</b><span>Ведём претензию и процесс</span></li><li><b>04</b><span>Контролируем фактическое взыскание</span></li></ol></section>'
        '</main>'
    )


def _developer(assets: Mapping[str, str]) -> str:
    photo = assets["office_exterior"]
    return (
        '<main class="po-route po-developer">'
        '<section class="po-developer-intro"><div><span>ДДУ · СРОКИ · КАЧЕСТВО КВАРТИРЫ</span>'
        '<h1>Взыскиваем с застройщика по документам и срокам</h1><p>Сначала проверяем договор, уведомления и акт, затем считаем требования по каждой правовой основе.</p></div>'
        f'<img src="{photo}" alt="Офис юридического бюро по спорам с застройщиками"></section>'
        '<section class="po-developer-work"><aside class="po-claim-types"><h2>Сценарий спора</h2>'
        '<button type="button" data-selectable="claim" data-value="delay" aria-pressed="true"><b>Нарушен срок передачи</b><span>Неустойка, штраф, убытки</span></button>'
        '<button type="button" data-selectable="claim" data-value="defects" aria-pressed="false"><b>Недостатки квартиры</b><span>Устранение или компенсация</span></button>'
        '<button type="button" data-selectable="claim" data-value="area" aria-pressed="false"><b>Изменена площадь</b><span>Перерасчёт цены договора</span></button>'
        '<button type="button" data-selectable="claim" data-value="terms" aria-pressed="false"><b>Навязаны условия</b><span>Возврат и признание недействительным</span></button></aside>'
        '<div class="po-deadline-matrix"><div class="po-matrix-head"><span>Матрица требований и сроков</span><b data-claim-heading>ДДУ · передача просрочена на 94 дня</b></div>'
        '<div class="po-matrix-row" data-claim-row="0"><b>Неустойка</b><span>Со дня просрочки до передачи</span><strong>расчёт ежедневно</strong></div>'
        '<div class="po-matrix-row" data-claim-row="1"><b>Потребительский штраф</b><span>При неудовлетворении претензии</span><strong>до 50% требований</strong></div>'
        '<div class="po-matrix-row" data-claim-row="2"><b>Убытки</b><span>Аренда, хранение, проценты</span><strong>по документам</strong></div>'
        '<div class="po-matrix-row" data-claim-row="3"><b>Судебные расходы</b><span>Экспертиза и представитель</span><strong>заявляются отдельно</strong></div>'
        '<div class="po-evidence" data-claim-evidence><span>Доказательства к претензии</span><b>ДДУ · допсоглашения · уведомления · акт · расходы</b><p>Сроки считаем по документам, а не со слов менеджера застройщика.</p></div></div>'
        '<aside class="po-recovery"><span>ПРЕДВАРИТЕЛЬНЫЙ РАСЧЁТ</span><h2 data-recovery-total>1 760 000 ₽</h2><p data-recovery-copy>Неустойка, штраф и подтверждённые расходы по текущим данным.</p>'
        '<dl><div><dt>Претензия</dt><dd>10 дней</dd></div><div><dt>Подготовка иска</dt><dd>5 рабочих дней</dd></div><div><dt>Госпошлина</dt><dd>по расчёту требований</dd></div></dl>'
        '<button class="po-gold" type="button">Проверить расчёт</button><small>Результат не гарантируется: суд оценивает доказательства и может снизить неустойку.</small></aside></section>'
        '<section class="po-filing"><div><span>Порядок подачи претензии</span><h2>Не пропускаем обязательный досудебный этап</h2></div>'
        '<ol><li><b>01</b><span>Проверка договора и адресата</span></li><li><b>02</b><span>Расчёт и приложения</span></li><li><b>03</b><span>Отправка с доказательством вручения</span></li><li><b>04</b><span>Контроль срока ответа</span></li></ol></section>'
        '</main>'
    )


def _assessment(assets: Mapping[str, str]) -> str:
    photo = assets["case_documents"]
    return (
        '<main class="po-route po-assessment">'
        '<section class="po-assessment-intro"><div><span>ПРЕДВАРИТЕЛЬНО · БЕЗ РЕГИСТРАЦИИ</span><h1>Проверьте перспективу дела до консультации</h1>'
        '<p>Пять ответов определят правовой путь, сроки и перечень документов. Это не заменяет заключение юриста.</p></div>'
        f'<img src="{photo}" alt="Договор и документы для оценки юридического дела"></section>'
        '<section class="po-assessment-work"><form class="po-questionnaire"><div class="po-question"><span>01 · ПРЕДМЕТ СПОРА</span><h2>Что произошло?</h2>'
        '<div><button type="button" data-selectable="issue" data-value="quality" aria-pressed="true">Есть недостатки</button><button type="button" data-selectable="issue" data-value="delay" aria-pressed="false">Нарушен срок передачи</button>'
        '<button type="button" data-selectable="issue" data-value="money" aria-pressed="false">Не возвращают деньги</button></div></div>'
        '<div class="po-question"><span>02 · ДОКУМЕНТЫ</span><h2>Есть подписанный договор?</h2><div><button type="button" data-selectable="contract" data-value="yes" aria-pressed="true">Да, договор на руках</button>'
        '<button type="button" data-selectable="contract" data-value="copy" aria-pressed="false">Есть копия</button><button type="button" data-selectable="contract" data-value="no" aria-pressed="false">Только переписка</button></div></div>'
        '<div class="po-question"><span>03 · СРОК</span><h2>Срок исполнения уже наступил?</h2><div><button type="button" data-selectable="deadline" data-value="passed" aria-pressed="true">Да, срок нарушен</button>'
        '<button type="button" data-selectable="deadline" data-value="soon" aria-pressed="false">Истекает в течение месяца</button><button type="button" data-selectable="deadline" data-value="unknown" aria-pressed="false">Не уверен</button></div></div>'
        '<div class="po-question-row"><label>04 · Желаемый результат<select><option>Взыскать деньги</option><option>Обязать устранить недостатки</option><option>Расторгнуть договор</option></select></label>'
        '<label>05 · Сумма спора<input type="text" value="1 500 000 ₽"></label></div></form>'
        '<aside class="po-assessment-result" data-assessment-result><span>Предварительный правовой путь</span><h2 data-path-title>Требование об устранении недостатков</h2>'
        '<p data-path-copy>Нужны акт осмотра, договор и подтверждение обращения к исполнителю.</p><div class="po-risk"><b data-deadline-status>Срок претензии не пропущен</b><strong data-risk>Риск: средний</strong></div>'
        '<h3>Документы к консультации</h3><ul data-document-list><li>Договор и приложения</li><li>Акт осмотра или дефектная ведомость</li><li>Переписка с исполнителем</li></ul>'
        '<button class="po-gold" type="button">Получить заключение юриста</button><small>Финальная оценка возможна только после изучения документов.</small></aside></section>'
        '<section class="po-assessment-bottom"><div><span>КОНФИДЕНЦИАЛЬНО</span><h2>Документы не становятся публичными</h2></div>'
        '<div><b>Защищённая передача</b><p>Файлы доступны только назначенному юристу.</p></div><div><b>Удаление по запросу</b><p>Закрываем доступ после завершения оценки.</p></div>'
        '<div><b>Письменный вывод</b><p>Правовой путь, риски, сроки и стоимость.</p></div></section>'
        '</main>'
    )


def _practice(assets: Mapping[str, str]) -> str:
    photo = assets["courtroom_hall"]
    return (
        '<main class="po-route po-practice">'
        '<section class="po-practice-intro"><div><span>ОБЕЗЛИЧЕННАЯ ПРАКТИКА · 2025–2026</span><h1>Судебная практика с суммами и сроками</h1>'
        '<p>Показываем предмет спора, стадию, срок и фактически взысканную сумму без обещаний повторить результат.</p></div>'
        f'<img src="{photo}" alt="Зал суда перед заседанием по гражданскому делу"></section>'
        '<section class="po-practice-work"><div class="po-practice-main"><div class="po-practice-filters">'
        '<button type="button" data-selectable="practice-filter" data-value="all" aria-pressed="true">Все категории</button><button type="button" data-selectable="practice-filter" data-value="developer" aria-pressed="false">Застройщики</button>'
        '<button type="button" data-selectable="practice-filter" data-value="consumer" aria-pressed="false">Потребители</button><button type="button" data-selectable="practice-filter" data-value="insurance" aria-pressed="false">Страховые</button></div>'
        '<div class="po-ledger" data-practice-ledger><div class="po-ledger-selection" data-practice-ledger-selection>'
        '<span>12 опубликованных дел</span><b>4 610 000 ₽</b><span>Средний срок: 5 месяцев</span></div>'
        '<div class="po-ledger-head"><span>Дело</span><span>Результат</span><span>Срок</span><span>Стадия</span></div>'
        '<div class="po-ledger-row"><b>Просрочка передачи квартиры</b><strong>2 140 000 ₽</strong><span>6 мес.</span><span>исполнено</span></div>'
        '<div class="po-ledger-row"><b>Недостатки отделки</b><strong>780 000 ₽</strong><span>5 мес.</span><span>мировое соглашение</span></div>'
        '<div class="po-ledger-row"><b>Возврат стоимости услуги</b><strong>430 000 ₽</strong><span>3 мес.</span><span>исполнено</span></div>'
        '<div class="po-ledger-row"><b>Страховое возмещение</b><strong>1 260 000 ₽</strong><span>7 мес.</span><span>апелляция</span></div></div></div>'
        '<aside class="po-practice-summary"><span>Взыскано по выбранным делам</span><h2 data-practice-total>4 610 000 ₽</h2><b data-practice-count>12 опубликованных дел</b>'
        '<p data-practice-term>Средний срок: 5 месяцев</p><dl><div><dt>Добровольно</dt><dd>3 дела</dd></div><div><dt>Суд</dt><dd>7 дел</dd></div><div><dt>Соглашение</dt><dd>2 дела</dd></div></dl>'
        '<button class="po-primary" type="button">Подобрать похожие дела</button><small>Прошлые результаты не гарантируют исход нового спора.</small></aside></section>'
        '<section class="po-court-timeline"><div><span>От претензии до исполнения</span><h2>Контролируем не только решение суда</h2></div>'
        '<ol><li><b>01</b><span>Претензия и срок ответа</span></li><li><b>02</b><span>Иск и обеспечительные меры</span></li><li><b>03</b><span>Решение и апелляция</span></li><li><b>04</b><span>Исполнительный лист и взыскание</span></li></ol></section>'
        '</main>'
    )


def _consultation(assets: Mapping[str, str]) -> str:
    portrait = assets["lawyer_portrait"]
    meeting = assets["client_meeting"]
    return (
        '<main class="po-route po-consultation">'
        '<section class="po-consultation-grid"><form class="po-consultation-form"><span>ЗАПИСЬ НА КОНСУЛЬТАЦИЮ</span>'
        '<h1>Консультация с юристом по вашей категории спора</h1><div class="po-form-row"><label>Категория<select><option>Споры с застройщиками</option><option>Защита прав потребителей</option><option>Страховые споры</option></select></label>'
        '<label>Формат<select><option>Видеосвязь</option><option>В офисе</option></select></label></div>'
        '<fieldset><legend>Юрист</legend><div class="po-lawyer-options"><button type="button" data-selectable="lawyer" data-value="sokolova" aria-pressed="true">Елена Соколова<span>застройщики · 14 лет</span></button>'
        '<button type="button" data-selectable="lawyer" data-value="orlov" aria-pressed="false">Дмитрий Орлов<span>застройщики · 11 лет</span></button></div></fieldset>'
        '<fieldset><legend>Сегодня</legend><div class="po-time-options"><button type="button" data-selectable="consultation-time" data-value="16:00" aria-pressed="true">16:00</button>'
        '<button type="button" data-selectable="consultation-time" data-value="17:15" aria-pressed="false">17:15</button><button type="button" data-selectable="consultation-time" data-value="18:30" aria-pressed="false">18:30</button></div></fieldset>'
        '<label>Кратко о ситуации<textarea>Застройщик нарушил срок передачи квартиры по ДДУ</textarea></label>'
        '<div class="po-upload"><span>Документы к встрече</span><b>Перетащите договор или выберите файл</b><p>PDF, DOCX, JPG · до 20 МБ · защищённая передача</p></div>'
        '<label class="po-consent"><input type="checkbox" checked> Согласен на обработку данных для проведения консультации</label><button class="po-gold" type="button">Подтвердить время</button></form>'
        '<aside class="po-lawyer-card"><figure>'
        f'<img src="{portrait}" alt="Юрист Елена Соколова"></figure><span>НАЗНАЧЕННЫЙ ЮРИСТ</span><h2 data-lawyer-name>Елена Соколова</h2>'
        '<p data-lawyer-role>Споры с застройщиками · 14 лет практики</p><div class="po-consultation-summary" data-consultation-summary><span>Подтверждение консультации</span>'
        '<b data-consultation-time>Сегодня · 16:00</b><p data-consultation-lawyer>Елена Соколова · Споры с застройщиками</p><strong>60 минут · видеосвязь</strong></div>'
        '<dl><div><dt>Стоимость</dt><dd>5 000 ₽</dd></div><div><dt>Результат</dt><dd>письменный план действий</dd></div></dl></aside></section>'
        '<section class="po-preparation"><figure>'
        f'<img src="{meeting}" alt="Юрист проводит конфиденциальную консультацию с клиентом"></figure>'
        '<div><span>Как подготовиться к встрече</span><h2>Соберите факты один раз</h2><p>Юрист заранее увидит документы и не потратит консультацию на восстановление хронологии.</p></div>'
        '<ol><li><b>01</b><span>Договор и приложения</span></li><li><b>02</b><span>Переписка и уведомления</span></li><li><b>03</b><span>Ключевые даты и суммы</span></li><li><b>04</b><span>Желаемый результат</span></li></ol></section>'
        '</main>'
    )


_CSS = r"""
.po-page, .po-page * { box-sizing: border-box; }
.po-page { width: 100%; height: 1120px; overflow: hidden; background: #f7f2e9; color: #232428; font-family: Arial, Helvetica, sans-serif; font-size: 14px; letter-spacing: 0; }
.po-page button, .po-page input, .po-page select, .po-page textarea { font: inherit; letter-spacing: 0; }
.po-page button { cursor: pointer; }
.po-page h1, .po-page h2, .po-page h3, .po-page p, .po-page figure, .po-page dl, .po-page fieldset { margin: 0; }
.po-page h1, .po-page h2, .po-page h3 { font-family: Georgia, "Times New Roman", serif; font-weight: 700; }
.po-header { height: 118px; background: #fff; border-bottom: 1px solid #d8d2c6; }
.po-header-main { height: 82px; padding: 0 42px; display: grid; grid-template-columns: 285px 1fr 150px 220px 160px; gap: 22px; align-items: center; }
.po-brand { display: flex; align-items: center; gap: 13px; text-decoration: none; color: #173f37; }
.po-shield { width: 48px; height: 54px; display: flex; align-items: center; justify-content: center; border: 3px solid #d5ae58; color: #173f37; font-family: Georgia, serif; font-size: 17px; font-weight: 800; clip-path: polygon(50% 0, 100% 14%, 92% 78%, 50% 100%, 8% 78%, 0 14%); }
.po-brand strong, .po-brand small { display: block; }
.po-brand strong { font-family: Georgia, serif; font-size: 19px; }
.po-brand small { margin-top: 4px; color: #73746f; font-size: 12px; }
.po-header nav { display: flex; justify-content: center; gap: 28px; }
.po-header nav a { padding: 29px 0 26px; border-bottom: 3px solid transparent; color: #303431; text-decoration: none; font-size: 13px; font-weight: 700; }
.po-header nav a.is-active { color: #173f37; border-bottom-color: #d5ae58; }
.po-confidential, .po-phone { display: flex; flex-direction: column; gap: 4px; }
.po-confidential span, .po-phone span { color: #73746f; font-size: 12px; }
.po-confidential b { color: #173f37; font-size: 14px; }
.po-phone b { color: #173f37; font-size: 18px; }
.po-header-cta, .po-primary, .po-gold { border: 0; display: inline-flex; align-items: center; justify-content: center; gap: 9px; font-weight: 800; }
.po-header-cta { height: 46px; color: #fff; background: #173f37; }
.po-trust { height: 36px; padding: 0 42px; display: grid; grid-template-columns: 1.25fr 1fr 1fr .8fr; align-items: center; background: #173f37; color: #fff; font-size: 12px; }
.po-trust b { color: #e1c47e; }
.po-trust span { padding-left: 24px; border-left: 1px solid #4d6d66; }
.po-route { height: 1002px; min-height: 0; overflow: hidden; }
.po-primary { min-height: 48px; padding: 0 22px; color: #fff; background: #173f37; }
.po-gold { min-height: 48px; padding: 0 22px; color: #232428; background: #d5ae58; }
.po-case-note { color: #7a3035; font-size: 12px; font-weight: 800; }

.po-cover-grid { height: 570px; display: grid; grid-template-columns: 1fr .86fr .7fr; background: #fff; }
.po-cover-copy { padding: 52px 38px 40px 42px; }
.po-cover-copy h1 { margin: 20px 0 17px; color: #173f37; font-size: 44px; line-height: 1.06; }
.po-cover-copy > p { max-width: 560px; color: #666863; font-size: 17px; line-height: 1.52; }
.po-cover-proof { margin: 28px 0; display: grid; grid-template-columns: repeat(3, 1fr); border-top: 1px solid #d9d2c6; border-bottom: 1px solid #d9d2c6; }
.po-cover-proof div { padding: 15px 15px 15px 0; border-right: 1px solid #d9d2c6; }
.po-cover-proof div:last-child { border: 0; padding-left: 14px; }
.po-cover-proof b, .po-cover-proof span { display: block; }
.po-cover-proof b { color: #173f37; font-family: Georgia, serif; font-size: 22px; }
.po-cover-proof span { margin-top: 5px; color: #73746f; font-size: 12px; }
.po-cover-photo { position: relative; overflow: hidden; background: #e2ddd4; }
.po-cover-photo img { width: 100%; height: 100%; object-fit: cover; }
.po-cover-photo figcaption { position: absolute; left: 0; right: 0; bottom: 0; padding: 17px 20px; background: #fff; border-top: 4px solid #d5ae58; }
.po-cover-photo figcaption b, .po-cover-photo figcaption span { display: block; }
.po-cover-photo figcaption b { font-family: Georgia, serif; }
.po-cover-photo figcaption span { margin-top: 5px; color: #73746f; font-size: 12px; }
.po-quick-assessment { padding: 29px 27px; background: #173f37; color: #fff; }
.po-quick-assessment > span { color: #e1c47e; font-size: 12px; font-weight: 800; }
.po-quick-assessment h2 { margin: 9px 0 14px; font-size: 24px; }
.po-quick-options { display: grid; grid-template-columns: 1fr 1fr; }
.po-quick-options button { min-height: 41px; border: 1px solid #718781; background: transparent; color: #fff; font-size: 12px; }
.po-quick-options button[aria-pressed="true"] { color: #232428; background: #d5ae58; border-color: #d5ae58; }
.po-quick-assessment label { display: block; margin-top: 14px; color: #c9d2cf; font-size: 12px; }
.po-quick-assessment select, .po-quick-assessment textarea { width: 100%; margin-top: 6px; padding: 0 10px; border: 1px solid #82948f; background: #fff; color: #232428; }
.po-quick-assessment select { height: 39px; }
.po-quick-assessment textarea { height: 55px; padding-top: 9px; resize: none; }
.po-quick-result { margin-top: 14px; padding: 13px; border-left: 4px solid #d5ae58; background: #234a42; }
.po-quick-result span { color: #cbd5d1; font-size: 12px; }
.po-quick-result b { display: block; margin: 4px 0; }
.po-quick-result p { color: #c8d2cf; font-size: 12px; }
.po-quick-assessment .po-gold { width: 100%; margin-top: 13px; }
.po-quick-assessment small { display: block; margin-top: 8px; color: #b8c5c1; font-size: 12px; }
.po-outcomes { height: 220px; display: grid; grid-template-columns: repeat(4, 1fr); background: #f7f2e9; border-bottom: 1px solid #d9d2c6; }
.po-outcomes div { padding: 34px 30px 25px 42px; border-right: 1px solid #d9d2c6; }
.po-outcomes span { color: #7a3035; font-size: 12px; font-weight: 800; }
.po-outcomes b { display: block; margin: 13px 0 9px; color: #173f37; font-family: Georgia, serif; font-size: 20px; }
.po-outcomes p { color: #73746f; line-height: 1.45; }
.po-cover-steps { height: 212px; padding: 0 42px; display: grid; grid-template-columns: 1.2fr 3fr; background: #232428; color: #fff; }
.po-cover-steps > div { padding: 38px 28px 25px 0; border-right: 1px solid #555651; }
.po-cover-steps > div span { color: #e1c47e; font-size: 12px; font-weight: 800; }
.po-cover-steps h2 { margin-top: 10px; font-size: 25px; }
.po-cover-steps ol { list-style: none; padding: 0; margin: 0; display: grid; grid-template-columns: repeat(4, 1fr); }
.po-cover-steps li { padding: 40px 24px; border-right: 1px solid #555651; }
.po-cover-steps li b, .po-cover-steps li span { display: block; }
.po-cover-steps li b { color: #d5ae58; font-size: 12px; }
.po-cover-steps li span { margin-top: 13px; line-height: 1.45; }

.po-developer-intro { height: 220px; min-height: 0; overflow: hidden; display: grid; grid-template-columns: minmax(0, 1fr) 530px; background: #f7f2e9; border-bottom: 1px solid #d9d2c6; }
.po-developer-intro > div, .po-assessment-intro > div, .po-practice-intro > div { padding: 36px 42px; }
.po-developer-intro span, .po-assessment-intro span, .po-practice-intro span { color: #7a3035; font-size: 12px; font-weight: 800; }
.po-developer-intro h1, .po-assessment-intro h1, .po-practice-intro h1 { margin: 10px 0; color: #173f37; font-size: 34px; line-height: 1.1; }
.po-developer-intro p, .po-assessment-intro p, .po-practice-intro p { color: #686a65; font-size: 15px; line-height: 1.45; }
.po-developer-intro img { display: block; width: 100%; height: 220px; max-height: 220px; object-fit: cover; }
.po-developer-work { height: 540px; display: grid; grid-template-columns: 320px 1fr 350px; background: #fff; }
.po-claim-types { padding: 28px 25px 24px 42px; background: #eee5d6; }
.po-claim-types h2 { margin-bottom: 14px; font-size: 20px; }
.po-claim-types button { width: 100%; min-height: 100px; padding: 14px; border: 0; border-top: 1px solid #cdbfa9; background: transparent; color: #30332f; text-align: left; }
.po-claim-types button b, .po-claim-types button span { display: block; }
.po-claim-types button span { margin-top: 7px; color: #73746f; font-size: 12px; }
.po-claim-types button[aria-pressed="true"] { color: #fff; background: #173f37; }
.po-claim-types button[aria-pressed="true"] span { color: #c7d4d0; }
.po-deadline-matrix { padding: 28px 32px; }
.po-matrix-head { display: flex; justify-content: space-between; align-items: end; padding-bottom: 15px; border-bottom: 3px solid #173f37; }
.po-matrix-head span { color: #73746f; font-size: 12px; }
.po-matrix-head b { color: #173f37; font-size: 17px; }
.po-matrix-row { min-height: 70px; display: grid; grid-template-columns: 1fr 1.2fr 140px; gap: 15px; align-items: center; border-bottom: 1px solid #d9d2c6; }
.po-matrix-row span { color: #73746f; font-size: 12px; }
.po-matrix-row strong { color: #7a3035; font-size: 12px; text-align: right; }
.po-evidence { margin-top: 16px; padding: 14px 17px; background: #f7f2e9; border-left: 4px solid #d5ae58; }
.po-evidence span { color: #73746f; font-size: 12px; }
.po-evidence b { display: block; margin: 5px 0; color: #173f37; }
.po-recovery { padding: 31px 28px; background: #173f37; color: #fff; }
.po-recovery > span { color: #e1c47e; font-size: 12px; font-weight: 800; }
.po-recovery h2 { margin: 10px 0 8px; color: #fff; font-size: 31px; }
.po-recovery > p { color: #c9d4d1; line-height: 1.45; }
.po-recovery dl { margin: 21px 0; border-top: 1px solid #536f69; }
.po-recovery dl div { min-height: 52px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #536f69; }
.po-recovery dt { color: #c4d0cc; }
.po-recovery dd { max-width: 150px; margin: 0; font-weight: 800; text-align: right; }
.po-recovery .po-gold { width: 100%; }
.po-recovery small { display: block; margin-top: 12px; color: #b8c5c1; font-size: 12px; line-height: 1.35; }
.po-filing { height: 242px; padding: 0 42px; display: grid; grid-template-columns: 1.2fr 3fr; background: #232428; color: #fff; }
.po-filing > div { padding: 42px 28px 25px 0; border-right: 1px solid #555651; }
.po-filing > div span { color: #e1c47e; font-size: 12px; font-weight: 800; }
.po-filing h2 { margin-top: 10px; font-size: 25px; }
.po-filing ol { list-style: none; padding: 0; margin: 0; display: grid; grid-template-columns: repeat(4, 1fr); }
.po-filing li { padding: 43px 24px; border-right: 1px solid #555651; }
.po-filing li b, .po-filing li span { display: block; }
.po-filing li b { color: #d5ae58; font-size: 12px; }
.po-filing li span { margin-top: 13px; line-height: 1.45; }

.po-assessment-intro, .po-practice-intro { height: 190px; min-height: 0; overflow: hidden; display: grid; grid-template-columns: minmax(0, 1fr) 490px; background: #fff; border-bottom: 1px solid #d9d2c6; }
.po-assessment-intro img, .po-practice-intro img { display: block; width: 100%; height: 190px; max-height: 190px; object-fit: cover; }
.po-assessment-work { height: 600px; display: grid; grid-template-columns: 1fr 430px; background: #f7f2e9; }
.po-questionnaire { padding: 24px 34px 20px 42px; }
.po-question { min-height: 125px; padding: 12px 0; border-bottom: 1px solid #d2c8b9; }
.po-question > span { color: #7a3035; font-size: 12px; font-weight: 800; }
.po-question h2 { margin: 5px 0 9px; font-family: Arial, sans-serif; font-size: 16px; }
.po-question > div { display: grid; grid-template-columns: repeat(3, 1fr); }
.po-question button { min-height: 40px; border: 1px solid #b8aa96; background: #fff; color: #454641; font-size: 12px; }
.po-question button[aria-pressed="true"] { color: #fff; background: #173f37; border-color: #173f37; }
.po-question-row { margin-top: 14px; display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.po-question-row label { color: #7a3035; font-size: 12px; font-weight: 800; }
.po-question-row select, .po-question-row input { width: 100%; height: 40px; margin-top: 6px; padding: 0 10px; border: 1px solid #b8aa96; }
.po-assessment-result { padding: 31px 29px; background: #173f37; color: #fff; }
.po-assessment-result > span { color: #e1c47e; font-size: 12px; font-weight: 800; }
.po-assessment-result h2 { min-height: 65px; margin: 10px 0 7px; color: #fff; font-size: 23px; }
.po-assessment-result > p { min-height: 55px; color: #c9d4d1; line-height: 1.45; }
.po-risk { margin: 17px 0; padding: 14px; background: #234a42; border-left: 4px solid #d5ae58; }
.po-risk b, .po-risk strong { display: block; }
.po-risk strong { margin-top: 6px; color: #e5ca8c; }
.po-assessment-result h3 { margin: 0 0 8px; color: #fff; font-family: Arial, sans-serif; font-size: 15px; }
.po-assessment-result ul { min-height: 105px; padding: 0; margin: 0 0 14px; list-style: none; }
.po-assessment-result li { padding: 8px 0 8px 20px; position: relative; border-bottom: 1px solid #536f69; font-size: 12px; }
.po-assessment-result li::before { content: "•"; position: absolute; left: 2px; color: #d5ae58; }
.po-assessment-result .po-gold { width: 100%; }
.po-assessment-result small { display: block; margin-top: 10px; color: #b8c5c1; font-size: 12px; }
.po-assessment-bottom { height: 212px; padding: 0 42px; display: grid; grid-template-columns: 1.25fr 1fr 1fr 1fr; background: #fff; }
.po-assessment-bottom > div { padding: 38px 27px; border-right: 1px solid #d9d2c6; }
.po-assessment-bottom span { color: #7a3035; font-size: 12px; font-weight: 800; }
.po-assessment-bottom h2 { margin-top: 9px; color: #173f37; font-size: 24px; }
.po-assessment-bottom b { color: #173f37; }
.po-assessment-bottom p { margin-top: 10px; color: #73746f; line-height: 1.45; }

.po-practice-intro { background: #f7f2e9; }
.po-practice-work { height: 560px; display: grid; grid-template-columns: 1fr 380px; background: #fff; }
.po-practice-main { padding: 26px 34px 22px 42px; }
.po-practice-filters { display: grid; grid-template-columns: repeat(4, 1fr); }
.po-practice-filters button { min-height: 42px; border: 1px solid #b9ad9b; background: #fff; color: #464741; }
.po-practice-filters button[aria-pressed="true"] { color: #fff; background: #173f37; border-color: #173f37; }
.po-ledger { margin-top: 18px; }
.po-ledger-selection { min-height: 34px; padding: 0 14px; display: grid; grid-template-columns: 1.4fr .8fr 1.35fr; gap: 16px; align-items: center; color: #173f37; background: #eee7da; font-size: 12px; }
.po-ledger-selection b { font-family: Georgia, serif; font-size: 15px; }
.po-ledger-head, .po-ledger-row { display: grid; grid-template-columns: 1.4fr .8fr .55fr .8fr; gap: 16px; align-items: center; }
.po-ledger-head { min-height: 40px; padding: 0 14px; color: #fff; background: #232428; font-size: 12px; }
.po-ledger-row { min-height: 85px; padding: 0 14px; border-bottom: 1px solid #d9d2c6; }
.po-ledger-row strong { color: #173f37; font-family: Georgia, serif; font-size: 17px; }
.po-ledger-row span { color: #73746f; font-size: 12px; }
.po-practice-summary { padding: 32px 28px; color: #fff; background: #173f37; }
.po-practice-summary > span { color: #e1c47e; font-size: 12px; font-weight: 800; }
.po-practice-summary h2 { min-height: 48px; margin: 9px 0; color: #fff; font-size: 31px; }
.po-practice-summary > b { display: block; }
.po-practice-summary > p { margin-top: 6px; color: #c8d3d0; }
.po-practice-summary dl { margin: 22px 0; border-top: 1px solid #536f69; }
.po-practice-summary dl div { min-height: 54px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #536f69; }
.po-practice-summary dt { color: #c4d0cc; }
.po-practice-summary dd { margin: 0; font-weight: 800; }
.po-practice-summary .po-primary { width: 100%; background: #d5ae58; color: #232428; }
.po-practice-summary small { display: block; margin-top: 12px; color: #b8c5c1; font-size: 12px; }
.po-court-timeline { height: 252px; padding: 0 42px; display: grid; grid-template-columns: 1.2fr 3fr; color: #fff; background: #232428; }
.po-court-timeline > div { padding: 42px 28px 25px 0; border-right: 1px solid #555651; }
.po-court-timeline > div span { color: #e1c47e; font-size: 12px; font-weight: 800; }
.po-court-timeline h2 { margin-top: 10px; font-size: 25px; }
.po-court-timeline ol { list-style: none; padding: 0; margin: 0; display: grid; grid-template-columns: repeat(4, 1fr); }
.po-court-timeline li { padding: 44px 24px; border-right: 1px solid #555651; }
.po-court-timeline li b, .po-court-timeline li span { display: block; }
.po-court-timeline li b { color: #d5ae58; font-size: 12px; }
.po-court-timeline li span { margin-top: 13px; line-height: 1.45; }

.po-consultation-grid { height: 700px; display: grid; grid-template-columns: 1fr 430px; background: #fff; }
.po-consultation-form { padding: 34px 48px 27px 42px; }
.po-consultation-form > span { color: #7a3035; font-size: 12px; font-weight: 800; }
.po-consultation-form h1 { margin: 9px 0 19px; color: #173f37; font-size: 35px; }
.po-form-row { display: grid; grid-template-columns: 1fr .7fr; gap: 15px; }
.po-consultation-form label { display: block; margin-top: 13px; color: #5f615d; font-size: 12px; font-weight: 700; }
.po-consultation-form select, .po-consultation-form textarea { width: 100%; margin-top: 6px; padding: 0 10px; border: 1px solid #b9ad9b; background: #fff; }
.po-consultation-form select { height: 40px; }
.po-consultation-form textarea { height: 55px; padding-top: 9px; resize: none; }
.po-consultation-form fieldset { padding: 0; margin-top: 15px; border: 0; }
.po-consultation-form legend { margin-bottom: 8px; color: #5f615d; font-size: 12px; font-weight: 700; }
.po-lawyer-options { display: grid; grid-template-columns: 1fr 1fr; }
.po-lawyer-options button { min-height: 57px; border: 1px solid #b9ad9b; background: #fff; color: #30332f; font-weight: 800; }
.po-lawyer-options button span { display: block; margin-top: 4px; color: #73746f; font-size: 12px; font-weight: 400; }
.po-lawyer-options button[aria-pressed="true"] { color: #fff; background: #173f37; border-color: #173f37; }
.po-lawyer-options button[aria-pressed="true"] span { color: #c6d3cf; }
.po-time-options { display: grid; grid-template-columns: repeat(3, 1fr); }
.po-time-options button { min-height: 40px; border: 1px solid #b9ad9b; background: #fff; }
.po-time-options button[aria-pressed="true"] { color: #232428; background: #d5ae58; border-color: #d5ae58; }
.po-upload { margin-top: 14px; padding: 13px 15px; border: 1px dashed #9d8e78; background: #f7f2e9; }
.po-upload span, .po-upload b, .po-upload p { display: block; }
.po-upload span { color: #7a3035; font-size: 12px; }
.po-upload b { margin-top: 4px; }
.po-upload p { margin-top: 4px; color: #73746f; font-size: 12px; }
.po-consent { display: flex !important; align-items: center; gap: 9px; font-weight: 400 !important; }
.po-consent input { width: 17px; height: 17px; }
.po-consultation-form .po-gold { min-width: 250px; margin-top: 15px; }
.po-lawyer-card { padding: 0 29px 25px; background: #173f37; color: #fff; }
.po-lawyer-card figure { height: 280px; margin: 0 -29px 24px; overflow: hidden; }
.po-lawyer-card img { width: 100%; height: 280px; object-fit: cover; object-position: center 24%; }
.po-lawyer-card > span { color: #e1c47e; font-size: 12px; font-weight: 800; }
.po-lawyer-card h2 { margin-top: 7px; color: #fff; font-size: 25px; }
.po-lawyer-card > p { margin-top: 5px; color: #c8d3d0; }
.po-consultation-summary { margin-top: 17px; padding: 14px; background: #234a42; border-left: 4px solid #d5ae58; }
.po-consultation-summary span, .po-consultation-summary b, .po-consultation-summary p, .po-consultation-summary strong { display: block; }
.po-consultation-summary span { color: #c5d1cd; font-size: 12px; }
.po-consultation-summary b { margin-top: 5px; font-size: 18px; }
.po-consultation-summary p { margin-top: 6px; color: #d2dbd8; }
.po-consultation-summary strong { margin-top: 6px; color: #e5ca8c; }
.po-lawyer-card dl { margin-top: 16px; border-top: 1px solid #536f69; }
.po-lawyer-card dl div { min-height: 48px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #536f69; }
.po-lawyer-card dt { color: #c3cfcb; }
.po-lawyer-card dd { max-width: 210px; margin: 0; font-weight: 800; text-align: right; }
.po-preparation { height: 302px; display: grid; grid-template-columns: 380px 420px 1fr; color: #fff; background: #232428; }
.po-preparation figure { overflow: hidden; }
.po-preparation img { width: 100%; height: 302px; object-fit: cover; }
.po-preparation > div { padding: 47px 37px; border-right: 1px solid #555651; }
.po-preparation > div span { color: #e1c47e; font-size: 12px; font-weight: 800; }
.po-preparation h2 { margin: 9px 0 12px; font-size: 25px; }
.po-preparation > div p { color: #c5c7c2; line-height: 1.5; }
.po-preparation ol { list-style: none; padding: 26px 36px; margin: 0; display: grid; grid-template-columns: 1fr 1fr; }
.po-preparation li { padding: 18px; border-bottom: 1px solid #555651; }
.po-preparation li:nth-child(odd) { border-right: 1px solid #555651; }
.po-preparation li b, .po-preparation li span { display: block; }
.po-preparation li b { color: #d5ae58; font-size: 12px; }
.po-preparation li span { margin-top: 8px; }
"""


_COVER_SCRIPT = r"""
(() => {
  const paths = {
    developer: ["Претензия → расчёт неустойки → иск", "Точный вывод после проверки ДДУ, уведомлений и сроков передачи."],
    consumer: ["Претензия продавцу → экспертиза → требование", "Проверяем договор, чек и срок ответа на претензию."],
    insurance: ["Заявление → независимая оценка → претензия", "Сопоставляем отказ, правила страхования и расчёт ущерба."],
    property: ["Проверка права → переговоры → иск", "Изучаем выписку, договор, историю перехода права и ограничения."]
  };
  const controls = [...document.querySelectorAll('[data-selectable="quick-issue"]')];
  controls.forEach((button) => button.addEventListener("click", () => {
    controls.forEach((option) => option.setAttribute("aria-pressed", String(option === button)));
    const value = paths[button.dataset.value];
    document.querySelector("[data-quick-path]").textContent = value[0];
    document.querySelector("[data-quick-copy]").textContent = value[1];
  }));
})();
"""


_DEVELOPER_SCRIPT = r"""
(() => {
  const claims = {
    delay: {
      heading: "ДДУ · передача просрочена на 94 дня",
      rows: [["Неустойка", "Со дня просрочки до передачи", "расчёт ежедневно"], ["Потребительский штраф", "При неудовлетворении претензии", "по решению суда"], ["Убытки", "Аренда, хранение, проценты", "по документам"], ["Судебные расходы", "Экспертиза и представитель", "заявляются отдельно"]],
      evidence: ["ДДУ · допсоглашения · уведомления · акт · расходы", "Сроки считаем по документам, а не со слов менеджера застройщика."],
      total: "1 760 000 ₽",
      copy: "Неустойка, штраф и подтверждённые расходы по текущим данным."
    },
    defects: {
      heading: "Акт дефектов · квартира передана",
      rows: [["Устранение недостатков", "Срок согласуем по акту", "основное требование"], ["Компенсация", "По стоимости исправления", "по смете или экспертизе"], ["Неустойка", "При пропуске срока устранения", "расчёт по периоду"], ["Расходы на экспертизу", "При подтверждении дефектов", "заявляются отдельно"]],
      evidence: ["ДДУ · акт приёмки · дефектная ведомость · фото · смета", "Фиксируем каждый недостаток до начала самостоятельного ремонта."],
      total: "780 000 ₽",
      copy: "Стоимость устранения, экспертиза и связанные расходы по акту."
    },
    area: {
      heading: "ДДУ · площадь отличается на 3,8 м²",
      rows: [["Перерасчёт цены", "По цене квадратного метра в ДДУ", "после обмера"], ["Независимый обмер", "До подписания итогового акта", "техническое основание"], ["Проценты", "При задержке возврата", "по периоду"], ["Судебные расходы", "Обмер и представитель", "заявляются отдельно"]],
      evidence: ["ДДУ · поэтажный план · акт · технический обмер", "Сравниваем договорную и фактическую площадь по одному методу."],
      total: "460 000 ₽",
      copy: "Предварительный возврат по цене метра и результатам обмера."
    },
    terms: {
      heading: "Допсоглашение · спорное условие оплаты",
      rows: [["Возврат платежа", "После анализа основания", "основное требование"], ["Недействительность условия", "По содержанию договора", "правовая оценка"], ["Проценты", "С даты удержания денег", "по периоду"], ["Судебные расходы", "Пошлина и представитель", "заявляются отдельно"]],
      evidence: ["ДДУ · допсоглашение · платёжные документы · переписка", "Проверяем, было ли условие согласовано и соответствует ли закону."],
      total: "320 000 ₽",
      copy: "Спорный платёж и возможные проценты по текущим документам."
    }
  };
  const controls = [...document.querySelectorAll('[data-selectable="claim"]')];
  controls.forEach((button) => button.addEventListener("click", () => {
    controls.forEach((option) => option.setAttribute("aria-pressed", String(option === button)));
    const claim = claims[button.dataset.value];
    document.querySelector("[data-claim-heading]").textContent = claim.heading;
    document.querySelectorAll("[data-claim-row]").forEach((row, index) => {
      const value = claim.rows[index];
      row.innerHTML = `<b>${value[0]}</b><span>${value[1]}</span><strong>${value[2]}</strong>`;
    });
    document.querySelector("[data-claim-evidence]").innerHTML = `<span>Доказательства к претензии</span><b>${claim.evidence[0]}</b><p>${claim.evidence[1]}</p>`;
    document.querySelector("[data-recovery-total]").textContent = claim.total;
    document.querySelector("[data-recovery-copy]").textContent = claim.copy;
  }));
})();
"""


_ASSESSMENT_SCRIPT = r"""
(() => {
  let issue = "quality";
  let contract = "yes";
  let deadline = "passed";
  const update = () => {
    const result = issue === "delay"
      ? ["Неустойка за нарушение срока передачи", "Проверим ДДУ, допсоглашения, уведомления и дату фактической передачи."]
      : issue === "money"
        ? ["Возврат денег и потребительский штраф", "Нужны договор, требование о возврате и доказательство его вручения."]
        : ["Требование об устранении недостатков", "Нужны акт осмотра, договор и подтверждение обращения к исполнителю."];
    document.querySelector("[data-path-title]").textContent = result[0];
    document.querySelector("[data-path-copy]").textContent = result[1];
    document.querySelector("[data-deadline-status]").textContent = deadline === "passed" ? "Срок претензии не пропущен" : "Срок необходимо уточнить по договору";
    document.querySelector("[data-risk]").textContent = contract === "no" ? "Риск: повышенный" : "Риск: средний";
    const docs = issue === "delay"
      ? ["ДДУ и дополнительные соглашения", "Акт приёма-передачи или уведомление", "Переписка и подтверждённые расходы"]
      : ["Договор и приложения", "Акт осмотра или дефектная ведомость", "Переписка с исполнителем"];
    document.querySelector("[data-document-list]").innerHTML = docs.map((item) => `<li>${item}</li>`).join("");
  };
  ["issue", "contract", "deadline"].forEach((group) => {
    document.querySelectorAll(`[data-selectable="${group}"]`).forEach((button) => button.addEventListener("click", () => {
      document.querySelectorAll(`[data-selectable="${group}"]`).forEach((option) => option.setAttribute("aria-pressed", String(option === button)));
      if (group === "issue") issue = button.dataset.value;
      if (group === "contract") contract = button.dataset.value;
      if (group === "deadline") deadline = button.dataset.value;
      update();
    }));
  });
})();
"""


_PRACTICE_SCRIPT = r"""
(() => {
  const totals = {
    all: ["4 610 000 ₽", "12 опубликованных дел", "Средний срок: 5 месяцев"],
    developer: ["3 840 000 ₽", "4 дела по застройщикам", "Средний срок: 5,5 месяца"],
    consumer: ["1 120 000 ₽", "5 потребительских дел", "Средний срок: 3 месяца"],
    insurance: ["2 260 000 ₽", "3 страховых дела", "Средний срок: 6 месяцев"]
  };
  document.querySelectorAll('[data-selectable="practice-filter"]').forEach((button) => button.addEventListener("click", () => {
    document.querySelectorAll('[data-selectable="practice-filter"]').forEach((option) => option.setAttribute("aria-pressed", String(option === button)));
    const value = totals[button.dataset.value];
    document.querySelector("[data-practice-total]").textContent = value[0];
    document.querySelector("[data-practice-count]").textContent = value[1];
    document.querySelector("[data-practice-term]").textContent = value[2];
    document.querySelector("[data-practice-ledger-selection]").innerHTML = `<span>${value[1]}</span><b>${value[0]}</b><span>${value[2]}</span>`;
  }));
})();
"""


_CONSULTATION_SCRIPT = r"""
(() => {
  let lawyer = "sokolova";
  let time = "16:00";
  const lawyers = {
    sokolova: ["Елена Соколова", "Споры с застройщиками · 14 лет практики"],
    orlov: ["Дмитрий Орлов", "Споры с застройщиками · 11 лет практики"]
  };
  const update = () => {
    const selected = lawyers[lawyer];
    document.querySelector("[data-lawyer-name]").textContent = selected[0];
    document.querySelector("[data-lawyer-role]").textContent = selected[1];
    document.querySelector("[data-consultation-time]").textContent = `Сегодня · ${time}`;
    document.querySelector("[data-consultation-lawyer]").textContent = `${selected[0]} · Споры с застройщиками`;
  };
  document.querySelectorAll('[data-selectable="lawyer"]').forEach((button) => button.addEventListener("click", () => {
    document.querySelectorAll('[data-selectable="lawyer"]').forEach((option) => option.setAttribute("aria-pressed", String(option === button)));
    lawyer = button.dataset.value; update();
  }));
  document.querySelectorAll('[data-selectable="consultation-time"]').forEach((button) => button.addEventListener("click", () => {
    document.querySelectorAll('[data-selectable="consultation-time"]').forEach((option) => option.setAttribute("aria-pressed", String(option === button)));
    time = button.dataset.value; update();
  }));
})();
"""


_ROUTES = {
    "cover": (_cover, _COVER_SCRIPT),
    "developer-disputes": (_developer, _DEVELOPER_SCRIPT),
    "assessment": (_assessment, _ASSESSMENT_SCRIPT),
    "practice": (_practice, _PRACTICE_SCRIPT),
    "consultation": (_consultation, _CONSULTATION_SCRIPT),
}


def render(
    project: ProjectSpec, shot: ShotSpec, assets: Mapping[str, str]
) -> RenderedPage:
    """Render one Pravovaya Opora route with route-owned legal workflows."""
    if project.slug != "pravo-opora":
        raise ValueError(f"Pravovaya Opora renderer received project {project.slug}")
    try:
        route_renderer, scripts = _ROUTES[shot.key]
    except KeyError as exc:
        raise KeyError(f"Unknown Pravovaya Opora route: {shot.key}") from exc
    safe_assets = {key: escape(value, quote=True) for key, value in assets.items()}
    html = (
        f'<div class="po-page" data-site="pravo-opora" data-route="{escape(shot.key, quote=True)}">'
        f'{_header(shot.key)}{route_renderer(safe_assets)}</div>'
    )
    return RenderedPage(html=html, css=_CSS, scripts=scripts)
