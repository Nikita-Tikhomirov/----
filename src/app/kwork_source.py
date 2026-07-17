from __future__ import annotations

import html
import json
import logging
import os
import re
import ssl
import subprocess
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit
from urllib.request import Request

import websocket

from app.kwork_sender import KworkReplySender
from app.telegram_client import TelegramPost

logger = logging.getLogger(__name__)

DEFAULT_KWORK_PROJECTS_URL = "https://kwork.ru/projects?c=11"
MOSCOW_TZ = timezone(timedelta(hours=3), "MSK")
CARD_PATTERN = re.compile(
    r'<(?:div|article)[^>]*class=["\'][^"\']*\bwant-card\b[^"\']*["\'][^>]*>[\s\S]*?'
    r'(?=<(?:div|article)[^>]*class=["\'][^"\']*\bwant-card\b|$)',
    re.IGNORECASE,
)
PROJECT_LINK_PATTERN = re.compile(
    r'href=["\'](?P<href>[^"\']*/projects/(?P<id>\d+)(?:/view)?[^"\']*)["\']',
    re.IGNORECASE,
)
TITLE_LINK_PATTERN = re.compile(
    r'<a[^>]*href=["\'][^"\']*/projects/\d+(?:/view)?[^"\']*["\'][^>]*>(?P<title>[\s\S]*?)</a>',
    re.IGNORECASE,
)
OFFER_COUNT_PATTERN = re.compile(r"\bПредложений\s*:\s*(\d+)\b", re.IGNORECASE)
TAG_PATTERN = re.compile(r"<[^>]+>")


class KworkWebSource:
    def __init__(
        self,
        projects_url: str = DEFAULT_KWORK_PROJECTS_URL,
        max_posts: int = 30,
        max_responses: int = 5,
        max_age_hours: int = 24,
        cookie: str = "",
        timeout_seconds: float = 30.0,
        use_browser: bool = True,
        cdp_url: str = "http://127.0.0.1:9222",
        browser_profile_dir: str = "",
        enable_replies: bool = False,
        login_email: str = "",
        login_password: str = "",
    ):
        self.projects_url = projects_url
        self.max_posts = max_posts
        self.max_responses = max_responses
        self.max_age_hours = max(0, max_age_hours)
        self.cookie = cookie
        self.timeout_seconds = timeout_seconds
        self.use_browser = use_browser
        self.cdp_url = cdp_url.rstrip("/")
        self.browser_profile_dir = browser_profile_dir
        self.enable_replies = enable_replies
        self.login_email = login_email
        self.login_password = login_password

    @property
    def can_send_replies(self) -> bool:
        return self.enable_replies

    def fetch_recent_posts(self) -> list[TelegramPost]:
        try:
            html_text = _fetch_html(self.projects_url, self.timeout_seconds, self.cookie)
        except Exception as exc:
            logger.warning("Failed to fetch Kwork projects page %s: %s", self.projects_url, exc)
            html_text = ""
        posts = parse_kwork_project_cards(
            html_text,
            max_responses=self.max_responses,
            max_age_hours=self.max_age_hours,
            base_url=self.projects_url,
        )
        if not posts and self.use_browser:
            try:
                rendered_html = _fetch_rendered_html(
                    self.projects_url,
                    self.cdp_url,
                    self.timeout_seconds,
                    self.browser_profile_dir,
                )
                posts = parse_kwork_project_cards(
                    rendered_html,
                    max_responses=self.max_responses,
                    max_age_hours=self.max_age_hours,
                    base_url=self.projects_url,
                )
            except Exception as exc:
                logger.warning("Failed to fetch rendered Kwork projects page via Chrome: %s", exc)
        return posts[: self.max_posts]

    def send_message(
        self,
        contact: str,
        text: str,
        *,
        price_rub: int | None = None,
        days: int | None = None,
        title: str = "",
    ) -> str:
        if not self.enable_replies:
            raise RuntimeError("Kwork web source is read-only; replies are sent manually.")
        sender = KworkReplySender(
            timeout_seconds=self.timeout_seconds,
            cdp_url=self.cdp_url,
            browser_profile_dir=self.browser_profile_dir,
            login_email=self.login_email,
            login_password=self.login_password,
            max_responses=self.max_responses,
            cookie=self.cookie,
        )
        return sender.send_message(
            contact,
            text,
            price_rub=price_rub,
            days=days,
            title=title,
        )


def parse_kwork_project_cards(
    html_text: str,
    max_responses: int,
    max_age_hours: int | None = None,
    base_url: str = "https://kwork.ru/projects",
    now: datetime | None = None,
) -> list[TelegramPost]:
    posts: list[TelegramPost] = []
    seen_ids: set[int] = set()
    card_blocks = CARD_PATTERN.findall(html_text)
    for block in card_blocks:
        post = _post_from_card(block, max_responses=max_responses, base_url=base_url)
        if post is None or post.message_id in seen_ids:
            continue
        seen_ids.add(post.message_id)
        posts.append(post)
    if card_blocks:
        return posts
    return _posts_from_embedded_wants(
        html_text,
        base_url=base_url,
        max_age_hours=max_age_hours,
        now=now,
    )


def _post_from_card(block: str, max_responses: int, base_url: str) -> TelegramPost | None:
    text = _visible_text(block)
    count_match = OFFER_COUNT_PATTERN.search(text)
    if not count_match:
        return None
    response_count = int(count_match.group(1))
    if response_count > max_responses:
        return None

    link_match = PROJECT_LINK_PATTERN.search(block)
    if not link_match:
        return None
    project_id = int(link_match.group("id"))
    project_url = urljoin(base_url, link_match.group("href"))
    title = _clean_text(_first_group(TITLE_LINK_PATTERN, block, "title")) or f"Kwork project {project_id}"

    return TelegramPost(
        channel="kwork-web",
        message_id=project_id,
        url=project_url,
        text="\n".join(
            [
                f"📌 {title}",
                text,
                f"Предложений: {response_count}",
                f"Отклик: {project_url}",
            ]
        ),
        posted_at="",
    )


def _posts_from_embedded_wants(
    html_text: str,
    base_url: str,
    max_age_hours: int | None = None,
    now: datetime | None = None,
) -> list[TelegramPost]:
    """Read Kwork's hydrated list when the SPA has not rendered want-card nodes."""
    decoder = json.JSONDecoder()
    for match in re.finditer(r'"wantsListData"\s*:\s*', html_text):
        try:
            payload, _ = decoder.raw_decode(html_text, match.end())
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        items = payload.get("pagination", {}).get("data", [])
        if not isinstance(items, list):
            continue
        posts = [
            post
            for item in items
            if (post := _post_from_embedded_want(item, base_url, max_age_hours=max_age_hours, now=now)) is not None
        ]
        return sorted(posts, key=lambda post: (bool(post.posted_at), post.posted_at), reverse=True)
    return []


def _post_from_embedded_want(
    item: object,
    base_url: str,
    max_age_hours: int | None = None,
    now: datetime | None = None,
) -> TelegramPost | None:
    if not isinstance(item, dict):
        return None
    if item.get("isWantActive") is False or str(item.get("status", "active")).lower() != "active":
        return None
    try:
        project_id = int(item.get("id", 0))
    except (TypeError, ValueError):
        return None
    if project_id <= 0:
        return None
    title = _clean_text(str(item.get("name", ""))) or f"Kwork project {project_id}"
    description = _clean_text(str(item.get("description", "")))
    remaining = _clean_text(str(item.get("timeLeft", "")))
    posted_at = _clean_text(str(item.get("date_create", "")))
    if max_age_hours is not None and not _is_recent_kwork_post(posted_at, max_age_hours, now):
        return None
    project_url = urljoin(base_url, f"/projects/{project_id}/view")
    lines = [f"📌 {title}"]
    if description:
        lines.append(description)
    if remaining:
        lines.append(f"Осталось: {remaining}")
    lines.append(f"Отклик: {project_url}")
    return TelegramPost(
        channel="kwork-web",
        message_id=project_id,
        url=project_url,
        text="\n".join(lines),
        posted_at=posted_at,
    )


def _is_recent_kwork_post(posted_at: str, max_age_hours: int, now: datetime | None = None) -> bool:
    if max_age_hours <= 0:
        return True
    try:
        timestamp = datetime.fromisoformat(posted_at.replace("Z", "+00:00"))
    except ValueError:
        return False
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=MOSCOW_TZ)
    reference = now or datetime.now(MOSCOW_TZ)
    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=MOSCOW_TZ)
    age = reference.astimezone(MOSCOW_TZ) - timestamp.astimezone(MOSCOW_TZ)
    return timedelta(minutes=-5) <= age <= timedelta(hours=max_age_hours)


def _fetch_html(url: str, timeout_seconds: float, cookie: str = "") -> str:
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


def _fetch_rendered_html(url: str, cdp_url: str, timeout_seconds: float, browser_profile_dir: str = "") -> str:
    _ensure_chrome_cdp(cdp_url, url, browser_profile_dir)
    page = _find_or_create_page(cdp_url, url, tab_kind="list")

    ws = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=timeout_seconds)
    try:
        _refresh_page(ws, url, timeout_seconds)
        _wait_for_cards(ws, timeout_seconds)
        return _evaluate(ws, 'Array.from(document.querySelectorAll(".want-card")).map(x=>x.outerHTML).join("\\n")')
    finally:
        ws.close()


def _refresh_page(ws, url: str, timeout_seconds: float) -> None:
    fresh_url = _cache_busted_url(url)
    _send_cdp(ws, "Page.enable", {})
    _send_cdp(ws, "Page.navigate", {"url": fresh_url})
    _wait_for_location(ws, fresh_url, timeout_seconds)


def _wait_for_location(ws, expected_url: str, timeout_seconds: float) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_location = ""
    while time.monotonic() < deadline:
        last_location = str(_evaluate(ws, "location.href") or "")
        if _is_same_kwork_page(expected_url, last_location):
            return
        time.sleep(0.25)
    raise RuntimeError(f"Kwork page did not navigate to fresh URL; last location={last_location}")


def _cache_busted_url(url: str) -> str:
    parts = urlsplit(url)
    query = [(key, value) for key, value in parse_qsl(parts.query, keep_blank_values=True) if key != "_lf_refresh"]
    query.append(("_lf_refresh", str(int(time.time() * 1000))))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def _is_same_kwork_page(expected_url: str, actual_url: str) -> bool:
    expected = urlsplit(expected_url)
    actual = urlsplit(actual_url)
    if expected.netloc.lower() != actual.netloc.lower():
        return False
    expected_path = expected.path.rstrip("/")
    actual_path = actual.path.rstrip("/")
    if actual_path == expected_path:
        return True
    return actual_path == f"{expected_path}/view"


def _ensure_chrome_cdp(cdp_url: str, url: str, browser_profile_dir: str = "") -> None:
    if _cdp_json(cdp_url, "/json/version", timeout=2):
        return

    chrome = _chrome_path()
    if not chrome:
        raise RuntimeError("Chrome executable not found")
    user_data = browser_profile_dir or _chrome_user_data_dir()
    os.makedirs(user_data, exist_ok=True)
    args = [
        chrome,
        f"--user-data-dir={user_data}",
        f"--profile-directory={_chrome_last_profile(user_data)}",
        f"--remote-debugging-port={_cdp_port(cdp_url)}",
        "--remote-allow-origins=*",
        "--no-first-run",
        url,
    ]
    subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    deadline = time.monotonic() + 12
    while time.monotonic() < deadline:
        if _cdp_json(cdp_url, "/json/version", timeout=2):
            return
        time.sleep(0.5)
    raise RuntimeError(
        "Chrome DevTools port is not available. Close Chrome and run watch again, "
        "or start Chrome with --remote-debugging-port."
    )


def _find_or_create_page(cdp_url: str, url: str, tab_kind: str = "any") -> dict[str, str]:
    pages = _cdp_json(cdp_url, "/json/list", timeout=5) or []
    for page in pages:
        if page.get("type") == "page" and _matches_tab_kind(page.get("url", ""), tab_kind):
            if page.get("webSocketDebuggerUrl"):
                return page

    version = _cdp_json(cdp_url, "/json/version", timeout=5)
    if not version:
        raise RuntimeError("Chrome DevTools version endpoint is unavailable")

    ws = websocket.create_connection(version["webSocketDebuggerUrl"], timeout=10)
    try:
        _send_cdp(ws, "Target.createTarget", {"url": url})
    finally:
        ws.close()

    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        pages = _cdp_json(cdp_url, "/json/list", timeout=5) or []
        for page in pages:
            if page.get("type") == "page" and _matches_created_tab(page.get("url", ""), url, tab_kind):
                if page.get("webSocketDebuggerUrl"):
                    return page
        time.sleep(0.5)
    raise RuntimeError("Kwork page did not appear in Chrome DevTools targets")


def _wait_for_cards(ws, timeout_seconds: float) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_count = 0
    while time.monotonic() < deadline:
        count = _evaluate(ws, 'document.querySelectorAll(".want-card").length')
        last_count = int(count or 0)
        if last_count > 0:
            return
        time.sleep(0.75)
    raise RuntimeError(f"Kwork page rendered no project cards; last count={last_count}")


def _evaluate(ws, expression: str):
    response = _send_cdp(
        ws,
        "Runtime.evaluate",
        {"expression": expression, "returnByValue": True, "awaitPromise": True},
    )
    result = response.get("result", {}).get("result", {})
    if "exceptionDetails" in response:
        raise RuntimeError(str(response["exceptionDetails"]))
    return result.get("value")


def _send_cdp(ws, method: str, params: dict) -> dict:
    _send_cdp.counter += 1
    request_id = _send_cdp.counter
    ws.send(json.dumps({"id": request_id, "method": method, "params": params}))
    while True:
        message = json.loads(ws.recv())
        if message.get("id") == request_id:
            return message


_send_cdp.counter = 0


def _cdp_json(cdp_url: str, path: str, timeout: float):
    try:
        with urllib.request.urlopen(f"{cdp_url}{path}", timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception:
        return None


def _cdp_port(cdp_url: str) -> str:
    return cdp_url.rsplit(":", 1)[-1].strip("/")


def _chrome_path() -> str:
    candidates = [
        os.path.join(os.environ.get("PROGRAMFILES", ""), "Google", "Chrome", "Application", "chrome.exe"),
        os.path.join(os.environ.get("PROGRAMFILES(X86)", ""), "Google", "Chrome", "Application", "chrome.exe"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google", "Chrome", "Application", "chrome.exe"),
    ]
    return next((path for path in candidates if path and os.path.exists(path)), "")


def _chrome_user_data_dir() -> str:
    return os.path.join(os.environ.get("LOCALAPPDATA", ""), "KworkLeadChromeUserData")


def _chrome_last_profile(user_data: str) -> str:
    local_state = os.path.join(user_data, "Local State")
    try:
        with open(local_state, "r", encoding="utf-8") as file:
            data = json.load(file)
        last_used = data.get("profile", {}).get("last_used", "")
        if last_used:
            return str(last_used)
    except Exception:
        pass
    return "Default"


def _is_kwork_tab(url: str) -> bool:
    parsed = urlsplit(url)
    return parsed.netloc.lower().endswith("kwork.ru")


def _is_kwork_list_tab(url: str) -> bool:
    parsed = urlsplit(url)
    return parsed.netloc.lower().endswith("kwork.ru") and parsed.path.rstrip("/") == "/projects"


def _is_kwork_project_tab(url: str) -> bool:
    parsed = urlsplit(url)
    if not parsed.netloc.lower().endswith("kwork.ru"):
        return False
    if re.match(r"^/projects/\d+(?:/view)?/?$", parsed.path):
        return True
    return parsed.path == "/new_offer" and any(key == "project" and value.isdigit() for key, value in parse_qsl(parsed.query))


def _matches_tab_kind(url: str, tab_kind: str) -> bool:
    if tab_kind == "list":
        return _is_kwork_list_tab(url)
    if tab_kind == "project":
        return _is_kwork_project_tab(url)
    return _is_kwork_tab(url)


def _matches_created_tab(actual_url: str, expected_url: str, tab_kind: str) -> bool:
    if tab_kind == "project":
        return _is_same_kwork_page(expected_url, actual_url)
    if tab_kind == "list":
        return _is_kwork_list_tab(actual_url)
    return _matches_tab_kind(actual_url, tab_kind)


def _first_group(pattern: re.Pattern[str], text: str, group: str) -> str:
    match = pattern.search(text)
    return match.group(group) if match else ""


def _visible_text(value: str) -> str:
    value = value.replace("<br/>", " ").replace("<br>", " ")
    return _clean_text(TAG_PATTERN.sub(" ", value))


def _clean_text(value: str) -> str:
    return " ".join(html.unescape(value).split())
