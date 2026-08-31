from __future__ import annotations

import argparse
import logging
import os
import re
import time
from contextlib import contextmanager
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Callable, Protocol

from app.ai_lead_judge import (
    DEFAULT_ACCEPT_DECISIONS,
    DEFAULT_BLOCKED_KEYWORDS,
    DEFAULT_HARD_REJECT_KEYWORDS,
    LeadAnalysisUnavailable,
    LeadJudgeResult,
    judge_lead,
)
from app.attachments import AttachmentProcessingResult, build_attachment_report
from app.chrome_cookies import chrome_cookie_header
from app.config import AppConfig, load_config
from app.handoff import write_codex_handoff
from app.kwork_client import KworkProjectClient
from app.kwork_sender import KWORK_MIN_PRICE_RUB, KworkReplySender
from app.kwork_source import KworkWebSource
from app.lead_filter import evaluate_post
from app.lead_api_client import LeadHubClient
from app.public_telegram_client import PublicTelegramClient
from app.reply_composer import (
    ReplyDraftContext,
    ReplyGenerationUnavailable,
    compose_customer_reply,
    is_generic_fallback_reply,
    reply_delivery_issue_summary,
)
from app.storage import Storage
from app.telegram_client import TelegramLeadClient

logger = logging.getLogger(__name__)
REPLY_GENERATION_ERROR_PREFIX = "AI-отклик не готов: "


@contextmanager
def _scan_execution_lock(lock_path: Path):
    """Prevent desktop and mobile entry points from scanning at the same time."""
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    handle = lock_path.open("a+b")
    acquired = False
    try:
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            try:
                handle.write(b"0")
                handle.flush()
            except OSError:
                yield False
                return
        handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:  # pragma: no cover - Windows is the supported production runtime
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            yield False
            return
        acquired = True
        yield True
    finally:
        if acquired:
            handle.seek(0)
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:  # pragma: no cover - Windows is the supported production runtime
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()


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
    openrouter_analysis_model: str = "openai/gpt-5.1",
    openrouter_reply_model: str = "anthropic/claude-sonnet-4.5",
    openrouter_fallback_models: tuple[str, ...] = (),
    openrouter_vision_model: str = "",
    openrouter_vision_mode: str = "fallback",
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
    lead_hub_executor_id: str = "kwork-desktop",
    new_lead_handler: Callable[[object], None] | None = None,
) -> int:
    # Older extensions called scan_once(storage, source, email_client) positionally.
    # Keep that test seam while production always supplies LeadHubClient here.
    if lead_hub is not None and not hasattr(lead_hub, "publish_lead") and email_client is None:
        email_client = lead_hub
        lead_hub = None
    if openrouter_api_key.strip():
        text_api_key = openrouter_api_key.strip()
        text_base_url = openrouter_base_url
        analysis_model = openrouter_analysis_model
        reply_model = openrouter_reply_model
        fallback_models = openrouter_fallback_models
    else:
        # Keep old installations usable while OpenRouter is being configured.
        text_api_key = deepseek_api_key.strip()
        text_base_url = "https://api.deepseek.com/v1"
        analysis_model = deepseek_model
        reply_model = deepseek_model
        fallback_models = ()
    created = 0
    posts = tuple(telegram_client.fetch_recent_posts())
    if posts and text_api_key.strip():
        _retire_generic_leads_outside_feed(storage, posts)
    for post in posts:
        post_id = storage.save_post(
            channel=post.channel,
            message_id=post.message_id,
            post_url=post.url,
            text=post.text,
            posted_at=post.posted_at,
        )
        existing_lead = storage.get_lead_for_post(post_id)
        if (
            text_api_key.strip()
            and existing_lead is not None
            and existing_lead.status == "approved"
            and is_generic_fallback_reply(existing_lead.draft_reply)
        ):
            reason = "Лид снят: одобренный общий шаблон запрещен к отправке и требует новой оценки."
            storage.mark_rejected(existing_lead.id, reason)
            logger.warning("Rejected approved generic draft for lead %s", existing_lead.id)
            continue
        retry_failed_reply = bool(
            existing_lead is not None
            and existing_lead.status == "failed"
            and existing_lead.last_error.startswith(REPLY_GENERATION_ERROR_PREFIX)
        )
        rebuild_existing = bool(
            text_api_key.strip()
            and
            existing_lead is not None
            and existing_lead.status not in {"approved", "sending", "sent", "rejected"}
            and (is_generic_fallback_reply(existing_lead.draft_reply) or retry_failed_reply)
        )
        if existing_lead is not None and not rebuild_existing:
            _refresh_existing_lead_live_status(
                storage=storage,
                lead=existing_lead,
                kwork_project_client=kwork_project_client,
                kwork_max_responses=kwork_max_responses,
            )
            if _deliver_new_lead(
                storage,
                lead_hub,
                email_client,
                existing_lead,
                executor_id=lead_hub_executor_id,
            ):
                created += 1
            else:
                logger.info("Skipping existing lead for post %s/%s", post.channel, post.message_id)
            continue
        if rebuild_existing:
            logger.warning(
                "Rebuilding retired generic draft for lead %s (%s/%s)",
                existing_lead.id,
                post.channel,
                post.message_id,
            )
        rejection_reason = storage.get_post_rejection(post_id)
        if rejection_reason:
            if rebuild_existing and existing_lead is not None:
                storage.mark_rejected(existing_lead.id, rejection_reason)
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
            reason = evaluation.reasons
            logger.info("Rejected post %s/%s: %s", post.channel, post.message_id, evaluation.reasons)
            storage.record_post_rejection(post_id, reason)
            if rebuild_existing and existing_lead is not None:
                storage.mark_rejected(existing_lead.id, reason)
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
            if rebuild_existing and existing_lead is not None:
                storage.update_lead_live_status(
                    existing_lead.id,
                    response_count=getattr(project_info, "response_count", None),
                    reason=str(getattr(project_info, "reason", "") or ""),
                )
            if project_info.is_unavailable:
                reason = project_info.reason or "Kwork заказ недоступен"
                logger.info(
                    "Rejected post %s/%s: %s",
                    post.channel,
                    post.message_id,
                    project_info.reason,
                )
                storage.record_post_rejection(post_id, reason)
                if rebuild_existing and existing_lead is not None:
                    storage.mark_rejected(existing_lead.id, reason)
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
                reason = (
                    f"Kwork откликов {project_info.response_count} больше лимита {kwork_max_responses}"
                )
                logger.info(
                    "Rejected post %s/%s: Kwork responses %s > %s",
                    post.channel,
                    post.message_id,
                    project_info.response_count,
                    kwork_max_responses,
                )
                storage.record_post_rejection(
                    post_id,
                    reason,
                )
                if rebuild_existing and existing_lead is not None:
                    storage.mark_rejected(existing_lead.id, reason)
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
                    openrouter_analysis_model=openrouter_analysis_model,
                    openrouter_fallback_models=openrouter_fallback_models,
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

        try:
            judge_result = lead_judge(
                project_text,
                api_key=text_api_key,
                model=analysis_model,
                base_url=text_base_url,
                fallback_models=fallback_models,
                min_score=lead_min_score,
                max_estimated_days=lead_max_days,
                accept_decisions=lead_accept_decisions,
                blocked_keywords=lead_blocked_keywords,
                hard_reject_keywords=lead_hard_reject_keywords,
            )
        except LeadAnalysisUnavailable as exc:
            logger.error(
                "Deferred post %s/%s until cloud analysis recovers: %s",
                post.channel,
                post.message_id,
                exc,
            )
            continue
        if not judge_result.accepted:
            reason = "; ".join(judge_result.reasons)
            logger.info(
                "Rejected post %s/%s by AI judge: %s",
                post.channel,
                post.message_id,
                reason,
            )
            storage.record_post_rejection(post_id, reason)
            if rebuild_existing and existing_lead is not None:
                storage.mark_rejected(existing_lead.id, reason)
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
            blocking_question=judge_result.blocking_question,
            customer_goal=judge_result.customer_goal,
            work_plan=tuple(judge_result.work_plan),
            risks=tuple(judge_result.risks),
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
        budget_ceiling_rub = kwork_max_price_rub or buyer_desired_budget_rub
        proposal_price_rub = _proposal_price_from_kwork_max(budget_ceiling_rub) or judge_result.price_rub or None

        try:
            draft_reply = reply_composer(
                reply_context,
                judge_result.draft_reply,
                api_key=text_api_key,
                model=reply_model,
                base_url=text_base_url,
                fallback_models=fallback_models,
            )
        except ReplyGenerationUnavailable as exc:
            error = REPLY_GENERATION_ERROR_PREFIX + str(exc)
            logger.error(
                "Saved post %s/%s for retry after cloud reply generation failed: %s",
                post.channel,
                post.message_id,
                exc,
            )
            if rebuild_existing and existing_lead is not None:
                lead_id = existing_lead.id
                storage.update_lead_assessment(
                    lead_id,
                    score=judge_result.score,
                    summary=summary,
                    price_rub=proposal_price_rub,
                    days=judge_result.estimated_days or None,
                )
                storage.update_lead_kwork_pricing(
                    lead_id,
                    buyer_desired_budget_rub=buyer_desired_budget_rub,
                    kwork_max_price_rub=kwork_max_price_rub,
                    proposal_price_rub=proposal_price_rub,
                )
            else:
                lead_id = storage.create_lead(
                    post_id=post_id,
                    score=judge_result.score,
                    summary=summary,
                    draft_reply="",
                    contact=evaluation.contact,
                    proposal_title=_proposal_title_from_text(post.text),
                    proposal_price_rub=proposal_price_rub,
                    proposal_days=judge_result.estimated_days or None,
                    buyer_desired_budget_rub=buyer_desired_budget_rub,
                    kwork_max_price_rub=kwork_max_price_rub,
                )
            storage.mark_failed(lead_id, error)
            if project_info is not None:
                storage.update_lead_live_status(
                    lead_id,
                    response_count=getattr(project_info, "response_count", None),
                    reason=str(getattr(project_info, "reason", "") or ""),
                )
            if attachment_reports:
                storage.replace_lead_attachments(lead_id, attachment_reports)
            failed_lead = storage.get_lead(lead_id)
            if rebuild_existing and lead_hub is not None:
                storage.prepare_lead_hub_resync(lead_id)
            if _deliver_new_lead(
                storage,
                lead_hub,
                email_client,
                failed_lead,
                executor_id=lead_hub_executor_id,
            ):
                created += 1
            continue

        if rebuild_existing and existing_lead is not None:
            lead_id = existing_lead.id
            storage.update_lead_assessment(
                lead_id,
                score=judge_result.score,
                summary=summary,
                price_rub=proposal_price_rub,
                days=judge_result.estimated_days or None,
            )
            storage.update_lead_proposal(
                lead_id,
                draft_reply=draft_reply,
                title=_proposal_title_from_text(post.text),
                price_rub=proposal_price_rub,
                days=judge_result.estimated_days or None,
            )
            storage.mark_ready(lead_id)
        else:
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
        if new_lead_handler is not None:
            try:
                new_lead_handler(lead)
            except Exception:
                logger.exception("Immediate lead handler failed for lead %s", lead.id)
            lead = storage.get_lead(lead_id)
        if rebuild_existing and lead_hub is not None:
            storage.prepare_lead_hub_resync(lead.id)
            if _publish_lead(
                storage,
                lead_hub,
                storage.get_lead(lead.id),
                executor_id=lead_hub_executor_id,
            ):
                created += 1
            continue
        if _deliver_new_lead(
            storage,
            lead_hub,
            email_client,
            lead,
            executor_id=lead_hub_executor_id,
        ):
            created += 1
    return created


def _retire_generic_leads_outside_feed(storage: Storage, posts: tuple[object, ...]) -> None:
    """Remove stale boilerplate from every unsent local queue, not only the latest page."""
    current_posts = {
        (str(getattr(post, "channel", "")), int(getattr(post, "message_id", 0)))
        for post in posts
    }
    reason = "Лид снят: устаревший общий шаблон не прошел обязательную AI-пересборку."
    for lead in storage.list_leads():
        if lead.status in {"sent", "sending", "rejected"}:
            continue
        if (lead.channel, lead.message_id) in current_posts:
            continue
        if is_generic_fallback_reply(lead.draft_reply):
            storage.mark_rejected(lead.id, reason)
            logger.warning("Retired stale generic draft for lead %s outside current feed", lead.id)


def _proposal_price_from_kwork_max(maximum_rub: int | None) -> int | None:
    """Price a proposal 15% below Kwork's current permitted ceiling."""
    if maximum_rub is None or maximum_rub <= 0:
        return None
    discounted = maximum_rub * 0.85
    rounded = int((discounted + 50) // 100) * 100
    return max(KWORK_MIN_PRICE_RUB, rounded)


def _refresh_existing_lead_live_status(
    storage: Storage,
    lead,
    kwork_project_client: ProjectInspector | None,
    kwork_max_responses: int,
) -> None:
    """Refresh competition data for an actionable lead without recreating it."""
    if kwork_project_client is None or lead.status in {"sent", "rejected"} or lead.sent_at:
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
    desired_budget = getattr(project_info, "buyer_desired_budget_rub", None)
    maximum_budget = getattr(project_info, "kwork_max_price_rub", None)
    if desired_budget is not None or maximum_budget is not None:
        storage.update_lead_kwork_pricing(
            lead.id,
            buyer_desired_budget_rub=desired_budget,
            kwork_max_price_rub=maximum_budget,
            proposal_price_rub=_proposal_price_from_kwork_max(maximum_budget or desired_budget),
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
            "openrouter_analysis_model",
            "openrouter_fallback_models",
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


def _publish_lead(
    storage: Storage,
    lead_hub: LeadHubClient,
    lead,
    *,
    executor_id: str = "kwork-desktop",
) -> bool:
    if not storage.claim_lead_hub_delivery(lead.id):
        logger.info("Skipping already synced lead %s", lead.id)
        return False
    try:
        hub_lead_id = lead_hub.publish_lead(lead, storage.list_lead_attachments(lead.id))
    except Exception as exc:
        storage.release_lead_hub_delivery(lead.id)
        logger.warning("Failed to publish lead %s to mobile hub: %s", lead.id, exc)
        return False
    if lead.status == "sent":
        try:
            lead_hub.report_auto_sent(hub_lead_id, executor_id)
        except Exception as exc:
            storage.release_lead_hub_delivery(lead.id)
            logger.warning("Failed to sync auto-sent lead %s to mobile hub: %s", lead.id, exc)
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

        if storage.was_lead_sent(local_lead.id):
            try:
                lead_hub.report_result(hub_lead_id, executor_id, sent=True)
            except Exception:
                logger.exception("Unable to reconcile already-sent mobile lead %s", hub_lead_id)
            continue
        if local_lead.status == "sending":
            uncertainty = (
                "Отправка уже начиналась, но итог не подтвержден локально. "
                "Проверь заказ на Kwork перед любыми повторными действиями."
            )
            try:
                lead_hub.report_result(
                    hub_lead_id,
                    executor_id,
                    sent=False,
                    error=uncertainty,
                )
            except Exception:
                logger.exception("Unable to report uncertain mobile lead %s", hub_lead_id)
            logger.error("Blocked uncertain repeated send for mobile lead %s", hub_lead_id)
            continue

        try:
            payload = _mobile_command_payload(claimed)
            quality_context = _mobile_reply_context(
                storage,
                local_lead,
                title=str(payload["title"]),
                days=int(payload["days"]),
            )
            quality_block = reply_delivery_issue_summary(str(payload["reply"]), quality_context)
            if quality_block:
                raise ValueError(quality_block)
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
            try:
                storage.mark_sent(local_lead.id, local_lead.contact, message_id)
            except Exception:
                logger.exception(
                    "Kwork accepted mobile lead %s, but local sent status was not persisted",
                    hub_lead_id,
                )
            try:
                lead_hub.report_result(hub_lead_id, executor_id, sent=True)
            except Exception:
                logger.exception(
                    "Kwork accepted mobile lead %s, but hub result reporting failed",
                    hub_lead_id,
                )
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


def _auto_send_new_leads(
    storage: Storage,
    previous_statuses: dict[int, str],
    sender: KworkReplySender,
    *,
    daily_limit: int,
) -> int:
    """Send only Kwork leads first created or rebuilt by the current scan."""
    remaining = max(0, daily_limit - storage.count_sent_today_moscow())
    if remaining <= 0:
        logger.info("Kwork auto-send daily limit %s is already reached", daily_limit)
        return 0

    sent = 0
    for lead in storage.list_leads():
        if sent >= remaining:
            break
        if lead.channel != "kwork-web" or lead.status != "new":
            continue
        previous_status = previous_statuses.get(lead.id)
        if previous_status not in {None, "failed"}:
            continue
        sent += int(_auto_send_lead(storage, lead, sender))
    return sent


def _auto_send_lead(storage: Storage, lead, sender: KworkReplySender) -> bool:
    """Validate, reserve and submit one lead without waiting for the scan to finish."""
    block_reason = _auto_send_block_reason(storage, lead)
    if block_reason:
        storage.mark_failed(lead.id, block_reason)
        logger.warning("Auto-send blocked lead %s: %s", lead.id, block_reason)
        return False
    if not storage.begin_lead_send(lead.id):
        logger.warning("Auto-send could not reserve lead %s", lead.id)
        return False

    try:
        message_id = sender.send_reply(
            lead.contact,
            lead.draft_reply,
            price_rub=lead.proposal_price_rub,
            days=lead.proposal_days,
            title=lead.proposal_title,
            submit=True,
        )
    except Exception as exc:
        storage.mark_failed(lead.id, str(exc))
        logger.exception("Auto-send failed for Kwork lead %s", lead.id)
        return False

    try:
        storage.mark_sent(lead.id, lead.contact, message_id)
    except Exception:
        # The browser may already have submitted the proposal. Keep the
        # reserved sending state so a later pass cannot duplicate it.
        logger.exception("Kwork accepted auto-send lead %s, but persistence failed", lead.id)
        return False
    logger.info("Auto-sent Kwork lead %s (%s)", lead.id, lead.contact)
    return True


def _auto_send_block_reason(storage: Storage, lead) -> str:
    if not lead.draft_reply.strip():
        return "Автоотправка: текст отклика не сформирован"
    if not lead.proposal_title.strip():
        return "Автоотправка: название заказа не сформировано"
    if not lead.proposal_price_rub or not lead.proposal_days:
        return "Автоотправка: цена или срок не определены"
    if lead.live_response_count is None:
        return "Автоотправка: не удалось подтвердить число предложений на Kwork"

    attachment_issue = _auto_send_attachment_issue(storage, lead.id)
    if attachment_issue:
        return attachment_issue
    quality_context = _mobile_reply_context(
        storage,
        lead,
        title=lead.proposal_title,
        days=lead.proposal_days,
    )
    quality_issue = reply_delivery_issue_summary(lead.draft_reply, quality_context)
    return f"Автоотправка: {quality_issue}" if quality_issue else ""


def _auto_send_attachment_issue(storage: Storage, lead_id: int) -> str:
    unsafe_markers = (
        "не скачан",
        "не прочитан",
        "не открыт",
        "не выполнен",
        "текст не извлечен",
        "тип не поддержан",
    )
    for attachment in storage.list_lead_attachments(lead_id):
        status = attachment.status.strip().lower()
        if any(marker in status for marker in unsafe_markers):
            return f"Автоотправка: вложение «{attachment.label}» обработано не полностью ({attachment.status})"
    return ""


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
    if price < KWORK_MIN_PRICE_RUB:
        raise ValueError(f"Цена отклика должна быть не меньше {KWORK_MIN_PRICE_RUB} руб.")
    return {"reply": reply, "title": title, "price": price, "days": days}


def _command_int(command: dict[str, object], field: str) -> int | None:
    value = command.get(field)
    try:
        number = int(value) if value is not None else None
    except (TypeError, ValueError):
        return None
    return number if number is not None and number > 0 else None


def _mobile_reply_context(
    storage: Storage,
    lead,
    *,
    title: str,
    days: int,
) -> ReplyDraftContext:
    attachments = storage.list_lead_attachments(lead.id)
    attachment_context = "\n".join(
        f"{attachment.label}: {(attachment.summary or attachment.status).strip()}"
        for attachment in attachments
        if attachment.label.strip() and (attachment.summary or attachment.status).strip()
    )
    return ReplyDraftContext(
        title=title,
        task_summary=_lead_summary_value(lead.summary, "Задача") or title,
        source_text=lead.post_text,
        attachment_context=attachment_context,
        estimated_days=max(1, days),
        blocking_question=_lead_summary_value(lead.summary, "Вопрос перед стартом"),
        customer_goal=_lead_summary_value(lead.summary, "Боль клиента"),
        work_plan=_lead_summary_items(lead.summary, "План работ"),
        risks=_lead_summary_items(lead.summary, "Риски"),
    )


def _lead_summary_value(summary: str, label: str) -> str:
    match = re.search(rf"^{re.escape(label)}:\s*(.+)$", summary, re.IGNORECASE | re.MULTILINE)
    return " ".join(match.group(1).split()).strip() if match else ""


def _lead_summary_items(summary: str, label: str) -> tuple[str, ...]:
    value = _lead_summary_value(summary, label)
    return tuple(item.strip() for item in value.split(";") if item.strip())[:5]


def _deliver_new_lead(
    storage: Storage,
    lead_hub: LeadHubClient | None,
    email_client,
    lead,
    *,
    executor_id: str = "kwork-desktop",
) -> bool:
    if lead_hub is not None:
        return _publish_lead(storage, lead_hub, lead, executor_id=executor_id)
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
    if result.blocking_question:
        lines.append("Вопрос перед стартом: " + result.blocking_question)
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
        logger.info("Using Kwork web source with replies through the active Chrome session")
        telegram_client = KworkWebSource(
            projects_url=config.kwork_projects_url,
            max_posts=config.max_posts_per_channel,
            max_pages=config.kwork_max_pages,
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
    with _scan_execution_lock(config.database_path.parent / "scan.lock") as acquired:
        if not acquired:
            logger.warning("Сканирование уже выполняется из другого окна или с мобильного приложения")
            return
        cookie = _resolve_kwork_cookie(config)
        previous_statuses = {lead.id: lead.status for lead in storage.list_leads()}
        auto_sender = None
        auto_send_daily_limit = max(1, getattr(config, "kwork_auto_send_daily_limit", 10))
        if getattr(config, "kwork_auto_send", False):
            auto_sender = KworkReplySender(
                cdp_url=config.kwork_cdp_url,
                browser_profile_dir=config.kwork_browser_profile_dir,
                login_email=config.kwork_login_email,
                login_password=config.kwork_login_password,
                max_responses=config.kwork_max_responses,
                cookie=cookie,
            )

        def send_immediately(lead) -> None:
            if auto_sender is None:
                return
            if storage.count_sent_today_moscow() >= auto_send_daily_limit:
                logger.info("Kwork auto-send daily limit %s is already reached", auto_send_daily_limit)
                return
            _auto_send_lead(storage, lead, auto_sender)

        scan_once(
            storage, telegram_client, lead_hub,
            deepseek_api_key=config.deepseek_api_key,
            deepseek_model=config.deepseek_model,
            openrouter_api_key=config.openrouter_api_key,
            openrouter_base_url=config.openrouter_base_url,
            openrouter_analysis_model=config.openrouter_analysis_model,
            openrouter_reply_model=config.openrouter_reply_model,
            openrouter_fallback_models=config.openrouter_fallback_models,
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
            lead_hub_executor_id=config.lead_hub_executor_id,
            new_lead_handler=send_immediately if auto_sender is not None else None,
        )
        if auto_sender is not None:
            _auto_send_new_leads(
                storage,
                previous_statuses,
                auto_sender,
                daily_limit=auto_send_daily_limit,
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
    approval_cookie = _resolve_kwork_cookie(config)
    while True:
        try:
            monitor = lead_hub.fetch_monitor_control()
            lead_hub.report_monitor_heartbeat(config.lead_hub_executor_id)
            _process_mobile_approvals_from_runtime(
                storage,
                lead_hub,
                config,
                approval_cookie,
            )
            requested = bool(monitor.get("scan_requested"))
            scheduled = (
                (
                    monitor.get("desired_state") == "running"
                    or getattr(config, "kwork_auto_send", False)
                )
                and time.monotonic() >= next_scheduled_scan
            )
            if requested or scheduled:
                scan_started_at = time.monotonic()
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
                next_scheduled_scan = scan_started_at + config.scan_interval_seconds
        except Exception:
            logger.exception("Mobile Kwork control poll failed")
        time.sleep(poll_seconds)


def _configure_runtime_logging(
    database_path: Path,
    *,
    root_logger: logging.Logger | None = None,
    include_console: bool = True,
) -> Path:
    """Persist diagnostics for both visible and hidden runtime entry points."""
    target_logger = root_logger or logging.getLogger()
    target_logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    log_path = database_path.parent / "lead-funnel.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_log_path = str(log_path.resolve())

    if not any(
        getattr(handler, "_lead_funnel_log_path", "") == resolved_log_path
        for handler in target_logger.handlers
    ):
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=2_000_000,
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        file_handler._lead_funnel_log_path = resolved_log_path
        target_logger.addHandler(file_handler)

    if include_console and not any(
        getattr(handler, "_lead_funnel_console", False)
        for handler in target_logger.handlers
    ):
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler._lead_funnel_console = True
        target_logger.addHandler(console_handler)
    return log_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Telegram lead funnel")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("scan")
    subparsers.add_parser("watch")
    subparsers.add_parser("mobile-control")
    args = parser.parse_args()

    _configure_runtime_logging(Path("data/leads.sqlite3"))
    try:
        config = load_config()
    except Exception:
        logger.exception("Unable to load application configuration")
        raise
    _configure_runtime_logging(config.database_path)
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
