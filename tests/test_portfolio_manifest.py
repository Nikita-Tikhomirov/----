import csv
import json

from PIL import Image

import portfolio.kwork_pack.cli as cli
from portfolio.kwork_pack.catalog import PROJECTS
from portfolio.kwork_pack.gallery import write_gallery
from portfolio.kwork_pack.manifest import write_manifests


def _write_project_images(root, project):
    paths = []
    for number, shot in enumerate(project.shots, start=1):
        path = root / project.slug / f"{number:02d}-{shot.key}.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (1920, 1280), "#d7dde2").save(path)
        paths.append(path)
    return tuple(paths)


def test_manifests_contain_fifteen_upload_rows_and_five_ordered_desktop_images(tmp_path):
    json_path, csv_path = write_manifests(PROJECTS, tmp_path)
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert len(payload["works"]) == 15
    assert payload["works"][0]["images"] == [
        "tochka-hoda/01-cover.png",
        "tochka-hoda/02-diagnostics.png",
        "tochka-hoda/03-services.png",
        "tochka-hoda/04-case-study.png",
        "tochka-hoda/05-prices.png",
    ]
    assert all(
        len(work["images"]) == 5 and all("mobile" not in image for image in work["images"])
        for work in payload["works"]
    )
    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        assert len(list(csv.DictReader(handle))) == 15


def test_manifests_are_deterministic_and_preserve_russian_metadata(tmp_path):
    json_path, csv_path = write_manifests(iter(PROJECTS), tmp_path)
    first_json = json_path.read_bytes()
    first_csv = csv_path.read_bytes()

    write_manifests(PROJECTS, tmp_path)

    assert json_path.name == "upload-manifest.json"
    assert csv_path.name == "upload-manifest.csv"
    assert json_path.read_bytes() == first_json
    assert csv_path.read_bytes() == first_csv
    assert first_csv.startswith(b"\xef\xbb\xbf")
    assert b"\\u0410" not in first_json
    work = json.loads(first_json.decode("utf-8"))["works"][0]
    assert work == {
        "slug": "tochka-hoda",
        "title": "Сайт автосервиса «Точка Хода»",
        "category": "Разработка и IT",
        "subcategory": "Создание сайта",
        "work_type": "Новый сайт",
        "description": PROJECTS[0].description,
        "domain": "tochka-hoda.ru",
        "images": [
            "tochka-hoda/01-cover.png",
            "tochka-hoda/02-diagnostics.png",
            "tochka-hoda/03-services.png",
            "tochka-hoda/04-case-study.png",
            "tochka-hoda/05-prices.png",
        ],
    }


def test_gallery_has_unframed_sections_and_never_rewrites_images(tmp_path):
    source_paths = _write_project_images(tmp_path, PROJECTS[0])
    original_bytes = tuple(path.read_bytes() for path in source_paths)

    gallery_path = write_gallery(PROJECTS, tmp_path)
    html = gallery_path.read_text(encoding="utf-8")

    assert gallery_path == tmp_path / "gallery.html"
    assert html.count('<section class="project-section') == 15
    assert html.count('<img class="project-shot"') == 75
    assert "aspect-ratio: 3 / 2" in html
    assert PROJECTS[0].kwork_title in html
    assert PROJECTS[0].domain in html
    assert PROJECTS[0].description in html
    assert "Проверка пройдена" in html
    assert "Есть замечания: 5" in html
    assert tuple(path.read_bytes() for path in source_paths) == original_bytes


def test_manifest_and_gallery_cli_commands_report_created_utf8_files(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setattr(cli, "PROJECTS", (PROJECTS[0],))

    assert cli.main(["manifest", "--output", str(tmp_path)]) == 0
    assert cli.main(["gallery", "--output", str(tmp_path)]) == 0

    output = capsys.readouterr().out
    assert "Манифесты созданы" in output
    assert "Галерея создана" in output
    assert (tmp_path / "upload-manifest.json").is_file()
    assert (tmp_path / "upload-manifest.csv").is_file()
    assert (tmp_path / "gallery.html").is_file()
