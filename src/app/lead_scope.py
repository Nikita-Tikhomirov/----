from __future__ import annotations

import re

from app.keyword_matching import has_non_excluded_match


_ACCOUNT_WORD = r"(?:ак+аунт\w*|account\w*|уч[её]тн\w*\s+запис\w*)"
_CREATE_ACCOUNT = rf"(?:созда\w*|зарегистрир\w*|оформ\w*)[^.!?\n]{{0,100}}{_ACCOUNT_WORD}"
_DEVELOPER_PLATFORM = (
    r"(?:google\s*play(?:\s*console)?|гугл\s*пл[еэ]й(?:\s*консол\w*)?|"
    r"play\s*console|app\s*store\s*connect|developer\s*account|"
    r"ак+аунт\w*\s+разработчик\w*)"
)
THIRD_PARTY_DEVELOPER_ACCOUNT_PATTERN = re.compile(
    rf"(?:{_CREATE_ACCOUNT}[^.!?\n]{{0,160}}{_DEVELOPER_PLATFORM}|"
    rf"{_DEVELOPER_PLATFORM}[^.!?\n]{{0,160}}{_CREATE_ACCOUNT})",
    re.IGNORECASE,
)
VISUAL_SITE_BUILDER_PATTERN = re.compile(
    r"(?:\boxygen(?:\s+builder)?\b|оксиджен\w*|"
    r"\bbricks(?:\s+builder)?\b|\bwpbakery\b|"
    r"\bdivi(?:\s+builder)?\b|\bbeaver\s+builder\b|"
    r"\bvisual\s+composer\b|\bbreakdance(?:\s+builder)?\b|"
    r"\bthrive\s+architect\b)",
    re.IGNORECASE,
)


def non_development_rejection(text: str) -> str:
    if has_non_excluded_match(text, THIRD_PARTY_DEVELOPER_ACCOUNT_PATTERN):
        return "регистрация стороннего аккаунта без разработки"
    if has_non_excluded_match(text, VISUAL_SITE_BUILDER_PATTERN):
        return "визуальный конструктор страниц"
    return ""
