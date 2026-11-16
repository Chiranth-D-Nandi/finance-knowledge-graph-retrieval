"""Unit tests for Pandera and Pydantic validators."""

from __future__ import annotations

import datetime
import pandas as pd
import pytest
from pydantic import ValidationError

from src.ingest.validators import FilingMetadata, validate_filing_metadata, validate_ohlcv_dataframe


def test_valid_ohlcv_dataframe():
    """Verify clean OHLCV data passes all invariant checks."""
    df = pd.DataFrame({
        "date": [pd.Timestamp("2024-01-02"), pd.Timestamp("2024-01-03")],
        "ticker": ["JPM", "JPM"],
        "open": [170.0, 172.0],
        "high": [173.0, 175.0],
        "low": [169.0, 171.0],
        "close": [172.5, 174.0],
        "volume": [1000000.0, 1200000.0],
    })
    validated = validate_ohlcv_dataframe(df)
    assert len(validated) == 2


def test_invalid_ohlcv_high_less_than_close():
    """Verify invariant failure when High < Close."""
    df = pd.DataFrame({
        "date": [pd.Timestamp("2024-01-02")],
        "ticker": ["AAPL"],
        "open": [180.0],
        "high": [182.0],  # Less than close
        "low": [179.0],
        "close": [185.0],
        "volume": [500000.0],
    })
    with pytest.raises(Exception):
        validate_ohlcv_dataframe(df)


def test_invalid_ohlcv_low_greater_than_open():
    """Verify invariant failure when Low > Open."""
    df = pd.DataFrame({
        "date": [pd.Timestamp("2024-01-02")],
        "ticker": ["AAPL"],
        "open": [180.0],
        "high": [190.0],
        "low": [185.0],  # Low > Open
        "close": [188.0],
        "volume": [500000.0],
    })
    with pytest.raises(Exception):
        validate_ohlcv_dataframe(df)


def test_empty_ohlcv_rejection():
    """Verify rejection of empty DataFrame."""
    with pytest.raises(ValueError, match="empty"):
        validate_ohlcv_dataframe(pd.DataFrame())


def test_valid_filing_metadata():
    """Verify valid SEC filing metadata formatting."""
    meta = validate_filing_metadata({
        "cik": "19617",
        "ticker": "JPM",
        "form": "10-K",
        "filing_date": "2024-02-16",
        "accession_number": "0000019617-24-000273",
        "source_url": "https://www.sec.gov/Archives/edgar/data/19617/000001961724000273/doc.htm",
        "content_raw": "A" * 150,
    })
    assert meta.cik == "0000019617"  # 10-digit zero padded
    assert meta.ticker == "JPM"


def test_invalid_cik_format():
    """Verify rejection of non-numeric CIK."""
    with pytest.raises(ValidationError):
        validate_filing_metadata({
            "cik": "INVALID_CIK",
            "ticker": "JPM",
            "form": "10-K",
            "filing_date": "2024-02-16",
            "accession_number": "0000019617-24-000273",
            "source_url": "https://www.sec.gov",
            "content_raw": "A" * 150,
        })


def test_future_filing_date_rejection():
    """Verify rejection of impossible future filing dates."""
    future_date = (datetime.date.today() + datetime.timedelta(days=30)).isoformat()
    with pytest.raises(ValidationError):
        validate_filing_metadata({
            "cik": "0000019617",
            "ticker": "JPM",
            "form": "10-K",
            "filing_date": future_date,
            "accession_number": "0000019617-24-000273",
            "source_url": "https://www.sec.gov",
            "content_raw": "A" * 150,
        })
