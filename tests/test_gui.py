from pathlib import Path
from types import SimpleNamespace
from datetime import datetime, timezone
from tkinter import Text, Tk

import pytest

from app.gui import (
    LeadFunnelGui,
    _lead_details_text,
    _attachment_row_values,
    _assessment_source_from_lead,
    _rejudge_existing_lead,
    _copy_widget_selection_to_clipboard,
    _fallback_attachments_from_summary,
    _extract_days,
    _extract_offer_count,
    _extract_price,
    _extract_remaining_time,
    _format_datetime,
    _format_storage_datetime,
    _lead_title,
    _lead_row_tags,
    _kwork_price_limit,
    _parse_optional_int,
    _post_title,
    _reply_context_from_lead,
    _should_refresh_after_process,
    direct_send_confirmation,
    lead_status_summary,
    lead_send_block_reason,
    build_lead_row_values,
    build_app_command,
    build_component_check_report,
    filter_active_leads,
    select_leads_for_live_check,
    build_script_command,
    normalize_filter_settings,
    read_env_values,
    update_env_values,
)
from app.ai_lead_judge import LeadJudgeResult
from app.storage import Lead, LeadAttachment, PostRejection, Storage


def test_build_app_command_runs_module_with_src_pythonpath(tmp_path, monkeypatch):
    monkeypatch.delenv("PYTHONUTF8", raising=False)

    command, env = build_app_command("scan", root_dir=tmp_path)

    assert command[-3:] == ["-m", "app.main", "scan"]
    assert env["PYTHONPATH"] == str(tmp_path / "src")
    assert env["PYTHONIOENCODING"] == "utf-8"
    assert "PYTHONUTF8" not in env


def test_build_app_command_can_run_approvals_from_gui(tmp_path):
    command, env = build_app_command("approvals", root_dir=tmp_path)

    assert command[-3:] == ["-m", "app.main", "approvals"]
    assert env["PYTHONPATH"] == str(tmp_path / "src")


def test_component_check_report_shows_ready_ocr_ai_and_kwork_chrome(tmp_path):
    tesseract = tmp_path / "tesseract.exe"
    tesseract.touch()

    report = build_component_check_report(
        {
            "TESSERACT_CMD": str(tesseract),
            "DEEPSEEK_API_KEY": "configured",
            "DEEPSEEK_MODEL": "deepseek-chat",
            "OPENROUTER_API_KEY": "configured",
            "OPENROUTER_VISION_MODEL": "qwen/qwen3.7-plus",
            "OPENROUTER_VISION_MODE": "smart",
            "KWORK_CDP_URL": "http://127.0.0.1:9222",
        },
        ocr_probe=lambda _command: {"rus", "eng", "osd"},
        chrome_probe=lambda _url: True,
        tesseract_command_resolver=lambda value: Path(value),
    )

    assert "Tesseract OCR: готов (rus, eng)" in report
    assert "DeepSeek: настроен (deepseek-chat)" in report
    assert "OpenRouter vision: настроен (qwen/qwen3.7-plus, smart)" in report
    assert "Kwork Chrome: доступен" in report


def test_component_check_report_explains_missing_components(tmp_path):
    missing_tesseract = tmp_path / "missing.exe"

    report = build_component_check_report(
        {
            "TESSERACT_CMD": str(missing_tesseract),
            "KWORK_CDP_URL": "http://127.0.0.1:9222",
        },
        chrome_probe=lambda _url: False,
        tesseract_command_resolver=lambda value: Path(value),
    )

    assert f"Tesseract OCR: не найден ({missing_tesseract})" in report
    assert "DeepSeek: ключ не настроен" in report
    assert "OpenRouter vision: ключ или модель не настроены" in report
    assert "Kwork Chrome: не запущен" in report


def test_component_check_report_explains_invalid_non_d_tesseract_path():
    report = build_component_check_report(
        {"TESSERACT_CMD": r"C:\\Tesseract-OCR\\tesseract.exe"},
        chrome_probe=lambda _url: False,
    )

    assert "Tesseract OCR: ошибка настройки" in report
    assert "D: диск" in report


def test_gui_sender_passes_live_response_limit_to_kwork_sender(monkeypatch):
    import app.gui as gui

    captured = {}

    class FakeSender:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    config = SimpleNamespace(
        kwork_cdp_url="http://127.0.0.1:9222",
        kwork_browser_profile_dir="C:/tmp/KworkChrome",
        kwork_login_email="bot@example.com",
        kwork_login_password="secret",
        kwork_max_responses=5,
        kwork_cookie="session=opaque",
    )
    monkeypatch.setattr(gui, "load_config", lambda: config)
    monkeypatch.setattr(gui, "KworkReplySender", FakeSender)

    LeadFunnelGui._sender(object())

    assert captured["max_responses"] == 5
    assert captured["cookie"] == "session=opaque"


def test_reply_context_for_regeneration_uses_selected_terms_and_attachment_reports():
    lead = Lead(
        id=23,
        post_id=9,
        score=82,
        summary="Задача: Исправить форму заявки\nСрок: 3 дн.",
        draft_reply="Старый черновик",
        contact="https://kwork.ru/projects/23/view",
        status="emailed",
        post_url="https://kwork.ru/projects/23/view",
        post_text="На мобильном не отправляется форма заявки.",
    )
    attachment = LeadAttachment(
        id=1,
        lead_id=23,
        label="ТЗ.pdf",
        url="https://kwork.ru/files/tz.pdf",
        local_path="C:/tmp/tz.pdf",
        status="скачан, текст прочитан",
        summary="Нужно проверить отправку формы на iPhone.",
        kind="pdf",
        opened_archive=False,
        ocr_scanned=False,
    )

    context = _reply_context_from_lead(
        lead,
        title="Исправить форму заявки",
        days=2,
        attachments=[attachment],
    )

    assert context.title == "Исправить форму заявки"
    assert context.estimated_days == 2
    assert "На мобильном не отправляется" in context.source_text
    assert "ТЗ.pdf" in context.attachment_context
    assert "iPhone" in context.attachment_context


def test_reply_context_for_regeneration_excludes_ai_summary_from_task_facts():
    lead = Lead(
        id=26,
        post_id=12,
        score=82,
        summary=(
            "Задача: Посадить каталог на WordPress\n"
            "Риск: интеграция может быть сложной для новичка."
        ),
        draft_reply="Старый черновик",
        contact="https://kwork.ru/projects/26/view",
        status="emailed",
        post_url="https://kwork.ru/projects/26/view",
        post_text="Посадить информационную страницу и каталог по PSD на WordPress.",
    )

    context = _reply_context_from_lead(
        lead,
        title="Посадить каталог на WordPress",
        days=4,
        attachments=[],
    )

    assert "информационную страницу" in context.source_text
    assert "сложной для новичка" not in context.source_text
    assert "сложной для новичка" not in context.task_summary


def test_assessment_source_uses_original_order_and_attachment_reports_not_old_ai_summary():
    lead = Lead(
        id=27,
        post_id=13,
        score=65,
        summary="AI: accept\nЗадача: Старая неподходящая интерпретация",
        draft_reply="Старый текст",
        contact="https://kwork.ru/projects/27/view",
        status="emailed",
        post_url="https://kwork.ru/projects/27/view",
        post_text="Правки формы заявки на WordPress\nПредложений: 3",
        proposal_title="Правки формы",
    )
    attachments = [
        LeadAttachment(
            id=1,
            lead_id=27,
            label="ТЗ.pdf",
            url="https://kwork.ru/files/tz.pdf",
            local_path="C:/tmp/tz.pdf",
            status="скачан, текст прочитан",
            summary="Нужно проверить отправку формы на мобильном.",
            kind="pdf",
            opened_archive=False,
            ocr_scanned=False,
        )
    ]

    source = _assessment_source_from_lead(lead, attachments)

    assert "Правки формы заявки на WordPress" in source
    assert "ТЗ.pdf" in source
    assert "проверить отправку формы" in source
    assert "Старая неподходящая интерпретация" not in source


def test_rejudge_existing_lead_updates_assessment_without_overwriting_manual_proposal():
    lead = Lead(
        id=28,
        post_id=14,
        score=65,
        summary="Старая AI-оценка",
        draft_reply="Вручную исправленный отклик",
        contact="https://kwork.ru/projects/28/view",
        status="emailed",
        post_url="https://kwork.ru/projects/28/view",
        post_text="Нужно исправить форму заявки на WordPress",
        proposal_title="Мое название",
        proposal_price_rub=9000,
        proposal_days=3,
    )
    captured = {}

    class Storage:
        def update_lead_assessment(self, lead_id, **values):
            captured["lead_id"] = lead_id
            captured.update(values)

    def judge(source, **kwargs):
        captured["source"] = source
        captured["judge_kwargs"] = kwargs
        return LeadJudgeResult(
            accepted=True,
            decision="accept",
            score=88,
            complexity="medium",
            estimated_days=5,
            price_rub=15000,
            summary="Исправить форму заявки",
            reasons=["задача понятна"],
            risks=[],
            questions=[],
            draft_reply="Здравствуйте!",
            customer_goal="Чтобы заявки доходили",
            work_plan=["Проверить форму", "Исправить обработку", "Протестировать"],
        )

    result = _rejudge_existing_lead(
        Storage(),
        lead,
        [],
        api_key="sk-test",
        model="deepseek-chat",
        min_score=60,
        max_days=7,
        accept_decisions=("accept", "maybe"),
        blocked_keywords=("bitrix",),
        hard_reject_keywords=(),
        judge=judge,
        summary_builder=lambda _result: "Новая AI-оценка",
    )

    assert result.score == 88
    assert "исправить форму" in captured["source"].lower()
    assert captured["lead_id"] == 28
    assert captured["score"] == 88
    assert captured["summary"] == "Новая AI-оценка"
    assert captured["price_rub"] == 9000
    assert captured["days"] == 3
    assert "draft_reply" not in captured


def test_gui_rejudge_confirmation_starts_background_analysis_without_kwork_send(monkeypatch):
    import app.gui as gui_module

    lead = Lead(
        id=29,
        post_id=15,
        score=65,
        summary="Старая AI-оценка",
        draft_reply="Старый отклик",
        contact="https://kwork.ru/projects/29/view",
        status="emailed",
        post_url="https://kwork.ru/projects/29/view",
        post_text="Нужно исправить форму заявки",
    )
    calls = []

    class Button:
        def config(self, **kwargs):
            calls.append(("button", kwargs))

    class Root:
        def after(self, *_args, **_kwargs):
            pytest.fail("AI rejudge must not run inline from the GUI click")

    class Thread:
        def __init__(self, *, target, args, daemon):
            calls.append(("thread", target, args, daemon))

        def start(self):
            calls.append(("start",))

    config = SimpleNamespace(
        deepseek_api_key="sk-test",
        deepseek_model="deepseek-chat",
        lead_min_score=60,
        lead_max_days=7,
        lead_accept_decisions=("accept", "maybe"),
        lead_blocked_keywords=("bitrix",),
        lead_hard_reject_keywords=(),
    )
    dummy = SimpleNamespace(
        _selected_lead=lambda: lead,
        rejudge_in_flight=False,
        pending_replies={},
        _attachments_for_lead=lambda _lead: [],
        rejudge_button=Button(),
        status_var=SimpleNamespace(set=lambda value: calls.append(("status", value))),
        write_log=lambda value: calls.append(("log", value)),
        _rejudge_selected_lead_thread=lambda *args: None,
        root=Root(),
    )
    monkeypatch.setattr(gui_module, "load_config", lambda: config)
    monkeypatch.setattr(gui_module.messagebox, "askyesno", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(gui_module.threading, "Thread", Thread)

    LeadFunnelGui.rejudge_selected_lead(dummy)

    assert dummy.rejudge_in_flight is True
    assert ("button", {"state": "disabled"}) in calls
    assert ("start",) in calls
    assert any(item[0] == "thread" and item[3] is True for item in calls)
    assert not any(item[0] == "send" for item in calls)


def test_selected_lead_shows_reply_repair_warning_before_send():
    lead = Lead(
        id=28,
        post_id=14,
        score=82,
        summary="Задача: Посадить каталог на WordPress",
        draft_reply=(
            "Здравствуйте! Посмотрел задачу по посадке сайта и каталога на WordPress. "
            "Сначала проверю текущую отправку формы и валидацию на мобильных, затем внесу нужные правки в разметку и стили. "
            "После изменений протестирую сценарий на телефоне и в основных браузерах, чтобы заявки стабильно доходили. "
            "На работу ориентируюсь на 5 дн., могу приступить сразу."
        ),
        contact="https://kwork.ru/projects/28/view",
        status="emailed",
        post_url="https://kwork.ru/projects/28/view",
        post_text="Посадить информационную страницу и каталог по PSD на WordPress.",
    )

    class Table:
        def selection(self):
            return ("lead-28",)

    class Storage:
        def get_lead(self, lead_id):
            assert lead_id == 28
            return lead

    class Value:
        def __init__(self):
            self.value = ""

        def set(self, value):
            self.value = value

    class Text:
        def __init__(self):
            self.value = ""

        def delete(self, *_args):
            self.value = ""

        def insert(self, _index, value):
            self.value = value

    dummy = SimpleNamespace(
        leads_table=Table(),
        lead_rows={"lead-28": 28},
        _storage=lambda: Storage(),
        current_lead_id=None,
        lead_title_var=Value(),
        lead_price_var=Value(),
        lead_days_var=Value(),
        lead_url_var=Value(),
        lead_status_var=Value(),
        pending_replies={},
        summary_text=Text(),
        reply_text=Text(),
        _attachments_for_lead=lambda _lead: [],
        _load_lead_attachments=lambda *_args: None,
    )

    LeadFunnelGui.on_lead_select(dummy)

    assert "требует правки" in dummy.lead_status_var.value
    assert "действие, которого нет в заказе" in dummy.lead_status_var.value


def test_apply_regenerated_reply_keeps_draft_in_memory_until_save():
    class Text:
        def __init__(self):
            self.value = "Старый текст"

        def delete(self, *_args):
            self.value = ""

        def insert(self, _index, value):
            self.value = value

    class Value:
        def __init__(self):
            self.value = ""

        def set(self, value):
            self.value = value

    dummy = type(
        "DummyGui",
        (),
        {
            "current_lead_id": 23,
            "pending_replies": {},
            "reply_text": Text(),
            "lead_status_var": Value(),
        },
    )()

    LeadFunnelGui._apply_regenerated_reply(dummy, 23, "Новый человеческий текст отклика.")

    assert dummy.pending_replies == {23: "Новый человеческий текст отклика."}
    assert dummy.reply_text.value == "Новый человеческий текст отклика."
    assert "не сохранен" in dummy.lead_status_var.value


def test_save_lead_payload_clears_pending_reply_after_storage_write():
    calls = []

    class FakeStorage:
        def update_lead_proposal(self, *args, **kwargs):
            calls.append((args, kwargs))

    lead = Lead(
        id=24,
        post_id=10,
        score=82,
        summary="Задача: Исправить форму",
        draft_reply="Старый",
        contact="https://kwork.ru/projects/24/view",
        status="emailed",
        post_url="https://kwork.ru/projects/24/view",
    )
    dummy = type(
        "DummyGui",
        (),
        {"pending_replies": {24: "Новый текст"}, "_storage": lambda self: FakeStorage()},
    )()

    LeadFunnelGui._save_lead_payload(
        dummy,
        lead,
        {"reply": "Новый текст", "title": "Исправить форму", "price": 3000, "days": 2},
    )

    assert calls
    assert dummy.pending_replies == {}


def test_regeneration_worker_only_applies_pending_draft_without_sending_or_storage(monkeypatch):
    import app.gui as gui

    class Text:
        def __init__(self):
            self.value = ""

        def delete(self, *_args):
            self.value = ""

        def insert(self, _index, value):
            self.value = value

    class Value:
        def __init__(self):
            self.value = ""

        def set(self, value):
            self.value = value

    class Root:
        def after(self, _delay, callback):
            callback()

    class Button:
        def config(self, **kwargs):
            self.kwargs = kwargs

    dummy = type(
        "DummyGui",
        (),
        {
            "root": Root(),
            "current_lead_id": 25,
            "pending_replies": {},
            "reply_text": Text(),
            "lead_status_var": Value(),
            "regenerate_reply_button": Button(),
            "reply_regeneration_in_flight": True,
            "write_log": lambda self, _text: None,
            "_apply_regenerated_reply": lambda self, lead_id, reply: LeadFunnelGui._apply_regenerated_reply(
                self, lead_id, reply
            ),
            "_finish_reply_regeneration": lambda self: LeadFunnelGui._finish_reply_regeneration(self),
        },
    )()
    context = _reply_context_from_lead(
        Lead(
            id=25,
            post_id=11,
            score=82,
            summary="Задача: Исправить форму",
            draft_reply="Старый текст",
            contact="https://kwork.ru/projects/25/view",
            status="emailed",
            post_url="https://kwork.ru/projects/25/view",
        ),
        title="Исправить форму",
        days=2,
        attachments=[],
    )
    monkeypatch.setattr(gui, "compose_customer_reply", lambda *args, **kwargs: "Новый текст без цены.")

    LeadFunnelGui._regenerate_reply_thread(dummy, 25, context, "Старый текст", "sk-test", "deepseek-chat")

    assert dummy.pending_replies == {25: "Новый текст без цены."}
    assert dummy.reply_text.value == "Новый текст без цены."
    assert dummy.reply_regeneration_in_flight is False
    assert dummy.regenerate_reply_button.kwargs == {"state": "normal"}


def test_build_script_command_uses_cmd_runner(tmp_path):
    script = tmp_path / "start-kwork-browser.cmd"
    script.write_text("@echo off", encoding="utf-8")

    command = build_script_command(script)

    assert command == ["cmd", "/c", str(script)]


def test_terminal_launcher_forces_utf8_for_russian_logs():
    launcher = (Path(__file__).resolve().parents[1] / "lead-funnel.cmd").read_text(encoding="utf-8")

    assert 'set "PYTHONIOENCODING=utf-8"' in launcher
    assert "PYTHONUTF8" not in launcher


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
        proposal_title="Сохраненное название заказа",
        proposal_price_rub=12000,
        proposal_days=5,
    )

    assert _extract_price(lead) == 12000
    assert _extract_days(lead) == 5
    assert _lead_title(lead) == "Сохраненное название заказа"
    assert _parse_optional_int(" 12 000 ", "Цена") == 12000
    assert _parse_optional_int("", "Цена") is None


def test_parse_optional_int_rejects_negative_values():
    with pytest.raises(ValueError, match="больше 0"):
        _parse_optional_int("-1", "Цена")


def test_kwork_price_limit_reads_maximum_from_live_form_error():
    assert _kwork_price_limit("Стоимость может быть не более 3 000 руб.") == 3000
    assert _kwork_price_limit("Kwork reply field was not found") is None


def test_post_title_uses_kwork_card_heading():
    assert _post_title("📌 Правки формы заявки\nОсталось: 2 д.\nПредложений: 1") == "Правки формы заявки"


def test_restore_selected_rejection_only_clears_rejection_mark():
    class Table:
        def selection(self):
            return ("rejection-7",)

    class Storage:
        def __init__(self):
            self.cleared = []

        def clear_post_rejection(self, post_id):
            self.cleared.append(post_id)

    class Value:
        def __init__(self):
            self.value = ""

        def set(self, value):
            self.value = value

    rejection = PostRejection(
        post_id=7,
        channel="kwork-web",
        message_id=123,
        post_url="https://kwork.ru/projects/123/view",
        post_text="📌 Правки формы заявки\nПредложений: 1",
        posted_at="2026-07-18 10:00:00",
        reason="AI: сложнее недельного лимита",
        rejected_at="2026-07-18 10:02:00",
    )
    storage = Storage()
    logs = []
    refreshed = []
    dummy = SimpleNamespace(
        rejections_table=Table(),
        rejection_rows={"rejection-7": rejection},
        _storage=lambda: storage,
        status_var=Value(),
        write_log=logs.append,
        refresh_rejections=lambda: refreshed.append(True),
    )

    LeadFunnelGui.restore_selected_rejection(dummy)

    assert storage.cleared == [7]
    assert "Правки формы заявки" in dummy.status_var.value
    assert logs == ["Заказ 7 возвращен в проверку.\n"]
    assert refreshed == [True]


def test_apply_kwork_price_limit_only_updates_the_editable_price_field():
    class Value:
        def __init__(self):
            self.value = "5000"
            self.values = []

        def set(self, value):
            self.value = value
            self.values.append(value)

    lead = Lead(
        id=29,
        post_id=12,
        score=80,
        summary="Правка формы",
        draft_reply="Здравствуйте! Исправлю форму и проверю отправку.",
        contact="https://kwork.ru/projects/29/view",
        status="emailed",
        post_url="https://kwork.ru/projects/29/view",
    )
    logs = []
    dummy = SimpleNamespace(
        _selected_lead=lambda: lead,
        kwork_price_limits={29: 3000},
        lead_price_var=Value(),
        lead_status_var=Value(),
        write_log=logs.append,
    )

    LeadFunnelGui.apply_kwork_price_limit(dummy)

    assert dummy.lead_price_var.value == "3000"
    assert "3 000 руб." in dummy.lead_status_var.value
    assert logs == ["Лид #29: в поле цены подставлен максимум Kwork 3000 руб.\n"]


def test_gui_prevents_duplicate_one_time_action_and_reenables_its_button():
    class Button:
        def __init__(self):
            self.configured = []

        def config(self, **kwargs):
            self.configured.append(kwargs)

    button = Button()
    logs = []
    dummy = SimpleNamespace(
        running_once_actions=set(),
        once_action_buttons={"Сканирование": button},
        write_log=logs.append,
    )

    assert LeadFunnelGui._begin_once_action(dummy, "Сканирование") is True
    assert LeadFunnelGui._begin_once_action(dummy, "Сканирование") is False
    LeadFunnelGui._finish_once_action(dummy, "Сканирование")

    assert button.configured == [{"state": "disabled"}, {"state": "normal"}]
    assert dummy.running_once_actions == set()
    assert logs == ["Сканирование уже выполняется.\n"]


def test_gui_payload_removes_price_from_manually_edited_reply():
    class Value:
        def __init__(self, value):
            self.value = value

        def get(self):
            return self.value

    class Text:
        def get(self, *_args):
            return (
                "Здравствуйте! Исправлю форму за 3 дня, цена 9000 руб. "
                "Проверю текущую отправку, внесу правки и протестирую результат."
            )

    lead = Lead(
        id=13,
        post_id=4,
        score=80,
        summary="Срок: 3 дн.\nЦена: 9000 руб.\nЗадача: Исправить форму заявки",
        draft_reply="Старый отклик",
        contact="https://kwork.ru/projects/2",
        status="emailed",
        post_url="https://kwork.ru/projects/2",
        proposal_price_rub=9000,
        proposal_days=3,
    )
    dummy = type(
        "DummyGui",
        (),
        {
            "reply_text": Text(),
            "lead_title_var": Value("Исправить форму заявки"),
            "lead_price_var": Value("9000"),
            "lead_days_var": Value("3"),
        },
    )()

    payload = LeadFunnelGui._lead_payload(dummy, lead)

    assert "9000" not in payload["reply"]
    assert "руб" not in payload["reply"].lower()
    assert payload["price"] == 9000
    assert payload["days"] == 3


def test_gui_payload_requires_order_title():
    class Value:
        def __init__(self, value):
            self.value = value

        def get(self):
            return self.value

    class Text:
        def get(self, *_args):
            return "Здравствуйте! Проверю форму и внесу нужные правки."

    lead = Lead(
        id=14,
        post_id=5,
        score=80,
        summary="",
        draft_reply="Старый отклик",
        contact="https://kwork.ru/projects/3",
        status="emailed",
        post_url="https://kwork.ru/projects/3",
    )
    dummy = type(
        "DummyGui",
        (),
        {
            "reply_text": Text(),
            "lead_title_var": Value(""),
            "lead_price_var": Value("9000"),
            "lead_days_var": Value("3"),
        },
    )()

    with pytest.raises(ValueError, match="Название заказа обязательно"):
        LeadFunnelGui._lead_payload(dummy, lead)


def test_format_datetime_displays_moscow_time():
    assert _format_datetime("2026-05-04T07:30:00+00:00") == "04.05 10:30 МСК"
    assert _format_datetime("2026-05-04T10:30:00+03:00") == "04.05 10:30 МСК"
    assert _format_datetime("2026-05-04 10:30:00") == "04.05 10:30 МСК"


def test_storage_datetime_is_converted_from_utc_to_moscow_time():
    assert _format_storage_datetime("2026-07-18 00:04:25") == "18.07 03:04 МСК"


def test_active_queue_keeps_recent_kwork_and_sqlite_leads_but_hides_archive():
    fresh_sqlite = Lead(
        id=1,
        post_id=1,
        score=70,
        summary="",
        draft_reply="",
        contact="https://kwork.ru/projects/1/view",
        status="emailed",
        post_url="https://kwork.ru/projects/1/view",
        created_at="2026-07-17 23:40:00",
    )
    fresh_kwork = Lead(
        id=2,
        post_id=2,
        score=70,
        summary="",
        draft_reply="",
        contact="https://kwork.ru/projects/2/view",
        status="emailed",
        post_url="https://kwork.ru/projects/2/view",
        posted_at="2026-07-18 02:30:00",
        created_at="2026-06-01 00:00:00",
    )
    archived = Lead(
        id=3,
        post_id=3,
        score=70,
        summary="",
        draft_reply="",
        contact="https://kwork.ru/projects/3/view",
        status="emailed",
        post_url="https://kwork.ru/projects/3/view",
        created_at="2026-07-16 00:00:00",
    )

    visible = filter_active_leads(
        [fresh_sqlite, fresh_kwork, archived],
        max_age_hours=24,
        now=datetime(2026, 7, 18, 0, 10, tzinfo=timezone.utc),
    )

    assert [lead.id for lead in visible] == [1, 2]


def test_batch_live_check_uses_only_active_unsent_leads():
    fresh = Lead(
        id=1,
        post_id=1,
        score=70,
        summary="",
        draft_reply="",
        contact="https://kwork.ru/projects/1/view",
        status="emailed",
        post_url="https://kwork.ru/projects/1/view",
        created_at="2026-07-17 23:40:00",
    )
    already_sent = Lead(
        id=2,
        post_id=2,
        score=70,
        summary="",
        draft_reply="",
        contact="https://kwork.ru/projects/2/view",
        status="sent",
        post_url="https://kwork.ru/projects/2/view",
        created_at="2026-07-17 23:45:00",
    )
    archived = Lead(
        id=3,
        post_id=3,
        score=70,
        summary="",
        draft_reply="",
        contact="https://kwork.ru/projects/3/view",
        status="emailed",
        post_url="https://kwork.ru/projects/3/view",
        created_at="2026-07-16 00:00:00",
    )

    selected = select_leads_for_live_check(
        [fresh, already_sent, archived],
        max_age_hours=24,
        limit=10,
        now=datetime(2026, 7, 18, 0, 10, tzinfo=timezone.utc),
    )

    assert [lead.id for lead in selected] == [1]


def test_scan_and_approval_processes_trigger_lead_refresh():
    assert _should_refresh_after_process("Сканирование")
    assert _should_refresh_after_process("Проверка почты")
    assert not _should_refresh_after_process("Kwork Chrome")


def test_gui_shows_process_error_when_background_command_fails(monkeypatch):
    import app.gui as gui_module

    class Root:
        def after(self, _delay, callback):
            callback()

    class Value:
        def __init__(self):
            self.values = []

        def set(self, value):
            self.values.append(value)

    class Process:
        returncode = 2

    status = Value()
    logs = []
    gui = SimpleNamespace(
        root=Root(),
        status_var=status,
        write_log=logs.append,
        _stream_process=lambda _process, _label: None,
        refresh_leads=lambda: None,
    )
    monkeypatch.setattr(gui_module.subprocess, "Popen", lambda *args, **kwargs: Process())

    LeadFunnelGui._run_once_thread(gui, ["broken-command"], {}, "Сканирование")

    assert status.values[-1] == "Сканирование: ошибка (код 2)"
    assert "кодом 2" in logs[-1]


def test_direct_send_confirmation_names_order_and_kwork_terms():
    lead = Lead(
        id=19,
        post_id=7,
        score=82,
        summary="Доработать форму",
        draft_reply="Здравствуйте! Исправлю форму и проверю отправку.",
        contact="https://kwork.ru/projects/19/view",
        status="emailed",
        post_url="https://kwork.ru/projects/19/view",
    )

    message = direct_send_confirmation(
        lead,
        {"title": "Доработать форму заявки", "price": 12000, "days": 3},
    )

    assert "Доработать форму заявки" in message
    assert "12 000" in message
    assert "3 дн." in message
    assert "Kwork" in message


def test_direct_send_blocks_already_sent_lead():
    lead = Lead(
        id=20,
        post_id=8,
        score=82,
        summary="Лендинг",
        draft_reply="Здравствуйте! Сделаю лендинг.",
        contact="https://kwork.ru/projects/20/view",
        status="sent",
        post_url="https://kwork.ru/projects/20/view",
        sent_at="2026-05-04 10:45:12",
    )

    assert lead_send_block_reason(lead, in_flight_lead_ids=set()) == "Отклик по этому лиду уже отправлен."


def test_direct_send_blocks_second_click_while_first_send_is_running():
    lead = Lead(
        id=21,
        post_id=9,
        score=82,
        summary="Лендинг",
        draft_reply="Здравствуйте! Сделаю лендинг.",
        contact="https://kwork.ru/projects/21/view",
        status="emailed",
        post_url="https://kwork.ru/projects/21/view",
    )

    assert lead_send_block_reason(lead, in_flight_lead_ids={21}) == "Отправка этого лида уже выполняется."


def test_direct_send_blocks_lead_that_live_kwork_check_already_put_over_limit():
    lead = Lead(
        id=22,
        post_id=10,
        score=82,
        summary="Лендинг",
        draft_reply="Здравствуйте! Сделаю лендинг.",
        contact="https://kwork.ru/projects/22/view",
        status="emailed",
        post_url="https://kwork.ru/projects/22/view",
        live_response_count=8,
        live_checked_at="2026-07-18 00:04:25",
    )

    assert "8" in lead_send_block_reason(lead, in_flight_lead_ids=set(), max_responses=5)


def test_lead_table_marks_live_kwork_response_limit_exceeded():
    lead = Lead(
        id=23,
        post_id=11,
        score=82,
        summary="Лендинг",
        draft_reply="Здравствуйте!",
        contact="https://kwork.ru/projects/23/view",
        status="emailed",
        post_url="https://kwork.ru/projects/23/view",
        live_response_count=9,
    )

    assert "over_limit" in _lead_row_tags(lead, max_responses=5)


def test_lead_status_summary_keeps_action_error_after_list_refresh():
    lead = Lead(
        id=28,
        post_id=11,
        score=82,
        summary="Доработать форму",
        draft_reply="Здравствуйте! Исправлю форму.",
        contact="https://kwork.ru/projects/28/view",
        status="emailed",
        post_url="https://kwork.ru/projects/28/view",
    )

    status = lead_status_summary(lead, pending_reply=False, action_error="Стоимость может быть не более 3 000 руб.")

    assert "Лид #28" in status
    assert "ошибка: Стоимость может быть не более 3 000 руб." in status


def test_gui_live_project_check_persists_current_kwork_count(monkeypatch, tmp_path):
    import app.gui as gui_module
    import app.kwork_client as kwork_client_module

    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    post_id = storage.save_post(
        channel="kwork-web",
        message_id=29,
        post_url="https://kwork.ru/projects/29/view",
        text="Предложений: 2",
        posted_at="2026-05-04T10:00:00+03:00",
    )
    lead_id = storage.create_lead(
        post_id=post_id,
        score=82,
        summary="Правки",
        draft_reply="Здравствуйте!",
        contact="https://kwork.ru/projects/29/view",
    )
    lead = storage.get_lead(lead_id)

    class Client:
        def __init__(self, **_kwargs):
            pass

        def inspect(self, _contact):
            return SimpleNamespace(response_count=7, reason="выше лимита")

    monkeypatch.setattr(kwork_client_module, "KworkProjectClient", Client)
    monkeypatch.setattr(
        gui_module,
        "load_config",
        lambda: SimpleNamespace(
            kwork_cookie="",
            kwork_use_browser=True,
            kwork_cdp_url="http://127.0.0.1:9222",
            kwork_browser_profile_dir="",
        ),
    )
    gui = SimpleNamespace(_storage=lambda: storage, _kwork_project_client=lambda: Client())

    result = LeadFunnelGui._refresh_lead_live_status(gui, lead)

    refreshed = storage.get_lead(lead_id)
    assert result == "Kwork responses: 7"
    assert refreshed.live_response_count == 7
    assert refreshed.live_reason == "выше лимита"


def test_gui_batch_live_check_updates_each_selected_lead_without_sending(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    lead_ids = []
    for message_id in (30, 31):
        post_id = storage.save_post(
            channel="kwork-web",
            message_id=message_id,
            post_url=f"https://kwork.ru/projects/{message_id}/view",
            text="Предложений: 1",
            posted_at="2026-07-18T02:30:00+03:00",
        )
        lead_ids.append(
            storage.create_lead(
                post_id=post_id,
                score=82,
                summary="Правки",
                draft_reply="Здравствуйте!",
                contact=f"https://kwork.ru/projects/{message_id}/view",
            )
        )

    class Client:
        def inspect(self, contact):
            return SimpleNamespace(response_count=5 if contact.endswith("30/view") else 8, reason="")

    finished = []

    class Root:
        def after(self, _delay, callback):
            callback()

    gui = SimpleNamespace(
        _kwork_project_client=lambda: Client(),
        _storage=lambda: storage,
        write_log=lambda _text: None,
        root=Root(),
        _finish_fresh_live_check=lambda checked, unreadable, error="": finished.append((checked, unreadable, error)),
    )

    LeadFunnelGui._check_fresh_leads_thread(gui, [storage.get_lead(lead_id) for lead_id in lead_ids])

    assert [storage.get_lead(lead_id).live_response_count for lead_id in lead_ids] == [5, 8]
    assert [storage.get_lead(lead_id).status for lead_id in lead_ids] == ["new", "new"]
    assert finished == [(2, 0, "")]


def test_gui_direct_send_blocks_stale_reply_with_unsupported_task_action(monkeypatch):
    import app.gui as gui_module

    lead = Lead(
        id=22,
        post_id=10,
        score=82,
        summary="Задача: Посадить каталог на WordPress",
        draft_reply="Старый черновик",
        contact="https://kwork.ru/projects/22/view",
        status="emailed",
        post_url="https://kwork.ru/projects/22/view",
        post_text="Посадить информационную страницу и каталог по PSD на WordPress.",
    )
    payload = {
        "reply": (
            "Здравствуйте! Посмотрел задачу по посадке сайта и каталога на WordPress. "
            "Сначала проверю текущую отправку формы и валидацию на мобильных, затем внесу нужные правки в разметку и стили. "
            "После изменений протестирую сценарий на телефоне и в основных браузерах, чтобы заявки стабильно доходили. "
            "На работу ориентируюсь на 5 дн., могу приступить сразу."
        ),
        "price": 12000,
        "days": 5,
        "title": "Настройка сайта и каталога на WordPress",
    }
    calls = []
    warnings = []

    class Value:
        def set(self, _value):
            return None

    dummy = SimpleNamespace(
        _selected_lead=lambda: lead,
        in_flight_lead_ids=set(),
        _lead_payload=lambda _lead: payload,
        _attachments_for_lead=lambda _lead: [],
        _save_lead_payload=lambda *_args: calls.append("save"),
        _run_lead_action=lambda *_args, **_kwargs: calls.append("send"),
        lead_status_var=Value(),
    )
    monkeypatch.setattr(
        gui_module.messagebox,
        "showwarning",
        lambda _title, message: warnings.append(message),
    )
    monkeypatch.setattr(
        gui_module.messagebox,
        "askyesno",
        lambda *_args, **_kwargs: pytest.fail("unsafe reply must not reach the confirmation dialog"),
    )

    LeadFunnelGui.send_selected_lead(dummy)

    assert calls == []
    assert warnings
    assert "не подтвержден" in warnings[0].lower()


def test_gui_direct_send_starts_submission_after_safe_reply(monkeypatch):
    import app.gui as gui_module

    lead = Lead(
        id=27,
        post_id=13,
        score=82,
        summary="Задача: Посадить каталог на WordPress",
        draft_reply="Старый черновик",
        contact="https://kwork.ru/projects/27/view",
        status="emailed",
        post_url="https://kwork.ru/projects/27/view",
        post_text="Посадить информационную страницу и каталог по PSD на WordPress.",
    )
    payload = {
        "reply": (
            "Здравствуйте! Посмотрел задачу по посадке информационной страницы и каталога на WordPress. "
            "Сверю структуру страниц и макеты PSD, затем соберу нужные разделы на WordPress. "
            "Проверю карточки товаров и отображение каталога на основных разрешениях, чтобы страницы работали корректно. "
            "Могу приступить сразу и покажу готовый рабочий вариант."
        ),
        "price": 12000,
        "days": 5,
        "title": "Настройка сайта и каталога на WordPress",
    }
    calls = []

    class Button:
        def __init__(self):
            self.configured = []

        def config(self, **kwargs):
            self.configured.append(kwargs)

    dummy = SimpleNamespace(
        _selected_lead=lambda: lead,
        in_flight_lead_ids=set(),
        _lead_payload=lambda _lead: payload,
        _attachments_for_lead=lambda _lead: [],
        _save_lead_payload=lambda *_args: calls.append("save"),
        _run_lead_action=lambda label, _action, **kwargs: calls.append((label, kwargs)),
        send_lead_button=Button(),
    )
    monkeypatch.setattr(gui_module.messagebox, "askyesno", lambda *_args, **_kwargs: True)

    LeadFunnelGui.send_selected_lead(dummy)

    assert dummy.in_flight_lead_ids == {27}
    assert dummy.send_lead_button.configured == [{"state": "disabled"}]
    assert calls[0] == "save"
    assert calls[1][0] == "Отправка лида #27"
    assert calls[1][1]["lead_id"] == 27


def test_gui_direct_send_submits_kwork_reply_and_marks_lead_sent():
    lead = Lead(
        id=22,
        post_id=10,
        score=82,
        summary="Лендинг",
        draft_reply="Здравствуйте! Сделаю лендинг.",
        contact="https://kwork.ru/projects/22/view",
        status="emailed",
        post_url="https://kwork.ru/projects/22/view",
    )
    sender_calls = []
    sent_marks = []

    class Sender:
        def send_reply(self, contact, text, *, price_rub, days, title, submit):
            sender_calls.append((contact, text, price_rub, days, title, submit))
            return "kwork-project-22"

    class Storage:
        def mark_sent(self, lead_id, contact, message_id):
            sent_marks.append((lead_id, contact, message_id))

    gui = SimpleNamespace(_sender=lambda: Sender(), _storage=lambda: Storage())
    payload = {
        "reply": "Здравствуйте! Возьму в работу лендинг и проверю форму.",
        "price": 12000,
        "days": 3,
        "title": "Сделать лендинг",
    }

    result = LeadFunnelGui._send_lead_now(gui, lead, payload)

    assert result == "kwork-project-22"
    assert sender_calls == [
        (
            "https://kwork.ru/projects/22/view",
            "Здравствуйте! Возьму в работу лендинг и проверю форму.",
            12000,
            3,
            "Сделать лендинг",
            True,
        )
    ]
    assert sent_marks == [(22, "https://kwork.ru/projects/22/view", "kwork-project-22")]


@pytest.mark.parametrize(
    ("mark_failed", "expected_failures"),
    [(False, []), (True, [(42, "Kwork reply field was not found")])],
)
def test_gui_marks_lead_failed_only_for_actual_submission_errors(mark_failed, expected_failures):
    failures = []

    class Root:
        def after(self, _delay, callback):
            callback()

    class Storage:
        def mark_failed(self, lead_id, error):
            failures.append((lead_id, error))

    class Value:
        def __init__(self):
            self.values = []

        def set(self, value):
            self.values.append(value)

    def fail_action():
        raise RuntimeError("Стоимость может быть не более 3 000 руб.")

    lead_status = Value()

    gui = SimpleNamespace(
        root=Root(),
        _storage=lambda: Storage(),
        write_log=lambda _text: None,
        status_var=Value(),
        lead_status_var=lead_status,
        current_lead_id=42,
        refresh_leads=lambda: None,
    )

    LeadFunnelGui._run_lead_action_thread(
        gui,
        "Заполнение лида #42",
        fail_action,
        lead_id=42,
        mark_failed=mark_failed,
    )

    assert failures == [
        (lead_id, error.replace("Kwork reply field was not found", "Стоимость может быть не более 3 000 руб."))
        for lead_id, error in expected_failures
    ]
    assert "Стоимость может быть не более 3 000 руб." in lead_status.values[-1]


def test_gui_keeps_current_lead_status_when_old_background_action_fails():
    class Value:
        def __init__(self):
            self.values = []

        def set(self, value):
            self.values.append(value)

    lead_status = Value()
    gui = SimpleNamespace(current_lead_id=43, lead_status_var=lead_status)

    LeadFunnelGui._show_lead_action_error(gui, 42, "Стоимость может быть не более 3 000 руб.")

    assert lead_status.values == []


def test_gui_names_mail_check_and_direct_submission_actions_clearly():
    source = (Path(__file__).resolve().parents[1] / "src" / "app" / "gui.py").read_text(encoding="utf-8")

    assert 'text="Проверить почту"' in source
    assert 'text="OK и отправить отклик"' in source
    assert "command=self.send_selected_lead" in source


def test_primary_lead_actions_are_created_before_long_lead_details():
    source = (Path(__file__).resolve().parents[1] / "src" / "app" / "gui.py").read_text(encoding="utf-8")

    assert source.index("buttons = ttk.Frame(frame)") < source.index("text_frame = ttk.Frame(frame)")


def test_monitoring_schedules_periodic_lead_refresh():
    source = (Path(__file__).resolve().parents[1] / "src" / "app" / "gui.py").read_text(encoding="utf-8")

    assert "self._schedule_watch_refresh()" in source
    assert "self.watch_refresh_after_id = self.root.after" in source
    assert "self._cancel_watch_refresh()" in source


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
        "04.05 10:30 МСК",
        4,
        "отправлен 04.05 13:45 МСК",
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


def test_lead_table_prefers_live_kwork_offer_count_and_shows_check_time():
    lead = Lead(
        id=19,
        post_id=8,
        score=70,
        summary="Задача: Исправить форму",
        draft_reply="Здравствуйте!",
        contact="https://kwork.ru/projects/19/view",
        status="emailed",
        post_url="https://kwork.ru/projects/19/view",
        post_text="Предложений: 2",
        live_response_count=8,
        live_checked_at="2026-07-18 02:45:00",
        live_reason="выше установленного лимита",
    )

    assert build_lead_row_values(lead)[2] == 8
    details = _lead_details_text(lead)
    assert "Проверка Kwork: 8 предложений, 18.07 05:45 МСК" in details
    assert "выше установленного лимита" in details


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


def test_text_selection_can_be_copied_to_clipboard():
    root = Tk()
    root.withdraw()
    try:
        widget = Text(root)
        widget.insert("1.0", "Данные заказа можно выделить и скопировать")
        widget.tag_add("sel", "1.0", "1.13")

        assert _copy_widget_selection_to_clipboard(widget, root) == "break"
        assert root.clipboard_get() == "Данные заказа"
    finally:
        root.destroy()


def test_lead_text_widgets_bind_copy_shortcuts():
    source = (Path(__file__).resolve().parents[1] / "src" / "app" / "gui.py").read_text(encoding="utf-8")

    assert "self._bind_copyable_text(self.summary_text)" in source
    assert "self._bind_copyable_text(self.reply_text)" in source
    assert "<Control-c>" in source
    assert "<Control-Insert>" in source


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
