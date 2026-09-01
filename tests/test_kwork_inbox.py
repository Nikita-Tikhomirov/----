from __future__ import annotations

import json
from pathlib import Path

import app.kwork_inbox as kwork_inbox_module

from app.kwork_inbox import (
    InboxConversation,
    InboxMessage,
    InboxPreview,
    KworkInboxClient,
    KworkInboxService,
    parse_conversation_previews,
)
from app.storage import Storage


def _sent_lead(storage: Storage, project_id: int = 123):
    post_id = storage.save_post(
        "kwork-web",
        project_id,
        f"https://kwork.ru/projects/{project_id}/view",
        "📌 Исправить форму WordPress\nНужно починить отправку формы и проверить результат.",
        "2026-09-01T07:00:00+00:00",
    )
    lead_id = storage.create_lead(
        post_id,
        90,
        "Небольшая правка формы WordPress",
        "Здравствуйте! Исправлю форму и проверю отправку.",
        f"https://kwork.ru/projects/{project_id}/view",
        proposal_title="Исправление формы WordPress",
        proposal_price_rub=2600,
        proposal_days=2,
    )
    storage.mark_sent(lead_id, f"https://kwork.ru/projects/{project_id}/view", f"kwork-project-{project_id}")
    return storage.get_lead_for_post(post_id)


class FakeInboxClient:
    def __init__(self, conversation: InboxConversation):
        self.conversation = conversation
        self.sent: list[tuple[str, str]] = []

    def list_incoming_previews(self) -> list[InboxPreview]:
        return [
            InboxPreview(
                username=self.conversation.username,
                preview=self.conversation.messages[-1].text,
                date_label="10:05",
            )
        ]

    def load_conversation(self, username: str) -> InboxConversation:
        assert username == self.conversation.username
        return self.conversation

    def send_reply(self, username: str, text: str) -> str:
        self.sent.append((username, text))
        return f"kwork-inbox-{username}-verified"


class FakeWebSocket:
    def close(self) -> None:
        pass


def test_inbox_client_owns_a_dedicated_tab_instead_of_reusing_user_chat(monkeypatch):
    existing_user_tab = {
        "id": "user-chat",
        "type": "page",
        "url": "https://kwork.ru/inbox/mashtc",
        "webSocketDebuggerUrl": "ws://user-chat",
    }
    monitor_tab = {
        "id": "monitor-chat",
        "type": "page",
        "url": "https://kwork.ru/inbox",
        "webSocketDebuggerUrl": "ws://monitor-chat",
    }
    created = False
    create_calls = 0

    def fake_cdp_json(_cdp_url, path, timeout):
        assert timeout in {5, 10}
        if path == "/json/version":
            return {"webSocketDebuggerUrl": "ws://browser"}
        if path == "/json/list":
            return [existing_user_tab, monitor_tab] if created else [existing_user_tab]
        raise AssertionError(f"Unexpected CDP path: {path}")

    def fake_send_cdp(_ws, method, params):
        nonlocal created, create_calls
        assert method == "Target.createTarget"
        assert params == {"url": "https://kwork.ru/inbox"}
        created = True
        create_calls += 1
        return {"result": {"targetId": "monitor-chat"}}

    monkeypatch.setattr(kwork_inbox_module, "_ensure_chrome_cdp", lambda *_args: None)
    monkeypatch.setattr(kwork_inbox_module, "_cdp_json", fake_cdp_json)
    monkeypatch.setattr(kwork_inbox_module, "_send_cdp", fake_send_cdp)
    monkeypatch.setattr(
        kwork_inbox_module.websocket,
        "create_connection",
        lambda *_args, **_kwargs: FakeWebSocket(),
    )

    client = KworkInboxClient()

    assert client._inbox_page()["id"] == "monitor-chat"
    assert client._inbox_page()["id"] == "monitor-chat"
    assert create_calls == 1


def test_parse_conversation_previews_keeps_only_current_incoming_messages():
    previews = parse_conversation_previews(
        [
            {"username": "new-client", "preview": "Когда сможете начать?", "date_label": "10:05", "has_outgoing_status": False},
            {"username": "answered", "preview": "Вы: Могу начать сегодня.", "date_label": "10:04", "has_outgoing_status": True},
            {"username": "old-client", "preview": "Есть вопрос", "date_label": "Вчера", "has_outgoing_status": False},
            {"username": "support", "preview": "Уведомление", "date_label": "10:03", "has_outgoing_status": False},
        ]
    )

    assert previews == [InboxPreview(username="new-client", preview="Когда сможете начать?", date_label="10:05")]


def test_inbox_client_keeps_attachment_only_messages(monkeypatch):
    payload = {
        "project_url": "",
        "project_title": "",
        "messages": [
            {
                "author": "customer",
                "text": "",
                "time_label": "10:05",
                "attachments": [
                    {
                        "label": "ТЗ.docx",
                        "url": "https://kwork.ru/files/uploaded/tz.docx",
                        "size_label": "12 Кб",
                    }
                ],
            }
        ],
    }
    client = KworkInboxClient()
    monkeypatch.setattr(client, "_inbox_page", lambda: {"webSocketDebuggerUrl": "ws://monitor"})
    monkeypatch.setattr(client, "_navigate_to_conversation", lambda *_args: None)
    monkeypatch.setattr(client, "_wait_for", lambda *_args: None)
    monkeypatch.setattr(kwork_inbox_module.websocket, "create_connection", lambda *_args, **_kwargs: FakeWebSocket())
    monkeypatch.setattr(kwork_inbox_module, "_evaluate", lambda *_args: json.dumps(payload, ensure_ascii=False))

    conversation = client.load_conversation("customer")

    assert len(conversation.messages) == 1
    assert conversation.messages[0].text == ""
    assert len(conversation.messages[0].attachments) == 1
    assert conversation.messages[0].attachments[0].label == "ТЗ.docx"
    assert conversation.messages[0].attachments[0].url.endswith("/tz.docx")


def test_inbox_service_replies_once_to_a_message_for_a_sent_project(tmp_path: Path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    lead = _sent_lead(storage)
    assert lead is not None
    conversation = InboxConversation(
        username="customer",
        project_id=123,
        project_title="Исправить форму WordPress",
        messages=(
            InboxMessage(author="stithc92", text=lead.draft_reply, time_label="10:00"),
            InboxMessage(author="customer", text="Когда сможете начать?", time_label="10:05"),
        ),
    )
    client = FakeInboxClient(conversation)
    composed: list[tuple[InboxConversation, int]] = []

    def compose(current: InboxConversation, current_lead):
        composed.append((current, current_lead.id))
        return "Могу начать сегодня. Прикрепите, пожалуйста, доступы к сайту в заказе."

    service = KworkInboxService(storage, client, compose)

    assert service.process_once() == 1
    assert service.process_once() == 0
    assert client.sent == [
        ("customer", "Могу начать сегодня. Прикрепите, пожалуйста, доступы к сайту в заказе.")
    ]
    assert composed == [(conversation, lead.id)]


def test_inbox_service_replies_once_to_a_direct_conversation(tmp_path: Path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    conversation = InboxConversation(
        username="direct-customer",
        project_id=None,
        project_title="",
        messages=(
            InboxMessage(
                author="direct-customer",
                text="Сколько времени займёт настройка?",
                time_label="10:05",
            ),
        ),
    )
    client = FakeInboxClient(conversation)
    composed_with = []

    def compose(current: InboxConversation, lead):
        composed_with.append((current, lead))
        return "Обычно такая настройка занимает один рабочий день."

    service = KworkInboxService(storage, client, compose)

    assert service.process_once() == 1
    assert service.process_once() == 0
    assert client.sent == [
        ("direct-customer", "Обычно такая настройка занимает один рабочий день.")
    ]
    assert composed_with == [(conversation, None)]

    with storage._connect() as conn:
        row = conn.execute(
            "SELECT lead_id, project_id, status FROM kwork_inbox_messages"
        ).fetchone()
    assert row["lead_id"] is None
    assert row["project_id"] is None
    assert row["status"] == "sent"


def test_attachment_identity_participates_in_inbox_message_key():
    first = InboxMessage(
        author="customer",
        text="",
        time_label="10:05",
        attachments=(
            kwork_inbox_module.InboxAttachment(
                label="first.docx",
                url="https://kwork.ru/files/first.docx",
                size_label="12 Кб",
            ),
        ),
    )
    second = InboxMessage(
        author="customer",
        text="",
        time_label="10:05",
        attachments=(
            kwork_inbox_module.InboxAttachment(
                label="second.docx",
                url="https://kwork.ru/files/second.docx",
                size_label="12 Кб",
            ),
        ),
    )
    conversation = InboxConversation(
        username="customer",
        project_id=None,
        project_title="",
        messages=(first, second),
    )

    assert kwork_inbox_module._message_key(conversation, first) != kwork_inbox_module._message_key(
        conversation,
        second,
    )


def test_inbox_service_ignores_conversations_not_linked_to_a_sent_lead(tmp_path: Path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    conversation = InboxConversation(
        username="unknown",
        project_id=999,
        project_title="Неизвестный проект",
        messages=(InboxMessage(author="unknown", text="Здравствуйте", time_label="10:05"),),
    )
    client = FakeInboxClient(conversation)
    service = KworkInboxService(storage, client, lambda *_: "Ответ")

    assert service.process_once() == 0
    assert client.sent == []


def test_inbox_service_does_not_reply_when_the_latest_message_is_ours(tmp_path: Path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    _sent_lead(storage)
    conversation = InboxConversation(
        username="customer",
        project_id=123,
        project_title="Исправить форму WordPress",
        messages=(
            InboxMessage(author="customer", text="Когда сможете начать?", time_label="10:05"),
            InboxMessage(author="stithc92", text="Могу начать сегодня.", time_label="10:06"),
        ),
    )
    client = FakeInboxClient(conversation)
    service = KworkInboxService(storage, client, lambda *_: "Лишний ответ")

    assert service.process_once() == 0
    assert client.sent == []
