"""Unit tests for Event Study CAR calculation using production EventStudyAnalyzer."""

from __future__ import annotations

import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from src.analytics.event_study import EventStudyAnalyzer
from src.config import settings


def test_event_study_real_market_data():
    """Verify EventStudyAnalyzer computes real CAR on the ingested yahoo_ohlcv.parquet file."""
    parquet_path = settings.MARKET_RAW_DIR / "yahoo_ohlcv.parquet"
    assert parquet_path.exists(), "Market OHLCV parquet must exist for event study test."

    analyzer = EventStudyAnalyzer(market_data_path=parquet_path)
    res = analyzer.compute_car(
        ticker="JPM",
        event_date="2024-02-16",
        estimation_window=(-60, -10),
        event_window=(-1, 10),
        market_benchmark="SPY",
    )

    assert res["ticker"] == "JPM"
    assert "car" in res and isinstance(res["car"], float)
    assert "t_stat" in res and isinstance(res["t_stat"], float)
    assert 0.0 <= res["p_value"] <= 1.0
    assert "statistically_significant" in res and isinstance(res["statistically_significant"], bool)
    assert res["market_model"]["benchmark"] == "SPY"
    assert isinstance(res["market_model"]["beta"], float)
    assert len(res["chart_points"]) > 0


def test_event_study_synthetic_injected_shock():
    """Verify CAR regression and summation math against known injected return shock."""
    np.random.seed(42)
    n_days = 90
    dates = pd.date_range("2023-01-01", periods=n_days, freq="B")

    # True parameters: alpha = 0.0005, beta = 1.2
    alpha_true = 0.0005
    beta_true = 1.2
    mkt_returns = np.random.normal(0.0005, 0.01, n_days)
    stock_returns = alpha_true + beta_true * mkt_returns + np.random.normal(0, 0.001, n_days)

    # Inject abnormal return of +2.0% on event day (index 70)
    event_idx = 70
    stock_returns[event_idx] += 0.020

    # Build price paths from returns
    mkt_prices = 400.0 * np.exp(np.cumsum(mkt_returns))
    stock_prices = 150.0 * np.exp(np.cumsum(stock_returns))

    rows = []
    for d, sp, mp in zip(dates, stock_prices, mkt_prices):
        rows.append({"date": d, "ticker": "TEST", "close": sp, "volume": 1000000.0})
        rows.append({"date": d, "ticker": "SPY", "close": mp, "volume": 50000000.0})

    df = pd.DataFrame(rows)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_parquet = Path(tmpdir) / "test_ohlcv.parquet"
        df.to_parquet(tmp_parquet, index=False)

        analyzer = EventStudyAnalyzer(market_data_path=tmp_parquet)
        event_date_str = dates[event_idx].strftime("%Y-%m-%d")

        res = analyzer.compute_car(
            ticker="TEST",
            event_date=event_date_str,
            estimation_window=(-60, -10),
            event_window=(-1, 1),
            market_benchmark="SPY",
        )

        # Assert beta recovered near 1.2 and CAR captures the +2% shock
        assert 1.0 < res["market_model"]["beta"] < 1.4
        assert abs(res["car"] - 0.020) < 0.006


def test_event_study_missing_ticker_error():
    """Verify ValueError is raised if ticker is not present in market data."""
    analyzer = EventStudyAnalyzer()
    with pytest.raises(ValueError, match="Insufficient OHLCV data"):
        analyzer.compute_car(ticker="NONEXISTENT_TICKER", event_date="2024-02-16")


def test_event_study_missing_file_error():
    """Verify FileNotFoundError is raised if market data parquet does not exist."""
    analyzer = EventStudyAnalyzer(market_data_path=Path("nonexistent_path/fake.parquet"))
    with pytest.raises(FileNotFoundError):
        analyzer.compute_car(ticker="JPM", event_date="2024-02-16")
