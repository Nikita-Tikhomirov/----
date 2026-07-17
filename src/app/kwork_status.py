from __future__ import annotations


UNAVAILABLE_PROJECT_REASON = "Kwork project is unavailable: page not found, closed, or removed."
UNAVAILABLE_PROJECT_MARKERS = (
    "страница не найдена",
    "проект не найден",
    "заказ не найден",
    "проект недоступен",
    "заказ недоступен",
    "проект закрыт",
    "заказ закрыт",
    "заказ снят",
    "page not found",
    "project not found",
    "project is unavailable",
)


def unavailable_project_message(page_text: str) -> str:
    lowered = page_text.lower()
    if any(marker in lowered for marker in UNAVAILABLE_PROJECT_MARKERS):
        return UNAVAILABLE_PROJECT_REASON
    return ""
