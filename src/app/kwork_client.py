from __future__ import annotations

import html
import json
import logging
import re
import ssl
import time
import urllib.request
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
from urllib.request import Request

from app.kwork_status import UNAVAILABLE_PROJECT_REASON, unavailable_project_message

logger = logging.getLogger(__name__)

TAG_PATTERN = re.compile(r"<[^>]+>")
OFFER_COUNT_PATTERN = re.compile(r"\bПредложений\s*:\s*(\d+)\b", re.IGNORECASE)
TITLE_PATTERN = re.compile(r"<title>(?P<title>[\s\S]*?)</title>", re.IGNORECASE)
DESCRIPTION_PATTERN = re.compile(
    r'<meta\s+name=["\']description["\']\s+content=["\'](?P<description>[\s\S]*?)["\']',
    re.IGNORECASE,
)
ATTACHMENT_LINK_PATTERN = re.compile(
    r'<a[^>]+href=["\'](?P<href>[^"\']*(?:/files/|download|attachment|upload)[^"\']*)["\'][^>]*>'
    r"(?P<label>[\s\S]*?)</a>",
    re.IGNORECASE,
)
FILE_EXT_PATTERN = re.compile(r"\.(?:pdf|docx?|xlsx?|txt|zip|rar|7z|png|jpe?g|webp)\b", re.IGNORECASE)


@dataclass(frozen=True)
class KworkProjectInfo:
    url: str
    response_count: int | None
    title: str
    description: str
    page_text: str = ""
    attachments: tuple[str, ...] = ()
    facts: tuple[str, ...] = ()
    reason: str = ""

    @property
    def has_response_count(self) -> bool:
        return self.response_count is not None

    @property
    def is_unavailable(self) -> bool:
        return self.reason == UNAVAILABLE_PROJECT_REASON


class KworkProjectReplyabilityError(RuntimeError):
    """Raised when the current Kwork project is unsafe to reply to."""


def ensure_project_is_replyable(
    info: KworkProjectInfo,
    max_responses: int,
) -> KworkProjectInfo:
    """Return a verified project or explain why a reply must not be sent."""
    if info.is_unavailable:
        raise KworkProjectReplyabilityError(info.reason or UNAVAILABLE_PROJECT_REASON)
    if not info.has_response_count:
        reason = f" ({info.reason})" if info.reason else ""
        raise KworkProjectReplyabilityError(f"Kwork response count is unavailable; reply was not sent{reason}")
    if info.response_count > max_responses:
        raise KworkProjectReplyabilityError(
            f"Kwork project now has {info.response_count} responses; limit is {max_responses}. Reply was not sent."
        )
    return info


class KworkProjectClient:
    def __init__(
        self,
        timeout_seconds: float = 20.0,
        cookie: str = "",
        use_browser: bool = True,
        cdp_url: str = "http://127.0.0.1:9222",
        browser_profile_dir: str = "",
        login_email: str = "",
        login_password: str = "",
    ):
        self.timeout_seconds = timeout_seconds
        self.cookie = cookie
        self.use_browser = use_browser
        self.cdp_url = cdp_url
        self.browser_profile_dir = browser_profile_dir
        self.login_email = login_email
        self.login_password = login_password
        self._browser_login_attempted = False

    def inspect(self, url: str) -> KworkProjectInfo:
        if not _is_kwork_project_url(url):
            return KworkProjectInfo(url=url, response_count=None, title="", description="", reason="это не Kwork-ссылка")
        try:
            html_text = ""
            if self.use_browser:
                html_text = self._fetch_browser_project_html(url)
            if not html_text:
                html_text = _fetch_project_html(url, self.timeout_seconds, self.cookie)
        except Exception as exc:
            logger.warning("Failed to fetch Kwork project %s: %s", url, exc)
            return KworkProjectInfo(url=url, response_count=None, title="", description="", reason=f"Kwork не открылся: {exc}")
        return parse_kwork_project_html(url, html_text)

    def _fetch_browser_project_html(self, url: str) -> str:
        try:
            return _fetch_rendered_project_html(
                url,
                timeout_seconds=self.timeout_seconds,
                cdp_url=self.cdp_url,
                browser_profile_dir=self.browser_profile_dir,
            )
        except Exception:
            if self._browser_login_attempted or not self.login_email or not self.login_password:
                raise
            self._ensure_browser_login()
            return _fetch_rendered_project_html(
                url,
                timeout_seconds=self.timeout_seconds,
                cdp_url=self.cdp_url,
                browser_profile_dir=self.browser_profile_dir,
            )

    def _ensure_browser_login(self) -> None:
        """Log into the isolated Kwork Chrome profile when its session has expired."""
        if self._browser_login_attempted:
            return
        self._browser_login_attempted = True

        from app import kwork_source

        login_url = "https://kwork.ru/login"
        kwork_source._ensure_chrome_cdp(self.cdp_url, login_url, self.browser_profile_dir)
        page = kwork_source._find_or_create_page(self.cdp_url, login_url, tab_kind="login")

        import websocket

        ws = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=self.timeout_seconds)
        try:
            kwork_source._send_cdp(ws, "Page.enable", {})
            kwork_source._send_cdp(ws, "Page.navigate", {"url": login_url})
            state = _wait_for_login_state(ws, self.timeout_seconds)
            if not state["has_login_form"]:
                return

            payload = json.dumps(
                {"email": self.login_email, "password": self.login_password},
                ensure_ascii=False,
            )
            from app.kwork_sender import _AUTO_LOGIN_SCRIPT

            result = kwork_source._evaluate(ws, f"({_AUTO_LOGIN_SCRIPT})({payload})")
            data = json.loads(result) if isinstance(result, str) else {"started": False, "reason": "no result"}
            if not data.get("started"):
                raise RuntimeError(str(data.get("reason") or "Kwork login form was not found"))
            _wait_for_authenticated_login(ws, self.timeout_seconds)
        finally:
            ws.close()


_LOGIN_STATE_SCRIPT = """
(() => JSON.stringify({
  url: location.href,
  hasLoginForm: !!(
    document.querySelector('input[type="email"], input[name*="email" i], input[name*="login" i]')
    && document.querySelector('input[type="password"], input[name*="password" i]')
  ),
  text: (document.body && document.body.innerText || '').slice(0, 6000)
}))()
"""


def _wait_for_login_state(ws, timeout_seconds: float) -> dict[str, object]:
    from app import kwork_source

    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        state = _browser_login_state(kwork_source._evaluate(ws, _LOGIN_STATE_SCRIPT))
        if bool(state["has_login_form"]) or _is_authenticated_login_state(state):
            return state
        time.sleep(0.25)
    raise RuntimeError("Kwork login page did not open")


def _wait_for_authenticated_login(ws, timeout_seconds: float) -> None:
    from app import kwork_source

    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        state = _browser_login_state(kwork_source._evaluate(ws, _LOGIN_STATE_SCRIPT))
        if _is_authenticated_login_state(state):
            return
        text = str(state["text"]).lower()
        if any(marker in text for marker in ("неверн", "неправильн", "ошибка входа")):
            raise RuntimeError("Kwork did not accept the saved login or password")
        if any(marker in text for marker in ("captcha", "капч", "смс", "код подтверждения")):
            raise RuntimeError("Kwork requires manual confirmation to finish login")
        time.sleep(0.5)
    raise RuntimeError("Kwork auto-login did not finish; captcha or manual confirmation may be required")


def _browser_login_state(raw_state: object) -> dict[str, object]:
    if not isinstance(raw_state, str):
        return {"url": "", "has_login_form": False, "text": ""}
    try:
        data = json.loads(raw_state)
    except json.JSONDecodeError:
        return {"url": "", "has_login_form": False, "text": raw_state}
    if not isinstance(data, dict):
        return {"url": "", "has_login_form": False, "text": ""}
    return {
        "url": str(data.get("url", "")),
        "has_login_form": bool(data.get("hasLoginForm")),
        "text": str(data.get("text", "")),
    }


def _is_authenticated_login_state(state: dict[str, object]) -> bool:
    parsed = urlparse(str(state["url"]))
    return parsed.netloc.lower().endswith("kwork.ru") and parsed.path.rstrip("/") != "/login" and not bool(
        state["has_login_form"]
    )


def parse_kwork_project_html(url: str, html_text: str) -> KworkProjectInfo:
    visible_text = _visible_text(html_text)
    count_match = OFFER_COUNT_PATTERN.search(visible_text)
    title = _clean_title(_first_group(TITLE_PATTERN, html_text, "title"))
    description = _clean_text(_first_group(DESCRIPTION_PATTERN, html_text, "description"))
    attachments = tuple(_extract_attachments(url, html_text))
    facts = tuple(_extract_facts(visible_text, response_count=count_match.group(1) if count_match else ""))
    page_text = _shorten(visible_text, 4000)

    if unavailable_project_message(visible_text):
        return KworkProjectInfo(
            url=url,
            response_count=None,
            title=title,
            description=description,
            page_text=page_text,
            attachments=attachments,
            facts=facts,
            reason=UNAVAILABLE_PROJECT_REASON,
        )

    if not count_match:
        return KworkProjectInfo(
            url=url,
            response_count=None,
            title=title,
            description=description,
            page_text=page_text,
            attachments=attachments,
            facts=facts,
            reason="на странице не найдено поле 'Предложений'",
        )

    return KworkProjectInfo(
        url=url,
        response_count=int(count_match.group(1)),
        title=title,
        description=description,
        page_text=page_text,
        attachments=attachments,
        facts=facts,
    )


def _is_kwork_project_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.netloc.lower().endswith("kwork.ru") and parsed.path.startswith("/projects/")


def _fetch_project_html(url: str, timeout_seconds: float, cookie: str = "") -> str:
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept-Encoding": "identity",
    }
    if cookie:
        headers["Cookie"] = cookie
    request = Request(url, headers=headers)
    opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ssl_ctx))
    with opener.open(request, timeout=timeout_seconds) as response:
        return response.read().decode("utf-8", errors="replace")


def _fetch_rendered_project_html(
    url: str,
    timeout_seconds: float,
    cdp_url: str,
    browser_profile_dir: str,
) -> str:
    from app.kwork_source import _ensure_chrome_cdp, _evaluate, _find_or_create_page, _refresh_page

    _ensure_chrome_cdp(cdp_url, url, browser_profile_dir)
    # Keep the scanner out of any unsent new_offer tab the user is reviewing.
    page = _find_or_create_page(cdp_url, url, tab_kind="inspection")

    import websocket

    ws = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=timeout_seconds)
    try:
        _refresh_page(ws, url, timeout_seconds)
        page_text = _wait_for_rendered_project_text(ws, timeout_seconds)
        if not page_text:
            return ""
        payload = _evaluate(
            ws,
            """
            JSON.stringify({
              html: document.documentElement.outerHTML,
              text: document.body.innerText,
              links: Array.from(document.querySelectorAll('a[href]')).map(a => ({
                href: a.href,
                text: a.innerText || a.getAttribute('download') || a.href
              }))
            })
            """,
        )
        if not payload:
            return ""
        data = json.loads(payload)
        links_html = "\n".join(
            f'<a href="{html.escape(item.get("href", ""))}">{html.escape(item.get("text", ""))}</a>'
            for item in data.get("links", [])
        )
        return f"{data.get('html', '')}\n<div data-rendered-text>{html.escape(data.get('text', ''))}</div>\n{links_html}"
    finally:
        ws.close()


def _wait_for_rendered_project_text(ws, timeout_seconds: float) -> str:
    from app.kwork_source import _evaluate

    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        text = str(_evaluate(ws, "document.body && document.body.innerText") or "")
        if "Предложений" in text or unavailable_project_message(text):
            return text
        time.sleep(0.5)
    return ""


def _first_group(pattern: re.Pattern[str], text: str, group: str) -> str:
    match = pattern.search(text)
    return match.group(group) if match else ""


def _clean_title(value: str) -> str:
    value = _clean_text(value)
    return value.removesuffix(" - Kwork").strip()


def _visible_text(value: str) -> str:
    value = value.replace("<br/>", " ").replace("<br>", " ")
    return _clean_text(TAG_PATTERN.sub(" ", value))


def _clean_text(value: str) -> str:
    return " ".join(html.unescape(value).split())


def _extract_attachments(base_url: str, html_text: str) -> list[str]:
    attachments: list[str] = []
    seen: set[str] = set()
    for match in ATTACHMENT_LINK_PATTERN.finditer(html_text):
        href = html.unescape(match.group("href"))
        label = _clean_text(match.group("label")) or href.rsplit("/", 1)[-1]
        if not FILE_EXT_PATTERN.search(href) and not FILE_EXT_PATTERN.search(label):
            continue
        url = urljoin(base_url, href)
        item = f"{label}: {url}"
        if item not in seen:
            seen.add(item)
            attachments.append(item)
    return attachments[:10]


def _extract_facts(visible_text: str, response_count: str = "") -> list[str]:
    facts: list[str] = []
    patterns = [
        ("Бюджет", r"\b(?:Бюджет|Цена)\s*:\s*[^.]{0,80}?(?:₽|руб\.?|р\b)"),
        ("Осталось", r"\bОсталось\s*:\s*\d+\s*д\.?(?:\s*\d+\s*ч\.?)?"),
        ("Покупатель", r"\b(?:Покупатель|Заказчик)\s*:\s*[A-Za-zА-Яа-я0-9_.@-]{2,60}"),
        ("Наймов", r"\b(?:Наймов|Нанято|Процент найма)\s*:\s*\d{1,3}%"),
    ]
    for _, pattern in patterns:
        match = re.search(pattern, visible_text, re.IGNORECASE)
        if match:
            facts.append(_clean_text(match.group(0)))
    if response_count:
        facts.append(f"Предложений: {int(response_count)}")
    return _dedupe(facts)[:8]


def _dedupe(items: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def _shorten(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"
