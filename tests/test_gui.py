from pathlib import Path
from types import SimpleNamespace
from tkinter import Text, Tk

import pytest

from app.gui import (
    LeadFunnelGui,
    _lead_details_text,
    _attachment_row_values,
    _copy_widget_selection_to_clipboard,
    _fallback_attachments_from_summary,
    _extract_days,
    _extract_offer_count,
    _extract_price,
    _extract_remaining_time,
    _format_datetime,
    _lead_title,
    _parse_optional_int,
    _reply_context_from_lead,
    _should_refresh_after_process,
    direct_send_confirmation,
    lead_send_block_reason,
    build_lead_row_values,
    build_app_command,
    build_script_command,
    normalize_filter_settings,
    read_env_values,
    update_env_values,
)
from app.storage import Lead, LeadAttachment


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
        "отправлен 04.05 10:45 МСК",
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
