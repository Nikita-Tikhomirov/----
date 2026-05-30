import pytest

from app.kwork_sender import (
    KworkReplySender,
    _extract_reply_terms,
    _login_required_message,
)


def test_extract_reply_terms_reads_price_and_days_from_human_reply():
    terms = _extract_reply_terms(
        "Здравствуйте! Сделаю за 4 дня. По цене ориентир 18 000 руб., начну сегодня."
    )

    assert terms.price_rub == 18000
    assert terms.days == 4


def test_extract_reply_terms_ignores_phone_like_numbers():
    terms = _extract_reply_terms(
        "Здравствуйте! Мой контакт +7 967 981 2438. Сделаю за 2 дня, цена 5000 руб."
    )

    assert terms.price_rub == 5000
    assert terms.days == 2


def test_login_required_message_detects_logged_out_kwork_page():
    page_text = "ФРИЛАНС МАРКЕТПЛЕЙС\nВход\nРегистрация\nПредложить услугу"

    assert _login_required_message(page_text, has_reply_field=False)


def test_login_required_message_allows_page_with_reply_field():
    page_text = "Вход\nРегистрация\nПредложить услугу"

    assert _login_required_message(page_text, has_reply_field=True) == ""


def test_kwork_reply_sender_rejects_non_kwork_project_url():
    sender = KworkReplySender()

    with pytest.raises(ValueError, match="Kwork project URL"):
        sender.send_message("https://example.com/project/1", "Здравствуйте!")
