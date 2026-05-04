from email.message import EmailMessage

from app.email_client import build_lead_email, parse_approval_messages
from app.storage import Lead


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
