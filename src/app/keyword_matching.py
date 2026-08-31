from __future__ import annotations

import re
from typing import Pattern


EXCLUSION_BEFORE_PATTERN = re.compile(
    r"(?:"
    r"\bбез\s+(?:использования|применения|подключения|установки|внедрения)\b"
    r"|\b(?:не|нельзя)\s+(?:использовать|применять|подключать|устанавливать|делать|собирать)\b"
    r"|\bзапрещ\w*\s+(?:использован\w*|применен\w*|подключен\w*)"
    r"|\b(?:отказ\w*|отказыва\w*)\s+от\b"
    r"|\bисключ\w*"
    r")[^.!?\n]{0,120}$",
    re.IGNORECASE,
)
DIRECT_EXCLUSION_BEFORE_PATTERN = re.compile(
    r"(?:\bбез(?:\s+использования)?|\bне\s+(?:на|через|в))\s*[\s(\[{'\"«]*$",
    re.IGNORECASE,
)
EXCLUSION_AFTER_PATTERN = re.compile(
    r"^[\s)\]}\"'»,:;-]{0,12}(?:"
    r"не\s+(?:использовать|применять|подключать|устанавливать|нужен|нужна|нужно|рассматриваем|рассматривается)"
    r"|исключ\w*"
    r"|запрещ\w*"
    r")\b",
    re.IGNORECASE,
)


def has_non_excluded_match(text: str, pattern: Pattern[str]) -> bool:
    return any(not _is_excluded(text, match.start(), match.end()) for match in pattern.finditer(text))


def has_non_excluded_keyword(text: str, keyword: str) -> bool:
    clean = keyword.strip()
    if not clean:
        return False
    return has_non_excluded_match(text, re.compile(re.escape(clean), re.IGNORECASE))


def _is_excluded(text: str, start: int, end: int) -> bool:
    before = text[max(0, start - 140) : start]
    after = text[end : end + 90]
    return bool(
        EXCLUSION_BEFORE_PATTERN.search(before)
        or DIRECT_EXCLUSION_BEFORE_PATTERN.search(before)
        or EXCLUSION_AFTER_PATTERN.search(after)
    )
