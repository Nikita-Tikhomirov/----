from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class LeadEvaluation:
    accepted: bool
    score: int
    summary: str
    draft_reply: str
    contact: str
    reasons: str


POSITIVE_PATTERNS = (
    ("HTML/CSS/JS", re.compile(r"\b(html|css|js|javascript)\b", re.IGNORECASE)),
    ("верстка", re.compile(r"верст|адаптив|лендинг|landing|доработать сайт|правки на сайт|создать сайт", re.IGNORECASE)),
    ("WordPress", re.compile(r"wordpress|wp|вордпресс", re.IGNORECASE)),
    ("форма", re.compile(r"форм|заявк|кнопк|поправ", re.IGNORECASE)),
)

CORE_WEB_LABELS = {"HTML/CSS/JS", "верстка", "WordPress"}

BLOCKED_PATTERNS = (
    ("Bitrix", re.compile(r"битрикс|bitrix", re.IGNORECASE)),
)

SMALL_TASK_PATTERN = re.compile(
    r"1-2\s*дн|1\s*день|2\s*дн|за день|пару часов|быстро|небольш|прост|правк",
    re.IGNORECASE,
)
REPLY_URL_PATTERN = re.compile(r"Отклик:\s*(https?://\S+)", re.IGNORECASE)
CONTACT_PATTERN = re.compile(r"@[A-Za-z0-9_]{5,}|https?://\S+", re.IGNORECASE)
DEADLINE_PATTERN = re.compile(
    r"(срок(?:и)?\s*[:—-]?\s*[^.!,;]{1,40}|за\s+(?:1|2|один|два)\s+д(?:ень|ня)|1-2\s*дн(?:я|ей)?)",
    re.IGNORECASE,
)
BUDGET_PATTERN = re.compile(
    r"((?:бюджет|оплата|цена|стоимость)\s*[:—-]?\s*[^.!,;]{1,50}|\d[\d\s]*(?:₽|руб|р\b|usd|\$))",
    re.IGNORECASE,
)
TASK_HINTS = (
    ("сверстать лендинг", re.compile(r"сверст|верстк|лендинг|landing", re.IGNORECASE)),
    ("доработать сайт", re.compile(r"доработ|правк|поправ|исправ", re.IGNORECASE)),
    ("настроить форму или заявки", re.compile(r"форм|заявк", re.IGNORECASE)),
    ("поправить адаптив", re.compile(r"адаптив|мобил", re.IGNORECASE)),
    ("помочь с WordPress", re.compile(r"wordpress|wp|вордпресс", re.IGNORECASE)),
    ("добавить JavaScript-логику", re.compile(r"js|javascript|скрипт", re.IGNORECASE)),
)


def evaluate_post(
    text: str,
    deepseek_api_key: str = "",
    deepseek_model: str = "deepseek-chat",
) -> LeadEvaluation:
    normalized = " ".join(text.split())
    scored_text = re.sub(r"https?://\S+", "", normalized)
    positive = [label for label, pattern in POSITIVE_PATTERNS if pattern.search(scored_text)]
    blocked = [label for label, pattern in BLOCKED_PATTERNS if pattern.search(scored_text)]
    contact = _extract_contact(normalized)
    has_core_web = any(label in CORE_WEB_LABELS for label in positive)
    reasons: list[str] = []

    reasons.extend(blocked)
    if not contact:
        reasons.append("нет контакта")

    small_task = bool(SMALL_TASK_PATTERN.search(scored_text)) or len(scored_text) <= 260

    score = _score(positive, blocked, contact, small_task, has_core_web)
    accepted = not blocked and contact != ""
    if not accepted and not reasons:
        reasons.append("score ниже порога")

    return LeadEvaluation(
        accepted=accepted,
        score=score,
        summary=_summary(positive, small_task),
        draft_reply=_draft_reply(
            normalized, positive, small_task,
            deadline=_first_match(DEADLINE_PATTERN, normalized),
            budget=_first_match(BUDGET_PATTERN, normalized),
            api_key=deepseek_api_key,
            model=deepseek_model,
        ),
        contact=contact,
        reasons=", ".join(reasons),
    )


def _extract_contact(text: str) -> str:
    reply_match = REPLY_URL_PATTERN.search(text)
    if reply_match:
        return _clean_contact(reply_match.group(1))
    match = CONTACT_PATTERN.search(text)
    return _clean_contact(match.group(0)) if match else ""


def _clean_contact(contact: str) -> str:
    return contact.rstrip(").,;")


def _score(
    positive: list[str],
    blocked: list[str],
    contact: str,
    small_task: bool,
    has_core_web: bool,
) -> int:
    score = 35
    score += min(len(positive), 3) * 18
    if has_core_web:
        score += 20
    if "WordPress" in positive:
        score += 10
    if contact:
        score += 15
    if small_task:
        score += 15
    score -= len(blocked) * 100
    return max(0, min(score, 100))


def _summary(positive: list[str], small_task: bool) -> str:
    stack = "/".join(dict.fromkeys(positive)) if positive else "Kwork разработка"
    size = "быстрый отклик" if small_task else "нужно оценить по ссылке"
    return f"{stack} задача, {size}"


def _draft_reply(
    text: str,
    positive: list[str],
    small_task: bool,
    deadline: str = "",
    budget: str = "",
    api_key: str = "",
    model: str = "deepseek-chat",
) -> str:
    if api_key:
        from app.ai_reply import generate_reply

        ai_reply = generate_reply(
            text=text,
            positive=positive,
            small_task=small_task,
            deadline=deadline,
            budget=budget,
            api_key=api_key,
            model=model,
        )
        if ai_reply:
            return ai_reply

    task = _task_description(text, positive)
    details: list[str] = []

    if deadline:
        details.append(f"вижу срок: {deadline}")
    elif small_task:
        details.append("по объему похоже на небольшую задачу")

    if budget:
        details.append(f"учту бюджет: {budget}")

    details_sentence = f" Также {', '.join(details)}." if details else ""
    return (
        f"Здравствуйте! Вижу задачу: {task}. "
        "Готов взяться и быстро приступить без лишней переписки. "
        "Сделаю аккуратно, проверю результат и буду держать вас в курсе по ходу работы."
        f"{details_sentence} "
        "Могу начать в ближайшее время."
    )


def _task_description(text: str, positive: list[str]) -> str:
    hints = [label for label, pattern in TASK_HINTS if pattern.search(text)]
    if hints:
        return ", ".join(dict.fromkeys(hints[:3]))
    if positive:
        return "задача по " + "/".join(dict.fromkeys(positive))
    return "задача по сайту"


def _first_match(pattern: re.Pattern[str], text: str) -> str:
    match = pattern.search(text)
    return " ".join(match.group(1).split()) if match else ""
