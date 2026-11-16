"""FinanceBench Benchmark Evaluator for Retrieval and Grounded QA."""

from __future__ import annotations

import logging
from typing import Any, Dict, List
import numpy as np

from eval.metrics import citation_coverage, exact_match, mrr, ndcg_at_k, recall_at_k, token_f1
from src.generation.qa_engine import QAEngine
from src.retrieval.engine import RetrievalEngine

logger = logging.getLogger("fin_nexus.financebench_eval")

FINANCEBENCH_QUESTIONS = [
    {
        "id": "FB_001",
        "question": "What was Apple's total Services revenue in fiscal 2023?",
        "ticker": "AAPL",
        "before": "2023-12-01",
        "ground_truth": "$85.2 billion",
        "expected_terms": ["services revenue", "85.2 billion", "all-time record"],
    },
    {
        "id": "FB_002",
        "question": "What was JPMorgan's managed net revenue for the year ended December 31, 2023?",
        "ticker": "JPM",
        "before": "2024-03-01",
        "ground_truth": "$162.4 billion",
        "expected_terms": ["managed basis", "162.4 billion", "23%"],
    },
    {
        "id": "FB_003",
        "question": "How much was JPMorgan's allowance for credit losses at the end of 2023?",
        "ticker": "JPM",
        "before": "2024-03-01",
        "ground_truth": "$14.3 billion",
        "expected_terms": ["allowance for credit losses", "14.3 billion", "credit card services"],
    },
    {
        "id": "FB_004",
        "question": "What drove NVIDIA's revenue growth in fiscal 2024?",
        "ticker": "NVDA",
        "before": "2024-03-01",
        "ground_truth": "Surged 126% to $60.9 billion driven by Hopper architecture GPU platforms like H100",
        "expected_terms": ["hopper", "h100", "compute & networking", "60.9 billion"],
    },
    {
        "id": "FB_005",
        "question": "What primary supply chain risks did Apple disclose in its fiscal 2023 10-K?",
        "ticker": "AAPL",
        "before": "2023-12-01",
        "ground_truth": "Outsourced manufacturing concentration in Asia including mainland China, India, and Vietnam",
        "expected_terms": ["outsourced partners", "asia", "china", "vietnam"],
    },
]


def evaluate_financebench(retrieval_engine: RetrievalEngine, qa_engine: QAEngine) -> Dict[str, Any]:
    """Evaluate retrieval and QA on FinanceBench subset."""
    retrieval_metrics = {
        "nDCG@10": 0.0,
        "Recall@10": 0.0,
        "MRR": 0.0,
    }
    qa_metrics = {
        "exact_match": 0.0,
        "token_f1": 0.0,
        "citation_coverage": 0.0,
    }

    n_q = len(FINANCEBENCH_QUESTIONS)

    for item in FINANCEBENCH_QUESTIONS:
        q = item["question"]
        t = item["ticker"]
        before = item["before"]
        gt = item["ground_truth"]
        terms = item["expected_terms"]

        # 1. Retrieval
        search_res = retrieval_engine.search(query=q, entity=t, before=before, limit=10)
        results = search_res.get("results", [])
        retrieved_ids = [c["chunk_id"] for c in results]

        # Determine relevant chunks
        relevant_ids = set()
        for c in retrieval_engine.chunks:
            if c.get("ticker") == t and any(term in c["text"].lower() for term in terms):
                relevant_ids.add(c["chunk_id"])

        retrieval_metrics["Recall@10"] += recall_at_k(retrieved_ids, relevant_ids, k=10)
        retrieval_metrics["nDCG@10"] += ndcg_at_k(retrieved_ids, relevant_ids, k=10)
        retrieval_metrics["MRR"] += mrr(retrieved_ids, relevant_ids)

        # 2. Grounded QA
        qa_res = qa_engine.generate_answer(
            question=q,
            retrieved_chunks=results,
            entity_filter=t,
            before_date=before,
        )
        pred_text = qa_res.answer_text

        qa_metrics["exact_match"] += exact_match(pred_text, gt)
        qa_metrics["token_f1"] += token_f1(pred_text, gt)
        qa_metrics["citation_coverage"] += citation_coverage(pred_text, qa_res.citations)

    # Average metrics
    for k in retrieval_metrics:
        retrieval_metrics[k] = round(retrieval_metrics[k] / n_q, 4)
    for k in qa_metrics:
        qa_metrics[k] = round(qa_metrics[k] / n_q, 4)

    return {
        "questions_count": n_q,
        "retrieval": retrieval_metrics,
        "qa": qa_metrics,
    }
