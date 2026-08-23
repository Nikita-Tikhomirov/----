"""Code-native site renderers for the Kwork portfolio pack."""

from ..models import ProjectSpec, ShotSpec
from .commercial import COMMERCIAL_LAYOUTS, render_commercial
from .complex import COMPLEX_LAYOUTS, render_complex
from .leadgen import LEADGEN_LAYOUTS, render_leadgen


_RENDERERS = {
    "Коммерческие сайты": render_commercial,
    "Лидогенерирующие лендинги": render_leadgen,
    "Проекты посложнее": render_complex,
}


def render_site(
    project: ProjectSpec, shot: ShotSpec, assets: dict[str, str]
) -> str:
    """Dispatch a catalog project to its code-native site renderer."""
    try:
        renderer = _RENDERERS[project.group]
    except KeyError as exc:
        raise KeyError(f"Unknown portfolio project group: {project.group}") from exc
    return renderer(project, shot, assets)


__all__ = [
    "COMMERCIAL_LAYOUTS",
    "COMPLEX_LAYOUTS",
    "LEADGEN_LAYOUTS",
    "render_commercial",
    "render_complex",
    "render_leadgen",
    "render_site",
]
