from collections.abc import Mapping
from html import escape

from .icons import icon


def escape_html(value: str) -> str:
    return escape(value, quote=True)


def _attrs(values: Mapping[str, str]) -> str:
    return "".join(
        f' {key}="{escape_html(value)}"'
        for key, value in values.items()
        if value != ""
    )


def window_controls() -> str:
    return (
        '<div class="window-controls" aria-hidden="true">'
        '<span class="window-dot window-dot-red"></span>'
        '<span class="window-dot window-dot-amber"></span>'
        '<span class="window-dot window-dot-green"></span>'
        "</div>"
    )


def browser_url_bar(url: str, *, mobile: bool = False) -> str:
    class_name = "mobile-url-bar" if mobile else "browser-url-bar"
    return (
        f'<div class="{class_name}">'
        f'{icon("lock", size=16)}'
        f'<span class="browser-url-text">{escape_html(url)}</span>'
        "</div>"
    )


def browser_toolbar(url: str, *, mobile: bool = False) -> str:
    if mobile:
        return (
            '<div class="mobile-browser-top">'
            '<div class="mobile-notch" aria-hidden="true"></div>'
            f'{browser_url_bar(url, mobile=True)}'
            "</div>"
        )

    return (
        '<header class="browser-toolbar">'
        f"{window_controls()}"
        '<div class="browser-toolbar-center">'
        f'{browser_url_bar(url)}'
        "</div>"
        "</header>"
    )


def panel(tag: str, content: str, *, class_name: str, attrs: Mapping[str, str] | None = None) -> str:
    attr_text = _attrs(attrs or {})
    return f'<{tag} class="{class_name}"{attr_text}>{content}</{tag}>'
