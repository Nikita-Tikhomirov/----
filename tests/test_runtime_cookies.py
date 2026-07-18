from app.config import AppConfig
from app.main import _resolve_kwork_cookie


def _config(cookie: str = "", auto: bool = True) -> AppConfig:
    return AppConfig(
        telegram_api_id=0,
        telegram_api_hash="fill_later",
        telegram_session_name="lead_funnel",
        telegram_channels=("@freelance_dev_work",),
        telegram_proxy="",
        database_path="data/test.sqlite3",
        kwork_cookie=cookie,
        kwork_auto_chrome_cookies=auto,
    )


def test_resolve_kwork_cookie_keeps_manual_cookie(monkeypatch):
    monkeypatch.setattr("app.main.chrome_cookie_header", lambda domain=".kwork.ru": "from=chrome")

    assert _resolve_kwork_cookie(_config(cookie="manual=1")) == "manual=1"


def test_resolve_kwork_cookie_imports_chrome_cookie_when_enabled(monkeypatch):
    monkeypatch.setattr("app.main.chrome_cookie_header", lambda domain=".kwork.ru": "from=chrome")

    assert _resolve_kwork_cookie(_config()) == "from=chrome"


def test_resolve_kwork_cookie_can_disable_import(monkeypatch):
    monkeypatch.setattr("app.main.chrome_cookie_header", lambda domain=".kwork.ru": "from=chrome")

    assert _resolve_kwork_cookie(_config(auto=False)) == ""
