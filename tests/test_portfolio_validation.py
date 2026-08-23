from pathlib import Path
import subprocess
import sys

import pytest
from PIL import Image, ImageDraw

import portfolio.kwork_pack.cli as cli
from portfolio.kwork_pack.catalog import PROJECTS
from portfolio.kwork_pack.validate import validate_pack


@pytest.fixture
def complete_fake_pack(tmp_path):
    def write_visual(path, seed, size):
        image = Image.new("RGB", size, (28 + seed * 7 % 100, 42, 58))
        draw = ImageDraw.Draw(image)
        width, height = size
        header = height // 7
        draw.rectangle((0, 0, width, header), fill=(242, 244, 247))
        draw.rectangle((width // 18, header // 3, width // 4, header * 2 // 3), fill=(20, 30, 42))
        draw.rectangle((width * 3 // 4, header // 3, width * 17 // 18, header * 2 // 3), fill=(seed * 29 % 200, 96, 70))
        for index in range(8):
            column = (index * 3 + seed) % 4
            row = index // 4
            left = width // 14 + column * (width // 5 + width // 40)
            top = height // 4 + row * (height // 6)
            right = left + width // 5
            bottom = top + height // 8
            draw.rectangle((left, top, right, bottom), fill=(70 + (seed + index) * 19 % 140, 115, 150))
            draw.rectangle((left + 24, top + 22, right - 32, top + 36), fill=(246, 246, 240))
        lower_top = height * 3 // 4
        for column in range(17):
            left = column * width // 17
            right = (column + 1) * width // 17
            tone = 35 if (seed >> (column % 8)) & 1 else 220
            draw.rectangle((left, lower_top, right, height), fill=(tone, 80 + column * 7 % 120, 150 - column * 5 % 90))
        for row in range(lower_top, height, max(8, height // 32)):
            draw.rectangle((0, row, width, row + max(2, height // 160)), fill=(244, 244, 244))
        image.save(path)

    def create(*, size=(1920, 1280), projects=PROJECTS):
        paths = []
        seed = 1
        for project in projects:
            for number, shot in enumerate(project.shots, start=1):
                path = tmp_path / project.slug / f"{number:02d}-{shot.key}.png"
                path.parent.mkdir(parents=True, exist_ok=True)
                write_visual(path, seed, size)
                paths.append(path)
                seed += 1
        return tuple(paths)

    return create


def test_empty_pack_reports_all_seventy_five_missing_images(tmp_path):
    report = validate_pack(PROJECTS, tmp_path)
    assert report.files_checked == 0
    assert len(report.issues) == 75
    assert all(issue.message == "missing image" for issue in report.issues)


def test_complete_pack_rejects_wrong_dimensions(tmp_path, complete_fake_pack):
    complete_fake_pack(size=(1600, 900))
    report = validate_pack(PROJECTS, tmp_path)
    assert any("expected 1920x1280" in issue.message for issue in report.issues)


def test_valid_project_has_five_checked_files_and_no_issues(
    tmp_path, complete_fake_pack
):
    project = PROJECTS[0]
    complete_fake_pack(projects=(project,))

    report = validate_pack((project,), tmp_path)

    assert report.files_checked == 5
    assert report.issues == ()


def test_pack_rejects_blank_lower_viewport(tmp_path, complete_fake_pack):
    project = PROJECTS[0]
    paths = complete_fake_pack(projects=(project,))
    image = Image.new("RGB", (1920, 1280), "white")
    ImageDraw.Draw(image).rectangle((0, 0, 1919, 700), fill="#222222")
    image.save(paths[0])

    report = validate_pack((project,), tmp_path)

    assert any(issue.code == "sparse-lower-viewport" for issue in report.issues)


def test_pack_rejects_cross_project_duplicate_screenshots(tmp_path, complete_fake_pack):
    first, second = PROJECTS[:2]
    paths = complete_fake_pack(projects=(first, second))
    paths[5].write_bytes(paths[0].read_bytes())

    report = validate_pack((first, second), tmp_path)

    duplicate_issues = [
        issue for issue in report.issues if issue.code == "duplicate-screenshot"
    ]
    assert len(duplicate_issues) == 1
    assert first.slug in duplicate_issues[0].message
    assert second.slug in duplicate_issues[0].message


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
    assert any(issue.file.endswith("02-diagnostics.png") and "exceeds 10000000 bytes" in issue.message for issue in report.issues)


def test_pack_reports_unexpected_png_with_stable_relative_path(
    tmp_path, complete_fake_pack
):
    project = PROJECTS[0]
    complete_fake_pack(projects=(project,))
    extra = tmp_path / project.slug / "05-extra.PNG"
    Image.new("RGB", (1920, 1280), "#d7dde2").save(extra, format="PNG")

    report = validate_pack((project,), tmp_path)

    assert report.files_checked == 5
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
    assert "Проверено файлов: 0; замечаний: 5" in output
    assert "изображение отсутствует" in output


def test_validate_assets_and_render_cli_reuse_existing_interfaces(
    tmp_path, monkeypatch, capsys
):
    project = PROJECTS[0]
    for index, declared_asset in enumerate(project.assets, start=1):
        asset = tmp_path / "assets" / project.slug / declared_asset.filename
        asset.parent.mkdir(parents=True, exist_ok=True)
        image = Image.new("RGB", (64, 64), (20 + index * 20, 60, 100))
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, index * 4, 63, index * 4 + 8), fill=(240, 240, 240))
        draw.rectangle((index * 5, 0, index * 5 + 8, 63), fill=(180, 70, 60))
        image.save(asset)
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
    assert "Ассеты: 7 из 7; отсутствуют: 0" in output
    assert "Отрендерено изображений: 5 из 5" in output
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
    assert "Ассеты: 0 из 91; отсутствуют: 91" in output
