"""Pydantic schemas for FastAPI endpoints."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    q: str = Field(..., min_length=1, max_length=500, description="Search query string")
    entity: Optional[str] = Field(default=None, description="Optional canonical ticker filter")
    before: Optional[str] = Field(default=None, description="ISO date YYYY-MM-DD for PIT filtering")
    limit: int = Field(default=10, ge=1, le=50, description="Max results to return")
    explain: bool = Field(default=False, description="Include component retrieval scores and linker details")


class SearchResultItem(BaseModel):
    rank: int
    chunk_id: str
    doc_id: str
    ticker: str
    cik: str
    form: str
    filing_date: str
    section: str
    text: str
    source_url: str
    rerank_score: float
    rrf_score: float
    entities: List[str] = Field(default_factory=list)
    sentiment: Optional[Dict[str, Any]] = None
    explanation: Optional[Dict[str, Any]] = None


class SearchResponse(BaseModel):
    query: str
    entity_linked: Optional[Dict[str, Any]] = None
    before: Optional[str] = None
    total_results: int
    latency_ms: float
    results: List[SearchResultItem]


class QARequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000, description="Financial question")
    entity: Optional[str] = Field(default=None, description="Optional entity filter")
    before: Optional[str] = Field(default=None, description="ISO date for point-in-time boundary")
    limit: int = Field(default=10, ge=1, le=20)


class CitationSchema(BaseModel):
    source_id: int
    chunk_id: Optional[str] = None
    excerpt: str
    url: str


class QAResponseSchema(BaseModel):
    answer_text: str
    citations: List[CitationSchema]
    confidence: float
    no_evidence: bool = False
    latency_ms: float
    retrievals: List[Dict[str, Any]] = Field(default_factory=list)


class TimelineEvent(BaseModel):
    date: str
    type: str
    title: str
    summary: str
    source_url: str
    node_id: Optional[str] = None


class TimelineResponse(BaseModel):
    ticker: str
    events_count: int
    events: List[TimelineEvent]


class ImpactResponse(BaseModel):
    event_id: str
    ticker: str
    target_event_date: str
    actual_event_date: str
    car: float
    t_stat: float
    p_value: float
    statistically_significant: bool
    vol_flag: bool
    interpretation: str
    market_model: Dict[str, Any]
    chart_points: List[Dict[str, Any]]


class EntityDossier(BaseModel):
    ticker: str
    cik: str
    name: str
    aliases: List[str]
    sector: str
    isin: Optional[str] = None
    qid: Optional[str] = None
    description: str
    filings_count: int
    kg_degree: int
    sentiment_summary: Dict[str, Any]
