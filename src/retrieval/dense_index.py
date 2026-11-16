"""Dense semantic retrieval index using BGE (BAAI/bge-base-en-v1.5)."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import torch

from src.config import settings

logger = logging.getLogger("fin_nexus.dense_index")


class DenseIndex:
    """
    Dense semantic vector index using BAAI/bge-base-en-v1.5.
    Encodes passages offline and queries with canonical BGE prefix.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        device: Optional[str] = None,
    ):
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.device = device or settings.DEVICE
        self._model = None
        self.chunks: List[Dict[str, Any]] = []
        self.embeddings: Optional[np.ndarray] = None  # shape (N, 768)

    def _get_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading dense embedding model '%s' on %s...", self.model_name, self.device)
            self._model = SentenceTransformer(self.model_name, device=self.device)
        return self._model

    def build(self, chunks: List[Dict[str, Any]], batch_size: int = 32) -> np.ndarray:
        """Encode all chunk texts and store normalized embeddings in memory."""
        self.chunks = list(chunks)
        if not self.chunks:
            self.embeddings = np.zeros((0, 768), dtype=np.float32)
            return self.embeddings

        model = self._get_model()
        texts = [c["text"] for c in self.chunks]

        logger.info("Encoding %d passages with batch size %d...", len(texts), batch_size)
        with torch.inference_mode():
            if self.device == "cuda" and torch.cuda.is_available():
                with torch.autocast("cuda", dtype=torch.float16):
                    embs = model.encode(
                        texts,
                        batch_size=batch_size,
                        show_progress_bar=False,
                        normalize_embeddings=True,
                    )
            else:
                embs = model.encode(
                    texts,
                    batch_size=batch_size,
                    show_progress_bar=False,
                    normalize_embeddings=True,
                )

        self.embeddings = np.array(embs, dtype=np.float32)
        return self.embeddings

    def search(
        self,
        query: str,
        top_k: int = 100,
        entity_filter: Optional[str] = None,
        before_date: Optional[str] = None,
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Query dense semantic index with BGE instruction prefix.
        Returns list of (chunk, cosine_similarity_score).
        """
        if self.embeddings is None or len(self.chunks) == 0:
            return []

        model = self._get_model()
        # BGE query instruction prefix
        formatted_query = f"Represent this sentence for searching relevant passages: {query}"

        with torch.inference_mode():
            if self.device == "cuda" and torch.cuda.is_available():
                with torch.autocast("cuda", dtype=torch.float16):
                    q_emb = model.encode(formatted_query, normalize_embeddings=True)
            else:
                q_emb = model.encode(formatted_query, normalize_embeddings=True)

        q_vec = np.array(q_emb, dtype=np.float32)
        # Cosine similarity via dot product of normalized vectors
        scores = np.dot(self.embeddings, q_vec)

        ranked_indices = np.argsort(scores)[::-1]
        results: List[Tuple[Dict[str, Any], float]] = []

        for idx in ranked_indices:
            score = float(scores[idx])
            chunk = self.chunks[idx]

            # Entity filter
            if entity_filter and chunk.get("ticker", "").upper() != entity_filter.upper():
                continue
            # PIT temporal filter
            if before_date and chunk.get("filing_date", "") > before_date:
                continue

            results.append((chunk, score))
            if len(results) >= top_k:
                break

        return results
