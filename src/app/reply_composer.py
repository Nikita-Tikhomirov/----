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
                "Последним предложением спокойно подтверди готовность начать."
            ),
            f"Единственный допустимый вопрос, если он действительно нужен: {question}" if question else "",
        )
        if part
    )


def _review_prompt(candidate: str, context: ReplyDraftContext) -> str:
    return (
        "Проверь отклик на Kwork-заказ. Одобри только если он опирается на факты, "
        "решает основную задачу клиента, называет конкретные действия и результат, "
        "не содержит коммерческих условий, выдуманных утверждений, AI-слов и пустых фраз. "
        "Вопрос допустим только один и только если он нужен для старта. "
        "Верни строго JSON: {\"approved\": true|false, \"issues\": [\"краткая причина\"]}.\n\n"
        f"Факты:\n{_redacted_facts(context)}\n\n"
        f"Отклик:\n{_normalize_reply(candidate)}"
    )


def _repair_prompt(candidate: str, issues: tuple[str, ...], context: ReplyDraftContext) -> str:
    issue_text = "; ".join(issues) or "нужна более точная формулировка"
    return (
        "Перепиши отклик по фактам ниже. Верни только готовый текст без markdown. "
        "Сохрани спокойный человеческий тон, 4-5 предложений и 350-850 символов. "
        "Не добавляй коммерческие условия, выдуманный опыт, AI-слова или лишние вопросы.\n\n"
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


def _fallback_reply(context: ReplyDraftContext) -> str:
    summary = _redact_commercial_context(context.task_summary) or _redact_commercial_context(context.title)
    summary = summary[:180].rstrip(" .,:;-") or "вашу задачу по сайту"
    details = " ".join((context.title, context.task_summary, context.source_text, context.attachment_context)).lower()
    actions, check = _fallback_actions(details)
    return (
        f"Здравствуйте! Посмотрел задачу: {summary}. "
        f"{actions} "
        f"{check} "
        f"На работу ориентируюсь на {max(1, context.estimated_days)} дн., могу приступить сразу."
    )


def _fallback_actions(details: str) -> tuple[str, str]:
    if "форм" in details:
        return (
            "Сначала проверю текущую отправку формы и валидацию на мобильных, затем внесу нужные правки в разметку и стили.",
            "После изменений протестирую сценарий на телефоне и в основных браузерах, чтобы заявки стабильно доходили.",
        )
    if "wordpress" in details or "вордпресс" in details:
        return (
            "Проверю текущие настройки WordPress и связанные плагины, затем внесу изменения по задаче.",
            "После этого пройду основной пользовательский сценарий и покажу работающий результат.",
        )
    if any(word in details for word in ("верст", "лендинг", "адаптив", "макет", "figma", "psd")):
        return (
            "Сверстаю нужные блоки по описанию, настрою адаптив и аккуратно подключу требуемую логику.",
            "Проверю отображение на основных разрешениях и покажу готовый вариант перед сдачей.",
        )
    if any(word in details for word in ("api", "интеграц", "парсер", "импорт")):
        return (
            "Сначала сверю входные данные и текущую интеграцию, затем настрою обмен и обработку нужных полей.",
            "После этого проверю работу на реальном сценарии и зафиксирую результат.",
        )
    if any(word in details for word in ("домен", "dns", "vercel", "хостинг")):
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
