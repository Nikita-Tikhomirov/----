from __future__ import annotations

import html
import json
import logging
import re
import ssl
import urllib.request
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
from urllib.request import Request

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
    reason: str = ""

    @property
    def has_response_count(self) -> bool:
        return self.response_count is not None


class KworkProjectClient:
    def __init__(
        self,
        timeout_seconds: float = 20.0,
        cookie: str = "",
        use_browser: bool = True,
        cdp_url: str = "http://127.0.0.1:9222",
        browser_profile_dir: str = "",
    ):
        self.timeout_seconds = timeout_seconds
        self.cookie = cookie
        self.use_browser = use_browser
        self.cdp_url = cdp_url
        self.browser_profile_dir = browser_profile_dir

    def inspect(self, url: str) -> KworkProjectInfo:
        if not _is_kwork_project_url(url):
            return KworkProjectInfo(url=url, response_count=None, title="", description="", reason="это не Kwork-ссылка")
        try:
            html_text = ""
            if self.use_browser:
                html_text = _fetch_rendered_project_html(
                    url,
                    timeout_seconds=self.timeout_seconds,
                    cdp_url=self.cdp_url,
                    browser_profile_dir=self.browser_profile_dir,
                )
            if not html_text:
                html_text = _fetch_project_html(url, self.timeout_seconds, self.cookie)
        except Exception as exc:
            logger.warning("Failed to fetch Kwork project %s: %s", url, exc)
            return KworkProjectInfo(url=url, response_count=None, title="", description="", reason=f"Kwork не открылся: {exc}")
        return parse_kwork_project_html(url, html_text)


def parse_kwork_project_html(url: str, html_text: str) -> KworkProjectInfo:
    visible_text = _visible_text(html_text)
    count_match = OFFER_COUNT_PATTERN.search(visible_text)
    title = _clean_title(_first_group(TITLE_PATTERN, html_text, "title"))
    description = _clean_text(_first_group(DESCRIPTION_PATTERN, html_text, "description"))
    attachments = tuple(_extract_attachments(url, html_text))
    page_text = _shorten(visible_text, 4000)

    if not count_match:
        return KworkProjectInfo(
            url=url,
            response_count=None,
            title=title,
            description=description,
            page_text=page_text,
            attachments=attachments,
            reason="на странице не найдено поле 'Предложений'",
        )

    return KworkProjectInfo(
        url=url,
        response_count=int(count_match.group(1)),
        title=title,
        description=description,
        page_text=page_text,
        attachments=attachments,
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
    page = _find_or_create_page(cdp_url, url, tab_kind="project")

    import websocket

    ws = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=timeout_seconds)
    try:
        _refresh_page(ws, url, timeout_seconds)
        deadline_text = _evaluate(ws, "document.body && document.body.innerText")
        if not deadline_text:
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


def _shorten(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"
