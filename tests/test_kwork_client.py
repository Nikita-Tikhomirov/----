import pytest

from app.kwork_client import (
    KworkProjectClient,
    KworkProjectInfo,
    KworkProjectReplyabilityError,
    ensure_project_is_replyable,
    parse_kwork_project_html,
)


def test_parse_kwork_project_html_extracts_visible_offer_count_and_meta():
    html = """
    <html>
      <head>
        <title>Правки на сайте WP - Kwork</title>
        <meta name="description" content="Нужно поправить форму и адаптив">
      </head>
      <div class="want-card__informers-row">
        <span>Осталось: 2 д. 17 ч.</span>
        <span>Предложений:&nbsp;4</span>
      </div>
    </html>
    """

    result = parse_kwork_project_html("https://kwork.ru/projects/1", html)

    assert result.response_count == 4
    assert result.title == "Правки на сайте WP"
    assert result.description == "Нужно поправить форму и адаптив"
    assert "Правки на сайте WP" in result.page_text
    assert result.reason == ""


def test_parse_kwork_project_html_handles_line_breaks_inside_offer_count():
    html = """
    <div class="want-card__informers-row">
      <span>
        Предложений:&nbsp;27
      </span>
    </div>
    """

    result = parse_kwork_project_html("https://kwork.ru/projects/1", html)

    assert result.response_count == 27


def test_parse_kwork_project_html_does_not_use_worker_count_as_offer_count():
    html = '<script>window.stateData={"workerCount":0,"pageName":"view_project"};</script>'

    result = parse_kwork_project_html("https://kwork.ru/projects/1", "<html></html>")

    assert result.response_count is None
    assert "Предложений" in result.reason

    result_with_worker_count = parse_kwork_project_html("https://kwork.ru/projects/1", html)
    assert result_with_worker_count.response_count is None
    assert "Предложений" in result_with_worker_count.reason


def test_parse_kwork_project_html_detects_unavailable_project_page():
    html = """
    <html>
      <head><title>Страница не найдена</title></head>
      <body><h1>СТРАНИЦА НЕ НАЙДЕНА</h1></body>
    </html>
    """

    result = parse_kwork_project_html("https://kwork.ru/projects/1", html)

    assert result.response_count is None
    assert result.is_unavailable is True
    assert "unavailable" in result.reason.lower()


def test_kwork_client_rejects_non_kwork_links_without_fetching():
    client = KworkProjectClient()

    result = client.inspect("https://example.com/order")

    assert result.response_count is None
    assert "не Kwork" in result.reason


def test_kwork_client_retries_private_project_after_browser_auto_login(monkeypatch):
    import app.kwork_client as client_module

    fetch_attempts = []
    login_attempts = []

    def fetch_rendered(*_args, **_kwargs):
        fetch_attempts.append(True)
        if len(fetch_attempts) == 1:
            raise RuntimeError("Kwork page did not navigate to fresh URL; last location=https://kwork.ru/projects")
        return "<title>Лендинг - Kwork</title><div>Предложений: 3</div>"

    monkeypatch.setattr(client_module, "_fetch_rendered_project_html", fetch_rendered)
    monkeypatch.setattr(client_module, "_fetch_project_html", lambda *_args, **_kwargs: "")
    monkeypatch.setattr(
        KworkProjectClient,
        "_ensure_browser_login",
        lambda self: login_attempts.append((self.login_email, self.login_password)),
        raising=False,
    )

    client = KworkProjectClient(
        use_browser=True,
        login_email="bot@example.com",
        login_password="secret",
    )

    result = client.inspect("https://kwork.ru/projects/123/view")

    assert result.response_count == 3
    assert len(fetch_attempts) == 2
    assert login_attempts == [("bot@example.com", "secret")]


def test_replyability_accepts_project_at_response_limit():
    info = KworkProjectInfo(
        url="https://kwork.ru/projects/1/view",
        response_count=5,
        title="Лендинг",
        description="",
    )

    assert ensure_project_is_replyable(info, max_responses=5) is info


def test_replyability_rejects_project_above_live_response_limit():
    info = KworkProjectInfo(
        url="https://kwork.ru/projects/1/view",
        response_count=7,
        title="Лендинг",
        description="",
    )

    with pytest.raises(KworkProjectReplyabilityError, match=r"7.*5"):
        ensure_project_is_replyable(info, max_responses=5)


def test_replyability_rejects_unavailable_or_unreadable_project():
    unavailable = KworkProjectInfo(
        url="https://kwork.ru/projects/1/view",
        response_count=None,
        title="",
        description="",
        reason="Kwork project is unavailable: page not found, closed, or removed.",
    )
    unreadable = KworkProjectInfo(
        url="https://kwork.ru/projects/2/view",
        response_count=None,
        title="",
        description="",
        reason="на странице не найдено поле 'Предложений'",
    )

    with pytest.raises(KworkProjectReplyabilityError, match="unavailable"):
        ensure_project_is_replyable(unavailable, max_responses=5)
    with pytest.raises(KworkProjectReplyabilityError, match="response count is unavailable"):
        ensure_project_is_replyable(unreadable, max_responses=5)


def test_parse_kwork_project_html_extracts_attachments():
    html = """
    <html>
      <body>
        <a href="https://kwork.ru/files/upload/task.pdf">Техническое задание.pdf</a>
        <a href="/files/upload/screen.png">screen.png</a>
      </body>
    </html>
    """

    result = parse_kwork_project_html("https://kwork.ru/projects/1", html)

    assert "Техническое задание.pdf" in result.attachments[0]
    assert "screen.png" in result.attachments[1]


def test_parse_kwork_project_html_extracts_actionable_facts():
    html = """
    <html>
      <head><title>Верстка лендинга - Kwork</title></head>
      <body>
        <h1>Верстка лендинга</h1>
        <div>Бюджет: до 15 000 ₽</div>
        <div>Осталось: 2 д. 17 ч.</div>
        <div>Предложений:&nbsp;4</div>
        <div>Покупатель: nikita_dev</div>
        <div>Наймов: 73%</div>
      </body>
    </html>
    """

    result = parse_kwork_project_html("https://kwork.ru/projects/1", html)

    assert "Бюджет: до 15 000 ₽" in result.facts
    assert "Осталось: 2 д. 17 ч." in result.facts
    assert "Предложений: 4" in result.facts
    assert "Покупатель: nikita_dev" in result.facts
    assert "Наймов: 73%" in result.facts
