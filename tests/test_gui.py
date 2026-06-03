from pathlib import Path

import pytest

from app.gui import (
    _extract_days,
    _extract_price,
    _lead_title,
    _parse_optional_int,
    build_app_command,
    build_script_command,
    normalize_filter_settings,
    read_env_values,
    update_env_values,
)
from app.storage import Lead


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


def test_update_env_values_preserves_unrelated_secrets(tmp_path):
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "SMTP_PASSWORD=secret",
                "KWORK_MAX_RESPONSES=5",
                "LEAD_MIN_SCORE=60",
            ]
        ),
        encoding="utf-8",
    )

    update_env_values(
        env_path,
        {
            "KWORK_MAX_RESPONSES": "3",
            "LEAD_MIN_SCORE": "75",
            "LEAD_REQUIRED_KEYWORDS": "wordpress, html",
        },
    )

    values = read_env_values(env_path)
    assert values["SMTP_PASSWORD"] == "secret"
    assert values["KWORK_MAX_RESPONSES"] == "3"
    assert values["LEAD_MIN_SCORE"] == "75"
    assert values["LEAD_REQUIRED_KEYWORDS"] == "wordpress, html"


def test_normalize_filter_settings_validates_numbers_and_decisions():
    values = normalize_filter_settings(
        {
            "KWORK_MAX_RESPONSES": " 6 ",
            "SCAN_INTERVAL_SECONDS": "120",
            "MAX_POSTS_PER_CHANNEL": "25",
            "LEAD_MIN_SCORE": "70",
            "LEAD_MAX_DAYS": "5",
            "LEAD_ACCEPT_DECISIONS": "accept, maybe, accept",
            "LEAD_BLOCKED_KEYWORDS": " битрикс, shopify ",
            "LEAD_HARD_REJECT_KEYWORDS": "android, webgl",
            "LEAD_REQUIRED_KEYWORDS": "",
            "KWORK_PROJECTS_URL": "https://kwork.ru/projects?c=11",
        }
    )

    assert values["KWORK_MAX_RESPONSES"] == "6"
    assert values["LEAD_ACCEPT_DECISIONS"] == "accept, maybe"
    assert values["LEAD_BLOCKED_KEYWORDS"] == "битрикс, shopify"
    assert values["LEAD_REQUIRED_KEYWORDS"] == ""


def test_normalize_filter_settings_rejects_bad_kwork_url():
    with pytest.raises(ValueError, match="Страница Kwork"):
        normalize_filter_settings({"KWORK_PROJECTS_URL": "https://example.com/projects"})


def test_lead_gui_helpers_extract_editable_fields():
    lead = Lead(
        id=12,
        post_id=3,
        score=80,
        summary="AI: accept\nСрок: 3 дн.\nЦена: 7000 руб.\nЗадача: Поправить форму заявки на WordPress",
        draft_reply="Здравствуйте! Сделаю за 2 дня, цена 5000 руб.",
        contact="https://kwork.ru/projects/1",
        status="emailed",
        post_url="https://kwork.ru/projects/1",
    )

    assert _extract_price(lead) == 5000
    assert _extract_days(lead) == 2
    assert _lead_title(lead) == "Поправить форму заявки на WordPress"
    assert _parse_optional_int(" 12 000 ", "Цена") == 12000
    assert _parse_optional_int("", "Цена") is None


def test_parse_optional_int_rejects_negative_values():
    with pytest.raises(ValueError, match="больше 0"):
        _parse_optional_int("-1", "Цена")
