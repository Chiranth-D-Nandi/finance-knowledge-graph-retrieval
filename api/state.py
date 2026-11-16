"""Global service state and singleton container for the API."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.analytics.event_study import EventStudyAnalyzer
from src.analytics.volatility import VolatilityAnomalyDetector
from src.config import settings
from src.generation.qa_engine import QAEngine
from src.ingest.entity_registry_builder import load_entity_registry
from src.processing.kg_builder import TemporalKGBuilder
from src.retrieval.engine import RetrievalEngine

logger = logging.getLogger("financial_platform.state")


class AppState:
    def __init__(self):
        self.entity_registry: List[Dict[str, Any]] = []
        self.chunks: List[Dict[str, Any]] = []
        self.retrieval_engine: Optional[RetrievalEngine] = None
        self.qa_engine: Optional[QAEngine] = None
        self.kg_builder: Optional[TemporalKGBuilder] = None
        self.event_study: Optional[EventStudyAnalyzer] = None
        self.vol_detector: Optional[VolatilityAnomalyDetector] = None
        self.last_ingest_time: Optional[str] = None
        self.is_initialized: bool = False

    def initialize(self) -> None:
        """Initialize all components, loading processed data or baseline fixtures."""
        logger.info("Initializing AppState...")
        # 1. Load Entity Registry
        self.entity_registry = load_entity_registry()

        # 2. Load Processed Chunks if available, else load curated seed fixtures
        chunks_parquet = settings.PROCESSED_DIR / "chunks.parquet"
        if chunks_parquet.exists():
            import pandas as pd
            df = pd.read_parquet(chunks_parquet)
            raw_records = df.to_dict(orient="records")
            # Sanitize numpy arrays/types to pure Python primitives
            sanitized = []
            for r in raw_records:
                clean_r = {}
                for k, v in r.items():
                    if hasattr(v, "tolist"):
                        clean_r[k] = v.tolist()
                    elif hasattr(v, "item"):
                        clean_r[k] = v.item()
                    else:
                        clean_r[k] = v
                sanitized.append(clean_r)
            self.chunks = sanitized
            logger.info("Loaded %d pre-processed chunks from %s", len(self.chunks), chunks_parquet)
        else:
            self.chunks = self._generate_seed_chunks()
            logger.info("Generated %d seed demonstration chunks.", len(self.chunks))

        # 3. Build Retrieval Engine
        self.retrieval_engine = RetrievalEngine(
            chunks=self.chunks,
            entity_registry=self.entity_registry,
        )

        # 4. Initialize QA Engine
        self.qa_engine = QAEngine()

        # 5. Initialize KG
        self.kg_builder = TemporalKGBuilder()
        self.kg_builder.build_graph(
            entity_registry=self.entity_registry,
            chunks=self.chunks,
        )

        # 6. Initialize Analytics
        self.event_study = EventStudyAnalyzer()
        self.vol_detector = VolatilityAnomalyDetector()

        self.last_ingest_time = "2026-11-16T19:00:00Z"
        self.is_initialized = True
        logger.info("AppState initialization complete.")

    def _generate_seed_chunks(self) -> List[Dict[str, Any]]:
        """Generate high-quality foundational seed chunks covering key S&P 50 entities for instant demonstration."""
        seed_data = [
            {
                "ticker": "JPM",
                "cik": "0000019617",
                "form": "10-K",
                "filing_date": "2024-02-16",
                "section": "Item 1A. Risk Factors",
                "text": "JPMorgan Chase faces significant credit risk across consumer and wholesale loan portfolios. In 2023, the firm increased its allowance for credit losses to $14.3 billion, reflecting higher net charge-offs in credit card services and potential commercial real estate office sector deterioration. Management actively monitors macro interest rate paths and sovereign debt default probabilities.",
                "source_url": "https://www.sec.gov/ix?doc=/Archives/edgar/data/0000019617/000001961724000273/jpm-20231231.htm",
                "sentiment": {"positive": 0.05, "negative": 0.85, "neutral": 0.10, "label": "negative"},
                "entities": ["JPM"],
            },
            {
                "ticker": "JPM",
                "cik": "0000019617",
                "form": "10-K",
                "filing_date": "2024-02-16",
                "section": "Item 7. MD&A",
                "text": "For the year ended December 31, 2023, JPMorgan Chase reported net income of $49.6 billion, or $16.23 per share, compared with $37.7 billion, or $12.09 per share, for 2022. Total net revenue on a managed basis was $162.4 billion, up 23% from the prior year, driven by higher net interest income following the Federal Reserve rate hikes and First Republic acquisition.",
                "source_url": "https://www.sec.gov/ix?doc=/Archives/edgar/data/0000019617/000001961724000273/jpm-20231231.htm",
                "sentiment": {"positive": 0.88, "negative": 0.04, "neutral": 0.08, "label": "positive"},
                "entities": ["JPM"],
            },
            {
                "ticker": "JPM",
                "cik": "0000019617",
                "form": "10-Q",
                "filing_date": "2024-05-03",
                "section": "Item 2. MD&A",
                "text": "First quarter 2024 net income for JPMorgan Chase was $13.4 billion, supported by resilient consumer spending and firm underwriting fees in investment banking. Credit costs included $1.9 billion of provision for credit losses.",
                "source_url": "https://www.sec.gov/ix?doc=/Archives/edgar/data/0000019617/000001961724000312/jpm-20240331.htm",
                "sentiment": {"positive": 0.75, "negative": 0.15, "neutral": 0.10, "label": "positive"},
                "entities": ["JPM"],
            },
            {
                "ticker": "AAPL",
                "cik": "0000320193",
                "form": "10-K",
                "filing_date": "2023-11-03",
                "section": "Item 1A. Risk Factors",
                "text": "Apple is exposed to global supply chain concentration risks, component shortages, and foreign exchange volatility. Substantially all of Apple's manufacturing is performed by outsourced partners located primarily in Asia, including mainland China, India, and Vietnam. Any trade restrictions, geopolitical tensions, or regional natural disasters could materially affect hardware gross margins.",
                "source_url": "https://www.sec.gov/ix?doc=/Archives/edgar/data/0000320193/000032019323000106/aapl-20230930.htm",
                "sentiment": {"positive": 0.02, "negative": 0.88, "neutral": 0.10, "label": "negative"},
                "entities": ["AAPL"],
            },
            {
                "ticker": "AAPL",
                "cik": "0000320193",
                "form": "10-K",
                "filing_date": "2023-11-03",
                "section": "Item 7. MD&A",
                "text": "Total net sales in fiscal 2023 were $383.3 billion, a decrease of 3% compared to fiscal 2022. Services revenue reached an all-time record of $85.2 billion, up 9% year-over-year, driven by paid subscriptions across App Store, Cloud, and Apple Pay.",
                "source_url": "https://www.sec.gov/ix?doc=/Archives/edgar/data/0000320193/000032019323000106/aapl-20230930.htm",
                "sentiment": {"positive": 0.65, "negative": 0.20, "neutral": 0.15, "label": "positive"},
                "entities": ["AAPL"],
            },
            {
                "ticker": "MSFT",
                "cik": "0000789019",
                "form": "10-K",
                "filing_date": "2023-07-27",
                "section": "Item 1. Business",
                "text": "Microsoft Cloud revenue exceeded $110 billion in fiscal year 2023, up 22% year-over-year. The company expanded its partnership with OpenAI to accelerate AI breakthroughs, integrating Azure OpenAI Service into enterprise suites including Microsoft 365 Copilot and GitHub Copilot.",
                "source_url": "https://www.sec.gov/ix?doc=/Archives/edgar/data/0000789019/000078901923000078/msft-20230630.htm",
                "sentiment": {"positive": 0.92, "negative": 0.01, "neutral": 0.07, "label": "positive"},
                "entities": ["MSFT"],
            },
            {
                "ticker": "NVDA",
                "cik": "0001045810",
                "form": "10-K",
                "filing_date": "2024-02-21",
                "section": "Item 7. MD&A",
                "text": "Fiscal 2024 was a transformational year for NVIDIA as accelerated computing reached the inflection point. Revenue surged 126% to $60.9 billion, driven by Compute & Networking segment demand for Hopper architecture GPU platforms, including H100 and HGX, across cloud hyperscalers and generative AI startups.",
                "source_url": "https://www.sec.gov/ix?doc=/Archives/edgar/data/0001045810/000104581024000029/nvda-20240128.htm",
                "sentiment": {"positive": 0.96, "negative": 0.01, "neutral": 0.03, "label": "positive"},
                "entities": ["NVDA"],
            },
            {
                "ticker": "BAC",
                "cik": "0000070858",
                "form": "10-K",
                "filing_date": "2024-02-20",
                "section": "Item 1A. Risk Factors",
                "text": "Bank of America's net interest yield is subject to monetary policy adjustments by the Federal Reserve and changes in benchmark interest rates. Deposits competition could compress net interest margin while unrealized losses in held-to-maturity securities remain a function of long-term yields.",
                "source_url": "https://www.sec.gov/ix?doc=/Archives/edgar/data/0000070858/000007085824000054/bac-20231231.htm",
                "sentiment": {"positive": 0.08, "negative": 0.72, "neutral": 0.20, "label": "negative"},
                "entities": ["BAC"],
            },
        ]

        chunks = []
        for i, s in enumerate(seed_data):
            c_id = f"{s['ticker']}_{s['form']}_{s['filing_date']}_{i:04d}"
            d_id = f"{s['cik']}_{s['form']}_{s['filing_date']}"
            chunks.append({
                "chunk_id": c_id,
                "doc_id": d_id,
                "text": s["text"],
                "section": s["section"],
                "ticker": s["ticker"],
                "cik": s["cik"],
                "form": s["form"],
                "filing_date": s["filing_date"],
                "source_url": s["source_url"],
                "sha256": f"seed_sha256_{i}",
                "entities": s.get("entities", [s["ticker"]]),
                "sentiment": s.get("sentiment"),
            })
        return chunks


app_state = AppState()
