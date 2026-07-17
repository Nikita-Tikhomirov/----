"""Compose and validate customer-safe Kwork proposal drafts."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

COMMERCIAL_PATTERN = re.compile(
    r"(?:\b(?:цена|стоим|бюджет|оплат|предоплат|скидк|ставка)\w*|"
    r"\d[\d\s.,]*\s*(?:₽|руб(?:\.|лей)?|р\.?|тыс\.?|к\b))",
    re.IGNORECASE,
)
GENERIC_PHRASE_PATTERN = re.compile(
    r"(?:уточните\s+детали|обсудим\s+(?:детали|всё|все)|давайте\s+обсудим|"
    r"я\s+правильно\s+понимаю|готов\s+помочь|буду\s+рад\s+помочь|"
    r"если\s+(?:нужно|понадобится).{0,80}?(?:скажите|напишите))",
    re.IGNORECASE,
)
CLARIFICATION_REQUEST_PATTERN = re.compile(
    r"\b(?:уточните|напишите|скажите|сообщите|пришлите|предоставьте|"
    r"подскажите|поясните|дайте)\b",
    re.IGNORECASE,
)
IMPLICIT_QUESTION_PATTERN = re.compile(
    r"^(?:какой|какая|какие|сколько|куда|когда|где|кто|что|есть\s+ли|нужн[аоы]\s+ли)\b",
    re.IGNORECASE,
)
CURRENT_STATE_CLAIM_PATTERN = re.compile(
    r"\bна\s+(?:десктоп\w*|desktop|компьютер\w*|мобильн\w*|телефон\w*|ios|android)"
    r"[^.!?]{0,70}?(?:всё\s+)?(?:не\s+)?(?:работает|срабатывает|падает|ломается|исправно)\b",
    re.IGNORECASE,
)
CURRENT_STATE_ENVIRONMENT_GROUPS = (
    ("десктоп", "desktop", "компьютер"),
    ("мобиль", "телефон", "ios", "android"),
)
UNCERTAIN_COMMITMENT_PATTERN = re.compile(
    r"(?:\b(?:пока\s+исхожу|это\s+уточняется|потребуется\s+уточнен\w*|"
    r"предположительно|скорее\s+всего)\b|"
    r"\bесли\s+[^.!?]{0,100}\b(?:действительно\s+)?(?:нужн[аоы]?|понадобится)\b)",
    re.IGNORECASE,
)
CUSTOMER_SKILL_ASSUMPTION_PATTERN = re.compile(
    r"\b(?:если\s+вы\s+(?:(?:не\s+)?(?:работали|знакомы|разбираетесь|использовали|умеете)|новичок)|"
    r"вам\s+(?:будет\s+)?(?:сложно|непонятно)|для\s+новичка)\b",
    re.IGNORECASE,
)
AI_MENTION_PATTERN = re.compile(
    r"(?:\b(?:ai|gpt|chatgpt)\b|нейросет\w*|искусственн\w*\s+интеллект\w*|"
    r"(?:ai|ии)[-\s]?агент\w*)",
    re.IGNORECASE,
)
ACTION_PATTERN = re.compile(
    r"(?:провер|исправ|внес|сверста|настро|реализ|подключ|доработ|адапт|"
    r"протестир|подготов|собер|интегр|оптимизир|разбер)",
    re.IGNORECASE,
)
SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+")
WORD_PATTERN = re.compile(r"[A-Za-zА-Яа-яЁё]{4,}")
FORM_TASK_PATTERN = re.compile(
    r"\b(?:форм(?:а|ы|е|у|ой|ами|ах)?|forms?|заявк\w*)\b",
    re.IGNORECASE,
)
WORDPRESS_TASK_PATTERN = re.compile(r"\b(?:wordpress|вордпресс)\w*\b", re.IGNORECASE)
LAYOUT_TASK_PATTERN = re.compile(
    r"\b(?:верстк\w*|лендинг\w*|адаптив\w*|макет\w*|figma|psd)\b",
    re.IGNORECASE,
)
INTEGRATION_TASK_PATTERN = re.compile(
    r"\b(?:api|crm|интеграц\w*|вебхук\w*|парсер\w*|импорт\w*)\b",
    re.IGNORECASE,
)
PAYMENT_TASK_PATTERN = re.compile(r"\b(?:платеж\w*|оплат\w*|эквайринг\w*)\b", re.IGNORECASE)
DOMAIN_TASK_PATTERN = re.compile(r"\b(?:домен\w*|dns|vercel|хостинг\w*)\b", re.IGNORECASE)
TASK_ACTION_REFERENCE_PATTERNS = (
    FORM_TASK_PATTERN,
    WORDPRESS_TASK_PATTERN,
    INTEGRATION_TASK_PATTERN,
    PAYMENT_TASK_PATTERN,
    DOMAIN_TASK_PATTERN,
)
DELIVERY_BLOCKING_ISSUES = frozenset(
    {
        "empty reply",
        "commercial term",
        "AI mention",
        "generic phrase",
        "unapproved clarification",
        "unsupported current state",
        "unsupported task action",
        "uncertain commitment",
        "customer skill assumption",
        "too many questions",
        "missing concrete action",
        "missing task reference",
    }
)
DELIVERY_ISSUE_LABELS = {
    "commercial term": "упоминает цену или оплату",
    "AI mention": "упоминает AI",
    "generic phrase": "слишком общий",
    "unapproved clarification": "просит неподтвержденное уточнение",
    "unsupported current state": "заявляет непроверенное состояние сайта",
    "unsupported task action": "обещает действие, которого нет в заказе",
    "uncertain commitment": "содержит неуверенное обещание",
    "customer skill assumption": "оценивает навыки заказчика",
    "too many questions": "задает лишние вопросы",
    "missing concrete action": "не описывает конкретное действие",
    "missing task reference": "не ссылается на задачу",
    "empty reply": "пустой",
}
MAX_REPLY_LENGTH = 850
MIN_REPLY_LENGTH = 260
MAX_REPLY_SENTENCES = 6


@dataclass(frozen=True)
class ReplyDraftContext:
    title: str
    task_summary: str
    source_text: str
    attachment_context: str
    estimated_days: int
    blocking_question: str = ""


@dataclass(frozen=True)
class ReplyQualityResult:
    approved: bool
    issues: tuple[str, ...]


def compose_customer_reply(
    context: ReplyDraftContext,
    seed_reply: str,
    api_key: str = "",
    model: str = "deepseek-chat",
    timeout_seconds: float = 45.0,
) -> str:
    """Return a concise proposal that is safe to show in email and send to Kwork."""
    candidate = _remove_commercial_sentences(seed_reply)
    if api_key.strip():
        generated = _compose_with_deepseek(context, api_key, model, timeout_seconds)
        if generated:
            candidate = _remove_commercial_sentences(generated)

    deterministic_issues = reply_quality_issues(candidate, context)
    ai_review: ReplyQualityResult | None = None
    if api_key.strip() and candidate:
        ai_review = _review_with_deepseek(candidate, context, api_key, model, timeout_seconds)

    review_issues = ai_review.issues if ai_review is not None else ()
    if deterministic_issues or (ai_review is not None and not ai_review.approved):
        if api_key.strip():
            repaired = _repair_with_deepseek(
                candidate,
                tuple(dict.fromkeys((*deterministic_issues, *review_issues))),
                context,
                api_key,
                model,
                timeout_seconds,
            )
            if not reply_quality_issues(repaired, context):
                return _normalize_reply(repaired)
        return _fallback_reply(context)

    if candidate:
        return _normalize_reply(candidate)
    return _fallback_reply(context)


def reply_quality_issues(reply: str, context: ReplyDraftContext) -> tuple[str, ...]:
    """Return stable, user-safe quality failures without calling a provider."""
    clean = _normalize_reply(reply)
    if not clean:
        return ("empty reply",)

    issues: list[str] = []
    lowered = clean.lower()
    if COMMERCIAL_PATTERN.search(clean):
        issues.append("commercial term")
    if AI_MENTION_PATTERN.search(clean):
        issues.append("AI mention")
    if GENERIC_PHRASE_PATTERN.search(clean):
        issues.append("generic phrase")
    if _has_unapproved_clarification(clean, context):
        issues.append("unapproved clarification")
    if _has_unsupported_current_state_claim(clean, context):
        issues.append("unsupported current state")
    if _has_unsupported_task_action(clean, context):
        issues.append("unsupported task action")
    if UNCERTAIN_COMMITMENT_PATTERN.search(clean):
        issues.append("uncertain commitment")
    if CUSTOMER_SKILL_ASSUMPTION_PATTERN.search(clean):
        issues.append("customer skill assumption")
    if clean.count("?") > 1:
        issues.append("too many questions")
    if len(clean) < MIN_REPLY_LENGTH:
        issues.append("too short")
    if len(clean) > MAX_REPLY_LENGTH:
        issues.append("too long")
    sentence_count = len(_sentences(clean))
    if sentence_count < 3:
        issues.append("too few sentences")
    if sentence_count > MAX_REPLY_SENTENCES:
        issues.append("too many sentences")
    if not ACTION_PATTERN.search(clean):
        issues.append("missing concrete action")
    if not _mentions_task(clean, context):
        issues.append("missing task reference")
    return tuple(issues)


def reply_delivery_issues(reply: str, context: ReplyDraftContext) -> tuple[str, ...]:
    """Return only unsafe issues that must block direct delivery to a customer."""
    return tuple(
        issue for issue in reply_quality_issues(reply, context) if issue in DELIVERY_BLOCKING_ISSUES
    )


def reply_delivery_issue_labels(reply: str, context: ReplyDraftContext) -> tuple[str, ...]:
    """Return customer-facing explanations for delivery blockers."""
    return tuple(
        DELIVERY_ISSUE_LABELS.get(issue, issue)
        for issue in reply_delivery_issues(reply, context)
    )


def reply_delivery_issue_summary(reply: str, context: ReplyDraftContext) -> str:
    labels = reply_delivery_issue_labels(reply, context)
    if not labels:
        return ""
    return "отклик требует правки: " + "; ".join(labels[:2])


def _compose_with_deepseek(
    context: ReplyDraftContext,
    api_key: str,
    model: str,
    timeout_seconds: float,
) -> str:
    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com/v1",
            timeout=timeout_seconds,
        )
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": _WRITER_SYSTEM_PROMPT},
                {"role": "user", "content": _writer_prompt(context)},
            ],
            temperature=0.35,
            max_tokens=800,
        )
        return str(response.choices[0].message.content or "").strip()
    except Exception:
        logger.exception("DeepSeek reply composition failed; using safe fallback")
        return ""


def _review_with_deepseek(
    candidate: str,
    context: ReplyDraftContext,
    api_key: str,
    model: str,
    timeout_seconds: float,
) -> ReplyQualityResult | None:
    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com/v1",
            timeout=timeout_seconds,
        )
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": _REVIEWER_SYSTEM_PROMPT},
                {"role": "user", "content": _review_prompt(candidate, context)},
            ],
            temperature=0,
            max_tokens=450,
        )
        return _parse_review_response(str(response.choices[0].message.content or ""))
    except Exception:
        logger.exception("DeepSeek reply review failed; using deterministic quality checks")
        return None


def _repair_with_deepseek(
    candidate: str,
    issues: tuple[str, ...],
    context: ReplyDraftContext,
    api_key: str,
    model: str,
    timeout_seconds: float,
) -> str:
    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com/v1",
            timeout=timeout_seconds,
        )
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": _REPAIR_SYSTEM_PROMPT},
                {"role": "user", "content": _repair_prompt(candidate, issues, context)},
            ],
            temperature=0.2,
            max_tokens=800,
        )
        return _remove_commercial_sentences(str(response.choices[0].message.content or ""))
    except Exception:
        logger.exception("DeepSeek reply repair failed; using deterministic fallback")
        return ""


def _writer_prompt(context: ReplyDraftContext) -> str:
    facts = _redacted_facts(context)
    question = _safe_question(context.blocking_question)
    question_policy = (
        "Разрешён ровно один вопрос, только дословно такой: "
        f"«{question}». Не добавляй другие вопросы, просьбы уточнить детали, прислать файлы или дать доступ."
        if question
        else "Не задавай вопросов и не проси уточнения, файлы, доступы или подтверждения. "
        "Если детали неизвестны, не выдумывай их и продолжай по фактам задачи. "
        "Не добавляй факты о текущем состоянии сайта, устройствах, доступах или технологиях, если их нет в фактах."
        " Не описывай внутренние сомнения и условные обещания: не пиши «пока исхожу», «это уточняется» или «если понадобится»."
        " Не оценивай навыки заказчика и не пиши «если вы не работали с этим раньше» или «вам будет сложно»."
    )
    return "\n\n".join(
        part
        for part in (
            "Факты по задаче:\n" + facts,
            (
                "Напиши готовое сообщение заказчику: 4-5 коротких предложений, 350-850 символов. "
                "Сначала покажи, что понял конечный результат, затем назови конкретные действия и проверку. "
                f"Реалистичный срок: до {max(1, context.estimated_days)} дн. "
                "Не упоминай коммерческие условия, скидки, оплату, AI, нейросети, портфолио или опыт, которого нет. "
                "Не повторяй всё ТЗ, не используй фразы «план такой» или «если нужно, скажите». "
                "Не делай больше пяти предложений, или шести вместе с отдельным приветствием. "
                "Последним предложением от первого лица спокойно подтверди готовность начать работу; "
                "не перекладывай на клиента поиск ответа или согласование деталей."
            ),
            question_policy,
        )
        if part
    )


def _review_prompt(candidate: str, context: ReplyDraftContext) -> str:
    question = _safe_question(context.blocking_question)
    question_policy = (
        f"Разрешён ровно один вопрос, только дословно такой: «{question}»."
        if question
        else "Вопросов и просьб к заказчику в этом отклике быть не должно."
    )
    return (
        "Проверь отклик на Kwork-заказ. Одобри только если он опирается на факты, "
        "решает основную задачу клиента, называет конкретные действия и результат, "
        "не содержит коммерческих условий, выдуманных утверждений, AI-слов и пустых фраз. "
        "Утверждение о том, что что-то уже работает или не работает на конкретном устройстве или в среде, "
        "допустимо только если это прямо есть в фактах. "
        "Отклони условные обещания и фразы про внутреннюю неопределенность, например «пока исхожу» или «это уточняется». "
        "Отклони оценку навыков заказчика, например «если вы не работали с этим раньше» или «вам будет сложно». "
        f"{question_policy} "
        "Верни строго JSON: {\"approved\": true|false, \"issues\": [\"краткая причина\"]}.\n\n"
        f"Факты:\n{_redacted_facts(context)}\n\n"
        f"Отклик:\n{_normalize_reply(candidate)}"
    )


def _repair_prompt(candidate: str, issues: tuple[str, ...], context: ReplyDraftContext) -> str:
    issue_text = "; ".join(issues) or "нужна более точная формулировка"
    question = _safe_question(context.blocking_question)
    question_policy = (
        f"Разрешён только вопрос «{question}» и только один раз."
        if question
        else "Не задавай вопросов и не проси заказчика уточнить, прислать или подтвердить что-либо."
    )
    return (
        "Перепиши отклик по фактам ниже. Верни только готовый текст без markdown. "
        "Сохрани спокойный человеческий тон, 4-5 предложений и 350-850 символов. "
        "Не добавляй коммерческие условия, выдуманный опыт или AI-слова. "
        "Не добавляй неподтвержденные факты о текущем состоянии сайта, устройствах, доступах или технологиях. "
        "Не описывай внутренние сомнения, условные обещания или фразы «пока исхожу» и «это уточняется». "
        "Не оценивай навыки заказчика и не добавляй формулировки про его опыт или сложность для него. "
        f"{question_policy}\n\n"
        f"Причины правки: {issue_text}\n\n"
        f"Факты:\n{_redacted_facts(context)}\n\n"
        f"Текущий отклик:\n{_normalize_reply(candidate)}"
    )


def _redacted_facts(context: ReplyDraftContext) -> str:
    parts = [
        f"Название: {_redact_commercial_context(context.title)}",
        f"Суть: {_redact_commercial_context(context.task_summary)}",
        f"Описание: {_redact_commercial_context(context.source_text)}",
    ]
    attachment_text = _redact_commercial_context(context.attachment_context)
    if attachment_text:
        parts.append(f"Файлы и визуальные материалы: {attachment_text}")
    return "\n".join(part for part in parts if part.rstrip(": ").strip())[:7000]


def _redact_commercial_context(value: str) -> str:
    parts = re.split(r"(?<=[.!?])\s+|\n+", value)
    safe_parts = [part.strip() for part in parts if part.strip() and not COMMERCIAL_PATTERN.search(part)]
    return " ".join(safe_parts)


def _remove_commercial_sentences(reply: str) -> str:
    sentences = _sentences(reply)
    return " ".join(sentence for sentence in sentences if not COMMERCIAL_PATTERN.search(sentence))


def _normalize_reply(value: str) -> str:
    clean = value.replace("```", " ").replace("\r", " ")
    return " ".join(clean.split()).strip()


def _sentences(value: str) -> list[str]:
    clean = _normalize_reply(value)
    if not clean:
        return []
    return [sentence.strip() for sentence in SENTENCE_SPLIT_PATTERN.split(clean) if sentence.strip()]


def _mentions_task(reply: str, context: ReplyDraftContext) -> bool:
    reply_lower = reply.lower()
    source = " ".join((context.title, context.task_summary, context.source_text)).lower()
    ignored = {
        "задача", "сделать", "нужно", "сайта", "сайт", "работа", "клиент", "заказ",
        "срок", "дней", "день", "готово", "результат", "пожалуйста",
    }
    keywords = [word for word in WORD_PATTERN.findall(source) if word.lower() not in ignored]
    return any(word[:4].lower() in reply_lower for word in keywords)


def _safe_question(value: str) -> str:
    question = _normalize_reply(value)
    if not question or GENERIC_PHRASE_PATTERN.search(question) or question.count("?") > 1:
        return ""
    return question[:220]


def _has_unapproved_clarification(reply: str, context: ReplyDraftContext) -> bool:
    """Allow only the exact blocking question, when the judge supplied one."""
    allowed_question = _question_key(_safe_question(context.blocking_question))
    for sentence in _sentences(reply):
        normalized_sentence = _question_key(sentence)
        is_allowed_question = bool(allowed_question and normalized_sentence == allowed_question)
        if "?" in sentence and not is_allowed_question:
            return True
        if is_allowed_question:
            continue
        if CLARIFICATION_REQUEST_PATTERN.search(sentence):
            return True
        if IMPLICIT_QUESTION_PATTERN.search(sentence):
            return True
    return False


def _question_key(value: str) -> str:
    return _normalize_reply(value).lower().rstrip(" ?!.")


def _has_unsupported_current_state_claim(reply: str, context: ReplyDraftContext) -> bool:
    """Reject claims that an unmentioned environment already works or fails."""
    source = " ".join(
        (context.title, context.task_summary, context.source_text, context.attachment_context)
    ).lower()
    for claim in CURRENT_STATE_CLAIM_PATTERN.findall(reply):
        lowered_claim = claim.lower()
        for environment_group in CURRENT_STATE_ENVIRONMENT_GROUPS:
            if any(term in lowered_claim for term in environment_group) and not any(
                term in source for term in environment_group
            ):
                return True
    return False


def _has_unsupported_task_action(reply: str, context: ReplyDraftContext) -> bool:
    """Reject specific implementation claims that have no support in the order facts."""
    facts = " ".join(
        (context.title, context.task_summary, context.source_text, context.attachment_context)
    )
    return any(
        pattern.search(reply) is not None and pattern.search(facts) is None
        for pattern in TASK_ACTION_REFERENCE_PATTERNS
    )


def _fallback_reply(context: ReplyDraftContext) -> str:
    summary = _safe_fallback_summary(context)
    details = " ".join((context.title, context.task_summary, context.source_text, context.attachment_context)).lower()
    actions, check = _fallback_actions(details)
    return (
        f"Здравствуйте! Посмотрел задачу: {summary}. "
        f"{actions} "
        f"{check} "
        f"На работу ориентируюсь на {max(1, context.estimated_days)} дн., могу приступить сразу."
    )


def _safe_fallback_summary(context: ReplyDraftContext) -> str:
    for value in (context.task_summary, context.title):
        summary = _redact_commercial_context(value)
        if summary and not _has_unsafe_summary_language(summary):
            return summary[:180].rstrip(" .,:;-")
    return "вашу задачу по сайту"


def _has_unsafe_summary_language(value: str) -> bool:
    return any(
        pattern.search(value) is not None
        for pattern in (
            AI_MENTION_PATTERN,
            GENERIC_PHRASE_PATTERN,
            CLARIFICATION_REQUEST_PATTERN,
            UNCERTAIN_COMMITMENT_PATTERN,
            CUSTOMER_SKILL_ASSUMPTION_PATTERN,
        )
    )


def _fallback_actions(details: str) -> tuple[str, str]:
    if FORM_TASK_PATTERN.search(details):
        return (
            "Сначала разберу сценарий работы формы и обработку заявок, затем внесу нужные правки в разметку и логику.",
            "После изменений пройду основной пользовательский сценарий и проверю, что заявки доходят корректно.",
        )
    if WORDPRESS_TASK_PATTERN.search(details):
        return (
            "Разберу структуру сайта и требования, затем внесу нужные изменения на WordPress.",
            "После этого пройду основной пользовательский сценарий и покажу работающий результат.",
        )
    if LAYOUT_TASK_PATTERN.search(details):
        return (
            "Сверстаю нужные блоки по описанию, настрою адаптив и аккуратно подключу требуемую логику.",
            "Проверю отображение на основных разрешениях и покажу готовый вариант перед сдачей.",
        )
    if INTEGRATION_TASK_PATTERN.search(details):
        return (
            "Сначала сверю входные данные и текущую интеграцию, затем настрою обмен и обработку нужных полей.",
            "После этого проверю работу на реальном сценарии и зафиксирую результат.",
        )
    if DOMAIN_TASK_PATTERN.search(details):
        return (
            "Проверю текущие DNS-записи и настройки проекта, затем внесу необходимые изменения без лишних редиректов.",
            "После этого удостоверюсь, что сайт корректно открывается по нужному адресу.",
        )
    return (
        "Сначала разберу текущую реализацию и требования, затем внесу нужные изменения по задаче.",
        "После этого проверю основной сценарий и покажу готовый рабочий результат.",
    )


def _parse_review_response(raw: str) -> ReplyQualityResult | None:
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end < start:
        return None
    try:
        payload = json.loads(raw[start : end + 1])
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    issues_value = payload.get("issues", [])
    if isinstance(issues_value, str):
        issues = (issues_value.strip(),) if issues_value.strip() else ()
    elif isinstance(issues_value, list):
        issues = tuple(str(item).strip() for item in issues_value if str(item).strip())[:5]
    else:
        issues = ()
    approved = bool(payload.get("approved")) and not issues
    return ReplyQualityResult(approved=approved, issues=issues)


_WRITER_SYSTEM_PROMPT = (
    "Ты опытный веб-разработчик, который пишет короткие отклики на Kwork. "
    "Твоя цель не продать любой ценой, а показать спокойное понимание задачи и понятный план работы. "
    "Пиши как человек, без канцелярита и шаблонных продаж. Возвращай только текст сообщения."
)

_REVIEWER_SYSTEM_PROMPT = (
    "Ты строгий редактор откликов веб-разработчика. Проверяй только факты и качество сообщения. "
    "Возвращай только валидный JSON без markdown."
)

_REPAIR_SYSTEM_PROMPT = (
    "Ты опытный веб-разработчик. Переписываешь отклик по фактам так, чтобы он был конкретным, честным и полезным заказчику. "
    "Возвращай только текст сообщения без markdown."
)
