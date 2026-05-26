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

# Matches "Rating: X", "评级: X", "建议: X" etc. — tolerates markdown
# bold wrappers and either a colon or hyphen separator.
_RATING_LABEL_RE = re.compile(r"(?:rating|评级|建议|结论|recommendation).*?[:\-][\s*]*([^\s*]+)", re.IGNORECASE)

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
    """Extract a 5-tier rating from text using hierarchical heuristics."""
    if not text:
        return "N/A"

    # Clean text: remove common thinking block markers or everything before </think>
    clean_text = text
    if "</think>" in text:
        clean_text = text.split("</think>")[-1].strip()
    elif "Output Generation]" in text:
        clean_text = text.split("Output Generation]")[-1].strip()
    elif "Conclusion:" in text: # Sometimes models put the final answer after a label
        # But only if it's near the end? No, let's stick to simple markers.
        pass

    # 1. Try label-based regex (highest precision)
    for line in clean_text.splitlines():
        line = line.strip()
        m = _RATING_LABEL_RE.search(line)
        if m:
            val = m.group(1).lower().strip("*:., ")
            # Check English first
            if val in _RATING_SET:
                return val.capitalize()
            # Check Chinese keyword in the value part
            for zh, en in _RATING_KEYWORDS_ZH.items():
                if zh in m.group(1):
                    return en

    # 2. Try looking for lines that ARE just a keyword (with optional markdown)
    lines = [line.strip().strip("*# ").lower() for line in clean_text.splitlines() if line.strip()]
    for line in lines:
        if line in _RATING_SET:
            return line.capitalize()
        for zh, en in _RATING_KEYWORDS_ZH.items():
            if line == zh:
                return en

    # 3. Fallback: Check for keywords in the first few lines of the CLEAN text
    head = "\n".join(clean_text.splitlines()[:15]).lower()
    priority_order = ["Sell", "Underweight", "Buy", "Overweight", "Hold"]
    
    # We check for the specific English/Chinese word pair for each rating in priority order
    for rating_en in priority_order:
        # Check Chinese keywords for this rating first (more specific in Chinese context)
        for zh, en in _RATING_KEYWORDS_ZH.items():
            if en == rating_en and zh in head:
                return en
        # Then check English word
        if rating_en.lower() in head:
            return rating_en

    return default
