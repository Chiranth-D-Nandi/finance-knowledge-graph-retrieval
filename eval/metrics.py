"""Evaluation metrics for financial retrieval, grounded QA, and entity resolution."""

from __future__ import annotations

import math
import re
from typing import Any, Dict, List, Set


def recall_at_k(retrieved_ids: List[str], relevant_ids: Set[str], k: int = 10) -> float:
    """Recall@K: 1.0 if at least one relevant document is in top-K, else 0.0."""
    if not relevant_ids:
        return 0.0
    top_k = retrieved_ids[:k]
    hits = sum(1 for doc_id in top_k if doc_id in relevant_ids)
    return 1.0 if hits > 0 else 0.0


def ndcg_at_k(retrieved_ids: List[str], relevant_ids: Set[str], k: int = 10) -> float:
    """Normalized Discounted Cumulative Gain at rank K with binary relevance."""
    if not relevant_ids:
        return 0.0
    dcg = 0.0
    for rank, doc_id in enumerate(retrieved_ids[:k], start=1):
        if doc_id in relevant_ids:
            dcg += 1.0 / math.log2(rank + 1)

    # Ideal DCG for all relevant documents up to k
    n_rel = min(len(relevant_ids), k)
    idcg = sum(1.0 / math.log2(r + 1) for r in range(1, n_rel + 1))
    return round(min(1.0, dcg / idcg), 4) if idcg > 0 else 0.0


def mrr(retrieved_ids: List[str], relevant_ids: Set[str]) -> float:
    """Mean Reciprocal Rank of first relevant document."""
    for rank, doc_id in enumerate(retrieved_ids, start=1):
        if doc_id in relevant_ids:
            return 1.0 / rank
    return 0.0


def normalize_answer(text: str) -> str:
    """Lower text and strip punctuation, articles and extra whitespace."""
    text = text.lower()
    text = re.sub(r"\b(a|an|the)\b", " ", text)
    text = re.sub(r"[^\w\s]", " ", text)
    return " ".join(text.split())


def exact_match(prediction: str, ground_truth: str) -> float:
    """Normalized exact match metric."""
    return 1.0 if normalize_answer(prediction) == normalize_answer(ground_truth) else 0.0


def token_f1(prediction: str, ground_truth: str) -> float:
    """Token-level F1 overlap score."""
    pred_tokens = normalize_answer(prediction).split()
    gt_tokens = normalize_answer(ground_truth).split()

    if not pred_tokens or not gt_tokens:
        return 1.0 if pred_tokens == gt_tokens else 0.0

    common = set(pred_tokens) & set(gt_tokens)
    if not common:
        return 0.0

    precision = len(common) / len(pred_tokens)
    recall = len(common) / len(gt_tokens)
    return 2 * (precision * recall) / (precision + recall)


def citation_coverage(answer_text: str, citations: List[Any]) -> float:
    """
    Percentage of sentences in answer that include a valid citation reference.
    e.g. '[1]', '[2]'.
    """
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", answer_text) if s.strip()]
    if not sentences:
        return 1.0

    cited_sentences = 0
    for s in sentences:
        if re.search(r"\[\d+\]", s):
            cited_sentences += 1

    return round(cited_sentences / len(sentences), 4)


def abstention_accuracy(predictions: List[Dict[str, Any]]) -> float:
    """
    Evaluates whether the system appropriately abstains ('no_evidence': True)
    when presented with out-of-corpus or unanswerable queries.
    """
    if not predictions:
        return 1.0
    correct = 0
    for p in predictions:
        is_negative = p.get("is_negative", False)
        abstained = p.get("no_evidence", False) or "no evidence found" in p.get("answer_text", "").lower()
        if is_negative and abstained:
            correct += 1
        elif not is_negative and not abstained:
            correct += 1
    return round(correct / len(predictions), 4)
