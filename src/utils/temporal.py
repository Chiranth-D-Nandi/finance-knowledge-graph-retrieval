"""Temporal validation, point-in-time (PIT) filtering, and leakage controls."""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from src.config import settings


def parse_date(date_val: str | date | datetime) -> date:
    """Parse various date representations to datetime.date object."""
    if isinstance(date_val, datetime):
        return date_val.date()
    if isinstance(date_val, date):
        return date_val
    if isinstance(date_val, str):
        # Truncate time if present
        clean_str = date_val.split("T")[0].strip()
        return datetime.strptime(clean_str, "%Y-%m-%d").date()
    raise ValueError(f"Cannot parse date from type {type(date_val)}: {date_val}")


def is_point_in_time(doc_filing_date: str | date, query_timestamp: str | date) -> bool:
    """
    Enforce Point-in-Time (PIT) invariant:
    A document is visible if and only if filing_date <= query_timestamp.
    """
    filing_d = parse_date(doc_filing_date)
    query_d = parse_date(query_timestamp)
    return filing_d <= query_d


def filter_pit_candidates(
    candidates: List[Dict[str, Any]],
    before_date: Optional[str | date] = None,
    date_key: str = "filing_date",
) -> List[Dict[str, Any]]:
    """
    Filter candidate records to strictly respect point-in-time boundary.
    Any record with date_key > before_date is excluded.
    """
    if before_date is None:
        return candidates

    cutoff = parse_date(before_date)
    filtered = []
    for item in candidates:
        item_date = parse_date(item[date_key])
        if item_date <= cutoff:
            filtered.append(item)
    return filtered


def get_temporal_split_config() -> Dict[str, Any]:
    """Load canonical temporal split boundaries from split_config.json."""
    split_file = settings.SPLITS_DIR / "split_config.json"
    if not split_file.exists():
        return {
            "train_end": "2023-12-31",
            "val_start": "2024-01-01",
            "val_end": "2024-12-31",
            "test_start": "2025-01-01",
            "test_end": "2025-11-01",
        }
    with open(split_file, "r", encoding="utf-8") as f:
        return json.load(f)


def assign_temporal_split(doc_date: str | date) -> str:
    """Assign document to 'train', 'val', or 'test' partition based on filing_date."""
    d = parse_date(doc_date)
    cfg = get_temporal_split_config()
    train_end = parse_date(cfg["train_end"])
    val_end = parse_date(cfg["val_end"])

    if d <= train_end:
        return "train"
    elif d <= val_end:
        return "val"
    else:
        return "test"
