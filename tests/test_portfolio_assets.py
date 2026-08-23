import pytest

from portfolio.kwork_pack.assets import (
    asset_path,
    missing_assets,
    resolve_project_assets,
)
from portfolio.kwork_pack.catalog import PROJECTS
from portfolio.kwork_pack.models import AssetSpec


def test_asset_path_uses_canonical_project_asset_location(tmp_path):
    project = PROJECTS[0]

    path = asset_path(tmp_path, project, project.assets[0])

    assert path == tmp_path / "assets" / "tochka-hoda" / "hero.png"


def test_asset_path_uses_declared_asset_filename(tmp_path):
    project = PROJECTS[0]
    asset = AssetSpec(
        key="hero",
        filename="custom-hero.webp",
        prompt="Text-free synthetic asset",
    )

    path = asset_path(tmp_path, project, asset)

    assert path == tmp_path / "assets" / project.slug / "custom-hero.webp"


def test_missing_assets_reports_every_expected_file(tmp_path):
    missing = missing_assets(tmp_path, PROJECTS)

    assert len(missing) == 15
    assert missing[0].name == "hero.png"


def test_resolve_project_assets_requires_generated_files(tmp_path):
    with pytest.raises(FileNotFoundError, match="hero.png"):
        resolve_project_assets(tmp_path, PROJECTS[0])


def test_resolve_project_assets_returns_absolute_file_uris(tmp_path):
    project = PROJECTS[0]
    hero_path = tmp_path / "assets" / project.slug / "hero.png"
    hero_path.parent.mkdir(parents=True)
    hero_path.write_bytes(b"generated bitmap")

    resolved = resolve_project_assets(tmp_path, project)

    assert resolved == {"hero": hero_path.resolve().as_uri()}
