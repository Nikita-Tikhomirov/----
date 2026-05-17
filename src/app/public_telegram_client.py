from __future__ import annotations

import html
import logging
import os
import re
import ssl
import urllib.request
from typing import Any
from urllib.request import Request

from app.telegram_client import TelegramPost


logger = logging.getLogger(__name__)


def _build_proxy_handler() -> Any | None:
    """Return a urllib ProxyHandler if proxy env vars are set, or None."""
    proxy_url = (
        os.getenv("TELEGRAM_PROXY")
        or os.getenv("HTTPS_PROXY")
        or os.getenv("HTTP_PROXY")
        or os.getenv("https_proxy")
        or os.getenv("http_proxy")
    )
    if proxy_url:
        logger.info("Using proxy: %s", proxy_url.split("@")[-1] if "@" in proxy_url else proxy_url)
        from urllib.request import ProxyHandler

        return ProxyHandler({"https": proxy_url, "http": proxy_url})
    if os.getenv("TELEGRAM_PROXY_SOCKS5"):
        logger.warning(
            "TELEGRAM_PROXY_SOCKS5 requires 'pysocks' package: pip install pysocks"
        )
    return None


MESSAGE_START_PATTERN = re.compile(
    r'<div class="[^"]*\btgme_widget_message\b[^"]*"[^>]*data-post="(?P<post>[^"]+)"',
    re.IGNORECASE,
)
TIME_PATTERN = re.compile(r'<time[^>]*datetime="(?P<datetime>[^"]+)"', re.IGNORECASE)
TEXT_PATTERN = re.compile(
    r'<div class="tgme_widget_message_text js-message_text"[^>]*>(?P<text>[\s\S]*?)</div>',
    re.IGNORECASE,
)
INLINE_BUTTON_PATTERN = re.compile(
    r'<a class="[^"]*\btgme_widget_message_inline_button\b[^"]*"[^>]*href="(?P<href>[^"]+)"',
    re.IGNORECASE,
)
TAG_PATTERN = re.compile(r"<[^>]+>")


class PublicTelegramClient:
    can_send_replies = False

    def __init__(self, channels: tuple[str, ...], max_posts_per_channel: int = 20):
        self.channels = channels
        self.max_posts_per_channel = max_posts_per_channel

    def fetch_recent_posts(self) -> list[TelegramPost]:
        posts: list[TelegramPost] = []
        for channel in self.channels:
            clean_channel = normalize_channel(channel)
            try:
                html_text = _fetch_channel_html(clean_channel)
            except Exception as exc:
                logger.warning("Skipping channel %s: %s", channel, exc)
                continue
            try:
                channel_posts = parse_public_channel_posts(clean_channel, html_text)
            except Exception as exc:
                logger.warning("Failed to parse posts from %s: %s", channel, exc)
                continue
            posts.extend(channel_posts[: self.max_posts_per_channel])
        return posts

    def send_message(self, contact: str, text: str) -> str:
        raise RuntimeError(
            "Telegram API is not configured. Public fallback can read channels, "
            "but cannot send Telegram replies automatically."
        )


def parse_public_channel_posts(channel: str, html_text: str) -> list[TelegramPost]:
    posts: list[TelegramPost] = []
    matches = list(MESSAGE_START_PATTERN.finditer(html_text))
    for index, match in enumerate(matches):
        post_ref = html.unescape(match.group("post"))
        message_id = _message_id(post_ref)
        block_end = matches[index + 1].start() if index + 1 < len(matches) else len(html_text)
        block = html_text[match.start() : block_end]
        text_match = TEXT_PATTERN.search(block)
        if text_match is None:
            continue
        text = _clean_text(text_match.group("text"))
        if not text:
            continue
        reply_url = _first_inline_reply_url(block)
        if reply_url:
            text = f"{text} Отклик: {reply_url}"
        time_match = TIME_PATTERN.search(block)
        posts.append(
            TelegramPost(
                channel=channel,
                message_id=message_id,
                url=f"https://t.me/{channel}/{message_id}",
                text=text,
                posted_at=time_match.group("datetime") if time_match else "",
            )
        )
    return posts


def normalize_channel(channel: str) -> str:
    return channel.strip().removeprefix("https://t.me/s/").removeprefix("https://t.me/").removeprefix("@")


def _fetch_channel_html(channel: str) -> str:
    proxy_handler = _build_proxy_handler()
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE

    if proxy_handler:
        opener = urllib.request.build_opener(proxy_handler, urllib.request.HTTPSHandler(context=ssl_ctx))
    else:
        opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ssl_ctx))

    request = Request(
        f"https://t.me/s/{channel}",
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
    )
    with opener.open(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def _message_id(post_ref: str) -> int:
    _, raw_id = post_ref.rsplit("/", 1)
    return int(raw_id)


def _clean_text(raw: str) -> str:
    raw = raw.replace("<br/>", "\n").replace("<br>", "\n")
    without_tags = TAG_PATTERN.sub("", raw)
    return " ".join(html.unescape(without_tags).split())


def _first_inline_reply_url(block: str) -> str:
    match = INLINE_BUTTON_PATTERN.search(block)
    return html.unescape(match.group("href")) if match else ""
