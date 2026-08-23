"""Deterministic visual quality gates for portfolio bitmap files."""

from collections.abc import Iterable
from dataclasses import dataclass
import hashlib
from itertools import combinations
from pathlib import Path

from PIL import Image, ImageChops, ImageStat, UnidentifiedImageError

from .assets import asset_path
from .models import ProjectSpec


@dataclass(frozen=True)
class ValidationIssue:
    project_slug: str
    file: str
    message: str
    code: str = ""


def dhash(path: Path, size: int = 16) -> int:
    """Return horizontal and vertical grayscale difference hashes for a bitmap."""
    with Image.open(path) as image:
        grayscale = image.convert("L").resize(
            (size + 1, size + 1), Image.Resampling.LANCZOS
        )
        pixels = list(grayscale.getdata())

    value = 0
    row_width = size + 1
    for row in range(size):
        offset = row * row_width
        for column in range(size):
            value = (value << 1) | int(
                pixels[offset + column] > pixels[offset + column + 1]
            )
    for row in range(size):
        offset = row * row_width
        for column in range(size):
            value = (value << 1) | int(
                pixels[offset + column] > pixels[offset + column + row_width]
            )
    return value


def hamming_distance(left: int, right: int) -> int:
    """Return the number of different bits in two image hashes."""
    return (left ^ right).bit_count()


def bottom_band_metrics(path: Path) -> tuple[float, float]:
    """Return grayscale variance and adjacent-pixel edge density below 75%."""
    lower_band = _lower_band(path)
    variance = ImageStat.Stat(lower_band).var[0]
    return variance, _edge_density(lower_band)


def bottom_band_content_coverage(path: Path) -> float:
    """Return the fraction of lower-band tiles containing distributed detail."""
    lower_band = _lower_band(path)
    columns, rows = 12, 8
    active_tiles = 0
    for row in range(rows):
        top = row * lower_band.height // rows
        bottom = (row + 1) * lower_band.height // rows
        for column in range(columns):
            left = column * lower_band.width // columns
            right = (column + 1) * lower_band.width // columns
            tile = lower_band.crop((left, top, right, bottom))
            variance = ImageStat.Stat(tile).var[0]
            if variance >= 40 and _edge_density(tile) >= 0.006:
                active_tiles += 1
    return active_tiles / (columns * rows)


def layout_structure_distance(left: Path, right: Path) -> int:
    """Compare coarse UI structure while treating high-entropy tiles as photos."""
    left_fingerprint = _layout_fingerprint(left)
    right_fingerprint = _layout_fingerprint(right)
    return _fingerprint_distance(left_fingerprint, right_fingerprint)


def _lower_band(path: Path) -> Image.Image:
    with Image.open(path) as image:
        grayscale = image.convert("L")
        width, height = grayscale.size
        return grayscale.crop((0, height * 3 // 4, width, height))


def _edge_density(image: Image.Image) -> float:
    width, height = image.size
    if width < 2 or height < 2:
        return 0.0
    horizontal = ImageChops.difference(
        image.crop((1, 0, width, height)),
        image.crop((0, 0, width - 1, height)),
    )
    vertical = ImageChops.difference(
        image.crop((0, 1, width, height)),
        image.crop((0, 0, width, height - 1)),
    )
    edge_pixels = sum(horizontal.histogram()[16:]) + sum(vertical.histogram()[16:])
    adjacent_pixels = (width - 1) * height + width * (height - 1)
    return edge_pixels / adjacent_pixels


def _layout_fingerprint(path: Path) -> tuple[int, ...]:
    with Image.open(path) as image:
        grayscale = image.convert("L").resize((384, 256), Image.Resampling.BILINEAR)

    fingerprint: list[int] = []
    columns, rows = 12, 8
    for row in range(rows):
        top = row * grayscale.height // rows
        bottom = (row + 1) * grayscale.height // rows
        for column in range(columns):
            left = column * grayscale.width // columns
            right = (column + 1) * grayscale.width // columns
            tile = grayscale.crop((left, top, right, bottom))
            variance = ImageStat.Stat(tile).var[0]
            edge_density = _edge_density(tile)
            if variance >= 800:
                fingerprint.append(3)
            elif edge_density >= 0.08:
                fingerprint.append(2)
            elif edge_density >= 0.015:
                fingerprint.append(1)
            else:
                fingerprint.append(0)
    return tuple(fingerprint)


def _fingerprint_distance(left: tuple[int, ...], right: tuple[int, ...]) -> int:
    return sum(first != second for first, second in zip(left, right))


def validate_unique_paths(
    paths: Iterable[Path], *, min_distance: int
) -> tuple[ValidationIssue, ...]:
    """Reject exact and perceptually similar bitmap files as portfolio assets."""
    candidates = tuple(sorted((Path(path) for path in paths), key=_sort_key))
    display_paths = {path: path.as_posix() for path in candidates}
    return _uniqueness_issues(
        candidates,
        min_distance=min_distance,
        item_kind="asset",
        display_paths=display_paths,
        project_slugs={},
    )


def validate_asset_uniqueness(
    root: Path, projects: Iterable[ProjectSpec]
) -> tuple[ValidationIssue, ...]:
    """Reject duplicate declared assets that exist in the portfolio asset root."""
    candidates: list[Path] = []
    display_paths: dict[Path, str] = {}
    project_slugs: dict[Path, str] = {}
    declarations: dict[Path, list[str]] = {}
    for project in projects:
        for asset in project.assets:
            path = asset_path(root, project, asset)
            if not path.is_file():
                continue
            declarations.setdefault(path, []).append(asset.key)
            display_paths[path] = path.relative_to(root).as_posix()
            project_slugs[path] = project.slug
    declaration_issues: list[ValidationIssue] = []
    for path in sorted(declarations, key=_sort_key):
        keys = declarations[path]
        candidates.append(path)
        for left_key, right_key in combinations(keys, 2):
            declaration_issues.append(
                ValidationIssue(
                    project_slugs[path],
                    display_paths[path],
                    "duplicate asset declaration for "
                    f"{display_paths[path]}: {left_key} and {right_key}",
                    "duplicate-asset",
                )
            )
    return tuple(declaration_issues) + _uniqueness_issues(
        candidates,
        min_distance=12,
        item_kind="asset",
        display_paths=display_paths,
        project_slugs=project_slugs,
    )


def validate_cross_project_screenshot_uniqueness(
    screenshots: Iterable[tuple[ProjectSpec, Path]],
    *,
    min_distance: int,
    root: Path | None = None,
) -> tuple[ValidationIssue, ...]:
    """Reject similar final screenshots only when they belong to different projects."""
    entries = tuple(screenshots)
    paths = tuple(path for _, path in entries)
    display_paths = {
        path: _display_path(path, root)
        for path in paths
    }
    project_slugs = {path: project.slug for project, path in entries}
    return _uniqueness_issues(
        paths,
        min_distance=min_distance,
        item_kind="screenshot",
        display_paths=display_paths,
        project_slugs=project_slugs,
        cross_project_only=True,
        layout_distance=8,
    )


def _uniqueness_issues(
    paths: Iterable[Path],
    *,
    min_distance: int,
    item_kind: str,
    display_paths: dict[Path, str],
    project_slugs: dict[Path, str],
    cross_project_only: bool = False,
    layout_distance: int | None = None,
) -> tuple[ValidationIssue, ...]:
    candidates = tuple(sorted({Path(path) for path in paths if Path(path).is_file()}, key=_sort_key))
    issues: list[ValidationIssue] = []
    perceptual_hashes: dict[Path, int] = {}
    for path in candidates:
        try:
            perceptual_hashes[path] = dhash(path)
        except (OSError, UnidentifiedImageError, ValueError):
            issues.append(
                ValidationIssue(
                    project_slugs.get(path, ""),
                    display_paths[path],
                    f"invalid {item_kind} image",
                    f"invalid-{item_kind}",
                )
            )
    candidates = tuple(path for path in candidates if path in perceptual_hashes)
    hashes = {path: _sha256(path) for path in candidates}
    exact_pairs: set[tuple[Path, Path]] = set()

    for left, right in combinations(candidates, 2):
        if cross_project_only and project_slugs[left] == project_slugs[right]:
            continue
        if hashes[left] != hashes[right]:
            continue
        exact_pairs.add((left, right))
        issues.append(
            _duplicate_issue(
                left,
                right,
                item_kind=item_kind,
                exact=True,
                distance=0,
                display_paths=display_paths,
                project_slugs=project_slugs,
            )
        )

    layout_fingerprints = (
        {path: _layout_fingerprint(path) for path in candidates}
        if layout_distance is not None
        else {}
    )
    for left, right in combinations(candidates, 2):
        if (left, right) in exact_pairs:
            continue
        if cross_project_only and project_slugs[left] == project_slugs[right]:
            continue
        distance = hamming_distance(perceptual_hashes[left], perceptual_hashes[right])
        if distance < min_distance:
            issues.append(
                _duplicate_issue(
                    left,
                    right,
                    item_kind=item_kind,
                    exact=False,
                    distance=distance,
                    comparison="Hamming distance",
                    display_paths=display_paths,
                    project_slugs=project_slugs,
                )
            )
            continue
        if layout_distance is None:
            continue
        structure_distance = _fingerprint_distance(
            layout_fingerprints[left], layout_fingerprints[right]
        )
        if structure_distance <= layout_distance:
            issues.append(
                _duplicate_issue(
                    left,
                    right,
                    item_kind=item_kind,
                    exact=False,
                    distance=structure_distance,
                    comparison="layout distance",
                    display_paths=display_paths,
                    project_slugs=project_slugs,
                )
            )
    return tuple(issues)


def _duplicate_issue(
    left: Path,
    right: Path,
    *,
    item_kind: str,
    exact: bool,
    distance: int,
    comparison: str = "Hamming distance",
    display_paths: dict[Path, str],
    project_slugs: dict[Path, str],
) -> ValidationIssue:
    left_display = display_paths[left]
    right_display = display_paths[right]
    qualifier = "duplicate" if exact else "near-duplicate"
    code = f"{qualifier}-{item_kind}"
    if exact:
        message = f"exact duplicate {item_kind}: {left_display} and {right_display}"
    else:
        message = (
            f"near-duplicate {item_kind} ({comparison} {distance}): "
            f"{left_display} and {right_display}"
        )
    return ValidationIssue(
        project_slugs.get(left, ""), left_display, message, code
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _sort_key(path: Path) -> tuple[str, str]:
    rendered = path.as_posix()
    return rendered.casefold(), rendered


def _display_path(path: Path, root: Path | None) -> str:
    if root is None:
        return path.as_posix()
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()
