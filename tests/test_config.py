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
