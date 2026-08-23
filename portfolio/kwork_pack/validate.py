from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from .models import ProjectSpec
from .render import output_path


_EXPECTED_SIZE = (1920, 1280)
_MAX_BYTES = 10_000_000


@dataclass(frozen=True)
class ValidationIssue:
    project_slug: str
    file: str
    message: str


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
    issues: list[ValidationIssue] = []
    files_checked = 0

    for project in projects:
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
            issues.extend(_inspect_image(project, path, root))

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

    return ValidationReport(files_checked, tuple(issues))
