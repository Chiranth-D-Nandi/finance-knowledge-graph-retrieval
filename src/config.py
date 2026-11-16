"""Central configuration using pydantic-settings."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Workspace Root
ROOT_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # SEC EDGAR Requirements
    SEC_USER_AGENT_EMAIL: str = Field(
        default="research.analyst@financial-platform.internal",
        description="User-Agent email for SEC EDGAR 10 req/s compliance",
    )

    # API Keys (Optional with graceful degradation)
    FRED_API_KEY: Optional[str] = Field(default=None)
    OPENAI_API_KEY: Optional[str] = Field(default=None)
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None)
    HF_TOKEN: Optional[str] = Field(default=None)

    # Model IDs (Pinned Hugging Face models per §4)
    EMBEDDING_MODEL: str = "BAAI/bge-base-en-v1.5"
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L6-v2"
    QWEN_MODEL: str = "Qwen/Qwen2.5-3B-Instruct"
    SENTIMENT_MODEL: str = "ProsusAI/finbert"
    USE_API_LLM_FALLBACK: bool = True

    # Reproducibility & Devices
    SEED: int = 42
    DEVICE: str = "cuda" if os.environ.get("FORCE_CPU") != "1" else "cpu"
    LOG_LEVEL: str = "INFO"

    # Directory Paths
    DATA_DIR: Path = ROOT_DIR / "data"
    RAW_DIR: Path = ROOT_DIR / "data" / "raw"
    EDGAR_RAW_DIR: Path = ROOT_DIR / "data" / "raw" / "edgar"
    MARKET_RAW_DIR: Path = ROOT_DIR / "data" / "raw" / "market"
    MACRO_RAW_DIR: Path = ROOT_DIR / "data" / "raw" / "macro"
    ENTITIES_RAW_DIR: Path = ROOT_DIR / "data" / "raw" / "entities"
    PROCESSED_DIR: Path = ROOT_DIR / "data" / "processed"
    BENCHMARKS_DIR: Path = ROOT_DIR / "data" / "benchmarks"
    SPLITS_DIR: Path = ROOT_DIR / "data" / "splits"
    LOGS_DIR: Path = ROOT_DIR / "logs"

    # Ingestion & Retrieval Hyperparameters
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50
    BM25_K1: float = 1.5
    BM25_B: float = 0.75
    RRF_K: int = 60
    TOP_K_CANDIDATES: int = 50
    TOP_K_FINAL: int = 10
    LINKER_THRESHOLD: float = 0.70


# Global singleton settings
settings = Settings()
