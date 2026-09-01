from app.config import load_config


def test_load_config_reads_mobile_lead_hub_settings_without_mail(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "TELEGRAM_API_ID=0",
                "TELEGRAM_API_HASH=fill_later",
                "TELEGRAM_CHANNELS=@unused",
                "LEAD_HUB_URL=http://31.129.97.211",
                "LEAD_HUB_API_KEY=mobile-integration-key",
                "LEAD_HUB_OWNER_PHONE=79679812438",
            ]
        ),
        encoding="utf-8",
    )
    for name in ("LEAD_HUB_URL", "LEAD_HUB_API_KEY", "LEAD_HUB_OWNER_PHONE"):
        monkeypatch.delenv(name, raising=False)

    config = load_config(env_file)

    assert config.lead_hub_url == "http://31.129.97.211"
    assert config.lead_hub_api_key == "mobile-integration-key"
    assert config.lead_hub_owner_phone == "79679812438"


def test_load_config_blocks_unsupported_site_builders_by_default(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "TELEGRAM_API_ID=0",
                "TELEGRAM_API_HASH=fill_later",
                "TELEGRAM_CHANNELS=@unused",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.delenv("LEAD_BLOCKED_KEYWORDS", raising=False)

    config = load_config(env_file)

    assert {
        "битрикс",
        "bitrix",
        "tilda",
        "тильда",
        "elementor",
        "элементор",
        "yandex kit",
        "яндекс кит",
        "timbly",
        "тимбли",
        "webflow",
        "wix",
        "визуальный конструктор",
        "swift",
        "xcode",
    } <= set(config.lead_blocked_keywords)


def test_load_config_reads_kwork_autosend_settings(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "TELEGRAM_API_ID=0",
                "TELEGRAM_API_HASH=fill_later",
                "TELEGRAM_CHANNELS=@unused",
                "KWORK_AUTO_SEND=1",
                "KWORK_AUTO_SEND_DAILY_LIMIT=10",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.delenv("KWORK_AUTO_SEND", raising=False)
    monkeypatch.delenv("KWORK_AUTO_SEND_DAILY_LIMIT", raising=False)

    config = load_config(env_file)

    assert config.kwork_auto_send is True
    assert config.kwork_auto_send_daily_limit == 10


def test_load_config_reads_kwork_inbox_schedule(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "TELEGRAM_API_ID=0",
                "TELEGRAM_API_HASH=fill_later",
                "TELEGRAM_CHANNELS=@unused",
                "KWORK_INBOX_POLL_SECONDS=300",
                "KWORK_INBOX_NIGHT_POLL_SECONDS=14400",
                "KWORK_INBOX_NIGHT_START_HOUR=0",
                "KWORK_INBOX_NIGHT_END_HOUR=8",
            ]
        ),
        encoding="utf-8",
    )
    for name in (
        "KWORK_INBOX_POLL_SECONDS",
        "KWORK_INBOX_NIGHT_POLL_SECONDS",
        "KWORK_INBOX_NIGHT_START_HOUR",
        "KWORK_INBOX_NIGHT_END_HOUR",
    ):
        monkeypatch.delenv(name, raising=False)

    config = load_config(env_file)

    assert config.kwork_inbox_poll_seconds == 300
    assert config.kwork_inbox_night_poll_seconds == 14_400
    assert config.kwork_inbox_night_start_hour == 0
    assert config.kwork_inbox_night_end_hour == 8


def test_load_config_uses_fast_kwork_monitoring_defaults(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "TELEGRAM_API_ID=0",
                "TELEGRAM_API_HASH=fill_later",
                "TELEGRAM_CHANNELS=@unused",
            ]
        ),
        encoding="utf-8",
    )
    for name in (
        "SCAN_INTERVAL_SECONDS",
        "KWORK_MAX_PAGES",
        "KWORK_MAX_RESPONSES",
        "KWORK_MAX_AGE_HOURS",
        "OPENROUTER_VISION_MODE",
    ):
        monkeypatch.delenv(name, raising=False)

    config = load_config(env_file)

    assert config.scan_interval_seconds == 5
    assert config.kwork_max_pages == 1
    assert config.kwork_max_responses == 6
    assert config.kwork_max_age_hours == 1
    assert config.openrouter_vision_mode == "fallback"


def test_load_config_reads_optional_kwork_login_credentials(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "TELEGRAM_API_ID=0",
                "TELEGRAM_API_HASH=fill_later",
                "TELEGRAM_CHANNELS=@unused",
                "SMTP_HOST=smtp.example.com",
                "SMTP_USER=bot@example.com",
                "SMTP_PASSWORD=mail-secret",
                "MAIL_FROM=bot@example.com",
                "MAIL_TO=me@example.com",
                "IMAP_HOST=imap.example.com",
                "IMAP_USER=bot@example.com",
                "IMAP_PASSWORD=mail-secret",
                "KWORK_MAX_AGE_HOURS=12",
                "KWORK_LOGIN_EMAIL=kwork@example.com",
                "KWORK_LOGIN_PASSWORD=kwork-secret",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.delenv("KWORK_LOGIN_EMAIL", raising=False)
    monkeypatch.delenv("KWORK_LOGIN_PASSWORD", raising=False)

    config = load_config(env_file)

    assert config.kwork_login_email == "kwork@example.com"
    assert config.kwork_login_password == "kwork-secret"
    assert config.kwork_max_age_hours == 12
    assert config.lead_hard_reject_keywords == ()


def test_load_config_reads_lead_filter_settings(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "TELEGRAM_API_ID=0",
                "TELEGRAM_API_HASH=fill_later",
                "TELEGRAM_CHANNELS=@unused",
                "SMTP_HOST=smtp.example.com",
                "SMTP_USER=bot@example.com",
                "SMTP_PASSWORD=mail-secret",
                "MAIL_FROM=bot@example.com",
                "MAIL_TO=me@example.com",
                "IMAP_HOST=imap.example.com",
                "IMAP_USER=bot@example.com",
                "IMAP_PASSWORD=mail-secret",
                "LEAD_MIN_SCORE=75",
                "LEAD_MAX_DAYS=5",
                "LEAD_ACCEPT_DECISIONS=accept",
                "LEAD_BLOCKED_KEYWORDS=битрикс, shopify",
                "LEAD_HARD_REJECT_KEYWORDS=android, webgl",
                "LEAD_REQUIRED_KEYWORDS=wordpress, html",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.delenv("LEAD_MIN_SCORE", raising=False)
    monkeypatch.delenv("LEAD_MAX_DAYS", raising=False)
    monkeypatch.delenv("LEAD_ACCEPT_DECISIONS", raising=False)
    monkeypatch.delenv("LEAD_BLOCKED_KEYWORDS", raising=False)
    monkeypatch.delenv("LEAD_HARD_REJECT_KEYWORDS", raising=False)
    monkeypatch.delenv("LEAD_REQUIRED_KEYWORDS", raising=False)

    config = load_config(env_file)

    assert config.lead_min_score == 75
    assert config.lead_max_days == 5
    assert config.lead_accept_decisions == ("accept",)
    assert config.lead_blocked_keywords == ("битрикс", "shopify")
    assert config.lead_hard_reject_keywords == ("android", "webgl")
    assert config.lead_required_keywords == ("wordpress", "html")


def test_load_config_prefers_env_file_over_existing_process_env(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "TELEGRAM_API_ID=0",
                "TELEGRAM_API_HASH=fill_later",
                "TELEGRAM_CHANNELS=@unused",
                "SMTP_HOST=smtp.example.com",
                "SMTP_USER=bot@example.com",
                "SMTP_PASSWORD=mail-secret",
                "MAIL_FROM=bot@example.com",
                "MAIL_TO=me@example.com",
                "IMAP_HOST=imap.example.com",
                "IMAP_USER=bot@example.com",
                "IMAP_PASSWORD=mail-secret",
                "LEAD_MIN_SCORE=71",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("LEAD_MIN_SCORE", "99")

    config = load_config(env_file)

    assert config.lead_min_score == 71


def test_load_config_reads_openrouter_vision_settings(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "TELEGRAM_API_ID=0",
                "TELEGRAM_API_HASH=fill_later",
                "TELEGRAM_CHANNELS=@unused",
                "SMTP_HOST=smtp.example.com",
                "SMTP_USER=bot@example.com",
                "SMTP_PASSWORD=mail-secret",
                "MAIL_FROM=bot@example.com",
                "MAIL_TO=me@example.com",
                "IMAP_HOST=imap.example.com",
                "IMAP_USER=bot@example.com",
                "IMAP_PASSWORD=mail-secret",
                "OPENROUTER_API_KEY=or-test-key",
                "OPENROUTER_BASE_URL=https://openrouter.example/v1",
                "OPENROUTER_VISION_MODEL=provider/vision-model",
                "OPENROUTER_VISION_MODE=smart",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_BASE_URL", raising=False)
    monkeypatch.delenv("OPENROUTER_VISION_MODEL", raising=False)
    monkeypatch.delenv("OPENROUTER_VISION_MODE", raising=False)

    config = load_config(env_file)

    assert config.openrouter_api_key == "or-test-key"
    assert config.openrouter_base_url == "https://openrouter.example/v1"
    assert config.openrouter_vision_model == "provider/vision-model"
    assert config.openrouter_vision_mode == "smart"


def test_load_config_reads_openrouter_text_models(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "TELEGRAM_API_ID=0",
                "TELEGRAM_API_HASH=fill_later",
                "TELEGRAM_CHANNELS=@unused",
                "OPENROUTER_API_KEY=or-test-key",
                "OPENROUTER_ANALYSIS_MODEL=openai/gpt-5.1",
                "OPENROUTER_REPLY_MODEL=anthropic/claude-sonnet-4.5",
                "OPENROUTER_FALLBACK_MODELS=openai/gpt-4.1, google/gemini-3.1-pro-preview",
            ]
        ),
        encoding="utf-8",
    )
    for name in (
        "OPENROUTER_API_KEY",
        "OPENROUTER_ANALYSIS_MODEL",
        "OPENROUTER_REPLY_MODEL",
        "OPENROUTER_FALLBACK_MODELS",
    ):
        monkeypatch.delenv(name, raising=False)

    config = load_config(env_file)

    assert config.openrouter_analysis_model == "openai/gpt-5.1"
    assert config.openrouter_reply_model == "anthropic/claude-sonnet-4.5"
    assert config.openrouter_fallback_models == (
        "openai/gpt-4.1",
        "google/gemini-3.1-pro-preview",
    )
