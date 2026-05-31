import pytest

from app.kwork_sender import (
    KworkReplySender,
    _AUTO_LOGIN_SCRIPT,
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


def test_kwork_reply_sender_keeps_autologin_credentials_in_memory_only():
    sender = KworkReplySender(login_email="me@example.com", login_password="secret")

    assert sender.login_email == "me@example.com"
    assert sender.login_password == "secret"


def test_auto_login_script_targets_email_password_and_submit_controls():
    assert "input[type=email]" in _AUTO_LOGIN_SCRIPT
    assert "input[type=password]" in _AUTO_LOGIN_SCRIPT
    assert "submit.click()" in _AUTO_LOGIN_SCRIPT


def test_reply_form_opener_supports_kwork_span_buttons():
    from app.kwork_sender import _FILL_AND_SUBMIT_SCRIPT, _HAS_REPLY_FIELD_SCRIPT, _OPEN_REPLY_FORM_SCRIPT

    assert ".kw-button" in _OPEN_REPLY_FORM_SCRIPT
    assert ".trumbowyg-editor" in _HAS_REPLY_FIELD_SCRIPT
    assert ".trumbowyg-editor" in _FILL_AND_SUBMIT_SCRIPT
    assert "#offer-custom-price" in _FILL_AND_SUBMIT_SCRIPT
    assert "input[type=tel]" in _FILL_AND_SUBMIT_SCRIPT
    assert "input[type=search]" in _FILL_AND_SUBMIT_SCRIPT


def test_kwork_reply_sender_rejects_non_kwork_project_url():
    sender = KworkReplySender()

    with pytest.raises(ValueError, match="Kwork project URL"):
        sender.send_message("https://example.com/project/1", "Здравствуйте!")
