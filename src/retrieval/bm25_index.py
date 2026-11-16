"""Sparse lexical BM25 retrieval index using rank-bm25."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple
from rank_bm25 import BM25Okapi

from src.config import settings


def tokenize_financial_text(text: str) -> List[str]:
    """Tokenize text preserving alphanumeric symbols, tickers, and financial decimals."""
    clean = re.sub(r"[^\w\.\$\%]", " ", text.lower())
    tokens = [t.strip("._") for t in clean.split() if len(t.strip("._")) > 1]
    return tokens


class BM25Index:
    """BM25 Okapi lexical index over chunk corpus."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.bm25: Optional[BM25Okapi] = None
        self.chunks: List[Dict[str, Any]] = []

    def build(self, chunks: List[Dict[str, Any]]) -> None:
        """Build BM25 index over provided chunk records."""
        self.chunks = list(chunks)
        tokenized_corpus = [tokenize_financial_text(c["text"]) for c in self.chunks]
        self.bm25 = BM25Okapi(tokenized_corpus, k1=self.k1, b=self.b)

    def search(
        self,
        query: str,
        top_k: int = 100,
        entity_filter: Optional[str] = None,
        before_date: Optional[str] = None,
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Execute BM25 search with optional entity and PIT temporal filters.
        Returns list of (chunk, bm25_score).
        """
        if self.bm25 is None or not self.chunks:
            return []

        tok_query = tokenize_financial_text(query)
        if not tok_query:
            return []

        raw_scores = self.bm25.get_scores(tok_query)
        ranked_indices = sorted(range(len(raw_scores)), key=lambda i: raw_scores[i], reverse=True)

        results: List[Tuple[Dict[str, Any], float]] = []
        for idx in ranked_indices:
            score = float(raw_scores[idx])
            if score <= 0.0:
                continue

            chunk = self.chunks[idx]
            # Entity filter
            if entity_filter and chunk.get("ticker", "").upper() != entity_filter.upper():
                continue
            # PIT temporal filter
            if before_date and chunk.get("filing_date", "") > before_date:
                continue

            results.append((chunk, score))
            if len(results) >= top_k:
                break

        return results
