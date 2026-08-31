import logging
import sys
from dataclasses import dataclass
from types import SimpleNamespace

import pytest

import app.main as main_module

from app.main import (
    _auto_send_new_leads,
    _mobile_command_payload,
    _proposal_price_from_kwork_max,
    _proposal_title_from_text,
    _scan_execution_lock,
    _summary_from_judge,
    _configure_runtime_logging,
    create_order_handoff,
    process_mobile_approvals,
    process_approvals,
    process_order_reviews,
    scan_once,
    submit_order,
)
from app.ai_lead_judge import LeadAnalysisUnavailable, LeadJudgeResult
from app.attachments import AttachmentProcessingResult, AttachmentReport
from app.kwork_client import KworkProjectInfo
from app.reply_composer import ReplyGenerationUnavailable
from app.storage import Storage


@dataclass
class FakePost:
    channel: str
    message_id: int
    url: str
    text: str
    posted_at: str


def test_proposal_price_uses_fifteen_percent_below_kwork_maximum():
    assert _proposal_price_from_kwork_max(6000) == 5100
    assert _proposal_price_from_kwork_max(6150) == 5200
    assert _proposal_price_from_kwork_max(500) == 500
    assert _proposal_price_from_kwork_max(None) is None


def test_mobile_command_rejects_price_below_kwork_minimum():
    with pytest.raises(ValueError, match="не меньше 500"):
        _mobile_command_payload(
            {
                "draft_reply": "Исправлю форму и проверю отправку заявки.",
                "proposal_title": "Исправить форму",
                "proposal_price_rub": 400,
                "proposal_days": 1,
            }
        )


def test_auto_send_only_submits_newly_discovered_kwork_leads(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    post_id = storage.save_post(
        channel="kwork-web",
        message_id=3246001,
        post_url="https://kwork.ru/projects/3246001/view",
        text=(
            "Нужно исправить отправку формы заявки на WordPress и проверить адаптив. "
            "Предложений: 2"
        ),
        posted_at="2026-08-31 12:00:00",
    )
    lead_id = storage.create_lead(
        post_id=post_id,
        score=88,
        summary=(
            "Задача: Исправить отправку формы заявки на WordPress\n"
            "Боль клиента: Заявки с мобильных устройств сейчас теряются\n"
            "План работ: Проверить обработчик; исправить отправку; протестировать адаптив"
        ),
        draft_reply=(
            "Здравствуйте! Проверю обработчик формы WordPress и найду, на каком шаге теряются заявки. "
            "Исправлю отправку и сообщения об ошибках, затем прогоню форму на компьютере и телефоне. "
            "В результате заявки будут стабильно доходить, а пользователь увидит понятное подтверждение."
        ),
        contact="https://kwork.ru/projects/3246001/view",
        proposal_title="Исправить форму WordPress",
        proposal_price_rub=5100,
        proposal_days=2,
    )
    storage.update_lead_live_status(lead_id, 2)
    sender = FakeKworkSender()

    assert _auto_send_new_leads(storage, {}, sender, daily_limit=10) == 1
    assert storage.get_lead(lead_id).status == "sent"
    assert len(sender.sent) == 1

    assert _auto_send_new_leads(storage, {}, sender, daily_limit=10) == 0
    assert len(sender.sent) == 1


def test_auto_send_does_not_submit_leads_that_were_already_waiting(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    post_id = storage.save_post(
        channel="kwork-web",
        message_id=3246002,
        post_url="https://kwork.ru/projects/3246002/view",
        text="Нужно поправить форму WordPress. Предложений: 1",
        posted_at="2026-08-30 12:00:00",
    )
    lead_id = storage.create_lead(
        post_id=post_id,
        score=90,
        summary="Задача: Поправить форму WordPress",
        draft_reply=(
            "Здравствуйте! Проверю текущую отправку формы и исправлю обработчик заявки. "
            "После изменений протестирую успешный и ошибочный сценарии на компьютере и телефоне."
        ),
        contact="https://kwork.ru/projects/3246002/view",
        proposal_title="Исправить форму WordPress",
        proposal_price_rub=3000,
        proposal_days=2,
    )
    sender = FakeKworkSender()

    assert _auto_send_new_leads(storage, {lead_id: "new"}, sender, daily_limit=10) == 0
    assert storage.get_lead(lead_id).status == "new"
    assert sender.sent == []


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


class FakeLeadHub:
    def __init__(self, commands=()):
        self.commands = list(commands)
        self.claimed = []
        self.results = []
        self.published = []

    def publish_lead(self, lead, attachments=()):
        self.published.append((lead.id, lead.draft_reply, tuple(attachments)))
        return lead.hub_lead_id or 91

    def fetch_approved_commands(self):
        return list(self.commands)

    def claim_command(self, lead_id, executor_id):
        self.claimed.append((lead_id, executor_id))
        for command in self.commands:
            if command["id"] == lead_id:
                return command | {"status": "sending"}
        return None

    def report_result(self, lead_id, executor_id, *, sent, error=""):
        self.results.append((lead_id, executor_id, sent, error))


class FakeKworkSender:
    def __init__(self):
        self.sent = []

    def send_reply(self, contact, text, *, price_rub, days, title, submit):
        self.sent.append((contact, text, price_rub, days, title, submit))
        return "kwork-project-1"


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
    def __init__(
        self,
        response_count=3,
        reason="",
        page_text="",
        attachments=(),
        facts=(),
        buyer_desired_budget_rub=None,
        kwork_max_price_rub=None,
    ):
        self.response_count = response_count
        self.reason = reason
        self.page_text = page_text
        self.attachments = attachments
        self.facts = facts
        self.buyer_desired_budget_rub = buyer_desired_budget_rub
        self.kwork_max_price_rub = kwork_max_price_rub
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
            buyer_desired_budget_rub=self.buyer_desired_budget_rub,
            kwork_max_price_rub=self.kwork_max_price_rub,
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


def test_summary_from_judge_shows_customer_goal_and_work_plan():
    result = LeadJudgeResult(
        accepted=True,
        decision="accept",
        score=84,
        complexity="medium",
        estimated_days=4,
        price_rub=15000,
        summary="Доработать форму заявки на WordPress",
        reasons=["результат понятен"],
        risks=["нужен доступ к админке"],
        questions=[],
        draft_reply="Здравствуйте!",
        customer_goal="Чтобы заявки стабильно приходили с сайта",
        work_plan=["Проверить форму", "Исправить обработку", "Протестировать отправку"],
        blocking_question="Куда должны поступать заявки?",
    )

    summary = _summary_from_judge(result)

    assert "Боль клиента: Чтобы заявки стабильно приходили с сайта" in summary
    assert "План работ: Проверить форму; Исправить обработку; Протестировать отправку" in summary
    assert "Вопрос перед стартом: Куда должны поступать заявки?" in summary


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


def test_scan_once_hands_new_lead_to_sender_before_scanning_next_post(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    source = FakeTelegramClient()
    first = source.fetch_recent_posts()[0]
    source.fetch_recent_posts = lambda: [
        first,
        FakePost(
            channel="jobs",
            message_id=2,
            url="https://t.me/jobs/2",
            text="Нужно исправить HTML/CSS форму за один день. Контакт @second_client",
            posted_at="2026-05-04T10:01:00+03:00",
        ),
    ]
    events = []

    def judge(text, **kwargs):
        events.append("judge-2" if "second_client" in text else "judge-1")
        return LeadJudgeResult(
            accepted=True,
            decision="accept",
            score=90,
            complexity="simple",
            estimated_days=1,
            price_rub=1500,
            summary="Исправить форму",
            reasons=["простая веб-задача"],
            risks=[],
            questions=[],
            draft_reply="Исправлю форму и проверю отправку.",
        )

    scan_once(
        storage=storage,
        telegram_client=source,
        email_client=FakeEmailClient(),
        lead_judge=judge,
        reply_composer=lambda context, seed_reply, **kwargs: seed_reply,
        new_lead_handler=lambda lead: events.append(f"send-{lead.message_id}"),
    )

    assert events == ["judge-1", "send-1", "judge-2", "send-2"]


def test_scan_once_skips_email_when_another_process_has_claimed_the_lead(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    email_client = FakeEmailClient()
    post = FakeTelegramClient().fetch_recent_posts()[0]
    post_id = storage.save_post(
        channel=post.channel,
        message_id=post.message_id,
        post_url=post.url,
        text=post.text,
        posted_at=post.posted_at,
    )
    lead_id = storage.create_lead(
        post_id=post_id,
        score=80,
        summary="HTML/CSS лендинг",
        draft_reply="Здравствуйте! Готов помочь.",
        contact="@client_dev",
    )

    assert storage.claim_lead_email_delivery(lead_id) is True

    scan_once(storage=storage, telegram_client=FakeTelegramClient(), email_client=email_client)

    assert email_client.sent_leads == []
    assert storage.get_lead(lead_id).status == "new"

def test_scan_once_persists_the_live_kwork_response_count(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()

    scan_once(
        storage=storage,
        telegram_client=FakeTelegramClient(),
        email_client=FakeEmailClient(),
        kwork_project_client=FakeKworkProjectClient(response_count=4),
    )

    lead = storage.list_leads()[0]
    assert lead.live_response_count == 4
    assert lead.live_checked_at
    assert lead.live_reason == ""


def test_scan_once_refreshes_live_kwork_count_for_existing_queued_lead(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    email_client = FakeEmailClient()
    project_client = FakeKworkProjectClient(response_count=5)

    scan_once(
        storage=storage,
        telegram_client=FakeTelegramClient(),
        email_client=email_client,
        kwork_project_client=project_client,
        kwork_max_responses=5,
    )

    project_client.response_count = 6
    created = scan_once(
        storage=storage,
        telegram_client=FakeTelegramClient(),
        email_client=email_client,
        kwork_project_client=project_client,
        kwork_max_responses=5,
    )

    leads = storage.list_leads()
    assert created == 0
    assert len(leads) == 1
    assert leads[0].live_response_count == 6
    assert email_client.sent_leads == [leads[0].id]
    assert project_client.inspected == ["@client_dev", "@client_dev"]


def test_scan_once_backfills_kwork_budgets_and_price_for_existing_lead(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    project_client = FakeKworkProjectClient(response_count=1)

    scan_once(
        storage=storage,
        telegram_client=FakeTelegramClient(),
        email_client=FakeEmailClient(),
        kwork_project_client=project_client,
        kwork_max_responses=5,
    )

    project_client.buyer_desired_budget_rub = 500
    project_client.kwork_max_price_rub = 1500
    scan_once(
        storage=storage,
        telegram_client=FakeTelegramClient(),
        email_client=FakeEmailClient(),
        kwork_project_client=project_client,
        kwork_max_responses=5,
    )

    lead = storage.list_leads()[0]
    assert lead.buyer_desired_budget_rub == 500
    assert lead.kwork_max_price_rub == 1500
    assert lead.proposal_price_rub == 1300


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


def test_scan_once_does_not_reinspect_durably_rejected_kwork_project(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    email_client = FakeEmailClient()
    project_client = FakeKworkProjectClient(response_count=7)

    scan_once(
        storage=storage,
        telegram_client=FakeTelegramClient(),
        email_client=email_client,
        kwork_project_client=project_client,
        kwork_max_responses=5,
    )
    scan_once(
        storage=storage,
        telegram_client=FakeTelegramClient(),
        email_client=email_client,
        kwork_project_client=project_client,
        kwork_max_responses=5,
    )

    assert len(project_client.inspected) == 1


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


def test_scan_once_retries_kwork_project_when_response_count_is_temporarily_unavailable(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    project_client = FakeKworkProjectClient(response_count=None, reason="счетчик еще загружается")

    scan_once(
        storage=storage,
        telegram_client=FakeTelegramClient(),
        email_client=FakeEmailClient(),
        kwork_project_client=project_client,
    )
    scan_once(
        storage=storage,
        telegram_client=FakeTelegramClient(),
        email_client=FakeEmailClient(),
        kwork_project_client=project_client,
    )

    assert len(project_client.inspected) == 2


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


def test_scan_once_keeps_post_retryable_when_cloud_analysis_is_unavailable(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    email_client = FakeEmailClient()
    attempts = 0

    def flaky_judge(_text, **_kwargs):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise LeadAnalysisUnavailable("cloud AI analysis unavailable")
        return LeadJudgeResult(
            accepted=True,
            decision="accept",
            score=86,
            complexity="simple",
            estimated_days=2,
            price_rub=5000,
            summary="Исправить форму заявки",
            reasons=["понятный результат"],
            risks=[],
            questions=[],
            draft_reply="Здравствуйте! Исправлю форму заявки и проверю отправку.",
        )

    first_created = scan_once(
        storage=storage,
        telegram_client=FakeTelegramClient(),
        email_client=email_client,
        lead_judge=flaky_judge,
        reply_composer=lambda _context, reply, **_kwargs: reply,
        openrouter_api_key="or-test",
    )

    post = FakeTelegramClient().fetch_recent_posts()[0]
    post_id = storage.save_post(
        channel=post.channel,
        message_id=post.message_id,
        post_url=post.url,
        text=post.text,
        posted_at=post.posted_at,
    )
    assert first_created == 0
    assert storage.list_leads() == []
    assert storage.get_post_rejection(post_id) == ""

    second_created = scan_once(
        storage=storage,
        telegram_client=FakeTelegramClient(),
        email_client=email_client,
        lead_judge=flaky_judge,
        reply_composer=lambda _context, reply, **_kwargs: reply,
        openrouter_api_key="or-test",
    )

    assert second_created == 1
    assert attempts == 2
    assert len(storage.list_leads()) == 1


def test_scan_once_keeps_post_retryable_when_cloud_reply_is_unavailable(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    composer_attempts = 0

    def accepted_judge(_text, **_kwargs):
        return LeadJudgeResult(
            accepted=True,
            decision="accept",
            score=86,
            complexity="simple",
            estimated_days=2,
            price_rub=5000,
            summary="Исправить форму заявки",
            reasons=["понятный результат"],
            risks=[],
            questions=[],
            draft_reply="Здравствуйте! Исправлю форму заявки и проверю отправку.",
        )

    def flaky_composer(_context, reply, **_kwargs):
        nonlocal composer_attempts
        composer_attempts += 1
        if composer_attempts == 1:
            raise ReplyGenerationUnavailable("cloud AI reply unavailable")
        return reply

    first_created = scan_once(
        storage=storage,
        telegram_client=FakeTelegramClient(),
        email_client=FakeEmailClient(),
        lead_judge=accepted_judge,
        reply_composer=flaky_composer,
        openrouter_api_key="or-test",
    )

    assert first_created == 0
    retryable_leads = storage.list_leads()
    assert len(retryable_leads) == 1
    assert retryable_leads[0].status == "failed"
    assert retryable_leads[0].draft_reply == ""

    second_created = scan_once(
        storage=storage,
        telegram_client=FakeTelegramClient(),
        email_client=FakeEmailClient(),
        lead_judge=accepted_judge,
        reply_composer=flaky_composer,
        openrouter_api_key="or-test",
    )

    assert second_created == 1
    assert composer_attempts == 2
    assert len(storage.list_leads()) == 1


def test_scan_once_rebuilds_and_republishes_existing_generic_lead(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    post = FakeTelegramClient().fetch_recent_posts()[0]
    post_id = storage.save_post(
        channel=post.channel,
        message_id=post.message_id,
        post_url=post.url,
        text=post.text,
        posted_at=post.posted_at,
    )
    lead_id = storage.create_lead(
        post_id=post_id,
        score=78,
        summary="Задача: Сверстать лендинг",
        draft_reply=(
            "Здравствуйте! Посмотрел задачу: сверстать лендинг. "
            "Сначала разберу текущую реализацию и требования, затем внесу нужные изменения по задаче. "
            "После этого проверю основной сценарий и покажу готовый рабочий результат."
        ),
        contact="@client_dev",
        proposal_title="Сверстать лендинг",
        proposal_price_rub=5000,
        proposal_days=2,
    )
    storage.mark_lead_hub_synced(lead_id, 91)
    storage.mark_failed(lead_id, "старый шаблон заблокирован проверкой качества")
    hub = FakeLeadHub()

    def accepted_judge(_text, **_kwargs):
        return LeadJudgeResult(
            accepted=True,
            decision="accept",
            score=91,
            complexity="simple",
            estimated_days=2,
            price_rub=5000,
            summary="Сверстать адаптивный лендинг и исправить форму",
            reasons=["понятный результат"],
            risks=[],
            questions=[],
            draft_reply="Черновик AI",
            customer_goal="Получить готовый адаптивный лендинг с рабочей формой",
            work_plan=["Сверстать блоки", "Настроить адаптив", "Проверить форму"],
        )

    rebuilt_reply = (
        "Здравствуйте! Сверстаю адаптивный лендинг и аккуратно подключу форму заявки. "
        "Проверю основные разрешения, отправку формы и исправлю найденные расхождения. "
        "После проверки покажу готовую страницу, могу приступить сразу."
    )
    created = scan_once(
        storage=storage,
        telegram_client=FakeTelegramClient(),
        lead_hub=hub,
        lead_judge=accepted_judge,
        reply_composer=lambda _context, _seed, **_kwargs: rebuilt_reply,
        openrouter_api_key="or-test",
    )

    lead = storage.get_lead(lead_id)
    assert created == 1
    assert lead.status == "new"
    assert lead.score == 91
    assert lead.draft_reply == rebuilt_reply
    assert hub.published == [(lead_id, rebuilt_reply, ())]


def test_scan_once_retries_mobile_sync_after_rebuilt_draft_publish_failure(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    post = FakeTelegramClient().fetch_recent_posts()[0]
    post_id = storage.save_post(
        channel=post.channel,
        message_id=post.message_id,
        post_url=post.url,
        text=post.text,
        posted_at=post.posted_at,
    )
    lead_id = storage.create_lead(
        post_id=post_id,
        score=78,
        summary="Задача: Сверстать лендинг",
        draft_reply=(
            "Здравствуйте! Посмотрел задачу: сверстать лендинг. "
            "Сначала разберу текущую реализацию и требования, затем внесу нужные изменения по задаче. "
            "После этого проверю основной сценарий и покажу готовый рабочий результат."
        ),
        contact="@client_dev",
        proposal_title="Сверстать лендинг",
        proposal_price_rub=5000,
        proposal_days=2,
    )
    storage.mark_lead_hub_synced(lead_id, 91)
    judge_calls = 0

    def accepted_judge(_text, **_kwargs):
        nonlocal judge_calls
        judge_calls += 1
        return LeadJudgeResult(
            accepted=True,
            decision="accept",
            score=91,
            complexity="simple",
            estimated_days=2,
            price_rub=5000,
            summary="Сверстать адаптивный лендинг и исправить форму",
            reasons=["понятный результат"],
            risks=[],
            questions=[],
            draft_reply="Черновик AI",
            customer_goal="Получить адаптивный лендинг с рабочей формой",
            work_plan=["Сверстать блоки", "Настроить адаптив", "Проверить форму"],
        )

    rebuilt_reply = (
        "Здравствуйте! Сверстаю адаптивный лендинг и подключу форму заявки. "
        "Проверю страницу на компьютере и телефоне, затем исправлю найденные расхождения."
    )

    class FlakyHub(FakeLeadHub):
        def __init__(self):
            super().__init__()
            self.attempts = 0

        def publish_lead(self, lead, attachments=()):
            self.attempts += 1
            if self.attempts == 1:
                raise TimeoutError("hub unavailable")
            return super().publish_lead(lead, attachments)

    hub = FlakyHub()

    first_created = scan_once(
        storage=storage,
        telegram_client=FakeTelegramClient(),
        lead_hub=hub,
        lead_judge=accepted_judge,
        reply_composer=lambda _context, _seed, **_kwargs: rebuilt_reply,
        openrouter_api_key="or-test",
    )
    second_created = scan_once(
        storage=storage,
        telegram_client=FakeTelegramClient(),
        lead_hub=hub,
        lead_judge=accepted_judge,
        reply_composer=lambda _context, _seed, **_kwargs: rebuilt_reply,
        openrouter_api_key="or-test",
    )

    lead = storage.get_lead(lead_id)
    assert first_created == 0
    assert second_created == 1
    assert judge_calls == 1
    assert hub.attempts == 2
    assert lead.hub_synced_at != ""


def test_scan_once_rejects_existing_generic_lead_after_fresh_ai_verdict(tmp_path, caplog):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    post = FakeTelegramClient().fetch_recent_posts()[0]
    post_id = storage.save_post(
        channel=post.channel,
        message_id=post.message_id,
        post_url=post.url,
        text=post.text,
        posted_at=post.posted_at,
    )
    lead_id = storage.create_lead(
        post_id=post_id,
        score=78,
        summary="Старая статическая оценка",
        draft_reply=(
            "Здравствуйте! Посмотрел задачу: выполнить проект. "
            "Сначала разберу текущую реализацию и требования, затем внесу нужные изменения по задаче. "
            "После этого проверю основной сценарий и покажу готовый рабочий результат."
        ),
        contact="@client_dev",
    )

    def rejected_judge(_text, **_kwargs):
        return LeadJudgeResult(
            accepted=False,
            decision="reject",
            score=25,
            complexity="too_complex",
            estimated_days=14,
            price_rub=0,
            summary="Задача требует профильного senior-опыта",
            reasons=["не подходит под недельный лимит"],
            risks=["высокий риск"],
            questions=[],
            draft_reply="",
        )

    created = scan_once(
        storage=storage,
        telegram_client=FakeTelegramClient(),
        lead_hub=FakeLeadHub(),
        lead_judge=rejected_judge,
        openrouter_api_key="or-test",
    )

    lead = storage.get_lead(lead_id)
    assert created == 0
    assert lead.status == "rejected"
    assert "недельный лимит" in lead.last_error

    caplog.clear()
    caplog.set_level(logging.WARNING)
    scan_once(
        storage=storage,
        telegram_client=FakeTelegramClient(),
        lead_hub=FakeLeadHub(),
        lead_judge=rejected_judge,
        openrouter_api_key="or-test",
    )

    assert "Rebuilding retired generic draft" not in caplog.text


def test_scan_once_retires_unsent_generic_lead_that_left_the_current_feed(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    post_id = storage.save_post(
        channel="kwork-web",
        message_id=77,
        post_url="https://kwork.ru/projects/77",
        text="Исправить форму на сайте",
        posted_at="2026-08-20T10:00:00+03:00",
    )
    lead_id = storage.create_lead(
        post_id=post_id,
        score=78,
        summary="Задача: Исправить форму на сайте",
        draft_reply=(
            "Здравствуйте! Посмотрел задачу: исправить форму. "
            "Сначала разберу текущую реализацию и требования, затем внесу нужные изменения по задаче. "
            "После этого проверю основной сценарий и покажу готовый рабочий результат."
        ),
        contact="https://kwork.ru/projects/77",
    )
    assert storage.record_approval(lead_id, "<lead-77@example.com>") is True

    class OtherPostSource:
        def fetch_recent_posts(self):
            return [
                FakePost(
                    channel="kwork-web",
                    message_id=78,
                    url="https://kwork.ru/projects/78",
                    text="Нужно настроить Bitrix. Отклик: https://kwork.ru/projects/78",
                    posted_at="2026-08-21T10:00:00+03:00",
                )
            ]

    assert scan_once(
        storage=storage,
        telegram_client=OtherPostSource(),
        lead_hub=FakeLeadHub(),
        openrouter_api_key="or-test",
    ) == 0

    lead = storage.get_lead(lead_id)
    assert lead.status == "rejected"
    assert "устаревший общий шаблон" in lead.last_error


def test_scan_once_does_not_retire_generic_leads_when_source_returns_no_posts(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    post_id = storage.save_post(
        channel="kwork-web",
        message_id=79,
        post_url="https://kwork.ru/projects/79",
        text="Исправить форму на сайте",
        posted_at="2026-08-20T10:00:00+03:00",
    )
    lead_id = storage.create_lead(
        post_id=post_id,
        score=78,
        summary="Задача: Исправить форму на сайте",
        draft_reply=(
            "Здравствуйте! Посмотрел задачу: исправить форму. "
            "Сначала разберу текущую реализацию и требования, затем внесу нужные изменения по задаче. "
            "После этого проверю основной сценарий и покажу готовый рабочий результат."
        ),
        contact="https://kwork.ru/projects/79",
    )

    class EmptySource:
        def fetch_recent_posts(self):
            return []

    scan_once(
        storage=storage,
        telegram_client=EmptySource(),
        lead_hub=FakeLeadHub(),
        openrouter_api_key="or-test",
    )

    assert storage.get_lead(lead_id).status == "new"


def test_scan_once_rejects_approved_generic_lead_even_when_it_is_in_current_feed(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    post = FakeTelegramClient().fetch_recent_posts()[0]
    post_id = storage.save_post(
        channel=post.channel,
        message_id=post.message_id,
        post_url=post.url,
        text=post.text,
        posted_at=post.posted_at,
    )
    lead_id = storage.create_lead(
        post_id=post_id,
        score=78,
        summary="Задача: Сверстать лендинг",
        draft_reply=(
            "Здравствуйте! Посмотрел задачу: сверстать лендинг. "
            "Сначала разберу текущую реализацию и требования, затем внесу нужные изменения по задаче. "
            "После этого проверю основной сценарий и покажу готовый рабочий результат."
        ),
        contact="@client_dev",
    )
    assert storage.record_approval(lead_id, "<lead-current@example.com>") is True

    scan_once(
        storage=storage,
        telegram_client=FakeTelegramClient(),
        lead_hub=FakeLeadHub(),
        openrouter_api_key="or-test",
    )

    lead = storage.get_lead(lead_id)
    assert lead.status == "rejected"
    assert "общий шаблон" in lead.last_error


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
            questions=["Куда должны приходить заявки после отправки формы?"],
            draft_reply="Здравствуйте! Цена 5000 руб. Уточните детали.",
            customer_goal="Получать заявки с мобильной версии без потерь",
            work_plan=["Проверить форму", "Исправить отправку", "Протестировать сценарий"],
            blocking_question="Куда должны поступать заявки?",
        )

    def fake_composer(context, seed_reply, **kwargs):
        seen_contexts.append((context, seed_reply, kwargs))
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
        openrouter_api_key="sk-or-test",
        openrouter_base_url="https://openrouter.example/v1",
        openrouter_analysis_model="openai/gpt-5.1",
        openrouter_reply_model="anthropic/claude-sonnet-4.5",
        openrouter_fallback_models=("openai/gpt-4.1",),
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
    assert seen_contexts[0][0].blocking_question == "Куда должны поступать заявки?"
    assert seen_contexts[0][0].customer_goal == "Получать заявки с мобильной версии без потерь"
    assert seen_contexts[0][0].work_plan == (
        "Проверить форму",
        "Исправить отправку",
        "Протестировать сценарий",
    )
    assert seen_contexts[0][2] == {
        "api_key": "sk-or-test",
        "model": "anthropic/claude-sonnet-4.5",
        "base_url": "https://openrouter.example/v1",
        "fallback_models": ("openai/gpt-4.1",),
    }


def test_scan_once_prices_lead_fifteen_percent_below_kwork_maximum(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()

    created = scan_once(
        storage=storage,
        telegram_client=FakeTelegramClient(),
        email_client=FakeEmailClient(),
        kwork_project_client=FakeKworkProjectClient(
            response_count=1,
            buyer_desired_budget_rub=2000,
            kwork_max_price_rub=6000,
        ),
        lead_judge=lambda *_args, **_kwargs: LeadJudgeResult(
            accepted=True,
            decision="accept",
            score=86,
            complexity="simple",
            estimated_days=2,
            price_rub=5000,
            summary="Исправить форму",
            reasons=["задача понятна"],
            risks=[],
            questions=[],
            draft_reply="Здравствуйте!",
        ),
        reply_composer=lambda _context, reply, **_kwargs: reply,
        deepseek_api_key="sk-test",
    )

    lead = storage.list_leads(status="emailed")[0]
    assert created == 1
    assert lead.buyer_desired_budget_rub == 2000
    assert lead.kwork_max_price_rub == 6000
    assert lead.proposal_price_rub == 5100


def test_scan_once_uses_desired_budget_when_kwork_maximum_is_missing(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()

    scan_once(
        storage=storage,
        telegram_client=FakeTelegramClient(),
        email_client=FakeEmailClient(),
        kwork_project_client=FakeKworkProjectClient(
            response_count=1,
            buyer_desired_budget_rub=5000,
            kwork_max_price_rub=None,
        ),
        lead_judge=lambda *_args, **_kwargs: LeadJudgeResult(
            accepted=True,
            decision="accept",
            score=86,
            complexity="simple",
            estimated_days=2,
            price_rub=12000,
            summary="Исправить форму",
            reasons=["задача понятна"],
            risks=[],
            questions=[],
            draft_reply="Здравствуйте!",
        ),
        reply_composer=lambda _context, reply, **_kwargs: reply,
        deepseek_api_key="sk-test",
    )

    lead = storage.list_leads()[0]
    assert lead.proposal_price_rub == 4300


def test_scan_once_keeps_accepted_lead_retryable_when_reply_generation_fails(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    hub = FakeLeadHub()
    project_client = FakeKworkProjectClient(
        response_count=4,
        buyer_desired_budget_rub=500,
        kwork_max_price_rub=1500,
    )

    judge_result = LeadJudgeResult(
        accepted=True,
        decision="accept",
        score=88,
        complexity="simple",
        estimated_days=1,
        price_rub=500,
        summary="Восстановить работу WordPress-сайта",
        reasons=["локальная задача"],
        risks=[],
        questions=[],
        draft_reply="Черновик анализатора не должен отправляться без проверки.",
    )

    def unavailable_reply(*_args, **_kwargs):
        raise ReplyGenerationUnavailable("quality gate rejected the draft")

    created = scan_once(
        storage=storage,
        telegram_client=FakeTelegramClient(),
        lead_hub=hub,
        kwork_project_client=project_client,
        lead_judge=lambda *_args, **_kwargs: judge_result,
        reply_composer=unavailable_reply,
        openrouter_api_key="sk-or-test",
    )

    lead = storage.list_leads()[0]
    assert created == 1
    assert lead.status == "failed"
    assert lead.draft_reply == ""
    assert lead.live_response_count == 4
    assert lead.buyer_desired_budget_rub == 500
    assert lead.kwork_max_price_rub == 1500
    assert lead.proposal_price_rub == 1300
    assert "AI-отклик" in lead.last_error
    assert not storage.get_post_rejection(lead.post_id)
    assert hub.published == [(lead.id, "", ())]


def test_scan_once_retries_failed_reply_generation_without_creating_a_duplicate(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    hub = FakeLeadHub()
    project_client = FakeKworkProjectClient(response_count=2, kwork_max_price_rub=6000)
    judge_result = LeadJudgeResult(
        accepted=True,
        decision="accept",
        score=90,
        complexity="simple",
        estimated_days=2,
        price_rub=5000,
        summary="Исправить форму заявки",
        reasons=["понятная задача"],
        risks=[],
        questions=[],
        draft_reply="Черновик анализатора.",
    )

    def unavailable_reply(*_args, **_kwargs):
        raise ReplyGenerationUnavailable("quality gate rejected the draft")

    scan_once(
        storage=storage,
        telegram_client=FakeTelegramClient(),
        lead_hub=hub,
        kwork_project_client=project_client,
        lead_judge=lambda *_args, **_kwargs: judge_result,
        reply_composer=unavailable_reply,
        openrouter_api_key="sk-or-test",
    )
    original_id = storage.list_leads()[0].id

    created = scan_once(
        storage=storage,
        telegram_client=FakeTelegramClient(),
        lead_hub=hub,
        kwork_project_client=project_client,
        lead_judge=lambda *_args, **_kwargs: judge_result,
        reply_composer=lambda *_args, **_kwargs: (
            "Здравствуйте! Проверю обработку формы заявки, найду причину сбоя и внесу точечные правки. "
            "После исправления протестирую отправку и покажу рабочий результат. Могу приступить сразу."
        ),
        openrouter_api_key="sk-or-test",
    )

    leads = storage.list_leads()
    assert created == 1
    assert len(leads) == 1
    assert leads[0].id == original_id
    assert leads[0].status == "new"
    assert leads[0].draft_reply.startswith("Здравствуйте!")
    assert len(hub.published) == 2


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


def test_process_approvals_marks_email_approval_once_without_sending(tmp_path):
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

    assert telegram_client.sent == []
    assert storage.get_lead(lead_id).status == "approved"


def test_process_approvals_does_not_run_kwork_preflight_before_gui_send(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    post_id = storage.save_post(
        channel="kwork-web",
        message_id=42,
        post_url="https://kwork.ru/projects/42/view",
        text="Нужно сделать адаптивный лендинг и настроить форму заявки.",
        posted_at="",
    )
    lead_id = storage.create_lead(
        post_id=post_id,
        score=84,
        summary="Лендинг",
        draft_reply=(
            "Здравствуйте! Посмотрел задачу по лендингу. Сверю структуру страницы, "
            "соберу адаптивную верстку и проверю отправку формы на мобильных. "
            "После тестирования покажу готовый результат."
        ),
        contact="https://kwork.ru/projects/42/view",
        proposal_title="Сделать лендинг",
        proposal_price_rub=12000,
        proposal_days=3,
    )
    storage.mark_lead_emailed(lead_id, "<lead@example.com>")

    processed = process_approvals(
        storage=storage,
        telegram_client=FakeTelegramClient(),
        email_client=FakeEmailClient(approvals=[(lead_id, "<approval@example.com>")]),
    )

    lead = storage.get_lead(lead_id)
    assert processed == 1
    assert lead.status == "approved"
    assert lead.live_response_count is None


def test_process_approvals_keeps_stale_reply_for_gui_review_without_sending(tmp_path):
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

    processed = process_approvals(
        storage=storage,
        telegram_client=telegram_client,
        email_client=FakeEmailClient(approvals=[(lead_id, approval_message_id)]),
    )

    lead = storage.get_lead(lead_id)
    assert processed == 1
    assert telegram_client.sent == []
    assert lead.status == "approved"
    assert lead.draft_reply == stale_reply
    assert approval_message_id in storage.seen_approval_message_ids()


def test_process_approvals_ignores_second_email_ok_after_gui_ready_status(tmp_path):
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

    first_processed = process_approvals(
        storage=storage,
        telegram_client=telegram_client,
        email_client=FakeEmailClient(approvals=[(lead_id, "<blocked@example.com>")]),
    )
    second_processed = process_approvals(
        storage=storage,
        telegram_client=telegram_client,
        email_client=FakeEmailClient(approvals=[(lead_id, "<retry@example.com>")]),
    )

    assert first_processed == 1
    assert second_processed == 0
    assert telegram_client.sent == []
    assert storage.get_lead(lead_id).status == "approved"


def test_process_approvals_marks_email_ok_even_with_read_only_source(tmp_path):
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

    processed = process_approvals(
        storage=storage,
        telegram_client=ReadOnlyTelegramClient(),
        email_client=FakeEmailClient(approvals=[(lead_id, "<approval@example.com>")]),
    )

    assert processed == 1
    assert storage.get_lead(lead_id).status == "approved"


def test_process_approvals_marks_kwork_lead_for_gui_without_sending(tmp_path):
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

    processed = process_approvals(
        storage=storage,
        telegram_client=telegram_client,
        email_client=email_client,
    )

    assert processed == 1
    assert telegram_client.sent == []
    assert storage.get_lead(lead_id).status == "approved"


def test_proposal_title_ignores_inline_kwork_offer_metadata():
    assert _proposal_title_from_text(
        "Нужно поправить WordPress. Предложений: 4\nОтклик: https://kwork.ru/projects/1/view"
    ) == "Нужно поправить WordPress"


def test_process_approvals_keeps_kwork_form_terms_for_gui_without_sending(tmp_path):
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

    processed = process_approvals(
        storage=storage,
        telegram_client=telegram_client,
        email_client=FakeEmailClient(approvals=[(lead_id, "<approval@example.com>")]),
    )

    assert processed == 1
    assert "10000" not in reply_text
    assert telegram_client.sent_details == []
    lead = storage.get_lead(lead_id)
    assert lead.status == "approved"
    assert lead.draft_reply == reply_text


def test_process_approvals_keeps_saved_form_terms_for_gui(tmp_path):
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

    processed = process_approvals(
        storage=storage,
        telegram_client=telegram_client,
        email_client=FakeEmailClient(approvals=[(lead_id, "<approval@example.com>")]),
    )

    assert processed == 1
    assert telegram_client.sent_details == []
    lead = storage.get_lead(lead_id)
    assert lead.status == "approved"
    assert (lead.proposal_title, lead.proposal_price_rub, lead.proposal_days) == (
        "Сохраненное название",
        14000,
        5,
    )


def test_process_approvals_keeps_legacy_reply_for_gui_review(tmp_path):
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

    processed = process_approvals(
        storage=storage,
        telegram_client=telegram_client,
        email_client=FakeEmailClient(approvals=[(lead_id, "<approval@example.com>")]),
    )

    assert processed == 1
    assert telegram_client.sent_details == []
    lead = storage.get_lead(lead_id)
    assert lead.status == "approved"
    assert lead.draft_reply == legacy_reply


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


def test_mobile_approval_sends_one_claimed_kwork_lead_and_reports_result(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    post_id = storage.save_post(
        channel="kwork-web",
        message_id=1,
        post_url="https://kwork.ru/projects/41",
        text="Сверстать лендинг",
        posted_at="2026-07-18T10:00:00+03:00",
    )
    lead_id = storage.create_lead(
        post_id=post_id,
        score=82,
        summary="Адаптивная верстка",
        draft_reply="Старый текст",
        contact="https://kwork.ru/projects/41",
        proposal_title="Старое название",
        proposal_price_rub=3000,
        proposal_days=3,
    )
    storage.mark_lead_hub_synced(lead_id, 91)
    hub = FakeLeadHub(
        commands=[
            {
                "id": 91,
                "status": "approved",
                "draft_reply": (
                    "Здравствуйте! Сверстаю адаптивный лендинг и настрою корректное отображение основных блоков. "
                    "После вёрстки проверю страницу на типовых разрешениях и исправлю найденные расхождения. "
                    "Готов приступить к работе."
                ),
                "proposal_title": "Адаптивная верстка лендинга",
                "proposal_price_rub": 6500,
                "proposal_days": 4,
            }
        ]
    )
    sender = FakeKworkSender()

    processed = process_mobile_approvals(
        storage=storage,
        lead_hub=hub,
        sender=sender,
        executor_id="desktop-main",
    )

    assert processed == 1
    assert sender.sent == [
        (
            "https://kwork.ru/projects/41",
            (
                "Здравствуйте! Сверстаю адаптивный лендинг и настрою корректное отображение основных блоков. "
                "После вёрстки проверю страницу на типовых разрешениях и исправлю найденные расхождения. "
                "Готов приступить к работе."
            ),
            6500,
            4,
            "Адаптивная верстка лендинга",
            True,
        )
    ]
    assert hub.claimed == [(91, "desktop-main")]
    assert hub.results == [(91, "desktop-main", True, "")]
    assert storage.get_lead(lead_id).status == "sent"


def test_mobile_approval_does_not_retry_after_kwork_send_when_local_persistence_fails(
    tmp_path,
    monkeypatch,
):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    post_id = storage.save_post(
        channel="kwork-web",
        message_id=43,
        post_url="https://kwork.ru/projects/43",
        text="Сверстать адаптивный лендинг",
        posted_at="2026-07-18T10:00:00+03:00",
    )
    lead_id = storage.create_lead(
        post_id=post_id,
        score=82,
        summary="Задача: Сверстать адаптивный лендинг",
        draft_reply="Старый текст",
        contact="https://kwork.ru/projects/43",
        proposal_title="Адаптивный лендинг",
        proposal_price_rub=6500,
        proposal_days=4,
    )
    storage.mark_lead_hub_synced(lead_id, 93)
    command = {
        "id": 93,
        "status": "approved",
        "draft_reply": (
            "Здравствуйте! Сверстаю адаптивный лендинг и настрою основные интерактивные блоки. "
            "После вёрстки проверю страницу на компьютере и телефоне, затем исправлю расхождения."
        ),
        "proposal_title": "Адаптивный лендинг",
        "proposal_price_rub": 6500,
        "proposal_days": 4,
    }
    hub = FakeLeadHub(commands=[command])
    sender = FakeKworkSender()

    def fail_after_external_send(*_args, **_kwargs):
        raise OSError("database write failed")

    monkeypatch.setattr(storage, "mark_sent", fail_after_external_send)

    assert process_mobile_approvals(storage, hub, sender, "desktop-main") == 1
    assert storage.get_lead(lead_id).status == "sending"
    assert hub.results == [(93, "desktop-main", True, "")]
    assert process_mobile_approvals(storage, hub, sender, "desktop-main") == 0
    assert len(sender.sent) == 1


def test_mobile_approval_does_not_retry_when_only_hub_result_reporting_fails(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    post_id = storage.save_post(
        channel="kwork-web",
        message_id=44,
        post_url="https://kwork.ru/projects/44",
        text="Сверстать адаптивный лендинг",
        posted_at="2026-07-18T10:00:00+03:00",
    )
    lead_id = storage.create_lead(
        post_id=post_id,
        score=82,
        summary="Задача: Сверстать адаптивный лендинг",
        draft_reply="Старый текст",
        contact="https://kwork.ru/projects/44",
        proposal_title="Адаптивный лендинг",
        proposal_price_rub=6500,
        proposal_days=4,
    )
    storage.mark_lead_hub_synced(lead_id, 94)
    command = {
        "id": 94,
        "status": "approved",
        "draft_reply": (
            "Здравствуйте! Сверстаю адаптивный лендинг и настрою основные интерактивные блоки. "
            "После вёрстки проверю страницу на компьютере и телефоне, затем исправлю расхождения."
        ),
        "proposal_title": "Адаптивный лендинг",
        "proposal_price_rub": 6500,
        "proposal_days": 4,
    }

    class FailingResultHub(FakeLeadHub):
        def report_result(self, lead_id, executor_id, *, sent, error=""):
            raise TimeoutError("hub result timeout")

    hub = FailingResultHub(commands=[command])
    sender = FakeKworkSender()

    assert process_mobile_approvals(storage, hub, sender, "desktop-main") == 1
    assert storage.get_lead(lead_id).status == "sent"
    assert process_mobile_approvals(storage, hub, sender, "desktop-main") == 0
    assert len(sender.sent) == 1


def test_mobile_approval_blocks_old_generic_fallback_before_kwork_send(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    post_id = storage.save_post(
        channel="kwork-web",
        message_id=2,
        post_url="https://kwork.ru/projects/42",
        text="Нужно найти расхождение серверной аналитики с Яндекс Метрикой.",
        posted_at="2026-08-21T08:53:40+03:00",
    )
    generic_reply = (
        "Здравствуйте! Посмотрел задачу: починить аналитику. "
        "Сначала разберу текущую реализацию и требования, затем внесу нужные изменения по задаче. "
        "После этого проверю основной сценарий и покажу готовый рабочий результат."
    )
    lead_id = storage.create_lead(
        post_id=post_id,
        score=78,
        summary="Задача: Найти расхождение серверной аналитики с Яндекс Метрикой",
        draft_reply=generic_reply,
        contact="https://kwork.ru/projects/42",
        proposal_title="Починить аналитику",
        proposal_price_rub=1300,
        proposal_days=2,
    )
    storage.mark_lead_hub_synced(lead_id, 92)
    hub = FakeLeadHub(
        commands=[
            {
                "id": 92,
                "status": "approved",
                "draft_reply": generic_reply,
                "proposal_title": "Починить аналитику",
                "proposal_price_rub": 1300,
                "proposal_days": 2,
            }
        ]
    )
    sender = FakeKworkSender()

    processed = process_mobile_approvals(
        storage=storage,
        lead_hub=hub,
        sender=sender,
        executor_id="desktop-main",
    )

    assert processed == 0
    assert sender.sent == []
    assert hub.results[0][0:3] == (92, "desktop-main", False)
    assert "общий шаблон" in hub.results[0][3]
    assert storage.get_lead(lead_id).status == "failed"


def test_scan_command_uses_shared_runtime_pipeline(monkeypatch, tmp_path):
    config = SimpleNamespace(database_path=tmp_path / "leads.sqlite3")
    runtime = (object(), object(), object(), object())
    calls = []

    monkeypatch.setattr(sys, "argv", ["app.main", "scan"])
    monkeypatch.setattr(main_module, "load_config", lambda: config)
    monkeypatch.setattr(main_module, "build_runtime", lambda _config: runtime)
    monkeypatch.setattr(main_module, "_configure_runtime_logging", lambda _path: None)
    monkeypatch.setattr(
        main_module,
        "_scan_runtime_once",
        lambda *args: calls.append(args),
    )

    assert main_module.main() == 0
    assert calls == [(*runtime, config)]


def test_mobile_control_command_uses_same_runtime_objects(monkeypatch, tmp_path):
    config = SimpleNamespace(database_path=tmp_path / "leads.sqlite3")
    runtime = (object(), object(), object(), object())
    calls = []

    monkeypatch.setattr(sys, "argv", ["app.main", "mobile-control"])
    monkeypatch.setattr(main_module, "load_config", lambda: config)
    monkeypatch.setattr(main_module, "build_runtime", lambda _config: runtime)
    monkeypatch.setattr(main_module, "_configure_runtime_logging", lambda _path: None)
    monkeypatch.setattr(
        main_module,
        "run_mobile_control_loop",
        lambda *args: calls.append(args),
    )

    assert main_module.main() == 0
    assert calls == [(*runtime, config)]


def test_runtime_logging_persists_utf8_for_hidden_mobile_process(tmp_path):
    root_logger = logging.Logger("lead-funnel-test", level=logging.INFO)
    log_path = _configure_runtime_logging(
        tmp_path / "leads.sqlite3",
        root_logger=root_logger,
        include_console=False,
    )

    root_logger.info("Мобильный запуск: проверка")
    for handler in root_logger.handlers:
        handler.flush()

    assert log_path == tmp_path / "lead-funnel.log"
    assert "Мобильный запуск: проверка" in log_path.read_text(encoding="utf-8")


def test_main_logs_configuration_error_before_hidden_mobile_process_exits(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["app.main", "mobile-control"])

    def fail_config():
        raise ValueError("broken env")

    monkeypatch.setattr(main_module, "load_config", fail_config)

    try:
        main_module.main()
    except ValueError as exc:
        assert str(exc) == "broken env"
    else:
        raise AssertionError("main() must propagate configuration errors")

    for handler in logging.getLogger().handlers:
        handler.flush()
    log_text = (tmp_path / "data" / "lead-funnel.log").read_text(encoding="utf-8")
    assert "Unable to load application configuration" in log_text


def test_scan_execution_lock_prevents_desktop_and_mobile_overlap(tmp_path):
    lock_path = tmp_path / "scan.lock"

    with _scan_execution_lock(lock_path) as first_acquired:
        with _scan_execution_lock(lock_path) as second_acquired:
            assert first_acquired is True
            assert second_acquired is False

    with _scan_execution_lock(lock_path) as acquired_after_release:
        assert acquired_after_release is True


def test_idle_mobile_control_resolves_chrome_cookie_only_once(monkeypatch):
    config = SimpleNamespace(scan_interval_seconds=60, lead_hub_executor_id="desktop-main")
    cookie_calls = []
    approval_cookies = []
    sleep_calls = 0

    class IdleHub:
        def fetch_monitor_control(self):
            return {"desired_state": "stopped", "scan_requested": False}

        def report_monitor_heartbeat(self, *_args, **_kwargs):
            return {}

    monkeypatch.setattr(
        main_module,
        "_resolve_kwork_cookie",
        lambda _config: cookie_calls.append(True) or "session-cookie",
    )
    monkeypatch.setattr(
        main_module,
        "_process_mobile_approvals_from_runtime",
        lambda _storage, _hub, _config, cookie: approval_cookies.append(cookie) or 0,
    )

    def stop_after_two_polls(_seconds):
        nonlocal sleep_calls
        sleep_calls += 1
        if sleep_calls >= 2:
            raise StopIteration

    monkeypatch.setattr(main_module.time, "sleep", stop_after_two_polls)

    try:
        main_module.run_mobile_control_loop(object(), object(), IdleHub(), object(), config)
    except StopIteration:
        pass
    else:
        raise AssertionError("mobile control loop must be stopped by the test")

    assert cookie_calls == [True]
    assert approval_cookies == ["session-cookie", "session-cookie"]


def test_mobile_control_scans_when_local_autosend_is_enabled(monkeypatch):
    config = SimpleNamespace(
        scan_interval_seconds=60,
        lead_hub_executor_id="desktop-main",
        kwork_auto_send=True,
    )
    scans = []

    class StoppedHub:
        def fetch_monitor_control(self):
            return {"desired_state": "stopped", "scan_requested": False}

        def report_monitor_heartbeat(self, *_args, **_kwargs):
            return {}

    monkeypatch.setattr(main_module, "_resolve_kwork_cookie", lambda _config: "")
    monkeypatch.setattr(main_module, "_process_mobile_approvals_from_runtime", lambda *_args: 0)
    monkeypatch.setattr(main_module, "_scan_runtime_once", lambda *_args: scans.append(True))
    def stop_loop(_seconds):
        raise StopIteration

    monkeypatch.setattr(main_module.time, "sleep", stop_loop)

    try:
        main_module.run_mobile_control_loop(object(), object(), StoppedHub(), object(), config)
    except StopIteration:
        pass

    assert scans == [True]
