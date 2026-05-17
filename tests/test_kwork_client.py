from app.kwork_client import KworkProjectClient, parse_kwork_project_html


def test_parse_kwork_project_html_extracts_worker_count_and_meta():
    html = """
    <html>
      <head>
        <title>Правки на сайте WP - Kwork</title>
        <meta name="description" content="Нужно поправить форму и адаптив">
      </head>
      <script>
        window.stateData={"workerCount":4,"pageName":"view_project"};
      </script>
    </html>
    """

    result = parse_kwork_project_html("https://kwork.ru/projects/1", html)

    assert result.response_count == 4
    assert result.title == "Правки на сайте WP"
    assert result.description == "Нужно поправить форму и адаптив"
    assert result.reason == ""


def test_parse_kwork_project_html_reports_missing_worker_count():
    result = parse_kwork_project_html("https://kwork.ru/projects/1", "<html></html>")

    assert result.response_count is None
    assert "workerCount" in result.reason


def test_kwork_client_rejects_non_kwork_links_without_fetching():
    client = KworkProjectClient()

    result = client.inspect("https://example.com/order")

    assert result.response_count is None
    assert "не Kwork" in result.reason
