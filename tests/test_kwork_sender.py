import pytest

from app.kwork_client import KworkProjectInfo, KworkProjectReplyabilityError
from app.kwork_sender import (
    KworkReplySender,
    ReplyTerms,
    _AUTO_LOGIN_SCRIPT,
    _extract_reply_terms,
    _form_fill_errors,
    _is_kwork_reply_destination,
    _login_required_message,
    _offer_url,
)


def test_extract_reply_terms_reads_price_and_days_from_human_reply():
    terms = _extract_reply_terms(
        "Здравствуйте! Сделаю за 4 дня. По цене ориентир 18 000 руб., начну сегодня."
    )

    assert terms.price_rub == 18000
    assert terms.days == 4


def test_extract_reply_terms_ignores_phone_like_numbers():
    terms = _extract_reply_terms(
        "Здравствуйте! Мой контакт +7 967 981 2438. Сделаю за 2 дня, цена 5000 руб."
    )

    assert terms.price_rub == 5000
    assert terms.days == 2


def test_login_required_message_detects_logged_out_kwork_page():
    page_text = "ФРИЛАНС МАРКЕТПЛЕЙС\nВход\nРегистрация\nПредложить услугу"

    assert _login_required_message(page_text, has_reply_field=False)


def test_login_required_message_allows_page_with_reply_field():
    page_text = "Вход\nРегистрация\nПредложить услугу"

    assert _login_required_message(page_text, has_reply_field=True) == ""


def test_wait_for_reply_field_reports_unavailable_kwork_project(monkeypatch):
    from app import kwork_source

    monkeypatch.setattr(
        kwork_source,
        "_evaluate",
        lambda ws, script: "СТРАНИЦА НЕ НАЙДЕНА" if "document.body" in script else False,
    )

    with pytest.raises(RuntimeError, match="Kwork project is unavailable"):
        KworkReplySender(timeout_seconds=0.1)._wait_for_reply_field(object())


def test_direct_offer_does_not_fallback_when_project_is_unavailable(monkeypatch):
    from app import kwork_source
    from app.kwork_sender import KworkProjectUnavailableError

    monkeypatch.setattr(kwork_source, "_refresh_page", lambda ws, url, timeout: None)
    monkeypatch.setattr(
        KworkReplySender,
        "_wait_for_page_text",
        lambda self, ws: (_ for _ in ()).throw(KworkProjectUnavailableError("Kwork project is unavailable: page not found")),
    )

    with pytest.raises(RuntimeError, match="Kwork project is unavailable"):
        KworkReplySender()._try_open_direct_offer(object(), "https://kwork.ru/new_offer?project=3190074")


def test_kwork_reply_sender_keeps_autologin_credentials_in_memory_only():
    sender = KworkReplySender(login_email="me@example.com", login_password="secret")

    assert sender.login_email == "me@example.com"
    assert sender.login_password == "secret"


def test_auto_login_script_targets_email_password_and_submit_controls():
    assert "input[type=email]" in _AUTO_LOGIN_SCRIPT
    assert "input[type=password]" in _AUTO_LOGIN_SCRIPT
    assert "submit.click()" in _AUTO_LOGIN_SCRIPT


def test_reply_form_opener_supports_kwork_span_buttons():
    from app.kwork_sender import _FILL_AND_SUBMIT_SCRIPT, _HAS_REPLY_FIELD_SCRIPT, _OPEN_REPLY_FORM_SCRIPT

    assert ".kw-button" in _OPEN_REPLY_FORM_SCRIPT
    assert ".trumbowyg-editor" in _OPEN_REPLY_FORM_SCRIPT
    assert "оставить отзыв" in _OPEN_REPLY_FORM_SCRIPT
    assert ".trumbowyg-editor" in _HAS_REPLY_FIELD_SCRIPT
    assert ".trumbowyg-editor" in _FILL_AND_SUBMIT_SCRIPT
    assert "#offer-custom-price" in _FILL_AND_SUBMIT_SCRIPT
    assert "Введите название заказа" in _FILL_AND_SUBMIT_SCRIPT
    assert 'textarea[name="name"]' in _FILL_AND_SUBMIT_SCRIPT
    assert "messageEditor" in _FILL_AND_SUBMIT_SCRIPT
    assert "messageTextarea" in _FILL_AND_SUBMIT_SCRIPT
    assert "payload.title" in _FILL_AND_SUBMIT_SCRIPT
    assert "payload.submit" in _FILL_AND_SUBMIT_SCRIPT
    assert "input[type=tel]" in _FILL_AND_SUBMIT_SCRIPT
    assert "input[type=search]" in _FILL_AND_SUBMIT_SCRIPT
    assert "const fieldValue" in _FILL_AND_SUBMIT_SCRIPT
    assert "document.querySelectorAll('select')" in _FILL_AND_SUBMIT_SCRIPT
    assert "async (payload)" in _FILL_AND_SUBMIT_SCRIPT
    assert ".vs__dropdown-option" in _FILL_AND_SUBMIT_SCRIPT
    assert "duration-select__selected-option" in _FILL_AND_SUBMIT_SCRIPT
    assert "input-style--error" in _FILL_AND_SUBMIT_SCRIPT
    assert "priceErrorText" in _FILL_AND_SUBMIT_SCRIPT
    assert "Стоимость может быть не более" in _FILL_AND_SUBMIT_SCRIPT
    assert ".duration-select__selected-option')" in _FILL_AND_SUBMIT_SCRIPT
    assert "|| durationWidget?.querySelector('.vs__selected')" in _FILL_AND_SUBMIT_SCRIPT


def test_reply_field_detector_ignores_generic_kwork_header_inputs():
    from app.kwork_sender import _HAS_REPLY_FIELD_SCRIPT

    assert 'textarea[name="description"]' in _HAS_REPLY_FIELD_SCRIPT
    assert ".trumbowyg-editor" in _HAS_REPLY_FIELD_SCRIPT
    assert "input[type=search]" not in _HAS_REPLY_FIELD_SCRIPT
    assert "input:not([type])" not in _HAS_REPLY_FIELD_SCRIPT


def test_kwork_reply_sender_has_prepare_mode():
    sender = KworkReplySender()

    assert hasattr(sender, "prepare_reply")


def test_kwork_form_fill_validation_rejects_unfilled_required_terms():
    errors = _form_fill_errors(
        {
            "messageFilled": True,
            "titleFilled": False,
            "priceFilled": True,
            "daysFilled": False,
        },
        ReplyTerms(price_rub=3000, days=3),
        "Исправить форму заявки",
    )

    assert errors == ["название заказа", "срок выполнения"]


def test_kwork_form_fill_validation_keeps_legacy_mock_results_compatible():
    assert _form_fill_errors({"ok": True}, ReplyTerms(price_rub=3000, days=3), "Название") == []


def test_kwork_reply_sender_rejects_non_kwork_project_url():
    sender = KworkReplySender()

    with pytest.raises(ValueError, match="Kwork project URL"):
        sender.send_message("https://example.com/project/1", "Здравствуйте!")


def test_kwork_reply_sender_requires_price_and_deadline_before_opening_chrome():
    sender = KworkReplySender()

    with pytest.raises(ValueError, match="price and execution days"):
        sender.send_reply(
            "https://kwork.ru/projects/123/view",
            "Здравствуйте! Готов разобраться.",
            price_rub=None,
            days=None,
        )


def test_kwork_reply_sender_preflights_live_count_before_opening_reply_form(monkeypatch):
    from app import kwork_client, kwork_source

    chrome_actions = []

    class FakeProjectClient:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def inspect(self, url):
            return KworkProjectInfo(
                url=url,
                response_count=7,
                title="Лендинг",
                description="",
            )

    monkeypatch.setattr(kwork_client, "KworkProjectClient", FakeProjectClient)
    monkeypatch.setattr(
        kwork_source,
        "_ensure_chrome_cdp",
        lambda *args, **kwargs: chrome_actions.append("ensure"),
    )

    sender = KworkReplySender(max_responses=5)

    with pytest.raises(KworkProjectReplyabilityError, match=r"7.*5"):
        sender.send_message(
            "https://kwork.ru/projects/123/view",
            "Здравствуйте! Готов разобраться.",
            price_rub=3000,
            days=3,
        )

    assert chrome_actions == []


def test_kwork_reply_sender_passes_structured_terms_from_approval(monkeypatch):
    captured = {}

    def fake_send_reply(self, contact, text, **kwargs):
        captured["contact"] = contact
        captured["text"] = text
        captured.update(kwargs)
        return "kwork-project-123"

    monkeypatch.setattr(KworkReplySender, "send_reply", fake_send_reply)

    result = KworkReplySender().send_message(
        "https://kwork.ru/projects/123/view",
        "Здравствуйте! Готов разобраться в задаче.",
        price_rub=3000,
        days=3,
        title="Название заказа",
    )

    assert result == "kwork-project-123"
    assert captured == {
        "contact": "https://kwork.ru/projects/123/view",
        "text": "Здравствуйте! Готов разобраться в задаче.",
        "price_rub": 3000,
        "days": 3,
        "title": "Название заказа",
        "submit": True,
    }


def test_offer_url_targets_kwork_new_offer_page():
    assert _offer_url("https://kwork.ru/projects/3190074/view") == "https://kwork.ru/new_offer?project=3190074"


def test_kwork_reply_destination_recognizes_verified_redirect_after_submit():
    assert _is_kwork_reply_destination("https://kwork.ru/inbox")
    assert _is_kwork_reply_destination("https://kwork.ru/projects/3190074/view")
    assert not _is_kwork_reply_destination("https://kwork.ru/new_offer?project=3190074")


def test_kwork_reply_sender_uses_new_offer_page_for_reply_form(monkeypatch):
    from app import kwork_source

    calls = []
    expected_url = "https://kwork.ru/new_offer?project=3190074"

    class FakeWebSocket:
        def close(self):
            calls.append(("close", ""))

    monkeypatch.setattr(
        kwork_source,
        "_ensure_chrome_cdp",
        lambda cdp_url, url, profile_dir: calls.append(("ensure", url)),
    )
    monkeypatch.setattr(
        kwork_source,
        "_find_or_create_page",
        lambda cdp_url, url, tab_kind: calls.append(("find", url)) or {"webSocketDebuggerUrl": "ws://test"},
    )
    monkeypatch.setattr(
        kwork_source,
        "_refresh_page",
        lambda ws, url, timeout: calls.append(("refresh", url)),
    )
    monkeypatch.setattr(
        kwork_source,
        "_evaluate",
        lambda ws, script: "Предложить услугу\nФорма отклика" if "document.body" in script else True,
    )
    monkeypatch.setattr("app.kwork_sender.websocket.create_connection", lambda url, timeout: FakeWebSocket())
    monkeypatch.setattr(KworkReplySender, "_wait_for_page_text", lambda self, ws: None)
    monkeypatch.setattr(KworkReplySender, "_open_reply_form", lambda self, ws: None)
    monkeypatch.setattr(KworkReplySender, "_wait_for_reply_field", lambda self, ws: None)
    monkeypatch.setattr(KworkReplySender, "_project_title", lambda self, ws: "Название заказа")
    monkeypatch.setattr(KworkReplySender, "_fill_and_submit", lambda self, ws, text, terms, title, submit=True: {"ok": True})

    result = KworkReplySender().prepare_reply(
        "https://kwork.ru/projects/3190074/view",
        "Здравствуйте! Сделаю аккуратно.",
        price_rub=5000,
        days=3,
        title="Название заказа",
    )

    assert ("ensure", "https://kwork.ru/projects/3190074/view") in calls
    assert ("find", "https://kwork.ru/projects/3190074/view") in calls
    assert ("refresh", expected_url) in calls
    assert result == "kwork-project-3190074-prepared"


def test_kwork_reply_sender_reconnects_before_project_button_fallback(monkeypatch):
    from app import kwork_source

    sockets = []
    calls = []

    class FakeWebSocket:
        def __init__(self, index):
            self.index = index
            self.closed = False

        def close(self):
            self.closed = True

    def fake_connect(url, timeout):
        socket = FakeWebSocket(len(sockets) + 1)
        sockets.append(socket)
        return socket

    def fake_try_direct(self, ws, offer_url):
        ws.close()
        return False

    def fake_refresh(ws, url, timeout):
        if ws.closed:
            raise AssertionError("fallback reused a closed websocket")
        calls.append(("refresh", url, ws.index))

    monkeypatch.setattr(kwork_source, "_ensure_chrome_cdp", lambda cdp_url, url, profile_dir: None)
    monkeypatch.setattr(
        kwork_source,
        "_find_or_create_page",
        lambda cdp_url, url, tab_kind: {"webSocketDebuggerUrl": "ws://test"},
    )
    monkeypatch.setattr(kwork_source, "_refresh_page", fake_refresh)
    monkeypatch.setattr(
        kwork_source,
        "_evaluate",
        lambda ws, script: "Предложить услугу\nФорма отклика" if "document.body" in script else True,
    )
    monkeypatch.setattr("app.kwork_sender.websocket.create_connection", fake_connect)
    monkeypatch.setattr(KworkReplySender, "_try_open_direct_offer", fake_try_direct)
    monkeypatch.setattr(KworkReplySender, "_wait_for_page_text", lambda self, ws: None)
    monkeypatch.setattr(KworkReplySender, "_open_reply_form", lambda self, ws: None)
    monkeypatch.setattr(KworkReplySender, "_switch_to_offer_page", lambda self, ws, offer_url, known_page_ids=None: ws)
    monkeypatch.setattr(KworkReplySender, "_wait_for_reply_field", lambda self, ws: None)
    monkeypatch.setattr(KworkReplySender, "_project_title", lambda self, ws: "Название заказа")
    monkeypatch.setattr(KworkReplySender, "_fill_and_submit", lambda self, ws, text, terms, title, submit=True: {"ok": True})

    result = KworkReplySender().prepare_reply(
        "https://kwork.ru/projects/3190074/view",
        "Здравствуйте! Сделаю аккуратно.",
        price_rub=5000,
        days=3,
        title="Название заказа",
    )

    assert len(sockets) == 2
    assert calls == [("refresh", "https://kwork.ru/projects/3190074/view", 2)]
    assert result == "kwork-project-3190074-prepared"


def test_kwork_reply_sender_confirms_submit_and_waits_for_success(monkeypatch):
    from app import kwork_source

    events = []

    class FakeWebSocket:
        def close(self):
            events.append("close")

    monkeypatch.setattr(kwork_source, "_ensure_chrome_cdp", lambda cdp_url, url, profile_dir: None)
    monkeypatch.setattr(
        kwork_source,
        "_find_or_create_page",
        lambda cdp_url, url, tab_kind: {"webSocketDebuggerUrl": "ws://test"},
    )
    monkeypatch.setattr(
        kwork_source,
        "_evaluate",
        lambda ws, script: "Предложить услугу\nФорма отклика" if "document.body" in script else True,
    )
    monkeypatch.setattr("app.kwork_sender.websocket.create_connection", lambda url, timeout: FakeWebSocket())
    monkeypatch.setattr(KworkReplySender, "_try_open_direct_offer", lambda self, ws, offer_url: True)
    monkeypatch.setattr(KworkReplySender, "_project_title", lambda self, ws: "Название заказа")
    monkeypatch.setattr(
        KworkReplySender,
        "_fill_and_submit",
        lambda self, ws, text, terms, title, submit=True: events.append(("submit", submit)) or {"ok": True},
    )
    monkeypatch.setattr(KworkReplySender, "_confirm_after_submit", lambda self, ws: events.append("confirm"))
    monkeypatch.setattr(KworkReplySender, "_wait_after_submit", lambda self, ws: events.append("wait"))

    result = KworkReplySender().send_message(
        "https://kwork.ru/projects/3190074/view",
        "Здравствуйте! Сделаю аккуратно.",
        price_rub=5000,
        days=3,
    )

    assert result == "kwork-project-3190074"
    assert events[:3] == [("submit", True), "confirm", "wait"]


def test_wait_after_submit_raises_when_kwork_keeps_form_open(monkeypatch):
    from app import kwork_source

    monkeypatch.setattr(
        kwork_source,
        "_evaluate",
        lambda ws, script: "Предложить услугу\nОписание\nСтоимость\nНазвание заказа",
    )

    sender = KworkReplySender(timeout_seconds=0.1)

    with pytest.raises(RuntimeError, match="not confirmed as sent"):
        sender._wait_after_submit(object())


def test_wait_after_submit_does_not_treat_project_page_with_open_form_as_sent(monkeypatch):
    from app import kwork_source
    from app.kwork_sender import _HAS_REPLY_FIELD_SCRIPT

    project_url = "https://kwork.ru/projects/3190074/view"

    def fake_evaluate(_ws, script):
        if script == "location.href":
            return project_url
        if script == _HAS_REPLY_FIELD_SCRIPT:
            return True
        if "document.body" in script:
            return "Описание\nСтоимость\nНазвание заказа\nСрок выполнения"
        raise AssertionError(f"Unexpected script: {script}")

    monkeypatch.setattr(kwork_source, "_evaluate", fake_evaluate)

    with pytest.raises(RuntimeError, match="not confirmed as sent"):
        KworkReplySender(timeout_seconds=0.1)._wait_after_submit(object())


def test_confirmation_script_clicks_kwork_modal_confirmation():
    from app.kwork_sender import _CONFIRM_SUBMIT_SCRIPT

    assert "role=dialog" in _CONFIRM_SUBMIT_SCRIPT
    assert "подтверд" in _CONFIRM_SUBMIT_SCRIPT
    assert "верификац" in _CONFIRM_SUBMIT_SCRIPT
    assert "button.click()" in _CONFIRM_SUBMIT_SCRIPT


def test_switch_to_offer_page_fails_when_kwork_opens_new_inbox_tab(monkeypatch):
    from app import kwork_source

    class FakeWebSocket:
        def close(self):
            pass

    monkeypatch.setattr(
        kwork_source,
        "_evaluate",
        lambda ws, script: "https://kwork.ru/projects/3190074/view" if "location.href" in script else False,
    )
    monkeypatch.setattr(
        kwork_source,
        "_cdp_json",
        lambda cdp_url, path, timeout: [
            {"id": "old", "url": "https://kwork.ru/projects/3190074/view", "webSocketDebuggerUrl": "ws://old"},
            {"id": "new", "url": "https://kwork.ru/inbox/alex-key", "webSocketDebuggerUrl": "ws://new"},
        ],
    )

    sender = KworkReplySender(timeout_seconds=1)

    with pytest.raises(RuntimeError, match="inbox"):
        sender._switch_to_offer_page(
            FakeWebSocket(),
            "https://kwork.ru/new_offer?project=3190074",
            known_page_ids={"old"},
        )
