from collections.abc import Callable, Mapping

from ..components import escape_html, panel
from ..icons import icon
from ..models import ProjectSpec, ShotSpec


COMMERCIAL_LAYOUTS = {
    "tochka-hoda": ("split-diagnostic", "service-timeline", "service-booking"),
    "dentalea": ("calm-editorial", "treatment-detail", "doctor-schedule"),
    "ventkontur": ("technical-index", "catalog-table", "equipment-filter"),
    "syr-hleb": ("product-led", "collection-grid", "gift-builder"),
    "kvadrat-remonta": ("project-gallery", "case-study", "estimate-table"),
}

_IMAGE_ALTS = {
    "tochka-hoda": "Автомобиль на диагностическом посту автосервиса",
    "dentalea": "Светлый кабинет стоматологии Денталея",
    "ventkontur": "Промышленная вентиляционная установка в цехе",
    "syr-hleb": "Сыры и свежий хлеб для подарочного набора",
    "kvadrat-remonta": "Готовая гостиная после ремонта квартиры",
}

_COMMERCIAL_CSS = """
.commercial-page { width: 100%; min-height: 100%; background: var(--surface); color: var(--ink); }
.commercial-page * { box-sizing: border-box; }
.commercial-page a { color: inherit; text-decoration: none; }
.commercial-page h1, .commercial-page h2, .commercial-page h3, .commercial-page p { margin-top: 0; }
.commercial-page h1 { margin-bottom: 24px; font-size: 62px; line-height: 1.02; letter-spacing: 0; }
.commercial-page h2 { margin-bottom: 20px; font-size: 42px; line-height: 1.08; letter-spacing: 0; }
.commercial-page h3 { margin-bottom: 10px; font-size: 21px; line-height: 1.25; }
.commercial-page p { color: var(--ink-muted); font-size: 18px; line-height: 1.5; }
.commercial-nav { display: flex; align-items: center; justify-content: space-between; min-height: 82px; padding: 0 56px; border-bottom: 1px solid rgba(91, 105, 118, .18); }
.commercial-brand { font-size: 23px; font-weight: 800; }
.commercial-links { display: flex; align-items: center; gap: 30px; font-size: 15px; font-weight: 600; }
.commercial-actions { display: flex; align-items: center; gap: 12px; }
.commercial-button { display: inline-flex; align-items: center; justify-content: center; gap: 9px; min-height: 48px; padding: 0 20px; border: 0; border-radius: 6px; background: var(--accent); color: white; font: inherit; font-size: 16px; font-weight: 700; }
.commercial-button.secondary { border: 1px solid rgba(91, 105, 118, .25); background: white; color: var(--ink); }
.commercial-hero-image { width: 100%; object-fit: cover; background: var(--highlight); }
.commercial-label { margin-bottom: 14px; color: var(--accent-strong); font-size: 14px; font-weight: 800; text-transform: uppercase; }
.commercial-mobile { min-height: 920px; }
.commercial-mobile .commercial-nav { min-height: 68px; padding: 0 22px; }
.commercial-mobile .commercial-links { display: none; }
.commercial-mobile h1 { font-size: 40px; line-height: 1.03; }
.commercial-mobile h2 { font-size: 32px; }
.commercial-mobile p { font-size: 16px; }
.commercial-mobile .commercial-button { width: 100%; }
.commercial-form-row { display: grid; gap: 12px; }
.commercial-field { min-height: 52px; padding: 14px 16px; border: 1px solid rgba(91, 105, 118, .28); border-radius: 6px; background: #fff; color: var(--ink); font-size: 15px; }
.commercial-check { display: flex; align-items: center; gap: 10px; color: var(--ink); font-weight: 650; }

.tochka-hoda .commercial-brand { color: #1e2822; text-transform: uppercase; }
.tochka-cover { display: grid; grid-template-columns: 46% 54%; min-height: 760px; }
.tochka-copy { padding: 78px 48px 50px 62px; background: #fff; }
.tochka-copy h1 { max-width: 620px; }
.tochka-media { position: relative; padding: 34px; background: #202623; }
.tochka-media img { height: 610px; }
.tochka-status { position: absolute; right: 56px; bottom: 62px; width: 280px; padding: 20px; border-left: 5px solid var(--support); background: #fff; }
.tochka-status strong { display: block; margin-bottom: 6px; font-size: 20px; }
.tochka-strip { display: grid; grid-template-columns: repeat(4, 1fr); border-top: 1px solid #d9dfdc; }
.tochka-strip div { padding: 25px 34px; border-right: 1px solid #d9dfdc; font-weight: 700; }
.tochka-timeline { padding: 52px 62px; background: #f2f5f3; }
.timeline-row { display: grid; grid-template-columns: 110px 1fr 340px; gap: 28px; align-items: center; padding: 22px 0; border-top: 1px solid #cbd4cf; }
.timeline-index { color: var(--accent); font-size: 34px; font-weight: 800; }
.timeline-row img { height: 170px; }
.tochka-booking { display: grid; grid-template-columns: 1.1fr .9fr; gap: 38px; padding: 48px 62px; background: #f3f5f4; }
.tochka-booking-form { padding: 34px; border-top: 7px solid var(--accent); background: white; }
.tochka-booking-form .commercial-form-row { grid-template-columns: 1fr 1fr; }
.tochka-booking-media img { height: 325px; margin-bottom: 20px; }
.tochka-mobile-body { padding: 30px 22px; }
.tochka-mobile-body img { height: 245px; margin: 22px 0; }

.dentalea { background: #fbfdfc; }
.dentalea .commercial-brand { font-family: Georgia, serif; color: #315b54; font-size: 28px; font-weight: 600; }
.dentalea .commercial-nav { border-bottom: 0; }
.dentalea-cover { display: grid; grid-template-columns: 1fr 460px; gap: 88px; align-items: center; min-height: 770px; padding: 60px 88px 80px 96px; }
.dentalea-copy h1 { max-width: 750px; font-family: Georgia, serif; font-size: 68px; font-weight: 500; }
.dentalea-copy p { max-width: 620px; }
.dentalea-portrait { position: relative; }
.dentalea-portrait img { height: 520px; border-radius: 220px 220px 8px 8px; }
.dentalea-note { position: absolute; left: -74px; bottom: 34px; width: 225px; padding: 22px; border-radius: 6px; background: #eb756c; color: #fff; font-weight: 700; }
.dentalea-services { display: grid; grid-template-columns: repeat(3, 1fr); padding: 28px 88px; background: #eaf5f1; }
.dentalea-services div { padding: 18px 28px; border-left: 1px solid #c6ddd5; }
.dentalea-detail { display: grid; grid-template-columns: 430px 1fr; min-height: 820px; }
.dentalea-detail-aside { padding: 50px 48px; background: #dff0eb; }
.dentalea-detail-aside img { height: 270px; margin-bottom: 28px; border-radius: 6px; }
.dentalea-detail-main { padding: 58px 76px; }
.dentalea-step { display: grid; grid-template-columns: 70px 1fr; gap: 20px; padding: 24px 0; border-bottom: 1px solid #d8e3df; }
.dentalea-step b { color: var(--support); font: 32px Georgia, serif; }
.dentalea-schedule { display: grid; grid-template-columns: 1fr 440px; gap: 50px; padding: 50px 74px; }
.schedule-days { display: grid; grid-template-columns: repeat(5, 1fr); border: 1px solid #d9e5e1; }
.schedule-day { min-height: 245px; padding: 18px; border-right: 1px solid #d9e5e1; }
.schedule-day strong { display: block; margin-bottom: 22px; }
.schedule-time { margin-bottom: 10px; padding: 9px; border-radius: 5px; background: #e9f5f1; color: #315b54; text-align: center; }
.dentalea-doctor { padding: 28px; background: #fff1ef; }
.dentalea-doctor img { height: 250px; margin-bottom: 20px; border-radius: 6px; }
.dentalea-mobile-body { padding: 24px; }
.dentalea-mobile-body img { height: 300px; border-radius: 160px 160px 6px 6px; margin-bottom: 26px; }

.ventkontur { background: #f0f2f4; }
.ventkontur .commercial-nav { background: #344250; color: white; }
.ventkontur .commercial-brand { font-family: Consolas, monospace; text-transform: uppercase; }
.vent-cover { display: grid; grid-template-columns: 310px 1fr; min-height: 830px; }
.vent-index { padding: 40px 34px; background: #e2b92e; color: #202934; }
.vent-index a { display: block; padding: 17px 0; border-bottom: 1px solid rgba(32, 41, 52, .35); font-weight: 800; }
.vent-main { padding: 54px 62px; }
.vent-main h1 { max-width: 850px; font-family: Arial, sans-serif; font-size: 60px; text-transform: uppercase; }
.vent-hero-grid { display: grid; grid-template-columns: 1fr 340px; gap: 24px; align-items: stretch; }
.vent-hero-grid img { height: 370px; }
.vent-spec-card { padding: 26px; border-top: 8px solid #e2b92e; background: #fff; }
.vent-spec-card dl { display: grid; grid-template-columns: 1fr auto; gap: 14px; margin: 0; }
.vent-spec-card dd { margin: 0; font-weight: 800; }
.vent-table-page { padding: 42px 56px; }
.vent-table { width: 100%; border-collapse: collapse; background: white; }
.vent-table th, .vent-table td { padding: 18px; border: 1px solid #cbd2d8; text-align: left; }
.vent-table th { background: #3f5268; color: white; }
.vent-table td:first-child { font-weight: 800; }
.vent-table-image { display: grid; grid-template-columns: 1fr 360px; gap: 28px; margin-bottom: 28px; }
.vent-table-image img { height: 220px; }
.vent-filter { display: grid; grid-template-columns: 360px 1fr; min-height: 830px; }
.vent-filter-panel { padding: 38px; background: #fff; border-right: 1px solid #cad1d7; }
.vent-filter-panel .commercial-field { margin-bottom: 14px; }
.vent-results { padding: 40px 48px; }
.equipment-row { display: grid; grid-template-columns: 120px 1fr 160px; gap: 24px; align-items: center; padding: 18px; border-top: 1px solid #cbd2d8; background: white; }
.equipment-row img { height: 82px; }
.equipment-code { font-family: Consolas, monospace; font-weight: 800; }
.vent-mobile-body { padding: 24px 20px; }
.vent-mobile-body img { height: 240px; margin: 20px 0; }
.vent-mobile-spec { display: grid; grid-template-columns: 1fr 1fr; gap: 1px; background: #c8d0d7; }
.vent-mobile-spec div { padding: 16px; background: #fff; }

.syr-hleb { background: #fff; }
.syr-hleb .commercial-nav { border-bottom: 1px solid #eadfe1; }
.syr-hleb .commercial-brand { color: #75273b; font: 700 30px Georgia, serif; }
.food-cover { display: grid; grid-template-columns: 58% 42%; min-height: 750px; }
.food-product { position: relative; padding: 32px 48px; background: #f4eceb; }
.food-product img { height: 610px; }
.food-price { position: absolute; right: 66px; top: 58px; display: grid; place-items: center; width: 128px; height: 128px; border-radius: 50%; background: #4d8757; color: white; font-size: 24px; font-weight: 800; }
.food-copy { display: flex; flex-direction: column; justify-content: center; padding: 62px; }
.food-copy h1 { font-family: Georgia, serif; font-size: 66px; font-weight: 500; }
.food-marquee { padding: 24px 56px; background: #75273b; color: white; font-size: 18px; font-weight: 700; word-spacing: 30px; }
.food-catalog { padding: 44px 58px; }
.food-grid { display: grid; grid-template-columns: 1.35fr 1fr 1fr; gap: 22px; }
.food-card { padding-bottom: 20px; border-bottom: 2px solid #75273b; }
.food-card img { height: 235px; margin-bottom: 18px; }
.food-card:first-child img { height: 340px; }
.food-card:first-child { grid-row: span 2; }
.food-builder { display: grid; grid-template-columns: 1fr 420px; gap: 42px; padding: 48px 62px; background: #f8f4f2; }
.gift-shelf { display: grid; grid-template-columns: repeat(2, 1fr); gap: 18px; }
.gift-item { display: grid; grid-template-columns: 120px 1fr; gap: 18px; padding: 14px; background: white; }
.gift-item img { height: 105px; }
.gift-summary { padding: 30px; border-top: 6px solid #4d8757; background: #fff; }
.gift-total { display: flex; justify-content: space-between; margin: 28px 0; font: 700 25px Georgia, serif; }
.food-mobile-body { padding: 24px; }
.food-mobile-body img { height: 315px; margin-bottom: 24px; }
.food-mobile-body h1 { color: #75273b; font-family: Georgia, serif; }

.kvadrat-remonta { background: #fff; }
.kvadrat-remonta .commercial-brand { display: flex; align-items: center; gap: 12px; text-transform: uppercase; }
.kvadrat-remonta .commercial-brand::before { content: ""; width: 22px; height: 22px; background: var(--support); }
.remont-cover { padding: 40px 56px; }
.remont-cover-head { display: grid; grid-template-columns: 1fr 390px; gap: 50px; align-items: end; margin-bottom: 28px; }
.remont-cover h1 { max-width: 980px; font-size: 74px; }
.remont-gallery { display: grid; grid-template-columns: 1.5fr .85fr .85fr; grid-template-rows: 230px 230px; gap: 14px; }
.remont-gallery img { width: 100%; height: 100%; object-fit: cover; }
.remont-gallery img:first-child { grid-row: 1 / 3; }
.remont-tile { display: flex; flex-direction: column; justify-content: flex-end; padding: 24px; background: #222a34; color: white; }
.remont-tile.support { background: var(--support); }
.remont-case { display: grid; grid-template-columns: 56% 44%; min-height: 830px; }
.remont-case-media { padding: 38px; background: #242c36; }
.remont-case-media img { height: 500px; }
.remont-case-facts { display: grid; grid-template-columns: 1fr 1fr; margin-top: 20px; color: white; }
.remont-case-copy { padding: 60px 58px; }
.remont-phase { padding: 18px 0; border-bottom: 1px solid #d4d9df; }
.remont-estimate { padding: 42px 58px; background: #f1f4f8; }
.estimate-head { display: grid; grid-template-columns: 1fr 360px; gap: 40px; align-items: end; }
.estimate-head img { height: 190px; }
.estimate-table { width: 100%; margin-top: 25px; border-collapse: collapse; background: white; }
.estimate-table th, .estimate-table td { padding: 17px 20px; border-bottom: 1px solid #d7dde4; text-align: left; }
.estimate-table th { background: #222a34; color: white; }
.estimate-table td:last-child, .estimate-table th:last-child { text-align: right; }
.estimate-total { color: var(--accent); font-size: 24px; font-weight: 800; }
.remont-mobile-body { padding: 24px 20px; }
.remont-mobile-body img { height: 280px; margin-bottom: 24px; }
.remont-mobile-facts { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin: 24px 0; }
.remont-mobile-facts div { padding: 15px; background: #edf2fb; }
"""


def _hero_image(project: ProjectSpec, assets: Mapping[str, str]) -> str:
    """Render the required project image with a deterministic crop contract."""
    try:
        source = assets["hero"]
    except KeyError as exc:
        raise KeyError(f"Missing hero asset for commercial project: {project.slug}") from exc
    return (
        '<img class="commercial-hero-image" '
        f'src="{escape_html(source)}" alt="{escape_html(_IMAGE_ALTS[project.slug])}" '
        'style="aspect-ratio: 16 / 10;" />'
    )


def _nav(project: ProjectSpec, links: tuple[str, ...], action: str, action_icon: str) -> str:
    link_html = "".join(f"<a href=\"#\">{escape_html(link)}</a>" for link in links)
    return (
        '<header class="commercial-nav">'
        f'<a class="commercial-brand" href="#">{escape_html(project.brand)}</a>'
        f'<nav class="commercial-links" aria-label="Основная навигация">{link_html}</nav>'
        f'<button class="commercial-button">{icon(action_icon, size=18)}{escape_html(action)}</button>'
        "</header>"
    )


def _widget(name: str, content: str, class_name: str) -> str:
    return panel("section", content, class_name=class_name, attrs={"data-widget": name})


def _page(project: ProjectSpec, shot: ShotSpec, layout: str, content: str) -> str:
    mobile_class = " commercial-mobile" if shot.layout == "mobile" else ""
    return (
        f"<style>{_COMMERCIAL_CSS}</style>"
        f'<main class="commercial-page {escape_html(project.palette)} {escape_html(project.slug)}{mobile_class}" '
        f'data-project="{escape_html(project.slug)}" data-layout="{escape_html(layout)}" '
        f'data-variant="{escape_html(shot.variant)}">{content}</main>'
    )


def _tochka_hoda(project: ProjectSpec, shot: ShotSpec, assets: Mapping[str, str]) -> str:
    image = _hero_image(project, assets)
    nav = _nav(project, ("Услуги", "Цены", "Команда", "Контакты"), "Записаться", "calendar")
    if shot.variant == "cover":
        body = (
            f"{nav}<section class=\"tochka-cover\"><div class=\"tochka-copy\">"
            '<div class="commercial-label">Автосервис полного цикла</div><h1>Диагностика без догадок</h1>'
            '<p>Проверяем автомобиль по понятному регламенту, показываем результаты и согласуем работы до ремонта.</p>'
            f'<button class="commercial-button">{icon("arrow-right")}Выбрать услугу</button></div>'
            f'<div class="tochka-media">{image}<div class="tochka-status"><strong>Свободный пост сегодня</strong>'
            '<span>Приём в 16:30 · мастер Алексей</span></div></div></section>'
            '<section class="tochka-strip"><div>Диагностика</div><div>Слесарный ремонт</div><div>ТО по регламенту</div><div>Гарантия на работы</div></section>'
        )
        return _page(project, shot, COMMERCIAL_LAYOUTS[project.slug][0], body)
    if shot.variant == "content":
        rows = "".join(
            f'<article class="timeline-row"><span class="timeline-index">0{index}</span><div><h3>{title}</h3><p>{copy}</p></div>{image if index == 2 else "<strong>30–45 минут</strong>"}</article>'
            for index, (title, copy) in enumerate((
                ("Принимаем автомобиль", "Фиксируем жалобы и историю обслуживания."),
                ("Проводим проверку", "Сканер, подъёмник и инструментальная диагностика."),
                ("Выдаём заключение", "Объясняем приоритеты и стоимость каждого шага."),
            ), start=1)
        )
        return _page(project, shot, COMMERCIAL_LAYOUTS[project.slug][1], f'{nav}<section class="tochka-timeline"><div class="commercial-label">Как проходит услуга</div><h2>Проверка по 28 пунктам</h2>{rows}</section>')
    if shot.variant == "function":
        form = (
            '<div class="tochka-booking-form"><div class="commercial-label">Онлайн-запись</div><h2>Диагностика без догадок</h2>'
            '<div class="commercial-form-row"><div class="commercial-field">Kia Rio, 2019</div><div class="commercial-field">Компьютерная диагностика</div>'
            '<div class="commercial-field">23 августа, после 15:00</div><div class="commercial-field">+7 999 245-18-40</div></div>'
            f'<button class="commercial-button">{icon("calendar")}Подтвердить время</button></div>'
        )
        side = f'<aside class="tochka-booking-media">{image}<h3>Что входит</h3><p class="commercial-check">{icon("check")}Сканирование электронных блоков</p><p class="commercial-check">{icon("check")}Осмотр ходовой части</p></aside>'
        return _page(project, shot, COMMERCIAL_LAYOUTS[project.slug][2], f'{nav}{_widget("service-booking", form + side, "tochka-booking")}')
    body = f'{nav}<section class="tochka-mobile-body"><div class="commercial-label">Автосервис рядом</div><h1>Диагностика без догадок</h1>{image}<p>Покажем состояние автомобиля и согласуем только нужные работы.</p><button class="commercial-button">{icon("phone")}Записаться</button></section>'
    return _page(project, shot, "split-diagnostic-mobile", body)


def _dentalea(project: ProjectSpec, shot: ShotSpec, assets: Mapping[str, str]) -> str:
    image = _hero_image(project, assets)
    nav = _nav(project, ("Лечение", "Врачи", "Клиника", "Пациентам"), "Выбрать врача", "calendar")
    if shot.variant == "cover":
        body = f'{nav}<section class="dentalea-cover"><div class="dentalea-copy"><div class="commercial-label">Стоматология для всей семьи</div><h1>Спокойно объясняем. Бережно лечим.</h1><p>Диагностика, понятный план и лечение в одном месте. Без спешки и недоказуемых обещаний.</p><button class="commercial-button">Первичная консультация{icon("arrow-right")}</button></div><div class="dentalea-portrait">{image}<div class="dentalea-note">План лечения до начала работ</div></div></section><section class="dentalea-services"><div>Терапия и профилактика</div><div>Имплантация и протезирование</div><div>Детский приём</div></section>'
        return _page(project, shot, COMMERCIAL_LAYOUTS[project.slug][0], body)
    if shot.variant == "content":
        steps = "".join(f'<article class="dentalea-step"><b>{number}</b><div><h3>{title}</h3><p>{copy}</p></div></article>' for number, title, copy in (("01", "Диагностика", "Снимки и осмотр помогают увидеть полную картину."), ("02", "План", "Фиксируем этапы, сроки и стоимость лечения."), ("03", "Лечение", "Двигаемся последовательно и контролируем результат.")))
        body = f'{nav}<section class="dentalea-detail"><aside class="dentalea-detail-aside">{image}<h3>Имплантация зубов</h3><p>Врач оценивает показания и обсуждает альтернативы на консультации.</p></aside><div class="dentalea-detail-main"><div class="commercial-label">Подробно об услуге</div><h2>План лечения до начала работ</h2>{steps}</div></section>'
        return _page(project, shot, COMMERCIAL_LAYOUTS[project.slug][1], body)
    if shot.variant == "function":
        schedule = (("Пн, 24", ("10:00", "13:30")), ("Вт, 25", ("12:00", "17:00")), ("Ср, 26", ("09:30", "15:30")), ("Чт, 27", ("11:00", "18:30")), ("Пт, 28", ("10:30", "14:00")))
        day_columns = []
        for day, times in schedule:
            time_slots = "".join(f'<div class="schedule-time">{time}</div>' for time in times)
            day_columns.append(f'<div class="schedule-day"><strong>{day}</strong>{time_slots}</div>')
        days = "".join(day_columns)
        content = f'<div><div class="commercial-label">Расписание на неделю</div><h2>План лечения до начала работ</h2><div class="schedule-days">{days}</div></div><aside class="dentalea-doctor">{image}<h3>Анна Михайлова</h3><p>Стоматолог-терапевт · первичный приём 60 минут</p><button class="commercial-button">Выбрать время</button></aside>'
        return _page(project, shot, COMMERCIAL_LAYOUTS[project.slug][2], f'{nav}{_widget("doctor-schedule", content, "dentalea-schedule")}')
    body = f'{nav}<section class="dentalea-mobile-body">{image}<div class="commercial-label">Бережная стоматология</div><h1>План лечения до начала работ</h1><p>Познакомьтесь с врачом и выберите удобное время консультации.</p><button class="commercial-button">{icon("calendar")}Выбрать врача</button></section>'
    return _page(project, shot, "calm-editorial-mobile", body)


def _ventkontur(project: ProjectSpec, shot: ShotSpec, assets: Mapping[str, str]) -> str:
    image = _hero_image(project, assets)
    nav = _nav(project, ("Каталог", "Подбор", "Документация", "Проекты"), "Запросить расчёт", "arrow-right")
    if shot.variant == "cover":
        side = '<aside class="vent-index"><div class="commercial-label">Разделы</div><a href="#">01 Установки</a><a href="#">02 Вентиляторы</a><a href="#">03 Автоматика</a><a href="#">04 Воздуховоды</a></aside>'
        specs = '<aside class="vent-spec-card"><div class="commercial-label">VKU-45</div><dl><dt>Расход</dt><dd>4 500 м³/ч</dd><dt>Давление</dt><dd>680 Па</dd><dt>КПД</dt><dd>83%</dd><dt>Срок поставки</dt><dd>12 дней</dd></dl></aside>'
        body = f'{nav}<section class="vent-cover">{side}<div class="vent-main"><h1>Подбор по расходу воздуха</h1><p>Каталог приточно-вытяжных установок с инженерными характеристиками и рабочими точками.</p><div class="vent-hero-grid">{image}{specs}</div></div></section>'
        return _page(project, shot, COMMERCIAL_LAYOUTS[project.slug][0], body)
    if shot.variant == "content":
        rows = "".join(f'<tr><td>{model}</td><td>{flow}</td><td>{pressure}</td><td>{power}</td><td>В наличии</td></tr>' for model, flow, pressure, power in (("VKU-25", "2 500 м³/ч", "540 Па", "1,5 кВт"), ("VKU-45", "4 500 м³/ч", "680 Па", "3,0 кВт"), ("VKU-70", "7 000 м³/ч", "820 Па", "5,5 кВт")))
        body = f'{nav}<section class="vent-table-page"><div class="vent-table-image"><div><div class="commercial-label">Каталог оборудования</div><h2>Приточно-вытяжные установки</h2><p>Сравните рабочие параметры без перехода между карточками.</p></div>{image}</div><table class="vent-table"><thead><tr><th>Модель</th><th>Расход</th><th>Давление</th><th>Мощность</th><th>Статус</th></tr></thead><tbody>{rows}</tbody></table></section>'
        return _page(project, shot, COMMERCIAL_LAYOUTS[project.slug][1], body)
    if shot.variant == "function":
        filters = f'<aside class="vent-filter-panel"><div class="commercial-label">Инженерный фильтр</div><h2>Подбор по расходу воздуха</h2><div class="commercial-field">Расход: 3 000–5 000 м³/ч</div><div class="commercial-field">Давление: от 600 Па</div><div class="commercial-field">Нагреватель: водяной</div><div class="commercial-field">Монтаж: внутренний</div><button class="commercial-button">{icon("filter")}Показать 3 модели</button></aside>'
        row = lambda model, value: f'<article class="equipment-row">{image}<div><span class="equipment-code">{model}</span><p>{value} · водяной нагреватель · автоматика</p></div><button class="commercial-button secondary">В спецификацию</button></article>'
        results = f'<div class="vent-results"><h3>Подходящие установки</h3>{row("VKU-45", "4 500 м³/ч")}{row("VKU-50", "5 000 м³/ч")}</div>'
        return _page(project, shot, COMMERCIAL_LAYOUTS[project.slug][2], f'{nav}{_widget("equipment-filter", filters + results, "vent-filter")}')
    body = f'{nav}<section class="vent-mobile-body"><div class="commercial-label">Каталог вентиляции</div><h1>Подбор по расходу воздуха</h1>{image}<div class="vent-mobile-spec"><div><strong>4 500</strong><br />м³/ч</div><div><strong>680</strong><br />Па</div></div><button class="commercial-button">{icon("filter")}Подобрать установку</button></section>'
    return _page(project, shot, "technical-index-mobile", body)


def _syr_hleb(project: ProjectSpec, shot: ShotSpec, assets: Mapping[str, str]) -> str:
    image = _hero_image(project, assets)
    nav = _nav(project, ("Сыры", "Хлеб", "Наборы", "Доставка"), "Корзина · 2", "shopping-cart")
    if shot.variant == "cover":
        body = f'{nav}<section class="food-cover"><div class="food-product">{image}<div class="food-price">2 490 ₽</div></div><div class="food-copy"><div class="commercial-label">Набор недели</div><h1>Сыр, хлеб и хороший повод</h1><p>Собираем гастрономические наборы из фермерских сыров, свежего хлеба и сезонных дополнений.</p><button class="commercial-button">Выбрать набор{icon("arrow-right")}</button></div></section><div class="food-marquee">КАМАМБЕР ЧИАБАТТА КОНФИТЮР ЧЕДДЕР ФОКАЧЧА</div>'
        return _page(project, shot, COMMERCIAL_LAYOUTS[project.slug][0], body)
    if shot.variant == "content":
        card = lambda title, price: f'<article class="food-card">{image}<h3>{title}</h3><p>{price} · доставка завтра</p></article>'
        body = f'{nav}<section class="food-catalog"><div class="commercial-label">Подарочные коллекции</div><h2>Наборы, которые хочется открыть</h2><div class="food-grid">{card("Большой вечер", "3 890 ₽")}{card("Завтрак в городе", "1 790 ₽")}{card("Сырное знакомство", "2 390 ₽")}{card("Для пикника", "2 790 ₽")}{card("Без вина", "1 990 ₽")}</div></section>'
        return _page(project, shot, COMMERCIAL_LAYOUTS[project.slug][1], body)
    if shot.variant == "function":
        item = lambda title, note: f'<article class="gift-item">{image}<div><h3>{title}</h3><p>{note}</p><span class="commercial-check">{icon("check")}Добавлено</span></div></article>'
        shelf = f'<div><div class="commercial-label">Шаг 2 из 3 · наполнение</div><h2>Соберите подарочный набор</h2><div class="gift-shelf">{item("Камамбер", "180 г · мягкий")}{item("Ремесленный хлеб", "400 г · на закваске")}{item("Грушевый конфитюр", "120 г · пряный")}{item("Ореховый микс", "150 г · жареный")}</div></div>'
        summary = f'<aside class="gift-summary"><h3>Ваш набор</h3><p>Коробка «Бордо»</p><p>4 продукта</p><p>Открытка с вашим текстом</p><div class="gift-total"><span>Итого</span><span>2 640 ₽</span></div><button class="commercial-button">{icon("shopping-cart")}В корзину</button></aside>'
        return _page(project, shot, COMMERCIAL_LAYOUTS[project.slug][2], f'{nav}{_widget("gift-builder", shelf + summary, "food-builder")}')
    body = f'{nav}<section class="food-mobile-body">{image}<div class="commercial-label">Подарочный набор</div><h1>Соберите вкусный подарок</h1><p>Выберите основу, добавьте продукты и подпишите открытку.</p><button class="commercial-button">Собрать набор{icon("arrow-right")}</button></section>'
    return _page(project, shot, "product-led-mobile", body)


def _kvadrat_remonta(project: ProjectSpec, shot: ShotSpec, assets: Mapping[str, str]) -> str:
    image = _hero_image(project, assets)
    nav = _nav(project, ("Проекты", "Услуги", "Этапы", "Стоимость"), "Обсудить ремонт", "phone")
    if shot.variant == "cover":
        gallery = f'<div class="remont-gallery">{image}<div class="remont-tile"><strong>ЖК «Береговой»</strong><span>82 м² · современный стиль</span></div><div class="remont-tile support"><strong>14 недель</strong><span>от замера до сдачи</span></div><div class="remont-tile"><strong>Смотреть все проекты</strong></div><div class="remont-tile"><strong>Авторский надзор</strong><span>включён в договор</span></div></div>'
        body = f'{nav}<section class="remont-cover"><div class="remont-cover-head"><div><div class="commercial-label">Ремонт квартир под ключ</div><h1>Пространство, собранное по плану</h1></div><div><p>Показываем реальные этапы, материалы и смету до начала работ.</p><button class="commercial-button">Смотреть проекты{icon("arrow-right")}</button></div></div>{gallery}</section>'
        return _page(project, shot, COMMERCIAL_LAYOUTS[project.slug][0], body)
    if shot.variant == "content":
        phases = "".join(f'<div class="remont-phase"><h3>{index}. {title}</h3><p>{copy}</p></div>' for index, title, copy in ((1, "Задача", "Объединить кухню и гостиную, сохранить много хранения."), (2, "Решение", "Скрытые шкафы, единая линия света и износостойкие материалы."), (3, "Результат", "Функциональный интерьер без визуального шума.")))
        body = f'{nav}<section class="remont-case"><div class="remont-case-media">{image}<div class="remont-case-facts"><div><strong>82 м²</strong><br />площадь</div><div><strong>14 недель</strong><br />срок работ</div></div></div><div class="remont-case-copy"><div class="commercial-label">Кейс · ЖК «Береговой»</div><h2>Квартира для семьи с двумя детьми</h2>{phases}</div></section>'
        return _page(project, shot, COMMERCIAL_LAYOUTS[project.slug][1], body)
    if shot.variant == "function":
        rows = "".join(f'<tr><td>{stage}</td><td>{term}</td><td>{cost}</td></tr>' for stage, term, cost in (("Демонтаж и подготовка", "8 дней", "186 000 ₽"), ("Инженерные работы", "15 дней", "342 000 ₽"), ("Черновая отделка", "18 дней", "428 000 ₽"), ("Чистовая отделка", "24 дня", "614 000 ₽")))
        content = f'<div class="estimate-head"><div><div class="commercial-label">Предварительный расчёт · 82 м²</div><h2>Смета по этапам</h2><p>Каждый блок работ вынесен отдельно: видно срок, стоимость и очередность.</p></div>{image}</div><table class="estimate-table"><thead><tr><th>Этап</th><th>Срок</th><th>Стоимость</th></tr></thead><tbody>{rows}<tr><td colspan="2"><strong>Работы по проекту</strong></td><td class="estimate-total">1 570 000 ₽</td></tr></tbody></table>'
        return _page(project, shot, COMMERCIAL_LAYOUTS[project.slug][2], f'{nav}{_widget("estimate-table", content, "remont-estimate")}')
    body = f'{nav}<section class="remont-mobile-body"><div class="commercial-label">Кейс · 82 м²</div><h1>Ремонт по ясному плану</h1>{image}<div class="remont-mobile-facts"><div><strong>14 недель</strong><br />срок</div><div><strong>1,57 млн ₽</strong><br />работы</div></div><button class="commercial-button">Получить смету{icon("arrow-right")}</button></section>'
    return _page(project, shot, "project-gallery-mobile", body)


_RENDERERS: dict[str, Callable[[ProjectSpec, ShotSpec, Mapping[str, str]], str]] = {
    "tochka-hoda": _tochka_hoda,
    "dentalea": _dentalea,
    "ventkontur": _ventkontur,
    "syr-hleb": _syr_hleb,
    "kvadrat-remonta": _kvadrat_remonta,
}


def render_commercial(project: ProjectSpec, shot: ShotSpec, assets: dict[str, str]) -> str:
    """Render one of the five commercial concepts for a declared shot variant."""
    try:
        renderer = _RENDERERS[project.slug]
    except KeyError as exc:
        raise KeyError(f"Unknown commercial project: {project.slug}") from exc
    if shot.variant not in {"cover", "content", "function", "mobile"}:
        raise ValueError(f"Unknown commercial shot variant: {shot.variant}")
    return renderer(project, shot, assets)
