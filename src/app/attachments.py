from __future__ import annotations

import html
import io
import logging
import os
import re
import ssl
import subprocess
import tempfile
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request

logger = logging.getLogger(__name__)

TEXT_EXTENSIONS = {".txt", ".md", ".csv", ".html", ".htm", ".json", ".xml"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
ARCHIVE_EXTENSIONS = {".zip", ".rar", ".7z"}
DEFAULT_TESSERACT_CMD = Path(r"D:\Tesseract-OCR\tesseract.exe")


@dataclass(frozen=True)
class AttachmentRef:
    label: str
    url: str


def build_attachment_context(
    attachments: tuple[str, ...],
    cookie: str = "",
    max_files: int = 3,
    max_bytes: int = 2_000_000,
    use_browser: bool = False,
    cdp_url: str = "http://127.0.0.1:9222",
    browser_profile_dir: str = "",
) -> str:
    """Download small readable attachments and return text for AI context."""
    if not attachments:
        return ""

    blocks: list[str] = ["ФАЙЛЫ/ТЗ:"]
    for raw in attachments[:max_files]:
        ref = parse_attachment(raw)
        try:
            content = _download_with_fallback(
                ref.url,
                cookie=cookie,
                max_bytes=max_bytes,
                use_browser=use_browser,
                cdp_url=cdp_url,
                browser_profile_dir=browser_profile_dir,
            )
            status, extracted = inspect_attachment(ref, content, max_bytes=max_bytes)
        except Exception as exc:
            logger.warning("Failed to read attachment %s: %s", ref.url, exc)
            status = "не скачан"
            extracted = f"Не удалось скачать или прочитать файл: {exc}"
        blocks.append(
            "\n".join(
                [
                    f"- {ref.label}",
                    f"  Ссылка: {ref.url}",
                    f"  Статус: {status}",
                    f"  Кратко: {_shorten(extracted, 2500)}",
                ]
            )
        )
    return "\n\n".join(blocks)


def parse_attachment(raw: str) -> AttachmentRef:
    label, sep, url = raw.partition(": ")
    if not sep:
        url = raw.strip()
        label = url.rsplit("/", 1)[-1] or "attachment"
    return AttachmentRef(label=html.unescape(label).strip(), url=url.strip())


def download_attachment(url: str, cookie: str = "", max_bytes: int = 2_000_000) -> bytes:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept-Encoding": "identity",
    }
    if cookie:
        headers["Cookie"] = cookie
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    request = Request(url, headers=headers)
    opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ssl_ctx))
    with opener.open(request, timeout=30) as response:
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = response.read(min(65536, max_bytes - total + 1))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > max_bytes:
                raise ValueError(f"файл больше лимита {max_bytes} байт")
        return b"".join(chunks)


def download_attachment_via_browser(
    url: str,
    cdp_url: str,
    browser_profile_dir: str = "",
    max_bytes: int = 2_000_000,
) -> bytes:
    """Download a private attachment through the logged-in Chrome session."""
    from app.kwork_source import _ensure_chrome_cdp, _evaluate, _find_or_create_page

    _ensure_chrome_cdp(cdp_url, "https://kwork.ru/projects", browser_profile_dir)
    page = _find_or_create_page(cdp_url, "https://kwork.ru/projects")

    import base64
    import json
    import websocket

    ws = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=45)
    try:
        payload = _evaluate(
            ws,
            f"""
            (async () => {{
              const response = await fetch({json.dumps(url)}, {{ credentials: 'include' }});
              const buffer = await response.arrayBuffer();
              const bytes = new Uint8Array(buffer);
              if (bytes.length > {int(max_bytes)}) {{
                throw new Error('файл больше лимита {int(max_bytes)} байт');
              }}
              let binary = '';
              const chunkSize = 32768;
              for (let i = 0; i < bytes.length; i += chunkSize) {{
                binary += String.fromCharCode(...bytes.slice(i, i + chunkSize));
              }}
              return JSON.stringify({{
                ok: response.ok,
                status: response.status,
                contentType: response.headers.get('content-type') || '',
                body: btoa(binary)
              }});
            }})()
            """,
        )
    finally:
        ws.close()
    if not payload:
        raise RuntimeError("Chrome не вернул файл")
    data = json.loads(payload)
    if not data.get("ok"):
        status = data.get("status", "unknown")
        raise PermissionError(f"Chrome не смог скачать файл, HTTP {status}. Проверь вход в Kwork.")
    return base64.b64decode(data.get("body", ""))


def _download_with_fallback(
    url: str,
    cookie: str,
    max_bytes: int,
    use_browser: bool,
    cdp_url: str,
    browser_profile_dir: str,
) -> bytes:
    try:
        return download_attachment(url, cookie=cookie, max_bytes=max_bytes)
    except Exception as direct_exc:
        if not use_browser:
            raise
        logger.info("Direct attachment download failed, trying Chrome session for %s: %s", url, direct_exc)
        try:
            return download_attachment_via_browser(
                url,
                cdp_url=cdp_url,
                browser_profile_dir=browser_profile_dir,
                max_bytes=max_bytes,
            )
        except Exception as browser_exc:
            raise RuntimeError(
                f"прямое скачивание не прошло ({direct_exc}); Chrome-сессия тоже не скачала файл ({browser_exc}). "
                "Проверь, что в отдельном Kwork Chrome выполнен вход в аккаунт."
            ) from browser_exc


def extract_attachment_text(ref: AttachmentRef, content: bytes) -> str:
    return inspect_attachment(ref, content)[1]


def inspect_attachment(ref: AttachmentRef, content: bytes, max_bytes: int = 2_000_000) -> tuple[str, str]:
    ext = _extension(ref.url) or _extension(ref.label)
    if ext in TEXT_EXTENSIONS:
        return "скачан, прочитан", _decode_text(content)
    if ext == ".docx":
        return "скачан, прочитан", _extract_docx(content)
    if ext == ".pdf":
        return "скачан, прочитан", _extract_pdf(content)
    if ext in IMAGE_EXTENSIONS:
        return _extract_image_ocr(content, ext)
    if ext in ARCHIVE_EXTENSIONS:
        return _extract_archive(ref, content, max_bytes=max_bytes)
    return "скачан, тип не поддержан", "Файл найден, но тип не поддержан для автоматического чтения."


def _decode_text(content: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1251"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", errors="replace")


def _extract_docx(content: bytes) -> str:
    try:
        from docx import Document
    except ImportError:
        return "DOCX найден, но python-docx недоступен."
    document = Document(io.BytesIO(content))
    parts = [paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()]
    for table in document.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if cells:
                parts.append(" | ".join(cells))
    return "\n".join(parts) or "DOCX прочитан, но текст не найден."


def _extract_pdf(content: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        try:
            from PyPDF2 import PdfReader
        except ImportError:
            return "PDF найден, но библиотека для чтения PDF не установлена."
    reader = PdfReader(io.BytesIO(content))
    pages = []
    for page in reader.pages[:5]:
        pages.append(page.extract_text() or "")
    return "\n".join(text for text in pages if text.strip()) or "PDF прочитан, но текст не извлечен."


def _extract_image_ocr(content: bytes, ext: str) -> tuple[str, str]:
    try:
        text = _run_tesseract_ocr(content, ext)
    except Exception as exc:
        return "скачан, OCR не выполнен", f"OCR не выполнен: {exc}"
    clean = _shorten(text, 2500)
    if clean:
        return "скачан, OCR прочитан", clean
    return "скачан, OCR не выполнен", "OCR выполнился, но текст на изображении не найден."


def _extract_archive(ref: AttachmentRef, content: bytes, max_bytes: int) -> tuple[str, str]:
    ext = _extension(ref.url) or _extension(ref.label)
    if ext != ".zip":
        return "скачан, архив не открыт", "Автоматически открываются только ZIP-архивы; RAR/7Z пока нужно смотреть вручную."
    try:
        lines = _read_zip_archive(content, max_bytes=max_bytes)
    except zipfile.BadZipFile:
        return "скачан, архив не открыт", "ZIP-архив поврежден или это не ZIP-файл."
    return "скачан, архив открыт", "\n".join(lines) or "ZIP-архив открыт, но подходящие файлы внутри не найдены."


def _read_zip_archive(content: bytes, max_bytes: int, max_entries: int = 8) -> list[str]:
    lines: list[str] = []
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        entries = [info for info in archive.infolist() if not info.is_dir()]
        for info in entries[:max_entries]:
            name = info.filename
            if info.file_size > max_bytes:
                lines.append(f"{name}: пропущен, файл больше лимита {max_bytes} байт")
                continue
            with archive.open(info) as file:
                data = file.read(max_bytes + 1)
            if len(data) > max_bytes:
                lines.append(f"{name}: пропущен, файл больше лимита {max_bytes} байт")
                continue
            nested_ref = AttachmentRef(label=name, url=name)
            status, extracted = inspect_attachment(nested_ref, data, max_bytes=max_bytes)
            nested_status = status.removeprefix("скачан, ")
            lines.append(f"{name}: {nested_status}\n{_shorten(extracted, 1500)}")
        if len(entries) > max_entries:
            lines.append(f"Еще файлов в архиве: {len(entries) - max_entries}, не читались из-за лимита.")
    return lines


def _run_tesseract_ocr(content: bytes, ext: str) -> str:
    command = _tesseract_command()
    if not command.exists():
        raise FileNotFoundError(f"Tesseract не найден: {command}")
    suffix = ext if ext.startswith(".") else f".{ext}"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as image_file:
        image_file.write(content)
        image_path = Path(image_file.name)
    try:
        result = subprocess.run(
            [str(command), str(image_path), "stdout", "-l", "rus+eng", "--psm", "6"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=45,
        )
    finally:
        image_path.unlink(missing_ok=True)
    if result.returncode != 0:
        error = (result.stderr or result.stdout or "неизвестная ошибка").strip()
        raise RuntimeError(error)
    return result.stdout.strip()


def _tesseract_command() -> Path:
    configured = os.getenv("TESSERACT_CMD", "").strip()
    if configured:
        path = Path(configured)
        if path.drive.upper() != "D:":
            raise RuntimeError("TESSERACT_CMD должен указывать на D: диск")
        return path
    return DEFAULT_TESSERACT_CMD


def _extension(value: str) -> str:
    path = urlparse(value).path if re.match(r"https?://", value, re.IGNORECASE) else value
    match = re.search(r"(\.[A-Za-z0-9]+)$", path)
    return match.group(1).lower() if match else ""


def _shorten(text: str, limit: int) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"
