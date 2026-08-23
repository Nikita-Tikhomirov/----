import pytest

from portfolio.kwork_pack.catalog import get_project
from portfolio.kwork_pack.sites.leadgen import render_leadgen


LEADGEN_SLUGS = (
    "okna-sfera",
    "chistiy-metr",
    "teplodom",
    "pereezd-prosto",
    "pravo-opora",
)


@pytest.mark.parametrize("slug", LEADGEN_SLUGS)
def test_function_shot_has_one_primary_submit_command(slug):
    project = get_project(slug)

    html = render_leadgen(project, project.shots[2], {"hero": "/asset.webp"})
    navbar, separator, _ = html.partition("</header>")

    assert separator
    assert 'class="leadgen-button"' not in navbar
    assert html.count('class="leadgen-button"') == 1
    assert '<button class="leadgen-button" type="submit">' in html
