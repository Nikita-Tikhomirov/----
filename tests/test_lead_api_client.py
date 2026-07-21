import json

from app.lead_api_client import LeadHubClient
from app.storage import Lead, LeadAttachment


def test_lead_hub_builds_structured_kwork_payload():
    client = LeadHubClient(
        base_url="http://example.test",
        api_key="test-key",
        owner_phone="79679812438",
    )
    lead = Lead(
        id=41,
        post_id=3,
        score=88,
        summary="AI: accept\nЗадача: Сверстать лендинг",
        draft_reply="Сделаю адаптивную страницу.",
        contact="https://kwork.ru/projects/41",
        status="new",
        post_url="https://kwork.ru/projects/41",
        post_text="Сверстать лендинг",
        proposal_title="Верстка лендинга",
        proposal_price_rub=5000,
        proposal_days=3,
        buyer_desired_budget_rub=2000,
        kwork_max_price_rub=6000,
        live_response_count=2,
    )
    attachment = LeadAttachment(
        id=1,
        lead_id=41,
        label="ТЗ.pdf",
        url="https://kwork.ru/files/tz.pdf",
        local_path="",
        status="прочитан",
        summary="PDF прочитан",
        kind="file",
        opened_archive=False,
        ocr_scanned=False,
    )

    payload = client.build_lead_payload(lead, [attachment])

    assert payload["external_key"] == "kwork:41"
    assert payload["owner_phone"] == "79679812438"
    assert payload["title"] == "Верстка лендинга"
    assert payload["offer_count"] == 2
    assert payload["buyer_desired_budget_rub"] == 2000
    assert payload["kwork_max_price_rub"] == 6000
    assert "ТЗ.pdf" in payload["attachment_report"]


def test_lead_hub_claims_mobile_approval_and_reports_result(monkeypatch):
    requests = []

    class Response:
        def __init__(self, payload):
            self.payload = payload

        def read(self):
            return json.dumps(self.payload).encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    responses = [
        {"ok": True, "commands": [{"id": 91, "status": "approved"}]},
        {"ok": True, "lead": {"id": 91, "status": "sending"}},
        {"ok": True, "lead": {"id": 91, "status": "sent"}},
    ]

    def fake_urlopen(request, timeout):
        requests.append((request.full_url, request.method, request.data, timeout))
        return Response(responses.pop(0))

    monkeypatch.setattr("app.lead_api_client.urlopen", fake_urlopen)
    client = LeadHubClient("http://hub.test", "test-key", "79679812438")

    assert client.fetch_approved_commands() == [{"id": 91, "status": "approved"}]
    assert client.claim_command(91, "desktop-main") == {"id": 91, "status": "sending"}
    client.report_result(91, "desktop-main", sent=True)

    assert [(url, method) for url, method, _data, _timeout in requests] == [
        ("http://hub.test/leads/commands", "GET"),
        ("http://hub.test/leads/claim", "POST"),
        ("http://hub.test/leads/result", "POST"),
    ]


def test_lead_hub_reads_mobile_monitor_command_and_reports_heartbeat(monkeypatch):
    requests = []

    class Response:
        def __init__(self, payload):
            self.payload = payload

        def read(self):
            return json.dumps(self.payload).encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    responses = [
        {"ok": True, "monitor": {"desired_state": "running", "scan_requested": True}},
        {"ok": True, "monitor": {"desired_state": "running", "last_seen_at": "2026-07-18T18:00:00+03:00"}},
    ]

    def fake_urlopen(request, timeout):
        requests.append((request.full_url, request.method, request.data, timeout))
        return Response(responses.pop(0))

    monkeypatch.setattr("app.lead_api_client.urlopen", fake_urlopen)
    client = LeadHubClient("http://hub.test", "test-key", "79679812438")

    assert client.fetch_monitor_control()["scan_requested"] is True
    client.report_monitor_heartbeat("desktop-main", scan_event="started")

    assert [(url, method) for url, method, _data, _timeout in requests] == [
        ("http://hub.test/leads/monitor/executor?owner_phone=79679812438", "GET"),
        ("http://hub.test/leads/monitor/heartbeat", "POST"),
    ]
    assert json.loads(requests[1][2].decode("utf-8")) == {
        "owner_phone": "79679812438",
        "executor_id": "desktop-main",
        "scan_event": "started",
        "error": "",
    }
