from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.llm_client import OpenRouterResult, openrouter_chat


def test_openrouter_chat_passes_ordered_deduplicated_fallback_models():
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = SimpleNamespace(
        model="anthropic/claude-sonnet-4.5",
        choices=[SimpleNamespace(message=SimpleNamespace(content="Готовый ответ"))],
    )

    with patch("openai.OpenAI", return_value=mock_client) as openai_class:
        result = openrouter_chat(
            api_key="or-test",
            base_url="https://openrouter.example/v1/",
            primary_model="anthropic/claude-sonnet-4.5",
            fallback_models=(
                "openai/gpt-5.1",
                "anthropic/claude-sonnet-4.5",
                "openai/gpt-4.1",
                "openai/gpt-5.1",
            ),
            messages=[{"role": "user", "content": "test"}],
            temperature=0.2,
            max_tokens=700,
            timeout_seconds=30,
        )

    assert result == OpenRouterResult(
        content="Готовый ответ",
        model="anthropic/claude-sonnet-4.5",
    )
    openai_class.assert_called_once_with(
        api_key="or-test",
        base_url="https://openrouter.example/v1",
        timeout=30,
        default_headers={"X-OpenRouter-Title": "Kwork Lead Funnel"},
    )
    call = mock_client.chat.completions.create.call_args.kwargs
    assert call["model"] == "anthropic/claude-sonnet-4.5"
    assert call["extra_body"] == {
        "models": ["openai/gpt-5.1", "openai/gpt-4.1"]
    }
    assert call["temperature"] == 0.2
    assert call["max_tokens"] == 700


def test_openrouter_chat_omits_fallback_body_when_no_models_are_configured():
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = SimpleNamespace(
        model="openai/gpt-4.1",
        choices=[SimpleNamespace(message=SimpleNamespace(content="Ответ"))],
    )

    with patch("openai.OpenAI", return_value=mock_client):
        openrouter_chat(
            api_key="or-test",
            base_url="https://openrouter.ai/api/v1",
            primary_model="openai/gpt-4.1",
            messages=[{"role": "user", "content": "test"}],
        )

    assert "extra_body" not in mock_client.chat.completions.create.call_args.kwargs

