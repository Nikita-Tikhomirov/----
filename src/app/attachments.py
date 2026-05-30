from __future__ import annotations

import html
import io
import logging
import re
import ssl
import urllib.request
from dataclasses import dataclass
from urllib.parse import urlparse
from urllib.request import Request

logger = logging.getLogger(__name__)

TEXT_EXTENSIONS = {".txt", ".md", ".csv", ".html", ".htm", ".json", ".xml"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
ARCHIVE_EXTENSIONS = {".zip", ".rar", ".7z"}


@dataclass(frozen=True)
class AttachmentRef:
    label: str
    url: str


def build_attachment_context(
    attachments: tuple[str, ...],
    cookie: str = "",
    max_files: int = 3,
    max_bytes: int = 2_000_000,
) -> str:
    """Download small readable attachments and return text for AI context."""
    if not attachments:
        return ""

    blocks: list[str] = []
    for raw in attachments[:max_files]:
        ref = parse_attachment(raw)
        try:
            content = download_attachment(ref.url, cookie=cookie, max_bytes=max_bytes)
            extracted = extract_attachment_text(ref, content)
        except Exception as exc:
            logger.warning("Failed to read attachment %s: %s", ref.url, exc)
            extracted = f"Не удалось скачать или прочитать файл: {exc}"
        blocks.append(f"Файл: {ref.label}\nСсылка: {ref.url}\n{_shorten(extracted, 2500)}")
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


def extract_attachment_text(ref: AttachmentRef, content: bytes) -> str:
    ext = _extension(ref.url) or _extension(ref.label)
    if ext in TEXT_EXTENSIONS:
        return _decode_text(content)
    if ext == ".docx":
        return _extract_docx(content)
    if ext == ".pdf":
        return _extract_pdf(content)
    if ext in IMAGE_EXTENSIONS:
        return "Изображение найдено, OCR пока не выполняется. Учитывай файл как визуальное ТЗ/скриншот."
    if ext in ARCHIVE_EXTENSIONS:
        return "Архив найден, содержимое автоматически не читается. Нужно учитывать риск неизвестного объема."
    return "Файл найден, но тип не поддержан для автоматического чтения."


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
    return "\n".join(paragraph.text for paragraph in document.paragraphs if paragraph.text.strip())


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


def _extension(value: str) -> str:
    path = urlparse(value).path if re.match(r"https?://", value, re.IGNORECASE) else value
    match = re.search(r"(\.[A-Za-z0-9]+)$", path)
    return match.group(1).lower() if match else ""


def _shorten(text: str, limit: int) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"
