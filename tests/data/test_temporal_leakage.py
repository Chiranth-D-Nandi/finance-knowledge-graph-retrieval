"""Parametrized Point-in-Time (PIT) Temporal Leakage Tests across 20 Fixtures."""

from __future__ import annotations

import pytest

from api.state import app_state
from eval.harness_temporal import TEMPORAL_FIXTURES


@pytest.fixture(scope="module", autouse=True)
def setup_app():
    if not app_state.is_initialized:
        app_state.initialize()


@pytest.mark.parametrize("fixture", TEMPORAL_FIXTURES, ids=[f["id"] for f in TEMPORAL_FIXTURES])
def test_temporal_leakage_fixture(fixture):
    """
    Assert that for a query with cut-off date T,
    no document filed after T is ever retrieved.
    """
    engine = app_state.retrieval_engine
    assert engine is not None

    res = engine.search(
        query=fixture["query"],
        entity=fixture["entity"],
        before=fixture["before"],
        limit=10,
    )

    results = res.get("results", [])
    cutoff = fixture["before"]

    for chunk in results:
        f_date = chunk.get("filing_date", "")
        assert f_date <= cutoff, (
            f"Temporal Leakage Violation in fixture {fixture['id']}: "
            f"Chunk {chunk['chunk_id']} has filing_date {f_date} > cutoff {cutoff}"
        )
