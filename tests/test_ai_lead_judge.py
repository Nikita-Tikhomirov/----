from unittest.mock import MagicMock, patch

from app.ai_lead_judge import _build_prompt, judge_lead, parse_judge_response


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


def test_judge_lead_rejects_bitrix_without_api_call():
    result = judge_lead(
        "Нужна интеграция Битрикс24 с CRM. Отклик: https://kwork.ru/projects/1",
        api_key="sk-test",
    )

    assert result.accepted is False
    assert result.decision == "reject"
    assert "Bitrix" in result.reasons[0]


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
