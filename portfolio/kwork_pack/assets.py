from collections.abc import Iterable
from pathlib import Path

from .models import AssetSpec, ProjectSpec


def asset_path(root: Path, project: ProjectSpec, asset: AssetSpec) -> Path:
    """Return the canonical local path for a project's bitmap asset."""
    return root / "assets" / project.slug / asset.filename


def resolve_project_assets(root: Path, project: ProjectSpec) -> dict[str, str]:
    """Resolve every required project asset to an absolute file URI."""
    resolved: dict[str, str] = {}
    for asset in project.assets:
        path = asset_path(root, project, asset)
        if not path.is_file():
            raise FileNotFoundError(f"Required portfolio asset is missing: {path}")
        resolved[asset.key] = path.resolve().as_uri()
    return resolved


def missing_assets(
    root: Path,
    projects: Iterable[ProjectSpec],
) -> tuple[Path, ...]:
    """Return required bitmap paths that are not regular files."""
    return tuple(
        path
        for project in projects
        for asset in project.assets
        if not (path := asset_path(root, project, asset)).is_file()
    )
