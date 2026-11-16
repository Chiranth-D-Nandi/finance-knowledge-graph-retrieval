"""Custom Point-in-Time (PIT) Benchmark Generator and Evaluator."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd

from eval.metrics import abstention_accuracy, citation_coverage, exact_match, mrr, ndcg_at_k, recall_at_k, token_f1
from src.config import settings
from src.generation.qa_engine import QAEngine
from src.retrieval.engine import RetrievalEngine

logger = logging.getLogger("fin_nexus.custom_pit_eval")


def build_custom_pit_qa_file(output_path: Optional[Path] = None, force_rebuild: bool = False) -> List[Dict[str, Any]]:
    """
    Generate 200 diverse point-in-time financial queries with temporal timestamps
    and negative questions (temporal lookahead leaks + unanswerables) for abstention testing.
    """
    path = output_path or (settings.BENCHMARKS_DIR / "custom_temporal_qa.jsonl")
    if path.exists() and not force_rebuild:
        records = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
        if len(records) >= 100:
            return records

    records: List[Dict[str, Any]] = []

    # Financial topics and companies for realistic query diversity
    company_profiles = [
        ("JPM", "JPMorgan Chase & Co.", "2024-02-16", [
            ("allowance for credit losses and consumer loan provisions", "$14.3 billion"),
            ("total net revenue and net interest income performance", "$162.4 billion managed revenue"),
            ("commercial real estate office exposure and reserve coverage", "credit loss reserves"),
            ("First Republic Bank acquisition integration and deposit growth", "acquisition accounting"),
            ("CET1 capital ratio and regulatory compliance", "15.0% CET1 ratio"),
            ("wholesale credit card net charge-off expectations", "consumer charge-offs"),
            ("investment banking fee momentum and advisory fees", "fee revenue"),
            ("macro interest rate sensitivity and deposit migration", "NII sensitivity"),
        ]),
        ("AAPL", "Apple Inc.", "2023-11-03", [
            ("Services segment revenue and paid subscriptions count", "$85.2 billion"),
            ("iPhone net sales and average selling price dynamics", "iPhone revenue"),
            ("gross margin progression across hardware and digital services", "44.1% gross margin"),
            ("research and development expenditure in artificial intelligence", "R&D spending"),
            ("greater China revenue performance and supply chain resiliency", "China segment sales"),
            ("share repurchase program and cash return to shareholders", "$77.5 billion buybacks"),
            ("wearables home and accessories revenue trends", "wearables segment"),
            ("operating cash flow generation and net cash neutrality", "operating cash flow"),
        ]),
        ("MSFT", "Microsoft Corporation", "2023-07-27", [
            ("Microsoft Cloud gross revenue and annualized run rate", "$110 billion"),
            ("Azure intelligent cloud revenue growth and AI infrastructure", "Azure growth"),
            ("Productivity and Business Processes segment operating income", "Office 365 commercial"),
            ("Activision Blizzard acquisition regulatory review and closing", "gaming revenue"),
            ("capital expenditure for AI data centers and GPUs", "capex investments"),
            ("commercial remaining performance obligation (RPO) balance", "commercial RPO"),
            ("LinkedIn talent solutions and premium subscriptions", "LinkedIn revenue"),
            ("effective income tax rate and foreign subsidiary earnings", "effective tax rate"),
        ]),
        ("BAC", "Bank of America Corporation", "2024-02-20", [
            ("Global Wealth and Investment Management net income", "wealth management"),
            ("held-to-maturity securities unrealized losses and capital", "HTM bond portfolio"),
            ("Global Markets sales and trading revenue performance", "FICC trading"),
            ("provision for credit losses and reserve build", "credit provisions"),
            ("net interest yield sensitivity to Fed rate cuts", "yield sensitivity"),
            ("consumer banking average deposit balances", "consumer deposits"),
            ("efficiency ratio and noninterest expense discipline", "expense discipline"),
            ("tier 1 risk-based capital and liquidity ratios", "Tier 1 capital"),
        ]),
        ("GS", "The Goldman Sachs Group, Inc.", "2024-02-22", [
            ("Global Banking & Markets net revenues and backlog", "investment banking"),
            ("Asset & Wealth Management management fees and AUS", "assets under supervision"),
            ("consumer platform divestitures and Marcus wind-down", "consumer lending exit"),
            ("FICC net revenues and equity financing growth", "FICC financing"),
            ("provision for credit losses and loan charge-offs", "credit provisions"),
            ("Standardized CET1 ratio and share repurchase capacity", "CET1 ratio"),
            ("operating expenses and compensation ratio target", "compensation ratio"),
            ("alternative investment harvesting and balance sheet commitments", "principal investments"),
        ]),
    ]

    qid = 1
    # 1. 160 Answerable point-in-time queries with diverse phrasing
    templates = [
        "What did {name} ({ticker}) report regarding {topic} in its filing dated {filing_date}?",
        "Summarize disclosures from {ticker} on {topic} as filed with the SEC on {filing_date}.",
        "According to {name}'s {filing_date} SEC filing, what are the details on {topic}?",
        "What financial figures or discussion did {ticker} provide concerning {topic} as of {query_ts}?",
    ]

    for ticker, name, filing_date, topics in company_profiles:
        f_dt = pd.to_datetime(filing_date)
        valid_query_ts = (f_dt + pd.Timedelta(days=14)).strftime("%Y-%m-%d")
        for topic, ans in topics:
            for tmpl_idx, tmpl in enumerate(templates):
                q_text = tmpl.format(
                    name=name,
                    ticker=ticker,
                    topic=topic,
                    filing_date=filing_date,
                    query_ts=valid_query_ts,
                )
                records.append({
                    "qid": f"PIT_{qid:04d}",
                    "question": q_text,
                    "ticker": ticker,
                    "filing_date": filing_date,
                    "query_timestamp": valid_query_ts,
                    "ground_truth": ans,
                    "is_negative": False,
                })
                qid += 1

    # 2. 40 Negative queries:
    # 2a. 20 Lookahead leakage queries (asked BEFORE filing date -> Must abstain)
    for ticker, name, filing_date, topics in company_profiles:
        f_dt = pd.to_datetime(filing_date)
        leakage_query_ts = (f_dt - pd.Timedelta(days=60)).strftime("%Y-%m-%d")
        for topic, _ in topics[:4]:
            records.append({
                "qid": f"PIT_{qid:04d}",
                "question": f"As of {leakage_query_ts}, what did {ticker} report for fiscal results in its future {filing_date} 10-K regarding {topic}?",
                "ticker": ticker,
                "filing_date": filing_date,
                "query_timestamp": leakage_query_ts,
                "ground_truth": "No evidence found in retrieved sources for this question given the time filter.",
                "is_negative": True,
            })
            qid += 1

    # 2b. 20 Out-of-domain / unanswerable queries (hallucination defense)
    unanswerable_topics = [
        ("JPM", "cryptocurrency mining rig sales and Bitcoin treasury holding"),
        ("AAPL", "deep sea oil exploration concession agreements in the Gulf of Mexico"),
        ("MSFT", "commercial supersonic passenger airline ticket bookings"),
        ("BAC", "uranium enrichment centrifuges operational capacity"),
        ("GS", "commercial space station asteroid mineral refinement royalties"),
    ]
    for ticker, u_topic in unanswerable_topics:
        for v in range(4):
            records.append({
                "qid": f"PIT_{qid:04d}",
                "question": f"What revenue did {ticker} report from {u_topic} in its regulatory disclosures?",
                "ticker": ticker,
                "filing_date": "2024-02-16",
                "query_timestamp": "2024-03-01",
                "ground_truth": "No evidence found in retrieved sources for this question given the time filter.",
                "is_negative": True,
            })
            qid += 1

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    logger.info("Generated %d custom PIT QA benchmark records at %s", len(records), path)
    return records


def evaluate_custom_pit_benchmark(retrieval_engine: RetrievalEngine, qa_engine: QAEngine) -> Dict[str, Any]:
    """Execute evaluation on the 200 custom point-in-time queries."""
    dataset = build_custom_pit_qa_file(force_rebuild=True)

    retrieval_scores = {"nDCG@10": 0.0, "Recall@10": 0.0, "MRR": 0.0}
    qa_scores = {"exact_match": 0.0, "token_f1": 0.0, "citation_coverage": 0.0}
    qa_predictions = []

    pos_count = 0

    for item in dataset:
        q = item["question"]
        t = item["ticker"]
        ts = item["query_timestamp"]
        gt = item["ground_truth"]
        is_neg = item["is_negative"]

        search_res = retrieval_engine.search(query=q, entity=t, before=ts, limit=10)
        results = search_res.get("results", [])
        retrieved_ids = [c["chunk_id"] for c in results]

        if not is_neg:
            pos_count += 1
            # Ground truth relevant chunks under PIT boundary
            relevant_ids = {c["chunk_id"] for c in retrieval_engine.chunks if c.get("ticker") == t and c.get("filing_date") <= ts}
            if relevant_ids:
                retrieval_scores["Recall@10"] += recall_at_k(retrieved_ids, relevant_ids, k=10)
                retrieval_scores["nDCG@10"] += ndcg_at_k(retrieved_ids, relevant_ids, k=10)
                retrieval_scores["MRR"] += mrr(retrieved_ids, relevant_ids)

        qa_res = qa_engine.generate_answer(question=q, retrieved_chunks=results, entity_filter=t, before_date=ts)
        pred_text = qa_res.answer_text

        qa_predictions.append({
            "qid": item["qid"],
            "answer_text": pred_text,
            "no_evidence": qa_res.no_evidence,
            "is_negative": is_neg,
        })

        if not is_neg:
            qa_scores["exact_match"] += exact_match(pred_text, gt)
            qa_scores["token_f1"] += token_f1(pred_text, gt)
            qa_scores["citation_coverage"] += citation_coverage(pred_text, qa_res.citations)

    # Normalize metrics
    if pos_count > 0:
        for k in retrieval_scores:
            retrieval_scores[k] = round(retrieval_scores[k] / pos_count, 4)
        for k in qa_scores:
            qa_scores[k] = round(qa_scores[k] / pos_count, 4)

    abstention_rate = abstention_accuracy(qa_predictions)

    return {
        "total_queries": len(dataset),
        "positive_queries": pos_count,
        "negative_queries": len(dataset) - pos_count,
        "retrieval": retrieval_scores,
        "qa": qa_scores,
        "abstention_accuracy": abstention_rate,
    }
