from functools import lru_cache
from pathlib import Path

from .catalog import public_url
from .components import browser_toolbar, escape_html, panel
from .models import ProjectSpec, ShotSpec


_STATIC_DIR = Path(__file__).with_name("static")


@lru_cache(maxsize=None)
def _static_css(name: str) -> str:
    return (_STATIC_DIR / name).read_text(encoding="utf-8")


def render_browser_shell(project: ProjectSpec, shot: ShotSpec, page_html: str) -> str:
    url = public_url(project, shot)
    content = (
        f"{browser_toolbar(url)}"
        f'<div class="browser-viewport">{page_html}</div>'
    )
    return panel(
        "section",
        content,
        class_name="browser-window",
        attrs={
            "data-layout": "desktop",
            "data-brand": project.brand,
        },
    )


def render_mobile_shell(project: ProjectSpec, shot: ShotSpec, page_html: str) -> str:
    url = public_url(project, shot)
    mobile_shell = (
        f"{browser_toolbar(url, mobile=True)}"
        f'<div class="mobile-viewport">{page_html}</div>'
    )
    return panel(
        "section",
        panel(
            "div",
            mobile_shell,
            class_name="mobile-device",
            attrs={"data-layout": "mobile"},
        ),
        class_name="mobile-stage",
    )


def build_document(project: ProjectSpec, shot: ShotSpec, page_html: str, css_text: str) -> str:
    shell_html = (
        render_mobile_shell(project, shot, page_html)
        if shot.layout == "mobile"
        else render_browser_shell(project, shot, page_html)
    )
    title = f"{project.brand} - {shot.key}"
    style_text = "\n".join(
        part for part in (_static_css("base.css"), _static_css("themes.css"), css_text) if part
    )
    body = (
        f'<div class="portfolio-document" data-brand="{escape_html(project.brand)}">'
        f'<div class="portfolio-canvas" data-canvas="1920x1280">{shell_html}</div>'
        "</div>"
    )
    return (
        "<!DOCTYPE html>"
        '<html lang="ru">'
        "<head>"
        '<meta charset="utf-8" />'
        '<meta name="viewport" content="width=1920, initial-scale=1" />'
        f"<title>{escape_html(title)}</title>"
        f"<style>{style_text}</style>"
        "</head>"
        f'<body data-layout="{escape_html(shot.layout)}" '
        f'data-palette="{escape_html(project.palette)}" data-shot="{escape_html(shot.key)}">'
        f"{body}"
        "</body>"
        "</html>"
    )
