import io
import zipfile

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

    assert "ФАЙЛЫ/ТЗ" in context
    assert "ТЗ.txt" in context
    assert "прочитан" in context
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
