import re
from unittest.mock import MagicMock, patch

from app.reply_composer import ReplyDraftContext, compose_customer_reply, reply_quality_issues


def _form_context() -> ReplyDraftContext:
    return ReplyDraftContext(
        title="Исправить форму заявки",
        task_summary="Исправить отправку формы заявки и адаптив лендинга",
        source_text=(
            "На лендинге форма заявки не отправляется на мобильных. "
            "Бюджет до 5000 руб."
        ),
        attachment_context="ТЗ: на скрине показана форма и кнопка отправки.",
        estimated_days=2,
    )


def test_composer_replaces_commercial_generic_seed_with_task_focused_fallback():
    reply = compose_customer_reply(
        _form_context(),
        "Здравствуйте! Цена 5000 руб. Уточните детали, и обсудим всё.",
    )

    lowered = reply.lower()
    assert "5000" not in lowered
    assert "руб" not in lowered
    assert re.search(r"\b(?:цена|стоимость|бюджет|оплата)\b", lowered) is None
    assert "уточните детали" not in lowered
    assert "обсудим" not in lowered
    assert "форм" in lowered
    assert "мобиль" in lowered or "адаптив" in lowered
    assert "провер" in lowered
    assert len(reply) >= 260


def test_composer_redacts_budget_before_calling_deepseek_and_keeps_good_reply():
    good_reply = (
        "Здравствуйте! По задаче вижу, что форма заявки на лендинге не отправляется на мобильных. "
        "Проверю текущую валидацию и обработку отправки, затем внесу правки и приведу блок к адаптивному виду. "
        "После этого протестирую сценарий на телефоне и в основных браузерах, чтобы заявки доходили стабильно. "
        "На работу ориентируюсь на 2 дня и могу приступить сразу."
    )
    mock_client = MagicMock()
    writer_choice = MagicMock()
    writer_choice.message.content = good_reply
    reviewer_choice = MagicMock()
    reviewer_choice.message.content = '{"approved": true, "issues": []}'
    mock_client.chat.completions.create.side_effect = [
        MagicMock(choices=[writer_choice]),
        MagicMock(choices=[reviewer_choice]),
    ]

    with patch("openai.OpenAI", return_value=mock_client):
        reply = compose_customer_reply(_form_context(), "", api_key="sk-test")

    writer_prompt = mock_client.chat.completions.create.call_args_list[0].kwargs["messages"][1]["content"].lower()
    assert "5000" not in writer_prompt
    assert "бюджет" not in writer_prompt
    assert "руб" not in writer_prompt
    assert reply == good_reply


def test_composer_repairs_reply_rejected_by_ai_reviewer():
    repaired_reply = (
        "Здравствуйте! Вижу задачу по исправлению отправки формы заявки и адаптива лендинга. "
        "Сначала проверю текущую валидацию и обработку формы, затем внесу правки в разметку и стили для мобильных. "
        "После изменений протестирую отправку в основных браузерах и покажу готовый работающий сценарий. "
        "На работу потребуется до 2 дней, могу приступить сразу."
    )
    mock_client = MagicMock()
    writer_choice = MagicMock()
    writer_choice.message.content = "Здравствуйте! Готов помочь, обсудим детали."
    reviewer_choice = MagicMock()
    reviewer_choice.message.content = '{"approved": false, "issues": ["нет конкретных действий"]}'
    repair_choice = MagicMock()
    repair_choice.message.content = repaired_reply
    mock_client.chat.completions.create.side_effect = [
        MagicMock(choices=[writer_choice]),
        MagicMock(choices=[reviewer_choice]),
        MagicMock(choices=[repair_choice]),
    ]

    with patch("openai.OpenAI", return_value=mock_client):
        reply = compose_customer_reply(_form_context(), "", api_key="sk-test")

    assert reply == repaired_reply
    assert mock_client.chat.completions.create.call_count == 3


def test_quality_gate_marks_ai_and_multiple_questions_as_unsafe():
    issues = reply_quality_issues(
        "Привет! AI-агент всё сделает. Какой у вас макет? Какая CMS? Давайте обсудим детали.",
        _form_context(),
    )

    assert "AI mention" in issues
    assert "too many questions" in issues
    assert "generic phrase" in issues


def test_quality_gate_rejects_overly_detailed_reply():
    reply = (
        "Здравствуйте! Вижу проблему с отправкой формы заявки на мобильных. "
        "Сначала проверю текущую валидацию и обработку данных. "
        "Затем внесу правки в разметку и стили формы. "
        "Проверю, чтобы кнопка оставалась видимой на всех разрешениях. "
        "После этого протестирую отправку на телефоне и компьютере. "
        "Покажу рабочий результат перед сдачей. "
        "Готов приступить сразу."
    )

    issues = reply_quality_issues(reply, _form_context())

    assert "too many sentences" in issues
