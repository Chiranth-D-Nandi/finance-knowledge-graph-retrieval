"""Volatility Anomaly Detection and EGARCH Conditional Variance Forecasting."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from src.config import settings

logger = logging.getLogger("fin_nexus.volatility")


class VolatilityAnomalyDetector:
    """
    Market Volatility Regime and Volume Anomaly Detector using
    GARCH conditional volatility intervals and Isolation Forest.
    """

    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.iso_forest = IsolationForest(
            n_estimators=100,
            contamination=0.05,
            random_state=self.random_state,
        )

    def analyze_event_window(
        self,
        ohlcv_df: pd.DataFrame,
        event_date: str,
        window_days: int = 20,
    ) -> Dict[str, Any]:
        """
        Evaluate whether the post-event volatility or trading volume constitutes an anomaly.
        """
        df = ohlcv_df.copy()
        df["date"] = pd.to_datetime(df["date"])
        df.sort_values("date", inplace=True)
        df.reset_index(drop=True, inplace=True)

        ev_dt = pd.to_datetime(event_date)
        df["ret"] = np.log(df["close"] / df["close"].shift(1))
        df["realized_vol_20"] = df["ret"].rolling(20).std() * np.sqrt(252)
        df["vol_ratio"] = df["volume"] / df["volume"].rolling(20).mean()
        df.dropna(inplace=True)

        if len(df) < 50:
            return {
                "vol_flag": False,
                "anomaly_score": 0.0,
                "realized_vol": 0.15,
                "volume_ratio": 1.0,
                "note": "Insufficient price history for robust volatility modeling.",
            }

        # Train Isolation Forest on pre-event baseline
        pre_event = df[df["date"] < ev_dt]
        if len(pre_event) < 30:
            pre_event = df.iloc[:40]

        X_train = pre_event[["realized_vol_20", "vol_ratio"]].values
        self.iso_forest.fit(X_train)

        # Evaluate window around event
        post_event = df[(df["date"] >= ev_dt) & (df["date"] <= ev_dt + pd.Timedelta(days=window_days))]
        if post_event.empty:
            post_event = df.iloc[-5:]

        X_test = post_event[["realized_vol_20", "vol_ratio"]].values
        scores = self.iso_forest.decision_function(X_test)
        preds = self.iso_forest.predict(X_test)

        anomaly_detected = bool(np.any(preds == -1))
        min_score = float(np.min(scores))
        latest_vol = float(post_event["realized_vol_20"].mean())
        latest_vol_ratio = float(post_event["vol_ratio"].mean())

        # GARCH-style conditional volatility forecast
        try:
            from arch import arch_model
            am = arch_model(df["ret"].values * 100, p=1, q=1, vol="EGARCH", dist="normal")
            res = am.fit(disp="off", show_warning=False)
            forecast = res.forecast(horizon=5)
            cond_vol = float(np.sqrt(forecast.variance.iloc[-1, 0]) * np.sqrt(252) / 100)
        except Exception:
            cond_vol = latest_vol * 1.05

        return {
            "vol_flag": anomaly_detected,
            "anomaly_score": round(min_score, 4),
            "realized_vol_annualized": round(latest_vol, 4),
            "volume_multiple": round(latest_vol_ratio, 2),
            "egarch_5d_vol_forecast": round(cond_vol, 4),
            "vol_regime": "High Volatility Spike" if anomaly_detected else "Normal Regime",
        }
