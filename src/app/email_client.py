from __future__ import annotations

import imaplib
import re
import smtplib
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser
from typing import Iterable

from app.storage import Lead


APPROVAL_PATTERN = re.compile(r"^\s*OK\s+(\d+)\s*$", re.IGNORECASE | re.MULTILINE)


class EmailClient:
    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        mail_from: str,
        mail_to: str,
        imap_host: str,
        imap_port: int,
        imap_user: str,
        imap_password: str,
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.mail_from = mail_from
        self.mail_to = mail_to
        self.imap_host = imap_host
        self.imap_port = imap_port
        self.imap_user = imap_user
        self.imap_password = imap_password

    def send_lead(self, lead: Lead) -> str:
        message = build_lead_email(lead, self.mail_from, self.mail_to)
        with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as smtp:
            smtp.starttls()
            smtp.login(self.smtp_user, self.smtp_password)
            smtp.send_message(message)
        return message["Message-ID"]

    def fetch_approvals(self, seen_message_ids: set[str]) -> list[tuple[int, str]]:
        messages = self._fetch_unseen_messages()
        return parse_approval_messages(messages, seen_message_ids)

    def _fetch_unseen_messages(self) -> list[EmailMessage]:
        parsed: list[EmailMessage] = []
        with imaplib.IMAP4_SSL(self.imap_host, self.imap_port) as imap:
            imap.login(self.imap_user, self.imap_password)
            imap.select("INBOX")
            _, data = imap.search(None, "UNSEEN")
            for message_id in data[0].split():
                _, fetched = imap.fetch(message_id, "(RFC822)")
                raw = fetched[0][1]
                parsed.append(BytesParser(policy=policy.default).parsebytes(raw))
        return parsed


def build_lead_email(lead: Lead, from_address: str, to_address: str) -> EmailMessage:
    message = EmailMessage()
    message["From"] = from_address
    message["To"] = to_address
    message["Subject"] = f"Новый Telegram-заказ #{lead.id}: score {lead.score}"
    message["Message-ID"] = f"<lead-{lead.id}@telegram-lead-funnel.local>"
    message.set_content(
        "\n".join(
            [
                f"Lead ID: {lead.id}",
                f"Score: {lead.score}",
                f"Ссылка: {lead.post_url}",
                f"Контакт: {lead.contact}",
                "",
                "Резюме:",
                lead.summary,
                "",
                "Черновик отклика:",
                lead.draft_reply,
                "",
                f"Чтобы отправить отклик, ответь на это письмо строкой: OK {lead.id}",
            ]
        ),
        charset="utf-8",
    )
    return message


def parse_approval_messages(
    messages: Iterable[EmailMessage],
    seen_message_ids: set[str],
) -> list[tuple[int, str]]:
    approvals: list[tuple[int, str]] = []
    for message in messages:
        message_id = message.get("Message-ID", "")
        if not message_id or message_id in seen_message_ids:
            continue
        body = _message_text(message)
        match = APPROVAL_PATTERN.search(body)
        if match:
            approvals.append((int(match.group(1)), message_id))
    return approvals


def _message_text(message: EmailMessage) -> str:
    if message.is_multipart():
        parts = [
            part.get_content()
            for part in message.walk()
            if part.get_content_type() == "text/plain"
        ]
        return "\n".join(parts)
    return message.get_content()
