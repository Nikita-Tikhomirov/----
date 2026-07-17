from unittest.mock import MagicMock, patch

from app.ai_reply import _SYSTEM_PROMPT, generate_reply, _build_prompt


def test_empty_api_key_returns_empty_string():
    result = generate_reply(
        text="Нужно сверстать лендинг",
        positive=["HTML/CSS/JS", "верстка"],
        small_task=True,
        api_key="",
    )
    assert result == ""


def test_api_error_returns_empty_string():
    with patch("openai.OpenAI") as mock_openai_class:
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API error")
        mock_openai_class.return_value = mock_client

        result = generate_reply(
            text="Нужно сверстать лендинг",
            positive=["HTML/CSS/JS"],
            small_task=True,
            api_key="sk-test-key",
        )
        assert result == ""


def test_successful_api_call_returns_reply():
    with patch("openai.OpenAI") as mock_openai_class:
        mock_client = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "Здравствуйте! Готов помочь с версткой."
        mock_client.chat.completions.create.return_value.choices = [mock_choice]
        mock_openai_class.return_value = mock_client

        result = generate_reply(
            text="Нужно сверстать лендинг HTML/CSS, 1 день. Бюджет 5000.",
            positive=["HTML/CSS/JS", "верстка"],
            small_task=True,
            deadline="1 день",
            budget="5000",
            api_key="sk-test-key",
        )
        assert "верст" in result.lower()
        assert "руб" not in result.lower()
        assert len(result) >= 180


def test_successful_api_call_removes_price_from_customer_reply():
    with patch("openai.OpenAI") as mock_openai_class:
        mock_client = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = (
            "Здравствуйте! Сделаю правки по форме. Цена 9000 руб. "
            "Сначала проверю текущую логику, затем внесу изменения и протестирую форму. "
            "Готов приступить сразу."
        )
        mock_client.chat.completions.create.return_value.choices = [mock_choice]
        mock_openai_class.return_value = mock_client

        result = generate_reply(
            text="Нужно исправить форму на лендинге",
            positive=["форма"],
            small_task=True,
            budget="9000 руб",
            api_key="sk-test-key",
        )

    assert "9000" not in result
    assert "руб" not in result.lower()
    assert "форма" in result.lower()


def test_successful_call_passes_correct_prompt():
    with patch("openai.OpenAI") as mock_openai_class:
        mock_client = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "Отклик"
        mock_client.chat.completions.create.return_value.choices = [mock_choice]
        mock_openai_class.return_value = mock_client

        generate_reply(
            text="Пост про WordPress",
            positive=["WordPress"],
            small_task=True,
            deadline="завтра",
            budget="3000 руб",
            api_key="sk-test-key",
        )

        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["model"] == "deepseek-chat"
        assert call_kwargs["temperature"] == 0.35
        assert call_kwargs["max_tokens"] == 350

        messages = call_kwargs["messages"]
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == _SYSTEM_PROMPT
        assert messages[1]["role"] == "user"
        assert "WordPress" in messages[1]["content"]
        assert "3000 руб" not in messages[1]["content"]
        assert "не упоминай цену" in messages[0]["content"].lower()


def test_custom_model_is_passed_through():
    with patch("openai.OpenAI") as mock_openai_class:
        mock_client = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "Reply"
        mock_client.chat.completions.create.return_value.choices = [mock_choice]
        mock_openai_class.return_value = mock_client

        generate_reply(
            text="Пост",
            positive=[],
            small_task=False,
            api_key="sk-test-key",
            model="deepseek-reasoner",
        )

        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["model"] == "deepseek-reasoner"


def test_empty_response_from_api_returns_empty_string():
    with patch("openai.OpenAI") as mock_openai_class:
        mock_client = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = ""
        mock_client.chat.completions.create.return_value.choices = [mock_choice]
        mock_openai_class.return_value = mock_client

        result = generate_reply(
            text="Пост",
            positive=[],
            small_task=True,
            api_key="sk-test-key",
        )
        assert result == ""


def test_none_response_from_api_returns_empty_string():
    with patch("openai.OpenAI") as mock_openai_class:
        mock_client = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = None
        mock_client.chat.completions.create.return_value.choices = [mock_choice]
        mock_openai_class.return_value = mock_client

        result = generate_reply(
            text="Пост",
            positive=[],
            small_task=True,
            api_key="sk-test-key",
        )
        assert result == ""


def test_build_prompt_includes_all_fields():
    prompt = _build_prompt(
        text="Нужно сверстать лендинг",
        positive=["верстка", "HTML/CSS/JS"],
        small_task=True,
        deadline="завтра",
        budget="5000 руб",
    )
    assert "Нужно сверстать лендинг" in prompt
    assert "верстка, HTML/CSS/JS" in prompt
    assert "небольшая задача" in prompt
    assert "завтра" in prompt
    assert "5000 руб" not in prompt


def test_build_prompt_without_optional_fields():
    prompt = _build_prompt(
        text="Задача",
        positive=[],
        small_task=False,
        deadline="",
        budget="",
    )
    assert "срок не определён" in prompt


def test_prompt_forbids_clarification_questions():
    prompt = _build_prompt(
        text="Нужно настроить сайт",
        positive=[],
        small_task=True,
        deadline="",
        budget="",
    )

    assert "Не задавай вопросов" in prompt
    assert "уточня" not in prompt.lower()
    assert "Не проси" in _SYSTEM_PROMPT
    assert "не упоминай цену" in _SYSTEM_PROMPT.lower()
