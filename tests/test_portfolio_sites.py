import pytest

from portfolio.kwork_pack.catalog import get_project
from portfolio.kwork_pack.sites.commercial import COMMERCIAL_LAYOUTS, render_commercial
from portfolio.kwork_pack.sites.leadgen import LEADGEN_FLOWS, LEADGEN_LAYOUTS, render_leadgen


COMMERCIAL_CASES = (
    ("tochka-hoda", "Диагностика без догадок", 'data-widget="service-booking"'),
    ("dentalea", "План лечения до начала работ", 'data-widget="doctor-schedule"'),
    ("ventkontur", "Подбор по расходу воздуха", 'data-widget="equipment-filter"'),
    ("syr-hleb", "Соберите подарочный набор", 'data-widget="gift-builder"'),
    ("kvadrat-remonta", "Смета по этапам", 'data-widget="estimate-table"'),
)

LEADGEN_CASES = (
    ("okna-sfera", "Рассчитайте окно по вашим размерам", 'data-widget="window-calculator"'),
    ("chistiy-metr", "Квартира готова к заселению", 'data-widget="cleaning-calculator"'),
    ("teplodom", "Вернём тепло в день обращения", 'data-widget="service-request"'),
    ("pereezd-prosto", "Переезд без потерянных коробок", 'data-widget="moving-calculator"'),
    ("pravo-opora", "Оценим перспективу спора", 'data-widget="case-assessment"'),
)


@pytest.mark.parametrize(("slug", "required_copy", "functional_marker"), COMMERCIAL_CASES)
def test_commercial_sites_have_unique_value_and_function(slug, required_copy, functional_marker):
    project = get_project(slug)
    html = render_commercial(project, project.shots[2], {"hero": "/asset.webp"})
    assert required_copy in html
    assert functional_marker in html


@pytest.mark.parametrize("slug", [case[0] for case in COMMERCIAL_CASES])
def test_commercial_sites_render_all_four_shot_variants(slug):
    project = get_project(slug)

    rendered = [render_commercial(project, shot, {"hero": "/asset.webp"}) for shot in project.shots]

    assert len(set(rendered)) == 4
    for shot, html in zip(project.shots, rendered):
        assert f'data-variant="{shot.variant}"' in html
        assert f'class="commercial-page {project.palette} ' in html


def test_commercial_sites_expose_five_distinct_layout_signatures():
    assert COMMERCIAL_LAYOUTS == {
        "tochka-hoda": ("split-diagnostic", "service-timeline", "service-booking"),
        "dentalea": ("calm-editorial", "treatment-detail", "doctor-schedule"),
        "ventkontur": ("technical-index", "catalog-table", "equipment-filter"),
        "syr-hleb": ("product-led", "collection-grid", "gift-builder"),
        "kvadrat-remonta": ("project-gallery", "case-study", "estimate-table"),
    }

    cover_layouts = []
    for slug in COMMERCIAL_LAYOUTS:
        project = get_project(slug)
        html = render_commercial(project, project.shots[0], {"hero": "/asset.webp"})
        cover_layouts.append(COMMERCIAL_LAYOUTS[slug][0])
        assert f'data-layout="{COMMERCIAL_LAYOUTS[slug][0]}"' in html

    assert len(set(cover_layouts)) == 5


@pytest.mark.parametrize("slug", [case[0] for case in COMMERCIAL_CASES])
def test_commercial_images_are_fixed_ratio_accessible_and_escaped(slug):
    project = get_project(slug)
    html = render_commercial(project, project.shots[0], {"hero": '/asset.webp?x=1&y="bad"'})

    assert '<img class="commercial-hero-image"' in html
    assert 'style="aspect-ratio: 16 / 10;"' in html
    assert 'alt="' in html
    assert 'src="/asset.webp?x=1&amp;y=&quot;bad&quot;"' in html


def test_commercial_renderer_rejects_unsupported_projects_and_variants():
    non_commercial = get_project("okna-sfera")
    with pytest.raises(KeyError, match="commercial project"):
        render_commercial(non_commercial, non_commercial.shots[0], {"hero": "/asset.webp"})

    project = get_project("tochka-hoda")
    unknown_shot = type(project.shots[0])("unknown", "/", "desktop", "unknown")
    with pytest.raises(ValueError, match="commercial shot variant"):
        render_commercial(project, unknown_shot, {"hero": "/asset.webp"})


@pytest.mark.parametrize(("slug", "required_copy", "functional_marker"), LEADGEN_CASES)
def test_leadgen_sites_solve_one_clear_customer_problem(slug, required_copy, functional_marker):
    project = get_project(slug)
    html = render_leadgen(project, project.shots[2], {"hero": "/asset.webp"})

    assert required_copy in html
    assert functional_marker in html


@pytest.mark.parametrize("slug", [case[0] for case in LEADGEN_CASES])
def test_leadgen_sites_render_four_distinct_shot_variants(slug):
    project = get_project(slug)

    rendered = [render_leadgen(project, shot, {"hero": "/asset.webp"}) for shot in project.shots]

    assert len(set(rendered)) == 4
    for shot, html in zip(project.shots, rendered):
        assert f'data-variant="{shot.variant}"' in html
        assert f'class="leadgen-page {project.palette} ' in html


def test_leadgen_sites_expose_five_distinct_layout_signatures():
    assert LEADGEN_LAYOUTS == {
        "okna-sfera": ("measurement-workbench", "glazing-guide", "window-calculator"),
        "chistiy-metr": ("before-after-proof", "cleaning-checklist", "cleaning-calculator"),
        "teplodom": ("urgent-service-board", "repair-route", "service-request"),
        "pereezd-prosto": ("moving-day-map", "packing-plan", "moving-calculator"),
        "pravo-opora": ("legal-editorial", "claim-roadmap", "case-assessment"),
    }

    cover_layouts = []
    for slug, layouts in LEADGEN_LAYOUTS.items():
        project = get_project(slug)
        html = render_leadgen(project, project.shots[0], {"hero": "/asset.webp"})
        cover_layouts.append(layouts[0])
        assert f'data-layout="{layouts[0]}"' in html

    assert len(set(cover_layouts)) == 5


def test_leadgen_function_views_follow_declared_flows_with_completed_controls():
    assert LEADGEN_FLOWS == {
        "okna-sfera": ("Размеры", "Профиль", "Монтаж", "Получить расчёт"),
        "chistiy-metr": ("Площадь", "Состояние", "Дополнительные зоны", "Узнать стоимость"),
        "teplodom": ("Марка котла", "Симптом", "Адрес", "Вызвать мастера"),
        "pereezd-prosto": ("Откуда", "Куда", "Объём вещей", "Рассчитать переезд"),
        "pravo-opora": ("Тип договора", "Срок просрочки", "Сумма", "Получить оценку"),
    }

    for slug, flow in LEADGEN_FLOWS.items():
        project = get_project(slug)
        html = render_leadgen(project, project.shots[2], {"hero": "/asset.webp"})
        for label in flow:
            assert label in html
        assert '<form ' in html
        assert 'type="number"' in html
        assert 'type="checkbox"' in html
        assert " checked" in html
        assert 'type="submit"' in html


@pytest.mark.parametrize("slug", [case[0] for case in LEADGEN_CASES])
def test_leadgen_images_are_fixed_ratio_accessible_and_escaped(slug):
    project = get_project(slug)
    html = render_leadgen(project, project.shots[0], {"hero": '/asset.webp?x=1&y="bad"'})

    assert '<img class="leadgen-hero-image"' in html
    assert 'style="aspect-ratio: 16 / 10;"' in html
    assert 'alt="' in html
    assert 'src="/asset.webp?x=1&amp;y=&quot;bad&quot;"' in html


def test_leadgen_renderer_rejects_unsupported_projects_variants_and_missing_assets():
    non_leadgen = get_project("tochka-hoda")
    with pytest.raises(KeyError, match="lead-generation project"):
        render_leadgen(non_leadgen, non_leadgen.shots[0], {"hero": "/asset.webp"})

    project = get_project("okna-sfera")
    unknown_shot = type(project.shots[0])("unknown", "/", "desktop", "unknown")
    with pytest.raises(ValueError, match="lead-generation shot variant"):
        render_leadgen(project, unknown_shot, {"hero": "/asset.webp"})
    with pytest.raises(KeyError, match="Missing hero asset"):
        render_leadgen(project, project.shots[0], {})
