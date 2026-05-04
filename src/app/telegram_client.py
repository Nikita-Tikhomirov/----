from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import timezone


@dataclass(frozen=True)
class TelegramPost:
    channel: str
    message_id: int
    url: str
    text: str
    posted_at: str


class TelegramLeadClient:
    def __init__(
        self,
        api_id: int,
        api_hash: str,
        session_name: str,
        channels: tuple[str, ...],
        max_posts_per_channel: int = 20,
    ):
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_name = session_name
        self.channels = channels
        self.max_posts_per_channel = max_posts_per_channel

    def fetch_recent_posts(self) -> list[TelegramPost]:
        return asyncio.run(self._fetch_recent_posts())

    def send_message(self, contact: str, text: str) -> str:
        return asyncio.run(self._send_message(contact, text))

    async def _fetch_recent_posts(self) -> list[TelegramPost]:
        from telethon import TelegramClient

        posts: list[TelegramPost] = []
        async with TelegramClient(self.session_name, self.api_id, self.api_hash) as client:
            for channel in self.channels:
                async for message in client.iter_messages(
                    channel,
                    limit=self.max_posts_per_channel,
                ):
                    text = message.message or ""
                    if not text.strip():
                        continue
                    posts.append(
                        TelegramPost(
                            channel=channel,
                            message_id=int(message.id),
                            url=_post_url(channel, int(message.id)),
                            text=text,
                            posted_at=message.date.astimezone(timezone.utc).isoformat(),
                        )
                    )
        return posts

    async def _send_message(self, contact: str, text: str) -> str:
        from telethon import TelegramClient

        async with TelegramClient(self.session_name, self.api_id, self.api_hash) as client:
            message = await client.send_message(contact, text)
            return str(message.id)


def _post_url(channel: str, message_id: int) -> str:
    clean_channel = channel.removeprefix("https://t.me/").removeprefix("@")
    return f"https://t.me/{clean_channel}/{message_id}"
