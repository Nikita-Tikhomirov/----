from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

BITRIX_PATTERN = re.compile(r"битрикс|bitrix", re.IGNORECASE)
HARD_REJECT_PATTERN = re.compile(
    r"\b(1c|1с|android|ios|flutter|react\s+native)\b|мобильн(?:ое|ое приложение|ые приложения)|"
    r"блокчейн|crypto|крипто|devops|kubernetes|unity|unreal",
    re.IGNORECASE,
)
SIMPLE_PATTERN = re.compile(
    r"верст|лендинг|landing|html|css|js|javascript|wordpress|вордпресс|wp|форма|"
    r"адаптив|правк|поправ|исправ|калькулятор|парсер|бот|интеграц",
    re.IGNORECASE,
)
BUDGET_PATTERN = re.compile(r"(\d[\d\s]{2,})\s*(?:₽|руб|р\b)", re.IGNORECASE)


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


def judge_lead(
    text: str,
    api_key: str = "",
    model: str = "deepseek-chat",
    timeout_seconds: float = 45.0,
) -> LeadJudgeResult:
    """Score a Kwork lead against the user's week-with-AI fit criteria."""
    if BITRIX_PATTERN.search(text):
        return _reject("Bitrix/Битрикс исключен", text)

    if api_key:
        ai_result = _judge_with_deepseek(
            text=text,
            api_key=api_key,
            model=model,
            timeout_seconds=timeout_seconds,
        )
        if ai_result is not None:
            return ai_result

    return _fallback_judge(text)


def parse_judge_response(raw: str) -> LeadJudgeResult:
    payload = _extract_json(raw)
    decision = _clean_decision(str(payload.get("decision", "reject")))
    score = _clamp_int(payload.get("score"), 0, 100, default=0)
    estimated_days = _clamp_int(payload.get("estimated_days"), 1, 7, default=7)
    price_rub = _clamp_int(payload.get("price_rub"), 0, 500_000, default=0)
    complexity = _clean_complexity(str(payload.get("complexity", "unknown")))
    summary = _clean_text(str(payload.get("summary", ""))) or "Kwork-заказ"
    reasons = _list_of_strings(payload.get("reasons"))[:5]
    risks = _list_of_strings(payload.get("risks"))[:5]
    questions = _list_of_strings(payload.get("questions"))[:2]
    draft_reply = _clean_text(str(payload.get("draft_reply", "")))

    accepted = decision in {"accept", "maybe"} and score >= 60 and estimated_days <= 7
    if not draft_reply:
        draft_reply = _fallback_reply(summary, estimated_days, price_rub, questions)
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
    if HARD_REJECT_PATTERN.search(text):
        return _reject("слишком рискованный стек или не web-задача", text)

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
        draft_reply=_fallback_reply(summary, estimated_days, price_rub, questions),
    )


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
        "Если в заказе есть блок Kwork attachments, учитывай названия файлов как часть ТЗ; "
        "если файл нельзя прочитать напрямую, не выдумывай его содержимое, а укажи риск. "
        "Задай максимум один уточняющий вопрос и только если без него нельзя нормально оценить старт. "
        "В отклике укажи срок и цену/вилку. Верни строго JSON без markdown:\n"
        "{\n"
        '  "decision": "accept|maybe|reject",\n'
        '  "score": 0-100,\n'
        '  "complexity": "simple|medium|too_complex|unknown",\n'
        '  "estimated_days": 1-7,\n'
        '  "price_rub": число,\n'
        '  "summary": "краткое резюме",\n'
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


def _fallback_reply(summary: str, estimated_days: int, price_rub: int, questions: list[str]) -> str:
    price = f"по цене ориентируюсь от {price_rub:,} руб.".replace(",", " ")
    question = f" Единственный момент: {questions[0]}" if questions else ""
    return (
        f"Здравствуйте! Посмотрел задачу: {summary}. "
        f"Могу взяться и сделать аккуратно за {estimated_days} дн., {price} "
        "Начну с короткой проверки, затем сразу перейду к реализации и покажу результат по ходу работы."
        f"{question}"
    )
