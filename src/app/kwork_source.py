from __future__ import annotations

import html
import logging
import re
import ssl
import urllib.request
from urllib.parse import urljoin
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
    ):
        self.projects_url = projects_url
        self.max_posts = max_posts
        self.max_responses = max_responses
        self.cookie = cookie
        self.timeout_seconds = timeout_seconds

    def fetch_recent_posts(self) -> list[TelegramPost]:
        try:
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


def _first_group(pattern: re.Pattern[str], text: str, group: str) -> str:
    match = pattern.search(text)
    return match.group(group) if match else ""


def _visible_text(value: str) -> str:
    value = value.replace("<br/>", " ").replace("<br>", " ")
    return _clean_text(TAG_PATTERN.sub(" ", value))


def _clean_text(value: str) -> str:
    return " ".join(html.unescape(value).split())
