"""Ingestion pipeline orchestrating SEC EDGAR, Market Data, and Entity Registry."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd

from src.config import settings
from src.ingest.entity_registry_builder import EntityRegistryBuilder, load_entity_registry
from src.ingest.market_loader import MarketLoader
from src.ingest.sec_fetcher import SECFetcher
from src.ingest.validators import validate_filing_metadata
from src.utils.provenance import DocumentProvenance, compute_sha256

logger = logging.getLogger("fin_nexus.ingest_pipeline")


class IngestPipeline:
    def __init__(
        self,
        scope: str = "minimal",
        user_agent_email: Optional[str] = None,
    ):
        self.scope = scope  # "minimal" (20 tickers, 1 yr) or "full" (50 tickers, 3 yrs)
        self.email = user_agent_email or settings.SEC_USER_AGENT_EMAIL
        self.sec_fetcher = SECFetcher(user_agent_email=self.email)
        self.market_loader = MarketLoader()
        self.registry_builder = EntityRegistryBuilder()

    def run(self) -> Dict[str, Any]:
        """Execute the ingestion pipeline according to configured scope."""
        logger.info("Starting Ingestion Pipeline in '%s' scope...", self.scope)
        summary: Dict[str, Any] = {
            "scope": self.scope,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "entities_count": 0,
            "filings_ingested": 0,
            "market_rows": 0,
            "provenance_records": [],
        }

        # 1. Build Entity Registry
        entities = self.registry_builder.build()
        summary["entities_count"] = len(entities)

        target_tickers = [e["ticker"] for e in entities]
        if self.scope == "minimal":
            target_tickers = target_tickers[:20]

        # 2. Ingest Market OHLCV
        logger.info("Ingesting market data for %d tickers...", len(target_tickers))
        try:
            ohlcv_df = self.market_loader.fetch_ohlcv(
                tickers=target_tickers,
                start_date="2022-01-01" if self.scope == "minimal" else "2020-01-01",
                end_date="2025-11-01",
            )
            summary["market_rows"] = len(ohlcv_df)
        except Exception as e:
            logger.warning("Market download error (using offline mock if needed): %s", e)

        # 3. Ingest Macro Data
        self.market_loader.fetch_fred_macro()

        # 4. Ingest SEC EDGAR Filings & XBRL
        ingested_filings = []
        seen_accessions = set()

        for entity in entities:
            ticker = entity["ticker"]
            if ticker not in target_tickers:
                continue

            cik = entity["cik"]
            logger.info("Processing SEC EDGAR submissions for %s (CIK: %s)...", ticker, cik)

            try:
                # Fetch submissions metadata
                submissions = self.sec_fetcher.fetch_submissions(cik)
                # Fetch XBRL facts
                try:
                    self.sec_fetcher.fetch_xbrl_companyfacts(cik)
                except Exception as xbrl_err:
                    logger.debug("XBRL facts unavailable for %s: %s", ticker, xbrl_err)

                recent = submissions.get("filings", {}).get("recent", {})
                forms = recent.get("form", [])
                filing_dates = recent.get("filingDate", [])
                accessions = recent.get("accessionNumber", [])
                primary_docs = recent.get("primaryDocument", [])

                max_filings_per_ticker = 3 if self.scope == "minimal" else 15
                count = 0

                for form, f_date, acc, doc_name in zip(forms, filing_dates, accessions, primary_docs):
                    if form in ["10-K", "10-Q", "8-K"] and acc not in seen_accessions:
                        seen_accessions.add(acc)
                        try:
                            doc_path = self.sec_fetcher.fetch_filing_document(
                                cik=cik,
                                ticker=ticker,
                                form=form,
                                filing_date=f_date,
                                accession_number=acc,
                                primary_doc_name=doc_name,
                            )
                            with open(doc_path, "r", encoding="utf-8", errors="replace") as f:
                                raw_text = f.read()

                            # Compute Provenance
                            prov = DocumentProvenance(
                                source_url=f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc.replace('-', '')}/{doc_name}",
                                filing_date=f_date,
                                cik=cik,
                                ticker=ticker,
                                form=form,
                                sha256=compute_sha256(raw_text),
                            )
                            ingested_filings.append(prov.model_dump())
                            count += 1
                            if count >= max_filings_per_ticker:
                                break
                        except Exception as doc_err:
                            logger.warning("Could not download doc %s for %s: %s", doc_name, ticker, doc_err)

            except Exception as sub_err:
                logger.warning("Could not fetch submissions for %s: %s", ticker, sub_err)

        summary["filings_ingested"] = len(ingested_filings)
        summary["provenance_records"] = ingested_filings
        summary["completed_at"] = datetime.now(timezone.utc).isoformat()

        logger.info("Pipeline completed: %d filings, %d market rows.", len(ingested_filings), summary["market_rows"])
        return summary


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    pipeline = IngestPipeline(scope="minimal")
    res = pipeline.run()
    print("Ingestion Summary:", res)
