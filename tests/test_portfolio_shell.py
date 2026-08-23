import pytest

from portfolio.kwork_pack.catalog import get_project
from portfolio.kwork_pack.icons import icon
from portfolio.kwork_pack.models import ProjectSpec, ShotSpec
from portfolio.kwork_pack.shell import build_document


def test_desktop_document_contains_realistic_browser_url_and_canvas_contract():
    project = get_project("tochka-hoda")
    shot = project.shots[1]
    html = build_document(project, shot, '<main data-page="diagnostics">Контент</main>', "")
    assert "https://tochka-hoda.ru/uslugi/diagnostika-avtomobilya" in html
    assert 'data-canvas="1920x1280"' in html
    assert "localhost" not in html


def test_desktop_document_never_uses_a_mobile_browser_frame():
    project = get_project("doma-u-ozera")
    shot = next(item for item in project.shots if item.key == "booking")
    html = build_document(project, shot, "<main>Дом с сауной</main>", "")
    assert 'data-layout="desktop"' in html
    assert 'data-canvas="1920x1280"' in html
    assert "doma-u-ozera.ru" in html
    assert 'class="mobile-url-bar"' not in html


def test_build_document_escapes_dynamic_shell_text_values():
    shot = ShotSpec("content", "/path?<danger>", "desktop", "content")
    project = ProjectSpec(
        slug="escape-check",
        brand="Brand & <tag>",
        kwork_title="Title",
        group="Group",
        domain="example.test<evil>",
        category=("A", "B"),
        work_type="Work",
        description="Авторский концепт",
        palette="palette",
        renderer_module="portfolio.kwork_pack.sites.escape_check",
        shots=(shot,),
        assets=(),
    )

    html = build_document(project, shot, "<main>trusted</main>", "")

    assert "Brand &amp; &lt;tag&gt;" in html
    assert "https://example.test&lt;evil&gt;/path?&lt;danger&gt;" in html
    assert "Brand & <tag>" not in html
    assert "<main>trusted</main>" in html


def test_icon_raises_key_error_for_unknown_name():
    with pytest.raises(KeyError, match="unknown"):
        icon("unknown")
