"""
DeepSeek API integration for generating lead reply drafts.

Uses DeepSeek's OpenAI-compatible endpoint to produce contextual,
professional replies instead of rigid template strings.
"""

from __future__ import annotations

import logging

from app.ai_lead_judge import clean_customer_reply

logger = logging.getLogger(__name__)


def generate_reply(
    *,
    text: str,
    positive: list[str],
    small_task: bool,
    deadline: str = "",
    budget: str = "",
    api_key: str,
    model: str = "deepseek-chat",
    timeout_seconds: float = 30.0,
) -> str:
    """Generate a draft reply using DeepSeek API.

    Returns the AI-generated reply, or a fallback template reply
    if the API call fails (network error, auth, timeout, etc.).
    """
    if not api_key:
        logger.debug("DEEPSEEK_API_KEY is empty, using template fallback")
        return ""

    prompt = _build_prompt(
        text=text,
        positive=positive,
        small_task=small_task,
        deadline=deadline,
        budget=budget,
    )

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
                {"role": "user", "content": prompt},
            ],
            temperature=0.35,
            max_tokens=350,
        )
        reply = response.choices[0].message.content
        if reply:
            summary = ", ".join(positive) if positive else "вашу задачу по сайту"
            estimated_days = 2 if small_task else 5
            return clean_customer_reply(reply, summary=summary, estimated_days=estimated_days)
        logger.warning("DeepSeek returned empty response, using template fallback")
    except ImportError:
        logger.warning("openai package not installed, using template fallback")
    except Exception:
        logger.exception("DeepSeek API call failed, using template fallback")

    return ""


def _build_prompt(
    *,
    text: str,
    positive: list[str],
    small_task: bool,
    deadline: str,
    budget: str,
) -> str:
    parts: list[str] = []
    parts.append("Пост заказчика из Telegram-канала по фрилансу:\n")
    parts.append(text)

    if positive:
        parts.append(f"\nОпределённый стек: {', '.join(positive)}")
    if small_task:
        parts.append("Объём: небольшая задача (до 1-2 дней)")
    else:
        parts.append("Объём: срок не определён")
    if deadline:
        parts.append(f"Срок: {deadline}")
    parts.append(
        "\nНапиши короткий профессиональный отклик от лица веб-разработчика "
        "(сайты, интеграции, правки, автоматизация, WordPress, HTML/CSS/JS). "
        "Отклик должен быть вежливым, по делу, без шаблонных фраз. "
        "Покажи, что ты вник в задачу. "
        "Не задавай вопросов. "
        "Не проси доступы, макет, ТЗ или дополнительные детали. "
        "Пиши так, будто готов стартовать по уже описанной задаче. "
        "Цена и бюджет не входят в сообщение заказчику. "
        "Не используй markdown, только чистый текст."
    )
    return "\n".join(parts)


_SYSTEM_PROMPT = (
    "Ты — веб-разработчик на фрилансе. Ты пишешь короткие профессиональные отклики "
    "на посты заказчиков в Telegram-каналах по фрилансу.\n\n"
    "Правила:\n"
    "- Начинай с приветствия.\n"
    "- Покажи, что понял суть задачи (1-2 предложения).\n"
    "- Укажи реалистичный срок, если он есть в задаче.\n"
    "- Не упоминай цену, бюджет, оплату, валюту или скидки.\n"
    "- Не проси уточнить детали, макет, доступы, ТЗ или требования.\n"
    "- Не задавай вопросов и не ставь знак вопроса.\n"
    "- Заверши уверенной фразой о готовности быстро приступить.\n"
    "- Будь вежливым, конкретным, без воды и шаблонов.\n"
    "- Только чистый текст, без markdown.\n"
    "- Не более 5 предложений.\n"
    "- Отвечай на том же языке, на котором написан пост заказчика."
)
