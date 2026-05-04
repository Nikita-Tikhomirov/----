from dataclasses import dataclass

from app.main import process_approvals, scan_once
from app.storage import Storage


@dataclass
class FakePost:
    channel: str
    message_id: int
    url: str
    text: str
    posted_at: str


class FakeTelegramClient:
    def __init__(self):
        self.sent = []

    def fetch_recent_posts(self):
        return [
            FakePost(
                channel="jobs",
                message_id=1,
                url="https://t.me/jobs/1",
                text=(
                    "Нужно сверстать лендинг HTML/CSS/JS, поправить форму. "
                    "Срок 1 день. Контакт @client_dev"
                ),
                posted_at="2026-05-04T10:00:00+03:00",
            )
        ]

    def send_message(self, contact, text):
        self.sent.append((contact, text))
        return "tg-message-1"


class FakeEmailClient:
    def __init__(self, approvals=None):
        self.sent_leads = []
        self.approvals = approvals or []

    def send_lead(self, lead):
        self.sent_leads.append(lead.id)
        return f"<lead-{lead.id}@example.com>"

    def fetch_approvals(self, seen_message_ids):
        return self.approvals


def test_scan_once_creates_lead_and_sends_email(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    email_client = FakeEmailClient()

    scan_once(
        storage=storage,
        telegram_client=FakeTelegramClient(),
        email_client=email_client,
    )

    leads = storage.list_leads(status="emailed")
    assert len(leads) == 1
    assert email_client.sent_leads == [leads[0].id]


def test_process_approvals_sends_only_approved_once(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    post_id = storage.save_post(
        channel="jobs",
        message_id=1,
        post_url="https://t.me/jobs/1",
        text="Нужно сверстать лендинг HTML/CSS/JS. Контакт @client_dev",
        posted_at="2026-05-04T10:00:00+03:00",
    )
    lead_id = storage.create_lead(
        post_id=post_id,
        score=82,
        summary="HTML/CSS лендинг",
        draft_reply="Здравствуйте! Готов помочь с лендингом.",
        contact="@client_dev",
    )
    storage.mark_lead_emailed(lead_id, "<lead@example.com>")
    telegram_client = FakeTelegramClient()
    email_client = FakeEmailClient(approvals=[(lead_id, "<approval@example.com>")])

    process_approvals(
        storage=storage,
        telegram_client=telegram_client,
        email_client=email_client,
    )
    process_approvals(
        storage=storage,
        telegram_client=telegram_client,
        email_client=email_client,
    )

    assert telegram_client.sent == [
        ("@client_dev", "Здравствуйте! Готов помочь с лендингом.")
    ]
    assert storage.get_lead(lead_id).status == "sent"
