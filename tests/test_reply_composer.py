import re
from dataclasses import replace
from unittest.mock import patch

from app.llm_client import OpenRouterResult
from app.reply_composer import (
    ReplyDraftContext,
    _redacted_facts,
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
        customer_goal="Получать заявки с мобильной версии лендинга без потерь",
        work_plan=(
            "Проверить валидацию и обработчик отправки формы",
            "Исправить логику формы и адаптив блока",
            "Протестировать отправку на мобильном и в основных браузерах",
        ),
        risks=("В ТЗ не указан конечный получатель заявки",),
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


def test_composer_redacts_budget_before_calling_openrouter_and_keeps_good_reply():
    good_reply = (
        "Здравствуйте! По задаче вижу, что форма заявки на лендинге не отправляется на мобильных. "
        "Проверю текущую валидацию и обработку отправки, затем внесу правки и приведу блок к адаптивному виду. "
        "После этого протестирую сценарий на телефоне и в основных браузерах, чтобы заявки доходили стабильно. "
        "На работу ориентируюсь на 2 дня и могу приступить сразу."
    )
    with patch(
        "app.reply_composer.openrouter_chat",
        side_effect=[
            OpenRouterResult(content=good_reply, model="anthropic/claude-sonnet-4.5"),
            OpenRouterResult(
                content='{"approved": true, "issues": []}',
                model="anthropic/claude-sonnet-4.5",
            ),
        ],
    ) as gateway:
        reply = compose_customer_reply(
            _form_context(),
            "",
            api_key="sk-test",
            model="anthropic/claude-sonnet-4.5",
            base_url="https://openrouter.example/v1",
            fallback_models=("openai/gpt-4.1",),
        )

    writer_prompt = gateway.call_args_list[0].kwargs["messages"][1]["content"].lower()
    assert "5000" not in writer_prompt
    assert "бюджет" not in writer_prompt
    assert "руб" not in writer_prompt
    assert reply == good_reply
    assert gateway.call_args_list[0].kwargs["primary_model"] == "anthropic/claude-sonnet-4.5"
    assert gateway.call_args_list[0].kwargs["fallback_models"] == ("openai/gpt-4.1",)
    assert gateway.call_args_list[0].kwargs["base_url"] == "https://openrouter.example/v1"


def test_composer_repairs_reply_rejected_by_ai_reviewer():
    repaired_reply = (
        "Здравствуйте! Вижу задачу по исправлению отправки формы заявки и адаптива лендинга. "
        "Сначала проверю текущую валидацию и обработку формы, затем внесу правки в разметку и стили для мобильных. "
        "После изменений протестирую отправку в основных браузерах и покажу готовый работающий сценарий. "
        "На работу потребуется до 2 дней, могу приступить сразу."
    )
    with patch(
        "app.reply_composer.openrouter_chat",
        side_effect=[
            OpenRouterResult(
                content="Здравствуйте! Готов помочь, обсудим детали.",
                model="anthropic/claude-sonnet-4.5",
            ),
            OpenRouterResult(
                content='{"approved": false, "issues": ["нет конкретных действий"]}',
                model="anthropic/claude-sonnet-4.5",
            ),
            OpenRouterResult(content=repaired_reply, model="anthropic/claude-sonnet-4.5"),
        ],
    ) as gateway:
        reply = compose_customer_reply(_form_context(), "", api_key="sk-test")

    assert reply == repaired_reply
    assert gateway.call_count == 3


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


def test_quality_gate_rejects_unmentioned_technical_components():
    issues = reply_quality_issues(
        (
            "Здравствуйте! Вижу задачу по исправлению формы заявки и адаптиву лендинга. "
            "Проверю логику отправки, настройки SMTP или плагина почты, затем внесу нужные правки. "
            "После этого протестирую форму на телефоне и в основных браузерах. "
            "Готов приступить сразу."
        ),
        _form_context(),
    )

    assert "unsupported technical detail" in issues


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


def test_writer_prompt_uses_customer_goal_and_fact_grounded_plan():
    prompt = _writer_prompt(_form_context()).lower()

    assert "цель клиента: получать заявки" in prompt
    assert "проверить валидацию и обработчик" in prompt
    assert "исправить логику формы" in prompt
    assert "риски: в тз не указан" in prompt


def test_composer_falls_back_when_provider_keeps_prohibited_clarification():
    unsafe_reply = (
        "Здравствуйте! Вижу проблему с отправкой формы заявки на мобильных и адаптивом лендинга. "
        "Проверю текущую валидацию и обработку данных, затем внесу правки в разметку и стили. "
        "Напишите, куда должны приходить заявки после заполнения формы. "
        "После этого протестирую сценарий на телефоне и в основных браузерах. "
        "Готов приступить сразу."
    )
    with patch(
        "app.reply_composer.openrouter_chat",
        side_effect=[
            OpenRouterResult(content=unsafe_reply, model="anthropic/claude-sonnet-4.5"),
            OpenRouterResult(
                content='{"approved": true, "issues": []}',
                model="anthropic/claude-sonnet-4.5",
            ),
            OpenRouterResult(content=unsafe_reply, model="anthropic/claude-sonnet-4.5"),
        ],
    ):
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


def test_fallback_does_not_treat_information_page_as_form_task():
    context = ReplyDraftContext(
        title="Настройка сайта и каталога на WordPress",
        task_summary="Посадить информационную страницу и каталог по PSD на WordPress",
        source_text=(
            "Нужно сверстать информационную страницу и каталог по PSD, затем посадить сайт на WordPress. "
            "Для каталога нужны карточки товаров и подключение платежного канала."
        ),
        attachment_context="Макеты PSD приложены к заказу.",
        estimated_days=5,
    )

    reply = compose_customer_reply(context, "Цена 5000 руб.")

    lowered = reply.lower()
    assert "текущую отправку формы" not in lowered
    assert "валидацию на мобильных" not in lowered
    assert "wordpress" in lowered
    assert reply_quality_issues(reply, context) == ()


def test_wordpress_catalog_payment_fallback_uses_explicit_order_scope():
    context = ReplyDraftContext(
        title="Посадка сайта на WordPress",
        task_summary="Посадить сайт на WordPress с каталогом товаров и оплатой",
        source_text=(
            "Нужна посадка сайта на WordPress. Каталог товаров и подключение оплаты через сайт. "
            "Возможны варианты реализации."
        ),
        attachment_context="",
        estimated_days=5,
    )

    reply = compose_customer_reply(context, "Цена 500 руб.")

    lowered = reply.lower()
    assert "каталог" in lowered
    assert "оплат" in lowered
    assert "импорт" not in lowered
    assert "фильтр" not in lowered
    assert reply_quality_issues(reply, context) == ()


def test_catalog_selection_fallback_names_the_customer_flow_from_order_facts():
    context = ReplyDraftContext(
        title="Разработка каталога для выбора стройматериалов",
        task_summary="Каталог стройматериалов с выбором позиций",
        source_text=(
            "Нужно сделать каталог с карточками материалов и чекбоксами. "
            "Посетитель выбирает позиции, формирует список и отправляет данные заказчику."
        ),
        attachment_context="",
        estimated_days=5,
    )

    reply = compose_customer_reply(context, "Цена 10000 руб.")

    lowered = reply.lower()
    assert "карточки материалов" in lowered
    assert "сформировать нужный список" in lowered
    assert "передачу сформированного списка" in lowered
    assert reply_quality_issues(reply, context) == ()


def test_writer_prompt_distinguishes_payment_feature_from_payment_terms():
    prompt = _writer_prompt(
        ReplyDraftContext(
            title="Посадка сайта на WordPress",
            task_summary="Посадить сайт на WordPress с каталогом товаров и оплатой",
            source_text="Нужны каталог товаров и подключение оплаты через сайт.",
            attachment_context="",
            estimated_days=5,
        )
    ).lower()

    assert "условия оплаты" in prompt
    assert "техническую оплату" in prompt


def test_payment_feature_is_not_treated_as_a_commercial_term():
    context = ReplyDraftContext(
        title="Посадка сайта на WordPress",
        task_summary="Посадить сайт на WordPress с каталогом товаров и оплатой",
        source_text="Нужны каталог товаров и подключение оплаты через сайт.",
        attachment_context="",
        estimated_days=5,
    )
    reply = (
        "Здравствуйте! Посмотрел задачу по WordPress-сайту с каталогом товаров. "
        "Сверю структуру страниц, затем соберу нужные разделы и карточки каталога. "
        "Проверю сценарий оформления и оплаты, чтобы пользователь мог пройти путь до заказа. "
        "После этого покажу рабочий результат и смогу приступить сразу."
    )

    assert "commercial term" not in reply_quality_issues(reply, context)


def test_payment_terms_are_still_treated_as_commercial():
    context = ReplyDraftContext(
        title="Посадка сайта на WordPress",
        task_summary="Посадить сайт на WordPress с каталогом товаров и оплатой",
        source_text="Нужны каталог товаров и подключение оплаты через сайт.",
        attachment_context="",
        estimated_days=5,
    )
    reply = (
        "Здравствуйте! Посмотрел задачу по WordPress-сайту с каталогом товаров. "
        "Сверю структуру страниц, затем соберу нужные разделы и карточки каталога. "
        "Проверю сценарий оформления и оплаты, чтобы пользователь мог пройти путь до заказа. "
        "Оплата после сдачи, после этого покажу рабочий результат."
    )

    assert "commercial term" in reply_quality_issues(reply, context)


def test_redacted_facts_keep_technical_payment_scope_and_remove_budget():
    context = ReplyDraftContext(
        title="Посадка сайта на WordPress",
        task_summary="Посадить сайт на WordPress с каталогом товаров и оплатой",
        source_text=(
            "Нужны каталог товаров и подключение оплаты через сайт. "
            "Бюджет до 5000 руб."
        ),
        attachment_context="",
        estimated_days=5,
    )

    facts = _redacted_facts(context).lower()

    assert "подключение оплаты" in facts
    assert "5000" not in facts
    assert "бюджет" not in facts


def test_quality_gate_rejects_form_action_without_form_facts():
    context = ReplyDraftContext(
        title="Настройка сайта и каталога на WordPress",
        task_summary="Посадить информационную страницу и каталог по PSD на WordPress",
        source_text="Нужно сверстать информационную страницу и каталог по PSD, затем посадить сайт на WordPress.",
        attachment_context="Макеты PSD приложены к заказу.",
        estimated_days=5,
    )
    reply = (
        "Здравствуйте! Посмотрел задачу по посадке сайта и каталога на WordPress. "
        "Сначала проверю текущую отправку формы и валидацию на мобильных, затем внесу нужные правки в разметку и стили. "
        "После изменений протестирую сценарий на телефоне и в основных браузерах, чтобы заявки стабильно доходили. "
        "На работу ориентируюсь на 5 дн., могу приступить сразу."
    )

    issues = reply_quality_issues(reply, context)

    assert "unsupported task action" in issues


def test_quality_gate_rejects_generic_discussion_closing():
    reply = (
        "Здравствуйте! Посмотрел задачу по исправлению отправки формы заявки и адаптиву лендинга. "
        "Проверю обработку данных и валидацию, затем внесу нужные правки в разметку и логику. "
        "После этого протестирую отправку заявки на мобильных и в основных браузерах. "
        "Если вас устраивает такой подход, готов обсудить детали."
    )

    assert "generic phrase" in reply_quality_issues(reply, _form_context())


def test_quality_gate_rejects_catalog_filters_and_product_filling_without_facts():
    context = ReplyDraftContext(
        title="Посадка сайта на WordPress",
        task_summary="Посадить информационную страницу и каталог по PSD на WordPress",
        source_text="Нужно сверстать информационную страницу и каталог по PSD, затем посадить сайт на WordPress.",
        attachment_context="Макеты PSD приложены к заказу.",
        estimated_days=5,
    )
    reply = (
        "Здравствуйте! Посмотрел задачу по посадке сайта и каталога на WordPress. "
        "Сверю структуру страниц, затем соберу разделы каталога, добавлю товары и настрою фильтры. "
        "После этого проверю карточки и основной пользовательский сценарий на сайте. "
        "На работу ориентируюсь на 5 дней, могу приступить сразу."
    )

    assert "unsupported task action" in reply_quality_issues(reply, context)


def test_quality_gate_rejects_unmentioned_wordpress_theme_plugins_and_categories():
    context = ReplyDraftContext(
        title="Посадка сайта на WordPress",
        task_summary="Посадить информационную страницу и каталог по PSD на WordPress",
        source_text="Нужно сверстать информационную страницу и каталог по PSD, затем посадить сайт на WordPress.",
        attachment_context="Макеты PSD приложены к заказу.",
        estimated_days=5,
    )
    reply = (
        "Здравствуйте! Я сделаю для вас сайт на WordPress с каталогом товаров. "
        "В работе установлю и настрою тему, создам структуру каталога с категориями и карточками товаров, добавлю базовые плагины. "
        "После завершения проверю корректность отображения на всех устройствах и работоспособность всех ссылок. "
        "Результат — готовый к наполнению сайт, который вы сможете сразу использовать."
    )

    assert "unsupported task action" in reply_quality_issues(reply, context)


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


def test_quality_gate_rejects_robotic_intro_and_unfounded_guarantee():
    reply = (
        "Привет. Понял задачу: нужно, чтобы форма на лендинге гарантированно передавала заявки в CRM. "
        "Сделаю следующее: проверю обработку данных, исправлю отправку и настрою нужную связку. "
        "Затем проверю адаптив формы и основной пользовательский сценарий на мобильных. "
        "На всё уйдёт до двух дней, готов приступить сразу."
    )

    issues = reply_quality_issues(reply, _form_context())

    assert "robotic phrasing" in issues
    assert "unfounded guarantee" in issues


def test_quality_gate_rejects_absolute_device_coverage_promise():
    reply = (
        "Здравствуйте! Проверю обработчик формы и воспроизведу ошибку отправки на мобильном. "
        "Исправлю причину сбоя и протестирую форму на основных разрешениях. "
        "После этого форма будет стабильно отправлять заявки с любых устройств."
    )

    assert "unfounded guarantee" in reply_quality_issues(reply, _form_context())


def test_writer_prompt_requires_a_human_specific_opening():
    prompt = _writer_prompt(_form_context()).lower()

    assert "начни с «здравствуйте!»" in prompt
    assert "не используй фразы «понял задачу»" in prompt


def test_quality_gate_rejects_plain_hi_opening_without_other_robotic_markers():
    reply = (
        "Привет. По форме заявки на лендинге нужно восстановить корректную отправку и адаптив. "
        "Проверю обработку данных и логику формы, затем внесу нужные правки. "
        "После этого протестирую отправку заявки и отображение на мобильных. "
        "Могу приступить сразу."
    )

    assert "robotic phrasing" in reply_quality_issues(reply, _form_context())
