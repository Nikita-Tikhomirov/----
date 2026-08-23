from pathlib import Path

from PIL import Image, ImageDraw

from portfolio.kwork_pack.catalog import PROJECTS
from portfolio.kwork_pack.quality import (
    bottom_band_metrics,
    validate_asset_uniqueness,
    validate_unique_paths,
)


def _write_visual(path: Path, seed: int, *, size: tuple[int, int] = (1920, 1280)) -> None:
    """Write a deterministic, content-bearing fixture with a distinct layout."""
    image = Image.new("RGB", size, (28 + seed * 7 % 100, 42, 58))
    draw = ImageDraw.Draw(image)
    width, height = size
    header = height // 7
    draw.rectangle((0, 0, width, header), fill=(242, 244, 247))
    draw.rectangle((width // 18, header // 3, width // 4, header * 2 // 3), fill=(20, 30, 42))
    draw.rectangle((width * 3 // 4, header // 3, width * 17 // 18, header * 2 // 3), fill=(seed * 29 % 200, 96, 70))

    card_width = width // 5
    for index in range(8):
        column = (index * 3 + seed) % 4
        row = index // 4
        left = width // 14 + column * (card_width + width // 40)
        top = height // 4 + row * (height // 6)
        right = left + card_width
        bottom = top + height // 8
        draw.rectangle((left, top, right, bottom), fill=(70 + (seed + index) * 19 % 140, 115, 150))
        draw.rectangle((left + 24, top + 22, right - 32, top + 36), fill=(246, 246, 240))
        draw.rectangle((left + 24, top + 56, left + card_width // 2, bottom - 22), fill=(190, 212, 224))

    lower_top = height * 3 // 4
    for column in range(17):
        left = column * width // 17
        right = (column + 1) * width // 17
        tone = 35 if (seed >> (column % 8)) & 1 else 220
        draw.rectangle((left, lower_top, right, height), fill=(tone, 80 + column * 7 % 120, 150 - column * 5 % 90))
    for row in range(lower_top, height, max(8, height // 32)):
        draw.rectangle((0, row, width, row + max(2, height // 160)), fill=(244, 244, 244))
    image.save(path)


def _write_hash_neighbor(path: Path, changed_cell: int | None = None) -> None:
    image = Image.new("L", (17, 16), 32)
    pixels = image.load()
    for y in range(16):
        for x in range(17):
            pixels[x, y] = 224 if (x + y * 3) % 5 < 2 else 24
    if changed_cell is not None:
        x, y = divmod(changed_cell, 16)
        pixels[x, y] = 24 if pixels[x, y] == 224 else 224
    image.resize((340, 320), Image.Resampling.NEAREST).convert("RGB").save(path)


def test_exact_duplicate_assets_are_rejected_with_both_paths(tmp_path):
    first = tmp_path / "first.png"
    second = tmp_path / "second.png"
    _write_hash_neighbor(first)
    second.write_bytes(first.read_bytes())

    issues = validate_unique_paths((first, second), min_distance=10)

    assert len(issues) == 1
    assert issues[0].code == "duplicate-asset"
    assert "first.png" in issues[0].message
    assert "second.png" in issues[0].message


def test_near_duplicate_assets_below_supplied_hamming_threshold_are_rejected(tmp_path):
    first = tmp_path / "first.png"
    second = tmp_path / "second.png"
    _write_hash_neighbor(first)
    _write_hash_neighbor(second, changed_cell=9)

    issues = validate_unique_paths((first, second), min_distance=10)

    assert len(issues) == 1
    assert issues[0].code == "near-duplicate-asset"
    assert "Hamming distance" in issues[0].message


def test_declared_duplicate_assets_are_rejected_from_the_asset_root(tmp_path):
    project = PROJECTS[0]
    first = tmp_path / "assets" / project.slug / project.assets[0].filename
    second = tmp_path / "assets" / project.slug / project.assets[1].filename
    first.parent.mkdir(parents=True)
    _write_hash_neighbor(first)
    second.write_bytes(first.read_bytes())

    issues = validate_asset_uniqueness(tmp_path, (project,))

    assert len(issues) == 1
    assert issues[0].code == "duplicate-asset"
    assert first.name in issues[0].message
    assert second.name in issues[0].message


def test_empty_lower_viewport_is_rejected_by_both_metrics(tmp_path):
    path = tmp_path / "blank-bottom.png"
    image = Image.new("RGB", (1920, 1280), "white")
    ImageDraw.Draw(image).rectangle((0, 0, 1919, 700), fill="#222222")
    image.save(path)

    variance, edge_density = bottom_band_metrics(path)

    assert variance < 25
    assert edge_density < 0.005


def test_content_bearing_lower_viewport_passes_both_metrics(tmp_path):
    path = tmp_path / "content-bottom.png"
    _write_visual(path, 3)

    variance, edge_density = bottom_band_metrics(path)

    assert variance >= 40
    assert edge_density >= 0.003
