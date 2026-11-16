"""Search endpoint router."""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from api.schemas import SearchResponse
from api.state import app_state

router = APIRouter(prefix="", tags=["search"])


@router.get("/search", response_model=SearchResponse)
async def search_filings(
    q: str = Query(..., min_length=1, description="Financial search query"),
    entity: Optional[str] = Query(None, description="Canonical ticker symbol filter"),
    before: Optional[str] = Query(None, description="Point-in-time filing date upper bound (YYYY-MM-DD)"),
    limit: int = Query(10, ge=1, le=50, description="Max results to return"),
    explain: bool = Query(False, description="Include component scoring details"),
):
    if not app_state.is_initialized or app_state.retrieval_engine is None:
        raise HTTPException(status_code=503, detail="Retrieval engine is initializing. Please retry.")

    try:
        results = app_state.retrieval_engine.search(
            query=q,
            entity=entity,
            before=before,
            limit=limit,
            explain=explain,
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search execution failed: {str(e)}")
