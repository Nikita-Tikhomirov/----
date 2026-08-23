"""Code-native site renderers for the Kwork portfolio pack."""

from collections.abc import Mapping

from ..models import ProjectSpec, ShotSpec
from .commercial import COMMERCIAL_LAYOUTS, render_commercial
from .complex import COMPLEX_LAYOUTS, render_complex
from .leadgen import LEADGEN_LAYOUTS, render_leadgen


_RENDERERS = {
    "Коммерческие сайты": render_commercial,
    "Лидогенерирующие лендинги": render_leadgen,
    "Проекты посложнее": render_complex,
}


def _legacy_asset_mapping(
    project: ProjectSpec, assets: Mapping[str, str]
) -> dict[str, str]:
    """Provide the semantic inventory to the pre-Task 3 renderer interface."""
    legacy_assets = dict(assets)
    if "hero" not in legacy_assets:
        # TODO(Task 3): remove this adapter with the legacy group renderers.
        first_asset = project.assets[0]
        legacy_assets["hero"] = legacy_assets[first_asset.key]
    return legacy_assets


def render_site(
    project: ProjectSpec, shot: ShotSpec, assets: dict[str, str]
) -> str:
    """Dispatch a catalog project through the temporary legacy renderer boundary."""
    try:
        renderer = _RENDERERS[project.group]
    except KeyError as exc:
        raise KeyError(f"Unknown portfolio project group: {project.group}") from exc
    return renderer(project, shot, _legacy_asset_mapping(project, assets))


__all__ = [
    "COMMERCIAL_LAYOUTS",
    "COMPLEX_LAYOUTS",
    "LEADGEN_LAYOUTS",
    "render_commercial",
    "render_complex",
    "render_leadgen",
    "render_site",
]
