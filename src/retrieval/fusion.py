"""Reciprocal Rank Fusion (RRF) for Hybrid Lexical and Semantic Retrieval."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple


def reciprocal_rank_fusion(
    ranked_lists: List[List[Tuple[Dict[str, Any], float]]],
    k: int = 60,
    top_n: int = 50,
) -> List[Dict[str, Any]]:
    """
    Combine multiple ranked candidate lists using Reciprocal Rank Fusion (RRF).
    score(d) = sum(1.0 / (k + rank_i(d))) for all lists where document d appears.
    """
    rrf_scores: Dict[str, float] = {}
    chunk_store: Dict[str, Dict[str, Any]] = {}
    component_ranks: Dict[str, Dict[str, int]] = {}

    for list_idx, rank_list in enumerate(ranked_lists):
        list_name = f"list_{list_idx}"
        for rank, (chunk, original_score) in enumerate(rank_list, start=1):
            chunk_id = chunk["chunk_id"]
            chunk_store[chunk_id] = chunk

            if chunk_id not in rrf_scores:
                rrf_scores[chunk_id] = 0.0
                component_ranks[chunk_id] = {}

            rrf_scores[chunk_id] += 1.0 / (k + rank)
            component_ranks[chunk_id][list_name] = rank

    # Sort candidates by descending RRF score
    sorted_chunks = sorted(rrf_scores.items(), key=lambda item: item[1], reverse=True)

    fused_results: List[Dict[str, Any]] = []
    for chunk_id, score in sorted_chunks[:top_n]:
        item = dict(chunk_store[chunk_id])
        item["rrf_score"] = round(score, 6)
        item["component_ranks"] = component_ranks.get(chunk_id, {})
        fused_results.append(item)

    return fused_results
