from collections.abc import Callable, Mapping

from ..components import escape_html, panel
from ..icons import icon
from ..models import ProjectSpec, ShotSpec


LEADGEN_LAYOUTS = {
    "okna-sfera": ("measurement-workbench", "glazing-guide", "window-calculator"),
    "chistiy-metr": ("before-after-proof", "cleaning-checklist", "cleaning-calculator"),
    "teplodom": ("urgent-service-board", "repair-route", "service-request"),
    "pereezd-prosto": ("moving-day-map", "packing-plan", "moving-calculator"),
    "pravo-opora": ("legal-editorial", "claim-roadmap", "case-assessment"),
}

LEADGEN_FLOWS = {
    "okna-sfera": ("Размеры", "Профиль", "Монтаж", "Получить расчёт"),
    "chistiy-metr": ("Площадь", "Состояние", "Дополнительные зоны", "Узнать стоимость"),
    "teplodom": ("Марка котла", "Симптом", "Адрес", "Вызвать мастера"),
    "pereezd-prosto": ("Откуда", "Куда", "Объём вещей", "Рассчитать переезд"),
    "pravo-opora": ("Тип договора", "Срок просрочки", "Сумма", "Получить оценку"),
}

_IMAGE_ALTS = {
    "okna-sfera": "Светлая гостиная с новым панорамным окном",
    "chistiy-metr": "Чистая квартира после завершения ремонта",
    "teplodom": "Мастер проверяет настенный газовый котёл",
    "pereezd-prosto": "Аккуратно упакованные вещи перед квартирным переездом",
    "pravo-opora": "Юрист изучает документы по договорному спору",
}

_WIDGETS = {
    "okna-sfera": "window-calculator",
    "chistiy-metr": "cleaning-calculator",
    "teplodom": "service-request",
    "pereezd-prosto": "moving-calculator",
    "pravo-opora": "case-assessment",
}

_LEADGEN_CSS = """
.leadgen-page { width: 100%; min-height: 100%; overflow: hidden; background: var(--surface); color: var(--ink); }
.leadgen-page * { box-sizing: border-box; }
.leadgen-page a { color: inherit; text-decoration: none; }
.leadgen-page h1, .leadgen-page h2, .leadgen-page h3, .leadgen-page p { margin-top: 0; }
.leadgen-page h1 { margin-bottom: 22px; font-size: 64px; line-height: 1.02; letter-spacing: 0; }
.leadgen-page h2 { margin-bottom: 18px; font-size: 42px; line-height: 1.08; letter-spacing: 0; }
.leadgen-page h3 { margin-bottom: 9px; font-size: 21px; line-height: 1.25; }
.leadgen-page p { color: var(--ink-muted); font-size: 18px; line-height: 1.5; }
.leadgen-nav { display: flex; align-items: center; justify-content: space-between; min-height: 78px; padding: 0 54px; border-bottom: 1px solid rgba(91, 105, 118, .18); }
.leadgen-brand { font-size: 23px; font-weight: 800; }
.leadgen-links { display: flex; align-items: center; gap: 28px; font-size: 15px; font-weight: 650; }
.leadgen-button { display: inline-flex; align-items: center; justify-content: center; gap: 9px; min-height: 50px; padding: 0 21px; border: 0; border-radius: 6px; background: var(--accent); color: #fff; font: inherit; font-size: 16px; font-weight: 750; cursor: pointer; }
.leadgen-button.secondary { border: 1px solid rgba(91, 105, 118, .28); background: #fff; color: var(--ink); }
.leadgen-label { margin-bottom: 13px; color: var(--accent-strong); font-size: 14px; font-weight: 800; text-transform: uppercase; }
.leadgen-hero-image { width: 100%; object-fit: cover; background: var(--highlight); }
.leadgen-form { display: grid; gap: 17px; }
.leadgen-field { display: grid; gap: 7px; color: var(--ink); font-size: 14px; font-weight: 700; }
.leadgen-field input, .leadgen-field select { width: 100%; min-height: 50px; padding: 0 14px; border: 1px solid rgba(91, 105, 118, .34); border-radius: 5px; background: #fff; color: var(--ink); font: inherit; font-size: 15px; }
.leadgen-check { display: flex; align-items: center; gap: 10px; color: var(--ink); font-size: 15px; font-weight: 650; }
.leadgen-check input { width: 18px; height: 18px; accent-color: var(--accent); }
.leadgen-steps { display: flex; gap: 8px; margin-bottom: 22px; }
.leadgen-step { flex: 1; padding: 10px 12px; border-bottom: 3px solid rgba(91, 105, 118, .22); color: var(--ink-muted); font-size: 13px; font-weight: 700; }
.leadgen-step.active { border-color: var(--accent); color: var(--accent-strong); }
.leadgen-mobile { min-height: 920px; }
.leadgen-mobile .leadgen-nav { min-height: 66px; padding: 0 20px; }
.leadgen-mobile .leadgen-links, .leadgen-mobile .leadgen-nav .leadgen-button { display: none; }
.leadgen-mobile .leadgen-brand { font-size: 20px; }
.leadgen-mobile h1 { font-size: 39px; line-height: 1.04; }
.leadgen-mobile h2 { font-size: 31px; }
.leadgen-mobile p { font-size: 16px; }
.leadgen-mobile .leadgen-button { width: 100%; }

.okna-sfera { background: #f8fcff; }
.okna-sfera .leadgen-brand { color: #176e99; }
.window-cover { display: grid; grid-template-columns: 47% 53%; min-height: 750px; }
.window-cover-copy { padding: 72px 44px 54px 62px; }
.window-cover-copy h1 { max-width: 700px; }
.window-size-summary { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1px; margin: 32px 0; background: #b8d8e6; }
.window-size-summary div { padding: 16px; background: #fff; }
.window-size-summary strong { display: block; color: #176e99; font-size: 25px; }
.window-cover-media { position: relative; padding: 34px; background: #e4f5fd; }
.window-cover-media img { height: 570px; }
.window-material { position: absolute; right: 54px; bottom: 64px; width: 270px; padding: 20px; border-left: 6px solid #edb92d; background: #fff; }
.window-guide { padding: 48px 58px; }
.window-guide-head { display: grid; grid-template-columns: 1fr 390px; gap: 42px; align-items: end; margin-bottom: 28px; }
.window-guide-head img { height: 210px; }
.window-options { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.window-option { padding: 24px; border-top: 5px solid #9bcfe6; background: #fff; box-shadow: 0 12px 26px rgba(31, 92, 120, .08); }
.window-option.selected { border-color: #edb92d; }
.window-calc { display: grid; grid-template-columns: 1fr 420px; gap: 42px; padding: 46px 60px; background: #eef8fd; }
.window-form-card { padding: 30px; background: #fff; }
.window-dimensions { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.window-preview { padding: 30px; background: #ddecf4; }
.window-preview img { height: 260px; margin-bottom: 20px; }
.window-total { display: flex; justify-content: space-between; padding-top: 18px; border-top: 1px solid #aac5d1; font-size: 22px; font-weight: 800; }
.window-mobile-body { padding: 24px 20px; }
.window-mobile-body img { height: 260px; margin: 20px 0; }

.chistiy-metr { background: #f8ffff; }
.chistiy-metr .leadgen-nav { background: #182c2e; color: #fff; }
.chistiy-metr .leadgen-brand { color: #d6df43; text-transform: uppercase; }
.clean-cover { display: grid; grid-template-columns: 58% 42%; min-height: 760px; }
.clean-visual { position: relative; padding: 38px; background: #26a59b; }
.clean-visual img { height: 560px; }
.clean-stamp { position: absolute; left: 58px; bottom: 58px; padding: 18px 22px; background: #182c2e; color: #fff; font-weight: 800; }
.clean-copy { display: flex; flex-direction: column; justify-content: center; padding: 52px; }
.clean-proof-list { margin: 12px 0 28px; padding: 0; list-style: none; }
.clean-proof-list li { padding: 12px 0; border-bottom: 1px solid #c9e1df; font-weight: 700; }
.clean-checklist { display: grid; grid-template-columns: 330px 1fr; min-height: 820px; }
.clean-checklist-aside { padding: 46px 38px; background: #192d2f; color: #fff; }
.clean-checklist-aside p { color: #cae0df; }
.clean-checklist-aside img { height: 210px; margin-bottom: 24px; }
.clean-rooms { padding: 46px 54px; }
.clean-room { display: grid; grid-template-columns: 70px 1fr 210px; gap: 20px; align-items: center; padding: 20px 0; border-top: 1px solid #c9dddc; }
.clean-room b { color: #26a59b; font-size: 30px; }
.clean-room span { color: #16766f; font-weight: 750; }
.clean-calc { display: grid; grid-template-columns: 440px 1fr; gap: 48px; padding: 46px 58px; background: #eaf8f7; }
.clean-form-card { padding: 30px; background: #fff; }
.clean-result { padding: 34px; border-left: 8px solid #d6cd39; background: #183033; color: #fff; }
.clean-result p { color: #c9dfde; }
.clean-result img { height: 260px; margin-bottom: 24px; }
.clean-result strong { display: block; margin: 18px 0 5px; color: #e4eb6b; font-size: 34px; }
.clean-mobile-body { padding: 22px 20px; }
.clean-mobile-body img { height: 245px; margin: 18px 0; }

.teplodom { background: #fff; }
.teplodom .leadgen-nav { border-bottom: 4px solid #c54b4b; }
.teplodom .leadgen-brand { color: #943434; text-transform: uppercase; }
.boiler-cover { display: grid; grid-template-columns: 360px 1fr; min-height: 790px; }
.boiler-status { padding: 48px 36px; background: #25352f; color: #fff; }
.boiler-status p { color: #cfddd7; }
.boiler-status-line { margin-top: 28px; padding: 18px 0; border-top: 1px solid #587268; }
.boiler-status-line strong { display: block; margin-bottom: 5px; color: #70c89c; }
.boiler-main { display: grid; grid-template-columns: 1fr 430px; gap: 42px; padding: 58px; }
.boiler-main h1 { max-width: 780px; }
.boiler-main img { height: 500px; }
.repair-route { padding: 46px 58px; background: #f6f7f6; }
.repair-route-head { display: grid; grid-template-columns: 1fr 390px; gap: 38px; align-items: end; }
.repair-route-head img { height: 210px; }
.repair-route-list { display: grid; grid-template-columns: repeat(4, 1fr); margin-top: 30px; border-top: 1px solid #cfd6d2; }
.repair-route-step { min-height: 250px; padding: 24px; border-right: 1px solid #cfd6d2; }
.repair-route-step b { display: block; margin-bottom: 32px; color: #c54b4b; font-size: 34px; }
.boiler-request { display: grid; grid-template-columns: 1fr 430px; gap: 42px; padding: 44px 58px; }
.boiler-form-card { padding: 30px; border-top: 7px solid #c54b4b; background: #f8eeee; }
.boiler-assurance { padding: 30px; background: #263a32; color: #fff; }
.boiler-assurance img { height: 250px; margin-bottom: 22px; }
.boiler-assurance p { color: #cedbd6; }
.boiler-mobile-body { padding: 22px 20px; }
.boiler-mobile-body img { height: 250px; margin: 18px 0; }

.pereezd-prosto { background: #f7f9ff; }
.pereezd-prosto .leadgen-brand { color: #24449b; }
.move-cover { display: grid; grid-template-columns: 1fr 510px; gap: 48px; min-height: 760px; padding: 54px 60px; }
.move-copy h1 { max-width: 850px; }
.move-route { display: grid; grid-template-columns: 1fr 48px 1fr; align-items: center; margin: 30px 0; }
.move-point { padding: 18px; border: 1px solid #b9c8ee; background: #fff; }
.move-arrow { color: #315fd6; text-align: center; }
.move-media { position: relative; }
.move-media img { height: 520px; }
.move-tag { position: absolute; left: -28px; bottom: 28px; width: 265px; padding: 20px; background: #24935f; color: #fff; font-weight: 750; }
.packing-plan { display: grid; grid-template-columns: 1fr 390px; min-height: 810px; }
.packing-main { padding: 48px 56px; }
.packing-zone { display: grid; grid-template-columns: 70px 1fr 170px; gap: 18px; align-items: center; padding: 21px 0; border-top: 1px solid #cbd4ec; }
.packing-zone b { color: #315fd6; font-size: 30px; }
.packing-zone span { color: #24935f; font-weight: 750; }
.packing-aside { padding: 38px; background: #e9efff; }
.packing-aside img { height: 245px; margin-bottom: 24px; }
.moving-calc { display: grid; grid-template-columns: 1fr 410px; gap: 44px; padding: 44px 58px; background: #eef2fc; }
.moving-form-card { padding: 30px; background: #fff; }
.moving-summary { padding: 30px; background: #253c77; color: #fff; }
.moving-summary p { color: #d5def4; }
.moving-summary img { height: 245px; margin-bottom: 22px; }
.moving-summary strong { display: block; margin-top: 18px; font-size: 28px; }
.moving-mobile-body { padding: 22px 20px; }
.moving-mobile-body img { height: 245px; margin: 18px 0; }

.pravo-opora { background: #fbfcfa; }
.pravo-opora .leadgen-nav { border-bottom: 0; background: #173e31; color: #fff; }
.pravo-opora .leadgen-brand { color: #d8ba6b; font-family: Georgia, serif; font-size: 27px; font-weight: 600; }
.legal-cover { display: grid; grid-template-columns: 54% 46%; min-height: 770px; }
.legal-copy { padding: 74px 58px 54px 72px; background: #f3f6f1; }
.legal-copy h1 { max-width: 800px; font-family: Georgia, serif; font-size: 68px; font-weight: 500; }
.legal-principles { display: grid; grid-template-columns: repeat(2, 1fr); gap: 1px; margin-top: 34px; background: #cdd9d2; }
.legal-principles div { padding: 17px; background: #fff; font-weight: 700; }
.legal-media { padding: 38px; background: #173e31; }
.legal-media img { height: 555px; }
.claim-roadmap { padding: 46px 62px; }
.claim-roadmap-head { display: grid; grid-template-columns: 1fr 390px; gap: 42px; align-items: end; margin-bottom: 22px; }
.claim-roadmap-head img { height: 205px; }
.claim-step { display: grid; grid-template-columns: 100px 1fr 220px; gap: 24px; padding: 20px 0; border-top: 1px solid #ced8d1; }
.claim-step b { color: #b28b2f; font: 30px Georgia, serif; }
.claim-step span { color: #1f6b4e; font-weight: 750; }
.case-assessment { display: grid; grid-template-columns: 1fr 410px; gap: 44px; padding: 44px 60px; background: #eef4f0; }
.legal-form-card { padding: 30px; background: #fff; }
.legal-note { padding: 30px; border-top: 7px solid #b28b2f; background: #173e31; color: #fff; }
.legal-note img { height: 230px; margin-bottom: 22px; }
.legal-note p { color: #d2dfd9; }
.legal-mobile-body { padding: 22px 20px; }
.legal-mobile-body h1 { font-family: Georgia, serif; font-weight: 500; }
.legal-mobile-body img { height: 240px; margin: 18px 0; }
"""


def _hero_image(project: ProjectSpec, assets: Mapping[str, str]) -> str:
    try:
        source = assets["hero"]
    except KeyError as exc:
        raise KeyError(f"Missing hero asset for lead-generation project: {project.slug}") from exc
    return (
        '<img class="leadgen-hero-image" '
        f'src="{escape_html(source)}" alt="{escape_html(_IMAGE_ALTS[project.slug])}" '
        'style="aspect-ratio: 16 / 10;" />'
    )


def _nav(project: ProjectSpec, links: tuple[str, ...], action: str) -> str:
    link_html = "".join(f'<a href="#">{escape_html(link)}</a>' for link in links)
    return (
        '<header class="leadgen-nav">'
        f'<a class="leadgen-brand" href="#">{escape_html(project.brand)}</a>'
        f'<nav class="leadgen-links" aria-label="Основная навигация">{link_html}</nav>'
        f'<button class="leadgen-button">{icon("phone", size=18)}{escape_html(action)}</button>'
        "</header>"
    )


def _field(label: str, name: str, value: str, *, input_type: str = "text") -> str:
    return (
        f'<label class="leadgen-field">{escape_html(label)}'
        f'<input type="{escape_html(input_type)}" name="{escape_html(name)}" '
        f'value="{escape_html(value)}" /></label>'
    )


def _select(label: str, name: str, value: str, options: tuple[str, ...]) -> str:
    option_html = "".join(
        f'<option{" selected" if option == value else ""}>{escape_html(option)}</option>'
        for option in options
    )
    return (
        f'<label class="leadgen-field">{escape_html(label)}'
        f'<select name="{escape_html(name)}">{option_html}</select></label>'
    )


def _checkbox(label: str, name: str) -> str:
    return (
        '<label class="leadgen-check">'
        f'<input type="checkbox" name="{escape_html(name)}" checked />'
        f"{escape_html(label)}</label>"
    )


def _form(project: ProjectSpec, fields: str) -> str:
    steps = "".join(
        f'<span class="leadgen-step{" active" if index < 3 else ""}">{escape_html(label)}</span>'
        for index, label in enumerate(LEADGEN_FLOWS[project.slug])
    )
    action = LEADGEN_FLOWS[project.slug][-1]
    return (
        f'<form class="leadgen-form" action="#" method="post"><div class="leadgen-steps">{steps}</div>'
        f'{fields}<button class="leadgen-button" type="submit">{escape_html(action)}{icon("arrow-right")}</button>'
        "</form>"
    )


def _widget(project: ProjectSpec, content: str, class_name: str) -> str:
    return panel(
        "section",
        content,
        class_name=class_name,
        attrs={"data-widget": _WIDGETS[project.slug]},
    )


def _page(project: ProjectSpec, shot: ShotSpec, layout: str, content: str) -> str:
    mobile_class = " leadgen-mobile" if shot.layout == "mobile" else ""
    return (
        f"<style>{_LEADGEN_CSS}</style>"
        f'<main class="leadgen-page {escape_html(project.palette)} {escape_html(project.slug)}{mobile_class}" '
        f'data-project="{escape_html(project.slug)}" data-layout="{escape_html(layout)}" '
        f'data-variant="{escape_html(shot.variant)}">{content}</main>'
    )


def _okna_sfera(project: ProjectSpec, shot: ShotSpec, assets: Mapping[str, str]) -> str:
    image = _hero_image(project, assets)
    nav = _nav(project, ("Окна", "Балконы", "Монтаж", "Примеры"), "Заказать замер")
    if shot.variant == "cover":
        summary = '<div class="window-size-summary"><div><strong>1400 мм</strong>ширина</div><div><strong>1500 мм</strong>высота</div><div><strong>3 створки</strong>конфигурация</div></div>'
        body = f'{nav}<section class="window-cover"><div class="window-cover-copy"><div class="leadgen-label">Окна по вашим размерам</div><h1>Теплее дома. Точнее в расчёте.</h1><p>Подберём профиль, стеклопакет и монтаж под комнату, этаж и способ проветривания.</p>{summary}<button class="leadgen-button">Рассчитать окно{icon("arrow-right")}</button></div><div class="window-cover-media">{image}<div class="window-material"><strong>Профиль 70 мм</strong><br />Трёхкамерный стеклопакет и тёплая дистанционная рамка</div></div></section>'
        return _page(project, shot, LEADGEN_LAYOUTS[project.slug][0], body)
    if shot.variant == "content":
        option = lambda title, copy, selected="": f'<article class="window-option {selected}"><h3>{title}</h3><p>{copy}</p><span>{icon("check")} Подходит для квартиры</span></article>'
        body = f'{nav}<section class="window-guide"><div class="window-guide-head"><div><div class="leadgen-label">Выбор без лишней терминологии</div><h2>Какой стеклопакет нужен комнате</h2><p>Сравните тепло, тишину и светопропускание в трёх понятных комплектациях.</p></div>{image}</div><div class="window-options">{option("Больше света", "Для тихого двора и хорошо отапливаемой комнаты.")}{option("Тепло и тишина", "Для спальни, детской или окна у дороги.", "selected")}{option("Максимум тепла", "Для угловой комнаты, балкона или загородного дома.")}</div></section>'
        return _page(project, shot, LEADGEN_LAYOUTS[project.slug][1], body)
    if shot.variant == "function":
        fields = f'<div class="window-dimensions">{_field("Размеры · ширина, мм", "width", "1400", input_type="number")}{_field("Высота, мм", "height", "1500", input_type="number")}</div>{_select("Профиль", "profile", "Тёплый · 70 мм", ("Базовый · 58 мм", "Тёплый · 70 мм", "Усиленный · 82 мм"))}{_checkbox("Монтаж с демонтажем старого окна", "installation")}'
        form = f'<div class="window-form-card"><div class="leadgen-label">Калькулятор окна</div><h2>Рассчитайте окно по вашим размерам</h2>{_form(project, fields)}</div>'
        preview = f'<aside class="window-preview">{image}<h3>Предварительная комплектация</h3><p>Три створки · поворотно-откидная фурнитура · москитная сетка</p><div class="window-total"><span>Ориентир</span><span>от 48 600 ₽</span></div></aside>'
        return _page(project, shot, LEADGEN_LAYOUTS[project.slug][2], f'{nav}{_widget(project, form + preview, "window-calc")}')
    body = f'{nav}<section class="window-mobile-body"><div class="leadgen-label">Окна по размеру</div><h1>Тепло и тишина для вашей комнаты</h1>{image}<p>Укажите размеры и сразу увидите подходящую комплектацию.</p><button class="leadgen-button">Рассчитать окно{icon("arrow-right")}</button></section>'
    return _page(project, shot, "measurement-workbench-mobile", body)


def _chistiy_metr(project: ProjectSpec, shot: ShotSpec, assets: Mapping[str, str]) -> str:
    image = _hero_image(project, assets)
    nav = _nav(project, ("После ремонта", "Генеральная", "Поддерживающая", "Что входит"), "Рассчитать уборку")
    if shot.variant == "cover":
        proof = '<ul class="clean-proof-list"><li>Удалим строительную пыль с поверхностей</li><li>Отмоем окна, рамы и подоконники</li><li>Соберём и вынесем упаковочный мусор</li></ul>'
        body = f'{nav}<section class="clean-cover"><div class="clean-visual">{image}<div class="clean-stamp">Принимаете чистую квартиру, а не список недоделок</div></div><div class="clean-copy"><div class="leadgen-label">Уборка после ремонта</div><h1>Квартира готова к заселению</h1><p>Команда приезжает со своей техникой и последовательно очищает каждую зону.</p>{proof}<button class="leadgen-button">Узнать стоимость{icon("arrow-right")}</button></div></section>'
        return _page(project, shot, LEADGEN_LAYOUTS[project.slug][0], body)
    if shot.variant == "content":
        rows = "".join(f'<article class="clean-room"><b>0{index}</b><div><h3>{title}</h3><p>{copy}</p></div><span>{status}</span></article>' for index, title, copy, status in ((1, "Кухня", "Фасады, фартук, шкафы снаружи и техника.", "12 пунктов"), (2, "Комнаты", "Пол, плинтусы, двери, розетки и светильники.", "18 пунктов"), (3, "Санузел", "Плитка, сантехника, стекло и швы.", "14 пунктов"), (4, "Окна", "Стёкла, рамы, откосы и подоконники.", "8 пунктов")))
        body = f'{nav}<section class="clean-checklist"><aside class="clean-checklist-aside">{image}<div class="leadgen-label">Чек-лист работ</div><h2>Проверяем каждую зону</h2><p>Бригадир принимает работу по тому же списку, который видите вы.</p></aside><div class="clean-rooms">{rows}</div></section>'
        return _page(project, shot, LEADGEN_LAYOUTS[project.slug][1], body)
    if shot.variant == "function":
        fields = f'{_field("Площадь, м²", "area", "68", input_type="number")}{_select("Состояние", "condition", "После капитального ремонта", ("После косметического ремонта", "После капитального ремонта", "После сдачи новостройки"))}{_checkbox("Дополнительные зоны · лоджия", "balcony")}'
        form = f'<div class="clean-form-card"><div class="leadgen-label">Расчёт уборки</div><h2>Квартира готова к заселению</h2>{_form(project, fields)}</div>'
        result = f'<aside class="clean-result">{image}<h3>Команда из трёх клинеров</h3><p>Ориентировочное время — 7–9 часов. Точную сумму подтвердим после короткого созвона.</p><strong>от 16 900 ₽</strong><span>включая технику и средства</span></aside>'
        return _page(project, shot, LEADGEN_LAYOUTS[project.slug][2], f'{nav}{_widget(project, form + result, "clean-calc")}')
    body = f'{nav}<section class="clean-mobile-body"><div class="leadgen-label">После ремонта</div><h1>Чисто до последней полки</h1>{image}<p>Посчитайте уборку по площади и состоянию квартиры.</p><button class="leadgen-button">Узнать стоимость{icon("arrow-right")}</button></section>'
    return _page(project, shot, "before-after-proof-mobile", body)


def _teplodom(project: ProjectSpec, shot: ShotSpec, assets: Mapping[str, str]) -> str:
    image = _hero_image(project, assets)
    nav = _nav(project, ("Ремонт котлов", "Обслуживание", "Марки", "Районы"), "Вызвать мастера")
    if shot.variant == "cover":
        status = '<aside class="boiler-status"><div class="leadgen-label">Сервисная линия</div><h2>Сегодня есть окна</h2><p>Мастер уточнит симптом по телефону и возьмёт подходящие запчасти.</p><div class="boiler-status-line"><strong>08:00–22:00</strong>принимаем заявки</div><div class="boiler-status-line"><strong>До выезда</strong>согласуем стоимость диагностики</div><div class="boiler-status-line"><strong>После проверки</strong>объясним причину неисправности</div></aside>'
        body = f'{nav}<section class="boiler-cover">{status}<div class="boiler-main"><div><div class="leadgen-label">Ремонт газовых котлов</div><h1>Вернём тепло в день обращения</h1><p>Диагностируем котёл на месте и начинаем ремонт только после согласования работ.</p><button class="leadgen-button">Описать неисправность{icon("arrow-right")}</button></div>{image}</div></section>'
        return _page(project, shot, LEADGEN_LAYOUTS[project.slug][0], body)
    if shot.variant == "content":
        steps = "".join(f'<article class="repair-route-step"><b>0{index}</b><h3>{title}</h3><p>{copy}</p></article>' for index, title, copy in ((1, "Уточняем симптом", "Ошибка на дисплее, шум, падение давления или отсутствие нагрева."), (2, "Готовим выезд", "Проверяем марку и берём расходники для типовой диагностики."), (3, "Находим причину", "Тестируем узлы и показываем, что требует ремонта."), (4, "Согласуем работы", "Называем стоимость и фиксируем выполненные операции.")))
        body = f'{nav}<section class="repair-route"><div class="repair-route-head"><div><div class="leadgen-label">Порядок работы</div><h2>От симптома до понятного решения</h2><p>Без замены деталей наугад и неожиданных работ в счёте.</p></div>{image}</div><div class="repair-route-list">{steps}</div></section>'
        return _page(project, shot, LEADGEN_LAYOUTS[project.slug][1], body)
    if shot.variant == "function":
        fields = f'{_select("Марка котла", "brand", "Baxi", ("Baxi", "Bosch", "Vaillant", "Protherm"))}{_select("Симптом", "symptom", "Не нагревает воду", ("Не нагревает воду", "Показывает ошибку", "Падает давление", "Шумит при работе"))}{_field("Адрес", "address", "ул. Полярная, 18")}{_field("Возраст котла, лет", "age", "6", input_type="number")}{_checkbox("Котёл отключён до приезда мастера", "powered_off")}'
        form = f'<div class="boiler-form-card"><div class="leadgen-label">Заявка на диагностику</div><h2>Вернём тепло в день обращения</h2>{_form(project, fields)}</div>'
        assurance = f'<aside class="boiler-assurance">{image}<h3>Мастер увидит детали заявки</h3><p>Марка, симптом и адрес уже будут в заказе — не придётся повторять всё по телефону.</p><p>{icon("check")} Стоимость диагностики согласуем до выезда</p></aside>'
        return _page(project, shot, LEADGEN_LAYOUTS[project.slug][2], f'{nav}{_widget(project, form + assurance, "boiler-request")}')
    body = f'{nav}<section class="boiler-mobile-body"><div class="leadgen-label">Ремонт котлов</div><h1>Тепло начинается с точной диагностики</h1>{image}<p>Опишите симптом — мастер подготовится к выезду заранее.</p><button class="leadgen-button">Вызвать мастера{icon("arrow-right")}</button></section>'
    return _page(project, shot, "urgent-service-board-mobile", body)


def _pereezd_prosto(project: ProjectSpec, shot: ShotSpec, assets: Mapping[str, str]) -> str:
    image = _hero_image(project, assets)
    nav = _nav(project, ("Квартирный", "С упаковкой", "Грузчики", "Как работаем"), "Рассчитать переезд")
    if shot.variant == "cover":
        route = f'<div class="move-route"><div class="move-point"><strong>Откуда</strong><br />Отрадное · 2 комнаты</div><div class="move-arrow">{icon("arrow-right")}</div><div class="move-point"><strong>Куда</strong><br />Сокол · есть лифт</div></div>'
        body = f'{nav}<section class="move-cover"><div class="move-copy"><div class="leadgen-label">Квартирный переезд под ключ</div><h1>Переезд без потерянных коробок</h1><p>Маркируем вещи по комнатам, фиксируем объём и заранее планируем маршрут.</p>{route}<button class="leadgen-button">Собрать план переезда{icon("arrow-right")}</button></div><div class="move-media">{image}<div class="move-tag">Каждая коробка получает комнату и номер в описи</div></div></section>'
        return _page(project, shot, LEADGEN_LAYOUTS[project.slug][0], body)
    if shot.variant == "content":
        zones = "".join(f'<article class="packing-zone"><b>0{index}</b><div><h3>{title}</h3><p>{copy}</p></div><span>{state}</span></article>' for index, title, copy, state in ((1, "Кухня", "Посуда в бумаге, техника в защитных коробах.", "14 коробок"), (2, "Спальня", "Одежда в гардеробных боксах, текстиль отдельно.", "9 коробок"), (3, "Кабинет", "Монитор и книги промаркированы по полкам.", "7 коробок"), (4, "Прихожая", "Обувь, сезонные вещи и хозяйственный блок.", "6 коробок")))
        aside = f'<aside class="packing-aside">{image}<div class="leadgen-label">План упаковки</div><h3>36 коробок · 5 предметов мебели</h3><p>Опись помогает проверить погрузку и сразу расставить вещи в новой квартире.</p></aside>'
        body = f'{nav}<section class="packing-plan"><div class="packing-main"><div class="leadgen-label">Подготовка по комнатам</div><h2>У каждой вещи есть место назначения</h2>{zones}</div>{aside}</section>'
        return _page(project, shot, LEADGEN_LAYOUTS[project.slug][1], body)
    if shot.variant == "function":
        fields = f'{_field("Откуда", "from", "ул. Декабристов, 12")}{_field("Куда", "to", "Ленинградский проспект, 74")}{_field("Объём вещей · коробок", "boxes", "36", input_type="number")}{_checkbox("Нужна упаковка хрупких вещей", "fragile")}{_checkbox("В доме есть грузовой лифт", "lift")}'
        form = f'<div class="moving-form-card"><div class="leadgen-label">Расчёт маршрута и объёма</div><h2>Переезд без потерянных коробок</h2>{_form(project, fields)}</div>'
        summary = f'<aside class="moving-summary">{image}<h3>Предварительный план</h3><p>Машина 18 м³ · 3 грузчика · упаковочные материалы</p><strong>Около 6 часов</strong><p>Диспетчер уточнит парковку и этаж перед финальным расчётом.</p></aside>'
        return _page(project, shot, LEADGEN_LAYOUTS[project.slug][2], f'{nav}{_widget(project, form + summary, "moving-calc")}')
    body = f'{nav}<section class="moving-mobile-body"><div class="leadgen-label">Бережный переезд</div><h1>Все коробки доедут по адресу</h1>{image}<p>Соберите маршрут и объём — подготовим понятный план работ.</p><button class="leadgen-button">Рассчитать переезд{icon("arrow-right")}</button></section>'
    return _page(project, shot, "moving-day-map-mobile", body)


def _pravo_opora(project: ProjectSpec, shot: ShotSpec, assets: Mapping[str, str]) -> str:
    image = _hero_image(project, assets)
    nav = _nav(project, ("Договорные споры", "Недвижимость", "Порядок работы", "Документы"), "Обсудить ситуацию")
    if shot.variant == "cover":
        principles = '<div class="legal-principles"><div>Изучаем документы до встречи</div><div>Объясняем риски простым языком</div><div>Предлагаем несколько сценариев</div><div>Фиксируем объём работы</div></div>'
        body = f'{nav}<section class="legal-cover"><div class="legal-copy"><div class="leadgen-label">Споры с застройщиками</div><h1>Сначала — документы и факты</h1><p>Разберём договор, сроки и переписку, чтобы выбрать обоснованный следующий шаг.</p><button class="leadgen-button">Описать ситуацию{icon("arrow-right")}</button>{principles}</div><div class="legal-media">{image}</div></section>'
        return _page(project, shot, LEADGEN_LAYOUTS[project.slug][0], body)
    if shot.variant == "content":
        steps = "".join(f'<article class="claim-step"><b>{index}</b><div><h3>{title}</h3><p>{copy}</p></div><span>{result}</span></article>' for index, title, copy, result in (("01", "Проверка договора", "Сверяем обязательства, сроки и порядок уведомлений.", "Перечень оснований"), ("02", "Расчёт требований", "Отделяем подтверждённые суммы от спорных.", "Расчёт и риски"), ("03", "Претензия", "Формулируем позицию и прикладываем доказательства.", "Готовый документ"), ("04", "Следующий шаг", "Оцениваем ответ и целесообразность обращения в суд.", "План действий")))
        body = f'{nav}<section class="claim-roadmap"><div class="claim-roadmap-head"><div><div class="leadgen-label">Работа по этапам</div><h2>От договора к аргументированной позиции</h2><p>На каждом шаге понятно, какие документы нужны и какой результат вы получите.</p></div>{image}</div>{steps}</section>'
        return _page(project, shot, LEADGEN_LAYOUTS[project.slug][1], body)
    if shot.variant == "function":
        fields = f'{_select("Тип договора", "contract", "Долевое участие", ("Долевое участие", "Подряд", "Купля-продажа", "Оказание услуг"))}{_field("Срок просрочки, дней", "delay", "74", input_type="number")}{_field("Сумма, ₽", "amount", "480000", input_type="number")}{_checkbox("Договор и переписка собраны", "documents")}'
        form = f'<div class="legal-form-card"><div class="leadgen-label">Предварительный разбор</div><h2>Оценим перспективу спора</h2><p>Ответьте на несколько вопросов — юрист поймёт контекст до звонка.</p>{_form(project, fields)}</div>'
        note = f'<aside class="legal-note">{image}<h3>Что будет в ответе</h3><p>{icon("check")} Какие документы стоит проверить</p><p>{icon("check")} Какие варианты действий применимы</p><p>{icon("check")} Какие факторы могут повлиять на спор</p><p>Предварительная оценка не заменяет правовое заключение.</p></aside>'
        return _page(project, shot, LEADGEN_LAYOUTS[project.slug][2], f'{nav}{_widget(project, form + note, "case-assessment")}')
    body = f'{nav}<section class="legal-mobile-body"><div class="leadgen-label">Правовая опора</div><h1>Разберём спор по документам</h1>{image}<p>Опишите договор и сроки — подготовим вопросы для первой консультации.</p><button class="leadgen-button">Получить оценку{icon("arrow-right")}</button></section>'
    return _page(project, shot, "legal-editorial-mobile", body)


_RENDERERS: dict[str, Callable[[ProjectSpec, ShotSpec, Mapping[str, str]], str]] = {
    "okna-sfera": _okna_sfera,
    "chistiy-metr": _chistiy_metr,
    "teplodom": _teplodom,
    "pereezd-prosto": _pereezd_prosto,
    "pravo-opora": _pravo_opora,
}


def render_leadgen(project: ProjectSpec, shot: ShotSpec, assets: dict[str, str]) -> str:
    """Render one of the five lead-generation concepts for a declared shot variant."""
    try:
        renderer = _RENDERERS[project.slug]
    except KeyError as exc:
        raise KeyError(f"Unknown lead-generation project: {project.slug}") from exc
    if shot.variant not in {"cover", "content", "function", "mobile"}:
        raise ValueError(f"Unknown lead-generation shot variant: {shot.variant}")
    return renderer(project, shot, assets)
