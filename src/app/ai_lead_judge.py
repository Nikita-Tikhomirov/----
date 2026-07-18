from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any

from app.reply_policy import COMMERCIAL_REPLY_PATTERN

logger = logging.getLogger(__name__)

BITRIX_PATTERN = re.compile(r"битрикс|bitrix", re.IGNORECASE)
SIMPLE_PATTERN = re.compile(
    r"верст|лендинг|landing|html|css|js|javascript|wordpress|вордпресс|wp|форма|"
    r"адаптив|правк|поправ|исправ|калькулятор|парсер|бот|интеграц",
    re.IGNORECASE,
)
BUDGET_PATTERN = re.compile(r"(\d[\d\s]{2,})\s*(?:₽|руб|р\b)", re.IGNORECASE)
COMMERCIAL_SUMMARY_SEGMENT_PATTERN = re.compile(
    r"(?:"
    r"\b(?:цена|бюджет|стоимость|ставка|предоплата|price|budget)\b\s*[:—-]?\s*[^,.;!?\n]*(?:[,.;!?]|$)"
    r"|\bуслови\w*\s+оплат\w*\b\s*[:—-]?\s*[^,.;!?\n]*(?:[,.;!?]|$)"
    r"|\bоплат\w*\s+(?:за|по|после|перед|работ\w*|услуг\w*|сделан\w*|проект\w*|частями|сразу|потом|перевод\w*|деньг\w*)\b\s*[^,.;!?\n]*(?:[,.;!?]|$)"
    r")",
    re.IGNORECASE,
)
GENERIC_QUESTION_PATTERN = re.compile(
    r"(?:уточните\s+детали|обсудим\s+детали|расскажите\s+подробнее|"
    r"давайте\s+обсудим|можем\s+обсудить)",
    re.IGNORECASE,
)
ACTION_PATTERN = re.compile(
    r"(?:сдела|исправ|сверста|настро|реализ|собер|провер|подготов|подключ|доработ|"
    r"интегрир|оптимизир|адаптир)",
    re.IGNORECASE,
)
DEFAULT_ACCEPT_DECISIONS = ("accept", "maybe")
DEFAULT_BLOCKED_KEYWORDS = ("битрикс", "bitrix")
DEFAULT_HARD_REJECT_KEYWORDS: tuple[str, ...] = ()


@dataclass(frozen=True)
class LeadJudgeResult:
    accepted: bool
    decision: str
    score: int
    complexity: str
    estimated_days: int
    price_rub: int
    summary: str
    reasons: list[str]
    risks: list[str]
    questions: list[str]
    draft_reply: str
    customer_goal: str = ""
    work_plan: list[str] = field(default_factory=list)


def judge_lead(
    text: str,
    api_key: str = "",
    model: str = "deepseek-chat",
    timeout_seconds: float = 45.0,
    min_score: int = 60,
    max_estimated_days: int = 7,
    accept_decisions: tuple[str, ...] = DEFAULT_ACCEPT_DECISIONS,
    blocked_keywords: tuple[str, ...] = DEFAULT_BLOCKED_KEYWORDS,
    hard_reject_keywords: tuple[str, ...] = DEFAULT_HARD_REJECT_KEYWORDS,
) -> LeadJudgeResult:
    """Score a Kwork lead against the user's week-with-AI fit criteria."""
    blocked = _matched_keywords(text, blocked_keywords)
    if BITRIX_PATTERN.search(text):
        return _reject("Bitrix/Битрикс исключен", text)
    if blocked:
        return _reject(f"стоп-слова: {', '.join(blocked)}", text)

    hard_reject = _matched_keywords(text, hard_reject_keywords)
    if hard_reject:
        return _reject(f"рискованный стек: {', '.join(hard_reject)}", text)

    if api_key:
        ai_result = _judge_with_deepseek(
            text=text,
            api_key=api_key,
            model=model,
            timeout_seconds=timeout_seconds,
        )
        if ai_result is not None:
            return _apply_acceptance_settings(
                ai_result,
                min_score=min_score,
                max_estimated_days=max_estimated_days,
                accept_decisions=accept_decisions,
            )

    return _apply_acceptance_settings(
        _fallback_judge(text),
        min_score=min_score,
        max_estimated_days=max_estimated_days,
        accept_decisions=accept_decisions,
    )


def parse_judge_response(raw: str) -> LeadJudgeResult:
    payload = _extract_json(raw)
    decision = _clean_decision(str(payload.get("decision", "reject")))
    score = _clamp_int(payload.get("score"), 0, 100, default=0)
    estimated_days = _clamp_int(payload.get("estimated_days"), 1, 7, default=7)
    price_rub = _clamp_int(payload.get("price_rub"), 0, 500_000, default=0)
    complexity = _clean_complexity(str(payload.get("complexity", "unknown")))
    summary = _clean_text(str(payload.get("summary", ""))) or "Kwork-заказ"
    customer_goal = _clean_text(str(payload.get("customer_goal", "")))[:420]
    work_plan = _list_of_strings(payload.get("work_plan"))[:4]
    reasons = _list_of_strings(payload.get("reasons"))[:5]
    risks = _list_of_strings(payload.get("risks"))[:5]
    questions = _list_of_strings(payload.get("questions"))[:1]
    draft_reply = clean_customer_reply(
        str(payload.get("draft_reply", "")),
        summary=summary,
        estimated_days=estimated_days,
    )

    accepted = decision in {"accept", "maybe"} and score >= 60 and estimated_days <= 7
    if not reasons:
        reasons = ["AI-оценка без подробных причин"]

    return LeadJudgeResult(
        accepted=accepted,
        decision=decision,
        score=score,
        complexity=complexity,
        estimated_days=estimated_days,
        price_rub=price_rub,
        summary=summary,
        reasons=reasons,
        risks=risks,
        questions=questions,
        draft_reply=draft_reply,
        customer_goal=customer_goal,
        work_plan=work_plan,
    )


def _judge_with_deepseek(
    *,
    text: str,
    api_key: str,
    model: str,
    timeout_seconds: float,
) -> LeadJudgeResult | None:
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
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": _build_prompt(text)},
            ],
            temperature=0.25,
            max_tokens=1200,
        )
        content = response.choices[0].message.content or ""
        return parse_judge_response(content)
    except Exception:
        logger.exception("DeepSeek lead judge failed, using fallback")
        return None


def _fallback_judge(text: str) -> LeadJudgeResult:
    simple = bool(SIMPLE_PATTERN.search(text))
    estimated_days = 2 if simple else 5
    price_rub = max(_first_budget(text), 5000 if simple else 12000)
    score = 78 if simple else 62
    decision = "accept" if simple else "maybe"
    summary = _summary_from_text(text)
    questions = ["Есть ли готовое описание результата или пример, на который ориентироваться?"] if not simple else []

    return LeadJudgeResult(
        accepted=True,
        decision=decision,
        score=score,
        complexity="simple" if simple else "medium",
        estimated_days=estimated_days,
        price_rub=price_rub,
        summary=summary,
        reasons=["похоже реально сделать за неделю с AI-агентом"],
        risks=[] if simple else ["нужно быстро сверить детали перед стартом"],
        questions=questions,
        draft_reply=_fallback_reply(summary, estimated_days),
        customer_goal=summary,
        work_plan=_fallback_work_plan(text),
    )


def _apply_acceptance_settings(
    result: LeadJudgeResult,
    min_score: int,
    max_estimated_days: int,
    accept_decisions: tuple[str, ...],
) -> LeadJudgeResult:
    allowed_decisions = {decision.strip().lower() for decision in accept_decisions if decision.strip()}
    accepted = (
        result.decision in allowed_decisions
        and result.score >= min_score
        and result.estimated_days <= max_estimated_days
    )
    if accepted == result.accepted:
        return result
    reasons = list(result.reasons)
    if not accepted:
        if result.decision not in allowed_decisions:
            reasons.append(f"решение AI не разрешено настройками: {result.decision}")
        if result.score < min_score:
            reasons.append(f"score {result.score} ниже порога {min_score}")
        if result.estimated_days > max_estimated_days:
            reasons.append(f"срок {result.estimated_days} дн. больше лимита {max_estimated_days}")
    return LeadJudgeResult(
        accepted=accepted,
        decision=result.decision,
        score=result.score,
        complexity=result.complexity,
        estimated_days=result.estimated_days,
        price_rub=result.price_rub,
        summary=result.summary,
        reasons=reasons,
        risks=result.risks,
        questions=result.questions,
        draft_reply=result.draft_reply,
        customer_goal=result.customer_goal,
        work_plan=result.work_plan,
    )


def _matched_keywords(text: str, keywords: tuple[str, ...]) -> list[str]:
    lowered = text.lower()
    matches: list[str] = []
    for keyword in keywords:
        clean = keyword.strip()
        if clean and clean.lower() in lowered and clean not in matches:
            matches.append(clean)
    return matches


def _reject(reason: str, text: str) -> LeadJudgeResult:
    summary = _summary_from_text(text)
    return LeadJudgeResult(
        accepted=False,
        decision="reject",
        score=0,
        complexity="too_complex",
        estimated_days=7,
        price_rub=0,
        summary=summary,
        reasons=[reason],
        risks=[reason],
        questions=[],
        draft_reply="",
    )


def _build_prompt(text: str) -> str:
    return (
        "Оцени Kwork-заказ для исполнителя с минимальными навыками разработки, "
        "но с AI-агентом на Pro-тарифе. Цель — брать простые и средние web-заказы, "
        "которые реально закрыть максимум за 7 дней.\n\n"
        "Критерии accept/maybe:\n"
        "- сайты, верстка, HTML/CSS/JS, WordPress, формы, калькуляторы, простые боты, парсеры, API-интеграции;\n"
        "- результат понятен из описания;\n"
        "- можно сделать за 1-7 дней с AI-агентом;\n"
        "- не требует глубокого senior-опыта.\n\n"
        "Критерии reject:\n"
        "- Bitrix/Битрикс, 1C/1С, мобильные приложения, React Native/Flutter, DevOps, blockchain, сложная CRM/ERP;\n"
        "- нет понятного результата;\n"
        "- явно больше недели;\n"
        "- слишком низкая цена при большом объёме.\n\n"
        "Составь живой отклик как нормальный человек. Не пиши как бот. "
        "Опирайся на Kwork facts: бюджет, срок, число предложений, вложения и текст ТЗ. "
        "Если в заказе есть блок Kwork attachments или Kwork attachment contents / ФАЙЛЫ/ТЗ, учитывай их как часть ТЗ. "
        "Если содержимое файла не удалось прочитать или это картинка без OCR, не выдумывай детали, а укажи риск. "
        "Не проси уточнить детали в целом и не пиши пустые фразы вроде «обсудим детали»; "
        "задай максимум один конкретный вопрос только если без него нельзя нормально начать. "
        "Не начинай с «я правильно понимаю» и не повторяй весь текст заказа. "
        "Цена/бюджет нужны только для внутренней оценки и поля цены на Kwork: не указывай цену, "
        "вилку, бюджет, валюту, скидки или условия оплаты в draft_reply. "
        "Техническую задачу про прием платежей можно упомянуть только если она прямо есть в заказе. "
        "В draft_reply коротко покажи, что понял главную боль клиента, дай конкретный следующий шаг, назови 2-3 конкретных шага "
        "и результат проверки. Укажи реалистичный срок без канцелярита и обещаний невозможного. "
        "Отдельно сформулируй customer_goal: главную боль клиента или нужный итог одним простым предложением. "
        "В work_plan перечисли 2-4 проверяемых шага, которые следуют только из ТЗ и вложений; это внутренний план для исполнителя, "
        "не добавляй туда отсутствующие технологии, доступы или интеграции. "
        "Отклик должен звучать как сообщение реального специалиста: 4-6 предложений, 350-800 символов, по делу. "
        "Верни строго JSON без markdown:\n"
        "{\n"
        '  "decision": "accept|maybe|reject",\n'
        '  "score": 0-100,\n'
        '  "complexity": "simple|medium|too_complex|unknown",\n'
        '  "estimated_days": 1-7,\n'
        '  "price_rub": число,\n'
        '  "summary": "краткое резюме",\n'
        '  "customer_goal": "главная боль или нужный заказчику результат, только по фактам",\n'
        '  "work_plan": ["2-4 конкретных шага по фактам ТЗ"],\n'
        '  "reasons": ["почему подходит или нет"],\n'
        '  "risks": ["риски"],\n'
        '  "questions": ["0-1 важный вопрос"],\n'
        '  "draft_reply": "готовый отклик заказчику"\n'
        "}\n\n"
        f"Заказ:\n{text}"
    )


_SYSTEM_PROMPT = (
    "Ты строгий помощник фрилансера. Твоя задача — не продать любой заказ, "
    "а выбрать только те Kwork-заказы, которые новичок с AI-агентом сможет сделать "
    "качественно за неделю максимум. Отвечай только валидным JSON."
)


def _extract_json(raw: str) -> dict[str, Any]:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("DeepSeek response does not contain JSON object")
    parsed = json.loads(cleaned[start : end + 1])
    if not isinstance(parsed, dict):
        raise ValueError("DeepSeek response JSON must be an object")
    return parsed


def _clean_decision(value: str) -> str:
    value = value.strip().lower()
    return value if value in {"accept", "maybe", "reject"} else "reject"


def _clean_complexity(value: str) -> str:
    value = value.strip().lower()
    return value if value in {"simple", "medium", "too_complex", "unknown"} else "unknown"


def _clamp_int(value: Any, minimum: int, maximum: int, default: int) -> int:
    try:
        number = int(float(str(value).replace(" ", "")))
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, number))


def _list_of_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [_clean_text(value)] if value.strip() else []
    if not isinstance(value, list):
        return []
    return [_clean_text(str(item)) for item in value if str(item).strip()]


def _clean_text(value: str) -> str:
    return " ".join(value.split())


def _first_budget(text: str) -> int:
    match = BUDGET_PATTERN.search(text)
    if not match:
        return 0
    return int(match.group(1).replace(" ", ""))


def _summary_from_text(text: str) -> str:
    first_line = _clean_text(text).removeprefix("📌").strip()
    return first_line[:120].rstrip() or "Kwork-заказ"


def _fallback_work_plan(text: str) -> list[str]:
    """Produce a conservative internal plan when the cloud judge is unavailable."""
    lowered = text.lower()
    plan = ["Проверить задачу и текущий сценарий"]
    if re.search(r"форм|заявк", lowered):
        plan.append("Исправить логику формы и обработку заявки")
    elif re.search(r"верст|лендинг|адаптив", lowered):
        plan.append("Внести правки в разметку и адаптивные стили")
    elif re.search(r"wordpress|вордпресс|\bwp\b", lowered):
        plan.append("Внести правки в WordPress-шаблон или настройки")
    else:
        plan.append("Реализовать изменения по описанию заказа")
    plan.append("Проверить результат по основному пользовательскому сценарию")
    return plan


def clean_customer_reply(reply: str, summary: str, estimated_days: int) -> str:
    """Return a concrete customer proposal without commercial terms or filler."""
    sentences = _reply_sentences(reply)
    safe_sentences = [
        sentence
        for sentence in sentences
        if not COMMERCIAL_REPLY_PATTERN.search(sentence)
        and not GENERIC_QUESTION_PATTERN.search(sentence)
    ]
    candidate = " ".join(safe_sentences).strip()
    if _reply_needs_fallback(candidate):
        return _fallback_reply(summary, estimated_days)
    return candidate


def sanitize_customer_reply(reply: str, summary: str, estimated_days: int) -> str:
    """Keep a manually written reply unless it leaks commercial terms to the customer."""
    clean = _clean_text(reply)
    if COMMERCIAL_REPLY_PATTERN.search(clean):
        return clean_customer_reply(clean, summary=summary, estimated_days=estimated_days)
    return clean


def _reply_sentences(value: str) -> list[str]:
    clean = _clean_text(value)
    if not clean:
        return []
    return [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", clean) if sentence.strip()]


def _reply_needs_fallback(reply: str) -> bool:
    return (
        len(reply) < 180
        or len(_reply_sentences(reply)) < 3
        or not ACTION_PATTERN.search(reply)
        or COMMERCIAL_REPLY_PATTERN.search(reply) is not None
    )


def _reply_safe_summary(summary: str) -> str:
    clean = _clean_text(summary)
    clean = COMMERCIAL_SUMMARY_SEGMENT_PATTERN.sub(" ", clean)
    clean = re.sub(
        r"(?:\b(?:бюджет|цена|стоимость)\b\s*[:\-]?\s*)?\d[\d\s.,]*\s*(?:₽|руб(?:\.|лей)?|р\.?)",
        "",
        clean,
        flags=re.IGNORECASE,
    )
    clean = re.sub(r"\b(?:бюджет|цена|стоимость)\b\s*[:\-]?\s*(?=$|[.!?,])", "", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\s+([,.!?])", r"\1", clean)
    return clean.strip(" ,.;:-")[:220] or "вашу задачу"


def _fallback_reply(summary: str, estimated_days: int) -> str:
    safe_summary = _reply_safe_summary(summary)
    return (
        f"Здравствуйте! Посмотрел задачу: {safe_summary}. "
        "Возьму на себя основную работу: разберу текущую реализацию и подготовлю понятный план изменений. "
        "Затем внесу правки, проверю результат на основных сценариях и покажу готовый вариант. "
        f"По сроку ориентируюсь на {estimated_days} дн. Готов приступить сразу."
    )
