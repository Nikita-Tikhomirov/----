from __future__ import annotations

import re


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


def non_development_rejection(text: str) -> str:
    if THIRD_PARTY_DEVELOPER_ACCOUNT_PATTERN.search(text):
        return "регистрация стороннего аккаунта без разработки"
    return ""
