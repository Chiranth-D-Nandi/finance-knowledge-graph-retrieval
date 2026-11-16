"""Unit tests for Hybrid Entity Linker across 30 test cases."""

from __future__ import annotations

import pytest

from src.processing.entity_linker import EntityLinker

LINKER_TEST_CASES = [
    # Exact Tickers
    ("JPM", "JPM", 1.0),
    ("AAPL", "AAPL", 1.0),
    ("MSFT", "MSFT", 1.0),
    ("NVDA", "NVDA", 1.0),
    ("BAC", "BAC", 1.0),
    ("TSLA", "TSLA", 1.0),
    ("GOOGL", "GOOGL", 1.0),
    ("AMZN", "AMZN", 1.0),
    ("V", "V", 1.0),
    ("UNH", "UNH", 1.0),
    ("XOM", "XOM", 1.0),
    ("WMT", "WMT", 1.0),
    ("MA", "MA", 1.0),
    ("PG", "PG", 1.0),
    ("HD", "HD", 1.0),
    ("CVX", "CVX", 1.0),
    ("KO", "KO", 1.0),
    ("COST", "COST", 1.0),
    ("MRK", "MRK", 1.0),
    ("PEP", "PEP", 1.0),
    # Canonical Corporate Names & Aliases
    ("Apple", "AAPL", 0.95),
    ("Apple Inc.", "AAPL", 0.95),
    ("Microsoft", "MSFT", 0.95),
    ("Microsoft Corp", "MSFT", 0.95),
    ("Google", "GOOGL", 0.95),
    ("Alphabet Inc.", "GOOGL", 0.95),
    ("Amazon", "AMZN", 0.95),
    ("Nvidia", "NVDA", 0.95),
    ("JPMorgan Chase", "JPM", 0.95),
    ("Bank of America", "BAC", 0.95),
]


@pytest.fixture(scope="module")
def linker() -> EntityLinker:
    return EntityLinker()


@pytest.mark.parametrize("mention,expected_ticker,min_score", LINKER_TEST_CASES)
def test_entity_linker_resolution(linker: EntityLinker, mention: str, expected_ticker: str, min_score: float):
    """Verify high-precision entity resolution across 30 distinct corporate queries."""
    res = linker.link_mention(mention)
    assert res is not None, f"Failed to link mention: {mention}"
    assert res.ticker == expected_ticker, f"Expected {expected_ticker}, got {res.ticker}"
    assert res.score >= min_score


def test_ambiguous_alias_with_context(linker: EntityLinker):
    """Verify contextual disambiguation for ambiguous alias 'Chase'."""
    res = linker.link_mention("Chase", context="JPMorgan Chase financial banking credit risk")
    assert res is not None
    assert res.ticker == "JPM"


def test_unknown_entity_abstention(linker: EntityLinker):
    """Verify that unrelated/unknown strings remain unlinked."""
    res = linker.link_mention("NonExistentCorporationXYZ123")
    assert res is None
