"""API tests for /qa endpoint."""

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


def test_qa_endpoint_grounded_citations():
    """Verify POST /qa produces grounded answer with valid citations."""
    payload = {
        "question": "What did JPMorgan say about credit risk allowance in 2023?",
        "entity": "JPM",
        "before": "2024-03-01",
        "limit": 5,
    }
    resp = client.post("/qa", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert "answer_text" in data
    assert len(data["answer_text"]) > 20
    assert "citations" in data
    assert len(data["citations"]) >= 1
    assert 0.0 <= data["confidence"] <= 1.0
    assert not data["no_evidence"]


def test_qa_endpoint_no_evidence_fallback():
    """Verify negative out-of-corpus query returns no_evidence=True."""
    payload = {
        "question": "What were the orbital mining colonies revenues in 1890?",
        "entity": "JPM",
        "before": "1890-01-01",
        "limit": 5,
    }
    resp = client.post("/qa", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["no_evidence"] is True
    assert "no evidence found" in data["answer_text"].lower()
    assert data["confidence"] == 0.0
