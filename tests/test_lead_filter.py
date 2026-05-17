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


def test_rejects_react_and_site_builders():
    result = evaluate_post(
        "Ищу разработчика React для доработки сайта на Tilda/Webflow. "
        "Контакт @builder_owner"
    )

    assert result.accepted is False
    assert "React" in result.reasons
    assert "конструктор" in result.reasons


def test_rejects_full_time_vacancies():
    result = evaluate_post(
        "Вакансия WordPress разработчик, зарплата 150 000 руб/мес, "
        "ищем в команду. Контакт @hr_manager"
    )

    assert result.accepted is False
    assert "вакансия" in result.reasons


def test_rejects_non_target_stack():
    result = evaluate_post(
        "Доработка интернет-магазина на ASP.NET, простые задачки. "
        "Отклик: https://example.com/order"
    )

    assert result.accepted is False
    assert "нецелевой stack" in result.reasons


def test_rejects_without_contact_or_reply_path():
    result = evaluate_post("Нужно поправить верстку лендинга за день, деталей мало")

    assert result.accepted is False
    assert "нет контакта" in result.reasons


def test_rejects_non_web_posts_even_with_contact():
    result = evaluate_post("Ищем модератора заявок, писать @client_dev")

    assert result.accepted is False
    assert "нет подходящего web-stack" in result.reasons


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

    assert result.accepted is False
    assert "нет подходящего web-stack" in result.reasons


def test_generates_contextual_customer_reply_from_order_text():
    result = evaluate_post(
        "Нужно сверстать лендинг HTML/CSS/JS, поправить адаптив и форму. "
        "Срок 1 день. Бюджет 5000 руб. Пишите @client_dev"
    )

    assert "сверстать лендинг" in result.draft_reply
    assert "настроить форму" in result.draft_reply
    assert "Срок 1 день" in result.draft_reply
    assert "Бюджет 5000 руб" in result.draft_reply
