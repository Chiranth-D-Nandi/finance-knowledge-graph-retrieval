"""Temporal Leakage Harness: Asserts Point-in-Time correctness across 20 test fixtures."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Tuple
from src.retrieval.engine import RetrievalEngine

logger = logging.getLogger("fin_nexus.temporal_harness")

# 20 Canonical Temporal Test Fixtures
TEMPORAL_FIXTURES: List[Dict[str, Any]] = [
    {
        "id": "T01",
        "query": "JPMorgan credit risk allowance and charge-offs",
        "entity": "JPM",
        "before": "2024-03-01",
        "future_filing_dates": ["2024-05-03", "2024-08-02", "2024-11-01", "2025-02-14"],
    },
    {
        "id": "T02",
        "query": "Apple supply chain risk and manufacturing concentration",
        "entity": "AAPL",
        "before": "2023-12-01",
        "future_filing_dates": ["2024-02-02", "2024-05-03", "2024-08-02", "2024-11-01"],
    },
    {
        "id": "T03",
        "query": "Microsoft Cloud Azure revenue growth and OpenAI partnership",
        "entity": "MSFT",
        "before": "2023-09-01",
        "future_filing_dates": ["2023-10-24", "2024-01-30", "2024-04-25", "2024-07-30"],
    },
    {
        "id": "T04",
        "query": "NVIDIA accelerated computing Hopper H100 revenue surge",
        "entity": "NVDA",
        "before": "2024-01-15",
        "future_filing_dates": ["2024-02-21", "2024-05-22", "2024-08-28", "2024-11-20"],
    },
    {
        "id": "T05",
        "query": "Bank of America net interest yield deposit costs",
        "entity": "BAC",
        "before": "2024-01-01",
        "future_filing_dates": ["2024-02-20", "2024-04-30", "2024-07-30", "2024-10-29"],
    },
    {
        "id": "T06",
        "query": "Tesla vehicle delivery gross margin automotive regulatory credits",
        "entity": "TSLA",
        "before": "2023-12-31",
        "future_filing_dates": ["2024-01-29", "2024-04-23", "2024-07-23", "2024-10-23"],
    },
    {
        "id": "T07",
        "query": "Amazon AWS operating income retail margins",
        "entity": "AMZN",
        "before": "2023-10-01",
        "future_filing_dates": ["2023-10-26", "2024-02-01", "2024-04-30", "2024-08-01"],
    },
    {
        "id": "T08",
        "query": "Alphabet Google advertising search revenue generative AI search",
        "entity": "GOOGL",
        "before": "2023-11-15",
        "future_filing_dates": ["2024-01-30", "2024-04-25", "2024-07-23", "2024-10-29"],
    },
    {
        "id": "T09",
        "query": "Meta Platforms advertising impressions family of apps headcount restructuring",
        "entity": "META",
        "before": "2023-08-01",
        "future_filing_dates": ["2023-10-25", "2024-02-01", "2024-04-24", "2024-07-31"],
    },
    {
        "id": "T10",
        "query": "ExxonMobil upstream oil production refining crack spreads",
        "entity": "XOM",
        "before": "2023-09-15",
        "future_filing_dates": ["2023-10-27", "2024-02-02", "2024-04-26", "2024-08-02"],
    },
    {
        "id": "T11",
        "query": "Johnson & Johnson medical devices pharmaceutical oncology pipeline",
        "entity": "JNJ",
        "before": "2023-12-15",
        "future_filing_dates": ["2024-01-23", "2024-04-16", "2024-07-17", "2024-10-15"],
    },
    {
        "id": "T12",
        "query": "Visa payment volume transaction processing cross-border fees",
        "entity": "V",
        "before": "2023-10-01",
        "future_filing_dates": ["2023-10-24", "2024-01-25", "2024-04-23", "2024-07-23"],
    },
    {
        "id": "T13",
        "query": "Walmart comparable sales grocery market share e-commerce growth",
        "entity": "WMT",
        "before": "2023-11-01",
        "future_filing_dates": ["2023-11-16", "2024-02-20", "2024-05-16", "2024-08-15"],
    },
    {
        "id": "T14",
        "query": "Procter & Gamble organic sales price elasticity commodities",
        "entity": "PG",
        "before": "2023-09-01",
        "future_filing_dates": ["2023-10-18", "2024-01-23", "2024-04-19", "2024-07-30"],
    },
    {
        "id": "T15",
        "query": "Chevron Permian Basin oil production capital expenditure",
        "entity": "CVX",
        "before": "2023-10-01",
        "future_filing_dates": ["2023-10-27", "2024-02-02", "2024-04-26", "2024-08-02"],
    },
    {
        "id": "T16",
        "query": "UnitedHealth Medical Care Ratio Medicare Advantage Optum revenue",
        "entity": "UNH",
        "before": "2023-12-01",
        "future_filing_dates": ["2024-01-12", "2024-04-16", "2024-07-16", "2024-10-15"],
    },
    {
        "id": "T17",
        "query": "Home Depot customer transactions average ticket mortgage rates",
        "entity": "HD",
        "before": "2023-10-15",
        "future_filing_dates": ["2023-11-14", "2024-02-20", "2024-05-14", "2024-08-13"],
    },
    {
        "id": "T18",
        "query": "Eli Lilly Mounjaro tirzepatide clinical trials oncology",
        "entity": "LLY",
        "before": "2023-09-01",
        "future_filing_dates": ["2023-11-02", "2024-02-06", "2024-04-30", "2024-08-08"],
    },
    {
        "id": "T19",
        "query": "Costco membership renewal rate fee increase warehouse expansion",
        "entity": "COST",
        "before": "2023-11-15",
        "future_filing_dates": ["2023-12-14", "2024-03-07", "2024-05-30", "2024-09-26"],
    },
    {
        "id": "T20",
        "query": "Broadcom VMware acquisition semiconductor networking software",
        "entity": "AVGO",
        "before": "2023-11-01",
        "future_filing_dates": ["2023-12-07", "2024-03-07", "2024-06-12", "2024-09-05"],
    },
]


def run_temporal_leakage_suite(retrieval_engine: RetrievalEngine) -> Dict[str, Any]:
    """
    Execute 20 fixtures against retrieval engine with strict temporal constraints.
    Returns pass count, total count, and leakage log.
    """
    passed = 0
    total = len(TEMPORAL_FIXTURES)
    violations = []

    for fix in TEMPORAL_FIXTURES:
        res = retrieval_engine.search(
            query=fix["query"],
            entity=fix["entity"],
            before=fix["before"],
            limit=10,
        )
        returned_chunks = res.get("results", [])

        # Check whether any returned chunk has filing_date > before
        leakage = [
            c for c in returned_chunks
            if c.get("filing_date", "") > fix["before"]
        ]

        if not leakage:
            passed += 1
        else:
            violations.append({
                "fixture_id": fix["id"],
                "before": fix["before"],
                "leaked_dates": [c.get("filing_date") for c in leakage],
            })

    return {
        "passed": passed,
        "total": total,
        "pass_rate": round(passed / total, 4),
        "violations": violations,
    }
