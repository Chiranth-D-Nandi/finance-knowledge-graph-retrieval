"""Named Entity Recognition (NER) for financial disclosures and filings."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel

from src.ingest.entity_registry_builder import load_entity_registry


class MentionSpan(BaseModel):
    start: int
    end: int
    text: str
    label: str  # TICKER, ORG, MONEY, DATE


class FinancialNER:
    """
    Financial Named Entity Recognizer combining regex filters,
    entity registry allowlists, and financial pattern detectors.
    """

    def __init__(self, registry: Optional[List[Dict[str, Any]]] = None):
        raw_reg = registry or load_entity_registry()
        self.tickers_allowlist: Set[str] = {r["ticker"].upper() for r in raw_reg}
        self.alias_to_ticker: Dict[str, str] = {}

        for r in raw_reg:
            canonical = r["ticker"].upper()
            for alias in r.get("aliases", []):
                if len(alias.strip()) > 1:
                    self.alias_to_ticker[alias.strip().lower()] = canonical

        # Regex patterns
        self.ticker_pattern = re.compile(r"\b[A-Z]{1,5}(?:\.[A-Z])?\b")
        self.money_pattern = re.compile(
            r"\$\s*\d{1,3}(?:,\d{3})*(?:\.\d+)?(?:\s*(?:trillion|billion|million|thousand|B|M|K))?",
            re.IGNORECASE,
        )
        self.date_pattern = re.compile(
            r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\b|\b\d{4}-\d{2}-\d{2}\b",
            re.IGNORECASE,
        )

    def extract_mentions(self, text: str) -> List[MentionSpan]:
        """Extract all financial entity and attribute spans from text."""
        mentions: List[MentionSpan] = []
        seen_spans = set()

        # 1. Money patterns
        for m in self.money_pattern.finditer(text):
            span_key = (m.start(), m.end())
            if span_key not in seen_spans:
                seen_spans.add(span_key)
                mentions.append(MentionSpan(start=m.start(), end=m.end(), text=m.group(), label="MONEY"))

        # 2. Date patterns
        for m in self.date_pattern.finditer(text):
            span_key = (m.start(), m.end())
            if span_key not in seen_spans:
                seen_spans.add(span_key)
                mentions.append(MentionSpan(start=m.start(), end=m.end(), text=m.group(), label="DATE"))

        # 3. Known Org Aliases
        text_lower = text.lower()
        for alias, ticker in self.alias_to_ticker.items():
            pattern = r"\b" + re.escape(alias) + r"\b"
            for m in re.finditer(pattern, text_lower):
                span_key = (m.start(), m.end())
                if span_key not in seen_spans:
                    seen_spans.add(span_key)
                    mentions.append(
                        MentionSpan(start=m.start(), end=m.end(), text=text[m.start() : m.end()], label="ORG")
                    )

        # 4. Tickers (restricted by allowlist to prevent false positives on common caps like "US", "A", "AND")
        for m in self.ticker_pattern.finditer(text):
            tok = m.group().upper()
            # Only match if in allowlist and not already consumed by an ORG
            if tok in self.tickers_allowlist:
                span_key = (m.start(), m.end())
                if span_key not in seen_spans:
                    seen_spans.add(span_key)
                    mentions.append(MentionSpan(start=m.start(), end=m.end(), text=m.group(), label="TICKER"))

        mentions.sort(key=lambda s: s.start)
        return mentions
