from datetime import datetime, timedelta, timezone

import pytest

from app.kwork_source import KworkWebSource, parse_kwork_project_cards


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


def test_rendered_cards_without_publication_time_are_skipped_when_freshness_filter_is_on():
    html = """
    <div class="want-card">
      <a class="want-card__title" href="/projects/3177548/view">Старый активный заказ</a>
      <div class="want-card__informers-row"><span>Предложений: 1</span></div>
    </div>
    """

    posts = parse_kwork_project_cards(html, max_responses=5, max_age_hours=24)

    assert posts == []


def test_parse_kwork_project_cards_skips_cards_without_offer_count():
    html = """
    <div class="want-card">
      <a href="/projects/1/view">Без счетчика</a>
    </div>
    """

    assert parse_kwork_project_cards(html, max_responses=5) == []


def test_parse_kwork_project_cards_uses_embedded_wants_without_treating_kwork_count_as_offers():
    html = """
    <script>
      window.pageState = {
        "wantsListData": {
          "pagination": {
            "data": [
              {
                "id": 3219001,
                "name": "Старый лендинг",
                "description": "Нужно поправить HTML и CSS",
                "date_create": "2026-07-17 20:05:00",
                "timeLeft": "2 д. 20 ч.",
                "status": "active",
                "isWantActive": true,
                "kwork_count": 27
              },
              {
                "id": 3219002,
                "name": "Свежая форма заявки",
                "description": "Исправить форму на WordPress",
                "date_create": "2026-07-17 23:50:00",
                "timeLeft": "2 д. 23 ч.",
                "status": "active",
                "isWantActive": true,
                "kwork_count": 1
              },
              {
                "id": 3219003,
                "name": "Закрытый заказ",
                "description": "Не должен попасть в ленту",
                "date_create": "2026-07-17 23:55:00",
                "timeLeft": "",
                "status": "closed",
                "isWantActive": false,
                "kwork_count": 1
              }
            ]
          }
        }
      };
    </script>
    """

    posts = parse_kwork_project_cards(html, max_responses=5)

    assert [post.message_id for post in posts] == [3219002, 3219001]
    assert posts[0].posted_at == "2026-07-17 23:50:00"
    assert "Свежая форма заявки" in posts[0].text
    assert "Осталось: 2 д. 23 ч." in posts[0].text
    assert "Предложений:" not in posts[0].text
    assert "27" not in posts[1].text


def test_kwork_web_source_uses_embedded_direct_html_without_waiting_for_browser_cards(monkeypatch):
    import app.kwork_source as source

    fresh_created = (datetime.now() - timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M:%S")
    html = """
    <script>
      window.pageState = {
        "wantsListData": {
          "pagination": {
            "data": [
              {
                "id": 3219004,
                "name": "Правки лендинга",
                "description": "Нужно поправить адаптив",
                "date_create": "__FRESH_CREATED__",
                "timeLeft": "2 д. 23 ч.",
                "status": "active",
                "isWantActive": true
              }
            ]
          }
        }
      };
    </script>
    """.replace("__FRESH_CREATED__", fresh_created)
    monkeypatch.setattr(source, "_fetch_html", lambda *args, **kwargs: html)
    monkeypatch.setattr(
        source,
        "_fetch_rendered_html",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("browser fallback must not run")),
    )

    posts = KworkWebSource(use_browser=True).fetch_recent_posts()

    assert [post.message_id for post in posts] == [3219004]


def test_embedded_kwork_projects_skip_old_active_cards():
    now = datetime(2026, 7, 18, 1, 30, tzinfo=timezone(timedelta(hours=3)))
    html = """
    <script>
      window.pageState = {
        "wantsListData": {
          "pagination": {
            "data": [
              {
                "id": 3219005,
                "name": "Свежая правка формы",
                "description": "Починить форму заявки",
                "date_create": "2026-07-17 23:40:00",
                "status": "active",
                "isWantActive": true
              },
              {
                "id": 3020909,
                "name": "Старый зависший заказ",
                "description": "Не должен попасть в подборку",
                "date_create": "2025-11-16 03:46:06",
                "status": "active",
                "isWantActive": true
              }
            ]
          }
        }
      };
    </script>
    """

    posts = parse_kwork_project_cards(html, max_responses=5, max_age_hours=24, now=now)

    assert [post.message_id for post in posts] == [3219005]


def test_embedded_freshness_wins_over_rendered_cards_when_both_are_present():
    now = datetime(2026, 7, 18, 1, 30, tzinfo=timezone(timedelta(hours=3)))
    html = """
    <div class="want-card">
      <a href="/projects/3020909/view">Старый проект из отрисованной карточки</a>
      <span>Предложений: 1</span>
    </div>
    <script>
      window.pageState = {
        "wantsListData": {
          "pagination": {
            "data": [
              {
                "id": 3219006,
                "name": "Свежая правка формы",
                "description": "Починить отправку заявки",
                "date_create": "2026-07-17 23:40:00",
                "status": "active",
                "isWantActive": true
              },
              {
                "id": 3020909,
                "name": "Старый зависший заказ",
                "description": "Не должен попасть в подборку",
                "date_create": "2025-11-16 03:46:06",
                "status": "active",
                "isWantActive": true
              }
            ]
          }
        }
      };
    </script>
    """

    posts = parse_kwork_project_cards(html, max_responses=5, max_age_hours=24, now=now)

    assert [post.message_id for post in posts] == [3219006]


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


def test_kwork_project_redirect_to_list_fails_without_waiting_for_timeout(monkeypatch):
    import app.kwork_source as source

    times = iter((0.0, 0.0, 1.0))
    monkeypatch.setattr(source.time, "monotonic", lambda: next(times))
    monkeypatch.setattr(source.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(source, "_evaluate", lambda _ws, _expression: "https://kwork.ru/projects")

    with pytest.raises(RuntimeError, match="redirected to the list"):
        source._wait_for_location(object(), "https://kwork.ru/projects/3187247/view", timeout_seconds=0.5)


def test_kwork_project_tab_accepts_new_offer_page():
    import app.kwork_source as source

    assert source._is_kwork_project_tab("https://kwork.ru/new_offer?project=3187247")


def test_project_inspection_does_not_reuse_unsent_offer_tab(monkeypatch):
    import websocket
    import app.kwork_source as source

    calls = []

    class FakeWebSocket:
        def close(self):
            return None

    pages = [
        [
            {
                "type": "page",
                "url": "https://kwork.ru/new_offer?project=3187247",
                "webSocketDebuggerUrl": "ws://offer",
            }
        ],
        [
            {
                "type": "page",
                "url": "https://kwork.ru/new_offer?project=3187247",
                "webSocketDebuggerUrl": "ws://offer",
            },
            {
                "type": "page",
                "url": "https://kwork.ru/projects/3187248/view",
                "webSocketDebuggerUrl": "ws://inspection",
            },
        ],
    ]

    def fake_cdp_json(_cdp_url, path, timeout):
        if path == "/json/list":
            return pages.pop(0) if pages else []
        if path == "/json/version":
            return {"webSocketDebuggerUrl": "ws://browser"}
        return None

    monkeypatch.setattr(source, "_cdp_json", fake_cdp_json)
    monkeypatch.setattr(websocket, "create_connection", lambda *_args, **_kwargs: FakeWebSocket())
    monkeypatch.setattr(source, "_send_cdp", lambda _ws, method, params: calls.append((method, params)) or {})

    page = source._find_or_create_page(
        "http://127.0.0.1:9222",
        "https://kwork.ru/projects/3187248/view",
        tab_kind="inspection",
    )

    assert page["webSocketDebuggerUrl"] == "ws://inspection"
    assert calls == [("Target.createTarget", {"url": "https://kwork.ru/projects/3187248/view"})]


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


def test_find_or_create_login_page_waits_for_created_target_not_existing_list_tab(monkeypatch):
    import websocket
    import app.kwork_source as source

    class FakeWebSocket:
        def close(self):
            return None

    page_lists = iter(
        [
            [
                {
                    "id": "list-target",
                    "type": "page",
                    "url": "https://kwork.ru/projects",
                    "webSocketDebuggerUrl": "ws://list",
                }
            ],
            [
                {
                    "id": "list-target",
                    "type": "page",
                    "url": "https://kwork.ru/projects",
                    "webSocketDebuggerUrl": "ws://list",
                },
                {
                    "id": "login-target",
                    "type": "page",
                    "url": "https://kwork.ru/seller",
                    "webSocketDebuggerUrl": "ws://login",
                },
            ],
        ]
    )

    def fake_cdp_json(_cdp_url, path, timeout):
        if path == "/json/list":
            return next(page_lists)
        if path == "/json/version":
            return {"webSocketDebuggerUrl": "ws://browser"}
        return None

    monkeypatch.setattr(source, "_cdp_json", fake_cdp_json)
    monkeypatch.setattr(websocket, "create_connection", lambda *_args, **_kwargs: FakeWebSocket())
    monkeypatch.setattr(
        source,
        "_send_cdp",
        lambda _ws, method, _params: {"result": {"targetId": "login-target"}} if method == "Target.createTarget" else {},
    )

    page = source._find_or_create_page(
        "http://127.0.0.1:9222",
        "https://kwork.ru/login",
        tab_kind="login",
    )

    assert page["webSocketDebuggerUrl"] == "ws://login"


def test_fetch_rendered_project_html_waits_for_body_text(monkeypatch):
    import websocket
    import app.kwork_client as client

    calls = []
    text_reads = iter(["", "Создание сайта\nПредложений: 3"])

    class FakeWebSocket:
        def close(self):
            calls.append("close")

    def fake_evaluate(ws, expression):
        if expression == "document.body && document.body.innerText":
            return next(text_reads)
        if "JSON.stringify" in expression:
            return '{"html":"<html></html>","text":"Создание сайта\\nПредложений: 3","links":[]}'
        return ""

    monkeypatch.setattr(client, "_fetch_project_html", lambda *args, **kwargs: "")
    monkeypatch.setattr("app.kwork_source._ensure_chrome_cdp", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        "app.kwork_source._find_or_create_page",
        lambda *args, **kwargs: {"webSocketDebuggerUrl": "ws://project"},
    )
    monkeypatch.setattr("app.kwork_source._refresh_page", lambda *args, **kwargs: None)
    monkeypatch.setattr("app.kwork_source._evaluate", fake_evaluate)
    monkeypatch.setattr(websocket, "create_connection", lambda url, timeout=20: FakeWebSocket())

    info = client.KworkProjectClient(use_browser=True).inspect("https://kwork.ru/projects/123/view")

    assert info.response_count == 3


def test_fetch_rendered_project_html_waits_for_offer_count_after_page_header(monkeypatch):
    import websocket
    import app.kwork_client as client

    text_reads = iter(
        [
            (
                "Страница проекта уже открыта. Описание задачи и данные заказчика загружены, "
                "но блок с откликами еще не отрисован после загрузки интерфейса Kwork."
            ),
            "Страница проекта\nПредложений: 3",
        ]
    )
    state = {"offer_count_ready": False}

    class FakeWebSocket:
        def close(self):
            return None

    def fake_evaluate(ws, expression):
        if expression == "document.body && document.body.innerText":
            text = next(text_reads)
            state["offer_count_ready"] = "Предложений" in text
            return text
        if "JSON.stringify" in expression:
            text = "Страница проекта\\nПредложений: 3" if state["offer_count_ready"] else "Страница проекта"
            return '{"html":"<html></html>","text":"' + text + '","links":[]}'
        return ""

    monkeypatch.setattr(client, "_fetch_project_html", lambda *args, **kwargs: "")
    monkeypatch.setattr(client.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr("app.kwork_source._ensure_chrome_cdp", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        "app.kwork_source._find_or_create_page",
        lambda *args, **kwargs: {"webSocketDebuggerUrl": "ws://project"},
    )
    monkeypatch.setattr("app.kwork_source._refresh_page", lambda *args, **kwargs: None)
    monkeypatch.setattr("app.kwork_source._evaluate", fake_evaluate)
    monkeypatch.setattr(websocket, "create_connection", lambda url, timeout=20: FakeWebSocket())

    info = client.KworkProjectClient(use_browser=True).inspect("https://kwork.ru/projects/123/view")

    assert info.response_count == 3


def test_cdp_evaluate_waits_for_async_kwork_form_updates(monkeypatch):
    import app.kwork_source as source

    captured = {}

    class FakeWebSocket:
        def send(self, payload):
            captured["payload"] = payload

        def recv(self):
            return '{"id": 1, "result": {"result": {"value": "ok"}}}'

    source._send_cdp.counter = 0

    assert source._evaluate(FakeWebSocket(), "Promise.resolve('ok')") == "ok"
    assert '"awaitPromise": true' in captured["payload"]


def test_default_chrome_user_data_dir_uses_kwork_bot_profile(monkeypatch, tmp_path):
    import app.kwork_source as source

    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))

    assert source._chrome_user_data_dir() == str(tmp_path / "KworkLeadChromeUserData")


def test_kwork_web_project_ids_deduplicate_through_storage(tmp_path, monkeypatch):
    from app.main import scan_once
    from app.ai_lead_judge import LeadJudgeResult
    from app.storage import Storage

    judge_calls = []

    def fake_judge(text, api_key="", model="deepseek-chat", **kwargs):
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
        last_kwargs = {}

        def __init__(self, **kwargs):
            self.kwargs = kwargs
            FakeSender.last_kwargs = kwargs

        def send_message(self, contact, text, *, price_rub=None, days=None, title=""):
            sent.append((contact, text, price_rub, days, title, self.kwargs["cdp_url"]))
            return "kwork-project-123"

    monkeypatch.setattr(source, "KworkReplySender", FakeSender)
    client = source.KworkWebSource(
        enable_replies=True,
        cdp_url="http://127.0.0.1:9222",
        login_email="bot@example.com",
        login_password="secret",
    )

    assert client.can_send_replies is True
    assert client.send_message(
        "https://kwork.ru/projects/123/view",
        "Здравствуйте!",
        price_rub=3000,
        days=3,
        title="Название заказа",
    ) == "kwork-project-123"
    assert sent == [
        (
            "https://kwork.ru/projects/123/view",
            "Здравствуйте!",
            3000,
            3,
            "Название заказа",
            "http://127.0.0.1:9222",
        )
    ]
    assert FakeSender.last_kwargs["login_email"] == "bot@example.com"
    assert FakeSender.last_kwargs["login_password"] == "secret"
    assert FakeSender.last_kwargs["max_responses"] == 5


def test_kwork_web_source_stays_read_only_when_replies_disabled():
    import pytest
    import app.kwork_source as source

    client = source.KworkWebSource(enable_replies=False)

    assert client.can_send_replies is False
    with pytest.raises(RuntimeError, match="read-only"):
        client.send_message("https://kwork.ru/projects/123/view", "Здравствуйте!")
