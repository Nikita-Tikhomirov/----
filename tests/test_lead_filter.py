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


def test_rejects_without_contact_or_reply_path():
    result = evaluate_post("Нужно поправить верстку лендинга за день, деталей мало")

    assert result.accepted is False
    assert "нет контакта" in result.reasons


def test_accepts_public_order_link_as_reply_path():
    result = evaluate_post(
        "Подборка заказов по тегу #wordpress: исправление ошибок на сайте "
        "за 1 200 руб. https://u.habr.com/example"
    )

    assert result.accepted is True
    assert result.contact == "https://u.habr.com/example"
