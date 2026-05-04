from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Lead:
    id: int
    post_id: int
    score: int
    summary: str
    draft_reply: str
    contact: str
    status: str
    post_url: str


class Storage:
    def __init__(self, database_path: str | Path):
        self.database_path = Path(database_path)

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel TEXT NOT NULL,
                    message_id INTEGER NOT NULL,
                    post_url TEXT NOT NULL,
                    text_hash TEXT NOT NULL,
                    raw_text TEXT NOT NULL,
                    posted_at TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(channel, message_id)
                );

                CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id INTEGER NOT NULL REFERENCES posts(id),
                    score INTEGER NOT NULL,
                    summary TEXT NOT NULL,
                    draft_reply TEXT NOT NULL,
                    contact TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'new',
                    email_message_id TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS approvals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lead_id INTEGER NOT NULL REFERENCES leads(id),
                    email_message_id TEXT NOT NULL UNIQUE,
                    approval_status TEXT NOT NULL,
                    approved_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS sent_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lead_id INTEGER NOT NULL UNIQUE REFERENCES leads(id),
                    contact TEXT NOT NULL,
                    sent_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    telegram_message_id TEXT NOT NULL
                );
                """
            )

    def save_post(
        self,
        channel: str,
        message_id: int,
        post_url: str,
        text: str,
        posted_at: str,
    ) -> int:
        text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO posts
                    (channel, message_id, post_url, text_hash, raw_text, posted_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (channel, message_id, post_url, text_hash, text, posted_at),
            )
            row = conn.execute(
                "SELECT id FROM posts WHERE channel = ? AND message_id = ?",
                (channel, message_id),
            ).fetchone()
        return int(row["id"])

    def create_lead(
        self,
        post_id: int,
        score: int,
        summary: str,
        draft_reply: str,
        contact: str,
    ) -> int:
        with self._connect() as conn:
            existing = conn.execute(
                "SELECT id FROM leads WHERE post_id = ?",
                (post_id,),
            ).fetchone()
            if existing:
                return int(existing["id"])
            cursor = conn.execute(
                """
                INSERT INTO leads (post_id, score, summary, draft_reply, contact, status)
                VALUES (?, ?, ?, ?, ?, 'new')
                """,
                (post_id, score, summary, draft_reply, contact),
            )
            return int(cursor.lastrowid)

    def mark_lead_emailed(self, lead_id: int, email_message_id: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE leads SET status = 'emailed', email_message_id = ? WHERE id = ?",
                (email_message_id, lead_id),
            )

    def record_approval(self, lead_id: int, email_message_id: str) -> bool:
        with self._connect() as conn:
            lead = conn.execute(
                "SELECT status FROM leads WHERE id = ?",
                (lead_id,),
            ).fetchone()
            if lead is None or lead["status"] in {"approved", "sent"}:
                return False
            try:
                conn.execute(
                    """
                    INSERT INTO approvals (lead_id, email_message_id, approval_status)
                    VALUES (?, ?, 'approved')
                    """,
                    (lead_id, email_message_id),
                )
            except sqlite3.IntegrityError:
                return False
            conn.execute("UPDATE leads SET status = 'approved' WHERE id = ?", (lead_id,))
            return True

    def mark_sent(self, lead_id: int, contact: str, telegram_message_id: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO sent_messages
                    (lead_id, contact, telegram_message_id)
                VALUES (?, ?, ?)
                """,
                (lead_id, contact, telegram_message_id),
            )
            conn.execute("UPDATE leads SET status = 'sent' WHERE id = ?", (lead_id,))

    def mark_failed(self, lead_id: int) -> None:
        with self._connect() as conn:
            conn.execute("UPDATE leads SET status = 'failed' WHERE id = ?", (lead_id,))

    def get_lead(self, lead_id: int) -> Lead:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT leads.*, posts.post_url
                FROM leads
                JOIN posts ON posts.id = leads.post_id
                WHERE leads.id = ?
                """,
                (lead_id,),
            ).fetchone()
        if row is None:
            raise KeyError(f"Lead not found: {lead_id}")
        return _lead_from_row(row)

    def list_leads(self, status: str | None = None) -> list[Lead]:
        sql = """
            SELECT leads.*, posts.post_url
            FROM leads
            JOIN posts ON posts.id = leads.post_id
        """
        params: tuple[str, ...] = ()
        if status:
            sql += " WHERE leads.status = ?"
            params = (status,)
        sql += " ORDER BY leads.id"
        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [_lead_from_row(row) for row in rows]

    def seen_approval_message_ids(self) -> set[str]:
        with self._connect() as conn:
            rows = conn.execute("SELECT email_message_id FROM approvals").fetchall()
        return {str(row["email_message_id"]) for row in rows}

    def count_posts(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS total FROM posts").fetchone()
        return int(row["total"])

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        return conn


def _lead_from_row(row: sqlite3.Row) -> Lead:
    return Lead(
        id=int(row["id"]),
        post_id=int(row["post_id"]),
        score=int(row["score"]),
        summary=str(row["summary"]),
        draft_reply=str(row["draft_reply"]),
        contact=str(row["contact"]),
        status=str(row["status"]),
        post_url=str(row["post_url"]),
    )
