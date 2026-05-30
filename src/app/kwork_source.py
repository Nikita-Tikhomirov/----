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
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit
from urllib.request import Request

from app.telegram_client import TelegramPost

logger = logging.getLogger(__name__)

DEFAULT_KWORK_PROJECTS_URL = "https://kwork.ru/projects?c=11"
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
    can_send_replies = False

    def __init__(
        self,
        projects_url: str = DEFAULT_KWORK_PROJECTS_URL,
        max_posts: int = 30,
        max_responses: int = 5,
        cookie: str = "",
        timeout_seconds: float = 30.0,
        use_browser: bool = True,
        cdp_url: str = "http://127.0.0.1:9222",
        browser_profile_dir: str = "",
    ):
        self.projects_url = projects_url
        self.max_posts = max_posts
        self.max_responses = max_responses
        self.cookie = cookie
        self.timeout_seconds = timeout_seconds
        self.use_browser = use_browser
        self.cdp_url = cdp_url.rstrip("/")
        self.browser_profile_dir = browser_profile_dir

    def fetch_recent_posts(self) -> list[TelegramPost]:
        html_text = ""
        if self.use_browser:
            try:
                html_text = _fetch_rendered_html(
                    self.projects_url,
                    self.cdp_url,
                    self.timeout_seconds,
                    self.browser_profile_dir,
                )
            except Exception as exc:
                logger.warning("Failed to fetch rendered Kwork projects page via Chrome: %s", exc)
        try:
            if not html_text:
                html_text = _fetch_html(self.projects_url, self.timeout_seconds, self.cookie)
        except Exception as exc:
            logger.warning("Failed to fetch Kwork projects page %s: %s", self.projects_url, exc)
            return []
        posts = parse_kwork_project_cards(
            html_text,
            max_responses=self.max_responses,
            base_url=self.projects_url,
        )
        return posts[: self.max_posts]

    def send_message(self, contact: str, text: str) -> str:
        raise RuntimeError("Kwork web source is read-only; replies are sent manually.")


def parse_kwork_project_cards(
    html_text: str,
    max_responses: int,
    base_url: str = "https://kwork.ru/projects",
) -> list[TelegramPost]:
    posts: list[TelegramPost] = []
    seen_ids: set[int] = set()
    for block in CARD_PATTERN.findall(html_text):
        post = _post_from_card(block, max_responses=max_responses, base_url=base_url)
        if post is None or post.message_id in seen_ids:
            continue
        seen_ids.add(post.message_id)
        posts.append(post)
    return posts


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
    page = _find_or_create_page(cdp_url, url)

    import websocket

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
    user_data = browser_profile_dir or os.path.join(os.environ.get("LOCALAPPDATA", ""), "KworkLeadChrome")
    os.makedirs(user_data, exist_ok=True)
    args = [
        chrome,
        f"--user-data-dir={user_data}",
        f"--remote-debugging-port={_cdp_port(cdp_url)}",
        "--remote-allow-origins=*",
        "--no-first-run",
        "--disable-default-apps",
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


def _find_or_create_page(cdp_url: str, url: str) -> dict[str, str]:
    pages = _cdp_json(cdp_url, "/json/list", timeout=5) or []
    for page in pages:
        if page.get("type") == "page" and page.get("url", "").startswith(url.split("?", 1)[0]):
            if page.get("webSocketDebuggerUrl"):
                return page

    version = _cdp_json(cdp_url, "/json/version", timeout=5)
    if not version:
        raise RuntimeError("Chrome DevTools version endpoint is unavailable")

    import websocket

    ws = websocket.create_connection(version["webSocketDebuggerUrl"], timeout=10)
    try:
        _send_cdp(ws, "Target.createTarget", {"url": url})
    finally:
        ws.close()

    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        pages = _cdp_json(cdp_url, "/json/list", timeout=5) or []
        for page in pages:
            if page.get("type") == "page" and page.get("url", "").startswith(url.split("?", 1)[0]):
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
        {"expression": expression, "returnByValue": True},
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


def _first_group(pattern: re.Pattern[str], text: str, group: str) -> str:
    match = pattern.search(text)
    return match.group(group) if match else ""


def _visible_text(value: str) -> str:
    value = value.replace("<br/>", " ").replace("<br>", " ")
    return _clean_text(TAG_PATTERN.sub(" ", value))


def _clean_text(value: str) -> str:
    return " ".join(html.unescape(value).split())
