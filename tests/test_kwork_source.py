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
        lambda cdp_url, url: {"webSocketDebuggerUrl": "ws://fake"},
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


def test_find_or_create_page_reuses_existing_kwork_tab_for_project(monkeypatch):
    import app.kwork_source as source

    monkeypatch.setattr(
        source,
        "_cdp_json",
        lambda cdp_url, path, timeout: [
            {
                "type": "page",
                "url": "https://kwork.ru/projects?c=11",
                "webSocketDebuggerUrl": "ws://existing",
            }
        ]
        if path == "/json/list"
        else None,
    )

    page = source._find_or_create_page("http://127.0.0.1:9222", "https://kwork.ru/projects/3187247/view")

    assert page["webSocketDebuggerUrl"] == "ws://existing"


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
