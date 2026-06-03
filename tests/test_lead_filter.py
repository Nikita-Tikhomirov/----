from app.lead_filter import evaluate_post


def test_accepts_simple_html_css_js_wordpress_task():
    result = evaluate_post(
        "Нужно сверстать лендинг HTML/CSS/JS, поправить адаптив и форму. "
        "Срок 1-2 дня. Пишите @client_dev"
    )

    assert result.accepted is True
    assert result.score >= 70
    assert "HTML/CSS/JS" in result.summary
    assert result.contact == "@client_dev"


def test_accepts_react_and_site_builders_except_bitrix():
    result = evaluate_post(
        "Ищу разработчика React для доработки сайта на Tilda/Webflow. "
        "Контакт @builder_owner"
    )

    assert result.accepted is True
    assert result.contact == "@builder_owner"


def test_accepts_full_time_vacancies_from_kwork_feed():
    result = evaluate_post(
        "Вакансия WordPress разработчик, зарплата 150 000 руб/мес, "
        "ищем в команду. Контакт @hr_manager"
    )

    assert result.accepted is True
    assert result.contact == "@hr_manager"


def test_accepts_non_target_stack_from_kwork_feed():
    result = evaluate_post(
        "Доработка интернет-магазина на ASP.NET, простые задачки. "
        "Отклик: https://example.com/order"
    )

    assert result.accepted is True
    assert result.contact == "https://example.com/order"


def test_rejects_bitrix_orders():
    result = evaluate_post(
        "Полная синхронизация Wildberries c Битрикс 24. "
        "Отклик: https://example.com/order"
    )

    assert result.accepted is False
    assert "Bitrix" in result.reasons


def test_rejects_custom_blocked_keywords():
    result = evaluate_post(
        "Нужно настроить Shopify магазин. Отклик: https://example.com/order",
        blocked_keywords=("shopify",),
    )

    assert result.accepted is False
    assert "shopify" in result.reasons


def test_required_keywords_can_restrict_feed():
    result = evaluate_post(
        "Нужно написать текст для сайта. Отклик: https://example.com/order",
        required_keywords=("wordpress", "html"),
    )

    assert result.accepted is False
    assert "нет обязательных слов" in result.reasons


def test_rejects_without_contact_or_reply_path():
    result = evaluate_post("Нужно поправить верстку лендинга за день, деталей мало")

    assert result.accepted is False
    assert "нет контакта" in result.reasons


def test_accepts_kwork_development_feed_posts_even_without_stack_signal():
    result = evaluate_post("Ищем модератора заявок, писать @client_dev")

    assert result.accepted is True
    assert result.contact == "@client_dev"


def test_accepts_public_order_link_as_reply_path():
    result = evaluate_post(
        "Подборка заказов по тегу #wordpress: исправление ошибок на сайте "
        "за 1 200 руб. Отклик: https://example.com/order"
    )

    assert result.accepted is True
    assert result.contact == "https://example.com/order"


def test_does_not_treat_html_url_suffix_as_stack_signal():
    result = evaluate_post(
        "Дизайн упаковки и этикетки, нужна форма банки. "
        "Отклик: https://freelancehunt.com/project/design.html"
    )

    assert result.accepted is True
    assert result.contact == "https://freelancehunt.com/project/design.html"


def test_generates_contextual_customer_reply_from_order_text():
    result = evaluate_post(
        "Нужно сверстать лендинг HTML/CSS/JS, поправить адаптив и форму. "
        "Срок 1 день. Бюджет 5000 руб. Пишите @client_dev"
    )

    assert "сверстать лендинг" in result.draft_reply
    assert "настроить форму" in result.draft_reply
    assert "Срок 1 день" in result.draft_reply
    assert "Бюджет 5000 руб" in result.draft_reply


def test_fallback_reply_does_not_ask_for_clarifications():
    result = evaluate_post(
        "Нужно подключить оплату на сайте. Бюджет 5000 руб. "
        "Отклик: https://kwork.ru/projects/123"
    )

    reply = result.draft_reply.lower()
    assert "?" not in result.draft_reply
    assert "уточ" not in reply
    assert "пришл" not in reply
    assert "доступ" not in reply
