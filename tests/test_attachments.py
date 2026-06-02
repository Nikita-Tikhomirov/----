import io
import zipfile

from app.attachments import build_attachment_context, parse_attachment
from app.attachments import _cookie_header_from_cdp_cookies


def test_parse_attachment_splits_label_and_url():
    parsed = parse_attachment("ТЗ.pdf: https://kwork.ru/files/tz.pdf")

    assert parsed.label == "ТЗ.pdf"
    assert parsed.url == "https://kwork.ru/files/tz.pdf"


def test_parse_attachment_strips_html_label():
    parsed = parse_attachment(
        '<i class="files-list__icon"></i> <span class="ml10 nowrap">профтест (28).docx</span>: '
        "https://kwork.ru/files/tz.docx"
    )

    assert parsed.label == "профтест (28).docx"


def test_cookie_header_from_cdp_cookies_keeps_matching_domains():
    header = _cookie_header_from_cdp_cookies(
        [
            {"name": "sid", "value": "abc", "domain": ".kwork.ru"},
            {"name": "theme", "value": "dark", "domain": "kwork.ru"},
            {"name": "foreign", "value": "skip", "domain": "example.com"},
        ],
        "https://kwork.ru/files/uploaded/tz.docx",
    )

    assert header == "sid=abc; theme=dark"


def test_build_attachment_context_reads_text_attachment(monkeypatch):
    monkeypatch.setattr(
        "app.attachments.download_attachment",
        lambda url, cookie="", max_bytes=2_000_000: b"brief text from customer",
    )

    context = build_attachment_context(
        ("ТЗ.txt: https://kwork.ru/files/tz.txt",),
        cookie="",
    )

    assert "ФАЙЛЫ/ТЗ" in context
    assert "ТЗ.txt" in context
    assert "прочитан" in context
    assert "brief text from customer" in context


def test_build_attachment_context_can_download_with_browser_session(monkeypatch):
    direct_calls = []
    browser_calls = []

    def fake_direct(url, cookie="", max_bytes=2_000_000):
        direct_calls.append(url)
        raise PermissionError("HTTP Error 403: Forbidden")

    def fake_browser(url, cdp_url, browser_profile_dir="", max_bytes=2_000_000):
        browser_calls.append((url, cdp_url))
        return b"private brief from logged account"

    monkeypatch.setattr("app.attachments.download_attachment", fake_direct)
    monkeypatch.setattr("app.attachments.download_attachment_via_browser", fake_browser)

    context = build_attachment_context(
        ("private.txt: https://kwork.ru/files/private.txt",),
        use_browser=True,
        cdp_url="http://127.0.0.1:9222",
    )

    assert direct_calls == ["https://kwork.ru/files/private.txt"]
    assert browser_calls == [("https://kwork.ru/files/private.txt", "http://127.0.0.1:9222")]
    assert "private brief from logged account" in context


def test_build_attachment_context_retries_docx_when_direct_download_is_html(monkeypatch):
    direct_calls = []
    browser_calls = []
    docx_bytes = _docx_bytes("Нужно сверстать страницу профтеста и форму заявки")

    def fake_direct(url, cookie="", max_bytes=2_000_000):
        direct_calls.append(url)
        return b"<!doctype html><html><body>login required</body></html>"

    def fake_browser(url, cdp_url, browser_profile_dir="", max_bytes=2_000_000):
        browser_calls.append(url)
        return docx_bytes

    monkeypatch.setattr("app.attachments.download_attachment", fake_direct)
    monkeypatch.setattr("app.attachments.download_attachment_via_browser", fake_browser)

    context = build_attachment_context(
        ("профтест (28).docx: https://kwork.ru/files/uploaded/tz.docx",),
        use_browser=True,
    )

    assert direct_calls == ["https://kwork.ru/files/uploaded/tz.docx"]
    assert browser_calls == ["https://kwork.ru/files/uploaded/tz.docx"]
    assert "Статус: скачан, прочитан" in context
    assert "Нужно сверстать страницу профтеста" in context


def test_build_attachment_context_reports_html_instead_of_docx_without_browser(monkeypatch):
    monkeypatch.setattr(
        "app.attachments.download_attachment",
        lambda url, cookie="", max_bytes=2_000_000: b"<html><body>login required</body></html>",
    )

    context = build_attachment_context(
        ("tz.docx: https://kwork.ru/files/tz.docx",),
        use_browser=False,
    )

    assert "Статус: не скачан" in context
    assert "HTML-страницу вместо файла" in context
    assert "File is not a zip file" not in context


def test_build_attachment_context_reports_unsupported_images(monkeypatch):
    monkeypatch.setattr(
        "app.attachments.download_attachment",
        lambda url, cookie="", max_bytes=2_000_000: b"fake image",
    )

    context = build_attachment_context(
        ("screen.png: https://kwork.ru/files/screen.png",),
        cookie="",
    )

    assert "screen.png" in context
    assert "OCR не выполнен" in context


def test_build_attachment_context_reads_image_with_tesseract(monkeypatch):
    monkeypatch.setattr(
        "app.attachments.download_attachment",
        lambda url, cookie="", max_bytes=2_000_000: b"fake image",
    )
    monkeypatch.setattr(
        "app.attachments._run_tesseract_ocr",
        lambda content, ext: "На скрине форма заявки и калькулятор",
        raising=False,
    )

    context = build_attachment_context(
        ("screen.png: https://kwork.ru/files/screen.png",),
        cookie="",
    )

    assert "Статус: скачан, OCR прочитан" in context
    assert "На скрине форма заявки" in context


def test_build_attachment_context_retries_image_when_direct_download_is_html(monkeypatch):
    browser_calls = []

    monkeypatch.setattr(
        "app.attachments.download_attachment",
        lambda url, cookie="", max_bytes=2_000_000: b"<!doctype html><html><body>login required</body></html>",
    )

    def fake_browser(url, cdp_url, browser_profile_dir="", max_bytes=2_000_000):
        browser_calls.append(url)
        return b"\x89PNG\r\n\x1a\nfake png bytes"

    monkeypatch.setattr("app.attachments.download_attachment_via_browser", fake_browser)
    monkeypatch.setattr(
        "app.attachments._run_tesseract_ocr",
        lambda content, ext: "На скриншоте показан макет главной страницы",
        raising=False,
    )

    context = build_attachment_context(
        ("screen.png: https://kwork.ru/files/screen.png",),
        use_browser=True,
    )

    assert browser_calls == ["https://kwork.ru/files/screen.png"]
    assert "Статус: скачан, OCR прочитан" in context
    assert "макет главной страницы" in context


def test_build_attachment_context_opens_zip_and_reads_inner_text(monkeypatch):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("brief.txt", "Нужно сверстать лендинг и форму")

    monkeypatch.setattr(
        "app.attachments.download_attachment",
        lambda url, cookie="", max_bytes=2_000_000: buffer.getvalue(),
    )

    context = build_attachment_context(
        ("tz.zip: https://kwork.ru/files/tz.zip",),
        cookie="",
    )

    assert "tz.zip" in context
    assert "Статус: скачан, архив открыт" in context
    assert "brief.txt: прочитан" in context
    assert "Нужно сверстать лендинг" in context


def _docx_bytes(text: str) -> bytes:
    from docx import Document

    document = Document()
    document.add_paragraph(text)
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()
