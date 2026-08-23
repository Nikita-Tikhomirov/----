"""Contracts shared by portfolio site renderers."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass

from ..models import ProjectSpec, ShotSpec


@dataclass(frozen=True)
class RenderedPage:
    """Project-owned page source consumed by the shared browser shell."""

    html: str
    css: str
    scripts: str = ""


SiteRenderer = Callable[[ProjectSpec, ShotSpec, Mapping[str, str]], RenderedPage]
