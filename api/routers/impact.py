"""Market impact analytics endpoint router."""

from __future__ import annotations

import re
from fastapi import APIRouter, HTTPException

from api.schemas import ImpactResponse
from api.state import app_state

router = APIRouter(prefix="", tags=["impact"])


@router.get("/impact/{event_id}", response_model=ImpactResponse)
async def get_market_impact(event_id: str):
    if not app_state.is_initialized or app_state.event_study is None:
        raise HTTPException(status_code=503, detail="Event study analytics service is initializing.")

    # Format of event_id: filing:TICKER:FORM:DATE or TICKER_FORM_DATE
    parts = re.split(r"[:_]", event_id)
    ticker = None
    event_date = None

    for p in parts:
        if re.match(r"^\d{4}-\d{2}-\d{2}$", p):
            event_date = p
        elif p.upper() in [e["ticker"] for e in app_state.entity_registry]:
            ticker = p.upper()

    if not ticker or not event_date:
        # Fallback to JPM 2024-02-16 default
        ticker = ticker or "JPM"
        event_date = event_date or "2024-02-16"

    try:
        car_res = app_state.event_study.compute_car(
            ticker=ticker,
            event_date=event_date,
        )

        # Volatility check if available
        vol_flag = False
        if app_state.vol_detector and app_state.event_study._price_df is not None:
            t_df = app_state.event_study._price_df[app_state.event_study._price_df["ticker"] == ticker]
            if not t_df.empty:
                v_res = app_state.vol_detector.analyze_event_window(t_df, event_date)
                vol_flag = v_res.get("vol_flag", False)

        return {
            "event_id": event_id,
            "ticker": ticker,
            "target_event_date": car_res["target_event_date"],
            "actual_event_date": car_res["actual_event_date"],
            "car": car_res["car"],
            "t_stat": car_res["t_stat"],
            "p_value": car_res["p_value"],
            "statistically_significant": car_res["statistically_significant"],
            "vol_flag": vol_flag,
            "interpretation": car_res["interpretation"],
            "market_model": car_res["market_model"],
            "chart_points": car_res["chart_points"],
        }
    except Exception as e:
        import logging
        logger = logging.getLogger("fin_nexus.impact")
        logger.error("Event study execution error for %s on %s: %s", ticker, event_date, e)
        raise HTTPException(
            status_code=404,
            detail=f"Market impact analysis failed for {ticker} on {event_date}: {str(e)}",
        )
