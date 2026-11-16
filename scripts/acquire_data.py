"""Acquisition script for public datasets D1-D12."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.config import settings
from src.ingest.pipeline import IngestPipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(settings.LOGS_DIR / "acquire.log", mode="a", encoding="utf-8"),
    ],
)
logger = logging.getLogger("fin_nexus.acquire_data")


def main() -> None:
    parser = argparse.ArgumentParser(description="Public Dataset Acquisition")
    parser.add_argument(
        "--scope",
        type=str,
        choices=["minimal", "full"],
        default="minimal",
        help="Acquisition scope: 'minimal' (20 tickers, ~60 filings) or 'full' (50 tickers, ~600 filings)",
    )
    parser.add_argument(
        "--email",
        type=str,
        default=settings.SEC_USER_AGENT_EMAIL,
        help="User-Agent contact email for SEC EDGAR Fair Access compliance",
    )
    args = parser.parse_args()

    logger.info("Initializing data acquisition: scope=%s, email=%s", args.scope, args.email)
    pipeline = IngestPipeline(scope=args.scope, user_agent_email=args.email)
    summary = pipeline.run()

    summary_file = settings.LOGS_DIR / "acquisition_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    logger.info(
        "Acquisition successful. Entities: %d, Filings: %d, Market Rows: %d",
        summary["entities_count"],
        summary["filings_ingested"],
        summary["market_rows"],
    )


if __name__ == "__main__":
    main()
