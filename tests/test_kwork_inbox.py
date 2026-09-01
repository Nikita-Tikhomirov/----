from __future__ import annotations

from pathlib import Path

from app.kwork_inbox import (
    InboxConversation,
    InboxMessage,
    InboxPreview,
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
