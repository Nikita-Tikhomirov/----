import re
from unittest.mock import MagicMock, patch

import pytest

from app.ai_lead_judge import (
    LeadJudgeResult,
    _apply_acceptance_settings,
    _build_prompt,
    judge_lead,
    parse_judge_response,
    sanitize_customer_reply,
)
from app.llm_client import OpenRouterResult


def test_parse_judge_response_accepts_medium_week_task():
    raw = """
    {
      "decision": "accept",
      "score": 84,
      "complexity": "medium",
      "estimated_days": 5,
      "price_rub": 18000,
      "summary": "Доработать WordPress-сайт и форму заявки",
      "reasons": ["понятный результат", "реально сделать за неделю с AI"],
      "risks": ["нужно проверить доступы"],
      "questions": ["Есть ли доступ к админке WordPress?"],
      "draft_reply": "Здравствуйте! Посмотрел задачу, могу взяться."
    }
    """

    result = parse_judge_response(raw)

    assert result.accepted is True
    assert result.decision == "accept"
    assert result.score == 84
    assert result.estimated_days == 5
    assert result.price_rub == 18000
    assert "WordPress" in result.summary
    assert "доступ" in result.questions[0]


@pytest.mark.parametrize("complexity", ["too_complex", "unknown"])
def test_acceptance_gate_rejects_non_simple_complexity(complexity):
    result = LeadJudgeResult(
        accepted=True,
        decision="maybe",
        score=85,
        complexity=complexity,
        estimated_days=3,
        price_rub=10000,
        summary="Неопределённый проект",
        reasons=["часть объёма неизвестна"],
        risks=[],
        questions=[],
        draft_reply="Здравствуйте! Проверю задачу и выполню работу.",
    )

    gated = _apply_acceptance_settings(
        result,
        min_score=60,
        max_estimated_days=7,
        accept_decisions=("accept", "maybe"),
    )

    assert gated.accepted is False
    assert f"сложность {complexity} не разрешена" in gated.reasons


def test_judge_prompt_keeps_questions_internal_and_out_of_customer_draft():
    prompt = _build_prompt("Нужно исправить форму заявки на сайте.").lower()

    assert "blocking_question обычно оставляй пустой строкой" in prompt
    assert "только если без ответа невозможно" in prompt
    assert "никаких других вопросов" in prompt
    assert "начни draft_reply с «здравствуйте!»" in prompt
    assert "не пиши «план такой»" in prompt
    assert "не добавляй каналы связи" in prompt


def test_parse_judge_response_keeps_customer_goal_and_fact_grounded_work_plan():
    raw = """
    {
      "decision": "accept",
      "score": 84,
      "complexity": "medium",
      "estimated_days": 5,
      "price_rub": 18000,
      "summary": "Доработать WordPress-сайт и форму заявки",
      "customer_goal": "Чтобы заявки с сайта стабильно доходили и страница корректно выглядела на телефоне",
      "work_plan": [
        "Проверить текущую форму и точки отправки заявки",
        "Внести правки в шаблон и стили WordPress",
        "Протестировать сценарий заявки на мобильном и десктопе"
      ],
      "reasons": ["понятный результат", "реально сделать за неделю с AI"],
      "risks": ["нужно проверить доступы"],
      "questions": ["Есть ли доступ к админке WordPress?"],
      "blocking_question": "Куда должны поступать заявки?",
      "draft_reply": "Здравствуйте! Посмотрел задачу, могу взяться."
    }
    """

    result = parse_judge_response(raw)

    assert result.customer_goal.startswith("Чтобы заявки")
    assert result.work_plan == [
        "Проверить текущую форму и точки отправки заявки",
        "Внести правки в шаблон и стили WordPress",
        "Протестировать сценарий заявки на мобильном и десктопе",
    ]
    assert result.blocking_question == "Куда должны поступать заявки?"


def test_parse_judge_response_leaves_non_blocking_question_out_of_customer_reply_context():
    raw = """
    {
      "decision": "accept",
      "score": 90,
      "complexity": "simple",
      "estimated_days": 2,
      "price_rub": 7000,
      "summary": "Исправить форму заявки",
      "customer_goal": "Получать заявки с лендинга",
      "work_plan": ["Проверить форму", "Исправить отправку", "Протестировать"],
      "reasons": ["задача ясна"],
      "risks": [],
      "questions": ["Можно узнать цвет кнопки?"],
      "blocking_question": "",
      "draft_reply": "Здравствуйте! Исправлю форму и проверю отправку."
    }
    """

    result = parse_judge_response(raw)

    assert result.questions == ["Можно узнать цвет кнопки?"]
    assert result.blocking_question == ""


def test_parse_judge_response_rejects_scope_longer_than_one_week():
    raw = """
    {
      "decision": "accept",
      "score": 89,
      "complexity": "medium",
      "estimated_days": 14,
      "price_rub": 35000,
      "summary": "Доработать сайт с личным кабинетом",
      "reasons": ["задача подробно описана"],
      "risks": ["объем больше недели"],
      "questions": [],
      "draft_reply": "Здравствуйте!"
    }
    """

    result = parse_judge_response(raw)

    assert result.estimated_days == 14
    assert result.accepted is False


def test_judge_lead_rejects_bitrix_without_api_call():
    result = judge_lead(
        "Нужна интеграция Битрикс24 с CRM. Отклик: https://kwork.ru/projects/1",
        api_key="sk-test",
    )

    assert result.accepted is False
    assert result.decision == "reject"
    assert "Bitrix" in result.reasons[0]


def test_judge_lead_rejects_orders_that_forbid_ai_workflow_without_api_call():
    with patch("app.ai_lead_judge.openrouter_chat") as chat:
        result = judge_lead(
            "Нужен сайт на WordPress. Не использовать AI/vibe-coding как основной способ разработки.",
            api_key="or-test",
        )

    assert result.accepted is False
    assert result.decision == "reject"
    assert "AI" in result.reasons[0]
    chat.assert_not_called()


def test_judge_lead_uses_deepseek_json_verdict():
    with patch("openai.OpenAI") as mock_openai_class:
        mock_client = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = """
        {
          "decision": "maybe",
          "score": 72,
          "complexity": "medium",
          "estimated_days": 6,
          "price_rub": 22000,
          "summary": "Сделать калькулятор на сайте",
          "reasons": ["задача понятная", "можно сделать за неделю"],
          "risks": ["нужны формулы расчета"],
          "questions": ["Формулы расчета уже готовы?"],
          "draft_reply": "Здравствуйте! Могу сделать калькулятор на сайте за 5-6 дней."
        }
        """
        mock_client.chat.completions.create.return_value.choices = [mock_choice]
        mock_openai_class.return_value = mock_client

        result = judge_lead(
            "Нужен сайт-калькулятор услуг. Отклик: https://kwork.ru/projects/2",
            api_key="sk-test",
        )

    assert result.accepted is True
    assert result.decision == "maybe"
    assert result.score == 72
    assert result.price_rub == 22000
    assert "калькулятор" in result.draft_reply.lower()


def test_judge_lead_routes_analysis_through_openrouter_with_fallbacks():
    raw = """
    {
      "decision": "accept",
      "score": 88,
      "complexity": "simple",
      "estimated_days": 2,
      "price_rub": 9000,
      "summary": "Исправить форму заявки",
      "customer_goal": "Получать заявки без потерь",
      "work_plan": ["Проверить обработчик", "Исправить отправку", "Протестировать"],
      "reasons": ["понятный результат"],
      "risks": [],
      "questions": [],
      "blocking_question": "",
      "draft_reply": "Здравствуйте! Исправлю форму и проверю отправку заявок."
    }
    """
    with patch(
        "app.ai_lead_judge.openrouter_chat",
        return_value=OpenRouterResult(content=raw, model="openai/gpt-5.1"),
    ) as chat:
        result = judge_lead(
            "Нужно исправить форму заявки.",
            api_key="or-test",
            base_url="https://openrouter.example/v1",
            model="openai/gpt-5.1",
            fallback_models=("anthropic/claude-sonnet-4.5", "openai/gpt-4.1"),
        )

    assert result.customer_goal == "Получать заявки без потерь"
    assert result.blocking_question == ""
    call = chat.call_args.kwargs
    assert call["base_url"] == "https://openrouter.example/v1"
    assert call["primary_model"] == "openai/gpt-5.1"
    assert call["fallback_models"] == (
        "anthropic/claude-sonnet-4.5",
        "openai/gpt-4.1",
    )
    assert call["reasoning_effort"] == "minimal"
    assert call["response_format"] == {"type": "json_object"}


def test_judge_lead_never_publishes_rule_fallback_when_cloud_analysis_fails():
    with patch(
        "app.ai_lead_judge.openrouter_chat",
        side_effect=ConnectionError("OpenRouter is temporarily unavailable"),
    ):
        with pytest.raises(RuntimeError, match="cloud AI analysis unavailable"):
            judge_lead(
                "Нужно проверить аналитику лендинга и найти расхождение с Метрикой.",
                api_key="or-test",
            )


def test_judge_lead_applies_configurable_thresholds_to_ai_result():
    with patch("openai.OpenAI") as mock_openai_class:
        mock_client = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = """
        {
          "decision": "maybe",
          "score": 72,
          "complexity": "medium",
          "estimated_days": 6,
          "price_rub": 22000,
          "summary": "Сделать калькулятор на сайте",
          "reasons": ["задача понятная"],
          "risks": [],
          "questions": [],
          "draft_reply": "Здравствуйте! Сделаю калькулятор."
        }
        """
        mock_client.chat.completions.create.return_value.choices = [mock_choice]
        mock_openai_class.return_value = mock_client

        result = judge_lead(
            "Нужен сайт-калькулятор услуг. Отклик: https://kwork.ru/projects/2",
            api_key="sk-test",
            min_score=80,
            max_estimated_days=5,
            accept_decisions=("accept",),
        )

    assert result.accepted is False
    assert "score 72 ниже порога 80" in result.reasons
    assert "срок 6 дн. больше лимита 5" in result.reasons
    assert "решение AI не разрешено настройками: maybe" in result.reasons


def test_judge_lead_rejects_custom_hard_reject_keywords():
    result = judge_lead(
        "Нужно доработать WebGL сцену. Отклик: https://kwork.ru/projects/9",
        hard_reject_keywords=("webgl",),
    )

    assert result.accepted is False
    assert "webgl" in result.reasons[0]


def test_judge_lead_does_not_apply_extra_static_stack_rejections_by_default():
    result = judge_lead(
        "Нужна небольшая доработка сайта с обменом данными с 1С. "
        "Отклик: https://kwork.ru/projects/10",
        api_key="",
    )

    assert result.accepted is True
    assert not any("рискованный стек" in reason for reason in result.reasons)


def test_judge_lead_fallback_accepts_simple_site_task_without_questions():
    result = judge_lead(
        "Нужно поправить форму заявки на сайте и адаптив. Бюджет 5000 руб. "
        "Отклик: https://kwork.ru/projects/3",
        api_key="",
    )

    assert result.accepted is True
    assert result.estimated_days <= 2
    assert result.price_rub >= 5000
    assert len(result.questions) <= 1
    assert "руб" not in result.draft_reply.lower()
    assert "цена " not in result.draft_reply.lower()


def test_parse_judge_response_removes_price_and_generic_question_from_customer_reply():
    raw = """
    {
      "decision": "accept",
      "score": 81,
      "complexity": "simple",
      "estimated_days": 3,
      "price_rub": 9000,
      "summary": "Исправить форму заявки и адаптив на лендинге",
      "reasons": ["понятный объем"],
      "risks": [],
      "questions": [],
      "draft_reply": "Здравствуйте! Исправлю форму и адаптив за 3 дня, цена 9000 руб. Уточните детали. Сначала проверю текущую отправку формы, затем внесу правки и проверю на телефоне."
    }
    """

    result = parse_judge_response(raw)

    reply = result.draft_reply.lower()
    assert "9000" not in reply
    assert "руб" not in reply
    assert "цена " not in reply
    assert "уточните детали" not in reply
    assert "форм" in reply
    assert "телефон" in reply or "провер" in reply


def test_sanitize_customer_reply_removes_commercial_terms_from_legacy_reply():
    reply = sanitize_customer_reply(
        "Здравствуйте! Исправлю форму и адаптив за 3 дня, цена 9000 руб. "
        "Сначала проверю текущую отправку формы, затем внесу правки и проверю на телефоне.",
        summary="Исправить форму заявки и адаптив на лендинге",
        estimated_days=3,
    )

    lowered = reply.lower()
    assert "9000" not in lowered
    assert "руб" not in lowered
    assert re.search(r"\bцена\b", lowered) is None
    assert "форм" in lowered


def test_sanitize_customer_reply_does_not_restore_budget_from_legacy_summary():
    reply = sanitize_customer_reply(
        "Здравствуйте! Сделаю парсер, бюджет 9000 руб.",
        summary="Парсер товаров по категориям, бюджет до 500-1500 руб, есть скрин-пример.",
        estimated_days=3,
    )

    assert re.search(r"\b(?:цена|бюджет|стоимость|оплата|ставка)\b", reply, re.IGNORECASE) is None
    assert "руб" not in reply.lower()
    assert "парсер" in reply.lower()


def test_sanitize_customer_reply_keeps_technical_payment_feature():
    original = (
        "Здравствуйте! Посмотрел задачу по WordPress-сайту с каталогом товаров. "
        "Сверю структуру страниц, затем соберу нужные разделы и карточки каталога. "
        "Проверю сценарий оформления и оплаты, чтобы пользователь мог пройти путь до заказа. "
        "После этого покажу рабочий результат и смогу приступить сразу."
    )

    reply = sanitize_customer_reply(
        original,
        summary="Посадить сайт на WordPress с каталогом и подключением оплаты",
        estimated_days=5,
    )

    assert reply == original


def test_sanitize_customer_reply_removes_payment_terms():
    original = (
        "Здравствуйте! Посмотрел задачу по WordPress-сайту с каталогом товаров. "
        "Сверю структуру страниц, затем соберу нужные разделы и карточки каталога. "
        "Проверю сценарий оформления и оплаты, чтобы пользователь мог пройти путь до заказа. "
        "Оплата после сдачи, после этого покажу рабочий результат."
    )

    reply = sanitize_customer_reply(
        original,
        summary="Посадить сайт на WordPress с каталогом и подключением оплаты",
        estimated_days=5,
    )

    assert "оплата после сдачи" not in reply.lower()
    assert "сценарий оформления и оплаты" in reply.lower()


def test_build_prompt_demands_specific_human_kwork_reply():
    prompt = _build_prompt(
        "Kwork facts:\nБюджет: до 15000 руб.\nОсталось: 2 д.\n"
        "Kwork attachment contents:\nФАЙЛЫ/ТЗ: форма заявки и адаптив"
    )

    assert "не проси уточнить детали в целом" in prompt.lower()
    assert "Kwork facts" in prompt
    assert "ФАЙЛЫ/ТЗ" in prompt
    assert "конкретный следующий шаг" in prompt
    assert "не указывай цену" in prompt.lower()
    assert "не начинай с «я правильно понимаю»" in prompt.lower()
    assert '"blocking_question"' in prompt
    assert "обычно оставляй пустой строкой" in prompt.lower()


def test_build_prompt_allows_explicit_technical_payment_scope():
    prompt = _build_prompt("Нужны каталог товаров и подключение оплаты через сайт.").lower()

    assert "условия оплаты" in prompt
    assert "техническую задачу" in prompt
