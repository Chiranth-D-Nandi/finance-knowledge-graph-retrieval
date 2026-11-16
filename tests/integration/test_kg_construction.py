"""Integration tests for Temporal Knowledge Graph construction."""

from __future__ import annotations

import pytest

from api.state import app_state
from src.processing.kg_builder import TemporalKGBuilder


@pytest.fixture(scope="module")
def initialized_app():
    if not app_state.is_initialized:
        app_state.initialize()
    return app_state


def test_kg_construction_node_and_edge_counts(initialized_app):
    """Verify graph holds Company and Filing nodes with issues edges."""
    kg = initialized_app.kg_builder
    assert kg is not None
    assert kg.graph.number_of_nodes() >= 50
    assert kg.graph.number_of_edges() >= 5

    # Assert company:JPM node exists
    assert kg.graph.has_node("company:JPM")
    node_data = kg.graph.nodes["company:JPM"]
    assert node_data["node_type"] == "Company"
    assert node_data["sector"] == "Financials"


def test_kg_timeline_query(initialized_app):
    """Verify chronological timeline extraction from graph."""
    kg = initialized_app.kg_builder
    timeline = kg.get_ticker_timeline("JPM")
    assert len(timeline) >= 2
    # Verify descending chronological order
    dates = [ev["date"] for ev in timeline]
    assert dates == sorted(dates, reverse=True)
