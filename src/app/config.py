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
    kwork_max_responses: int = 5
    kwork_max_age_hours: int = 24
    kwork_cookie: str = ""
    kwork_source: str = "web"
    kwork_projects_url: str = "https://kwork.ru/projects?c=11"
    kwork_use_browser: bool = True
    kwork_cdp_url: str = "http://127.0.0.1:9222"
    kwork_browser_profile_dir: str = ""
    kwork_auto_chrome_cookies: bool = True
    kwork_login_email: str = ""
    kwork_login_password: str = ""
    lead_min_score: int = 60
    lead_max_days: int = 7
    lead_accept_decisions: tuple[str, ...] = ("accept", "maybe")
    lead_blocked_keywords: tuple[str, ...] = ("битрикс", "bitrix")
    lead_hard_reject_keywords: tuple[str, ...] = ()
    lead_required_keywords: tuple[str, ...] = ()
    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-chat"
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_vision_model: str = ""
    openrouter_vision_mode: str = "smart"


def load_config(env_path: str | Path = ".env") -> AppConfig:
    if load_dotenv is not None:
        load_dotenv(env_path, encoding="utf-8", override=True)

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
        kwork_max_responses=_int_env("KWORK_MAX_RESPONSES", 5),
        kwork_max_age_hours=_int_env("KWORK_MAX_AGE_HOURS", 24),
        kwork_cookie=os.getenv("KWORK_COOKIE", ""),
        kwork_source=os.getenv("KWORK_SOURCE", "web"),
        kwork_projects_url=os.getenv("KWORK_PROJECTS_URL", "https://kwork.ru/projects?c=11"),
        kwork_use_browser=_bool_env("KWORK_USE_BROWSER", True),
        kwork_cdp_url=os.getenv("KWORK_CDP_URL", "http://127.0.0.1:9222"),
        kwork_browser_profile_dir=os.getenv("KWORK_BROWSER_PROFILE_DIR", ""),
        kwork_auto_chrome_cookies=_bool_env("KWORK_AUTO_CHROME_COOKIES", True),
        kwork_login_email=os.getenv("KWORK_LOGIN_EMAIL", ""),
        kwork_login_password=os.getenv("KWORK_LOGIN_PASSWORD", ""),
        lead_min_score=_int_env("LEAD_MIN_SCORE", 60),
        lead_max_days=_int_env("LEAD_MAX_DAYS", 7),
        lead_accept_decisions=_csv_env("LEAD_ACCEPT_DECISIONS", ("accept", "maybe")),
        lead_blocked_keywords=_csv_env("LEAD_BLOCKED_KEYWORDS", ("битрикс", "bitrix")),
        lead_hard_reject_keywords=_csv_env("LEAD_HARD_REJECT_KEYWORDS", ()),
        lead_required_keywords=_csv_env("LEAD_REQUIRED_KEYWORDS", ()),
        deepseek_api_key=os.getenv("DEEPSEEK_API_KEY", ""),
        deepseek_model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY", ""),
        openrouter_base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        openrouter_vision_model=os.getenv("OPENROUTER_VISION_MODEL", ""),
        openrouter_vision_mode=_vision_mode(os.getenv("OPENROUTER_VISION_MODE", "smart")),
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


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value in (None, ""):
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _channels(value: str) -> tuple[str, ...]:
    channels = tuple(item.strip() for item in value.split(",") if item.strip())
    if not channels:
        raise ValueError("TELEGRAM_CHANNELS must contain at least one channel")
    return channels


def _csv_env(name: str, default: tuple[str, ...]) -> tuple[str, ...]:
    value = os.getenv(name)
    if value in (None, ""):
        return default
    return tuple(item.strip() for item in value.split(",") if item.strip())


def _vision_mode(value: str) -> str:
    normalized = value.strip().lower()
    return normalized if normalized in {"off", "fallback", "smart"} else "smart"
