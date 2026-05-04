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
    ("верстка", re.compile(r"верст|адаптив|лендинг|landing|сайт", re.IGNORECASE)),
    ("WordPress", re.compile(r"wordpress|wp|вордпресс", re.IGNORECASE)),
    ("форма", re.compile(r"форм|заявк|кнопк|поправ", re.IGNORECASE)),
)

BLOCKED_PATTERNS = (
    ("React", re.compile(r"\breact\b|next\.?js|gatsby", re.IGNORECASE)),
    ("конструктор", re.compile(r"tilda|webflow|wix|битрикс|bitrix|taplink", re.IGNORECASE)),
)

SMALL_TASK_PATTERN = re.compile(
    r"1-2\s*дн|1\s*день|2\s*дн|за день|пару часов|быстро|небольш|прост",
    re.IGNORECASE,
)
CONTACT_PATTERN = re.compile(r"@[A-Za-z0-9_]{5,}|https?://t\.me/[A-Za-z0-9_]+", re.IGNORECASE)


def evaluate_post(text: str) -> LeadEvaluation:
    normalized = " ".join(text.split())
    positive = [label for label, pattern in POSITIVE_PATTERNS if pattern.search(normalized)]
    blocked = [label for label, pattern in BLOCKED_PATTERNS if pattern.search(normalized)]
    contact = _extract_contact(normalized)
    reasons: list[str] = []

    if not positive:
        reasons.append("нет подходящего web-stack")
    reasons.extend(blocked)
    if not contact:
        reasons.append("нет контакта")

    small_task = bool(SMALL_TASK_PATTERN.search(normalized)) or len(normalized) <= 220
    if not small_task:
        reasons.append("похоже больше 1-2 дней")

    score = _score(positive, blocked, contact, small_task)
    accepted = score >= 70 and not blocked and contact != "" and bool(positive)
    if not accepted and not reasons:
        reasons.append("score ниже порога")

    return LeadEvaluation(
        accepted=accepted,
        score=score,
        summary=_summary(positive, small_task),
        draft_reply=_draft_reply(contact),
        contact=contact,
        reasons=", ".join(reasons),
    )


def _extract_contact(text: str) -> str:
    match = CONTACT_PATTERN.search(text)
    return match.group(0) if match else ""


def _score(positive: list[str], blocked: list[str], contact: str, small_task: bool) -> int:
    score = 20
    score += min(len(positive), 3) * 20
    if "WordPress" in positive:
        score += 10
    if contact:
        score += 15
    if small_task:
        score += 15
    score -= len(blocked) * 45
    return max(0, min(score, 100))


def _summary(positive: list[str], small_task: bool) -> str:
    stack = "/".join(dict.fromkeys(positive)) if positive else "web"
    size = "до 1-2 дней" if small_task else "нужно уточнить срок"
    return f"{stack} задача, {size}"


def _draft_reply(contact: str) -> str:
    greeting = "Здравствуйте!"
    return (
        f"{greeting} Готов помочь с задачей по сайту: HTML/CSS/JS или WordPress, "
        "могу быстро оценить объем и приступить. Пришлите, пожалуйста, детали и доступы, "
        "если задача еще актуальна."
    )
