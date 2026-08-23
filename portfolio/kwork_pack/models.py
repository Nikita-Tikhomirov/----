from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class ShotSpec:
    key: str
    path: str
    layout: Literal["desktop"]
    # TODO(Task 3): remove this temporary legacy renderer dispatch field.
    variant: Literal["cover", "content", "function"]

    @property
    def public_path(self) -> str:
        """Return the legacy browser-shell route alias until Task 3."""
        # TODO(Task 3): migrate browser-shell callers to ``path`` and remove this.
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
