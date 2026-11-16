"""Unit tests for document provenance and cryptographic hashing."""

from __future__ import annotations

import pytest

from src.utils.provenance import (
    ChunkProvenance,
    DocumentProvenance,
    compute_sha256,
    create_chunk_provenance,
)


def test_sha256_determinism():
    """Verify SHA-256 computation is deterministic and reproducible."""
    content_a = "JPMorgan credit risk disclosures 2023."
    content_b = "JPMorgan credit risk disclosures 2023."
    content_c = "JPMorgan credit risk disclosures 2024."

    hash_a = compute_sha256(content_a)
    hash_b = compute_sha256(content_b)
    hash_c = compute_sha256(content_c)

    assert hash_a == hash_b
    assert hash_a != hash_c
    assert len(hash_a) == 64


def test_chunk_provenance_schema():
    """Verify chunk provenance carries full audit trail."""
    doc_prov = DocumentProvenance(
        source_url="https://www.sec.gov/edgar/data/19617/doc.htm",
        filing_date="2024-02-16",
        cik="0000019617",
        ticker="JPM",
        form="10-K",
        sha256="abc123hash",
    )

    chunk_prov = create_chunk_provenance(
        doc_prov=doc_prov,
        chunk_id="JPM_10-K_2024-02-16_0001",
        doc_id="0000019617_10-K_2024-02-16",
        chunk_text="Allowance for credit losses increased.",
        section="Item 1A. Risk Factors",
    )

    assert chunk_prov.ticker == "JPM"
    assert chunk_prov.cik == "0000019617"
    assert chunk_prov.section == "Item 1A. Risk Factors"
    assert chunk_prov.source_url == doc_prov.source_url
    assert len(chunk_prov.sha256) == 64
