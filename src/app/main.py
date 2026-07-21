from __future__ import annotations

import argparse
import logging
import re
import time
from pathlib import Path
from typing import Protocol

from app.ai_lead_judge import (
    DEFAULT_ACCEPT_DECISIONS,
    DEFAULT_BLOCKED_KEYWORDS,
    DEFAULT_HARD_REJECT_KEYWORDS,
    LeadJudgeResult,
    judge_lead,
)
from app.attachments import AttachmentProcessingResult, build_attachment_report
from app.chrome_cookies import chrome_cookie_header
from app.config import AppConfig, load_config
from app.handoff import write_codex_handoff
from app.kwork_client import KworkProjectClient
from app.kwork_sender import KworkReplySender
from app.kwork_source import KworkWebSource
from app.lead_filter import evaluate_post
from app.lead_api_client import LeadHubClient
from app.public_telegram_client import PublicTelegramClient
from app.reply_composer import (
    ReplyDraftContext,
    compose_customer_reply,
    reply_delivery_issue_summary,
)
from app.storage import Storage
from app.telegram_client import TelegramLeadClient

logger = logging.getLogger(__name__)


class PostSource(Protocol):
    def fetch_recent_posts(self):
        ...

    def send_message(
        self,
        contact: str,
        text: str,
        *,
        price_rub: int | None = None,
        days: int | None = None,
        title: str = "",
    ) -> str:
        ...


class ProjectInspector(Protocol):
    def inspect(self, contact: str):
        ...


def scan_once(
    storage: Storage,
    telegram_client: PostSource,
    lead_hub: LeadHubClient | None = None,
    # Compatibility seam for historical unit tests. Production never wires this;
    # build_runtime always supplies the mobile hub instead.
    email_client=None,
    deepseek_api_key: str = "",
    deepseek_model: str = "deepseek-chat",
    openrouter_api_key: str = "",
    openrouter_base_url: str = "https://openrouter.ai/api/v1",
    openrouter_vision_model: str = "",
    openrouter_vision_mode: str = "smart",
    kwork_project_client: ProjectInspector | None = None,
    kwork_max_responses: int = 5,
    lead_judge=judge_lead,
    reply_composer=compose_customer_reply,
    attachment_context_builder=build_attachment_report,
    kwork_cookie: str = "",
    kwork_use_browser: bool = True,
    kwork_cdp_url: str = "http://127.0.0.1:9222",
    kwork_browser_profile_dir: str = "",
    lead_min_score: int = 60,
    lead_max_days: int = 7,
    lead_accept_decisions: tuple[str, ...] = DEFAULT_ACCEPT_DECISIONS,
    lead_blocked_keywords: tuple[str, ...] = DEFAULT_BLOCKED_KEYWORDS,
    lead_hard_reject_keywords: tuple[str, ...] = DEFAULT_HARD_REJECT_KEYWORDS,
    lead_required_keywords: tuple[str, ...] = (),
) -> int:
    # Older extensions called scan_once(storage, source, email_client) positionally.
    # Keep that test seam while production always supplies LeadHubClient here.
    if lead_hub is not None and not hasattr(lead_hub, "publish_lead") and email_client is None:
        email_client = lead_hub
        lead_hub = None
    created = 0
    for post in telegram_client.fetch_recent_posts():
        post_id = storage.save_post(
            channel=post.channel,
            message_id=post.message_id,
            post_url=post.url,
            text=post.text,
            posted_at=post.posted_at,
        )
        existing_lead = storage.get_lead_for_post(post_id)
        if existing_lead is not None:
            _refresh_existing_lead_live_status(
                storage=storage,
                lead=existing_lead,
                kwork_project_client=kwork_project_client,
                kwork_max_responses=kwork_max_responses,
            )
            if _deliver_new_lead(storage, lead_hub, email_client, existing_lead):
                created += 1
            else:
                logger.info("Skipping existing lead for post %s/%s", post.channel, post.message_id)
            continue
        rejection_reason = storage.get_post_rejection(post_id)
        if rejection_reason:
            logger.info(
                "Skipping durably rejected post %s/%s: %s",
                post.channel,
                post.message_id,
                rejection_reason,
            )
            continue
        evaluation = evaluate_post(
            post.text,
            blocked_keywords=lead_blocked_keywords,
            required_keywords=lead_required_keywords,
        )
        if not evaluation.accepted:
            logger.info("Rejected post %s/%s: %s", post.channel, post.message_id, evaluation.reasons)
            storage.record_post_rejection(post_id, "; ".join(evaluation.reasons))
            continue

        project_text = post.text
        project_summary_suffix = ""
        attachment_context = ""
        attachment_reports = ()
        kwork_facts: tuple[str, ...] = ()
        project_info = None
        project_title = ""
        project_description = ""
        project_page_text = ""
        if kwork_project_client is not None:
            project_info = kwork_project_client.inspect(evaluation.contact)
            if project_info.is_unavailable:
                logger.info(
                    "Rejected post %s/%s: %s",
                    post.channel,
                    post.message_id,
                    project_info.reason,
                )
                storage.record_post_rejection(post_id, project_info.reason or "Kwork заказ недоступен")
                continue
            kwork_facts = tuple(getattr(project_info, "facts", ()))
            project_title = project_info.title
            project_description = project_info.description
            project_page_text = project_info.page_text
            if not project_info.has_response_count:
                logger.info(
                    "Rejected post %s/%s: cannot verify Kwork responses (%s)",
                    post.channel,
                    post.message_id,
                    project_info.reason,
                )
                continue
            if project_info.has_response_count and project_info.response_count > kwork_max_responses:
                logger.info(
                    "Rejected post %s/%s: Kwork responses %s > %s",
                    post.channel,
                    post.message_id,
                    project_info.response_count,
                    kwork_max_responses,
                )
                storage.record_post_rejection(
                    post_id,
                    f"Kwork откликов {project_info.response_count} больше лимита {kwork_max_responses}",
                )
                continue
            if project_info.has_response_count:
                project_summary_suffix = f", откликов: {project_info.response_count}"
            if project_info.attachments:
                attachment_lead_context = "\n\n".join(
                    part
                    for part in (
                        post.text,
                        project_info.title,
                        project_info.description,
                        project_info.page_text,
                    )
                    if part
                )
                attachment_result = _build_attachment_processing_result(
                    attachment_context_builder,
                    project_info.attachments,
                    cookie=kwork_cookie,
                    use_browser=kwork_use_browser,
                    cdp_url=kwork_cdp_url,
                    browser_profile_dir=kwork_browser_profile_dir,
                    output_dir=storage.database_path.parent / "attachments" / f"post_{post_id}",
                    lead_context=attachment_lead_context,
                    deepseek_api_key=deepseek_api_key,
                    deepseek_model=deepseek_model,
                    openrouter_api_key=openrouter_api_key,
                    openrouter_base_url=openrouter_base_url,
                    openrouter_vision_model=openrouter_vision_model,
                    openrouter_vision_mode=openrouter_vision_mode,
                )
                attachment_context = attachment_result.context
                attachment_reports = attachment_result.reports
            if project_info.title or project_info.description or project_info.page_text or project_info.attachments or kwork_facts:
                project_text = "\n\n".join(
                    part
                    for part in [
                        post.text,
                        f"Kwork title: {project_info.title}" if project_info.title else "",
                        f"Kwork description: {project_info.description}" if project_info.description else "",
                        "Kwork facts:\n" + "\n".join(kwork_facts) if kwork_facts else "",
                        f"Kwork page text: {project_info.page_text}" if project_info.page_text else "",
                        "Kwork attachments:\n" + "\n".join(project_info.attachments) if project_info.attachments else "",
                        f"Kwork attachment contents:\n{attachment_context}" if attachment_context else "",
                    ]
                    if part
                )

        judge_result = lead_judge(
            project_text,
            api_key=deepseek_api_key,
            model=deepseek_model,
            min_score=lead_min_score,
            max_estimated_days=lead_max_days,
            accept_decisions=lead_accept_decisions,
            blocked_keywords=lead_blocked_keywords,
            hard_reject_keywords=lead_hard_reject_keywords,
        )
        if not judge_result.accepted:
            logger.info(
                "Rejected post %s/%s by AI judge: %s",
                post.channel,
                post.message_id,
                "; ".join(judge_result.reasons),
            )
            storage.record_post_rejection(post_id, "; ".join(judge_result.reasons))
            continue

        reply_title = project_title.strip() or _proposal_title_from_text(post.text, judge_result.summary)
        reply_context = ReplyDraftContext(
            title=reply_title,
            task_summary=reply_title or "вашу задачу",
            source_text=_reply_source_text(
                post_text=post.text,
                project_title=project_title,
                project_description=project_description,
                project_page_text=project_page_text,
            ),
            attachment_context=attachment_context,
            estimated_days=judge_result.estimated_days,
            # The first Kwork response should sell the solution, not make the
            # customer answer a discovery question. Keep AI questions in the
            # internal assessment for the follow-up conversation instead.
            blocking_question="",
        )
        draft_reply = reply_composer(
            reply_context,
            judge_result.draft_reply,
            api_key=deepseek_api_key,
            model=deepseek_model,
        )
        summary = f"{_summary_from_judge(judge_result)}{project_summary_suffix}"
        if kwork_facts:
            summary = "\n\n".join([summary, _format_kwork_facts(kwork_facts)])
        if attachment_context:
            summary = "\n\n".join([summary, _shorten_attachment_report(attachment_context)])

        buyer_desired_budget_rub = (
            getattr(project_info, "buyer_desired_budget_rub", None) if project_info is not None else None
        )
        kwork_max_price_rub = (
            getattr(project_info, "kwork_max_price_rub", None) if project_info is not None else None
        )
        proposal_price_rub = _proposal_price_from_kwork_max(kwork_max_price_rub) or judge_result.price_rub or None

        lead_id = storage.create_lead(
            post_id=post_id,
            score=judge_result.score,
            summary=summary,
            draft_reply=draft_reply,
            contact=evaluation.contact,
            proposal_title=_proposal_title_from_text(post.text),
            proposal_price_rub=proposal_price_rub,
            proposal_days=judge_result.estimated_days or None,
            buyer_desired_budget_rub=buyer_desired_budget_rub,
            kwork_max_price_rub=kwork_max_price_rub,
        )
        if project_info is not None:
            storage.update_lead_live_status(
                lead_id,
                response_count=getattr(project_info, "response_count", None),
                reason=str(getattr(project_info, "reason", "") or ""),
            )
        if attachment_reports:
            storage.replace_lead_attachments(lead_id, attachment_reports)
        lead = storage.get_lead(lead_id)
        if lead.status != "new":
            continue
        if _deliver_new_lead(storage, lead_hub, email_client, lead):
            created += 1
    return created


def _proposal_price_from_kwork_max(maximum_rub: int | None) -> int | None:
    """Price a proposal 15% below Kwork's current permitted ceiling."""
    if maximum_rub is None or maximum_rub <= 0:
        return None
    discounted = maximum_rub * 0.85
    return int((discounted + 50) // 100) * 100


def _refresh_existing_lead_live_status(
    storage: Storage,
    lead,
    kwork_project_client: ProjectInspector | None,
    kwork_max_responses: int,
) -> None:
    """Refresh competition data for an actionable lead without recreating it."""
    if kwork_project_client is None or lead.status == "sent" or lead.sent_at:
        return
    if lead.live_response_count is not None and lead.live_response_count > kwork_max_responses:
        return

    try:
        project_info = kwork_project_client.inspect(lead.contact)
    except Exception:
        logger.warning("Unable to refresh Kwork status for lead #%s", lead.id, exc_info=True)
        return

    storage.update_lead_live_status(
        lead.id,
        response_count=getattr(project_info, "response_count", None),
        reason=str(getattr(project_info, "reason", "") or ""),
    )


def _build_attachment_processing_result(builder, attachments: tuple[str, ...], **kwargs) -> AttachmentProcessingResult:
    try:
        result = builder(attachments, **kwargs)
    except TypeError as exc:
        optional_keys = {
            "output_dir",
            "lead_context",
            "deepseek_api_key",
            "deepseek_model",
            "openrouter_api_key",
            "openrouter_base_url",
            "openrouter_vision_model",
            "openrouter_vision_mode",
        }
        if not any(key in str(exc) for key in optional_keys):
            raise
        fallback_kwargs = {key: value for key, value in kwargs.items() if key not in optional_keys}
        result = builder(attachments, **fallback_kwargs)
    if isinstance(result, AttachmentProcessingResult):
        return result
    return AttachmentProcessingResult(context=str(result or ""), reports=())


def _reply_source_text(
    post_text: str,
    project_title: str = "",
    project_description: str = "",
    project_page_text: str = "",
) -> str:
    """Keep task facts for the reply writer separate from Kwork commercial metadata."""
    return "\n\n".join(
        part
        for part in (
            post_text,
            f"Название Kwork: {project_title}" if project_title else "",
            f"Описание Kwork: {project_description}" if project_description else "",
            f"Текст страницы Kwork: {project_page_text}" if project_page_text else "",
        )
        if part
    )


def _publish_lead(storage: Storage, lead_hub: LeadHubClient, lead) -> bool:
    if not storage.claim_lead_hub_delivery(lead.id):
        logger.info("Skipping already synced lead %s", lead.id)
        return False
    try:
        hub_lead_id = lead_hub.publish_lead(lead, storage.list_lead_attachments(lead.id))
    except Exception as exc:
        storage.release_lead_hub_delivery(lead.id)
        logger.warning("Failed to publish lead %s to mobile hub: %s", lead.id, exc)
        return False
    storage.mark_lead_hub_synced(lead.id, hub_lead_id)
    logger.info("Published lead %s to mobile hub as %s", lead.id, hub_lead_id)
    return True


def process_mobile_approvals(
    storage: Storage,
    lead_hub,
    sender: KworkReplySender,
    executor_id: str,
) -> int:
    """Execute mobile-approved Kwork replies exactly once on the desktop session."""
    processed = 0
    for command in lead_hub.fetch_approved_commands():
        hub_lead_id = _command_int(command, "id")
        if hub_lead_id is None:
            logger.warning("Skipping mobile lead command without a valid id")
            continue
        local_lead = storage.get_lead_for_hub_id(hub_lead_id)
        if local_lead is None:
            logger.warning("Mobile lead %s has no paired local Kwork lead", hub_lead_id)
            continue
        claimed = lead_hub.claim_command(hub_lead_id, executor_id)
        if claimed is None:
            continue

        try:
            payload = _mobile_command_payload(claimed)
            storage.update_lead_proposal(
                local_lead.id,
                payload["reply"],
                payload["title"],
                payload["price"],
                payload["days"],
            )
            if not storage.begin_lead_send(local_lead.id):
                raise RuntimeError("Локальный лид уже отправлен или занят другой отправкой")
            message_id = sender.send_reply(
                local_lead.contact,
                payload["reply"],
                price_rub=payload["price"],
                days=payload["days"],
                title=payload["title"],
                submit=True,
            )
            storage.mark_sent(local_lead.id, local_lead.contact, message_id)
            lead_hub.report_result(hub_lead_id, executor_id, sent=True)
            logger.info("Sent mobile-approved lead %s as local lead %s", hub_lead_id, local_lead.id)
            processed += 1
        except Exception as exc:
            storage.mark_failed(local_lead.id, str(exc))
            try:
                lead_hub.report_result(hub_lead_id, executor_id, sent=False, error=str(exc))
            except Exception:
                logger.exception("Unable to report mobile lead %s failure", hub_lead_id)
            logger.exception("Failed to send mobile-approved lead %s", hub_lead_id)
    return processed


def _mobile_command_payload(command: dict[str, object]) -> dict[str, str | int]:
    reply = str(command.get("draft_reply") or "").strip()
    title = str(command.get("proposal_title") or command.get("title") or "").strip()[:70]
    price = _command_int(command, "proposal_price_rub")
    days = _command_int(command, "proposal_days")
    if not reply:
        raise ValueError("В мобильной карточке не заполнен текст отклика")
    if not title:
        raise ValueError("В мобильной карточке не заполнено название заказа")
    if price is None or days is None:
        raise ValueError("В мобильной карточке нужно указать цену и срок")
    return {"reply": reply, "title": title, "price": price, "days": days}


def _command_int(command: dict[str, object], field: str) -> int | None:
    value = command.get(field)
    try:
        number = int(value) if value is not None else None
    except (TypeError, ValueError):
        return None
    return number if number is not None and number > 0 else None


def _deliver_new_lead(storage: Storage, lead_hub: LeadHubClient | None, email_client, lead) -> bool:
    if lead_hub is not None:
        return _publish_lead(storage, lead_hub, lead)
    if email_client is None:
        raise RuntimeError("Mobile lead hub is not configured")
    return _legacy_email_delivery(storage, email_client, lead)


def _legacy_email_delivery(storage: Storage, email_client, lead) -> bool:
    """Test-only compatibility for pre-mobile saved workflows."""
    if not storage.claim_lead_email_delivery(lead.id):
        return False
    try:
        message_id = email_client.send_lead(lead)
    except Exception:
        storage.release_lead_email_delivery(lead.id)
        return False
    storage.mark_lead_emailed(lead.id, message_id)
    return True


def _summary_from_judge(result: LeadJudgeResult) -> str:
    lines = [
        f"AI: {result.decision}, сложность: {result.complexity}",
        f"Срок: {result.estimated_days} дн.",
        f"Цена: {result.price_rub} руб." if result.price_rub else "Цена: не определена",
        f"Задача: {result.summary}",
    ]
    if result.customer_goal:
        lines.append("Боль клиента: " + result.customer_goal)
    if result.work_plan:
        lines.append("План работ: " + "; ".join(result.work_plan))
    if result.reasons:
        lines.append("Почему подходит: " + "; ".join(result.reasons))
    if result.risks:
        lines.append("Риски: " + "; ".join(result.risks))
    if result.questions:
        lines.append("Уточнение: " + "; ".join(result.questions))
    return "\n".join(lines)


def _shorten_attachment_report(report: str, limit: int = 1800) -> str:
    report = report.strip()
    if len(report) <= limit:
        return report
    return report[: limit - 1].rstrip() + "…"


def _format_kwork_facts(facts: tuple[str, ...], limit: int = 1200) -> str:
    report = "KWORK-ДАННЫЕ:\n" + "\n".join(f"- {fact}" for fact in facts)
    if len(report) <= limit:
        return report
    return report[: limit - 1].rstrip() + "…"


def _proposal_title_from_text(post_text: str, summary: str = "") -> str:
    meta_prefixes = ("осталось:", "предложений:", "бюджет:", "контакт:", "kwork facts:")
    for line in post_text.splitlines():
        clean = line.strip()
        if not clean:
            continue
        if clean.startswith("\U0001f4cc"):
            return _strip_kwork_inline_metadata(clean.lstrip("\U0001f4cc").strip())[:70]
        if clean.lower().startswith(meta_prefixes):
            continue
        return _strip_kwork_inline_metadata(clean)[:70]
    for line in summary.splitlines():
        clean = line.strip()
        if clean.startswith("Задача:"):
            return _strip_kwork_inline_metadata(clean.removeprefix("Задача:").strip())[:70]
    return ""


def _strip_kwork_inline_metadata(value: str) -> str:
    clean = re.split(
        r"(?:[.,;]?\s+)(?:предложений|отклик|осталось|бюджет|контакт)\s*:",
        value,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]
    return clean.rstrip(" .,:;-")


def print_orders(storage: Storage, status: str | None = None) -> None:
    for order in storage.list_orders(status=status):
        print(f"#{order.id} [{order.status}] {order.title} - {order.contact}")


def process_approvals(storage: Storage, telegram_client: PostSource, email_client, max_sends: int = 5) -> int:
    """Compatibility helper retained for old local databases; not exposed by the product."""
    del telegram_client, max_sends
    processed = 0
    for lead_id, message_id in email_client.fetch_approvals(storage.seen_approval_message_ids()):
        if storage.record_approval(lead_id, message_id):
            processed += 1
    return processed


def submit_order(storage: Storage, email_client, order_id: int, deliverable: str) -> str:
    storage.submit_order_for_approval(order_id, deliverable)
    return email_client.send_order_for_approval(storage.get_order(order_id))


def process_order_reviews(storage: Storage, email_client) -> int:
    processed = 0
    for review in email_client.fetch_order_reviews(storage.seen_order_review_message_ids()):
        if review.decision == "approved":
            changed = storage.approve_order(review.order_id, review.message_id)
        elif review.decision == "revision":
            changed = storage.request_order_revision(review.order_id, review.message_id, review.notes)
        else:
            changed = False
        processed += int(changed)
    return processed


def create_order_handoff(storage: Storage, order_id: int, output_dir: str | Path) -> Path:
    order = storage.get_order(order_id)
    return write_codex_handoff(order, output_dir)


def build_runtime(config: AppConfig):
    storage = Storage(config.database_path)
    storage.initialize()
    kwork_cookie = _resolve_kwork_cookie(config)
    kwork_project_client = KworkProjectClient(
        cookie=kwork_cookie,
        use_browser=config.kwork_use_browser,
        cdp_url=config.kwork_cdp_url,
        browser_profile_dir=config.kwork_browser_profile_dir,
        login_email=config.kwork_login_email,
        login_password=config.kwork_login_password,
    )
    if config.kwork_source == "web":
        logger.warning("Using Kwork web source with GUI-only replies")
        telegram_client = KworkWebSource(
            projects_url=config.kwork_projects_url,
            max_posts=config.max_posts_per_channel,
            max_responses=config.kwork_max_responses,
            max_age_hours=config.kwork_max_age_hours,
            cookie=kwork_cookie,
            use_browser=config.kwork_use_browser,
            cdp_url=config.kwork_cdp_url,
            browser_profile_dir=config.kwork_browser_profile_dir,
            enable_replies=False,
            login_email=config.kwork_login_email,
            login_password=config.kwork_login_password,
        )
    elif config.telegram_api_id > 0 and config.telegram_api_hash != "fill_later":
        telegram_client = TelegramLeadClient(
            api_id=config.telegram_api_id,
            api_hash=config.telegram_api_hash,
            session_name=config.telegram_session_name,
            channels=config.telegram_channels,
            max_posts_per_channel=config.max_posts_per_channel,
        )
    else:
        logger.warning("Telegram API is not configured; using public read-only fallback")
        telegram_client = PublicTelegramClient(
            channels=config.telegram_channels,
            max_posts_per_channel=config.max_posts_per_channel,
        )
    lead_hub = LeadHubClient(
        base_url=config.lead_hub_url,
        api_key=config.lead_hub_api_key,
        owner_phone=config.lead_hub_owner_phone,
    )
    return storage, telegram_client, lead_hub, kwork_project_client


def _resolve_kwork_cookie(config: AppConfig) -> str:
    if config.kwork_cookie.strip():
        return config.kwork_cookie.strip()
    if not config.kwork_auto_chrome_cookies:
        return ""
    cookie = chrome_cookie_header(".kwork.ru")
    if cookie:
        logger.info("Imported Kwork cookies from the current Chrome profile")
    elif config.kwork_use_browser:
        logger.info("Kwork HTTP cookies were not imported; logged-in Chrome session will be used for private pages and files")
    else:
        logger.warning("Kwork Chrome cookies were not imported; private files may require manual login")
    return cookie


def _process_mobile_approvals_from_runtime(
    storage: Storage,
    lead_hub: LeadHubClient,
    config: AppConfig,
    cookie: str,
) -> int:
    sender = KworkReplySender(
        cdp_url=config.kwork_cdp_url,
        browser_profile_dir=config.kwork_browser_profile_dir,
        login_email=config.kwork_login_email,
        login_password=config.kwork_login_password,
        max_responses=config.kwork_max_responses,
        cookie=cookie,
    )
    try:
        return process_mobile_approvals(
            storage=storage,
            lead_hub=lead_hub,
            sender=sender,
            executor_id=config.lead_hub_executor_id,
        )
    except Exception:
        logger.exception("Unable to fetch mobile-approved Kwork replies")
        return 0


def _scan_runtime_once(
    storage: Storage,
    telegram_client: PostSource,
    lead_hub: LeadHubClient,
    kwork_project_client: ProjectInspector,
    config: AppConfig,
) -> None:
    """Run one Kwork pass and then execute any mobile-approved replies."""
    cookie = _resolve_kwork_cookie(config)
    scan_once(
        storage, telegram_client, lead_hub,
        deepseek_api_key=config.deepseek_api_key,
        deepseek_model=config.deepseek_model,
        openrouter_api_key=config.openrouter_api_key,
        openrouter_base_url=config.openrouter_base_url,
        openrouter_vision_model=config.openrouter_vision_model,
        openrouter_vision_mode=config.openrouter_vision_mode,
        kwork_project_client=kwork_project_client,
        kwork_max_responses=config.kwork_max_responses,
        kwork_cookie=cookie,
        kwork_use_browser=config.kwork_use_browser,
        kwork_cdp_url=config.kwork_cdp_url,
        kwork_browser_profile_dir=config.kwork_browser_profile_dir,
        lead_min_score=config.lead_min_score,
        lead_max_days=config.lead_max_days,
        lead_accept_decisions=config.lead_accept_decisions,
        lead_blocked_keywords=config.lead_blocked_keywords,
        lead_hard_reject_keywords=config.lead_hard_reject_keywords,
        lead_required_keywords=config.lead_required_keywords,
    )
    _process_mobile_approvals_from_runtime(storage, lead_hub, config, cookie)


def run_mobile_control_loop(
    storage: Storage,
    telegram_client: PostSource,
    lead_hub: LeadHubClient,
    kwork_project_client: ProjectInspector,
    config: AppConfig,
) -> None:
    """Keep the local Kwork session responsive to commands from the mobile app."""
    next_scheduled_scan = 0.0
    poll_seconds = min(15, max(3, config.scan_interval_seconds // 12))
    while True:
        try:
            monitor = lead_hub.fetch_monitor_control()
            lead_hub.report_monitor_heartbeat(config.lead_hub_executor_id)
            _process_mobile_approvals_from_runtime(
                storage,
                lead_hub,
                config,
                _resolve_kwork_cookie(config),
            )
            requested = bool(monitor.get("scan_requested"))
            scheduled = (
                monitor.get("desired_state") == "running"
                and time.monotonic() >= next_scheduled_scan
            )
            if requested or scheduled:
                lead_hub.report_monitor_heartbeat(
                    config.lead_hub_executor_id,
                    scan_event="started",
                )
                try:
                    _scan_runtime_once(
                        storage,
                        telegram_client,
                        lead_hub,
                        kwork_project_client,
                        config,
                    )
                except Exception as exc:
                    logger.exception("Mobile-requested Kwork scan failed")
                    lead_hub.report_monitor_heartbeat(
                        config.lead_hub_executor_id,
                        scan_event="finished",
                        error=str(exc),
                    )
                else:
                    lead_hub.report_monitor_heartbeat(
                        config.lead_hub_executor_id,
                        scan_event="finished",
                    )
                next_scheduled_scan = time.monotonic() + config.scan_interval_seconds
        except Exception:
            logger.exception("Mobile Kwork control poll failed")
        time.sleep(poll_seconds)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Telegram lead funnel")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("scan")
    subparsers.add_parser("watch")
    subparsers.add_parser("mobile-control")
    args = parser.parse_args()

    config = load_config()
    storage, telegram_client, lead_hub, kwork_project_client = build_runtime(config)

    if args.command == "scan":
        _scan_runtime_once(storage, telegram_client, lead_hub, kwork_project_client, config)
        return 0
    if args.command == "mobile-control":
        run_mobile_control_loop(storage, telegram_client, lead_hub, kwork_project_client, config)
        return 0
    while True:
        _scan_runtime_once(storage, telegram_client, lead_hub, kwork_project_client, config)
        time.sleep(config.scan_interval_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
