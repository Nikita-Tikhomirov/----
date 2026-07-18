from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.storage import Lead, LeadAttachment


@dataclass(frozen=True)
class LeadHubClient:
    """Small authenticated client for the mobile Kwork lead inbox."""

    base_url: str
    api_key: str
    owner_phone: str
    timeout_seconds: int = 20

    def build_lead_payload(
        self,
        lead: Lead,
        attachments: Iterable[LeadAttachment] = (),
    ) -> dict[str, object]:
        attachment_lines = [
            " | ".join(
                part
                for part in (
                    attachment.label.strip(),
                    f"Статус: {attachment.status.strip()}" if attachment.status.strip() else "",
                    attachment.summary.strip(),
                    f"Ссылка: {attachment.url.strip()}" if attachment.url.strip() else "",
                    "Архив раскрыт" if attachment.opened_archive else "",
                    "OCR выполнен" if attachment.ocr_scanned else "",
                )
                if part
            )
            for attachment in attachments
        ]
        return {
            "external_key": f"kwork:{lead.id}",
            "owner_phone": self.owner_phone,
            "source": "kwork",
            "source_url": lead.post_url or lead.contact,
            "title": lead.proposal_title.strip() or _lead_title(lead),
            "raw_brief": lead.post_text,
            "summary": lead.summary,
            "attachment_report": "\n".join(line for line in attachment_lines if line),
            "draft_reply": lead.draft_reply,
            "proposal_title": lead.proposal_title,
            "proposal_price_rub": lead.proposal_price_rub,
            "proposal_days": lead.proposal_days,
            "offer_count": lead.live_response_count,
        }

    def publish_lead(
        self,
        lead: Lead,
        attachments: Iterable[LeadAttachment] = (),
    ) -> int:
        payload = json.dumps(
            self.build_lead_payload(lead, attachments),
            ensure_ascii=False,
        ).encode("utf-8")
        url = self.base_url.rstrip("/") + "/leads/ingest"
        request = Request(
            url,
            data=payload,
            method="POST",
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "X-Api-Key": self.api_key,
            },
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise RuntimeError(f"Lead hub rejected Kwork lead: HTTP {exc.code}") from exc
        except URLError as exc:
            raise RuntimeError(f"Lead hub is unavailable: {exc.reason}") from exc
        if not response_payload.get("ok"):
            raise RuntimeError(str(response_payload.get("error") or "Lead hub rejected Kwork lead"))
        lead_id = response_payload.get("lead", {}).get("id")
        if not isinstance(lead_id, int) or lead_id <= 0:
            raise RuntimeError("Lead hub returned an invalid lead id")
        return lead_id

    def fetch_approved_commands(self) -> list[dict[str, object]]:
        payload = self._request("/leads/commands")
        commands = payload.get("commands", [])
        if not isinstance(commands, list):
            raise RuntimeError("Lead hub returned invalid approved commands")
        return [command for command in commands if isinstance(command, dict)]

    def claim_command(self, lead_id: int, executor_id: str) -> dict[str, object] | None:
        payload = self._request(
            "/leads/claim",
            {"lead_id": lead_id, "executor_id": executor_id},
        )
        lead = payload.get("lead")
        return lead if isinstance(lead, dict) else None

    def report_result(
        self,
        lead_id: int,
        executor_id: str,
        *,
        sent: bool,
        error: str = "",
    ) -> None:
        self._request(
            "/leads/result",
            {
                "lead_id": lead_id,
                "executor_id": executor_id,
                "sent": sent,
                "error": error,
            },
        )

    def _request(self, path: str, body: dict[str, object] | None = None) -> dict[str, object]:
        data = None
        method = "GET"
        headers = {"X-Api-Key": self.api_key}
        if body is not None:
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
            method = "POST"
            headers["Content-Type"] = "application/json; charset=utf-8"
        request = Request(
            self.base_url.rstrip("/") + path,
            data=data,
            method=method,
            headers=headers,
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise RuntimeError(f"Lead hub request failed: HTTP {exc.code}") from exc
        except URLError as exc:
            raise RuntimeError(f"Lead hub is unavailable: {exc.reason}") from exc
        if not isinstance(response_payload, dict) or not response_payload.get("ok"):
            error = response_payload.get("error") if isinstance(response_payload, dict) else "invalid response"
            raise RuntimeError(f"Lead hub rejected request: {error}")
        return response_payload


def _lead_title(lead: Lead) -> str:
    for line in lead.post_text.splitlines():
        clean = line.strip().lstrip("📌").strip()
        if clean:
            return clean[:70]
    return f"Kwork заказ #{lead.id}"
