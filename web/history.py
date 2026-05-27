"""Manage analysis history by scanning existing log files."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

# In-memory cache for stock names to avoid repeated disk/network lookups
_NAME_CACHE: dict[str, str] = {}


def _cache_file() -> Path:
    p = Path.home() / ".tradingagents" / "cache" / "stock_names.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _load_cache():
    global _NAME_CACHE
    if _NAME_CACHE:
        return
    p = _cache_file()
    if p.exists():
        try:
            with open(p, encoding="utf-8") as f:
                _NAME_CACHE.update(json.load(f))
        except Exception:
            pass


def _save_cache():
    p = _cache_file()
    try:
        with open(p, "w", encoding="utf-8") as f:
            json.dump(_NAME_CACHE, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _results_dir() -> Path:
    return Path.home() / ".tradingagents" / "logs"


def _read_stock_name(json_path: str, ticker: str) -> str:
    _load_cache()
    if ticker in _NAME_CACHE and _NAME_CACHE[ticker]:
        return _NAME_CACHE[ticker]

    # 1. Try reading from JSON
    try:
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)
        name = data.get("stock_name", "")
        if name:
            _NAME_CACHE[ticker] = name
            _save_cache()
            return name
    except Exception:
        pass

    # 2. Try network lookup
    try:
        from tradingagents.dataflows.a_stock import get_stock_name
        name = get_stock_name(ticker)
        if name:
            _NAME_CACHE[ticker] = name
            _save_cache()
            return name
    except Exception:
        pass

    return ""


def get_history() -> list[dict[str, str]]:
    """Scan saved analysis logs and return a sorted list (newest first).

    Each entry: {"ticker": "300750", "name": "宁德时代", "date": "2026-05-12", "path": "/abs/path/...json"}
    """
    root = _results_dir()
    if not root.exists():
        return []

    entries: list[dict[str, str]] = []
    # Use a set to avoid duplicate entries for the same ticker/date (if any)
    seen = set()

    for log_file in root.rglob("full_states_log_*.json"):
        match = re.search(r"full_states_log_(\d{4}-\d{2}-\d{2})\.json$", log_file.name)
        if not match:
            continue
        date = match.group(1)
        ticker = log_file.parent.parent.name
        
        key = (ticker, date)
        if key in seen:
            continue
        seen.add(key)

        name = _read_stock_name(str(log_file), ticker)
        entries.append({
            "ticker": ticker,
            "name": name,
            "date": date,
            "path": str(log_file)
        })

    # Sort by date (desc) then ticker (asc)
    entries.sort(key=lambda e: (e["date"], e["ticker"]), reverse=True)
    return entries


def load_analysis(path: str) -> dict[str, Any]:
    """Load a saved analysis JSON file."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def extract_signal(state: dict[str, Any]) -> str:
    from tradingagents.agents.utils.rating import parse_rating

    for field in (
        "final_trade_decision",
        "trader_investment_decision",
        "trader_investment_plan",
        "investment_plan",
    ):
        text = state.get(field, "")
        if not text:
            continue
        rating = parse_rating(text)
        if rating != "N/A":
            return rating
    return "N/A"
