from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional during tests
    load_dotenv = None


@dataclass(frozen=True)
class AppConfig:
    telegram_api_id: int
    telegram_api_hash: str
    telegram_session_name: str
    telegram_channels: tuple[str, ...]
    telegram_proxy: str
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    mail_from: str
    mail_to: str
    imap_host: str
    imap_port: int
    imap_user: str
    imap_password: str
    database_path: Path
    scan_interval_seconds: int = 300
    max_posts_per_channel: int = 20
    max_sends_per_run: int = 5
    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-chat"


def load_config(env_path: str | Path = ".env") -> AppConfig:
    if load_dotenv is not None:
        load_dotenv(env_path, encoding="utf-8")

    return AppConfig(
        telegram_api_id=_required_int("TELEGRAM_API_ID"),
        telegram_api_hash=_required("TELEGRAM_API_HASH"),
        telegram_session_name=os.getenv("TELEGRAM_SESSION_NAME", "lead_funnel"),
        telegram_channels=_channels(os.getenv("TELEGRAM_CHANNELS", "")),
        telegram_proxy=os.getenv("TELEGRAM_PROXY", ""),
        smtp_host=_required("SMTP_HOST"),
        smtp_port=_int_env("SMTP_PORT", 587),
        smtp_user=_required("SMTP_USER"),
        smtp_password=_required("SMTP_PASSWORD"),
        mail_from=_required("MAIL_FROM"),
        mail_to=_required("MAIL_TO"),
        imap_host=_required("IMAP_HOST"),
        imap_port=_int_env("IMAP_PORT", 993),
        imap_user=_required("IMAP_USER"),
        imap_password=_required("IMAP_PASSWORD"),
        database_path=Path(os.getenv("DATABASE_PATH", "data/leads.sqlite3")),
        scan_interval_seconds=_int_env("SCAN_INTERVAL_SECONDS", 300),
        max_posts_per_channel=_int_env("MAX_POSTS_PER_CHANNEL", 20),
        max_sends_per_run=_int_env("MAX_SENDS_PER_RUN", 5),
        deepseek_api_key=os.getenv("DEEPSEEK_API_KEY", ""),
        deepseek_model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
    )


def _required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def _required_int(name: str) -> int:
    return int(_required(name))


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    return default if value in (None, "") else int(value)


def _channels(value: str) -> tuple[str, ...]:
    channels = tuple(item.strip() for item in value.split(",") if item.strip())
    if not channels:
        raise ValueError("TELEGRAM_CHANNELS must contain at least one channel")
    return channels
