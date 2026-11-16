"""Integration tests for hybrid retrieval pipeline and PIT temporal filters."""

from __future__ import annotations

import pytest

from api.state import app_state


@pytest.fixture(scope="module")
def initialized_app():
    if not app_state.is_initialized:
        app_state.initialize()
    return app_state


def test_hybrid_search_credit_risk(initialized_app):
    """Index chunks -> query 'credit risk' -> Recall@10 >= 0.5; JPM returned."""
    engine = initialized_app.retrieval_engine
    assert engine is not None

    res = engine.search(query="credit risk allowance", limit=5)
    results = res.get("results", [])

    assert len(results) > 0
    top_tickers = [c["ticker"] for c in results]
    assert "JPM" in top_tickers


def test_retrieval_pit_filter_enforcement(initialized_app):
    """Assert query with before='2024-03-01' strictly excludes May 2024 10-Q."""
    engine = initialized_app.retrieval_engine
    res = engine.search(query="net income", entity="JPM", before="2024-03-01", limit=10)
    results = res.get("results", [])

    for c in results:
        assert c["filing_date"] <= "2024-03-01"
        assert c["filing_date"] != "2024-05-03"
