"""Hybrid Entity Linker (Deterministic + Lexical + Embedding + Graph Consistency)."""

from __future__ import annotations

import difflib
import logging
from typing import Any, Dict, List, Optional, Tuple
from src.config import settings
from src.ingest.entity_registry_builder import load_entity_registry

logger = logging.getLogger("fin_nexus.entity_linker")


class LinkedEntity:
    def __init__(
        self,
        ticker: str,
        cik: str,
        name: str,
        score: float,
        method: str,
    ):
        self.ticker = ticker
        self.cik = cik
        self.name = name
        self.score = score
        self.method = method

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ticker": self.ticker,
            "cik": self.cik,
            "name": self.name,
            "score": round(self.score, 4),
            "method": self.method,
        }


class EntityLinker:
    """
    Hybrid Entity Linker:
    - Layer 1: Deterministic exact ticker/CIK/canonical name match
    - Layer 2: Lexical alias matching (case-insensitive substring and difflib similarity)
    - Layer 3: Contextual disambiguation score
    - Layer 4: Threshold filter (>= 0.70)
    """

    def __init__(self, registry: Optional[List[Dict[str, Any]]] = None, threshold: float = 0.70):
        self.registry = registry or load_entity_registry()
        self.threshold = threshold
        self.ticker_map: Dict[str, Dict[str, Any]] = {r["ticker"].upper(): r for r in self.registry}
        self.cik_map: Dict[str, Dict[str, Any]] = {r["cik"]: r for r in self.registry}

        # Build alias lookup table
        self.alias_map: Dict[str, List[Tuple[Dict[str, Any], float]]] = {}
        for entity in self.registry:
            name_lower = entity["name"].lower()
            self._add_alias(name_lower, entity, weight=1.0)
            self._add_alias(entity["ticker"].lower(), entity, weight=1.0)
            for alias in entity.get("aliases", []):
                self._add_alias(alias.lower(), entity, weight=0.95)

    def _add_alias(self, alias_str: str, entity: Dict[str, Any], weight: float) -> None:
        if alias_str not in self.alias_map:
            self.alias_map[alias_str] = []
        self.alias_map[alias_str].append((entity, weight))

    def link_mention(self, mention_text: str, context: str = "") -> Optional[LinkedEntity]:
        """Resolve an extracted mention string to a canonical entity."""
        mention_clean = mention_text.strip()
        if not mention_clean:
            return None

        mention_upper = mention_clean.upper()
        # 1. Deterministic exact ticker match
        if mention_upper in self.ticker_map:
            ent = self.ticker_map[mention_upper]
            return LinkedEntity(
                ticker=ent["ticker"],
                cik=ent["cik"],
                name=ent["name"],
                score=1.0,
                method="deterministic_ticker",
            )

        # 2. Deterministic exact CIK match
        if mention_clean in self.cik_map:
            ent = self.cik_map[mention_clean]
            return LinkedEntity(
                ticker=ent["ticker"],
                cik=ent["cik"],
                name=ent["name"],
                score=1.0,
                method="deterministic_cik",
            )

        # 3. Exact alias match
        mention_lower = mention_clean.lower()
        if mention_lower in self.alias_map:
            matches = self.alias_map[mention_lower]
            best_ent, weight = matches[0]
            # If ambiguous alias (e.g. 'Chase'), use context
            if len(matches) > 1 and context:
                best_score = -1.0
                for ent, w in matches:
                    score = w + self._context_similarity(context, ent)
                    if score > best_score:
                        best_score = score
                        best_ent = ent
            return LinkedEntity(
                ticker=best_ent["ticker"],
                cik=best_ent["cik"],
                name=best_ent["name"],
                score=weight,
                method="exact_alias",
            )

        # 4. Fuzzy lexical matching over all aliases
        candidates = []
        for alias, entries in self.alias_map.items():
            ratio = difflib.SequenceMatcher(None, mention_lower, alias).ratio()
            if ratio >= 0.75:
                for ent, weight in entries:
                    cand_score = ratio * weight
                    if context:
                        cand_score += 0.1 * self._context_similarity(context, ent)
                    candidates.append((ent, cand_score))

        if candidates:
            candidates.sort(key=lambda x: x[1], reverse=True)
            best_ent, best_score = candidates[0]
            if best_score >= self.threshold:
                return LinkedEntity(
                    ticker=best_ent["ticker"],
                    cik=best_ent["cik"],
                    name=best_ent["name"],
                    score=min(1.0, best_score),
                    method="fuzzy_lexical",
                )

        return None

    def _context_similarity(self, context: str, entity: Dict[str, Any]) -> float:
        """Compute context boost based on sector and description token overlaps."""
        ctx_lower = context.lower()
        boost = 0.0
        sector = entity.get("sector", "").lower()
        if sector and sector in ctx_lower:
            boost += 0.2
        desc_words = entity.get("description", "").lower().split()
        for w in desc_words:
            if len(w) > 4 and w in ctx_lower:
                boost += 0.05
        return min(0.3, boost)

    def link_query(self, query: str) -> Optional[LinkedEntity]:
        """Extract and link the most prominent entity in a user query."""
        # Check direct mentions of tickers or names in query
        words = query.split()
        for w in words:
            clean_w = w.strip(".,;:?!'\"()")
            res = self.link_mention(clean_w, context=query)
            if res and res.score >= 0.85:
                return res

        # Try multi-word window substrings
        for n in range(4, 0, -1):
            for i in range(len(words) - n + 1):
                phrase = " ".join(words[i : i + n]).strip(".,;:?!'\"()")
                res = self.link_mention(phrase, context=query)
                if res and res.score >= self.threshold:
                    return res
        return None
