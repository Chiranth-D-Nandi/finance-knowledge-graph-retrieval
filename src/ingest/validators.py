"""Data schema validators and invariant enforcement using Pandera and Pydantic."""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any, Dict, List, Optional
import pandas as pd
import pandera as pa
from pandera import Check, Column, DataFrameSchema
from pydantic import BaseModel, Field, field_validator


# Pandera schema for Market OHLCV data
OHLCVSchema = DataFrameSchema(
    columns={
        "date": Column(pa.DateTime, nullable=False),
        "ticker": Column(pa.String, nullable=False),
        "open": Column(pa.Float, checks=Check.gt(0), nullable=False),
        "high": Column(pa.Float, checks=Check.gt(0), nullable=False),
        "low": Column(pa.Float, checks=Check.gt(0), nullable=False),
        "close": Column(pa.Float, checks=Check.gt(0), nullable=False),
        "volume": Column(pa.Float, checks=Check.ge(0), nullable=False),
    },
    checks=[
        # Invariant 1: High >= Open
        Check(lambda df: (df["high"] >= df["open"] - 1e-4).all(), error="High must be >= Open"),
        # Invariant 2: High >= Close
        Check(lambda df: (df["high"] >= df["close"] - 1e-4).all(), error="High must be >= Close"),
        # Invariant 3: Low <= Open
        Check(lambda df: (df["low"] <= df["open"] + 1e-4).all(), error="Low must be <= Open"),
        # Invariant 4: Low <= Close
        Check(lambda df: (df["low"] <= df["close"] + 1e-4).all(), error="Low must be <= Close"),
    ],
    coerce=True,
    strict=False,
)


def validate_ohlcv_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Validate a DataFrame containing OHLCV price series against invariants."""
    if df.empty:
        raise ValueError("OHLCV DataFrame cannot be empty.")
    return OHLCVSchema.validate(df)


# Pydantic schema for raw SEC filing metadata
class FilingMetadata(BaseModel):
    cik: str = Field(..., description="10-digit zero-padded SEC Central Index Key")
    ticker: str = Field(..., description="Canonical stock symbol")
    form: str = Field(..., description="Form type: 10-K, 10-Q, 8-K")
    filing_date: str = Field(..., description="ISO 8601 filing date YYYY-MM-DD")
    accession_number: str = Field(..., description="SEC EDGAR accession number")
    source_url: str = Field(..., description="Canonical SEC URL")
    content_raw: str = Field(..., description="HTML or plain text filing content")

    @field_validator("cik")
    @classmethod
    def validate_cik_format(cls, v: str) -> str:
        v_clean = v.strip()
        if not re.match(r"^\d{1,10}$", v_clean):
            raise ValueError(f"Invalid CIK format: {v}. Must be up to 10 digits.")
        return v_clean.zfill(10)

    @field_validator("content_raw")
    @classmethod
    def validate_non_empty_content(cls, v: str) -> str:
        if not v or len(v.strip()) < 100:
            raise ValueError("Filing content is empty or contains less than 100 characters.")
        return v

    @field_validator("filing_date")
    @classmethod
    def validate_filing_date(cls, v: str) -> str:
        parsed = datetime.strptime(v.split("T")[0].strip(), "%Y-%m-%d").date()
        if parsed > date.today():
            raise ValueError(f"Filing date {v} is in the future. Today is {date.today()}.")
        return v


def validate_filing_metadata(data: Dict[str, Any]) -> FilingMetadata:
    """Validate raw filing metadata and content."""
    return FilingMetadata(**data)
