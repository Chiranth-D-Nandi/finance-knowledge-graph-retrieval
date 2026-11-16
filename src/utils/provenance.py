"""Provenance tracking and validation for financial artifacts."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class DocumentProvenance(BaseModel):
    """Provenance metadata attached to ingested raw documents."""
    source_url: str = Field(..., description="Canonical source URL (e.g. SEC EDGAR archive)")
    retrieved_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp of retrieval"
    )
    filing_date: str = Field(..., description="ISO 8601 filing date YYYY-MM-DD")
    cik: str = Field(..., description="10-digit padded SEC Central Index Key")
    ticker: str = Field(..., description="Stock symbol / ticker")
    form: str = Field(..., description="Form type: 10-K, 10-Q, 8-K")
    sha256: str = Field(..., description="SHA-256 hash of raw document content")


class ChunkProvenance(BaseModel):
    """Provenance metadata embedded into indexed document chunks."""
    chunk_id: str
    doc_id: str
    source_url: str
    filing_date: str
    cik: str
    ticker: str
    form: str
    section: str = Field(default="Unspecified", description="Filing Item (e.g. Item 1A, Item 7)")
    sha256: str
    retrieved_at: str


def compute_sha256(content: str | bytes) -> str:
    """Compute deterministic SHA-256 hex digest of string or byte content."""
    if isinstance(content, str):
        content = content.encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def create_chunk_provenance(
    doc_prov: DocumentProvenance,
    chunk_id: str,
    doc_id: str,
    chunk_text: str,
    section: str = "Unspecified",
) -> ChunkProvenance:
    """Generate immutable provenance for an individual chunk."""
    return ChunkProvenance(
        chunk_id=chunk_id,
        doc_id=doc_id,
        source_url=doc_prov.source_url,
        filing_date=doc_prov.filing_date,
        cik=doc_prov.cik,
        ticker=doc_prov.ticker,
        form=doc_prov.form,
        section=section,
        sha256=compute_sha256(chunk_text),
        retrieved_at=doc_prov.retrieved_at,
    )
