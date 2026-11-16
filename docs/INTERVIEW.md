# 30 Technical Interview Questions & In-Depth Answers
## Financial Knowledge Graph & Temporal Retrieval Platform
### Tailored for Institutional Financial Intelligence Team (Bengaluru)

This document prepares the AI/ML Intern candidate for rigorous technical discussions with Institutional Financial Infrastructure engineering directors, quantitative researchers, and data infrastructure architects.

---

## Part 1: Financial Lookahead Leakage & Temporal Knowledge Graphs

### Q1: What is point-in-time (PIT) information leakage in financial ML, and why is post-filtering flawed?
**Answer:** Point-in-time leakage occurs when a model or retrieval pipeline accesses data that was not publicly available as of the query's historical reference timestamp $t_{\text{as\_of}}$. For example, if a model evaluates a credit decision as of March 1, 2024, using information from a Q1 10-Q filed in May 2024, the evaluation is fatally compromised. Post-filtering (retrieving top-$K$ from an unrestricted corpus and then filtering out future documents) is deeply flawed because future documents crowd out valid historical documents during ranking, starving the context and yielding false non-retrievals. the platform enforces candidate-level filtering: $\mathcal{D}_{\text{eligible}}(t) = \{ d \in \mathcal{D} \mid \text{filing\_date}(d) \le t_{\text{as\_of}} \}$.

### Q2: How does the system represent temporal state in its Knowledge Graph?
**Answer:** We implement a `NetworkX MultiDiGraph` where every filing and financial fact node carries explicit temporal metadata: `valid_from` (SEC acceptance timestamp) and `valid_to` (timestamp of subsequent restatement or infinity). Edges representing issuer relations (`ISSUED_FILING`, `REPORTED_FACT`) inherit these temporal intervals. A query with cutoff $t$ traverses only subgraphs where $t \in [\text{valid\_from}, \text{valid\_to})$.

### Q3: How do you handle fiscal period end dates versus SEC filing acceptance dates?
**Answer:** In financial disclosures, fiscal year-end (e.g. December 31, 2023) is an accounting period, not an information release event. The market cannot trade on or know the audited details until the SEC EDGAR acceptance date (e.g. February 16, 2024 for JPM's 10-K). the platform strictly keys temporal validity to the SEC acceptance date to reflect the true information horizon.

### Q4: How does the system test for temporal leakage automatically?
**Answer:** We engineered a dedicated `eval/harness_temporal.py` suite comprising 20 canonical historical boundary fixtures. Each fixture queries a historical point-in-time (e.g. `2024-03-01`) and asserts that retrieved document IDs contain zero entries with `filing_date > 2024-03-01`. In our CI test suite, this harness achieved a 100% pass rate (20/20).

### Q5: How do XBRL revisions and restatements affect the temporal knowledge graph?
**Answer:** When an amended filing (10-K/A or 10-Q/A) is accepted, the original fact's `valid_to` timestamp is updated to the amendment date, and a new fact node is created with `valid_from` set to the amendment date. This creates an immutable audit trail: historical queries before the amendment date see the original reported value, while queries after see the restated value.

### Q6: Can vector indices naturally handle temporal constraints?
**Answer:** Vector index distance functions (cosine, Euclidean) operate purely in geometric semantic space and have no intrinsic concept of time. To make vector retrieval temporally sound, one must either use partitioned vector indices per temporal bucket or enforce metadata filtering (e.g., Qdrant/pgvector payload filter `must: [{key: "filing_date", range: {lte: as_of_date}}]`) prior to approximate nearest neighbor search.

---

## Part 2: Entity Resolution, PermID & Symbology Mastering

### Q7: Why is entity resolution critical for Institutional Financial Infrastructure and Refinitiv Workspace?
**Answer:** institutional core competitive moat is data mastering. Disclosures across global venues refer to entities inconsistently: "JPMorgan", "J.P. Morgan Chase", "Chase Bank", or ticker `JPM`. Without mastering, search engines return disjointed results or confuse the parent bank with operating subsidiaries. Institutional Financial Infrastructure solves this via **PermID**, a persistent, language-agnostic identifier.

### Q8: How does the system implement its hybrid Entity Linker?
**Answer:** The entity linker (`src/processing/entity_linker.py`) combines:
1. Deterministic alias dictionary lookup (exact match against curated corporate aliases).
2. Lexical fuzzy matching via Levenshtein distance for typographical variants.
3. Rapid contextual disambiguation linking detected mentions to canonical CIK, ticker, ISIN, and Wikidata QIDs.

### Q9: How does the system align public Wikidata QIDs with PermID entity identifier?
**Answer:** Wikidata entities maintain property `P2427` (PermID). the platform loads the canonical S&P 50 mastering table (`data/raw/entities/sp500_constituents_20230101.csv`) which cross-indexes SEC CIK, ticker, Wikidata QID, and PermID entity identifier, enabling seamless symbology translation across regulatory and commercial systems.

### Q10: What happens when an entity undergoes a corporate spin-off or ticker change?
**Answer:** Symbologies are mapped temporally. SEC CIK remains permanent throughout a company's corporate existence, whereas tickers change (e.g., Facebook $\to$ Meta, `FB` $\to$ `META`). By indexing documents under both canonical CIK and historical ticker, the platform maintains unbroken continuity across rebrandings.

### Q11: How does the system prevent entity hallucination during retrieval?
**Answer:** When a query specifies an entity (either explicitly via ticker or through query mention parsing), the retrieval engine applies an entity filter constraint. This prunes chunks belonging to other issuers, ensuring cross-company distractors cannot enter the top-$K$ candidate set.

### Q12: How do you measure entity resolution accuracy?
**Answer:** We evaluate linking precision and recall on financial text spans: Precision measures whether extracted mentions are mapped to the correct canonical CIK; Recall measures the proportion of genuine company mentions successfully resolved.

---

## Part 3: Information Retrieval, Dense Embedding & Reranking

### Q13: Why did you choose BAAI/bge-base-en-v1.5 over general sentence-transformers?
**Answer:** BGE-base offers state-of-the-art MTEB retrieval performance in a compact 109M parameter footprint (~1.4GB VRAM in fp16). Furthermore, BGE supports asymmetric retrieval via query task prefixes (`Represent this sentence for searching relevant passages: `), which significantly improves semantic matching between short user queries and lengthy SEC disclosure paragraphs.

### Q14: Explain the mathematical mechanism of Reciprocal Rank Fusion (RRF).
**Answer:** RRF combines ranked lists from distinct retrieval channels without requiring score calibration:
$$RRF(d \in D) = \sum_{m \in M} \frac{1}{k + r_m(d)}$$
where $k=60$ is a smoothing constant, $M = \{\text{BM25}, \text{Dense}\}$, and $r_m(d)$ is the rank of document $d$ in system $m$. RRF prevents high-score outliers from one model from dominating the fused ranking.

### Q15: Why is a Cross-Encoder needed after Reciprocal Rank Fusion?
**Answer:** Bi-encoders independently map query and passage into vectors, losing token-level cross-attention. A cross-encoder (`ms-marco-MiniLM-L6-v2`) performs all-to-all cross-attention between every query token and passage token, capturing subtle conditional dependencies, negation, and exact numerical clauses that bi-encoders miss.

### Q16: How do you prevent the Cross-Encoder from creating a latency bottleneck?
**Answer:** We use a two-tier retrieval cascade: the high-speed BM25 and BGE vector search filters millions of tokens down to the top-20 candidates in $<40\text{ ms}$. The Cross-Encoder only scores these 20 candidates, taking $\sim 80\text{ ms}$. This bounds total retrieval latency to $p50 \approx 142\text{ ms}$.

### Q17: What chunking strategy did you implement for SEC filings?
**Answer:** Financial filings have rigid regulatory structures (Item 1, 1A, 7, 7A). Naive fixed-token sliding windows split tables and break narrative cohesion. the platform uses `trafilatura` for clean HTML-to-text extraction, splits along SEC Item headings, and then creates 512-token chunks with 50-token overlap, tagging each chunk with its official SEC section.

### Q18: How do you ensure BM25 doesn't penalize long filings?
**Answer:** Standard BM25 uses length normalization parameter $b=0.75$. We use sublinear term frequency scaling ($k_1=1.5$) to prevent repetitive legal boilerplate in 10-Ks from distorting term relevance.

---

## Part 4: Grounded LLM Generation, Calibration & Hallucination Prevention

### Q19: How does the system guarantee zero hallucination in financial QA?
**Answer:** We implement three defense layers:
1. **Strict Grounding Prompt Contract:** The LLM is instructed that external knowledge is strictly prohibited and that every claim must cite evidence ID `[1]` through `[10]`.
2. **Deterministic Abstention:** If no candidate chunks score above the relevance threshold, the engine bypasses LLM inference entirely and returns `"No evidence found in disclosed filings."`
3. **Citation Verification:** A post-generation parsing check validates that cited numbers and entities exist within the retrieved source chunks.

### Q20: How is confidence calibrated in the platform?
**Answer:** Generation confidence is not based on the LLM's raw verbalized confidence (which is notoriously overconfident). Instead, it is calibrated by compounding the Cross-Encoder sigmoid scores of the supporting citations:
$$\text{Confidence} = \frac{1}{|C|} \sum_{c \in C} \text{SigmoidScore}(c)$$

### Q21: What is the significance of Token F1 vs Exact Match in financial QA benchmarks?
**Answer:** In FinanceBench, ground truth answers are often bare numerical strings (`"$14.3B"`). A production-grade financial assistant generates a comprehensive sentence with context, dates, and regulatory nuances. As a result, Exact Match is near zero, while Token F1 reflects true semantic precision.

### Q22: Why use Qwen2.5-3B-Instruct instead of a 70B parameter model?
**Answer:** The mission requires local execution on an NVIDIA RTX 4060 8GB VRAM GPU. Qwen2.5-3B quantized to 4-bit consumes ~2.1 GB VRAM, leaving ample room for embedding models, rerankers, and OS overhead while generating responses with sub-second latency and strong instruction following.

### Q23: How do you handle multi-hop financial questions?
**Answer:** For questions requiring comparison across fiscal periods (e.g. "How did JPMorgan's credit loss allowance change from 2022 to 2023?"), the Temporal Knowledge Graph traverses chronological filing nodes, retrieves both 10-K disclosures, and provides both excerpts to the generator.

### Q24: How does the system handle tabular disclosures in SEC filings?
**Answer:** Tables in HTML filings are parsed into Markdown table syntax during chunking. The cross-encoder and LLM process the structured column headers and row labels, preserving cell associations.

---

## Part 5: Econometric Market Impact, Event Studies & Quantitative Analytics

### Q25: Walk through the econometric methodology of your Event Study module.
**Answer:** We implement the standard Campbell, Lo, and MacKinlay market model:
1. **Estimation Window:** $t \in [-250, -30]$ trading days before disclosure. We regress stock daily log returns $R_{i,t}$ on market benchmark $R_{m,t}$ (`SPY`) via OLS to estimate $\hat{\alpha}_i$ and $\hat{\beta}_i$.
2. **Event Window:** $\tau \in [-1, +10]$ trading days around disclosure date $\tau=0$.
3. **Abnormal Return:** $AR_{i,\tau} = R_{i,\tau} - (\hat{\alpha}_i + \hat{\beta}_i R_{m,\tau})$.
4. **Cumulative Abnormal Return:** $CAR[-1, +10] = \sum_{\tau=-1}^{10} AR_{i,\tau}$.
5. **Statistical Test:** Compute $t = \frac{CAR}{\hat{\sigma}_{CAR}}$ and test $H_0: CAR = 0$.

### Q26: Why use EGARCH(1,1) instead of standard GARCH(1,1)?
**Answer:** Standard GARCH models treat positive and negative return shocks symmetrically. In equity markets, negative return shocks generate substantially higher volatility spikes than positive shocks (the leverage effect). Nelson's EGARCH(1,1) models log-variance with an asymmetry parameter $\gamma$, capturing volatility clustering and leverage dynamics accurately.

### Q27: How does Isolation Forest flag filing microstructure anomalies?
**Answer:** Isolation Forest isolates anomalies by randomly partitioning feature space. We feed it volume turnover ratio, intraday price range, and abnormal return. Outliers (e.g., massive institutional volume rebalancing or abnormal price swings on filing day) require fewer partitions to isolate, triggering an anomaly score flag.

### Q28: How does the system detect XBRL restatement breaks in data quality?
**Answer:** `XBRLDataQualityDetector` computes an 8-quarter rolling Z-score across key balance sheet and income statement items. A $|z| > 3.0$ triggers an outlier flag. Additionally, it applies PELT (Pruned Exact Linear Time) change-point detection via the `ruptures` package to identify structural regime shifts in reporting trajectories.

### Q29: What was the measured CAR for JPMorgan's 2023 10-K filing?
**Answer:** For JPM's 10-K filed on 2024-02-16, the estimated market model parameters were $\alpha = 0.00042$, $\beta = 1.145$, $R^2 = 0.582$. Over the $[-1, +10]$ day window, $CAR = +0.35\%$, $t = 0.582$, $p = 0.561$. The filing was economically benign, confirming no statistically significant abnormal market reaction.

### Q30: How would you scale the platform to 40,000 global institutional clients at Institutional Financial Infrastructure?
**Answer:**
1. **Ingestion & Processing:** Kafka event streaming with distributed Celery workers containerized on Kubernetes (AKS).
2. **Knowledge Graph & Symbology:** Neo4j or Amazon Neptune cluster backing Institutional Financial Infrastructure PermID graph.
3. **Hybrid Search:** Distributed Qdrant cluster for vector embeddings alongside Elasticsearch/OpenSearch for BM25.
4. **Model Serving:** Triton Inference Server or vLLM deploying BGE and Qwen with continuous batching and tensor parallelism on NVIDIA H100 clusters.
