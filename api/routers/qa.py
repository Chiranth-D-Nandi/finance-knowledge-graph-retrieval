"""Grounded QA endpoint router."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.schemas import QARequest, QAResponseSchema
from api.state import app_state

router = APIRouter(prefix="", tags=["qa"])


def _clean_for_json(obj):
    """Recursively convert NumPy structures and non-standard types to Python primitives."""
    if hasattr(obj, "tolist"):
        return obj.tolist()
    if hasattr(obj, "item"):
        return obj.item()
    if isinstance(obj, dict):
        return {k: _clean_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_clean_for_json(v) for v in obj]
    return obj


@router.post("/qa", response_model=QAResponseSchema)
async def generate_grounded_answer(request: QARequest):
    if not app_state.is_initialized or app_state.retrieval_engine is None or app_state.qa_engine is None:
        raise HTTPException(status_code=503, detail="QA and Retrieval services are initializing.")

    try:
        # 1. Retrieve top-10 chunks under PIT constraint
        retrieval_res = app_state.retrieval_engine.search(
            query=request.question,
            entity=request.entity,
            before=request.before,
            limit=request.limit,
            explain=False,
        )
        chunks = retrieval_res.get("results", [])

        # 2. Generate grounded answer with citations
        qa_res = app_state.qa_engine.generate_answer(
            question=request.question,
            retrieved_chunks=chunks,
            entity_filter=request.entity,
            before_date=request.before,
        )

        return _clean_for_json(qa_res.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"QA generation failed: {str(e)}")
