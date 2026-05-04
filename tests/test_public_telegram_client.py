from app.public_telegram_client import parse_public_channel_posts


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
