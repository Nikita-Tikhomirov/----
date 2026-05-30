from dataclasses import dataclass

from app.main import create_order_handoff, process_approvals, process_order_reviews, scan_once, submit_order
from app.ai_lead_judge import LeadJudgeResult
from app.kwork_client import KworkProjectInfo
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


class FakeKworkProjectClient:
    def __init__(self, response_count=3, reason="", page_text="", attachments=()):
        self.response_count = response_count
        self.reason = reason
        self.page_text = page_text
        self.attachments = attachments
        self.inspected = []

    def inspect(self, contact):
        self.inspected.append(contact)
        return KworkProjectInfo(
            url=contact,
            response_count=self.response_count,
            title="Kwork project",
            description="Детали задачи со страницы Kwork",
            page_text=self.page_text,
            attachments=tuple(self.attachments),
            reason=self.reason,
        )


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


def test_scan_once_skips_kwork_projects_with_too_many_responses(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    email_client = FakeEmailClient()

    created = scan_once(
        storage=storage,
        telegram_client=FakeTelegramClient(),
        email_client=email_client,
        kwork_project_client=FakeKworkProjectClient(response_count=7),
        kwork_max_responses=5,
    )

    assert created == 0
    assert storage.list_leads() == []
    assert email_client.sent_leads == []


def test_scan_once_skips_kwork_projects_without_response_count(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    email_client = FakeEmailClient()

    created = scan_once(
        storage=storage,
        telegram_client=FakeTelegramClient(),
        email_client=email_client,
        kwork_project_client=FakeKworkProjectClient(response_count=None, reason="нет workerCount"),
        kwork_max_responses=5,
    )

    assert created == 0
    assert storage.list_leads() == []
    assert email_client.sent_leads == []


def test_scan_once_uses_ai_judge_for_summary_reply_and_score(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    email_client = FakeEmailClient()

    def fake_judge(text, api_key="", model="deepseek-chat"):
        return LeadJudgeResult(
            accepted=True,
            decision="accept",
            score=88,
            complexity="medium",
            estimated_days=5,
            price_rub=18000,
            summary="Сделать калькулятор на сайте",
            reasons=["понятный результат"],
            risks=["нужно сверить формулы"],
            questions=["Формулы готовы?"],
            draft_reply="Здравствуйте! Сделаю калькулятор за 5 дней, цена 18000 руб.",
        )

    created = scan_once(
        storage=storage,
        telegram_client=FakeTelegramClient(),
        email_client=email_client,
        lead_judge=fake_judge,
        deepseek_api_key="sk-test",
    )

    assert created == 1
    lead = storage.list_leads(status="emailed")[0]
    assert lead.score == 88
    assert "AI: accept" in lead.summary
    assert "Срок: 5 дн." in lead.summary
    assert "Цена: 18000 руб." in lead.summary
    assert "понятный результат" in lead.summary
    assert "калькулятор" in lead.draft_reply


def test_scan_once_passes_kwork_page_details_and_attachments_to_ai_judge(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    email_client = FakeEmailClient()
    seen_texts = []

    def fake_judge(text, api_key="", model="deepseek-chat"):
        seen_texts.append(text)
        return LeadJudgeResult(
            accepted=True,
            decision="accept",
            score=90,
            complexity="medium",
            estimated_days=4,
            price_rub=20000,
            summary="Сделать сайт по ТЗ",
            reasons=["ТЗ приложено"],
            risks=["нужно прочитать вложение"],
            questions=[],
            draft_reply="Здравствуйте! Изучу приложенное ТЗ и сделаю сайт за 4 дня.",
        )

    scan_once(
        storage=storage,
        telegram_client=FakeTelegramClient(),
        email_client=email_client,
        kwork_project_client=FakeKworkProjectClient(
            response_count=2,
            page_text="Полное описание проекта со страницы",
            attachments=("ТЗ.pdf: https://kwork.ru/files/tz.pdf",),
        ),
        lead_judge=fake_judge,
    )

    assert "Полное описание проекта со страницы" in seen_texts[0]
    assert "ТЗ.pdf" in seen_texts[0]


def test_scan_once_passes_downloaded_attachment_text_to_ai_judge(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    email_client = FakeEmailClient()
    seen_texts = []

    def fake_judge(text, api_key="", model="deepseek-chat"):
        seen_texts.append(text)
        return LeadJudgeResult(
            accepted=True,
            decision="accept",
            score=91,
            complexity="medium",
            estimated_days=3,
            price_rub=15000,
            summary="Сделать сайт по ТЗ",
            reasons=["ТЗ прочитано"],
            risks=[],
            questions=[],
            draft_reply="Здравствуйте! Сделаю по ТЗ за 3 дня.",
        )

    def fake_attachment_context(attachments, cookie="", **kwargs):
        assert kwargs["use_browser"] is True
        assert kwargs["cdp_url"] == "http://127.0.0.1:9222"
        return "Attachment text: сделать форму, калькулятор и адаптив"

    scan_once(
        storage=storage,
        telegram_client=FakeTelegramClient(),
        email_client=email_client,
        kwork_project_client=FakeKworkProjectClient(
            response_count=1,
            attachments=("ТЗ.txt: https://kwork.ru/files/tz.txt",),
        ),
        lead_judge=fake_judge,
        attachment_context_builder=fake_attachment_context,
        kwork_use_browser=True,
        kwork_cdp_url="http://127.0.0.1:9222",
    )

    assert "Attachment text: сделать форму" in seen_texts[0]


def test_scan_once_includes_attachment_report_in_email_summary(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    email_client = FakeEmailClient()

    def fake_judge(text, api_key="", model="deepseek-chat"):
        return LeadJudgeResult(
            accepted=True,
            decision="accept",
            score=91,
            complexity="medium",
            estimated_days=3,
            price_rub=15000,
            summary="Сделать сайт по ТЗ",
            reasons=["ТЗ прочитано"],
            risks=[],
            questions=[],
            draft_reply="Здравствуйте! Сделаю по ТЗ за 3 дня.",
        )

    def fake_attachment_context(attachments, cookie="", **kwargs):
        return "ФАЙЛЫ/ТЗ:\n- ТЗ.zip\n  Статус: скачан, архив открыт\n  Кратко: внутри brief.txt, нужна форма"

    scan_once(
        storage=storage,
        telegram_client=FakeTelegramClient(),
        email_client=email_client,
        kwork_project_client=FakeKworkProjectClient(
            response_count=1,
            attachments=("ТЗ.zip: https://kwork.ru/files/tz.zip",),
        ),
        lead_judge=fake_judge,
        attachment_context_builder=fake_attachment_context,
    )

    lead = storage.list_leads()[0]
    assert "ФАЙЛЫ/ТЗ" in lead.summary
    assert "архив открыт" in lead.summary
    assert "внутри brief.txt" in lead.summary


def test_scan_once_skips_ai_rejected_lead(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    email_client = FakeEmailClient()

    def fake_judge(text, api_key="", model="deepseek-chat"):
        return LeadJudgeResult(
            accepted=False,
            decision="reject",
            score=20,
            complexity="too_complex",
            estimated_days=7,
            price_rub=0,
            summary="Сложная CRM",
            reasons=["больше недели"],
            risks=["высокий риск"],
            questions=[],
            draft_reply="",
        )

    created = scan_once(
        storage=storage,
        telegram_client=FakeTelegramClient(),
        email_client=email_client,
        lead_judge=fake_judge,
        deepseek_api_key="sk-test",
    )

    assert created == 0
    assert storage.list_leads() == []
    assert email_client.sent_leads == []


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


def test_create_order_handoff_writes_codex_task_file(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    order_id = storage.create_order(
        contact="@client_dev",
        title="Лендинг",
        brief="Сверстать HTML/CSS/JS лендинг",
    )

    handoff_path = create_order_handoff(
        storage=storage,
        order_id=order_id,
        output_dir=tmp_path / "handoffs",
    )

    assert handoff_path.name == "order-1-handoff.md"
    content = handoff_path.read_text(encoding="utf-8")
    assert "Codex task: order #1" in content
    assert "Сверстать HTML/CSS/JS лендинг" in content
