from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class ShotSpec:
    key: str
    path: str
    layout: Literal["desktop", "mobile"]
    variant: str

    @property
    def public_path(self) -> str:
        """Return the route name used by the existing browser-shell API."""
        return self.path


@dataclass(frozen=True)
class AssetSpec:
    key: str
    filename: str
    prompt: str


@dataclass(frozen=True)
class ProjectSpec:
    slug: str
    brand: str
    kwork_title: str
    group: str
    domain: str
    category: tuple[str, str]
    work_type: str
    description: str
    palette: str
    renderer_module: str
    shots: tuple[ShotSpec, ...]
    assets: tuple[AssetSpec, ...]
