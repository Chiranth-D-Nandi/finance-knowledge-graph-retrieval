"""Unified Hybrid Retrieval Engine with Point-in-Time Guarantees."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd

from src.config import settings
from src.processing.entity_linker import EntityLinker, LinkedEntity
from src.retrieval.bm25_index import BM25Index
from src.retrieval.dense_index import DenseIndex
from src.retrieval.fusion import reciprocal_rank_fusion
from src.retrieval.reranker import CrossEncoderReranker
from src.utils.temporal import filter_pit_candidates

logger = logging.getLogger("fin_nexus.retrieval_engine")


class RetrievalEngine:
    """
    Production-grade hybrid financial retrieval engine:
    Entity Resolution -> Lexical (BM25) + Semantic (BGE) -> RRF (k=60) -> MiniLM Rerank -> PIT Filter
    """

    def __init__(
        self,
        chunks: Optional[List[Dict[str, Any]]] = None,
        entity_registry: Optional[List[Dict[str, Any]]] = None,
    ):
        self.chunks: List[Dict[str, Any]] = chunks or []
        self.entity_linker = EntityLinker(registry=entity_registry)
        self.bm25_index = BM25Index(k1=settings.BM25_K1, b=settings.BM25_B)
        self.dense_index = DenseIndex(model_name=settings.EMBEDDING_MODEL, device=settings.DEVICE)
        self.reranker = CrossEncoderReranker(model_name=settings.RERANKER_MODEL, device=settings.DEVICE)
        self._is_ready = False

        if self.chunks:
            self.index_chunks(self.chunks)

    def index_chunks(self, chunks: List[Dict[str, Any]]) -> None:
        """Index chunks across sparse and dense indices."""
        self.chunks = list(chunks)
        logger.info("Indexing %d chunks into BM25 and Dense BGE indices...", len(self.chunks))
        self.bm25_index.build(self.chunks)
        self.dense_index.build(self.chunks)
        self._is_ready = True
        logger.info("Hybrid indices successfully constructed.")

    def search(
        self,
        query: str,
        entity: Optional[str] = None,
        before: Optional[str] = None,
        limit: int = 10,
        explain: bool = False,
    ) -> Dict[str, Any]:
        """
        Execute full end-to-end hybrid retrieval with entity resolution and temporal constraints.
        """
        start_time = time.perf_counter()
        query_clean = query.strip()

        # 1. Entity Resolution
        linked_ent: Optional[LinkedEntity] = None
        target_entity = entity
        if not target_entity:
            linked_ent = self.entity_linker.link_query(query_clean)
            if linked_ent and linked_ent.score >= 0.70:
                target_entity = linked_ent.ticker

        # 2. Candidate Retrieval: BM25 (top-100) + Dense (top-100)
        # Apply PIT filter directly at retrieval candidate level
        bm25_candidates = self.bm25_index.search(
            query=query_clean,
            top_k=100,
            entity_filter=target_entity,
            before_date=before,
        )
        dense_candidates = self.dense_index.search(
            query=query_clean,
            top_k=100,
            entity_filter=target_entity,
            before_date=before,
        )

        # 3. Reciprocal Rank Fusion (k=60) -> Top 50
        fused_candidates = reciprocal_rank_fusion(
            ranked_lists=[bm25_candidates, dense_candidates],
            k=settings.RRF_K,
            top_n=settings.TOP_K_CANDIDATES,
        )

        # 4. Cross-Encoder Joint Reranking -> Top K
        reranked_results = self.reranker.rerank(
            query=query_clean,
            candidates=fused_candidates,
            top_k=limit,
        )

        # Final safety assertion: strictly enforce PIT filter
        if before:
            reranked_results = filter_pit_candidates(reranked_results, before_date=before)

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # Build structured response with provenance
        results_payload = []
        for rank, r in enumerate(reranked_results, start=1):
            raw_entities = r.get("entities", [])
            if hasattr(raw_entities, "tolist"):
                clean_entities = raw_entities.tolist()
            elif isinstance(raw_entities, (list, tuple)):
                clean_entities = [str(x) for x in raw_entities]
            else:
                clean_entities = []

            item = {
                "rank": rank,
                "chunk_id": str(r["chunk_id"]),
                "doc_id": str(r["doc_id"]),
                "ticker": str(r["ticker"]),
                "cik": str(r["cik"]),
                "form": str(r["form"]),
                "filing_date": str(r["filing_date"]),
                "section": str(r["section"]),
                "text": str(r["text"]),
                "source_url": str(r.get("source_url", "")),
                "sha256": str(r.get("sha256", "")),
                "rerank_score": float(r.get("rerank_score", 0.0)),
                "rrf_score": float(r.get("rrf_score", 0.0)),
                "entities": clean_entities,
                "sentiment": r.get("sentiment"),
            }
            if explain:
                item["explanation"] = {
                    "bm25_rank": r.get("component_ranks", {}).get("list_0"),
                    "dense_rank": r.get("component_ranks", {}).get("list_1"),
                    "linked_entity": linked_ent.to_dict() if linked_ent else None,
                }
            results_payload.append(item)

        return {
            "query": query_clean,
            "entity_linked": linked_ent.to_dict() if linked_ent else ({"ticker": target_entity} if target_entity else None),
            "before": before,
            "total_results": len(results_payload),
            "latency_ms": elapsed_ms,
            "results": results_payload,
        }
