from pathlib import Path

import pytest

from app.gui import (
    LeadFunnelGui,
    _lead_details_text,
    _attachment_row_values,
    _fallback_attachments_from_summary,
    _extract_days,
    _extract_offer_count,
    _extract_price,
    _extract_remaining_time,
    _lead_title,
    _parse_optional_int,
    build_lead_row_values,
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


def test_lead_table_row_uses_kwork_card_title_and_operational_metadata():
    lead = Lead(
        id=18,
        post_id=7,
        score=65,
        summary="AI: maybe\nСрок: 5 дн.\nЦена: 12000 руб.\nЗадача: AI написал слишком общий заголовок",
        draft_reply="Здравствуйте! Сделаю за 4 дня, цена 9000 руб.",
        contact="https://kwork.ru/projects/3187247/view",
        status="sent",
        post_url="https://kwork.ru/projects/3187247/view",
        post_text=(
            "📌 Доработать форму заявки на WordPress\n"
            "Осталось: 2 д. 17 ч.\n"
            "Предложений: 4\n"
            "Отклик: https://kwork.ru/projects/3187247/view"
        ),
        posted_at="2026-05-04T10:30:00+03:00",
        sent_at="2026-05-04 10:45:12",
    )

    assert _lead_title(lead) == "Доработать форму заявки на WordPress"
    assert _extract_offer_count(lead) == 4
    assert _extract_remaining_time(lead) == "2 д. 17 ч."
    assert build_lead_row_values(lead) == (
        18,
        "04.05 10:30",
        4,
        "отправлен 04.05 10:45",
        "sent",
        65,
        9000,
        4,
        "Доработать форму заявки на WordPress",
    )

    details = _lead_details_text(lead)
    assert "Название: Доработать форму заявки на WordPress" in details
    assert "Ссылка: https://kwork.ru/projects/3187247/view" in details
    assert "Предложений: 4" in details
    assert "Осталось: 2 д. 17 ч." in details
    assert "КАРТОЧКА KWORK" in details
    assert "AI написал слишком общий заголовок" in details


def test_lead_url_is_rendered_as_clickable_link():
    source = (Path(__file__).resolve().parents[1] / "src" / "app" / "gui.py").read_text(encoding="utf-8")

    assert "self.lead_url_label = ttk.Label" in source
    assert 'style="Link.TLabel"' in source
    assert 'cursor="hand2"' in source
    assert 'self.lead_url_label.bind("<Button-1>", self.open_selected_lead_from_url)' in source


def test_clickable_url_handler_opens_selected_lead():
    class DummyGui:
        def __init__(self):
            self.opened = 0

        def open_selected_lead(self):
            self.opened += 1

    dummy = DummyGui()

    assert LeadFunnelGui.open_selected_lead_from_url(dummy) == "break"
    assert dummy.opened == 1


def test_gui_extracts_attachment_rows_from_existing_lead_summary():
    lead = Lead(
        id=22,
        post_id=8,
        score=74,
        summary=(
            "AI: maybe\n\n"
            "ФАЙЛЫ/ТЗ:\n"
            "- ТЗ.zip\n"
            "  Ссылка: https://kwork.ru/files/tz.zip\n"
            "  Статус: скачан, архив открыт\n"
            "  Кратко: brief.txt: прочитан Нужно сверстать форму\n\n"
            "- screen.png\n"
            "  Ссылка: https://kwork.ru/files/screen.png\n"
            "  Статус: скачан, OCR прочитан\n"
            "  Кратко: На скрине форма заявки"
        ),
        draft_reply="Здравствуйте! Сделаю.",
        contact="https://kwork.ru/projects/22/view",
        status="emailed",
        post_url="https://kwork.ru/projects/22/view",
    )

    attachments = _fallback_attachments_from_summary(lead)

    assert len(attachments) == 2
    assert attachments[0].label == "ТЗ.zip"
    assert attachments[0].opened_archive is True
    assert attachments[0].ocr_scanned is False
    assert attachments[1].label == "screen.png"
    assert attachments[1].ocr_scanned is True
    assert _attachment_row_values(attachments[0]) == (
        "ТЗ.zip",
        "скачан, архив открыт",
        "archive",
        "нет локального файла",
        "brief.txt: прочитан Нужно сверстать форму",
    )
