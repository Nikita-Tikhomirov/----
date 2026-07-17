import io
import zipfile
from pathlib import Path

import pytest

from app.attachments import ArchiveSelection, build_attachment_context, build_attachment_report, parse_attachment
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


def test_build_attachment_context_smart_mode_combines_ocr_and_vision(monkeypatch):
    monkeypatch.setattr(
        "app.attachments.download_attachment",
        lambda url, cookie="", max_bytes=2_000_000: b"fake image",
    )
    monkeypatch.setattr(
        "app.attachments._run_tesseract_ocr",
        lambda content, ext: "На скрине форма заявки и кнопка отправки.",
        raising=False,
    )
    monkeypatch.setattr(
        "app.attachments.describe_image_with_openrouter",
        lambda content, extension, api_key, model, base_url, timeout_seconds=45.0: (
            "На экране форма в первом блоке лендинга, кнопка должна оставаться видимой на мобильных."
        ),
        raising=False,
    )

    context = build_attachment_context(
        ("screen.png: https://kwork.ru/files/screen.png",),
        openrouter_api_key="or-test-key",
        openrouter_vision_model="provider/vision-model",
        openrouter_vision_mode="smart",
    )

    assert "Статус: скачан, OCR + vision прочитан" in context
    assert "OCR: На скрине форма заявки" in context
    assert "Vision: На экране форма" in context


def test_build_attachment_context_uses_openrouter_vision_when_ocr_has_no_text(monkeypatch):
    monkeypatch.setattr(
        "app.attachments.download_attachment",
        lambda url, cookie="", max_bytes=2_000_000: b"fake image",
    )
    monkeypatch.setattr(
        "app.attachments._run_tesseract_ocr",
        lambda content, ext: "",
    )
    monkeypatch.setattr(
        "app.attachments.describe_image_with_openrouter",
        lambda content, extension, api_key, model, base_url, timeout_seconds=45.0: "На макете видны форма заявки и блок тарифов.",
        raising=False,
    )

    context = build_attachment_context(
        ("screen.png: https://kwork.ru/files/screen.png",),
        openrouter_api_key="or-test-key",
        openrouter_vision_model="provider/vision-model",
    )

    assert "Статус: скачан, vision прочитан" in context
    assert "форма заявки и блок тарифов" in context


def test_build_attachment_context_off_mode_never_calls_openrouter_vision(monkeypatch):
    monkeypatch.setattr(
        "app.attachments.download_attachment",
        lambda url, cookie="", max_bytes=2_000_000: b"fake image",
    )
    monkeypatch.setattr("app.attachments._run_tesseract_ocr", lambda content, ext: "", raising=False)

    def fail_vision(*args, **kwargs):
        raise AssertionError("vision must stay disabled")

    monkeypatch.setattr("app.attachments.describe_image_with_openrouter", fail_vision, raising=False)

    context = build_attachment_context(
        ("screen.png: https://kwork.ru/files/screen.png",),
        openrouter_api_key="or-test-key",
        openrouter_vision_model="provider/vision-model",
        openrouter_vision_mode="off",
    )

    assert "Статус: скачан, OCR не выполнен" in context


def test_build_attachment_context_uses_openrouter_vision_for_docx_without_text(monkeypatch):
    monkeypatch.setattr(
        "app.attachments.download_attachment",
        lambda url, cookie="", max_bytes=2_000_000: _docx_bytes(""),
    )
    monkeypatch.setattr(
        "app.attachments._extract_docx",
        lambda content: "DOCX прочитан, но текст не найден.",
    )
    monkeypatch.setattr(
        "app.attachments.describe_docx_with_openrouter",
        lambda content, api_key, model, base_url, timeout_seconds=45.0: "В документе показаны экран каталога и форма обратной связи.",
        raising=False,
    )

    context = build_attachment_context(
        ("ТЗ.docx: https://kwork.ru/files/tz.docx",),
        openrouter_api_key="or-test-key",
        openrouter_vision_model="provider/vision-model",
    )

    assert "Статус: скачан, vision прочитан" in context
    assert "экран каталога и форма обратной связи" in context


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


def test_build_attachment_context_opens_rar_and_reads_inner_text(monkeypatch):
    monkeypatch.setattr(
        "app.attachments.download_attachment",
        lambda url, cookie="", max_bytes=2_000_000: b"fake rar bytes",
    )
    monkeypatch.setattr("app.attachments._rar_executable", lambda: Path("C:/WinRAR/UnRAR.exe"), raising=False)
    monkeypatch.setattr("app.attachments._winrar_executable", lambda: None, raising=False)
    monkeypatch.setattr("app.attachments._list_rar_entries", lambda *_args: ("brief.txt",), raising=False)
    monkeypatch.setattr(
        "app.attachments._read_rar_entry",
        lambda _exe, _archive, name, _limit: "Нужно сверстать лендинг и форму".encode("utf-8") if name == "brief.txt" else b"",
        raising=False,
    )

    context = build_attachment_context(
        ("tz.rar: https://kwork.ru/files/tz.rar",),
        cookie="",
    )

    assert "Статус: скачан, архив открыт" in context
    assert "brief.txt: прочитан" in context
    assert "Нужно сверстать лендинг" in context


def test_build_attachment_context_opens_7z_and_reads_inner_text(monkeypatch):
    monkeypatch.setattr(
        "app.attachments.download_attachment",
        lambda url, cookie="", max_bytes=2_000_000: b"fake 7z bytes",
    )
    monkeypatch.setattr("app.attachments._seven_zip_executable", lambda: Path("C:/7-Zip/7z.exe"), raising=False)
    monkeypatch.setattr("app.attachments._winrar_executable", lambda: None, raising=False)
    monkeypatch.setattr("app.attachments._list_7z_entries", lambda *_args: ("brief.txt",), raising=False)
    monkeypatch.setattr(
        "app.attachments._read_7z_entry",
        lambda _exe, _archive, name, _limit: "Нужно настроить форму заявки".encode("utf-8") if name == "brief.txt" else b"",
        raising=False,
    )

    context = build_attachment_context(
        ("tz.7z: https://kwork.ru/files/tz.7z",),
        cookie="",
    )

    assert "Статус: скачан, архив открыт" in context
    assert "brief.txt: прочитан" in context
    assert "Нужно настроить форму" in context


def test_build_attachment_context_reports_missing_rar_tool(monkeypatch):
    monkeypatch.setattr(
        "app.attachments.download_attachment",
        lambda url, cookie="", max_bytes=2_000_000: b"fake rar bytes",
    )
    monkeypatch.setattr("app.attachments._rar_executable", lambda: None, raising=False)
    monkeypatch.setattr("app.attachments._winrar_executable", lambda: None, raising=False)

    context = build_attachment_context(
        ("tz.rar: https://kwork.ru/files/tz.rar",),
        cookie="",
    )

    assert "Статус: скачан, архив не открыт" in context
    assert "UnRAR/RAR не найден" in context


def test_build_attachment_context_skips_over_limit_winrar_entry(monkeypatch):
    monkeypatch.setattr(
        "app.attachments.download_attachment",
        lambda url, cookie="", max_bytes=2_000_000: b"fake rar bytes",
    )
    monkeypatch.setattr("app.attachments._rar_executable", lambda: Path("C:/WinRAR/UnRAR.exe"), raising=False)
    monkeypatch.setattr("app.attachments._winrar_executable", lambda: None, raising=False)
    monkeypatch.setattr("app.attachments._list_rar_entries", lambda *_args: ("brief.txt",), raising=False)
    monkeypatch.setattr(
        "app.attachments._read_rar_entry",
        lambda *_args: b"x" * 11,
        raising=False,
    )

    context = build_attachment_context(
        ("tz.rar: https://kwork.ru/files/tz.rar",),
        cookie="",
        max_bytes=10,
    )

    assert "brief.txt: пропущен, файл больше лимита 10 байт" in context


def test_build_attachment_report_marks_password_protected_archive_not_opened(monkeypatch):
    monkeypatch.setattr(
        "app.attachments.download_attachment",
        lambda url, cookie="", max_bytes=2_000_000: b"fake rar bytes",
    )
    monkeypatch.setattr("app.attachments._rar_executable", lambda: Path("C:/WinRAR/UnRAR.exe"), raising=False)
    monkeypatch.setattr("app.attachments._list_rar_entries", lambda *_args: ("brief.txt",), raising=False)
    monkeypatch.setattr(
        "app.attachments._read_rar_entry",
        lambda *_args: (_ for _ in ()).throw(RuntimeError("The specified password is incorrect")),
        raising=False,
    )

    result = build_attachment_report(
        ("tz.rar: https://kwork.ru/files/tz.rar",),
        cookie="",
    )

    assert result.reports[0].status == "скачан, архив не открыт"
    assert result.reports[0].opened_archive is False
    assert "password is incorrect" in result.reports[0].summary


def test_rar_listing_keeps_a_bounded_number_of_entry_names(monkeypatch):
    from app import attachments

    listing = "\n".join(f"file-{index}.txt" for index in range(300)).encode("utf-8")

    class FakeResult:
        returncode = 0
        stdout = listing
        stderr = b""

    class FakeProcess:
        def __init__(self):
            self.stdout = io.BytesIO(listing)
            self.stderr = io.BytesIO()
            self.returncode = None

        def poll(self):
            return self.returncode

        def kill(self):
            self.returncode = -9

        def wait(self, timeout=None):
            self.returncode = 0
            return 0

    monkeypatch.setattr(attachments.subprocess, "run", lambda *args, **kwargs: FakeResult())
    monkeypatch.setattr(attachments.subprocess, "Popen", lambda *args, **kwargs: FakeProcess())

    entries = attachments._list_rar_entries(Path("C:/WinRAR/UnRAR.exe"), Path("C:/tmp/tz.rar"))

    assert len(entries) == 200
    assert entries[0] == "file-0.txt"
    assert entries[-1] == "file-199.txt"


def test_rar_entry_uses_one_combined_bounded_output_pipe(monkeypatch):
    from app import attachments

    captured = {}

    class FakeProcess:
        def __init__(self):
            self.stdout = io.BytesIO(b"brief text")
            self.stderr = io.BytesIO()
            self.returncode = None

        def poll(self):
            return self.returncode

        def kill(self):
            self.returncode = -9

        def wait(self, timeout=None):
            self.returncode = 0
            return 0

    def fake_popen(command, stdout, stderr):
        captured["command"] = command
        captured["stdout"] = stdout
        captured["stderr"] = stderr
        return FakeProcess()

    monkeypatch.setattr(attachments.subprocess, "Popen", fake_popen)

    content = attachments._read_rar_entry(
        Path("C:/WinRAR/UnRAR.exe"),
        Path("C:/tmp/tz.rar"),
        "brief.txt",
        100,
    )

    assert content == b"brief text"
    assert captured["stderr"] is attachments.subprocess.STDOUT


def test_unrar_password_exit_code_becomes_readable_error():
    from app import attachments

    message = attachments._archive_tool_error_message("UnRAR", b"", b"", 11)

    assert "парол" in message.lower()


def test_7z_listing_parses_cp866_file_names_and_skips_directories(monkeypatch):
    from app import attachments

    listing = (
        "Path = tz.7z\n"
        "Type = 7z\n"
        "\n"
        "----------\n"
        "Path = папка\\\n"
        "Attributes = D\n"
        "\n"
        "Path = ТЗ.txt\n"
        "Attributes = A\n"
        "\n"
    ).encode("cp866")

    class FakeProcess:
        def __init__(self):
            self.stdout = io.BytesIO(listing)
            self.returncode = None

        def poll(self):
            return self.returncode

        def kill(self):
            self.returncode = -9

        def wait(self, timeout=None):
            self.returncode = 0
            return 0

    monkeypatch.setattr(attachments.subprocess, "Popen", lambda *args, **kwargs: FakeProcess())

    entries = attachments._list_7z_entries(Path("C:/7-Zip/7z.exe"), Path("C:/tmp/tz.7z"))

    assert entries == ("ТЗ.txt",)


def test_rar_listing_rejects_output_larger_than_the_safe_limit(monkeypatch):
    from app import attachments

    class FakeProcess:
        def __init__(self):
            self.stdout = io.BytesIO(b"x" * (attachments.MAX_ARCHIVE_LIST_BYTES + 1))
            self.returncode = None

        def poll(self):
            return self.returncode

        def kill(self):
            self.returncode = -9

        def wait(self, timeout=None):
            self.returncode = 0
            return 0

    monkeypatch.setattr(attachments.subprocess, "Popen", lambda *args, **kwargs: FakeProcess())

    with pytest.raises(ValueError, match="список файлов больше лимита"):
        attachments._list_rar_entries(Path("C:/WinRAR/UnRAR.exe"), Path("C:/tmp/tz.rar"))


def test_external_archive_removes_temporary_file_after_listing_error(monkeypatch, tmp_path):
    from app import attachments

    original_mkstemp = attachments.tempfile.mkstemp

    def create_test_temp_file(*args, **kwargs):
        return original_mkstemp(dir=tmp_path, *args, **kwargs)

    monkeypatch.setattr(attachments.tempfile, "mkstemp", create_test_temp_file)
    monkeypatch.setattr(attachments, "_rar_executable", lambda: Path("C:/WinRAR/UnRAR.exe"))
    monkeypatch.setattr(attachments, "_list_rar_entries", lambda *_args: (_ for _ in ()).throw(RuntimeError("bad archive")))

    status, summary = attachments.inspect_attachment(
        attachments.AttachmentRef("tz.rar", "tz.rar"),
        b"fake rar bytes",
    )

    assert status == "скачан, архив не открыт"
    assert "bad archive" in summary
    assert list(tmp_path.iterdir()) == []


def test_build_attachment_report_saves_file_and_exposes_processing_flags(monkeypatch, tmp_path):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("brief.txt", "Нужно сверстать лендинг и форму")

    monkeypatch.setattr(
        "app.attachments.download_attachment",
        lambda url, cookie="", max_bytes=2_000_000: buffer.getvalue(),
    )

    result = build_attachment_report(
        ("ТЗ клиента.zip: https://kwork.ru/files/tz.zip",),
        output_dir=tmp_path / "attachments",
    )

    assert "ФАЙЛЫ/ТЗ" in result.context
    assert len(result.reports) == 1
    report = result.reports[0]
    assert report.label == "ТЗ клиента.zip"
    assert report.url == "https://kwork.ru/files/tz.zip"
    assert report.status == "скачан, архив открыт"
    assert report.kind == "archive"
    assert report.opened_archive is True
    assert report.ocr_scanned is False
    assert "brief.txt: прочитан" in report.summary
    assert report.local_path
    assert (tmp_path / "attachments" / Path(report.local_path).name).exists()


def test_build_attachment_report_uses_ai_to_choose_zip_entries(monkeypatch, tmp_path):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("random-notes.txt", "Это читать не нужно")
        archive.writestr("brief.txt", "Нужно сверстать форму заявки и адаптив")

    monkeypatch.setattr(
        "app.attachments.download_attachment",
        lambda url, cookie="", max_bytes=2_000_000: buffer.getvalue(),
    )

    def fake_select_archive_entries(ref, entries, lead_context="", api_key="", model="deepseek-chat", max_entries=8):
        assert ref.label == "ТЗ.zip"
        assert [entry.name for entry in entries] == ["random-notes.txt", "brief.txt"]
        assert "форма заявки" in lead_context
        assert api_key == "sk-test"
        return ArchiveSelection(names=("brief.txt",), used_ai=True, reason="это похоже на ТЗ")

    monkeypatch.setattr("app.attachments.select_archive_entries_with_deepseek", fake_select_archive_entries)

    result = build_attachment_report(
        ("ТЗ.zip: https://kwork.ru/files/tz.zip",),
        output_dir=tmp_path / "attachments",
        lead_context="Заказ: форма заявки на сайте",
        deepseek_api_key="sk-test",
    )

    report = result.reports[0]
    assert "AI выбрала файлы: brief.txt" in report.summary
    assert "Нужно сверстать форму заявки" in report.summary
    assert "Это читать не нужно" not in report.summary
    assert report.status == "скачан, архив открыт, AI выбрала файлы"


def test_build_attachment_context_reads_scanned_pdf_with_ocr(monkeypatch):
    monkeypatch.setattr(
        "app.attachments.download_attachment",
        lambda url, cookie="", max_bytes=2_000_000: _blank_pdf_bytes(),
    )
    monkeypatch.setattr(
        "app.attachments._extract_pdf_ocr",
        lambda content: "На PDF скане инструкция по cookie-уведомлению",
    )

    context = build_attachment_context(
        ("ТЗ.pdf: https://kwork.ru/files/tz.pdf",),
        cookie="",
    )

    assert "Статус: скачан, OCR прочитан" in context
    assert "инструкция по cookie" in context


def test_build_attachment_context_smart_mode_enriches_short_pdf_ocr(monkeypatch):
    monkeypatch.setattr(
        "app.attachments.download_attachment",
        lambda url, cookie="", max_bytes=2_000_000: _blank_pdf_bytes(),
    )
    monkeypatch.setattr(
        "app.attachments._extract_pdf_ocr",
        lambda content: "Форма заявки и адаптив.",
    )
    monkeypatch.setattr(
        "app.attachments.describe_pdf_with_openrouter",
        lambda content, api_key, model, base_url, timeout_seconds=45.0: (
            "На первой странице ТЗ показаны правки формы и мобильной версии лендинга."
        ),
        raising=False,
    )

    context = build_attachment_context(
        ("ТЗ.pdf: https://kwork.ru/files/tz.pdf",),
        openrouter_api_key="or-test-key",
        openrouter_vision_model="provider/vision-model",
        openrouter_vision_mode="smart",
    )

    assert "Статус: скачан, OCR + vision прочитан" in context
    assert "OCR: Форма заявки" in context
    assert "Vision: На первой странице ТЗ" in context


def test_build_attachment_context_reports_pdf_ocr_failure(monkeypatch):
    monkeypatch.setattr(
        "app.attachments.download_attachment",
        lambda url, cookie="", max_bytes=2_000_000: _blank_pdf_bytes(),
    )
    monkeypatch.setattr(
        "app.attachments._extract_pdf_ocr",
        lambda content: (_ for _ in ()).throw(RuntimeError("Tesseract не найден")),
    )

    context = build_attachment_context(
        ("ТЗ.pdf: https://kwork.ru/files/tz.pdf",),
        cookie="",
    )

    assert "Статус: скачан, текст не извлечен" in context
    assert "OCR PDF не выполнен" in context


def test_build_attachment_context_uses_openrouter_vision_when_pdf_ocr_fails(monkeypatch):
    monkeypatch.setattr(
        "app.attachments.download_attachment",
        lambda url, cookie="", max_bytes=2_000_000: _blank_pdf_bytes(),
    )
    monkeypatch.setattr(
        "app.attachments._extract_pdf_ocr",
        lambda content: (_ for _ in ()).throw(RuntimeError("Tesseract не найден")),
    )
    monkeypatch.setattr(
        "app.attachments.describe_pdf_with_openrouter",
        lambda content, api_key, model, base_url, timeout_seconds=45.0: "На скане описаны правки формы и мобильной версии.",
        raising=False,
    )

    context = build_attachment_context(
        ("ТЗ.pdf: https://kwork.ru/files/tz.pdf",),
        openrouter_api_key="or-test-key",
        openrouter_vision_model="provider/vision-model",
    )

    assert "Статус: скачан, vision прочитан" in context
    assert "правки формы и мобильной версии" in context


def _docx_bytes(text: str) -> bytes:
    from docx import Document

    document = Document()
    document.add_paragraph(text)
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def _blank_pdf_bytes() -> bytes:
    import fitz

    document = fitz.open()
    document.new_page(width=200, height=200)
    data = document.tobytes()
    document.close()
    return data
