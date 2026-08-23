from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class ShotSpec:
    key: str
    public_path: str
    layout: Literal["desktop", "mobile"]
    variant: str


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
    shots: tuple[ShotSpec, ...]
    assets: tuple[AssetSpec, ...]
