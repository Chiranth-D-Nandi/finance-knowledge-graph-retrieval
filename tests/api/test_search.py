"""API tests for /search endpoint."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.state import app_state

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_app():
    if not app_state.is_initialized:
        app_state.initialize()


def test_search_endpoint_success():
    """Verify GET /search returns 200 and structured results with provenance."""
    resp = client.get("/search?q=credit%20risk&limit=5")
    assert resp.status_code == 200
    data = resp.json()

    assert data["query"] == "credit risk"
    assert "latency_ms" in data
    assert len(data["results"]) <= 5

    first = data["results"][0]
    assert "chunk_id" in first
    assert "source_url" in first
    assert "filing_date" in first
    assert "rerank_score" in first


def test_search_with_entity_filter():
    """Verify entity filter isolates results to requested ticker."""
    resp = client.get("/search?q=revenue&entity=AAPL&limit=5")
    assert resp.status_code == 200
    data = resp.json()

    for item in data["results"]:
        assert item["ticker"] == "AAPL"


def test_search_validation_empty_query():
    """Verify 422 Unprocessable Entity when query string is empty."""
    resp = client.get("/search?q=")
    assert resp.status_code == 422
