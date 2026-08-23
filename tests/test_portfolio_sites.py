import pytest

from portfolio.kwork_pack.catalog import get_project
from portfolio.kwork_pack.sites.commercial import COMMERCIAL_LAYOUTS, render_commercial


COMMERCIAL_CASES = (
    ("tochka-hoda", "Диагностика без догадок", 'data-widget="service-booking"'),
    ("dentalea", "План лечения до начала работ", 'data-widget="doctor-schedule"'),
    ("ventkontur", "Подбор по расходу воздуха", 'data-widget="equipment-filter"'),
    ("syr-hleb", "Соберите подарочный набор", 'data-widget="gift-builder"'),
    ("kvadrat-remonta", "Смета по этапам", 'data-widget="estimate-table"'),
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
