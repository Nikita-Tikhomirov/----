from __future__ import annotations

import html
import logging
import re
import ssl
import urllib.request
from dataclasses import dataclass
from urllib.parse import urlparse
from urllib.request import Request

logger = logging.getLogger(__name__)

WORKER_COUNT_PATTERN = re.compile(r'"workerCount"\s*:\s*(\d+)', re.IGNORECASE)
TITLE_PATTERN = re.compile(r"<title>(?P<title>[\s\S]*?)</title>", re.IGNORECASE)
DESCRIPTION_PATTERN = re.compile(
    r'<meta\s+name=["\']description["\']\s+content=["\'](?P<description>[\s\S]*?)["\']',
    re.IGNORECASE,
)


@dataclass(frozen=True)
class KworkProjectInfo:
    url: str
    response_count: int | None
    title: str
    description: str
    reason: str = ""

    @property
    def has_response_count(self) -> bool:
        return self.response_count is not None


class KworkProjectClient:
    def __init__(self, timeout_seconds: float = 20.0):
        self.timeout_seconds = timeout_seconds

    def inspect(self, url: str) -> KworkProjectInfo:
        if not _is_kwork_project_url(url):
            return KworkProjectInfo(url=url, response_count=None, title="", description="", reason="это не Kwork-ссылка")
        try:
            html_text = _fetch_project_html(url, self.timeout_seconds)
        except Exception as exc:
            logger.warning("Failed to fetch Kwork project %s: %s", url, exc)
            return KworkProjectInfo(url=url, response_count=None, title="", description="", reason=f"Kwork не открылся: {exc}")
        return parse_kwork_project_html(url, html_text)


def parse_kwork_project_html(url: str, html_text: str) -> KworkProjectInfo:
    count_match = WORKER_COUNT_PATTERN.search(html_text)
    title = _clean_title(_first_group(TITLE_PATTERN, html_text, "title"))
    description = _clean_text(_first_group(DESCRIPTION_PATTERN, html_text, "description"))

    if not count_match:
        return KworkProjectInfo(
            url=url,
            response_count=None,
            title=title,
            description=description,
            reason="на странице не найден workerCount",
        )

    return KworkProjectInfo(
        url=url,
        response_count=int(count_match.group(1)),
        title=title,
        description=description,
    )


def _is_kwork_project_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.netloc.lower().endswith("kwork.ru") and parsed.path.startswith("/projects/")


def _fetch_project_html(url: str, timeout_seconds: float) -> str:
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Encoding": "identity",
        },
    )
    opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ssl_ctx))
    with opener.open(request, timeout=timeout_seconds) as response:
        return response.read().decode("utf-8", errors="replace")


def _first_group(pattern: re.Pattern[str], text: str, group: str) -> str:
    match = pattern.search(text)
    return match.group(group) if match else ""


def _clean_title(value: str) -> str:
    value = _clean_text(value)
    return value.removesuffix(" - Kwork").strip()


def _clean_text(value: str) -> str:
    return " ".join(html.unescape(value).split())
