from pathlib import Path

from app.gui import build_app_command, build_script_command


def test_build_app_command_runs_module_with_src_pythonpath(tmp_path):
    command, env = build_app_command("scan", root_dir=tmp_path)

    assert command[-3:] == ["-m", "app.main", "scan"]
    assert env["PYTHONPATH"] == str(tmp_path / "src")


def test_build_app_command_can_run_approvals_from_gui(tmp_path):
    command, env = build_app_command("approvals", root_dir=tmp_path)

    assert command[-3:] == ["-m", "app.main", "approvals"]
    assert env["PYTHONPATH"] == str(tmp_path / "src")


def test_build_script_command_uses_cmd_runner(tmp_path):
    script = tmp_path / "start-kwork-browser.cmd"
    script.write_text("@echo off", encoding="utf-8")

    command = build_script_command(script)

    assert command == ["cmd", "/c", str(script)]


def test_kwork_browser_script_does_not_touch_regular_chrome_profile():
    script = (Path(__file__).resolve().parents[1] / "start-kwork-browser.cmd").read_text(encoding="utf-8")

    assert "taskkill" not in script.lower()
    assert "Get-Process chrome" not in script
    assert "robocopy" not in script.lower()
    assert "KworkLeadChromeUserData" in script
    assert "--user-data-dir=\"%BOT_PROFILE%\"" in script
    assert "--remote-debugging-address=127.0.0.1" in script
    assert "--remote-debugging-port=9222" in script
