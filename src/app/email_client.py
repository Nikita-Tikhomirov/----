from __future__ import annotations

import imaplib
import re
import smtplib
from dataclasses import dataclass
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser
from typing import Iterable

from app.storage import Lead, Order


APPROVAL_PATTERN = re.compile(r"^\s*OK\s+(\d+)\s*$", re.IGNORECASE | re.MULTILINE)
ORDER_APPROVAL_PATTERN = re.compile(r"^\s*(DONE|APPROVE)\s+(\d+)\s*$", re.IGNORECASE | re.MULTILINE)
ORDER_REVISION_PATTERN = re.compile(
    r"^\s*(FIX|REVISION)\s+(\d+)\s*:\s*(.+?)\s*$",
    re.IGNORECASE | re.MULTILINE,
)


@dataclass(frozen=True)
class OrderReviewCommand:
    order_id: int
    message_id: str
    decision: str
    notes: str


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
        manual_reply_only: bool = False,
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
        self.manual_reply_only = manual_reply_only

    def send_lead(self, lead: Lead) -> str:
        message = build_lead_email(
            lead,
            self.mail_from,
            self.mail_to,
            manual_reply_only=self.manual_reply_only,
        )
        with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as smtp:
            smtp.starttls()
            smtp.login(self.smtp_user, self.smtp_password)
            smtp.send_message(message)
        return message["Message-ID"]

    def fetch_approvals(self, seen_message_ids: set[str]) -> list[tuple[int, str]]:
        messages = self._fetch_unseen_messages()
        return parse_approval_messages(messages, seen_message_ids)

    def send_order_for_approval(self, order: Order) -> str:
        message = build_order_approval_email(order, self.mail_from, self.mail_to)
        with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as smtp:
            smtp.starttls()
            smtp.login(self.smtp_user, self.smtp_password)
            smtp.send_message(message)
        return message["Message-ID"]

    def fetch_order_reviews(self, seen_message_ids: set[str]) -> list[OrderReviewCommand]:
        messages = self._fetch_unseen_messages()
        return parse_order_review_messages(messages, seen_message_ids)

    def _fetch_unseen_messages(self) -> list[EmailMessage]:
        parsed: list[EmailMessage] = []
        with imaplib.IMAP4_SSL(self.imap_host, self.imap_port) as imap:
            imap.login(self.imap_user, self.imap_password)
            imap.select("INBOX")
            _, data = imap.search(None, "ALL")
            message_ids = data[0].split()[-80:]
            for message_id in message_ids:
                _, fetched = imap.fetch(message_id, "(RFC822)")
                raw = fetched[0][1]
                parsed.append(BytesParser(policy=policy.default).parsebytes(raw))
        return parsed


def build_lead_email(
    lead: Lead,
    from_address: str,
    to_address: str,
    manual_reply_only: bool = False,
) -> EmailMessage:
    message = EmailMessage()
    message["From"] = from_address
    message["To"] = to_address
    message["Subject"] = f"Новый заказ #{lead.id}: score {lead.score}"
    message["Message-ID"] = f"<lead-{lead.id}@telegram-lead-funnel.local>"
    message.set_content(_lead_email_body(lead, manual_reply_only), charset="utf-8")
    return message


def _lead_email_body(lead: Lead, manual_reply_only: bool) -> str:
    lines = [
        f"Lead ID: {lead.id}",
        f"Score: {lead.score}",
        f"Ссылка на пост: {lead.post_url}",
        f"Контакт: {lead.contact}",
    ]
    contact_url = _telegram_contact_url(lead.contact)
    if contact_url:
        lines.append(f"Открыть контакт: {contact_url}")
    lines.extend(
        [
            "",
            "AI-ОЦЕНКА:",
            lead.summary,
            "",
            "СКОПИРОВАТЬ ОТКЛИК:",
            "-----",
            lead.draft_reply,
            "-----",
        ]
    )
    if manual_reply_only:
        lines.extend(
            [
                "",
                "РУЧНОЙ РЕЖИМ:",
                "1. Открой ссылку на пост или контакт.",
                "2. Скопируй текст между линиями выше.",
                "3. Вставь его в Telegram и отправь вручную.",
            ]
        )
    else:
        lines.extend(
            [
                "",
                "АПРУВ:",
                f"Чтобы отправить отклик автоматически, ответь на это письмо строкой: OK {lead.id}",
            ]
        )
    return "\n".join(lines)


def _telegram_contact_url(contact: str) -> str:
    if contact.startswith("@"):
        return f"https://t.me/{contact[1:]}"
    if contact.startswith("https://t.me/"):
        return contact
    return ""


def build_order_approval_email(
    order: Order,
    from_address: str,
    to_address: str,
) -> EmailMessage:
    message = EmailMessage()
    message["From"] = from_address
    message["To"] = to_address
    message["Subject"] = f"Заказ #{order.id} готов к проверке: {order.title}"
    message["Message-ID"] = f"<order-{order.id}@telegram-lead-funnel.local>"
    message.set_content(_order_approval_email_body(order), charset="utf-8")
    return message


def _order_approval_email_body(order: Order) -> str:
    proposal = build_customer_proposal(order)
    return "\n".join(
        [
            f"Order ID: {order.id}",
            f"Статус: {order.status}",
            f"Контакт: {order.contact}",
            f"Название: {order.title}",
            "",
            "Задача:",
            order.brief,
            "",
            "Результат:",
            order.deliverable,
            "",
            "ПРЕДЛОЖЕНИЕ / ПИСЬМО ЗАКАЗЧИКУ:",
            "-----",
            proposal,
            "-----",
            "",
            f"Если готово, ответь строкой: DONE {order.id}",
            f"Если нужны правки, ответь строкой: FIX {order.id}: что поправить",
        ]
    )


def build_customer_proposal(order: Order) -> str:
    task_summary = _shorten(_clean_text(order.brief), limit=260)
    deliverable = _clean_text(order.deliverable)
    revision_notes = _clean_text(order.revision_notes)

    lines = [
        "Здравствуйте!",
        "",
        f"Подготовил результат по задаче «{order.title}».",
    ]
    if task_summary:
        lines.extend(["", "Что учел по задаче:", task_summary])
    if revision_notes:
        lines.extend(["", "Также учел последние правки:", revision_notes])
    if deliverable:
        lines.extend(["", "Результат:", deliverable])
    lines.extend(
        [
            "",
            "Пожалуйста, посмотрите и напишите, все ли ок. Если нужны небольшие правки — пришлите список, оперативно поправлю.",
        ]
    )
    return "\n".join(lines)


def _clean_text(text: str) -> str:
    return "\n".join(line.strip() for line in text.strip().splitlines() if line.strip())


def _shorten(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


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


def parse_order_review_messages(
    messages: Iterable[EmailMessage],
    seen_message_ids: set[str],
) -> list[OrderReviewCommand]:
    reviews: list[OrderReviewCommand] = []
    for message in messages:
        message_id = message.get("Message-ID", "")
        if not message_id or message_id in seen_message_ids:
            continue
        body = _message_text(message)
        approval = ORDER_APPROVAL_PATTERN.search(body)
        if approval:
            reviews.append(
                OrderReviewCommand(
                    order_id=int(approval.group(2)),
                    message_id=message_id,
                    decision="approved",
                    notes="",
                )
            )
            continue
        revision = ORDER_REVISION_PATTERN.search(body)
        if revision:
            reviews.append(
                OrderReviewCommand(
                    order_id=int(revision.group(2)),
                    message_id=message_id,
                    decision="revision",
                    notes=revision.group(3).strip(),
                )
            )
    return reviews


def _message_text(message: EmailMessage) -> str:
    if message.is_multipart():
        parts = [
            part.get_content()
            for part in message.walk()
            if part.get_content_type() == "text/plain"
        ]
        return "\n".join(parts)
    return message.get_content()
