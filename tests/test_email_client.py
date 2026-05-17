from email.message import EmailMessage

from app.email_client import (
    build_customer_proposal,
    build_lead_email,
    build_order_approval_email,
    parse_approval_messages,
    parse_order_review_messages,
)
from app.storage import Lead, Order


def test_build_lead_email_contains_reply_instruction():
    lead = Lead(
        id=12,
        post_id=3,
        score=86,
        summary="HTML/CSS лендинг на 1-2 дня",
        draft_reply="Здравствуйте! Готов быстро помочь с лендингом.",
        contact="@client_dev",
        status="new",
        post_url="https://t.me/jobs/42",
    )

    message = build_lead_email(
        lead=lead,
        from_address="bot@example.com",
        to_address="me@example.com",
    )

    assert message["Subject"] == "Новый Telegram-заказ #12: score 86"
    assert "OK 12" in message.get_content()
    assert "https://t.me/jobs/42" in message.get_content()
    assert "Здравствуйте!" in message.get_content()


def test_build_manual_lead_email_contains_copyable_reply_and_no_ok_instruction():
    lead = Lead(
        id=12,
        post_id=3,
        score=86,
        summary="HTML/CSS лендинг на 1-2 дня",
        draft_reply="Здравствуйте! Готов быстро помочь с лендингом.",
        contact="@client_dev",
        status="new",
        post_url="https://t.me/jobs/42",
    )

    message = build_lead_email(
        lead=lead,
        from_address="bot@example.com",
        to_address="me@example.com",
        manual_reply_only=True,
    )
    content = message.get_content()

    assert "РУЧНОЙ РЕЖИМ" in content
    assert "СКОПИРОВАТЬ ОТКЛИК" in content
    assert "https://t.me/client_dev" in content
    assert "OK 12" not in content


def test_parse_approval_messages_reads_ok_lead_id_once():
    approved = EmailMessage()
    approved["Message-ID"] = "<approval-1@example.com>"
    approved.set_content("OK 42\n")

    ignored = EmailMessage()
    ignored["Message-ID"] = "<ignored@example.com>"
    ignored.set_content("Спасибо, посмотрю позже")

    approvals = parse_approval_messages([approved, ignored], seen_message_ids=set())

    assert approvals == [(42, "<approval-1@example.com>")]


def test_parse_approval_messages_skips_seen_message_ids():
    approved = EmailMessage()
    approved["Message-ID"] = "<approval-1@example.com>"
    approved.set_content("OK 42\n")

    approvals = parse_approval_messages(
        [approved],
        seen_message_ids={"<approval-1@example.com>"},
    )

    assert approvals == []


def test_build_order_approval_email_contains_review_commands():
    order = Order(
        id=7,
        lead_id=None,
        contact="@client_dev",
        title="Лендинг",
        brief="Сверстать HTML/CSS/JS лендинг",
        status="ready_for_approval",
        deliverable="Готовая ссылка: https://example.com",
        revision_notes="",
        created_at="2026-05-04 10:00:00",
        updated_at="2026-05-04 10:30:00",
    )

    message = build_order_approval_email(order, "bot@example.com", "me@example.com")
    content = message.get_content()

    assert message["Subject"] == "Заказ #7 готов к проверке: Лендинг"
    assert "DONE 7" in content
    assert "FIX 7:" in content
    assert "ПРЕДЛОЖЕНИЕ / ПИСЬМО ЗАКАЗЧИКУ" in content
    assert "Подготовил результат по задаче «Лендинг»" in content
    assert "Сверстать HTML/CSS/JS лендинг" in content
    assert "https://example.com" in content



def test_build_customer_proposal_uses_order_details_and_revision_notes():
    order = Order(
        id=8,
        lead_id=None,
        contact="client@example.com",
        title="Правки WordPress",
        brief="Поправить форму заявки и мобильный адаптив на WordPress-сайте",
        status="ready_for_approval",
        deliverable="Тестовая версия: https://example.com/wp",
        revision_notes="Кнопку сделать заметнее",
        created_at="2026-05-04 10:00:00",
        updated_at="2026-05-04 10:30:00",
    )

    proposal = build_customer_proposal(order)

    assert "Правки WordPress" in proposal
    assert "Поправить форму заявки" in proposal
    assert "Кнопку сделать заметнее" in proposal
    assert "https://example.com/wp" in proposal
    assert "шаблон" not in proposal.lower()

def test_parse_order_review_messages_reads_done_and_fix_commands_once():
    done = EmailMessage()
    done["Message-ID"] = "<done@example.com>"
    done.set_content("DONE 7\n")

    revision = EmailMessage()
    revision["Message-ID"] = "<fix@example.com>"
    revision.set_content("FIX 8: поправить мобильную форму\n")

    seen = EmailMessage()
    seen["Message-ID"] = "<seen@example.com>"
    seen.set_content("DONE 9\n")

    reviews = parse_order_review_messages(
        [done, revision, seen],
        seen_message_ids={"<seen@example.com>"},
    )

    assert [(item.order_id, item.decision, item.notes, item.message_id) for item in reviews] == [
        (7, "approved", "", "<done@example.com>"),
        (8, "revision", "поправить мобильную форму", "<fix@example.com>"),
    ]
