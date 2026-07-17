from app.config import load_config


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
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_BASE_URL", raising=False)
    monkeypatch.delenv("OPENROUTER_VISION_MODEL", raising=False)

    config = load_config(env_file)

    assert config.openrouter_api_key == "or-test-key"
    assert config.openrouter_base_url == "https://openrouter.example/v1"
    assert config.openrouter_vision_model == "provider/vision-model"
