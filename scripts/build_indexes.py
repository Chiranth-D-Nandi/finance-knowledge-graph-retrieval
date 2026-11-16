"""Build and persist BM25, Dense Embeddings, and Knowledge Graph."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from api.state import app_state
from src.config import settings
from src.ingest.entity_registry_builder import load_entity_registry
from src.processing.kg_builder import TemporalKGBuilder
from src.processing.xbrl_parser import XBRLParser

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("fin_nexus.build_indexes")


def main() -> None:
    logger.info("Building and persisting search indices...")
    settings.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load Registry
    entities = load_entity_registry()
    logger.info("Loaded %d entities from registry.", len(entities))

    # 2. Build or load chunks
    chunks_parquet = settings.PROCESSED_DIR / "chunks.parquet"
    if not chunks_parquet.exists():
        if not app_state.is_initialized:
            app_state.initialize()
        chunks = app_state.chunks
        df_chunks = pd.DataFrame(chunks)
        df_chunks.to_parquet(chunks_parquet, index=False)
        logger.info("Saved %d chunks to %s", len(df_chunks), chunks_parquet)
    else:
        df_chunks = pd.read_parquet(chunks_parquet)
        chunks = df_chunks.to_dict(orient="records")
        logger.info("Loaded %d existing chunks from %s", len(chunks), chunks_parquet)

    # 3. XBRL facts parsing
    xbrl_parser = XBRLParser()
    facts_df = xbrl_parser.parse_all(entities)

    # 4. KG Construction
    kg_builder = TemporalKGBuilder()
    kg_builder.build_graph(entity_registry=entities, chunks=chunks, xbrl_facts=facts_df)
    kg_builder.export_parquet()

    logger.info("All indices successfully built and persisted to %s", settings.PROCESSED_DIR)


if __name__ == "__main__":
    main()
