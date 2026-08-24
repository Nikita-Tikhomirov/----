"""Code-native site renderers for the Kwork portfolio pack."""

from collections.abc import Mapping
from importlib import import_module
from types import ModuleType
from typing import cast

from ..models import ProjectSpec, ShotSpec
from .runtime import RenderedPage, SiteRenderer


_LEGACY_RENDERERS = {
    "Коммерческие сайты": (
        "portfolio.kwork_pack.sites.commercial",
        "render_commercial",
    ),
    "Лидогенерирующие лендинги": (
        "portfolio.kwork_pack.sites.leadgen",
        "render_leadgen",
    ),
    "Проекты посложнее": (
        "portfolio.kwork_pack.sites.complex",
        "render_complex",
    ),
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


def get_renderer_module(project: ProjectSpec) -> ModuleType:
    """Import and validate the renderer module declared by one project."""
    module = import_module(project.renderer_module)
    expected_name = project.slug.replace("-", "_")
    actual_name = module.__name__.rsplit(".", 1)[-1]
    if actual_name != expected_name:
        raise ValueError(
            f"Project {project.slug} declares renderer module "
            f"{project.renderer_module}, but imported {module.__name__}; "
            f"expected final module name {expected_name}"
        )
    return module


def get_renderer(project: ProjectSpec) -> SiteRenderer:
    """Return the callable dedicated renderer declared by one project."""
    module = get_renderer_module(project)
    renderer = getattr(module, "render", None)
    if not callable(renderer):
        raise TypeError(
            f"Project {project.slug} renderer module {project.renderer_module} "
            "must define a callable render"
        )
    return cast(SiteRenderer, renderer)


def _render_legacy_site(
    project: ProjectSpec, shot: ShotSpec, assets: Mapping[str, str]
) -> RenderedPage:
    """Keep pre-migration projects renderable until Task 8 removes this path."""
    try:
        module_name, renderer_name = _LEGACY_RENDERERS[project.group]
    except KeyError as exc:
        raise KeyError(f"Unknown portfolio project group: {project.group}") from exc
    renderer = getattr(import_module(module_name), renderer_name)
    html = renderer(project, shot, _legacy_asset_mapping(project, assets))
    return RenderedPage(html=html, css="")


def render_site(
    project: ProjectSpec, shot: ShotSpec, assets: Mapping[str, str]
) -> RenderedPage:
    """Render a dedicated module or the temporary exact-module migration fallback."""
    try:
        renderer = get_renderer(project)
    except ModuleNotFoundError as exc:
        if exc.name != project.renderer_module:
            raise
        return _render_legacy_site(project, shot, assets)
    page = renderer(project, shot, assets)
    if not isinstance(page, RenderedPage):
        raise TypeError(
            f"Project {project.slug} renderer module {project.renderer_module} "
            f"must return RenderedPage, got {type(page).__name__}"
        )
    return page


__all__ = [
    "RenderedPage",
    "SiteRenderer",
    "get_renderer",
    "get_renderer_module",
    "render_site",
]
