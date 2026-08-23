"""Deterministic visual quality gates for portfolio bitmap files."""

from collections.abc import Iterable
from dataclasses import dataclass
import hashlib
from itertools import combinations
from pathlib import Path

from PIL import Image, ImageChops, ImageStat

from .assets import asset_path
from .models import ProjectSpec


@dataclass(frozen=True)
class ValidationIssue:
    project_slug: str
    file: str
    message: str
    code: str = ""


def dhash(path: Path, size: int = 16) -> int:
    """Return a grayscale difference hash for a bitmap image."""
    with Image.open(path) as image:
        grayscale = image.convert("L").resize(
            (size + 1, size), Image.Resampling.LANCZOS
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
    return value


def hamming_distance(left: int, right: int) -> int:
    """Return the number of different bits in two image hashes."""
    return (left ^ right).bit_count()


def bottom_band_metrics(path: Path) -> tuple[float, float]:
    """Return grayscale variance and adjacent-pixel edge density below 75%."""
    with Image.open(path) as image:
        grayscale = image.convert("L")
        width, height = grayscale.size
        lower_band = grayscale.crop((0, height * 3 // 4, width, height))

    variance = ImageStat.Stat(lower_band).var[0]
    horizontal = ImageChops.difference(
        lower_band.crop((1, 0, width, lower_band.height)),
        lower_band.crop((0, 0, width - 1, lower_band.height)),
    )
    vertical = ImageChops.difference(
        lower_band.crop((0, 1, width, lower_band.height)),
        lower_band.crop((0, 0, width, lower_band.height - 1)),
    )
    edge_pixels = sum(horizontal.histogram()[16:]) + sum(vertical.histogram()[16:])
    adjacent_pixels = (width - 1) * lower_band.height + width * (
        lower_band.height - 1
    )
    return variance, edge_pixels / adjacent_pixels


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
    for project in projects:
        for asset in project.assets:
            path = asset_path(root, project, asset)
            if not path.is_file():
                continue
            candidates.append(path)
            display_paths[path] = path.relative_to(root).as_posix()
            project_slugs[path] = project.slug
    return _uniqueness_issues(
        candidates,
        min_distance=12,
        item_kind="asset",
        display_paths=display_paths,
        project_slugs=project_slugs,
    )


def validate_cross_project_screenshot_uniqueness(
    screenshots: Iterable[tuple[ProjectSpec, Path]], *, min_distance: int
) -> tuple[ValidationIssue, ...]:
    """Reject similar final screenshots only when they belong to different projects."""
    entries = tuple(screenshots)
    paths = tuple(path for _, path in entries)
    display_paths = {path: path.as_posix() for path in paths}
    project_slugs = {path: project.slug for project, path in entries}
    return _uniqueness_issues(
        paths,
        min_distance=min_distance,
        item_kind="screenshot",
        display_paths=display_paths,
        project_slugs=project_slugs,
        cross_project_only=True,
    )


def _uniqueness_issues(
    paths: Iterable[Path],
    *,
    min_distance: int,
    item_kind: str,
    display_paths: dict[Path, str],
    project_slugs: dict[Path, str],
    cross_project_only: bool = False,
) -> tuple[ValidationIssue, ...]:
    candidates = tuple(sorted(set(paths), key=_sort_key))
    hashes = {path: _sha256(path) for path in candidates}
    issues: list[ValidationIssue] = []
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

    perceptual_hashes = {path: dhash(path) for path in candidates}
    for left, right in combinations(candidates, 2):
        if (left, right) in exact_pairs:
            continue
        if cross_project_only and project_slugs[left] == project_slugs[right]:
            continue
        distance = hamming_distance(perceptual_hashes[left], perceptual_hashes[right])
        if distance >= min_distance:
            continue
        issues.append(
            _duplicate_issue(
                left,
                right,
                item_kind=item_kind,
                exact=False,
                distance=distance,
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
            f"near-duplicate {item_kind} (Hamming distance {distance}): "
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
