from __future__ import annotations

import argparse
import logging
import time
from typing import Protocol

from app.config import AppConfig, load_config
from app.email_client import EmailClient
from app.lead_filter import evaluate_post
from app.storage import Storage
from app.telegram_client import TelegramLeadClient

logger = logging.getLogger(__name__)


class PostSource(Protocol):
    def fetch_recent_posts(self):
        ...

    def send_message(self, contact: str, text: str) -> str:
        ...


class LeadMailer(Protocol):
    def send_lead(self, lead) -> str:
        ...

    def fetch_approvals(self, seen_message_ids: set[str]) -> list[tuple[int, str]]:
        ...


def scan_once(
    storage: Storage,
    telegram_client: PostSource,
    email_client: LeadMailer,
) -> int:
    created = 0
    for post in telegram_client.fetch_recent_posts():
        post_id = storage.save_post(
            channel=post.channel,
            message_id=post.message_id,
            post_url=post.url,
            text=post.text,
            posted_at=post.posted_at,
        )
        evaluation = evaluate_post(post.text)
        if not evaluation.accepted:
            logger.info("Rejected post %s/%s: %s", post.channel, post.message_id, evaluation.reasons)
            continue

        lead_id = storage.create_lead(
            post_id=post_id,
            score=evaluation.score,
            summary=evaluation.summary,
            draft_reply=evaluation.draft_reply,
            contact=evaluation.contact,
        )
        lead = storage.get_lead(lead_id)
        if lead.status != "new":
            continue
        email_message_id = email_client.send_lead(lead)
        storage.mark_lead_emailed(lead_id, email_message_id)
        logger.info("Emailed lead %s from %s", lead_id, post.url)
        created += 1
    return created


def process_approvals(
    storage: Storage,
    telegram_client: PostSource,
    email_client: LeadMailer,
    max_sends: int = 5,
) -> int:
    sent = 0
    approvals = email_client.fetch_approvals(storage.seen_approval_message_ids())
    for lead_id, approval_message_id in approvals:
        if sent >= max_sends:
            logger.warning("Send limit reached, skipping remaining approvals")
            break
        if not storage.record_approval(lead_id, approval_message_id):
            logger.info("Skipping duplicate or invalid approval for lead %s", lead_id)
            continue

        lead = storage.get_lead(lead_id)
        try:
            telegram_message_id = telegram_client.send_message(lead.contact, lead.draft_reply)
        except Exception:
            logger.exception("Failed to send Telegram reply for lead %s", lead_id)
            storage.mark_failed(lead_id)
            continue
        storage.mark_sent(lead_id, lead.contact, telegram_message_id)
        logger.info("Sent approved lead %s to %s", lead_id, lead.contact)
        sent += 1
    return sent


def build_runtime(config: AppConfig):
    storage = Storage(config.database_path)
    storage.initialize()
    telegram_client = TelegramLeadClient(
        api_id=config.telegram_api_id,
        api_hash=config.telegram_api_hash,
        session_name=config.telegram_session_name,
        channels=config.telegram_channels,
        max_posts_per_channel=config.max_posts_per_channel,
    )
    email_client = EmailClient(
        smtp_host=config.smtp_host,
        smtp_port=config.smtp_port,
        smtp_user=config.smtp_user,
        smtp_password=config.smtp_password,
        mail_from=config.mail_from,
        mail_to=config.mail_to,
        imap_host=config.imap_host,
        imap_port=config.imap_port,
        imap_user=config.imap_user,
        imap_password=config.imap_password,
    )
    return storage, telegram_client, email_client


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Telegram lead funnel")
    parser.add_argument("command", choices=("scan", "watch", "approvals"))
    args = parser.parse_args()

    config = load_config()
    storage, telegram_client, email_client = build_runtime(config)

    if args.command == "scan":
        scan_once(storage, telegram_client, email_client)
        return 0
    if args.command == "approvals":
        process_approvals(
            storage,
            telegram_client,
            email_client,
            max_sends=config.max_sends_per_run,
        )
        return 0

    while True:
        scan_once(storage, telegram_client, email_client)
        process_approvals(
            storage,
            telegram_client,
            email_client,
            max_sends=config.max_sends_per_run,
        )
        time.sleep(config.scan_interval_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
