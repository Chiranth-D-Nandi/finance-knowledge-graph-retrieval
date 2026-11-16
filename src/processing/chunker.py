"""Document Chunking and Section Tagging using Trafilatura."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional
import trafilatura
from bs4 import BeautifulSoup

from src.config import settings
from src.utils.provenance import ChunkProvenance, DocumentProvenance, compute_sha256

SECTION_PATTERNS = [
    (re.compile(r"item\s+1a[\.\:\s\-]+risk\s+factors", re.IGNORECASE), "Item 1A. Risk Factors"),
    (re.compile(r"item\s+1b[\.\:\s\-]+unresolved\s+staff\s+comments", re.IGNORECASE), "Item 1B. Unresolved Staff Comments"),
    (re.compile(r"item\s+1[\.\:\s\-]+business", re.IGNORECASE), "Item 1. Business"),
    (re.compile(r"item\s+7[\.\:\s\-]+management(?:'s)?\s+discussion\s+and\s+analysis", re.IGNORECASE), "Item 7. MD&A"),
    (re.compile(r"item\s+7a[\.\:\s\-]+quantitative\s+and\s+qualitative\s+disclosures", re.IGNORECASE), "Item 7A. Market Risk"),
    (re.compile(r"item\s+8[\.\:\s\-]+financial\s+statements", re.IGNORECASE), "Item 8. Financial Statements"),
    (re.compile(r"item\s+2[\.\:\s\-]+management(?:'s)?\s+discussion", re.IGNORECASE), "Item 2. MD&A (10-Q)"),
]


def extract_text_from_html(html_content: str) -> str:
    """Extract clean markdown/plain text from HTML using trafilatura with BeautifulSoup fallback."""
    extracted = trafilatura.extract(
        html_content,
        include_comments=False,
        include_tables=True,
        output_format="txt",
    )
    if extracted and len(extracted.strip()) > 100:
        return extracted

    # Fallback to BeautifulSoup if trafilatura stripped too much
    soup = BeautifulSoup(html_content, "html.parser")
    # Remove script and style elements
    for s in soup(["script", "style", "header", "footer", "nav"]):
        s.decompose()
    text = soup.get_text(separator="\n")
    # Clean whitespace
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


def detect_section(text_window: str) -> str:
    """Identify SEC filing section from header patterns within chunk context."""
    for pattern, section_name in SECTION_PATTERNS:
        if pattern.search(text_window[:300]):
            return section_name
    return "General Corporate Disclosures"


def chunk_document(
    doc_text: str,
    doc_prov: DocumentProvenance,
    chunk_size_tokens: int = 512,
    chunk_overlap_tokens: int = 50,
) -> List[Dict[str, Any]]:
    """
    Split document text into fixed-size overlapping chunks with provenance and section metadata.
    Uses approximate tokenization (1 token ~ 4 chars / 0.75 words) for speed and determinism.
    """
    words = doc_text.split()
    if not words:
        return []

    # Map target token size to word count: ~380 words for 512 tokens
    word_chunk_size = int(chunk_size_tokens * 0.75)
    word_overlap = int(chunk_overlap_tokens * 0.75)
    step = max(1, word_chunk_size - word_overlap)

    chunks: List[Dict[str, Any]] = []
    current_section = "Item 1. Business"

    for i in range(0, len(words), step):
        chunk_words = words[i : i + word_chunk_size]
        if not chunk_words:
            continue
        chunk_text = " ".join(chunk_words)

        # Check if a new section heading appears
        detected = detect_section(chunk_text)
        if detected != "General Corporate Disclosures":
            current_section = detected

        chunk_id = f"{doc_prov.ticker}_{doc_prov.form}_{doc_prov.filing_date}_{len(chunks):04d}"
        doc_id = f"{doc_prov.cik}_{doc_prov.form}_{doc_prov.filing_date}"

        prov = ChunkProvenance(
            chunk_id=chunk_id,
            doc_id=doc_id,
            source_url=doc_prov.source_url,
            filing_date=doc_prov.filing_date,
            cik=doc_prov.cik,
            ticker=doc_prov.ticker,
            form=doc_prov.form,
            section=current_section,
            sha256=compute_sha256(chunk_text),
            retrieved_at=doc_prov.retrieved_at,
        )

        chunks.append({
            "chunk_id": chunk_id,
            "doc_id": doc_id,
            "text": chunk_text,
            "section": current_section,
            "ticker": doc_prov.ticker,
            "cik": doc_prov.cik,
            "form": doc_prov.form,
            "filing_date": doc_prov.filing_date,
            "source_url": doc_prov.source_url,
            "sha256": prov.sha256,
            "entities": [],
            "sentiment": None,
        })

    return chunks
