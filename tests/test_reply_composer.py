import re
from dataclasses import replace
from unittest.mock import MagicMock, patch

from app.reply_composer import (
    ReplyDraftContext,
    _writer_prompt,
    compose_customer_reply,
    reply_quality_issues,
)


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


def test_quality_gate_rejects_hidden_clarification_without_allowed_question():
    issues = reply_quality_issues(
        (
            "Здравствуйте! Вижу проблему с отправкой формы заявки и адаптивом лендинга. "
            "Проверю валидацию и обработку данных, затем внесу нужные правки в разметку и стили. "
            "Уточните, куда должны приходить заявки после отправки формы. "
            "После изменений протестирую сценарий на телефоне и в основных браузерах. "
            "Готов приступить сразу."
        ),
        _form_context(),
    )

    assert "unapproved clarification" in issues


def test_quality_gate_allows_only_explicit_blocking_question():
    context = replace(
        _form_context(),
        blocking_question="К какой CRM нужно подключить форму?",
    )
    issues = reply_quality_issues(
        (
            "Здравствуйте! Вижу задачу по исправлению формы заявки и адаптива лендинга. "
            "К какой CRM нужно подключить форму? "
            "Проверю текущую валидацию, внесу правки в обработку данных и адаптивные стили. "
            "После этого протестирую отправку формы на телефоне и компьютере. "
            "Готов приступить сразу."
        ),
        context,
    )

    assert "unapproved clarification" not in issues


def test_quality_gate_rejects_different_question_with_allowed_blocking_question():
    context = replace(
        _form_context(),
        blocking_question="К какой CRM нужно подключить форму?",
    )
    issues = reply_quality_issues(
        (
            "Здравствуйте! Вижу задачу по исправлению формы заявки и адаптива лендинга. "
            "Куда нужно отправлять заявки после заполнения формы? "
            "Проверю текущую валидацию, внесу правки в обработку данных и адаптивные стили. "
            "После этого протестирую отправку формы на телефоне и компьютере. "
            "Готов приступить сразу."
        ),
        context,
    )

    assert "unapproved clarification" in issues


def test_quality_gate_rejects_implicit_question_without_question_mark():
    issues = reply_quality_issues(
        (
            "Здравствуйте! Вижу проблему с отправкой формы заявки и адаптивом лендинга. "
            "Какая CRM используется для заявок с формы. "
            "Проверю текущую валидацию, внесу правки в обработку данных и адаптивные стили. "
            "После этого протестирую отправку формы на телефоне и компьютере. "
            "Готов приступить сразу."
        ),
        _form_context(),
    )

    assert "unapproved clarification" in issues


def test_quality_gate_rejects_unconfirmed_current_state_claim():
    issues = reply_quality_issues(
        (
            "Здравствуйте! Вижу проблему с отправкой формы заявки на мобильных и адаптивом лендинга. "
            "На десктопе всё работает, поэтому проверю обработку данных только для телефона. "
            "Затем внесу правки в разметку и стили, чтобы форма корректно реагировала на действия пользователя. "
            "После этого протестирую сценарий на телефоне и в основных браузерах. "
            "Готов приступить сразу."
        ),
        _form_context(),
    )

    assert "unsupported current state" in issues


def test_quality_gate_rejects_uncertain_commitment_about_unknown_requirement():
    issues = reply_quality_issues(
        (
            "Здравствуйте! Вижу проблему с отправкой формы заявки и адаптивом лендинга. "
            "Проверю текущую валидацию и обработку данных, затем внесу правки в разметку и стили. "
            "Если интеграция с CRM действительно нужна, смогу её реализовать, но пока исхожу из того, что это уточняется. "
            "После изменений протестирую сценарий на телефоне и в основных браузерах. "
            "Готов приступить сразу."
        ),
        _form_context(),
    )

    assert "uncertain commitment" in issues


def test_quality_gate_rejects_assumption_about_customer_skill():
    issues = reply_quality_issues(
        (
            "Здравствуйте! Вижу проблему с отправкой формы заявки и адаптивом лендинга. "
            "Проверю текущую валидацию и обработку данных, затем внесу правки в разметку и стили. "
            "Интеграция с CRM может потребовать дополнительных настроек, особенно если вы не работали с этим раньше. "
            "После изменений протестирую сценарий на телефоне и в основных браузерах. "
            "Готов приступить сразу."
        ),
        _form_context(),
    )

    assert "customer skill assumption" in issues


def test_writer_prompt_forbids_questions_without_blocking_question():
    prompt = _writer_prompt(_form_context()).lower()

    assert "не задавай вопросов" in prompt
    assert "не добавляй факты о текущем состоянии" in prompt
    assert "не описывай внутренние сомнения" in prompt
    assert "не оценивай навыки заказчика" in prompt


def test_composer_falls_back_when_provider_keeps_prohibited_clarification():
    unsafe_reply = (
        "Здравствуйте! Вижу проблему с отправкой формы заявки на мобильных и адаптивом лендинга. "
        "Проверю текущую валидацию и обработку данных, затем внесу правки в разметку и стили. "
        "Напишите, куда должны приходить заявки после заполнения формы. "
        "После этого протестирую сценарий на телефоне и в основных браузерах. "
        "Готов приступить сразу."
    )
    mock_client = MagicMock()
    writer_choice = MagicMock()
    writer_choice.message.content = unsafe_reply
    reviewer_choice = MagicMock()
    reviewer_choice.message.content = '{"approved": true, "issues": []}'
    repair_choice = MagicMock()
    repair_choice.message.content = unsafe_reply
    mock_client.chat.completions.create.side_effect = [
        MagicMock(choices=[writer_choice]),
        MagicMock(choices=[reviewer_choice]),
        MagicMock(choices=[repair_choice]),
    ]

    with patch("openai.OpenAI", return_value=mock_client):
        reply = compose_customer_reply(_form_context(), "", api_key="sk-test")

    assert "напишите, куда" not in reply.lower()
    assert "unapproved clarification" not in reply_quality_issues(reply, _form_context())


def test_fallback_uses_title_when_task_summary_judges_customer_skill():
    context = replace(
        _form_context(),
        task_summary="Есть риск, что интеграция с CRM будет сложной для новичка.",
    )

    reply = compose_customer_reply(context, "Цена 5000 руб.")

    assert "нович" not in reply.lower()
    assert "исправить форму заявки" in reply.lower()
    assert reply_quality_issues(reply, context) == ()


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
