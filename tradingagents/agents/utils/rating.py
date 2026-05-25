"""Shared 5-tier rating vocabulary and a deterministic heuristic parser.

The same five-tier scale (Buy, Overweight, Hold, Underweight, Sell) is used by:
- The Research Manager (investment plan recommendation)
- The Portfolio Manager (final position decision)
- The signal processor (rating extracted for downstream consumers)
- The memory log (rating tag stored alongside each decision entry)

Centralising it here avoids drift between those call sites.
"""

from __future__ import annotations

import re
from typing import Tuple


# Canonical, ordered 5-tier scale (most bullish to most bearish).
RATINGS_5_TIER: Tuple[str, ...] = (
    "Buy", "Overweight", "Hold", "Underweight", "Sell",
)

_RATING_SET = {r.lower() for r in RATINGS_5_TIER}

# Matches "Rating: X" / "rating - X" / "Rating: **X**" — tolerates markdown
# bold wrappers and either a colon or hyphen separator.
_RATING_LABEL_RE = re.compile(r"rating.*?[:\-][\s*]*(\w+)", re.IGNORECASE)

_RATING_KEYWORDS_ZH = {
    "买入": "Buy",
    "加仓": "Overweight",
    "增持": "Overweight",
    "持有": "Hold",
    "观望": "Hold",
    "减持": "Underweight",
    "减仓": "Underweight",
    "卖出": "Sell",
    "清仓": "Sell",
}


def parse_rating(text: str, default: str = "Hold") -> str:
    for line in text.splitlines():
        m = _RATING_LABEL_RE.search(line)
        if m and m.group(1).lower() in _RATING_SET:
            return m.group(1).capitalize()

    lines = text.splitlines()
    for line in lines:
        line_lower = line.lower()
        for word in line_lower.split():
            clean = word.strip("*:.,")
            if clean in _RATING_SET:
                return clean.capitalize()

    full_lower = text.lower()
    for zh_keyword, en_rating in _RATING_KEYWORDS_ZH.items():
        if zh_keyword in full_lower:
            return en_rating

    return default
