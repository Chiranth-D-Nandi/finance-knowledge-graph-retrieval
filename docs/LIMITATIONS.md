# System Limitations, Technical Boundaries & Honest Disclosures
## Financial Knowledge Graph & Temporal Retrieval Platform

In accordance with institutional financial engineering and machine learning standards, this document explicitly articulates the technical limitations, scope boundaries, and known failure modes of the platform.

---

## 1. Asset Universe & Scope Constraints

- **Coverage:** The platform is configured for the **S&P 50 focus universe** of large-cap US equities (financials, technology, healthcare, energy, consumer).
- **Expansion Boundary:** Extending the system to the full Russell 3000 or global MSCI World universe requires sharded vector indices (e.g. distributed Qdrant or Milvus clusters) and multi-node ingestion workers.
- **Corporate Restructuring:** Mergers, spin-offs, and ticker changes occurring within the S&P 50 between 2020 and 2024 are resolved via canonical SEC CIK and Wikidata QIDs, but historical entity matching before 2020 is not covered.

---

## 2. Ingestion & SEC Rate Limiting

- **Regulatory Rate Limit:** SEC EDGAR strictly enforces a limit of 10 requests/second per IP address. The platform caps its internal client at 8 req/sec. Consequently, cold ingestion of 10 years of 10-K, 10-Q, and 8-K filings for 500 companies requires approximately 4.5 hours of throttled download time.
- **Reporting Deadlines:** SEC 10-K disclosures are filed up to 60-90 days after fiscal year-end; 10-Q disclosures are filed up to 40-45 days after quarter-end. Point-in-time queries must reflect the **acceptance date**, not the fiscal period end date.

---

## 3. Hardware Boundaries (RTX 4060 8GB VRAM)

- **Quantization Requirements:** Serving generative models locally on an 8GB VRAM budget necessitates 4-bit AWQ / GGUF quantization for 3B parameter models (e.g. Qwen2.5-3B-Instruct).
- **Model Size Scaling:** Deploying frontier 70B+ financial reasoning models locally is impossible on 8GB VRAM without offloading to CPU RAM (which causes prohibitive latency $>30\text{ s/token}$) or utilizing multi-GPU servers (e.g. $4\times$ NVIDIA A100 80GB).
- **Batch Size Saturation:** Dense embedding inference is bounded to batch sizes $\le 64$ to avoid CUDA out-of-memory exceptions during continuous streaming.

---

## 4. Synthetic Evaluation Fixtures

- **Data Quality Anomaly Fixtures:** Because official SEC Accounting and Auditing Enforcement Releases (AAERs) and severe restatements are sparse in large-cap equities, the data quality evaluation suite utilizes synthetic restatement breaks injected into real XBRL trajectories.
- **Audit Requirement:** All synthetic data are strictly flagged with `is_synthetic: true` in `eval/results.json` and are quarantined from the real-world retrieval and market impact analytics pipelines.

---

## 5. Econometric Modeling Limitations

- **Single-Index Market Model:** The event study module utilizes an OLS market model against `SPY`. While computationally fast and interpretable, it does not control for multi-factor risks (Fama-French size, value, momentum, or profitability factors).
- **Confounding Events:** Announcements occurring concurrently with SEC filings (e.g. earnings press releases, Federal Reserve rate decisions, geopolitical shocks) can bias Cumulative Abnormal Return (CAR) calculations if event windows are widened beyond $[-1, +2]$ days.
