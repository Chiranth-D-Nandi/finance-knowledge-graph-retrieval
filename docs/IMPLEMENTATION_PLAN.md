# Master Implementation Plan
## Financial Knowledge Graph & Temporal Retrieval Platform

**System:** the platform (Entity-Resolved Temporal Knowledge Graph with Hybrid Financial Retrieval, Grounded QA, and Explainable Market Impact Analytics)  
**Target:** Institutional Financial Intelligence Project  
**Author:** Principal AI/ML Engineer + Data Engineer  
**Hardware Profile:** NVIDIA RTX 4060 Laptop (8GB VRAM), Python 3.11.9, Node.js v22.18.0  
**Version:** 1.0.0 ,  Dated 2026-11-16  

---

## 1. Executive Summary & Objective

the platform solves the financial disclosure fragmentation problem by implementing an end-to-end, production-grade AI system inspired by institutional research terminals, PermID mastering, and Risk Intelligence infrastructure. Using solely public data (SEC EDGAR, yfinance, FRED macro, Wikidata), it provides:
1. **Entity Resolution & Symbology:** Canonical mapping across ticker aliases, legal corporate names, and SEC CIKs.
2. **Temporal Knowledge Graph:** Point-in-time (PIT) graph representation linking companies, filings, executive officers, material events, and macro timestamps without future-data leakage.
3. **Hybrid Retrieval:** Multi-stage retrieval combining BM25 lexical recall, BGE dense semantic vectors, Reciprocal Rank Fusion ($k=60$), cross-encoder reranking (`ms-marco-MiniLM-L6-v2`), and strict point-in-time timestamp filtering.
4. **Grounded Generation:** Verifiable QA with per-sentence document citations, confidence estimation, and explicit negative abstention ("No evidence found").
5. **Market Impact Analytics:** Classical econometric event study (Cumulative Abnormal Return via market model vs. SPY), EGARCH conditional volatility intervals, and volume anomaly detection (Isolation Forest).
6. **Full-Stack Interface:** A financial-terminal dashboard (Next.js 14, Tailwind, dark navy `#0a1628` and teal `#00d4aa` palette) featuring 4 distinct analytical workflows.

---

## 2. Phased Milestones & Task Breakdown

```
Phase 1: Core Hybrid IR & Temporal Foundation (Milestone 1)
├── Task 1.1: Environment & Virtualenv Setup (Python 3.11, PyTorch CUDA, sentence-transformers, FastAPI)
├── Task 1.2: Project Architecture Scaffolding (src/, data/, api/, eval/, tests/, frontend/, docs/)
├── Task 1.3: Data Ingestion & Validation Pipeline (SEC EDGAR, yfinance, FRED, Pandera invariants, provenance)
├── Task 1.4: Preprocessing & Chunking (HTML to Markdown, 512-token chunks, 50 overlap, section tagging)
├── Task 1.5: Index Construction (BM25 sparse index, BGE dense index, Qdrant/vector store)
├── Task 1.6: Hybrid Retrieval Engine (Lexical + Dense candidate pools, RRF k=60, MiniLM reranker, PIT filter)
├── Task 1.7: Evaluation Harness & Leakage Verification (Temporal test suite, FiQA-BEIR & FinanceBench evaluators)
└── Task 1.8: Core FastAPI Service (/health, /search, /metrics) & Baseline Benchmarks

Phase 2: Entity Mastering & Temporal Knowledge Graph (Milestone 2)
├── Task 2.1: Entity Registry Construction (S&P 50 subset, SEC tickers, Wikidata aliases, sectors)
├── Task 2.2: Named Entity Recognition & Regex Disambiguation (FiNER-ORD / sec-bert / ticker regex)
├── Task 2.3: Hybrid Entity Linker (Deterministic exact match + BM25 aliases + BGE context disambiguation)
├── Task 2.4: Temporal Knowledge Graph Construction (NetworkX nodes: Company, Filing, Event, Person, Macro; temporal edges)
├── Task 2.5: Sentiment Tagging (FinBERT per-chunk positive/negative/neutral inference)
├── Task 2.6: XBRL Parser & Data Quality Anomaly Detector (companyfacts flattening, rolling Z-score, PELT change-point)
└── Task 2.7: Entity & Timeline APIs (/entity/{ticker}, /timeline/{ticker}, /entity/search)

Phase 3: Grounded QA, Impact Analytics & Production Frontend (Milestone 3)
├── Task 3.1: Grounded QA Generator (Prompt template with citation constraints, Qwen2.5-3B 4-bit / API fallback)
├── Task 3.2: Market Impact Econometrics (Market model OLS vs. SPY, CAR estimation [-1, +10], t-stat, p-value)
├── Task 3.3: Volatility & Volume Anomaly Detectors (EGARCH(1,1), Isolation Forest over volume/volatility)
├── Task 3.4: Complete API Endpoints (/qa, /impact/{event_id})
├── Task 3.5: Financial UI Development (Next.js 14 App Router, 4 workflows, Institutional Research Workspace theme)
├── Task 3.6: End-to-End Integration & Validation (scripts/validate_e2e.py, pytest suite)
└── Task 3.7: Portfolio Documentation & Verification (Ablation tables, figures, technical report, completion evidence)
```

---

## 3. Scope Management & Cut Lines

To guarantee zero incomplete features while delivering an enterprise-ready system:

- **Primary Gate (Milestone 1 ,  Non-negotiable):** Ingest, clean, validate with Pandera, compute BM25 + dense BGE embeddings, RRF fusion, MiniLM reranking, PIT leakage test pass (20/20), 4+ retrieval baselines measured.
- **Secondary Gate (Milestone 2 ,  Non-negotiable):** Entity registry (50 constituents), hybrid linker, NetworkX temporal KG, timeline view, sentiment enrichment, XBRL data quality flags.
- **Cut Line 1 (Entity Linker):** If embedding-based disambiguation underperforms on edge cases, fallback cleanly to deterministic ticker/alias match + warning in metadata.
- **Cut Line 2 (PatchTST Forecasting):** Time-series PatchTST is secondary to the primary event-study econometric CAR model + EGARCH. If VRAM or training time risks schedule, PatchTST will be ablated and documented as a planned extension in `LIMITATIONS.md`.
- **Cut Line 3 (News Proxies):** If external news feeds present licensing or availability hurdles, filing-based event disclosures (8-K, 10-K, 10-Q) serve as the primary ground-truth event catalog.
- **Cut Line 4 (Local LLM VRAM fallback):** If local 4-bit quantization on Windows hits CUDA toolkit library conflicts, the engine automatically routes to API LLM fallback with identical prompts and structured schemas, logging the exact execution mode without faking local GPU inference.

---

## 4. Risk Matrix & Mitigations

| Risk | Likelihood | Impact | Mitigation Strategy |
|---|---|---|---|
| **SEC EDGAR Rate Limiting (10 req/s)** | High | Med | Custom throttled client with backoff and exponential delay; declare standard academic/research User-Agent header with contact email. Cache raw filings on disk. |
| **GPU VRAM Overrun (>8GB)** | Med | High | Staged memory management: unload dense embedder / reranker models before invoking generation; use fp16 autocast and 4-bit quantization; batch sizes pinned to 32. |
| **Lookahead / Data Leakage** | High | Critical | Enforce strict PIT filter at the storage query level; verify with automated 20-fixture temporal leakage test in CI. |
| **XBRL Schema Inconsistencies** | Med | Low | Standardize taxonomy keys (e.g., US-GAAP Revenues, Assets, NetIncomeLoss) with fallback alias lists and robust error logging. |
| **Frontend-Backend CORS / Proxy Issues** | Low | Med | Implement Next.js App Router route handlers (`/api/search`, `/api/qa`, etc.) that proxy server-to-server calls to FastAPI at `127.0.0.1:8000`. |

---

## 5. Definition of Done (DoD)

A milestone or feature is marked complete only when:
1. Production code is typed, modular, and adhering to PEP 8 standards.
2. Invariants are validated with Pandera and Pydantic schemas.
3. Unit and integration tests pass cleanly via `pytest` without mocking away core logic.
4. Measured metrics are exported to `eval/results.json` and rendered in Markdown/CSV tables.
5. All 12 completion criteria (C1-C12) defined in §13 are satisfied with reproducible log evidence.
