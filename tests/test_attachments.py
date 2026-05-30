from app.attachments import build_attachment_context, parse_attachment


def test_parse_attachment_splits_label_and_url():
    parsed = parse_attachment("ТЗ.pdf: https://kwork.ru/files/tz.pdf")

    assert parsed.label == "ТЗ.pdf"
    assert parsed.url == "https://kwork.ru/files/tz.pdf"


def test_build_attachment_context_reads_text_attachment(monkeypatch):
    monkeypatch.setattr(
        "app.attachments.download_attachment",
        lambda url, cookie="", max_bytes=2_000_000: b"brief text from customer",
    )

    context = build_attachment_context(
        ("ТЗ.txt: https://kwork.ru/files/tz.txt",),
        cookie="",
    )

    assert "ТЗ.txt" in context
    assert "brief text from customer" in context


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
    assert "OCR" in context
