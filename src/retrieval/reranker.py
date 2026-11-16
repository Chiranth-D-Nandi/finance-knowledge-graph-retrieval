"""Cross-Encoder Reranker using cross-encoder/ms-marco-MiniLM-L6-v2."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
import torch

from src.config import settings

logger = logging.getLogger("fin_nexus.reranker")


class CrossEncoderReranker:
    """
    Joint Cross-Encoder Reranker using ms-marco-MiniLM-L6-v2.
    Applies calibrated relevance scoring across fused candidates.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        device: Optional[str] = None,
    ):
        self.model_name = model_name or settings.RERANKER_MODEL
        self.device = device or settings.DEVICE
        self._model = None

    def _get_model(self):
        if self._model is None:
            from sentence_transformers import CrossEncoder
            logger.info("Loading cross-encoder reranker '%s' on %s...", self.model_name, self.device)
            self._model = CrossEncoder(self.model_name, device=self.device, max_length=512)
        return self._model

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = 10,
        batch_size: int = 32,
    ) -> List[Dict[str, Any]]:
        """
        Rerank top-N candidate chunks jointly with query.
        Returns top-K items sorted by cross-encoder relevance probability.
        """
        if not candidates:
            return []

        model = self._get_model()
        pairs = [[query, c["text"]] for c in candidates]

        with torch.inference_mode():
            if self.device == "cuda" and torch.cuda.is_available():
                with torch.autocast("cuda", dtype=torch.float16):
                    scores = model.predict(pairs, batch_size=batch_size, show_progress_bar=False)
            else:
                scores = model.predict(pairs, batch_size=batch_size, show_progress_bar=False)

        # Apply sigmoid if scores are raw logits
        scores_arr = torch.sigmoid(torch.tensor(scores)).numpy()

        scored_candidates = []
        for cand, score in zip(candidates, scores_arr):
            item = dict(cand)
            item["rerank_score"] = round(float(score), 4)
            scored_candidates.append(item)

        scored_candidates.sort(key=lambda x: x["rerank_score"], reverse=True)
        return scored_candidates[:top_k]
