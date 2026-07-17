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
    post_text: str = ""
    last_error: str = ""
    channel: str = ""
    message_id: int = 0
    posted_at: str = ""
    created_at: str = ""
    email_message_id: str = ""
    sent_at: str = ""
    proposal_title: str = ""
    proposal_price_rub: int | None = None
    proposal_days: int | None = None


@dataclass(frozen=True)
class LeadAttachment:
    id: int
    lead_id: int
    label: str
    url: str
    local_path: str
    status: str
    summary: str
    kind: str
    opened_archive: bool
    ocr_scanned: bool


@dataclass(frozen=True)
class Order:
    id: int
    lead_id: int | None
    contact: str
    title: str
    brief: str
    status: str
    deliverable: str
    revision_notes: str
    created_at: str
    updated_at: str


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
                    proposal_title TEXT NOT NULL DEFAULT '',
                    proposal_price_rub INTEGER,
                    proposal_days INTEGER,
                    status TEXT NOT NULL DEFAULT 'new',
                    email_message_id TEXT,
                    last_error TEXT NOT NULL DEFAULT '',
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

                CREATE TABLE IF NOT EXISTS lead_attachments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lead_id INTEGER NOT NULL REFERENCES leads(id),
                    label TEXT NOT NULL,
                    url TEXT NOT NULL,
                    local_path TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL,
                    summary TEXT NOT NULL DEFAULT '',
                    kind TEXT NOT NULL DEFAULT 'file',
                    opened_archive INTEGER NOT NULL DEFAULT 0,
                    ocr_scanned INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lead_id INTEGER REFERENCES leads(id),
                    contact TEXT NOT NULL,
                    title TEXT NOT NULL,
                    brief TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'received',
                    deliverable TEXT NOT NULL DEFAULT '',
                    revision_notes TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(lead_id)
                );

                CREATE TABLE IF NOT EXISTS order_reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL REFERENCES orders(id),
                    email_message_id TEXT NOT NULL UNIQUE,
                    decision TEXT NOT NULL,
                    notes TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            _ensure_column(conn, "leads", "last_error", "TEXT NOT NULL DEFAULT ''")
            _ensure_column(conn, "leads", "proposal_title", "TEXT NOT NULL DEFAULT ''")
            _ensure_column(conn, "leads", "proposal_price_rub", "INTEGER")
            _ensure_column(conn, "leads", "proposal_days", "INTEGER")

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
        proposal_title: str = "",
        proposal_price_rub: int | None = None,
        proposal_days: int | None = None,
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
                INSERT INTO leads (
                    post_id, score, summary, draft_reply, contact,
                    proposal_title, proposal_price_rub, proposal_days, status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'new')
                """,
                (
                    post_id,
                    score,
                    summary,
                    draft_reply,
                    contact,
                    proposal_title.strip()[:70],
                    _optional_positive_int(proposal_price_rub, "Lead proposal price"),
                    _optional_positive_int(proposal_days, "Lead proposal days"),
                ),
            )
            return int(cursor.lastrowid)

    def mark_lead_emailed(self, lead_id: int, email_message_id: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE leads SET status = 'emailed', email_message_id = ?, last_error = '' WHERE id = ?",
                (email_message_id, lead_id),
            )

    def update_lead_reply(self, lead_id: int, draft_reply: str) -> None:
        clean_reply = draft_reply.strip()
        if not clean_reply:
            raise ValueError("Lead draft reply must not be empty")
        with self._connect() as conn:
            conn.execute(
                "UPDATE leads SET draft_reply = ?, last_error = '' WHERE id = ?",
                (clean_reply, lead_id),
            )

    def update_lead_proposal(
        self,
        lead_id: int,
        draft_reply: str,
        title: str,
        price_rub: int | None,
        days: int | None,
    ) -> None:
        clean_reply = draft_reply.strip()
        if not clean_reply:
            raise ValueError("Lead draft reply must not be empty")
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE leads
                SET draft_reply = ?,
                    proposal_title = ?,
                    proposal_price_rub = ?,
                    proposal_days = ?,
                    last_error = ''
                WHERE id = ?
                """,
                (
                    clean_reply,
                    title.strip()[:70],
                    _optional_positive_int(price_rub, "Lead proposal price"),
                    _optional_positive_int(days, "Lead proposal days"),
                    lead_id,
                ),
            )

    def has_lead_for_post(self, post_id: int) -> bool:
        with self._connect() as conn:
            row = conn.execute("SELECT 1 FROM leads WHERE post_id = ?", (post_id,)).fetchone()
        return row is not None

    def get_lead_for_post(self, post_id: int) -> Lead | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT leads.*, posts.post_url, posts.raw_text,
                       posts.channel AS post_channel,
                       posts.message_id AS post_message_id,
                       posts.posted_at AS post_posted_at,
                       sent_messages.sent_at AS sent_at
                FROM leads
                JOIN posts ON posts.id = leads.post_id
                LEFT JOIN sent_messages ON sent_messages.lead_id = leads.id
                WHERE leads.post_id = ?
                """,
                (post_id,),
            ).fetchone()
        return _lead_from_row(row) if row is not None else None

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
            conn.execute("UPDATE leads SET status = 'sent', last_error = '' WHERE id = ?", (lead_id,))
        self.create_order_from_lead(lead_id)

    def mark_failed(self, lead_id: int, error: str = "") -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE leads SET status = 'failed', last_error = ? WHERE id = ?",
                (error.strip()[:2000], lead_id),
            )

    def replace_lead_attachments(self, lead_id: int, attachments: Iterable) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM lead_attachments WHERE lead_id = ?", (lead_id,))
            conn.executemany(
                """
                INSERT INTO lead_attachments
                    (lead_id, label, url, local_path, status, summary, kind, opened_archive, ocr_scanned)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        lead_id,
                        str(getattr(attachment, "label", "")).strip(),
                        str(getattr(attachment, "url", "")).strip(),
                        str(getattr(attachment, "local_path", "")).strip(),
                        str(getattr(attachment, "status", "")).strip(),
                        str(getattr(attachment, "summary", "")).strip(),
                        str(getattr(attachment, "kind", "file")).strip() or "file",
                        1 if bool(getattr(attachment, "opened_archive", False)) else 0,
                        1 if bool(getattr(attachment, "ocr_scanned", False)) else 0,
                    )
                    for attachment in attachments
                    if str(getattr(attachment, "label", "")).strip() or str(getattr(attachment, "url", "")).strip()
                ],
            )

    def list_lead_attachments(self, lead_id: int) -> list[LeadAttachment]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM lead_attachments
                WHERE lead_id = ?
                ORDER BY id
                """,
                (lead_id,),
            ).fetchall()
        return [_lead_attachment_from_row(row) for row in rows]

    def get_lead(self, lead_id: int) -> Lead:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT leads.*, posts.post_url, posts.raw_text,
                       posts.channel AS post_channel,
                       posts.message_id AS post_message_id,
                       posts.posted_at AS post_posted_at,
                       sent_messages.sent_at AS sent_at
                FROM leads
                JOIN posts ON posts.id = leads.post_id
                LEFT JOIN sent_messages ON sent_messages.lead_id = leads.id
                WHERE leads.id = ?
                """,
                (lead_id,),
            ).fetchone()
        if row is None:
            raise KeyError(f"Lead not found: {lead_id}")
        return _lead_from_row(row)

    def list_leads(self, status: str | None = None) -> list[Lead]:
        sql = """
            SELECT leads.*, posts.post_url, posts.raw_text,
                   posts.channel AS post_channel,
                   posts.message_id AS post_message_id,
                   posts.posted_at AS post_posted_at,
                   sent_messages.sent_at AS sent_at
            FROM leads
            JOIN posts ON posts.id = leads.post_id
            LEFT JOIN sent_messages ON sent_messages.lead_id = leads.id
        """
        params: tuple[str, ...] = ()
        if status:
            sql += " WHERE leads.status = ?"
            params = (status,)
        sql += " ORDER BY COALESCE(NULLIF(posts.posted_at, ''), leads.created_at) DESC, leads.id DESC"
        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [_lead_from_row(row) for row in rows]

    def create_order(
        self,
        contact: str,
        title: str,
        brief: str,
        lead_id: int | None = None,
    ) -> int:
        with self._connect() as conn:
            if lead_id is not None:
                existing = conn.execute(
                    "SELECT id FROM orders WHERE lead_id = ?",
                    (lead_id,),
                ).fetchone()
                if existing:
                    return int(existing["id"])
            cursor = conn.execute(
                """
                INSERT INTO orders (lead_id, contact, title, brief, status)
                VALUES (?, ?, ?, ?, 'received')
                """,
                (lead_id, contact, title, brief),
            )
            return int(cursor.lastrowid)

    def create_order_from_lead(self, lead_id: int) -> int:
        lead = self.get_lead(lead_id)
        return self.create_order(
            lead_id=lead.id,
            contact=lead.contact,
            title=lead.summary,
            brief=lead.post_text or lead.draft_reply,
        )

    def start_order(self, order_id: int) -> None:
        self._update_order_status(
            order_id,
            allowed_statuses={"received", "revision_requested"},
            next_status="in_progress",
        )

    def submit_order_for_approval(self, order_id: int, deliverable: str) -> None:
        if not deliverable.strip():
            raise ValueError("Order deliverable must not be empty")
        with self._connect() as conn:
            order = conn.execute(
                "SELECT status FROM orders WHERE id = ?",
                (order_id,),
            ).fetchone()
            if order is None:
                raise KeyError(f"Order not found: {order_id}")
            if order["status"] not in {"received", "in_progress", "revision_requested"}:
                raise ValueError(f"Order cannot be submitted from status: {order['status']}")
            conn.execute(
                """
                UPDATE orders
                SET status = 'ready_for_approval',
                    deliverable = ?,
                    revision_notes = '',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (deliverable.strip(), order_id),
            )

    def request_order_revision(self, order_id: int, email_message_id: str, notes: str) -> bool:
        clean_notes = notes.strip()
        if not clean_notes:
            clean_notes = "Нужны правки без уточнения деталей"
        with self._connect() as conn:
            order = conn.execute(
                "SELECT status FROM orders WHERE id = ?",
                (order_id,),
            ).fetchone()
            if order is None or order["status"] != "ready_for_approval":
                return False
            if not _insert_order_review(conn, order_id, email_message_id, "revision", clean_notes):
                return False
            conn.execute(
                """
                UPDATE orders
                SET status = 'revision_requested',
                    revision_notes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND status = 'ready_for_approval'
                """,
                (clean_notes, order_id),
            )
            return True

    def approve_order(self, order_id: int, email_message_id: str) -> bool:
        with self._connect() as conn:
            order = conn.execute(
                "SELECT status FROM orders WHERE id = ?",
                (order_id,),
            ).fetchone()
            if order is None or order["status"] != "ready_for_approval":
                return False
            if not _insert_order_review(conn, order_id, email_message_id, "approved", ""):
                return False
            cursor = conn.execute(
                """
                UPDATE orders
                SET status = 'done',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND status = 'ready_for_approval'
                """,
                (order_id,),
            )
            return cursor.rowcount == 1

    def get_order(self, order_id: int) -> Order:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        if row is None:
            raise KeyError(f"Order not found: {order_id}")
        return _order_from_row(row)

    def list_orders(self, status: str | None = None) -> list[Order]:
        sql = "SELECT * FROM orders"
        params: tuple[str, ...] = ()
        if status:
            sql += " WHERE status = ?"
            params = (status,)
        sql += " ORDER BY id"
        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [_order_from_row(row) for row in rows]

    def seen_order_review_message_ids(self) -> set[str]:
        with self._connect() as conn:
            rows = conn.execute("SELECT email_message_id FROM order_reviews").fetchall()
        return {str(row["email_message_id"]) for row in rows}

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

    def _update_order_status(
        self,
        order_id: int,
        allowed_statuses: set[str],
        next_status: str,
    ) -> None:
        with self._connect() as conn:
            order = conn.execute(
                "SELECT status FROM orders WHERE id = ?",
                (order_id,),
            ).fetchone()
            if order is None:
                raise KeyError(f"Order not found: {order_id}")
            if order["status"] not in allowed_statuses:
                raise ValueError(f"Order cannot move from {order['status']} to {next_status}")
            conn.execute(
                """
                UPDATE orders
                SET status = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (next_status, order_id),
            )


def _lead_from_row(row: sqlite3.Row) -> Lead:
    keys = set(row.keys())
    return Lead(
        id=int(row["id"]),
        post_id=int(row["post_id"]),
        score=int(row["score"]),
        summary=str(row["summary"]),
        draft_reply=str(row["draft_reply"]),
        contact=str(row["contact"]),
        status=str(row["status"]),
        post_url=str(row["post_url"]),
        post_text=str(row["raw_text"]) if "raw_text" in keys else "",
        last_error=str(row["last_error"]) if "last_error" in keys else "",
        channel=str(row["post_channel"]) if "post_channel" in keys else "",
        message_id=int(row["post_message_id"]) if "post_message_id" in keys else 0,
        posted_at=str(row["post_posted_at"]) if "post_posted_at" in keys else "",
        created_at=str(row["created_at"]) if "created_at" in keys else "",
        email_message_id=str(row["email_message_id"]) if "email_message_id" in keys and row["email_message_id"] is not None else "",
        sent_at=str(row["sent_at"]) if "sent_at" in keys and row["sent_at"] is not None else "",
        proposal_title=str(row["proposal_title"] or "") if "proposal_title" in keys else "",
        proposal_price_rub=(
            int(row["proposal_price_rub"])
            if "proposal_price_rub" in keys and row["proposal_price_rub"] is not None
            else None
        ),
        proposal_days=(
            int(row["proposal_days"])
            if "proposal_days" in keys and row["proposal_days"] is not None
            else None
        ),
    )


def _order_from_row(row: sqlite3.Row) -> Order:
    return Order(
        id=int(row["id"]),
        lead_id=None if row["lead_id"] is None else int(row["lead_id"]),
        contact=str(row["contact"]),
        title=str(row["title"]),
        brief=str(row["brief"]),
        status=str(row["status"]),
        deliverable=str(row["deliverable"]),
        revision_notes=str(row["revision_notes"]),
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
    )


def _lead_attachment_from_row(row: sqlite3.Row) -> LeadAttachment:
    return LeadAttachment(
        id=int(row["id"]),
        lead_id=int(row["lead_id"]),
        label=str(row["label"]),
        url=str(row["url"]),
        local_path=str(row["local_path"]),
        status=str(row["status"]),
        summary=str(row["summary"]),
        kind=str(row["kind"]),
        opened_archive=bool(row["opened_archive"]),
        ocr_scanned=bool(row["ocr_scanned"]),
    )


def _insert_order_review(
    conn: sqlite3.Connection,
    order_id: int,
    email_message_id: str,
    decision: str,
    notes: str,
) -> bool:
    try:
        conn.execute(
            """
            INSERT INTO order_reviews (order_id, email_message_id, decision, notes)
            VALUES (?, ?, ?, ?)
            """,
            (order_id, email_message_id, decision, notes),
        )
    except sqlite3.IntegrityError:
        return False
    return True


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    columns = {str(row["name"]) for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def _optional_positive_int(value: int | None, field_name: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{field_name} must be a positive integer")
    return value
