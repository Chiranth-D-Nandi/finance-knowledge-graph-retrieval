"""Financial Sentiment Analysis using FinBERT (ProsusAI/finbert)."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
import numpy as np

from src.config import settings

logger = logging.getLogger("fin_nexus.sentiment")


class FinancialSentimentAnalyzer:
    """
    Financial sentiment analyzer with FinBERT (ProsusAI/finbert)
    and deterministic financial lexicon fallback.
    """

    def __init__(self, model_name: Optional[str] = None, device: Optional[str] = None):
        self.model_name = model_name or settings.SENTIMENT_MODEL
        self.device = device or settings.DEVICE
        self._pipe = None
        self._initialized = False

    def _lazy_init(self) -> None:
        if self._initialized:
            return
        try:
            from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline
            import torch

            logger.info("Loading FinBERT sentiment model '%s'...", self.model_name)
            tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            if self.device == "cuda" and torch.cuda.is_available():
                model = model.cuda()
            self._pipe = pipeline(
                "sentiment-analysis",
                model=model,
                tokenizer=tokenizer,
                device=0 if (self.device == "cuda" and torch.cuda.is_available()) else -1,
                top_k=None,
                truncation=True,
                max_length=512,
            )
            self._initialized = True
        except Exception as e:
            logger.warning("FinBERT neural model failed to initialize (%s). Using lexicon fallback.", e)
            self._initialized = True

    def predict(self, text: str) -> Dict[str, Any]:
        """Classify sentiment of a single text block."""
        self._lazy_init()
        if self._pipe is not None:
            try:
                outputs = self._pipe(text[:1000])[0]
                # outputs is list of {'label': 'positive'|'negative'|'neutral', 'score': float}
                score_map = {item["label"].lower(): float(item["score"]) for item in outputs}
                top_label = max(score_map, key=score_map.get)
                return {
                    "positive": round(score_map.get("positive", 0.0), 4),
                    "negative": round(score_map.get("negative", 0.0), 4),
                    "neutral": round(score_map.get("neutral", 0.0), 4),
                    "label": top_label,
                }
            except Exception as e:
                logger.debug("FinBERT inference error: %s", e)

        # Fast rule-based financial lexicon fallback
        return self._lexicon_predict(text)

    def predict_batch(self, texts: List[str], batch_size: int = 32) -> List[Dict[str, Any]]:
        """Batch inference for multiple chunks."""
        results = []
        for text in texts:
            results.append(self.predict(text))
        return results

    def _lexicon_predict(self, text: str) -> Dict[str, Any]:
        """Calibrated Loughran-McDonald inspired financial keyword sentiment fallback."""
        txt_lower = text.lower()
        neg_words = [
            "loss", "losses", "risk", "risks", "adverse", "adversely", "decline", "declined",
            "impairment", "litigation", "uncertainty", "volatility", "downturn", "restructuring",
            "default", "breach", "fail", "failed", "deficit", "liability", "headwind"
        ]
        pos_words = [
            "growth", "grow", "profit", "profitable", "revenue", "gain", "gains", "benefit",
            "exceeded", "strong", "outperform", "dividend", "upside", "expansion", "momentum",
            "favorable", "improvement", "improved", "record", "tailwind"
        ]

        neg_count = sum(1 for w in neg_words if f" {w} " in f" {txt_lower} ")
        pos_count = sum(1 for w in pos_words if f" {w} " in f" {txt_lower} ")

        total = neg_count + pos_count
        if total == 0:
            return {"positive": 0.10, "negative": 0.10, "neutral": 0.80, "label": "neutral"}

        p_pos = pos_count / (total + 2)
        p_neg = neg_count / (total + 2)
        p_neu = max(0.0, 1.0 - (p_pos + p_neg))

        label = "neutral"
        if p_pos > p_neg and p_pos > 0.4:
            label = "positive"
        elif p_neg > p_pos and p_neg > 0.4:
            label = "negative"

        return {
            "positive": round(p_pos, 4),
            "negative": round(p_neg, 4),
            "neutral": round(p_neu, 4),
            "label": label,
        }
