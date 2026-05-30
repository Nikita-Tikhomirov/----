from app.kwork_source import parse_kwork_project_cards


def test_parse_kwork_project_cards_keeps_only_low_offer_projects():
    html = """
    <div class="want-card">
      <a class="want-card__title" href="/projects/3177548/view">Создать сайт на Tilda</a>
      <div class="want-card__description">Нужна помощь с лендингом</div>
      <div class="want-card__informers-row">
        <span>Осталось: 2 д. 17 ч.</span>
        <span>Предложений:&nbsp;4</span>
      </div>
    </div>
    <div class="want-card">
      <a class="want-card__title" href="/projects/3177557/view">Сайт-калькулятор</a>
      <div class="want-card__description">Нужен калькулятор услуг</div>
      <div class="want-card__informers-row">
        <span>Предложений:&nbsp;27</span>
      </div>
    </div>
    """

    posts = parse_kwork_project_cards(html, max_responses=5)

    assert len(posts) == 1
    assert posts[0].channel == "kwork-web"
    assert posts[0].message_id == 3177548
    assert posts[0].url == "https://kwork.ru/projects/3177548/view"
    assert "Предложений: 4" in posts[0].text
    assert "Отклик: https://kwork.ru/projects/3177548/view" in posts[0].text


def test_parse_kwork_project_cards_skips_cards_without_offer_count():
    html = """
    <div class="want-card">
      <a href="/projects/1/view">Без счетчика</a>
    </div>
    """

    assert parse_kwork_project_cards(html, max_responses=5) == []


def test_fetch_rendered_html_refreshes_page_before_reading(monkeypatch):
    import websocket
    import app.kwork_source as source

    calls = []
    navigated_url = ""

    class FakeWebSocket:
        def close(self):
            calls.append(("close", {}))

    def fake_send_cdp(ws, method, params):
        nonlocal navigated_url
        calls.append((method, params))
        if method == "Page.navigate":
            navigated_url = params["url"]
            return {}
        if method == "Runtime.evaluate":
            if params.get("expression") == "location.href":
                return {"result": {"result": {"value": navigated_url}}}
            return {"result": {"result": {"value": "<div class='want-card'></div>"}}}
        return {}

    monkeypatch.setattr(source, "_ensure_chrome_cdp", lambda cdp_url, url, browser_profile_dir="": None)
    monkeypatch.setattr(
        source,
        "_find_or_create_page",
        lambda cdp_url, url, tab_kind="any": {"webSocketDebuggerUrl": "ws://fake"},
    )
    monkeypatch.setattr(websocket, "create_connection", lambda url, timeout=30: FakeWebSocket())
    monkeypatch.setattr(source, "_send_cdp", fake_send_cdp)
    monkeypatch.setattr(source, "_wait_for_cards", lambda ws, timeout_seconds: None)

    source._fetch_rendered_html(
        "https://kwork.ru/projects?c=11",
        "http://127.0.0.1:9222",
        30,
    )

    methods = [method for method, _ in calls]
    assert "Page.navigate" in methods
    assert methods.index("Page.navigate") < methods.index("Runtime.evaluate")


def test_kwork_fresh_location_accepts_view_redirect_and_cache_strip():
    import app.kwork_source as source

    assert source._is_same_kwork_page(
        "https://kwork.ru/projects/3187247?_lf_refresh=1",
        "https://kwork.ru/projects/3187247/view",
    )


def test_find_or_create_page_does_not_reuse_list_tab_for_project(monkeypatch):
    import websocket
    import app.kwork_source as source

    calls = []

    class FakeWebSocket:
        def close(self):
            pass

    def fake_send_cdp(ws, method, params):
        calls.append((method, params))
        return {}

    lists = [
        [
            {
                "type": "page",
                "url": "https://kwork.ru/projects?c=11",
                "webSocketDebuggerUrl": "ws://list",
            }
        ],
        [
            {
                "type": "page",
                "url": "https://kwork.ru/projects?c=11",
                "webSocketDebuggerUrl": "ws://list",
            },
            {
                "type": "page",
                "url": "https://kwork.ru/projects/3187247/view",
                "webSocketDebuggerUrl": "ws://project",
            },
        ],
    ]

    def fake_cdp_json(cdp_url, path, timeout):
        if path == "/json/list":
            return lists.pop(0) if lists else lists[-1]
        if path == "/json/version":
            return {"webSocketDebuggerUrl": "ws://browser"}
        return None

    monkeypatch.setattr(
        source,
        "_cdp_json",
        fake_cdp_json,
    )
    monkeypatch.setattr(websocket, "create_connection", lambda url, timeout=10: FakeWebSocket())
    monkeypatch.setattr(source, "_send_cdp", fake_send_cdp)

    page = source._find_or_create_page(
        "http://127.0.0.1:9222",
        "https://kwork.ru/projects/3187247/view",
        tab_kind="project",
    )

    assert page["webSocketDebuggerUrl"] == "ws://project"
    assert calls == [("Target.createTarget", {"url": "https://kwork.ru/projects/3187247/view"})]


def test_find_or_create_page_reuses_list_tab_for_list(monkeypatch):
    import app.kwork_source as source

    monkeypatch.setattr(
        source,
        "_cdp_json",
        lambda cdp_url, path, timeout: [
            {
                "type": "page",
                "url": "https://kwork.ru/projects?c=11",
                "webSocketDebuggerUrl": "ws://list",
            }
        ]
        if path == "/json/list"
        else None,
    )

    page = source._find_or_create_page(
        "http://127.0.0.1:9222",
        "https://kwork.ru/projects?c=11",
        tab_kind="list",
    )

    assert page["webSocketDebuggerUrl"] == "ws://list"


def test_default_chrome_user_data_dir_uses_kwork_bot_profile(monkeypatch, tmp_path):
    import app.kwork_source as source

    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))

    assert source._chrome_user_data_dir() == str(tmp_path / "KworkLeadChromeUserData")


def test_kwork_web_project_ids_deduplicate_through_storage(tmp_path, monkeypatch):
    from app.main import scan_once
    from app.ai_lead_judge import LeadJudgeResult
    from app.storage import Storage

    judge_calls = []

    def fake_judge(text, api_key="", model="deepseek-chat"):
        judge_calls.append(text)
        return LeadJudgeResult(
            accepted=True,
            decision="accept",
            score=80,
            complexity="simple",
            estimated_days=1,
            price_rub=5000,
            summary="Проект",
            reasons=["подходит"],
            risks=[],
            questions=[],
            draft_reply="AI reply",
        )

    class FakeSource:
        def fetch_recent_posts(self):
            return parse_kwork_project_cards(
                """
                <div class="want-card">
                  <a href="/projects/123/view">Проект</a>
                  <span>Предложений: 1</span>
                </div>
                """,
                max_responses=5,
            )

        def send_message(self, contact, text):
            raise AssertionError("not used")

    class FakeEmail:
        def __init__(self):
            self.sent = []

        def send_lead(self, lead):
            self.sent.append(lead.id)
            return f"<lead-{lead.id}@example.com>"

    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    email = FakeEmail()

    assert scan_once(storage, FakeSource(), email, deepseek_api_key="sk-test", lead_judge=fake_judge) == 1
    assert scan_once(storage, FakeSource(), email, deepseek_api_key="sk-test", lead_judge=fake_judge) == 0
    assert len(storage.list_leads()) == 1
    assert email.sent == [1]
    assert len(judge_calls) == 1


def test_kwork_web_source_can_send_when_replies_enabled(monkeypatch):
    import app.kwork_source as source

    sent = []

    class FakeSender:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def send_message(self, contact, text):
            sent.append((contact, text, self.kwargs["cdp_url"]))
            return "kwork-project-123"

    monkeypatch.setattr(source, "KworkReplySender", FakeSender)
    client = source.KworkWebSource(
        enable_replies=True,
        cdp_url="http://127.0.0.1:9222",
    )

    assert client.can_send_replies is True
    assert client.send_message("https://kwork.ru/projects/123/view", "Здравствуйте!") == "kwork-project-123"
    assert sent == [
        ("https://kwork.ru/projects/123/view", "Здравствуйте!", "http://127.0.0.1:9222")
    ]


def test_kwork_web_source_stays_read_only_when_replies_disabled():
    import pytest
    import app.kwork_source as source

    client = source.KworkWebSource(enable_replies=False)

    assert client.can_send_replies is False
    with pytest.raises(RuntimeError, match="read-only"):
        client.send_message("https://kwork.ru/projects/123/view", "Здравствуйте!")
