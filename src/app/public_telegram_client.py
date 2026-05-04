from __future__ import annotations

import html
import re
import urllib.request

from app.telegram_client import TelegramPost


MESSAGE_START_PATTERN = re.compile(
    r'<div class="[^"]*\btgme_widget_message\b[^"]*"[^>]*data-post="(?P<post>[^"]+)"',
    re.IGNORECASE,
)
TIME_PATTERN = re.compile(r'<time[^>]*datetime="(?P<datetime>[^"]+)"', re.IGNORECASE)
TEXT_PATTERN = re.compile(
    r'<div class="tgme_widget_message_text js-message_text"[^>]*>(?P<text>[\s\S]*?)</div>',
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
            html_text = _fetch_channel_html(clean_channel)
            posts.extend(parse_public_channel_posts(clean_channel, html_text))
        return posts[: self.max_posts_per_channel * max(len(self.channels), 1)]

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
    request = urllib.request.Request(
        f"https://t.me/s/{channel}",
        headers={"User-Agent": "Mozilla/5.0"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def _message_id(post_ref: str) -> int:
    _, raw_id = post_ref.rsplit("/", 1)
    return int(raw_id)


def _clean_text(raw: str) -> str:
    raw = raw.replace("<br/>", "\n").replace("<br>", "\n")
    without_tags = TAG_PATTERN.sub("", raw)
    return " ".join(html.unescape(without_tags).split())
