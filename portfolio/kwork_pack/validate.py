from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from .models import ProjectSpec
from .quality import (
    ValidationIssue,
    bottom_band_metrics,
    validate_asset_uniqueness,
    validate_cross_project_screenshot_uniqueness,
)
from .render import output_path


_EXPECTED_SIZE = (1920, 1280)
_MAX_BYTES = 10_000_000
_MIN_LOWER_BAND_VARIANCE = 40.0
_MIN_LOWER_BAND_EDGE_DENSITY = 0.003
_SCREENSHOT_MIN_DISTANCE = 12


@dataclass(frozen=True)
class ValidationReport:
    files_checked: int
    issues: tuple[ValidationIssue, ...]


def _relative_path(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _inspect_image(
    project: ProjectSpec, path: Path, root: Path
) -> tuple[ValidationIssue, ...]:
    file = _relative_path(path, root)
    issues: list[ValidationIssue] = []
    if path.stat().st_size > _MAX_BYTES:
        issues.append(
            ValidationIssue(
                project.slug,
                file,
                f"file size {path.stat().st_size} exceeds {_MAX_BYTES} bytes",
            )
        )
    try:
        with Image.open(path) as image:
            image_format = image.format
            image_size = image.size
            image.verify()
    except (OSError, UnidentifiedImageError, ValueError) as exc:
        issues.append(
            ValidationIssue(project.slug, file, f"invalid image: {exc}")
        )
        return tuple(issues)

    if image_format != "PNG":
        issues.append(
            ValidationIssue(
                project.slug,
                file,
                f"expected PNG format, got {image_format or 'unknown'}",
            )
        )
    if image_size != _EXPECTED_SIZE:
        issues.append(
            ValidationIssue(
                project.slug,
                file,
                f"expected 1920x1280, got {image_size[0]}x{image_size[1]}",
            )
        )
    return tuple(issues)


def validate_pack(
    projects: Iterable[ProjectSpec], output_root: Path
) -> ValidationReport:
    """Validate every declared render and reject undeclared project PNG files."""
    root = Path(output_root)
    project_specs = tuple(projects)
    issues: list[ValidationIssue] = []
    files_checked = 0
    valid_screenshots: list[tuple[ProjectSpec, Path]] = []

    for project in project_specs:
        expected_paths = tuple(
            output_path(root, project, shot) for shot in project.shots
        )
        project_dir = root / project.slug
        expected_relatives = {
            path.relative_to(project_dir).as_posix().casefold()
            for path in expected_paths
        }
        for path in expected_paths:
            file = _relative_path(path, root)
            if not path.is_file():
                issues.append(ValidationIssue(project.slug, file, "missing image"))
                continue
            files_checked += 1
            image_issues = _inspect_image(project, path, root)
            issues.extend(image_issues)
            if image_issues:
                continue
            valid_screenshots.append((project, path))
            variance, edge_density = bottom_band_metrics(path)
            if (
                variance < _MIN_LOWER_BAND_VARIANCE
                or edge_density < _MIN_LOWER_BAND_EDGE_DENSITY
            ):
                issues.append(
                    ValidationIssue(
                        project.slug,
                        file,
                        "lower viewport lacks meaningful visual content "
                        f"(variance {variance:.2f}, edge density {edge_density:.4f})",
                        "sparse-lower-viewport",
                    )
                )

        if project_dir.is_dir():
            unexpected = sorted(
                (
                    path
                    for path in project_dir.rglob("*")
                    if path.is_file()
                    and path.suffix.casefold() == ".png"
                    and path.relative_to(project_dir).as_posix().casefold()
                    not in expected_relatives
                ),
                key=lambda path: (
                    path.relative_to(project_dir).as_posix().casefold(),
                    path.relative_to(project_dir).as_posix(),
                ),
            )
            issues.extend(
                ValidationIssue(
                    project.slug,
                    _relative_path(path, root),
                    "unexpected PNG file",
                )
                for path in unexpected
            )

    issues.extend(validate_asset_uniqueness(root, project_specs))
    issues.extend(
        validate_cross_project_screenshot_uniqueness(
            valid_screenshots, min_distance=_SCREENSHOT_MIN_DISTANCE
        )
    )
    return ValidationReport(files_checked, tuple(issues))
