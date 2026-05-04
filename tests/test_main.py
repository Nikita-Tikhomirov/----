from dataclasses import dataclass

from app.main import process_approvals, process_order_reviews, scan_once, submit_order
from app.storage import Storage


@dataclass
class FakePost:
    channel: str
    message_id: int
    url: str
    text: str
    posted_at: str


class FakeTelegramClient:
    can_send_replies = True

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


class FakeOrderEmailClient(FakeEmailClient):
    def __init__(self, reviews=None):
        super().__init__()
        self.sent_orders = []
        self.reviews = reviews or []

    def send_order_for_approval(self, order):
        self.sent_orders.append((order.id, order.deliverable))
        return f"<order-{order.id}@example.com>"

    def fetch_order_reviews(self, seen_message_ids):
        return self.reviews


class ReadOnlyTelegramClient(FakeTelegramClient):
    can_send_replies = False

    def send_message(self, contact, text):
        raise AssertionError("read-only fallback must not send Telegram replies")


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


def test_process_approvals_skips_sending_in_read_only_fallback(tmp_path):
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

    sent = process_approvals(
        storage=storage,
        telegram_client=ReadOnlyTelegramClient(),
        email_client=FakeEmailClient(approvals=[(lead_id, "<approval@example.com>")]),
    )

    assert sent == 0
    assert storage.get_lead(lead_id).status == "emailed"


def test_submit_order_sends_for_approval_and_review_can_request_revision(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    order_id = storage.create_order(
        contact="@client_dev",
        title="Лендинг",
        brief="Сверстать HTML/CSS/JS лендинг",
    )
    email_client = FakeOrderEmailClient()

    submit_order(
        storage=storage,
        email_client=email_client,
        order_id=order_id,
        deliverable="Готовая ссылка: https://example.com",
    )

    assert email_client.sent_orders == [(order_id, "Готовая ссылка: https://example.com")]
    assert storage.get_order(order_id).status == "ready_for_approval"

    from app.email_client import OrderReviewCommand

    processed = process_order_reviews(
        storage=storage,
        email_client=FakeOrderEmailClient(
            reviews=[
                OrderReviewCommand(
                    order_id=order_id,
                    message_id="<fix@example.com>",
                    decision="revision",
                    notes="Поправить форму на мобильном",
                )
            ]
        ),
    )

    assert processed == 1
    assert storage.get_order(order_id).status == "revision_requested"


def test_process_order_reviews_marks_order_done_after_approval(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    order_id = storage.create_order(
        contact="@client_dev",
        title="Лендинг",
        brief="Сверстать HTML/CSS/JS лендинг",
    )
    storage.submit_order_for_approval(order_id, "Готовая ссылка: https://example.com")

    from app.email_client import OrderReviewCommand

    processed = process_order_reviews(
        storage=storage,
        email_client=FakeOrderEmailClient(
            reviews=[
                OrderReviewCommand(
                    order_id=order_id,
                    message_id="<done@example.com>",
                    decision="approved",
                    notes="",
                )
            ]
        ),
    )

    assert processed == 1
    assert storage.get_order(order_id).status == "done"
