from app.public_telegram_client import PublicTelegramClient, parse_public_channel_posts


def test_parse_public_channel_posts_extracts_text_and_url():
    html = """
    <div class="tgme_widget_message_wrap">
      <div class="tgme_widget_message" data-post="jobs/42">
        <a class="tgme_widget_message_date" href="https://t.me/jobs/42">
          <time datetime="2026-05-04T10:00:00+00:00"></time>
        </a>
        <div class="tgme_widget_message_text js-message_text">
          Нужно сверстать <b>лендинг</b><br/>HTML/CSS/JS. Контакт @client_dev
        </div>
      </div>
    </div>
    """

    posts = parse_public_channel_posts("jobs", html)

    assert len(posts) == 1
    assert posts[0].channel == "jobs"
    assert posts[0].message_id == 42
    assert posts[0].url == "https://t.me/jobs/42"
    assert "Нужно сверстать лендинг" in posts[0].text
    assert "HTML/CSS/JS" in posts[0].text
    assert posts[0].posted_at == "2026-05-04T10:00:00+00:00"


def test_parse_public_channel_posts_adds_inline_reply_button():
    html = """
    <div class="tgme_widget_message_wrap">
      <div class="tgme_widget_message" data-post="jobs/43">
        <div class="tgme_widget_message_text js-message_text">
          Доработка WordPress сайта
        </div>
        <a class="tgme_widget_message_inline_button url_button"
           href="https://kwork.ru/projects/123">
          <span class="tgme_widget_message_inline_button_text">Связаться с заказчиком</span>
        </a>
      </div>
    </div>
    """

    posts = parse_public_channel_posts("jobs", html)

    assert "Отклик: https://kwork.ru/projects/123" in posts[0].text


def test_public_client_limits_posts_per_channel(monkeypatch):
    html_by_channel = {
        "first": "".join(
            f'<div class="tgme_widget_message" data-post="first/{index}">'
            f'<div class="tgme_widget_message_text js-message_text">WordPress {index} @client_dev</div>'
            "</div>"
            for index in range(1, 4)
        ),
        "second": "".join(
            f'<div class="tgme_widget_message" data-post="second/{index}">'
            f'<div class="tgme_widget_message_text js-message_text">HTML {index} @client_dev</div>'
            "</div>"
            for index in range(10, 13)
        ),
    }

    monkeypatch.setattr(
        "app.public_telegram_client._fetch_channel_html",
        lambda channel: html_by_channel[channel],
    )

    posts = PublicTelegramClient(("first", "second"), max_posts_per_channel=2).fetch_recent_posts()

    assert [(post.channel, post.message_id) for post in posts] == [
        ("first", 1),
        ("first", 2),
        ("second", 10),
        ("second", 11),
    ]
