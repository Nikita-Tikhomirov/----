import re

from portfolio.kwork_pack.catalog import get_project
from portfolio.kwork_pack.sites.complex import render_complex


def test_lakeside_photo_caption_has_a_readable_backdrop():
    project = get_project("doma-u-ozera")

    html = render_complex(project, project.shots[0], {"hero": "/hero.png"})
    caption_rule = html.split(".lake-media .lake-caption", 1)[1].split("}", 1)[0]

    assert "background:" in caption_rule
    assert "padding:" in caption_rule


def test_praktika_lesson_menu_stacks_navigation_links():
    project = get_project("praktika")

    html = render_complex(project, project.shots[2], {"hero": "/hero.png"})
    css = html.split("<style>", 1)[1].split("</style>", 1)[0]

    assert re.search(r"\.lesson-menu\s*\{[^}]*display:\s*grid", css)
