from pathlib import Path

import portfolio.kwork_pack.cli as cli
from portfolio.kwork_pack.validate import ValidationReport


def test_render_command_can_select_one_project(tmp_path, monkeypatch, capsys):
    calls = []

    def fake_render_all(projects, output_root):
        selected = tuple(projects)
        calls.append((selected, Path(output_root)))
        return tuple(
            Path(output_root) / selected[0].slug / f"{index:02d}-{shot.key}.png"
            for index, shot in enumerate(selected[0].shots, start=1)
        )

    monkeypatch.setattr(cli, "render_all", fake_render_all)

    result = cli.main(
        [
            "render",
            "--output",
            str(tmp_path),
            "--project",
            "tochka-hoda",
        ]
    )

    assert result == 0
    assert [project.slug for project in calls[0][0]] == ["tochka-hoda"]
    assert calls[0][1] == tmp_path
    assert "Отрендерено изображений: 5 из 5" in capsys.readouterr().out


def test_validate_command_can_select_one_project(tmp_path, monkeypatch, capsys):
    calls = []

    def fake_validate_pack(projects, output_root):
        selected = tuple(projects)
        calls.append((selected, Path(output_root)))
        return ValidationReport(files_checked=5, issues=())

    monkeypatch.setattr(cli, "validate_pack", fake_validate_pack)

    result = cli.main(
        [
            "validate",
            "--output",
            str(tmp_path),
            "--project",
            "tochka-hoda",
        ]
    )

    assert result == 0
    assert [project.slug for project in calls[0][0]] == ["tochka-hoda"]
    assert calls[0][1] == tmp_path
    assert "Проверено файлов: 5; замечаний: 0" in capsys.readouterr().out

