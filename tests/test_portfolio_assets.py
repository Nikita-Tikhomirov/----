import re

import pytest
from PIL import Image, ImageDraw

from portfolio.kwork_pack.assets import (
    asset_path,
    missing_assets,
    resolve_project_assets,
)
from portfolio.kwork_pack.catalog import PROJECTS
from portfolio.kwork_pack.models import AssetSpec


def _write_asset_fixture(path, seed):
    image = Image.new("RGB", (64, 64), (30 + seed * 20, 60, 100))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, seed * 4, 63, seed * 4 + 8), fill=(240, 240, 240))
    draw.rectangle((seed * 5, 0, seed * 5 + 8, 63), fill=(180, 70, 60))
    image.save(path)


def test_asset_path_uses_canonical_project_asset_location(tmp_path):
    project = PROJECTS[0]

    path = asset_path(tmp_path, project, project.assets[0])

    assert path == tmp_path / "assets" / project.slug / project.assets[0].filename


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

    assert len(missing) == sum(len(project.assets) for project in PROJECTS)
    assert missing[0].name == PROJECTS[0].assets[0].filename


def test_resolve_project_assets_requires_generated_files(tmp_path):
    first_asset = PROJECTS[0].assets[0]
    with pytest.raises(FileNotFoundError, match=re.escape(first_asset.filename)):
        resolve_project_assets(tmp_path, PROJECTS[0])


def test_resolve_project_assets_returns_absolute_file_uris(tmp_path):
    project = PROJECTS[0]
    for index, declared_asset in enumerate(project.assets, start=1):
        asset = tmp_path / "assets" / project.slug / declared_asset.filename
        asset.parent.mkdir(parents=True, exist_ok=True)
        _write_asset_fixture(asset, index)

    resolved = resolve_project_assets(tmp_path, project)

    assert resolved == {
        asset.key: (
            tmp_path / "assets" / project.slug / asset.filename
        ).resolve().as_uri()
        for asset in project.assets
    }
