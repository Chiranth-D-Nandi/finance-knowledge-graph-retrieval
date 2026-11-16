"""Timeline endpoint router driven by Knowledge Graph."""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from api.schemas import TimelineResponse
from api.state import app_state

router = APIRouter(prefix="", tags=["timeline"])


@router.get("/timeline/{ticker}", response_model=TimelineResponse)
async def get_entity_timeline(
    ticker: str,
    from_date: Optional[str] = Query(None, alias="from", description="Start date YYYY-MM-DD"),
    to_date: Optional[str] = Query(None, alias="to", description="End date YYYY-MM-DD"),
):
    if not app_state.is_initialized or app_state.kg_builder is None:
        raise HTTPException(status_code=503, detail="Knowledge Graph is initializing.")

    t_upper = ticker.upper()
    events = app_state.kg_builder.get_ticker_timeline(
        ticker=t_upper,
        from_date=from_date,
        to_date=to_date,
    )

    return {
        "ticker": t_upper,
        "events_count": len(events),
        "events": events,
    }
