from __future__ import annotations

import hashlib
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


MISSING_ERROR_MESSAGE = "Причина ошибки не получена."


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
    buyer_desired_budget_rub: int | None = None
    kwork_max_price_rub: int | None = None
    live_response_count: int | None = None
    live_checked_at: str = ""
    live_reason: str = ""
    hub_lead_id: int | None = None
    hub_synced_at: str = ""


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
class PostRejection:
    post_id: int
    channel: str
    message_id: int
    post_url: str
    post_text: str
    posted_at: str
    reason: str
    rejected_at: str


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
                    buyer_desired_budget_rub INTEGER,
                    kwork_max_price_rub INTEGER,
                    live_response_count INTEGER,
                    live_checked_at TEXT NOT NULL DEFAULT '',
                    live_reason TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'new',
                    email_message_id TEXT,
                    email_claimed_at TEXT NOT NULL DEFAULT '',
                    hub_lead_id INTEGER,
                    hub_synced_at TEXT NOT NULL DEFAULT '',
                    hub_claimed_at TEXT NOT NULL DEFAULT '',
                    last_error TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS post_rejections (
                    post_id INTEGER PRIMARY KEY REFERENCES posts(id),
                    reason TEXT NOT NULL,
                    rejected_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
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
            _ensure_column(conn, "leads", "buyer_desired_budget_rub", "INTEGER")
            _ensure_column(conn, "leads", "kwork_max_price_rub", "INTEGER")
            _ensure_column(conn, "leads", "live_response_count", "INTEGER")
            _ensure_column(conn, "leads", "live_checked_at", "TEXT NOT NULL DEFAULT ''")
            _ensure_column(conn, "leads", "live_reason", "TEXT NOT NULL DEFAULT ''")
            _ensure_column(conn, "leads", "email_claimed_at", "TEXT NOT NULL DEFAULT ''")
            _ensure_column(conn, "leads", "hub_lead_id", "INTEGER")
            _ensure_column(conn, "leads", "hub_synced_at", "TEXT NOT NULL DEFAULT ''")
            _ensure_column(conn, "leads", "hub_claimed_at", "TEXT NOT NULL DEFAULT ''")
            _backfill_missing_failed_errors(conn)
            _deduplicate_lead_attachment_urls(conn)
            conn.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS idx_lead_attachments_unique_url
                ON lead_attachments(lead_id, url)
                WHERE url <> ''
                """
            )
            _backfill_generated_order_titles(conn)

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

    def record_post_rejection(self, post_id: int, reason: str) -> None:
        """Persist a stable rejection so watch mode does not re-analyze the same post."""
        clean_reason = reason.strip()[:2000] or "заказ отклонен"
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO post_rejections (post_id, reason)
                VALUES (?, ?)
                ON CONFLICT(post_id) DO UPDATE SET
                    reason = excluded.reason,
                    rejected_at = CURRENT_TIMESTAMP
                """,
                (post_id, clean_reason),
            )

    def get_post_rejection(self, post_id: int) -> str:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT reason FROM post_rejections WHERE post_id = ?",
                (post_id,),
            ).fetchone()
        return str(row["reason"]) if row is not None else ""

    def list_post_rejections(self, limit: int = 100) -> list[PostRejection]:
        safe_limit = max(1, min(int(limit), 500))
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT post_rejections.post_id, post_rejections.reason, post_rejections.rejected_at,
                       posts.channel, posts.message_id, posts.post_url, posts.raw_text, posts.posted_at
                FROM post_rejections
                JOIN posts ON posts.id = post_rejections.post_id
                ORDER BY COALESCE(NULLIF(posts.posted_at, ''), post_rejections.rejected_at) DESC,
                         post_rejections.post_id DESC
                LIMIT ?
                """,
                (safe_limit,),
            ).fetchall()
        return [
            PostRejection(
                post_id=int(row["post_id"]),
                channel=str(row["channel"]),
                message_id=int(row["message_id"]),
                post_url=str(row["post_url"]),
                post_text=str(row["raw_text"]),
                posted_at=str(row["posted_at"]),
                reason=str(row["reason"]),
                rejected_at=str(row["rejected_at"]),
            )
            for row in rows
        ]

    def clear_post_rejection(self, post_id: int) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM post_rejections WHERE post_id = ?", (post_id,))

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
        buyer_desired_budget_rub: int | None = None,
        kwork_max_price_rub: int | None = None,
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
                    proposal_title, proposal_price_rub, proposal_days,
                    buyer_desired_budget_rub, kwork_max_price_rub, status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'new')
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
                    _optional_positive_int(buyer_desired_budget_rub, "Buyer desired budget"),
                    _optional_positive_int(kwork_max_price_rub, "Kwork maximum price"),
                ),
            )
            return int(cursor.lastrowid)

    def mark_lead_emailed(self, lead_id: int, email_message_id: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE leads
                SET status = 'emailed', email_message_id = ?, email_claimed_at = '', last_error = ''
                WHERE id = ?
                """,
                (email_message_id, lead_id),
            )

    def begin_lead_send(self, lead_id: int) -> bool:
        """Record a Kwork send attempt before opening the reply form."""
        with self._connect() as conn:
            cursor = conn.execute(
                """
                UPDATE leads
                SET status = 'sending', last_error = ''
                WHERE id = ? AND status IN ('new', 'emailed', 'approved', 'failed')
                """,
                (lead_id,),
            )
        return cursor.rowcount > 0

    def claim_lead_email_delivery(self, lead_id: int) -> bool:
        """Atomically reserve a new lead so concurrent scans cannot email it twice."""
        with self._connect() as conn:
            cursor = conn.execute(
                """
                UPDATE leads
                SET email_claimed_at = CURRENT_TIMESTAMP
                WHERE id = ?
                  AND status = 'new'
                  AND (
                      email_claimed_at = ''
                      OR email_claimed_at < datetime('now', '-15 minutes')
                  )
                """,
                (lead_id,),
            )
        return cursor.rowcount > 0

    def release_lead_email_delivery(self, lead_id: int) -> None:
        """Make a failed email attempt retryable without changing the lead's status."""
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE leads
                SET email_claimed_at = ''
                WHERE id = ? AND status = 'new'
                """,
                (lead_id,),
            )

    def claim_lead_hub_delivery(self, lead_id: int) -> bool:
        """Reserve an unsynced lead so scanner instances cannot create duplicate hub records."""
        with self._connect() as conn:
            cursor = conn.execute(
                """
                UPDATE leads
                SET hub_claimed_at = CURRENT_TIMESTAMP
                WHERE id = ?
                  AND hub_synced_at = ''
                  AND (hub_claimed_at = '' OR hub_claimed_at < datetime('now', '-15 minutes'))
                """,
                (lead_id,),
            )
        return cursor.rowcount > 0

    def mark_lead_hub_synced(self, lead_id: int, hub_lead_id: int) -> None:
        if hub_lead_id <= 0:
            raise ValueError("Hub lead id must be positive")
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE leads
                SET hub_lead_id = ?, hub_synced_at = CURRENT_TIMESTAMP, hub_claimed_at = ''
                WHERE id = ?
                """,
                (hub_lead_id, lead_id),
            )

    def release_lead_hub_delivery(self, lead_id: int) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE leads SET hub_claimed_at = '' WHERE id = ? AND hub_synced_at = ''",
                (lead_id,),
            )

    def update_lead_live_status(self, lead_id: int, response_count: int | None, reason: str = "") -> None:
        """Store the latest non-destructive Kwork page check for a lead."""
        if response_count is not None and response_count < 0:
            raise ValueError("Lead response count must not be negative")
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE leads
                SET live_response_count = ?, live_checked_at = CURRENT_TIMESTAMP, live_reason = ?
                WHERE id = ?
                """,
                (response_count, reason.strip()[:2000], lead_id),
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

    def update_lead_assessment(
        self,
        lead_id: int,
        *,
        score: int,
        summary: str,
        price_rub: int | None,
        days: int | None,
    ) -> None:
        """Replace only the AI assessment while preserving user-edited proposal content."""
        if not 0 <= score <= 100:
            raise ValueError("Lead score must be between 0 and 100")
        clean_summary = summary.strip()
        if not clean_summary:
            raise ValueError("Lead assessment summary must not be empty")
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE leads
                SET score = ?, summary = ?, proposal_price_rub = ?, proposal_days = ?
                WHERE id = ?
                """,
                (
                    score,
                    clean_summary,
                    _optional_positive_int(price_rub, "Lead proposal price"),
                    _optional_positive_int(days, "Lead proposal days"),
                    lead_id,
                ),
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
            conn.execute("UPDATE leads SET status = 'approved', last_error = '' WHERE id = ?", (lead_id,))
            return True

    def record_blocked_approval(self, lead_id: int, email_message_id: str, reason: str) -> bool:
        """Remember a rejected email command while keeping the lead available for correction."""
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
                    VALUES (?, ?, 'blocked')
                    """,
                    (lead_id, email_message_id),
                )
            except sqlite3.IntegrityError:
                return False
            conn.execute(
                "UPDATE leads SET last_error = ? WHERE id = ?",
                (reason.strip()[:2000], lead_id),
            )
            return True

    def restore_approved_lead(self, lead_id: int, reason: str) -> bool:
        """Return a preflight-blocked approval to the actionable email queue."""
        clean_reason = reason.strip()[:2000] or MISSING_ERROR_MESSAGE
        with self._connect() as conn:
            cursor = conn.execute(
                """
                UPDATE leads
                SET status = 'emailed', last_error = ?
                WHERE id = ? AND status = 'approved'
                """,
                (clean_reason, lead_id),
            )
        return cursor.rowcount > 0

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
        clean_error = error.strip()[:2000] or MISSING_ERROR_MESSAGE
        with self._connect() as conn:
            conn.execute(
                "UPDATE leads SET status = 'failed', last_error = ? WHERE id = ?",
                (clean_error, lead_id),
            )

    def replace_lead_attachments(self, lead_id: int, attachments: Iterable) -> None:
        values = _attachment_rows(lead_id, attachments)
        with self._connect() as conn:
            conn.execute("DELETE FROM lead_attachments WHERE lead_id = ?", (lead_id,))
            conn.executemany(
                """
                INSERT INTO lead_attachments
                    (lead_id, label, url, local_path, status, summary, kind, opened_archive, ocr_scanned)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                values,
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

    def get_lead_for_hub_id(self, hub_lead_id: int) -> Lead | None:
        """Return the local Kwork lead paired with a mobile inbox card."""
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
                WHERE leads.hub_lead_id = ?
                """,
                (hub_lead_id,),
            ).fetchone()
        return _lead_from_row(row) if row is not None else None

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
            title=_order_title_from_lead(lead),
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


def _attachment_rows(lead_id: int, attachments: Iterable) -> list[tuple]:
    values: list[tuple] = []
    seen_urls: set[str] = set()
    for attachment in attachments:
        label = str(getattr(attachment, "label", "")).strip()
        url = str(getattr(attachment, "url", "")).strip()
        if not label and not url:
            continue
        if url and url in seen_urls:
            continue
        if url:
            seen_urls.add(url)
        values.append(
            (
                lead_id,
                label,
                url,
                str(getattr(attachment, "local_path", "")).strip(),
                str(getattr(attachment, "status", "")).strip(),
                str(getattr(attachment, "summary", "")).strip(),
                str(getattr(attachment, "kind", "file")).strip() or "file",
                1 if bool(getattr(attachment, "opened_archive", False)) else 0,
                1 if bool(getattr(attachment, "ocr_scanned", False)) else 0,
            )
        )
    return values


def _deduplicate_lead_attachment_urls(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        DELETE FROM lead_attachments
        WHERE url <> ''
          AND id NOT IN (
              SELECT MAX(id)
              FROM lead_attachments
              WHERE url <> ''
              GROUP BY lead_id, url
          )
        """
    )


def _backfill_missing_failed_errors(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        UPDATE leads
        SET last_error = ?
        WHERE status = 'failed' AND TRIM(last_error) = ''
        """,
        (MISSING_ERROR_MESSAGE,),
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
        buyer_desired_budget_rub=(
            int(row["buyer_desired_budget_rub"])
            if "buyer_desired_budget_rub" in keys and row["buyer_desired_budget_rub"] is not None
            else None
        ),
        kwork_max_price_rub=(
            int(row["kwork_max_price_rub"])
            if "kwork_max_price_rub" in keys and row["kwork_max_price_rub"] is not None
            else None
        ),
        live_response_count=(
            int(row["live_response_count"])
            if "live_response_count" in keys and row["live_response_count"] is not None
            else None
        ),
        live_checked_at=str(row["live_checked_at"] or "") if "live_checked_at" in keys else "",
        live_reason=str(row["live_reason"] or "") if "live_reason" in keys else "",
        hub_lead_id=(
            int(row["hub_lead_id"])
            if "hub_lead_id" in keys and row["hub_lead_id"] is not None
            else None
        ),
        hub_synced_at=str(row["hub_synced_at"] or "") if "hub_synced_at" in keys else "",
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


def _backfill_generated_order_titles(conn: sqlite3.Connection) -> None:
    rows = conn.execute(
        """
        SELECT orders.id AS order_id,
               leads.id AS lead_id,
               leads.proposal_title,
               leads.summary,
               posts.raw_text
        FROM orders
        JOIN leads ON leads.id = orders.lead_id
        JOIN posts ON posts.id = leads.post_id
        WHERE orders.lead_id IS NOT NULL
          AND orders.title LIKE 'AI:%'
        """
    ).fetchall()
    for row in rows:
        title = _order_title_from_values(
            post_text=str(row["raw_text"] or ""),
            proposal_title=str(row["proposal_title"] or ""),
            summary=str(row["summary"] or ""),
            fallback=f"Kwork project {row['lead_id']}",
        )
        conn.execute(
            """
            UPDATE orders
            SET title = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (title, int(row["order_id"])),
        )


def _order_title_from_lead(lead: Lead) -> str:
    return _order_title_from_values(
        post_text=lead.post_text,
        proposal_title=lead.proposal_title,
        summary=lead.summary,
        fallback=f"Kwork project {lead.id}",
    )


def _order_title_from_values(
    post_text: str,
    proposal_title: str,
    summary: str,
    fallback: str,
) -> str:
    title = _title_from_post_text(post_text)
    if title:
        return title
    if proposal_title.strip():
        return _strip_kwork_inline_metadata(proposal_title.strip())[:70]
    title = _title_from_summary(summary)
    if title:
        return title
    return fallback


def _title_from_post_text(post_text: str) -> str:
    meta_prefixes = ("осталось:", "предложений:", "бюджет:", "контакт:", "kwork facts:")
    for line in post_text.splitlines():
        clean = line.strip()
        if not clean:
            continue
        if clean.startswith("📌"):
            return _strip_kwork_inline_metadata(clean.lstrip("📌").strip())[:70]
        if clean.lower().startswith(meta_prefixes):
            continue
        return _strip_kwork_inline_metadata(clean)[:70]
    return ""


def _title_from_summary(summary: str) -> str:
    for line in summary.splitlines():
        clean = line.strip()
        if clean.startswith("Задача:"):
            return _strip_kwork_inline_metadata(clean.removeprefix("Задача:").strip())[:70]
    return ""


def _strip_kwork_inline_metadata(value: str) -> str:
    clean = re.split(
        r"(?:[.,;]?\s+)(?:предложений|отклик|осталось|бюджет|контакт)\s*:",
        value,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]
    return clean.rstrip(" .,:;-")


def _optional_positive_int(value: int | None, field_name: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{field_name} must be a positive integer")
    return value
