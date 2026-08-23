import csv
import json
from collections.abc import Iterable
from pathlib import Path

from .models import ProjectSpec
from .render import output_path


_CSV_FIELDS = (
    "slug",
    "title",
    "category",
    "subcategory",
    "work_type",
    "description",
    "domain",
    "image_1",
    "image_2",
    "image_3",
    "image_4",
    "image_5",
)


def _relative_images(project: ProjectSpec, output_root: Path) -> list[str]:
    return [
        output_path(output_root, project, shot).relative_to(output_root).as_posix()
        for shot in project.shots
    ]


def _work_record(project: ProjectSpec, output_root: Path) -> dict[str, object]:
    category, subcategory = project.category
    return {
        "slug": project.slug,
        "title": project.kwork_title,
        "category": category,
        "subcategory": subcategory,
        "work_type": project.work_type,
        "description": project.description,
        "domain": project.domain,
        "images": _relative_images(project, output_root),
    }


def write_manifests(
    projects: Iterable[ProjectSpec], output_root: Path
) -> tuple[Path, Path]:
    """Write deterministic Kwork upload metadata in JSON and Excel-safe CSV."""
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    works = [_work_record(project, root) for project in projects]
    json_path = root / "upload-manifest.json"
    csv_path = root / "upload-manifest.csv"

    with json_path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump({"works": works}, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=_CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        for work in works:
            images = work["images"]
            writer.writerow(
                {
                    key: work[key]
                    for key in _CSV_FIELDS
                    if not key.startswith("image_")
                }
                | {
                    f"image_{number}": image
                    for number, image in enumerate(images, start=1)
                }
            )

    return json_path, csv_path
