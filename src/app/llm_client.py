"""Shared OpenRouter text completion client."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class OpenRouterResult:
    content: str
    model: str


def openrouter_chat(
    *,
    api_key: str,
    base_url: str,
    primary_model: str,
    messages: list[dict[str, str]],
    fallback_models: Iterable[str] = (),
    temperature: float = 0.2,
    max_tokens: int = 1000,
    timeout_seconds: float = 45.0,
    reasoning_effort: str = "",
    response_format: dict[str, str] | None = None,
) -> OpenRouterResult:
    """Return one completion, letting OpenRouter fail over between models."""
    if not api_key.strip():
        raise ValueError("OpenRouter API key is not configured")
    model = primary_model.strip()
    if not model:
        raise ValueError("OpenRouter primary model is not configured")

    from openai import OpenAI

    client = OpenAI(
        api_key=api_key,
        base_url=base_url.rstrip("/"),
        timeout=timeout_seconds,
        default_headers={"X-OpenRouter-Title": "Kwork Lead Funnel"},
    )
    request: dict[str, object] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    extra_body: dict[str, object] = {}
    fallbacks = _clean_fallback_models(model, fallback_models)
    if fallbacks:
        extra_body["models"] = list(fallbacks)
    effort = reasoning_effort.strip().lower()
    if effort:
        extra_body["reasoning"] = {"effort": effort, "exclude": True}
    if extra_body:
        request["extra_body"] = extra_body
    if response_format:
        request["response_format"] = dict(response_format)
    response = client.chat.completions.create(**request)
    content = str(response.choices[0].message.content or "").strip()
    used_model = str(getattr(response, "model", "") or model).strip()
    return OpenRouterResult(content=content, model=used_model)


def _clean_fallback_models(
    primary_model: str,
    fallback_models: Iterable[str],
) -> tuple[str, ...]:
    result: list[str] = []
    seen = {primary_model}
    for value in fallback_models:
        model = str(value).strip()
        if not model or model in seen:
            continue
        seen.add(model)
        result.append(model)
    return tuple(result)
