import argparse
from collections.abc import Sequence
from pathlib import Path
import sys

from .assets import missing_assets
from .catalog import PROJECTS
from .domain_check import check_domain
from .gallery import write_gallery
from .manifest import write_manifests
from .render import render_all
from .validate import ValidationIssue, validate_pack


_DEFAULT_OUTPUT = Path("artifacts/kwork-portfolio")


def _add_output_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--output",
        type=Path,
        default=_DEFAULT_OUTPUT,
        help="Каталог ассетов и итоговых файлов",
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Подготовка портфолио Kwork")
    commands = parser.add_subparsers(dest="command", required=True)

    domains = commands.add_parser("domains", help="Проверить домены концептов")
    domains.add_argument("--check", action="store_true", required=True)
    domains.set_defaults(handler=_run_domains)

    for name, help_text, handler in (
        ("validate-assets", "Проверить исходные изображения", _run_validate_assets),
        ("render", "Отрендерить изображения портфолио", _run_render),
        ("manifest", "Создать манифесты загрузки", _run_manifest),
        ("validate", "Проверить итоговый набор", _run_validate),
        ("gallery", "Создать локальную галерею", _run_gallery),
    ):
        command = commands.add_parser(name, help=help_text)
        _add_output_argument(command)
        command.set_defaults(handler=handler)
    return parser


def _display_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _run_domains(_args: argparse.Namespace) -> int:
    failed = False
    for project in PROJECTS:
        try:
            status = check_domain(project.domain)
        except Exception as exc:
            failed = True
            print(f"[{project.slug}] Ошибка проверки домена {project.domain}: {exc}")
            continue
        if status.resolves:
            failed = True
            addresses = ", ".join(status.addresses)
            print(
                f"[{project.slug}] Коллизия домена {project.domain}: {addresses}"
            )
        else:
            print(f"[{project.slug}] {project.domain}: DNS-записей нет")
    return int(failed)


def _run_validate_assets(args: argparse.Namespace) -> int:
    root = Path(args.output)
    missing = missing_assets(root, PROJECTS)
    expected = sum(len(project.assets) for project in PROJECTS)
    for path in missing:
        print(f"Отсутствует ассет: {_display_path(path, root)}")
    print(f"Ассеты: {expected - len(missing)} из {expected}; отсутствуют: {len(missing)}")
    return int(bool(missing))


def _run_render(args: argparse.Namespace) -> int:
    paths = render_all(PROJECTS, Path(args.output))
    expected = sum(len(project.shots) for project in PROJECTS)
    print(f"Отрендерено изображений: {len(paths)} из {expected}")
    return int(len(paths) != expected)


def _run_manifest(args: argparse.Namespace) -> int:
    json_path, csv_path = write_manifests(PROJECTS, Path(args.output))
    print(f"Манифесты созданы: {json_path.name}, {csv_path.name}")
    return 0


def _russian_issue(issue: ValidationIssue) -> str:
    message = issue.message
    if message == "missing image":
        return "изображение отсутствует"
    if message == "unexpected PNG file":
        return "лишний PNG-файл"
    if message.startswith("expected 1920x1280, got "):
        return message.replace("expected 1920x1280, got ", "ожидался размер 1920x1280, получен ")
    if message.startswith("expected PNG format, got "):
        return message.replace("expected PNG format, got ", "ожидался формат PNG, получен ")
    if message.startswith("file size ") and " exceeds 10000000 bytes" in message:
        size = message.removeprefix("file size ").removesuffix(
            " exceeds 10000000 bytes"
        )
        return f"размер файла {size} байт превышает 10000000 байт"
    if message.startswith("invalid image: "):
        return "файл не является читаемым изображением"
    return message


def _run_validate(args: argparse.Namespace) -> int:
    report = validate_pack(PROJECTS, Path(args.output))
    for issue in report.issues:
        print(
            f"[{issue.project_slug}] {issue.file}: {_russian_issue(issue)}"
        )
    print(
        f"Проверено файлов: {report.files_checked}; замечаний: {len(report.issues)}"
    )
    return int(bool(report.issues))


def _run_gallery(args: argparse.Namespace) -> int:
    gallery_path = write_gallery(PROJECTS, Path(args.output))
    print(f"Галерея создана: {gallery_path}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run a portfolio preparation command without publication side effects."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except Exception as exc:
        print(f"Ошибка выполнения команды {args.command}: {exc}")
        return 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
