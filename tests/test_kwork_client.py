from app.kwork_client import KworkProjectClient, parse_kwork_project_html


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


def test_kwork_client_rejects_non_kwork_links_without_fetching():
    client = KworkProjectClient()

    result = client.inspect("https://example.com/order")

    assert result.response_count is None
    assert "не Kwork" in result.reason
