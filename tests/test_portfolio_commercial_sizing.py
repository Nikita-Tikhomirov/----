import re

import pytest

from portfolio.kwork_pack.catalog import get_project
from portfolio.kwork_pack.sites.commercial import render_commercial


COMMERCIAL_SLUGS = (
    "tochka-hoda",
    "dentalea",
    "ventkontur",
    "syr-hleb",
    "kvadrat-remonta",
)

_STYLE_PATTERN = re.compile(r"<style>(?P<css>.*?)</style>", re.DOTALL)
_RULE_PATTERN = re.compile(r"(?P<selector>[^{}]+)\{(?P<declarations>[^{}]*)\}")
_FIXED_HEIGHT_PATTERN = re.compile(
    r"(?<![-\w])height\s*:\s*\d+(?:\.\d+)?(?:px|rem|em|vh|vw|vmin|vmax|pt)\b",
    re.IGNORECASE,
)


def _fixed_image_height_rules(css: str) -> list[str]:
    conflicts = []
    for rule in _RULE_PATTERN.finditer(css):
        selector = rule.group("selector").strip()
        targets_image_slot = "img" in selector or ".commercial-image-slot" in selector
        if targets_image_slot and _FIXED_HEIGHT_PATTERN.search(rule.group("declarations")):
            conflicts.append(selector)
    return conflicts


@pytest.mark.parametrize("slug", COMMERCIAL_SLUGS)
def test_commercial_image_slots_keep_ratio_without_fixed_height_overrides(slug):
    project = get_project(slug)
    rendered = [
        render_commercial(project, shot, {"hero": "/asset.webp"})
        for shot in project.shots
    ]

    css = _STYLE_PATTERN.search(rendered[0]).group("css")
    assert _fixed_image_height_rules(css) == []
    assert ".commercial-image-slot" in css
    assert "aspect-ratio: 16 / 10" in css
    assert "overflow: hidden" in css

    for html in rendered:
        slot_count = html.count('class="commercial-image-slot"')
        image_count = html.count('class="commercial-hero-image"')
        assert slot_count == image_count
        assert slot_count > 0
        assert '<figure class="commercial-image-slot" style="aspect-ratio: 16 / 10;">' in html
