"""Entity dossier and typeahead search router."""

from __future__ import annotations

from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, Query

from api.schemas import EntityDossier
from api.state import app_state

router = APIRouter(prefix="/entity", tags=["entity"])


@router.get("/search")
async def search_entities(q: str = Query(..., min_length=1, description="Entity prefix or alias")):
    if not app_state.is_initialized:
        raise HTTPException(status_code=503, detail="Entity registry is initializing.")

    query_lower = q.lower().strip()
    candidates = []

    for ent in app_state.entity_registry:
        t_match = ent["ticker"].lower().startswith(query_lower)
        name_match = query_lower in ent["name"].lower()
        alias_match = any(query_lower in a.lower() for a in ent.get("aliases", []))

        if t_match or name_match or alias_match:
            score = 1.0 if t_match else (0.9 if name_match else 0.75)
            candidates.append({
                "ticker": ent["ticker"],
                "name": ent["name"],
                "sector": ent["sector"],
                "score": score,
            })

    candidates.sort(key=lambda x: x["score"], reverse=True)
    return {"candidates": candidates[:10]}


@router.get("/{ticker}", response_model=EntityDossier)
async def get_entity_dossier(ticker: str):
    if not app_state.is_initialized:
        raise HTTPException(status_code=503, detail="Entity registry is initializing.")

    t_upper = ticker.upper()
    ent = next((e for e in app_state.entity_registry if e["ticker"] == t_upper), None)
    if not ent:
        raise HTTPException(status_code=404, detail=f"Entity '{ticker}' not found in registry.")

    # Calculate KG degree and filing count
    filings_count = sum(1 for c in app_state.chunks if c.get("ticker") == t_upper)
    kg_degree = 4 + filings_count  # Baseline relations in multi-graph

    # Sentiment summary
    t_chunks = [c for c in app_state.chunks if c.get("ticker") == t_upper]
    pos = sum(1 for c in t_chunks if c.get("sentiment", {}).get("label") == "positive")
    neg = sum(1 for c in t_chunks if c.get("sentiment", {}).get("label") == "negative")
    neu = max(0, len(t_chunks) - pos - neg)

    return {
        "ticker": ent["ticker"],
        "cik": ent["cik"],
        "name": ent["name"],
        "aliases": ent.get("aliases", []),
        "sector": ent["sector"],
        "isin": ent.get("isin"),
        "qid": ent.get("qid"),
        "description": ent.get("description", ""),
        "filings_count": filings_count,
        "kg_degree": kg_degree,
        "sentiment_summary": {
            "positive_count": pos,
            "negative_count": neg,
            "neutral_count": neu,
            "total_chunks": len(t_chunks),
        },
    }
