# Winning Project Deep Dive ,  Financial Knowledge Graph & Temporal Retrieval Platform

**Winner:** C21 ,  **Financial Knowledge Graph & Temporal Retrieval Platform** (Entity-Resolved Temporal Knowledge Graph with Hybrid Financial Retrieval, Grounded QA, and Explainable Market Impact Analytics)  
**Core System:** Financial Knowledge Graph & Temporal Retrieval Platform  
**Tagline:** *"What Bloomberg and Institutional Financial Infrastructure built behind closed doors ,  rebuilt open, reproducible, and interview-defensible."*  
**One-liner for resume:** Entity-resolved temporal Knowledge Graph + Hybrid Retrieval (BM25 + Dense + Cross-Encoder) over SEC filings & news-proxies → Grounded QA with provenance + Market-impact analytics, evaluated on FinanceBench + custom point-in-time benchmark.

**Rank:** 94/100 (C21) ,  unanimous winner  
**Feasibility gate:** Passed ,  one developer, RTX 4060 8GB, public data, 8-week build with milestone cut lines

---

## 1. Problem Definition ,  Exact

### 1.1 Problem Statement (Single paragraph, interview-ready)

> Financial professionals waste 30-40% of research time reconciling fragmented disclosures: earnings filings (10-K/Q), material events (8-K), press releases, and news ,  each mentioning companies by inconsistent aliases ("Apple," "AAPL," "Apple Inc., Cupertino"), published on different cadences, with no unified entity timeline or evidence-linked QA. Institutional Financial Infrastructure solves this with proprietary entity mastering (PermID), tagging/symbology, and Knowledge-Graph-backed retrieval in Workspace. No public system replicates this pipeline end-to-end with measurable retrieval quality, temporal correctness, and grounded generation. The platform builds it: a reproducible platform over public SEC EDGAR + price/macro data that (a) resolves every mention to a canonical ticker/CIK, (b) builds a temporal Knowledge Graph (entity ↔ event ↔ filing ↔ market context), (c) serves hybrid retrieval (BM25 + dense + cross-encoder reranking) with point-in-time guarantees, (d) generates grounded answers with citations + uncertainty, and (e) quantifies market impact of events ,  all evaluated (nDCG, Recall@K, EM/F1, PR-AUC, latency) and monitored.

### 1.2 Why the problem exists

- **Entity fragmentation:** Same issuer appears as "JPMorgan Chase & Co.," "JPM," "JPMorgan," CIK 19617, ticker JPM. Naive chunking → retrieval returns irrelevant docs; QA hallucinates across entities.
- **Temporal fragmentation:** Filings arrive quarterly; news intraday; prices tick. Query at T must not see T+future documents. Public benchmarks ignore this; production systems fail silently without it.
- **Evidence gap:** LLM QA without provenance → hallucinations on numerically precise claims ("What was FY2024 revenue?"). institutional governance (OpenAI case: human-in-loop) requires provenance ,  no student RAG provides it.
- **Impact opacity:** Event → market impact is assumed but never quantified. Analysts need "this 8-K was associated with +2.1% abnormal return vs peers, with volatility doubling for 3 days" ,  not vibes.
- **Data quality debt:** SEC XBRL facts contain restatements; price feeds have missing/delisted gaps; entity registries drift (ticker changes from rebrands). No pipeline validates.

### 1.3 Who experiences it & why it matters

| User | Workflow Pain | Platform Action |
|------|---------------|------------------|
| Equity research analyst (Workspace persona) | Reconstruct "risk timeline for AAPL 2023-25": find every 10-K risk disclosure, earnings surprise, regulatory event, and its price aftermath | Entity-filtered hybrid search + KG timeline + impact chart, with filing citations |
| Risk officer (Risk Intelligence persona) | Trace "exposure to entities mentioning supply-chain sanctions in filings" | Entity-resolved adverse-media proxy search over risk-factor sections |
| Index product team (FTSE Russell) | Validate if a constituent's restatement affects index composition data | Data-quality anomaly flag over XBRL time-series |
| Compliance/PM (Innovation & Intelligence stakeholder) | Verify LLM-generated investment thesis against filings | Grounded QA: answer + cited filing excerpt + confidence + "no evidence found" fallback |

**Why Institutional Financial Infrastructure cares:** This is Workspace's core job ,  and MCP's agent retrieval ,  reduced to a reproducible prototype. It mirrors institutional marketed capabilities (entity-resolved KG, adverse-media screening, Trade Surveillance anomaly) with public data.

### 1.4 Why conventional approaches fail

- **Pure dense retrieval:** Embeddings smear ticker ISINs/symbols ("BRK.A" vs "BRK.B" collapse). Finance queries are 20-40% identifier-heavy → BM25 required.
- **Single-source QA (filings only):** Misses event context (news) and market reaction (price/macro). Briefs assembled from filings alone are incomplete.
- **No entity layer:** Search "Apple risks" returns "Apple supplier TSMC" docs with equal rank → false positives flood results.
- **Chatbot RAG wrappers:** No fusion, no reranking, no temporal filter, no provenance ,  cannot pass nDCG or FinanceBench evaluation; cannot defend in review.
- **Pure time-series forecasting:** Predicts price but cannot explain *why*; not actionable for compliance/risk workflows.

### 1.5 Why our approach is appropriate

- **Hybrid retrieval is SOTA for production RAG** (RRF + cross-encoder gives +10-15% nDCG over bi-encoder alone ,  consistent across FiQA-BEIR literature). Matches Bloomberg/Institutional Financial Infrastructure production pattern.
- **Entity-first filtering is institutional "mastering & alignment" principle** ,  proven to reduce false positives by >30% in adverse-media screening (World-Check narrative).
- **Temporal KG + PIT retrieval is necessary for financial temporal correctness** ,  novel in open source but standard in regulated finance (point-in-time databases). Demonstrates understanding of leakage.
- **Grounded generation with citations + calibrated confidence** mirrors institutional OpenAI governance (human-in-loop, provenance).
- **Event-conditioned anomaly detection** bridges document intelligence → market analytics, completing the product loop and hitting anomaly-detection JD signal.

---

## 2. System Architecture ,  Full Stack

### 2.1 Architecture Diagram (Text-mermaid + description)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  DATA SOURCES (Public)                                                       │
│  SEC EDGAR (10-K/Q/8-K + XBRL) │ yfinance OHLCV │ FRED Macro │ Wikidata/SEC registry │ FNSPID/news-proxy │
└──────┬──────────────┬──────────────┬────────────────┬───────────────────────────────┘
       │              │              │                │
       ▼              ▼              ▼                ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  INGESTION & VALIDATION LAYER (Airflow-lite: scheduled Python + Pandera)     │
│  SEC fetcher (10 req/s, UA header) │ yfinance OHLCV loader │ FRED API │      │
│  → Schema validation: OHLCV invariants, filing non-empty, CIK format         │
│  → Provenance: {source_url, retrieved_at, filing_date, cik, ticker, sha256}  │
│  → Deduplication: sha256 + filing accession deduplication                    │
│  Storage: data/raw/edgar/{cik}/{form}/{date}.html (+ parquet for OHLCV)    │
└──────────────────────────────────────────────────────────────────────────────┘
       │ chunk + enrich
       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  PROCESSING & ENRICHMENT                                                     │
│  ┌─────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────────────────┐  │
│  │ HTML→MD     │ │ Entity NER + │ │ XBRL Parser  │ │ Sentiment (FinBERT)│  │
│  │ (trafilatura│ │ Linking      │ │ → financial  │ │ per chunk (pos/neg)│  │
│  │  + chunk)   │ │ (ticker/QID) │ │ facts table  │ └────────────────────┘  │
│  │ 512 tok,    │ │ FiNER-ORD +  │ │ Rev/Assets   │                         │
│  │ 50 overlap  │ │ rule+embed   │ └──────┬───────┘                         │
│  └──────┬──────┘ └──────┬───────┘ └──────┬───────┘                         │
└─────────┼───────────────┼────────────────┼───────────────────────────────────┘
          │               │                │
          ▼               ▼                ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  STORAGE & INDEX (Postgres + pgvector OR SQLite + Qdrant/Chroma lite)       │
│  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────────────────┐ │
│  │ Documents        │ │ Chunks            │ │ XBRL Facts                   │ │
│  │ id, cik, ticker, │ │ chunk_id, doc_id, │ │ cik, ticker, period, fact, │ │
│  │ form, filing_date│ │ text, section,    │ │ value, unit, filing_date   │ │
│  │ source_url, sha  │ │ embedding (BGE),  │ └────────┬───────────────────┘ │
│  │ text_md          │ │ entities[], BM25  │          │                     │
│  └────────┬─────────┘ │ tokens, sentiment │          │                     │
│           │           └────────┬──────────┘          │                     │
│           │                    │                     │                     │
│  ┌────────▼────────────────────▼─────────────────────▼───────────────────┐  │
│  │  INDEXES                                                             │  │
│  │  • BM25 index (tantivy/rank-bm25 over chunk text)                    │  │
│  │  • Dense index (pgvector/Qdrant; BGE-base-en embeddings)              │  │
│  │  • Temporal Knowledge Graph (NetworkX + Parquet nodes/edges)          │  │
│  │    Nodes: Company, Security, Person, Event (Filing/News), MacroDate   │  │
│  │    Edges: issues → (company-filing), mentions → (event-entity),       │  │
│  │           leads → (officer-company), co_occurs → (entity-entity)       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Entity Registry (Wikidata+SEC company_tickers.json hybrid)           │  │
│  │  ticker, cik, name, aliases[], isin, sector, qid                     │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
       │ retrieve
       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  RETRIEVAL & RANKING LAYER                                                   │
│  Query ──► [ Entity Linker (mention→ticker) ] ──► Entity filter (optional) │
│            │                                                                 │
│            ├─► BM25 retrieval (top-100) ──┐                                  │
│            ├─► Dense retrieval (BGE, top-100) ├─► RRF Fusion (k=60) ──►      │
│            │                                 │      Top-50                  │
│            └─► Hybrid candidate pool (dedup) ┘                                │
│                                                                              │
│                        ▼                                                     │
│              Cross-Encoder Reranker (MiniLM-L6 / ColBERT)                   │
│                     Rerank top-50 → Top-10 (with scores)                     │
│                        │                                                     │
│              Temporal filter: filing_date ≤ query_timestamp (PIT)            │
│              Provenance attach: source_url + section + filing_date            │
└──────────────────────────────────────────────────────────────────────────────┘
       │ top-10 evidence
       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  GENERATION & ANALYTICS                                                      │
│  ┌────────────────────────┐ ┌──────────────────────────────────────────────┐ │
│  │ Grounded QA (RAG)      │ │ Market Impact Analytics                     │ │
│  │ LLM (Qwen2.5-3B local │ │ Event window (t-1, t+10) over Yahoo OHLCV  │ │
│  │  or GPT-4o-mini API)  │ │ → Abnormal return (vs SPY)                │ │
│  │ Prompt: evidence +    │ │ → Volatility regime (GARCH-conditional)   │ │
│  │  instruction           │ │ → Volume anomaly (IsolationForest)        │ │
│  │ Output: answer +       │ │ → PatchTST volatility forecast (optional) │ │
│  │  citations + confidence│ └───────────────────────────────────────────┘ │
│  │  "No evidence" fallback│                                                │
│  └────────────┬───────────┘                                                │
└───────────────┼──────────────────────────────────────────────────────────────┘
                │ API response
                ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  API LAYER (FastAPI)                                                         │
│  GET  /search?q=&entity=&before=&limit=          Hybrid retrieval            │
│  POST /qa       {question, entity, before}       Grounded QA                 │
│  GET  /timeline/{ticker}?from=&to=              KG timeline                 │
│  GET  /impact/{event_id}                        Impact analytics             │
│  GET  /entity/{ticker}/profile                  Entity dossier              │
│  GET  /health /metrics                          Monitoring                  │
└──────────────────────────────────────────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  FRONTEND (Next.js/React ,  Financial Technology Aesthetic)                   │
│  • Search bar + entity filter + date range + "Strict PIT" toggle             │
│  • Results: chunk cards with provenance (ticker, form, section, date, src)   │
│  • QA panel: answer + per-claim citations (clickable to filing excerpt) +    │
│  │           confidence bar + "No evidence" state                             │
│  • Timeline: event-entity chronological view (KG-driven, filterable)          │
│  • Impact: price/vol chart (t-5 → t+10) + abnormal return metric +           │
│  │         volatility band + volume anomaly flag                               │
│  • Benchmark: live nDCG/Recall@10 from eval run + ablation toggles           │
│  • Admin: ingestion status, validation, drift metrics                         │
└──────────────────────────────────────────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  EVALUATION & MONITORING                                                     │
│  • Offline eval suite (see §9.5): FinanceBench, FiQA-BEIR, custom PIT QA    │
│  │  → nDCG@10, Recall@10, MRR, EM/F1, PR-AUC; stored to eval/results.json   │
│  • Temporal correctness harness: future doc leak assertion                    │
│  • MLflow or JSON experiment tracker (ab lations logged)                     │
│  • Monitoring: retrieval latency p50/p95, reranker throughput,               │
│  │  embedding VRAM, ingestion freshness, XBRL schema drift                   │
│  • Tests: unit (ER accuracy) + integration (search→qa) + e2e (demo flows)  │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow Example (Traceable)

> **User query:** "What did JPMorgan say about credit risk in its latest 10-K before March 2024?"

1. **Ingest (offline):** SEC fetcher pulled JPM (CIK 19617) 2023 10-K (filed 2024-02-16), chunked 512 tokens, NER detected "credit risk" segments in Item 1A + 7, linked entity "JPMorgan" → ticker JPM, XBRL facts parsed (revenues, provisions)
2. **Index:** Chunks indexed in BM25 + dense (BGE) + KG edge: (JPM) , issues→ (2023-10K, 2024-02-16) , mentions→ (credit risk, provision for credit losses $X)
3. **Query:** Entity linker maps "JPMorgan" → JPM; temporal filter `before=2024-03-01` excludes 2024 Q1 10-Q (filed April)
4. **Retrieve:** BM25 hits "credit risk" lexical; dense hits semantic "credit losses/provisions"; RRF fusion → top 50; Cross-encoder reranks → top 10 (Item 1A + Item 7 chunks of JPM 2023 10-K + peers if relevant)
5. **Generate:** LLM receives 10 chunks + provenance; outputs: "JPM highlighted rising credit risk due to X, provisioning $Y (see 10-K Item 1A §2, filed 2024-02-16 [link])" + confidence 0.82 + "No post-March 2024 disclosure considered"
6. **Impact (optional):** User clicks "Impact" → price chart 2024-02-16 ±10d, abnormal return vs SPY +0.3% (ns), volatility no spike ,  "filing not market-moving"
7. **Eval:** This query type is part of custom PIT QA (200 Qs) → recall@10 + EM evaluated offline; temporal harness asserts April filing not returned.

---

## 3. Model Architecture ,  Every Model Specified

### 3.1 Embedding / Bi-Encoder ,  Dense Retrieval

- **Purpose:** Query → chunk semantic similarity; candidate pool for hybrid retrieval
- **Model:** `BAAI/bge-base-en-v1.5` (768-d, 110M params, Apache 2.0) ,  primary. Alternative: `intfloat/e5-base-v2` (comparable; ablation). *Not* large (BGE-large 335M unnecessary; 8GB safe)
- **Input:** Chunk text (≤512 tokens) or query text (≤128 tokens)
- **Output:** L2-normalized 768-d vector
- **Training:** Zero-shot initially; optional **fine-tuning on financial pairs** (FiQA + FinanceBench Q→evidence pairs via hard-negative mining from filings) using Sentence-Transformers MultipleNegativesRankingLoss ,  1 epoch, lr 2e-5, batch 32, fp16 → ~15 min on 4060 8GB. Ablation compares zero-shot vs fine-tuned (reported in eval)
- **Why BGE:** SOTA on BEIR; 768-d fits pgvector index (50k chunks × 768 × 4 bytes ≈ 150MB)

### 3.2 Sparse Retrieval ,  BM25

- **Model:** BM25 (Robertson & Zaragoza) via `rank-bm25` (Python) or `tantivy` (Rust-backed for larger corpus) ,  no training; k1=1.5, b=0.75 (tuned on FiQA val)
- **Input:** Tokenized chunk/query
- **Output:** Score + rank
- **Why:** Deterministic lexical recall for identifiers (ticker BRK.B, section "Item 1A", legal entities). Proven +10% Recall@100 over pure dense on finance benchmarks (ablation in Bloomberg pattern)

### 3.3 Fusion ,  Reciprocal Rank Fusion (RRF)

- **Model:** RRF: score(d) = Σ 1/(k + rank_i(d)), k=60 (Cormack et al.)
- **Input:** BM25 ranked list + Dense ranked list (top-100 each)
- **Output:** Fused top-50 candidate set (deduped)
- **Why:** Training-free hybrid fusion; reproducible; outperforms learned fusion on small val sets

### 3.4 Cross-Encoder Reranker

- **Model:** `cross-encoder/ms-marco-MiniLM-L6-v2` (80M params, Apache 2.0) or `colbert-ir/colbertv2.0` ,  reranks fused candidates jointly (query+doc input)
- **Input:** (query text, chunk text) pair ,  truncation to 512 tokens combined
- **Output:** Relevance logit → calibrated score + rank; top-10 selected
- **Inference:** Batch 16-32 fits 8GB (80M param → ~320MB VRAM + activations). ~0.05s per rerank batch of 32 on 4060
- **Training:** Zero-shot MS MARCO already. Domain fine-tuning optional (FiQA triples) but not required for strong baseline ,  ablation reports zero-shot vs fine-tuned
- **Why:** Cross-encoders deliver +10-15% nDCG@10 over bi-encoders (Karpukhin, Llinás). We rerank only 50 → 10 to contain latency (p95 <400ms)

### 3.5 Named Entity Recognition (NER) ,  Mention Detection

- **Model:** `nlpaueb/sec-bert-num` (BERT pre-trained on SEC filings) or `Jean-Baptiste/roberta-large-ner-english` fine-tuned ,  token classification
- **Input:** Chunk text
- **Output:** Spans: ORG (company), MONEY, DATE, possibly TICKER via regex layer
- **Training:** FiNER-ORD (201 sentences) + distant supervision from SEC registry (exact ticker aliases → synthetic labels) ,  fine-tune 3 epochs, lr 3e-5
- **Fallback:** Regex TICKER detector: `\b[A-Z]{1,5}(\.[A-Z])?\b` filtered against entity registry (prevents false ticker detection on common caps)

### 3.6 Entity Linking (ER) ,  Mention → Canonical Ticker/CIK

- **Model:** Hybrid:
  1. **Deterministic:** Exact ticker/CIK match (from NER ticker regex + SEC ticker map)
  2. **Lexical:** BM25 over entity registry (name/aliases) ,  candidate generation (top-5)
  3. **Embedding re-rank:** BGE similarity between mention context (50 tokens) and entity description (Wikidata + sector) ,  disambiguation
  4. **Graph consistency:** If query contains multiple entities, joint resolution via KG co-occurrence prior
- **Input:** Mention span + surrounding chunk context + query context (if available)
- **Output:** Ranked candidates: `{ticker, cik, qid, score, type: deterministic|embedding}`; top-1 threshold 0.7, else "unlinked"
- **Training:** No LM training ,  deterministic + embedding similarity already zero-shot; rule weights tuned on FiNER-ORD + custom 200-mention eval set
- **Evaluation:** Accuracy @1, F1 over entity-linked chunks; target >85% @1 on our entity set (50 tickers)
- **Why hybrid:** Mirrors Senzing/Institutional Financial Infrastructure pattern: rule + ML + graph. Replicable without giant ER model (Ditto, DeepER require large supervised record pairs)

### 3.7 Financial Sentiment Classifier (Auxiliary)

- **Model:** `ProsusAI/finbert` (FinBERT, BERT-base finetuned on PhraseBank) ,  110M params
- **Input:** Sentence or chunk
- **Output:** Probs: positive / neutral / negative (+ logits)
- **Training:** Already fine-tuned on PhraseBank (allagree ~86% accuracy). We do NOT retrain unless ablation shows gain via additional FiQA data
- **Role:** Per-chunk sentiment signal stored alongside embedding; enables sentiment-filtered search ("show negative risk-factor updates") and event sentiment feature for impact model
- **Evaluation:** Accuracy/F1 on PhraseBank held-out (standard 80/20 split); PR-AUC for negative class (operationally important)

### 3.8 XBRL Financial Facts Temporal Model

- **Model:** Not a neural model ,  **statistical anomaly detector** over XBRL time-series (Revenue, Net Income, Total Assets per period)
- **Method:** Per-company Z-score / change-point detection (PELT) over sequential filings (e.g., revenue discontinuity, restatement flag)
- **Input:** XBRL facts table (company × period × fact value)
- **Output:** Anomaly flag + severity for facts deviating >3σ from rolling mean or break-point
- **Why:** Demonstrates data-quality pipeline (institutional governance) with measurable anomalies (e.g., synthetic restatement injection for eval). Lightweight ,  no VRAM cost

### 3.9 Market Impact Analytics Models

#### a) Event Study ,  Abnormal Return

- **Model:** Market model (CAPM-like) regression: R_it = α + β R_mt + ε; abnormal return AR = R_it − (α̂ + β̂ R_mt)
- **Estimation window:** t-60 to t-10 (excludes event window t-1 to t+10)
- **Market proxy:** SPY / VTI ETF (or sector ETF for heterogenous adjustment)
- **Output:** Cumulative abnormal return (CAR), t-statistic, significance (p-value under Gaussian)
- **Evaluation:** Check CAR distribution over random dates vs event dates (should diverge for real events) ,  not claiming predictability, just quantifying
- **Why:** Classical, interview-defensible, requires no training ,  demonstrates financial literacy, not naive ML

#### b) Volatility Anomaly Detector

- **Model:** EGARCH(1,1) conditional volatility (statsmodels `arch` or `neuralforecast` TFT) + Isolation Forest over realized vol / VIX-relative vol / volume z-scores
- **Input:** OHLCV derived features: log returns, realized vol (20d), volume ratio, macro rate regime
- **Output:** Anomaly score (IF decision function) + volatility forecast interval (EGARCH 1-5d ahead) + flag if post-event vol exceeds forecast 95% CI
- **Training:** Unsupervised on t-250 to t-10 window; supervised labels from synthetic injection (vol spike of known magnitude) for PR-AUC evaluation
- **Evaluation:** PR-AUC, detection delay (days), FPR@90% Recall ,  proper imbalance-aware metrics
- **Why:** Aligns with Institutional Financial Infrastructure Trade Surveillance (anomaly detection over market data) but feasible on public OHLCV

#### c) Optional Volatility Forecaster (PatchTST)

- **Model:** `PatchTST` (Nie et al.) via neuralforecast/TSlib ,  10M params, channel-independent
- **Input:** 120-day log-return sequence (patched) → 5-day realized vol forecast
- **Output:** Point forecast + probabilistic interval (if quantile head)
- **Training:** Pre-train on S&P 500 OHLCV panel (50 tickers × 750 days) ,  30k windows; 10 epochs, lr 1e-3, batch 32, fp16 → ~20 min on 4060
- **Evaluation:** MAE/RMSE on held-out tickers/time + MASE vs naive seasonal; ablation: PatchTST vs TFT vs GARCH baseline
- **Activation gate:** Only if Phase 1 IR/KG complete; can be omitted if VRAM pressure (cut line) ,  event study + GARCH already sufficient

### 3.10 Generative QA Model ,  Grounded Answer Generation

- **Model:** Local: `Qwen/Qwen2.5-3B-Instruct` (3B, ~6GB in 4-bit quantization via `bitsandbytes` → fits 4060 8GB with 768-d embeddings co-resident) OR API: `gpt-4o-mini` / `claude-3.5-haiku` fallback if local infeasible
- **Input prompt template:**
  ```
  You are a financial document assistant. Answer ONLY from the provided evidence. Cite each claim as [source filing_date section source_url]. If evidence is insufficient, say "No evidence found in retrieved sources."
  Question: {question}
  Entity filter: {entity} (if linked)
  Evidence (top-10 chunks with provenance):
  [1] {chunk_text} ,  Source: {ticker} {form} {section} filed {filing_date} {source_url}
  ...
  Answer with citations after each sentence.
  Confidence (low/med/high): calibrate based on evidence coverage and agreement.
  ```
- **Output:** Structured JSON: `{answer_text, citations: [{source_id, excerpt, url}], confidence: 0-1, no_evidence_flag}`
- **Training:** No fine-tuning ,  RAG via prompting. Instruction-tuning unnecessary; evidence sufficiency is controlled via retrieval, not LLM training. This is intentional (demonstrates understanding that RAG quality = retrieval quality)
- **Evaluation:** FinanceBench human scoring pattern: correctness (0/0.5/1), citation coverage (% answer sentences with valid citation), abstention rate when no evidence (should be high → hallucination prevention)
- **Why not fine-tune LLM:** 8GB cannot hold training for 7B+ finetuned LLMs; prompt-based RAG is reproducible and correctly attributes quality to retrieval ,  a more sophisticated engineering statement

---

## 4. Dataset Strategy ,  Exact

### 4.1 Primary Corpora (see DATASET_AND_SOURCE_CATALOG for full access details)

| Corpus | Entities | Time Span | Size | Split |
|--------|----------|-----------|------|-------|
| SEC 10-K/Q/8-K (S&P 50 subset: AAPL, MSFT, JPM, BAC, WFC, GS, JNJ, PFE, XOM, ... 50) | 50 tickers | 2022-01-01 → 2025-11-01 | ~600 filings (10-K+Q mixed) → ~15k chunks | Train: ≤2023-12-31, Val: 2024-01-01→2024-12-31, Test: 2025 only (temporal, no shuffling) |
| Yahoo OHLCV | Same 50 tickers + SPY benchmark | 2020-01-01 → 2025-11-01 | ~750 trading days × 50 = 37.5k rows | Same temporal splits as above; features lag 1 day |
| FRED macro | DFF, DTB3, T10Y2Y, INDPRO | 2020 → 2025 | ~2k rows | Aligned to OHLCV dates |
| Entity registry | 50 entities + aliases | Static as-of 2023-01 | 50 rows × ~10 aliases | N/A (registry frozen) |

**Temporal split rationale:** Mandatory for finance ,  prevents future filing → past query leakage. Test set is always future relative to training (2025 filings/questions never seen during retrieval tuning). This is the interview differentiator.

### 4.2 Benchmark Splits

| Benchmark | Our Temporal Split | Size | Notes |
|-----------|--------------------|------|-------|
| FinanceBench | Original 150 Qs (filings up to 2023) ,  we re-time PIT via filing_date | 150 → filtered to 90 within our 50-entity universe | Human-grade QA |
| FiQA-BEIR (HF `BeIR/fiqa`) | Original train/val/test preserved (non-temporal; acceptable for retrieval bench) | 648 queries | Retrieval only (nDCG) |
| Custom PIT QA | **Generated from our EDGAR corpus** ,  templated questions with known answers per filing (revenue, officers, risks) + temporal stamps | 200 Qs (80 train for tuning, 40 val, 80 test strictly future) | Core temporal correctness proof |

### 4.3 Leakage Prevention Controls

- **PIT assertion test:** `test_pit_retrieval()` ,  for 20 fixtures, creates query at T, indexes future filing at T+30 days, asserts future doc never returned (via retrieval API with `before=T` param). Runs in CI.
- **Survivorship:** Universe fixed as S&P 500 constituents as-of 2023-01-01 (Wikipedia historical table). Delisted entities remain in corpus (yfinance may lack post-delisting prices ,  flagged as missing, not excluded). Document survivorship bias explicitly in report.
- **Label leakage:** Custom PIT QA answers derived from XBRL facts *of the same filing* chunked separately ,  QA retriever must retrieve chunk containing answer; no label injected into chunk metadata.
- **Time-series:** Features use only t-1 prices; no forward fill of today's close into features.

---

## 5. Evaluation ,  Suite Designed Before Implementation

### 5.1 Retrieval Evaluation

| Metric | Definition | Why Appropriate | Target |
|--------|------------|-----------------|--------|
| **Recall@10** | % of queries where ≥1 relevant doc in top-10 | Primary for financial discovery (find relevant disclosure) | >0.82 on FiQA; >0.75 on FinanceBench |
| **nDCG@10** | Graded relevance (0/1/2) discounted by rank | Captures ranking quality (best doc should be top, not 10th) ,  production RAG KPI | >0.72 FiQA; >0.68 FinanceBench |
| **MRR** | Mean reciprocal rank of first relevant | QA latency proxy ,  first hit matters | >0.70 FiQA |
| **MAP** | Mean average precision | Rank-insensitive supplement | Tracked |
| **Baselines:** | BM25 only, Dense only (BGE zero-shot), Dense fine-tuned only, Hybrid RRF, Hybrid+reranker (our final) ,  **5-way ablation** | Demonstrates each layer's contribution | Report per benchmark |

### 5.2 QA / Grounded Generation Evaluation

| Metric | Method | Target |
|--------|--------|--------|
| **Exact Match (FinQA/ConvFinQA style)** | Normalized answer string match | >0.35 (FinanceBench is hard ,  median ~0.30 for RAG) |
| **F1 / ROUGE-L** | Token overlap / longest subsequence | >0.55 F1 on custom PIT QA |
| **Citation Coverage** | % answer sentences with valid citation to retrieved chunk (automated via citation parser) | >85% |
| **Abstention Accuracy** | When no evidence exists, model says "No evidence found" (not hallucinate) ,  measured on 20 negative queries | >90% |
| **LLM-as-Judge (optional)** | GPT-4o-mini grades correctness 0-1 (FinanceBench protocol) | Correlation with human 0.8+ |
| **Latency p95** | End-to-end QA response time (retrieval + rerank + LLM) | <3s (local Qwen-3B) / <1.5s (API) |

### 5.3 Entity Resolution Evaluation

| Metric | Dataset | Target |
|--------|---------|--------|
| **Accuracy@1** | FiNER-ORD + 200 custom mentions (ambiguous aliases like "Chase" → JPM vs SCHW) | >0.85 |
| **Precision/Recall per entity** | Confusion matrix for top-10 tickers | P>0.87, R>0.83 |
| **Linking latency** | Mean per mention | <50ms |

### 5.4 Anomaly / Impact Evaluation

| Metric | Method | Target |
|--------|--------|--------|
| **Event study: CAR significance** | % events with CAR t-stat >1.96 (p<0.05) vs random dates (placebo) | Report both; CAR not accuracy claim |
| **Volatility anomaly PR-AUC** | Isolation Forest scores vs synthetic injected spikes (200 events) | PR-AUC >0.75 |
| **Detection delay** | Trading days from event to anomaly flag | ≤2 days |
| **FPR@90% Recall** | False positives when catching 90% of injected anomalies | Report honestly |
| **PatchTST vs GARCH MASE** | MASE (scaled MAE) vs naive/one-step | MASE <1.0 (beats naive) |

### 5.5 Ablation Experiments (Required in Implementation)

1. **Retrieval ablation:** BM25 → +Dense → +RRF → +Reranker (4 bars per benchmark)
2. **Entity filter ablation:** Hybrid without entity filter vs with (measures entity layer lift)
3. **Temporal filter ablation:** PIT on vs off (does off retrieve future docs? measure leakage incidence)
4. **Sentiment ablation:** Does sentiment-enriched reranking improve finance QA? (likely small ,  report negative result honestly)
5. **Embedding fine-tune ablation:** Zero-shot BGE vs finetuned on FiQA+filings

### 5.6 Robustness & Resource Tests

- **Missing data:** Filing HTML corrupt / XBRL fact missing → graceful degradation (return available chunks, flag missing)
- **Duplicate records:** Same filing accession ingested twice → deduplicated by accession id
- **Malformed inputs:** Empty query, unknown ticker, future date beyond corpus → 200 with informational response
- **Latency/Throughput:** Locust/k6 load test over /search (100 req/sec sustained, p95 <400ms retrieval-only)
- **VRAM profiling:** `torch.cuda.memory_summary()` logged per batch config; stays <7.2GB peak (mixed precision + batch 32 + gradient accumulation if fine-tuning BGE)
- **Generalisation:** Test on 10 held-out tickers not in top-50 training universe (transfer to unseen issuer)

---

## 6. GPU & Performance Engineering ,  RTX 4060 8GB

### 6.1 VRAM Budget (Mixed Precision fp16 via autocast)

| Component | Params | VRAM (fp16) | Batch | Notes |
|-----------|--------|-------------|-------|-------|
| BGE-base (embedding) | 110M | ~220MB model + ~1.2GB activations @ batch 32 | 32 chunks/batch | Embedding inference only; finetune needs ~3GB with grads |
| MiniLM-L6 cross-encoder | 80M | ~160MB + ~800MB activations @ batch 32 | 32 (rerank) | Rerank top-50 in 2 batches (32+18) |
| FinBERT | 110M | ~220MB | 32 | Sentiment pass over chunks (offline) |
| Qwen2.5-3B (4-bit BnB) | 3B | ~2.5GB (4-bit quant) + ~1GB KV cache | 1 (generation) | Local LLM ,  if VRAM pressure, fallback to API |
| PatchTST | ~10M | ~40MB + activations | 32 seq | Negligible |
| **Concurrent peak** | | **~6.8GB** | | Leaving ~1.2GB headroom |

**Techniques:**
- **Mixed precision (fp16):** All embedding/reranking inference under `torch.autocast`
- **Gradient accumulation:** BGE fine-tuning: effective batch 64 via 2×32 micro-batches if finetuning needed (grad accumulation 2)
- **4-bit quantization (bitsandbytes NF4):** Qwen-3B local inference
- **ONNX Runtime:** FinBERT sentiment over entire corpus ,  batch export to ONNX → CPU inference for offline pass (free GPU for retrieval)
- **Embedding cache:** Precompute all chunk embeddings → store in Qdrant/pgvector → zero VRAM at query time except reranking pass
- **CPU/GPU split:** BM25 (CPU), XBRL parsing (CPU), KG construction (CPU/NetworkX), GARCH/anomaly (CPU/sklearn+arch) ,  GPU only for embedding/reranking/generation
- **Memory profiling script:** `scripts/profile_vram.py` logs peak per stage → documented in report

### 6.2 Latency SLOs

| Endpoint | Target p95 | Technique |
|----------|------------|-----------|
| /search (retrieval only) | <400ms | BM25 (CPU ~50ms) + dense ANN (pgvector ~80ms) + RRF (negligible) + rerank 50→10 (~200ms on 4060) |
| /qa (RAG) | <3s local / <1.5s API | Retrieval (400ms) + prompt construction (~50ms) + Qwen-3B decode (2s for 200 tokens) |
| /timeline | <300ms | KG query (NetworkX traverse ~20ms) + enrich from docs (cached) |
| /impact | <500ms | Event study calc (CPU, cached prices ~100ms) + chart payload |

---

## 7. Technical Feasibility Gate ,  One Developer, 8 Weeks

| Question | Answer | Mitigation if Fails |
|----------|--------|---------------------|
| Can one developer build it? | Yes ,  phased delivery: P1 (ingest→IR→eval) 3 weeks, P2 (ER→KG→timeline) 2 weeks, P3 (QA→impact→frontend→tests) 3 weeks. Each phase independently demonstrable. | Cut PatchTST (optional) first, then impact analytics, then KG graph ML ,  leaving core IR+ER+provenance as minimal viable product (still 80+ score candidate C09+C07) |
| Datasets acquirable? | Yes ,  all public, scripted; SEC fetcher respects 10 req/s → 600 filings in ~60 sec + chunking | If EDGAR rate-limited, use sec-edgar-downloader fallback + cache |
| Models accessible? | Yes ,  all HF Apache/MIT; no gated models; Qwen-3B public; BGE/MiniLM public | Fallback: gpt-4o-mini API for QA if local Qwen VRAM fails (documented branch) |
| Reproducible? | Yes ,  temporal splits documented, seeds fixed, pip freeze, Docker | GitHub repo with DVC or download script + Makefile |
| Runs on 8GB? | Yes ,  budget above proves 6.8GB peak; mixed precision + 4-bit LLM + CPU offloads | Fallback to API LLM documented |
| Evaluable? | Yes ,  4 benchmarks (FiQA-BEIR, FinanceBench, TAT-QA optional, custom PIT 200) + ablation harness | Minimum: FiQA + custom PIT always evaluable (public filing corpus) |
| Demoable? | Yes ,  Next.js UI with 4 workflows (search, QA, timeline, impact) + chart | Screenshots + Loom for non-local deployment |

---

## 8. Research Feasibility ,  Methodological Foundation

**Strongest papers supporting each component:**

- **Hybrid retrieval:** Karpukhin 2020 (DPR), Khattab & Zaharia 2020 (ColBERT), Formal 2021 (SPLADE), Robertson BM25, RRF (Cormack 2009) ,  all open, reproduced, HF implementations available
- **Financial sentiment:** Araci 2019 (FinBERT) ,  4,845 PhraseBank samples, reproducible via `ProsusAI/finbert`
- **Financial QA:** Chen 2021 (FinQA), Zhu 2021 (TAT-QA), Islam 2023 (FinanceBench) ,  all MIT, with code/data
- **Time-series:** Nie 2023 (PatchTST ICLR), Wu 2023 (TimesNet) ,  TSlib/neuralforecast implementations
- **Entity resolution pattern:** Mudgal 2018, Li 2020 (Ditto) ,  not directly reused but pattern informs hybrid ER (rule+embedding) ,  we cite as inspiration, not claim replication of large supervised ER
- **Temporal KG:** Cai et al. TFLEX ,  temporal logic embeddings; we cite for KG temporal edge motivation

**Baselines to reproduce before claiming lift:** BM25 alone, BGE zero-shot, FinBERT sentiment (all trivial to run) → then show hybrid+rerank+ER beats them (ablation provides honest comparison, including negative results).

**Novelty statement (interview-safe):** "We do not claim a novel architecture. We claim a **novel integration** of production IR patterns (hybrid fusion, cross-encoder reranking, entity-resolved temporal retrieval) applied rigorously to financial filings with point-in-time guarantees ,  a combination absent from open source and directly mapping to institutional documented pipeline. Our contribution is engineering rigor (evaluation, leakage prevention, provenance) not architectural invention."

---

## 9. Evaluation Feasibility ,  Can It Be Quantitatively Evaluated?

- **Retrieval:** Yes ,  FiQA-BEIR (648 queries), FinanceBench (90 filtered), custom PIT QA (200) ,  3 benchmarks, 5 ablation conditions, ~15 × 3 = 45 reported nDCG/Recall numbers
- **QA:** Yes ,  FinanceBench EM/F1 + custom PIT EM/F1 + citation coverage + abstention (all automated except LLM-judge correlation check)
- **ER:** Yes ,  FiNER-ORD + custom 200 mentions
- **Anomaly:** Yes ,  synthetic injection over Yahoo OHLCV (200 injected spikes vs 200 normal windows → PR-AUC)
- **Reproducibility:** Seeds fixed; splits versioned; `eval/run_all.py` outputs `eval/results.json` with all metrics + timestamps + git SHA
- **Business utility proxy:** Event study CAR distribution (quantifiable); timeline query latency; user workflow click-through (mock user study: 10 sample tasks timed vs naive baseline ,  optional stretch)

---

## 10. Interview Feasibility ,  Can You Defend It?

A rehearsed candidate must be able to answer (30-question prep in Implementation Prompt covers all):

- **Domain:** What's survivorship bias in price data and how did you handle it? Why is point-in-time retrieval required for finance? What's XBRL and why is it imperfect? What is institutional PermID and your substitute?
- **ML:** Why hybrid retrieval vs pure dense? Why cross-encoder reranking vs bi-encoder only? Why RRF over learned fusion? Why BGE-base not large? Why FinBERT auxiliary not end-to-end?
- **Data:** How many filings did you ingest and how did you respect SEC Fair Access? How do you detect duplicate filings? What's the provenance schema?
- **Architecture:** Draw the full pipeline. Where does VRAM pressure peak? Why Qdrant vs pgvector? How does entity linking reduce false positives?
- **Evaluation:** What's nDCG vs Recall@K? Why PR-AUC not ROC-AUC for anomaly? What was the biggest ablation surprise (negative result)? What fails on held-out tickers?
- **Deployment:** How would you monitor retrieval relevance drift? What's your indexing throughput? How do you handle XBRL schema change?
- **Trade-offs:** Why didn't you fine-tune a 7B LLM? Why not real order-book surveillance? Why not BloombergGPT-scale pretraining?

All answerable from this document ,  no hidden magic.

---

## 11. Winner Selection Summary

**Project:** Financial Knowledge Graph & Temporal Retrieval Platform ,  Entity-Resolved Temporal KG + Hybrid Retrieval + Grounded QA + Impact Analytics  
**Score:** 94/100 ,  clear winner by >12 points over next (C11 82)  
**Institutional Financial Infrastructure alignment:** All four divisions + Innovation & Intelligence JD (9/9)  
**ML depth:** Hybrid IR (fusion+reranking), NER+ER (hybrid), graph construction, anomaly detection, event studies, optional PatchTST ,  multiple defensible components  
**Feasibility:** Public data, 8GB VRAM budget (6.8GB peak), 8-week phased delivery with cut lines  
**Evaluation:** 4 benchmarks, 5-way ablation, leakage harness, resource profiling ,  measurable before implementation  
**Differentiation:** 0/6 open-source financial RAG systems have this stack (proven in landscape audit)  
**Interview angle:** "I rebuilt institutional documented mastering + Knowledge Graph + Workspace retrieval pattern with public data, measured it, and prevented temporal leakage ,  here's the evidence."

**No second-guessing.** C21 proceeds as specified.
