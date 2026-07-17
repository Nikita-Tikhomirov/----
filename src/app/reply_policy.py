"""Shared safety rules for customer-facing Kwork replies."""

from __future__ import annotations

import re

# "Оплата" can describe a required website feature. Only commercial payment terms
# belong in the blocked category; a checkout or payment-integration task does not.
COMMERCIAL_REPLY_PATTERN = re.compile(
    r"(?:"
    r"\b(?:цена|стоим|бюджет|предоплат|скидк|ставка|тариф|бесплатн)\w*"
    r"|\bуслови\w*\s+оплат\w*\b"
    r"|\bоплат\w*\s+(?:за|по|после|перед|работ\w*|услуг\w*|сделан\w*|проект\w*|частями|сразу|потом|перевод\w*|деньг\w*)\b"
    r"|\b(?:payment\s+terms|payment\s+(?:after|before|for))\b"
    r"|\d[\d\s.,]*\s*(?:₽|руб(?:\.|лей)?|р\.?|тыс\.?|к\b)"
    r")",
    re.IGNORECASE,
)
