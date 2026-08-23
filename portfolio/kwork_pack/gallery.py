from collections.abc import Iterable
from html import escape
from pathlib import Path

from .models import ProjectSpec
from .render import output_path
from .validate import validate_pack


_STYLE = """
:root { color-scheme: light; font-family: Arial, sans-serif; color: #17202a; }
* { box-sizing: border-box; letter-spacing: 0; }
body { margin: 0; background: #f5f6f7; }
header, main { width: min(1600px, calc(100% - 48px)); margin: 0 auto; }
header { padding: 48px 0 28px; }
h1, h2, p { margin-top: 0; }
.project-section { padding: 36px 0 42px; border-top: 1px solid #cbd2d9; }
.project-heading { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 24px; }
.project-domain { color: #476174; }
.validation-ok { color: #167146; font-weight: 700; }
.validation-error { color: #a12d2d; font-weight: 700; }
.shot-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 20px; }
figure { margin: 0; }
.project-shot { display: block; width: 100%; aspect-ratio: 3 / 2; object-fit: cover; background: #dde2e6; }
figcaption { padding-top: 8px; color: #52606b; }
@media (max-width: 900px) {
  .shot-grid, .project-heading { grid-template-columns: 1fr; }
}
""".strip()


def _project_section(
    project: ProjectSpec, output_root: Path, issue_count: int
) -> str:
    if issue_count:
        state_class = "validation-error"
        state = f"Есть замечания: {issue_count}"
    else:
        state_class = "validation-ok"
        state = "Проверка пройдена"

    thumbnails = []
    for shot in project.shots:
        path = output_path(output_root, project, shot)
        relative = path.relative_to(output_root).as_posix()
        thumbnails.append(
            '<figure><img class="project-shot" '
            f'src="{escape(relative, quote=True)}" '
            f'alt="{escape(project.brand, quote=True)}: {escape(shot.key, quote=True)}" />'
            f"<figcaption>{escape(shot.key)}</figcaption></figure>"
        )

    return (
        f'<section class="project-section" data-project="{escape(project.slug, quote=True)}">'
        '<div class="project-heading"><div>'
        f"<h2>{escape(project.kwork_title)}</h2>"
        f'<p class="project-domain">{escape(project.domain)}</p>'
        f"<p>{escape(project.description)}</p>"
        f'</div><p class="{state_class}">{state}</p></div>'
        f'<div class="shot-grid">{"".join(thumbnails)}</div>'
        "</section>"
    )


def write_gallery(projects: Iterable[ProjectSpec], output_root: Path) -> Path:
    """Write a read-only local contact sheet for the selected projects."""
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    selected_projects = tuple(projects)
    report = validate_pack(selected_projects, root)
    issue_counts = {project.slug: 0 for project in selected_projects}
    for issue in report.issues:
        issue_counts[issue.project_slug] += 1

    sections = "".join(
        _project_section(project, root, issue_counts[project.slug])
        for project in selected_projects
    )
    document = (
        "<!doctype html>\n"
        '<html lang="ru"><head><meta charset="utf-8" />'
        '<meta name="viewport" content="width=device-width, initial-scale=1" />'
        "<title>Портфолио Kwork</title>"
        f"<style>{_STYLE}</style></head><body>"
        "<header><h1>Портфолио Kwork</h1>"
        f"<p>Работ: {len(selected_projects)}. Проверено файлов: {report.files_checked}.</p>"
        f"</header><main>{sections}</main></body></html>\n"
    )
    gallery_path = root / "gallery.html"
    with gallery_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(document)
    return gallery_path
