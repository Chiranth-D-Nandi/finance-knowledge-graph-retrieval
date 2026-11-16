"""End-to-End integration test covering the 4 core financial terminal workflows."""

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


def test_complete_e2e_analyst_workflow():
    """
    Simulate complete Equity Research Analyst workflow:
    1. Entity search & typeahead for JPMorgan Chase
    2. Hybrid Search for credit risk disclosures
    3. Grounded QA with per-sentence evidence citations
    4. Timeline retrieval from Knowledge Graph
    5. Market Impact event study analysis
    """
    # Step 1: Entity Lookup
    ent_resp = client.get("/entity/search?q=JPMorgan")
    assert ent_resp.status_code == 200
    candidates = ent_resp.json().get("candidates", [])
    assert len(candidates) > 0
    assert candidates[0]["ticker"] == "JPM"

    # Step 2: Hybrid Search under PIT constraint
    search_resp = client.get("/search?q=credit%20risk&entity=JPM&before=2024-03-01&limit=5")
    assert search_resp.status_code == 200
    search_data = search_resp.json()
    assert len(search_data["results"]) > 0
    top_chunk = search_data["results"][0]
    assert top_chunk["ticker"] == "JPM"
    assert top_chunk["filing_date"] <= "2024-03-01"

    # Step 3: Grounded QA with Citations
    qa_resp = client.post("/qa", json={
        "question": "What did JPMorgan say about credit risk allowance in its 2023 10-K?",
        "entity": "JPM",
        "before": "2024-03-01",
        "limit": 5,
    })
    assert qa_resp.status_code == 200
    qa_data = qa_resp.json()
    assert len(qa_data["citations"]) >= 1
    assert "JPMorgan" in qa_data["answer_text"]

    # Step 4: Temporal Timeline from KG
    timeline_resp = client.get("/timeline/JPM")
    assert timeline_resp.status_code == 200
    timeline_data = timeline_resp.json()
    assert timeline_data["ticker"] == "JPM"
    assert len(timeline_data["events"]) > 0

    # Step 5: Market Impact Event Study
    impact_resp = client.get("/impact/filing:JPM:10-K:2024-02-16")
    assert impact_resp.status_code == 200
    impact_data = impact_resp.json()
    assert impact_data["ticker"] == "JPM"
    assert "car" in impact_data
    assert "chart_points" in impact_data
    assert len(impact_data["chart_points"]) > 0
