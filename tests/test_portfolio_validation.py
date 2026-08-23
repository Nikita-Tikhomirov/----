from pathlib import Path
import subprocess
import sys

import pytest
from PIL import Image

import portfolio.kwork_pack.cli as cli
from portfolio.kwork_pack.catalog import PROJECTS
from portfolio.kwork_pack.validate import validate_pack


@pytest.fixture
def complete_fake_pack(tmp_path):
    def create(*, size=(1920, 1280), projects=PROJECTS):
        paths = []
        for project in projects:
            for number, shot in enumerate(project.shots, start=1):
                path = tmp_path / project.slug / f"{number:02d}-{shot.key}.png"
                path.parent.mkdir(parents=True, exist_ok=True)
                Image.new("RGB", size, "#d7dde2").save(path)
                paths.append(path)
        return tuple(paths)

    return create


def test_empty_pack_reports_all_sixty_missing_images(tmp_path):
    report = validate_pack(PROJECTS, tmp_path)
    assert report.files_checked == 0
    assert len(report.issues) == 60
    assert all(issue.message == "missing image" for issue in report.issues)


def test_complete_pack_rejects_wrong_dimensions(tmp_path, complete_fake_pack):
    complete_fake_pack(size=(1600, 900))
    report = validate_pack(PROJECTS, tmp_path)
    assert any("expected 1920x1280" in issue.message for issue in report.issues)


def test_valid_project_has_four_checked_files_and_no_issues(
    tmp_path, complete_fake_pack
):
    project = PROJECTS[0]
    complete_fake_pack(projects=(project,))

    report = validate_pack((project,), tmp_path)

    assert report.files_checked == 4
    assert report.issues == ()


def test_pack_rejects_non_png_content_and_oversized_files(
    tmp_path, complete_fake_pack
):
    project = PROJECTS[0]
    paths = complete_fake_pack(projects=(project,))
    Image.new("RGB", (1920, 1280), "#d7dde2").save(paths[0], format="JPEG")
    with paths[1].open("ab") as handle:
        handle.write(b"\0" * (10_000_001 - paths[1].stat().st_size))

    report = validate_pack((project,), tmp_path)

    assert any(issue.file.endswith("01-cover.png") and "PNG format" in issue.message for issue in report.issues)
    assert any(issue.file.endswith("02-content.png") and "exceeds 10000000 bytes" in issue.message for issue in report.issues)


def test_pack_reports_unexpected_png_with_stable_relative_path(
    tmp_path, complete_fake_pack
):
    project = PROJECTS[0]
    complete_fake_pack(projects=(project,))
    extra = tmp_path / project.slug / "05-extra.PNG"
    Image.new("RGB", (1920, 1280), "#d7dde2").save(extra, format="PNG")

    report = validate_pack((project,), tmp_path)

    assert report.files_checked == 4
    assert [(issue.project_slug, issue.file, issue.message) for issue in report.issues] == [
        ("tochka-hoda", "tochka-hoda/05-extra.PNG", "unexpected PNG file")
    ]


def test_pack_rejects_png_nested_below_a_project_directory(
    tmp_path, complete_fake_pack
):
    project = PROJECTS[0]
    complete_fake_pack(projects=(project,))
    extra = tmp_path / project.slug / "nested" / "extra.png"
    extra.parent.mkdir()
    Image.new("RGB", (1920, 1280), "#d7dde2").save(extra)

    report = validate_pack((project,), tmp_path)

    assert [(issue.file, issue.message) for issue in report.issues] == [
        ("tochka-hoda/nested/extra.png", "unexpected PNG file")
    ]


def test_validate_cli_uses_russian_diagnostics_and_failure_exit(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setattr(cli, "PROJECTS", (PROJECTS[0],))

    assert cli.main(["validate", "--output", str(tmp_path)]) == 1

    output = capsys.readouterr().out
    assert "Проверено файлов: 0; замечаний: 4" in output
    assert "изображение отсутствует" in output


def test_validate_assets_and_render_cli_reuse_existing_interfaces(
    tmp_path, monkeypatch, capsys
):
    project = PROJECTS[0]
    asset = tmp_path / "assets" / project.slug / "hero.png"
    asset.parent.mkdir(parents=True)
    asset.write_bytes(b"bitmap")
    calls = []

    def fake_render_all(projects, output_root):
        calls.append((tuple(projects), Path(output_root)))
        return tuple(
            output_root / project.slug / f"{number:02d}-{shot.key}.png"
            for number, shot in enumerate(project.shots, start=1)
        )

    monkeypatch.setattr(cli, "PROJECTS", (project,))
    monkeypatch.setattr(cli, "render_all", fake_render_all)

    assert cli.main(["validate-assets", "--output", str(tmp_path)]) == 0
    assert cli.main(["render", "--output", str(tmp_path)]) == 0

    output = capsys.readouterr().out
    assert "Ассеты: 1 из 1; отсутствуют: 0" in output
    assert "Отрендерено изображений: 4 из 4" in output
    assert calls == [((project,), tmp_path)]


def test_render_cli_reports_unexpected_handler_exception_without_traceback(
    tmp_path, monkeypatch, capsys
):
    def fail_render(*_args, **_kwargs):
        raise Exception("неожиданный сбой")

    monkeypatch.setattr(cli, "render_all", fail_render)

    result = cli.main(["render", "--output", str(tmp_path)])

    captured = capsys.readouterr()
    assert result == 1
    assert captured.out == (
        "Ошибка выполнения команды render: неожиданный сбой\n"
    )
    assert captured.err == ""


def test_module_cli_emits_utf8_russian_diagnostics(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "portfolio.kwork_pack.cli",
            "validate-assets",
            "--output",
            str(tmp_path),
        ],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    output = result.stdout.decode("utf-8")
    assert result.returncode == 1
    assert "Ассеты: 0 из 15; отсутствуют: 15" in output
