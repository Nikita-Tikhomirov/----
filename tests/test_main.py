from dataclasses import dataclass

from app.main import (
    _proposal_title_from_text,
    create_order_handoff,
    process_approvals,
    process_order_reviews,
    scan_once,
    submit_order,
)
from app.ai_lead_judge import LeadJudgeResult
from app.attachments import AttachmentProcessingResult, AttachmentReport
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
        self.sent_details = []

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

    def send_message(self, contact, text, *, price_rub=None, days=None, title=""):
        self.sent.append((contact, text))
        self.sent_details.append((contact, text, price_rub, days, title))
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


class FlakyEmailClient(FakeEmailClient):
    def __init__(self):
        super().__init__()
        self.fail_once = True

    def send_lead(self, lead):
        if self.fail_once:
            self.fail_once = False
            raise TimeoutError("SMTP timed out")
        return super().send_lead(lead)


class FakeKworkProjectClient:
    def __init__(self, response_count=3, reason="", page_text="", attachments=(), facts=()):
        self.response_count = response_count
        self.reason = reason
        self.page_text = page_text
        self.attachments = attachments
        self.facts = facts
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
            facts=tuple(self.facts),
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


def test_scan_once_keeps_new_lead_retryable_when_email_fails(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    email_client = FlakyEmailClient()

    first_created = scan_once(
        storage=storage,
        telegram_client=FakeTelegramClient(),
        email_client=email_client,
    )
    lead = storage.list_leads()[0]

    assert first_created == 0
    assert lead.status == "new"
    assert email_client.sent_leads == []

    second_created = scan_once(
        storage=storage,
        telegram_client=FakeTelegramClient(),
        email_client=email_client,
    )

    assert second_created == 1
    assert storage.get_lead(lead.id).status == "emailed"
    assert email_client.sent_leads == [lead.id]


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


def test_scan_once_skips_kwork_web_projects_without_response_count(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    email_client = FakeEmailClient()
    source = FakeTelegramClient()
    source.fetch_recent_posts = lambda: [
        FakePost(
            channel="kwork-web",
            message_id=3,
            url="https://kwork.ru/projects/3/view",
            text="Нужно поправить форму на WordPress. Отклик: https://kwork.ru/projects/3/view",
            posted_at="2026-07-17 23:58:00",
        )
    ]

    created = scan_once(
        storage=storage,
        telegram_client=source,
        email_client=email_client,
        kwork_project_client=FakeKworkProjectClient(response_count=None, reason="счетчик скрыт"),
    )

    assert created == 0
    assert storage.list_leads() == []
    assert email_client.sent_leads == []


def test_scan_once_skips_kwork_project_that_became_unavailable(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    email_client = FakeEmailClient()
    source = FakeTelegramClient()
    source.fetch_recent_posts = lambda: [
        FakePost(
            channel="kwork-web",
            message_id=2,
            url="https://kwork.ru/projects/2/view",
            text=(
                "Нужно сверстать лендинг HTML/CSS/JS. Предложений: 2\n"
                "Отклик: https://kwork.ru/projects/2/view"
            ),
            posted_at="",
        )
    ]

    created = scan_once(
        storage=storage,
        telegram_client=source,
        email_client=email_client,
        kwork_project_client=FakeKworkProjectClient(
            response_count=None,
            reason="Kwork project is unavailable: page not found, closed, or removed.",
        ),
    )

    assert created == 0
    assert storage.list_leads() == []
    assert email_client.sent_leads == []


def test_scan_once_uses_ai_judge_for_summary_reply_and_score(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    email_client = FakeEmailClient()

    def fake_judge(text, api_key="", model="deepseek-chat", **kwargs):
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
        reply_composer=lambda context, seed_reply, **kwargs: (
            "Здравствуйте! Проверю логику калькулятора, внесу нужные правки и протестирую расчеты. "
            "Готов показать работающий результат после проверки основных сценариев."
        ),
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
    assert lead.proposal_price_rub == 18000
    assert lead.proposal_days == 5


def test_scan_once_persists_composed_price_free_reply(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    email_client = FakeEmailClient()
    seen_contexts = []

    def fake_judge(text, api_key="", model="deepseek-chat", **kwargs):
        return LeadJudgeResult(
            accepted=True,
            decision="accept",
            score=86,
            complexity="simple",
            estimated_days=2,
            price_rub=5000,
            summary="Исправить отправку формы заявки и адаптив лендинга",
            reasons=["задача понятна"],
            risks=[],
            questions=[],
            draft_reply="Здравствуйте! Цена 5000 руб. Уточните детали.",
        )

    def fake_composer(context, seed_reply, api_key="", model="deepseek-chat"):
        seen_contexts.append((context, seed_reply, api_key, model))
        return (
            "Здравствуйте! Проверю отправку формы и адаптив лендинга, затем внесу нужные правки. "
            "После изменений протестирую сценарий на мобильных и покажу готовый результат."
        )

    created = scan_once(
        storage=storage,
        telegram_client=FakeTelegramClient(),
        email_client=email_client,
        kwork_project_client=FakeKworkProjectClient(
            response_count=1,
            facts=("Бюджет: до 5 000 ₽",),
        ),
        lead_judge=fake_judge,
        reply_composer=fake_composer,
        deepseek_api_key="sk-test",
    )

    assert created == 1
    lead = storage.list_leads(status="emailed")[0]
    assert lead.draft_reply == (
        "Здравствуйте! Проверю отправку формы и адаптив лендинга, затем внесу нужные правки. "
        "После изменений протестирую сценарий на мобильных и покажу готовый результат."
    )
    assert lead.proposal_price_rub == 5000
    assert lead.proposal_days == 2
    assert seen_contexts[0][1] == "Здравствуйте! Цена 5000 руб. Уточните детали."
    assert "Бюджет" not in seen_contexts[0][0].source_text
    assert seen_contexts[0][0].task_summary != "Исправить отправку формы заявки и адаптив лендинга"
    assert seen_contexts[0][0].task_summary == "Kwork project"
    assert seen_contexts[0][2:] == ("sk-test", "deepseek-chat")


def test_scan_once_passes_kwork_page_details_and_attachments_to_ai_judge(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    email_client = FakeEmailClient()
    seen_texts = []

    def fake_judge(text, api_key="", model="deepseek-chat", **kwargs):
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

    def fake_judge(text, api_key="", model="deepseek-chat", **kwargs):
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

    def fake_judge(text, api_key="", model="deepseek-chat", **kwargs):
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


def test_scan_once_records_structured_attachment_reports(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    email_client = FakeEmailClient()
    seen_texts = []

    def fake_judge(text, api_key="", model="deepseek-chat", **kwargs):
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

    def fake_attachment_report(attachments, cookie="", **kwargs):
        assert kwargs["output_dir"].name.startswith("post_")
        return AttachmentProcessingResult(
            context="ФАЙЛЫ/ТЗ:\n- ТЗ.zip\n  Статус: скачан, архив открыт\n  Кратко: внутри brief.txt, нужна форма",
            reports=(
                AttachmentReport(
                    label="ТЗ.zip",
                    url="https://kwork.ru/files/tz.zip",
                    local_path=str(tmp_path / "attachments" / "tz.zip"),
                    status="скачан, архив открыт",
                    summary="внутри brief.txt, нужна форма",
                    kind="archive",
                    opened_archive=True,
                    ocr_scanned=False,
                ),
            ),
        )

    scan_once(
        storage=storage,
        telegram_client=FakeTelegramClient(),
        email_client=email_client,
        kwork_project_client=FakeKworkProjectClient(
            response_count=1,
            attachments=("ТЗ.zip: https://kwork.ru/files/tz.zip",),
        ),
        lead_judge=fake_judge,
        attachment_context_builder=fake_attachment_report,
    )

    lead = storage.list_leads()[0]
    attachments = storage.list_lead_attachments(lead.id)
    assert "внутри brief.txt" in seen_texts[0]
    assert len(attachments) == 1
    assert attachments[0].label == "ТЗ.zip"
    assert attachments[0].opened_archive is True


def test_scan_once_includes_kwork_facts_in_email_summary(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    email_client = FakeEmailClient()

    def fake_judge(text, api_key="", model="deepseek-chat", **kwargs):
        assert "Kwork facts:" in text
        assert "Бюджет: до 15 000 ₽" in text
        assert "Осталось: 2 д. 17 ч." in text
        return LeadJudgeResult(
            accepted=True,
            decision="accept",
            score=89,
            complexity="simple",
            estimated_days=2,
            price_rub=15000,
            summary="Сверстать лендинг",
            reasons=["ясный бюджет и срок"],
            risks=[],
            questions=[],
            draft_reply="Здравствуйте! Сделаю лендинг за 2 дня, бюджет 15000 руб.",
        )

    scan_once(
        storage=storage,
        telegram_client=FakeTelegramClient(),
        email_client=email_client,
        kwork_project_client=FakeKworkProjectClient(
            response_count=4,
            facts=(
                "Бюджет: до 15 000 ₽",
                "Осталось: 2 д. 17 ч.",
                "Предложений: 4",
            ),
        ),
        lead_judge=fake_judge,
    )

    lead = storage.list_leads()[0]
    assert "KWORK-ДАННЫЕ:" in lead.summary
    assert "Бюджет: до 15 000 ₽" in lead.summary
    assert "Осталось: 2 д. 17 ч." in lead.summary


def test_scan_once_skips_ai_rejected_lead(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    email_client = FakeEmailClient()

    def fake_judge(text, api_key="", model="deepseek-chat", **kwargs):
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
        draft_reply=(
            "Здравствуйте! Посмотрел задачу по лендингу HTML/CSS/JS. "
            "Сверстаю нужные блоки, настрою адаптивное отображение и проверю основной сценарий страницы. "
            "После этого покажу готовый рабочий вариант."
        ),
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
        (
            "@client_dev",
            (
                "Здравствуйте! Посмотрел задачу по лендингу HTML/CSS/JS. "
                "Сверстаю нужные блоки, настрою адаптивное отображение и проверю основной сценарий страницы. "
                "После этого покажу готовый рабочий вариант."
            ),
        )
    ]
    assert storage.get_lead(lead_id).status == "sent"


def test_process_approvals_blocks_stale_reply_that_invents_missing_form_work(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    post_id = storage.save_post(
        channel="kwork-web",
        message_id=28,
        post_url="https://kwork.ru/projects/28/view",
        text="Посадить информационную страницу и каталог по PSD на WordPress. Предложений: 2",
        posted_at="2026-07-18T10:00:00+03:00",
    )
    stale_reply = (
        "Здравствуйте! Посмотрел задачу по посадке сайта и каталога на WordPress. "
        "Сначала проверю текущую отправку формы и валидацию на мобильных, затем внесу нужные правки в разметку и стили. "
        "После изменений протестирую сценарий на телефоне и в основных браузерах, чтобы заявки стабильно доходили. "
        "На работу ориентируюсь на 5 дн., могу приступить сразу."
    )
    lead_id = storage.create_lead(
        post_id=post_id,
        score=82,
        summary="Задача: Посадить каталог на WordPress",
        draft_reply=stale_reply,
        contact="https://kwork.ru/projects/28/view",
        proposal_title="Посадить каталог на WordPress",
        proposal_days=5,
    )
    storage.mark_lead_emailed(lead_id, "<lead@example.com>")
    telegram_client = FakeTelegramClient()
    approval_message_id = "<approval@example.com>"

    sent = process_approvals(
        storage=storage,
        telegram_client=telegram_client,
        email_client=FakeEmailClient(approvals=[(lead_id, approval_message_id)]),
    )

    lead = storage.get_lead(lead_id)
    assert sent == 0
    assert telegram_client.sent == []
    assert lead.status == "emailed"
    assert "требует правки" in lead.last_error.lower()
    assert approval_message_id in storage.seen_approval_message_ids()


def test_process_approvals_can_retry_after_blocked_email_once_reply_is_corrected(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    post_id = storage.save_post(
        channel="kwork-web",
        message_id=29,
        post_url="https://kwork.ru/projects/29/view",
        text="Посадить информационную страницу и каталог по PSD на WordPress. Предложений: 2",
        posted_at="2026-07-18T10:00:00+03:00",
    )
    lead_id = storage.create_lead(
        post_id=post_id,
        score=82,
        summary="Задача: Посадить каталог на WordPress",
        draft_reply=(
            "Здравствуйте! Посмотрел задачу по посадке сайта и каталога на WordPress. "
            "Сначала проверю текущую отправку формы и валидацию на мобильных, затем внесу нужные правки в разметку и стили. "
            "После изменений протестирую сценарий на телефоне и в основных браузерах, чтобы заявки стабильно доходили. "
            "На работу ориентируюсь на 5 дн., могу приступить сразу."
        ),
        contact="https://kwork.ru/projects/29/view",
        proposal_title="Посадить каталог на WordPress",
        proposal_days=5,
    )
    storage.mark_lead_emailed(lead_id, "<lead@example.com>")
    telegram_client = FakeTelegramClient()

    first_sent = process_approvals(
        storage=storage,
        telegram_client=telegram_client,
        email_client=FakeEmailClient(approvals=[(lead_id, "<blocked@example.com>")]),
    )
    storage.update_lead_proposal(
        lead_id,
        draft_reply=(
            "Здравствуйте! Посмотрел задачу по посадке информационной страницы и каталога на WordPress. "
            "Сверю структуру страниц и макеты PSD, затем соберу нужные разделы на WordPress. "
            "Проверю карточки товаров и отображение каталога, чтобы страницы работали корректно. "
            "Могу приступить сразу и покажу готовый рабочий вариант."
        ),
        title="Посадить каталог на WordPress",
        price_rub=12000,
        days=5,
    )

    second_sent = process_approvals(
        storage=storage,
        telegram_client=telegram_client,
        email_client=FakeEmailClient(approvals=[(lead_id, "<retry@example.com>")]),
    )

    assert first_sent == 0
    assert second_sent == 1
    assert len(telegram_client.sent) == 1
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


def test_process_approvals_sends_kwork_web_reply_after_ok(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    post_id = storage.save_post(
        channel="kwork-web",
        message_id=3186746,
        post_url="https://kwork.ru/projects/3186746/view",
        text="Нужно поправить WordPress. Предложений: 4",
        posted_at="",
    )
    lead_id = storage.create_lead(
        post_id=post_id,
        score=86,
        summary="WordPress задача",
        draft_reply="Здравствуйте! Сделаю за 3 дня, цена 10000 руб.",
        contact="https://kwork.ru/projects/3186746/view",
    )
    storage.mark_lead_emailed(lead_id, "<lead@example.com>")
    telegram_client = FakeTelegramClient()
    email_client = FakeEmailClient(approvals=[(lead_id, "<approval@example.com>")])

    sent = process_approvals(
        storage=storage,
        telegram_client=telegram_client,
        email_client=email_client,
    )

    assert sent == 1
    sent_text = telegram_client.sent[0][1].lower()
    assert "10000" not in sent_text
    assert "руб" not in sent_text
    assert storage.get_lead(lead_id).status == "sent"


def test_proposal_title_ignores_inline_kwork_offer_metadata():
    assert _proposal_title_from_text(
        "Нужно поправить WordPress. Предложений: 4\nОтклик: https://kwork.ru/projects/1/view"
    ) == "Нужно поправить WordPress"


def test_process_approvals_passes_kwork_form_terms_without_price_in_reply_text(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    project_url = "https://kwork.ru/projects/3186746/view"
    post_id = storage.save_post(
        channel="kwork-web",
        message_id=3186746,
        post_url=project_url,
        text="Название заказа\nНужно поправить WordPress. Предложений: 4",
        posted_at="",
    )
    reply_text = (
        "Здравствуйте! Посмотрел задачу по доработке WordPress. "
        "Изучу текущую реализацию, внесу нужные правки и проверю результат на основном сценарии."
    )
    lead_id = storage.create_lead(
        post_id=post_id,
        score=86,
        summary="WordPress задача\nСрок: 3 дн.\nЦена: 10 000 руб.",
        draft_reply=reply_text,
        contact=project_url,
    )
    storage.mark_lead_emailed(lead_id, "<lead@example.com>")
    telegram_client = FakeTelegramClient()

    sent = process_approvals(
        storage=storage,
        telegram_client=telegram_client,
        email_client=FakeEmailClient(approvals=[(lead_id, "<approval@example.com>")]),
    )

    assert sent == 1
    assert "10000" not in reply_text
    assert telegram_client.sent_details == [
        (project_url, reply_text, 10000, 3, "Название заказа")
    ]


def test_process_approvals_uses_saved_form_terms_after_ok(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    project_url = "https://kwork.ru/projects/3186747/view"
    post_id = storage.save_post(
        channel="kwork-web",
        message_id=3186747,
        post_url=project_url,
        text="📌 Исходное название\nНужно доработать WordPress. Предложений: 2",
        posted_at="",
    )
    lead_id = storage.create_lead(
        post_id=post_id,
        score=86,
        summary="WordPress задача\nСрок: 3 дн.\nЦена: 10 000 руб.",
        draft_reply="Старый текст",
        contact=project_url,
    )
    reply_text = (
        "Здравствуйте! Разберу текущую реализацию WordPress и внесу нужные изменения. "
        "После этого проверю основной сценарий и покажу готовый результат."
    )
    storage.update_lead_proposal(
        lead_id,
        draft_reply=reply_text,
        title="Сохраненное название",
        price_rub=14000,
        days=5,
    )
    storage.mark_lead_emailed(lead_id, "<lead@example.com>")
    telegram_client = FakeTelegramClient()

    sent = process_approvals(
        storage=storage,
        telegram_client=telegram_client,
        email_client=FakeEmailClient(approvals=[(lead_id, "<approval@example.com>")]),
    )

    assert sent == 1
    assert telegram_client.sent_details == [
        (project_url, reply_text, 14000, 5, "Сохраненное название")
    ]


def test_process_approvals_removes_price_from_legacy_customer_reply(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    project_url = "https://kwork.ru/projects/3186748/view"
    post_id = storage.save_post(
        channel="kwork-web",
        message_id=3186748,
        post_url=project_url,
        text="📌 Доработать форму\nПредложений: 2",
        posted_at="",
    )
    legacy_reply = (
        "Здравствуйте! Исправлю форму и адаптив за 3 дня, цена 10000 руб. "
        "Сначала проверю текущую отправку, затем внесу правки и протестирую на телефоне."
    )
    lead_id = storage.create_lead(
        post_id=post_id,
        score=86,
        summary="Срок: 3 дн.\nЦена: 10 000 руб.\nЗадача: Доработать форму заявки",
        draft_reply=legacy_reply,
        contact=project_url,
        proposal_title="Доработать форму",
        proposal_price_rub=10000,
        proposal_days=3,
    )
    storage.mark_lead_emailed(lead_id, "<lead@example.com>")
    telegram_client = FakeTelegramClient()

    sent = process_approvals(
        storage=storage,
        telegram_client=telegram_client,
        email_client=FakeEmailClient(approvals=[(lead_id, "<approval@example.com>")]),
    )

    assert sent == 1
    sent_text = telegram_client.sent_details[0][1].lower()
    assert "10000" not in sent_text
    assert "руб" not in sent_text
    assert telegram_client.sent_details[0][2:] == (10000, 3, "Доработать форму")
    assert "руб" not in storage.get_lead(lead_id).draft_reply.lower()


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
