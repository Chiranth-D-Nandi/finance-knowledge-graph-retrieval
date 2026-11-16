"""Econometric Event Study: Market Model and Cumulative Abnormal Return (CAR) vs SPY."""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats

from src.config import settings

logger = logging.getLogger("fin_nexus.event_study")


class EventStudyAnalyzer:
    """
    Classical Market Model Event Study:
    R_it = alpha + beta * R_mt + eps
    Estimation window: [t - 60, t - 10]
    Event window: [t - 1, t + 10]
    """

    def __init__(self, market_data_path: Optional[str] = None):
        self.market_parquet = market_data_path or (settings.MARKET_RAW_DIR / "yahoo_ohlcv.parquet")
        self._price_df: Optional[pd.DataFrame] = None

    def _load_data(self) -> pd.DataFrame:
        if self._price_df is None:
            if not self.market_parquet.exists():
                raise FileNotFoundError(f"Market OHLCV data missing: {self.market_parquet}")
            self._price_df = pd.read_parquet(self.market_parquet)
            self._price_df["date"] = pd.to_datetime(self._price_df["date"])
        return self._price_df

    def compute_car(
        self,
        ticker: str,
        event_date: str | datetime | date,
        estimation_window: Tuple[int, int] = (-60, -10),
        event_window: Tuple[int, int] = (-1, 10),
        market_benchmark: str = "SPY",
    ) -> Dict[str, Any]:
        """
        Calculate Cumulative Abnormal Return (CAR) and statistical significance.
        """
        df = self._load_data()
        ev_dt = pd.to_datetime(event_date)

        # Filter price history for ticker and benchmark
        df_t = df[df["ticker"] == ticker.upper()].copy()
        df_m = df[df["ticker"] == market_benchmark.upper()].copy()

        if df_t.empty or df_m.empty:
            raise ValueError(f"Insufficient OHLCV data for {ticker} or {market_benchmark}.")

        # Merge ticker and market on date
        merged = pd.merge(
            df_t[["date", "close", "volume"]],
            df_m[["date", "close"]],
            on="date",
            suffixes=("_stock", "_mkt"),
        ).sort_values("date").reset_index(drop=True)

        if len(merged) < 40:
            raise ValueError(f"Not enough trading days for event study ({len(merged)} found).")

        # Compute log returns
        merged["ret_stock"] = np.log(merged["close_stock"] / merged["close_stock"].shift(1))
        merged["ret_mkt"] = np.log(merged["close_mkt"] / merged["close_mkt"].shift(1))
        merged.dropna(subset=["ret_stock", "ret_mkt"], inplace=True)

        # Locate closest trading day to event date
        merged["date_diff"] = (merged["date"] - ev_dt).abs()
        event_idx = merged["date_diff"].idxmin()
        actual_event_date = merged.loc[event_idx, "date"].strftime("%Y-%m-%d")

        # Relative trading day indices
        merged["t"] = np.arange(len(merged)) - event_idx

        # Estimation window
        est_mask = (merged["t"] >= estimation_window[0]) & (merged["t"] <= estimation_window[1])
        est_data = merged[est_mask]

        if len(est_data) < 20:
            # Fallback estimation if window is constrained
            alpha = 0.0
            beta = 1.0
            sigma_eps = est_data["ret_stock"].std() if not est_data.empty else 0.015
        else:
            # OLS Regression: R_it = alpha + beta * R_mt
            x = est_data["ret_mkt"].values
            y = est_data["ret_stock"].values
            slope, intercept, r_val, p_val, std_err = stats.linregress(x, y)
            alpha = float(intercept)
            beta = float(slope)
            residuals = y - (alpha + beta * x)
            sigma_eps = float(np.std(residuals, ddof=2))

        # Event window
        ev_mask = (merged["t"] >= event_window[0]) & (merged["t"] <= event_window[1])
        ev_data = merged[ev_mask].copy()

        if ev_data.empty:
            raise ValueError(f"No trading data available in event window {event_window}.")

        ev_data["expected_ret"] = alpha + beta * ev_data["ret_mkt"]
        ev_data["abnormal_ret"] = ev_data["ret_stock"] - ev_data["expected_ret"]
        ev_data["cum_abnormal_ret"] = ev_data["abnormal_ret"].cumsum()

        # Cumulative Abnormal Return (CAR)
        car = float(ev_data["cum_abnormal_ret"].iloc[-1])
        n_days = len(ev_data)
        car_std_err = float(sigma_eps * np.sqrt(n_days))
        t_stat = float(car / car_std_err) if car_std_err > 0 else 0.0
        p_value = float(2 * (1 - stats.norm.cdf(abs(t_stat))))

        # Chart payload for frontend
        chart_points = []
        for _, row in ev_data.iterrows():
            chart_points.append({
                "date": row["date"].strftime("%Y-%m-%d"),
                "t": int(row["t"]),
                "close": round(float(row["close_stock"]), 2),
                "volume": float(row["volume"]),
                "abnormal_return": round(float(row["abnormal_ret"]), 4),
                "car": round(float(row["cum_abnormal_ret"]), 4),
            })

        return {
            "ticker": ticker.upper(),
            "target_event_date": str(event_date),
            "actual_event_date": actual_event_date,
            "market_model": {
                "alpha": round(alpha, 6),
                "beta": round(beta, 4),
                "benchmark": market_benchmark,
            },
            "car": round(car, 4),
            "t_stat": round(t_stat, 3),
            "p_value": round(p_value, 4),
            "statistically_significant": bool(p_value < 0.05),
            "event_window": event_window,
            "chart_points": chart_points,
            "interpretation": (
                f"Statistically significant abnormal return of {car*100:+.2f}% (p={p_value:.3f})"
                if p_value < 0.05
                else f"No statistically significant abnormal price reaction: CAR={car*100:+.2f}% (p={p_value:.3f})"
            ),
        }
