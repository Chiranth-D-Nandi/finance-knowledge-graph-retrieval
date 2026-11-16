# Dataset & Source Catalog ,  Financial AI Project

**Date:** 2026-11-16  
**Constraint:** Entire core project implementable using legitimate public data ,  no proprietary Institutional Financial Infrastructure feeds  
**Compliance:** SEC Fair Access (10 req/s, User-Agent header with contact email), Yahoo Finance ToS (educational/research, derived features only), FRED public domain macro series  

---

## 1. Market & Macro Datasets

### 1.1 Yahoo Finance OHLCV (`yfinance`)
- **Location:** `data/raw/market/yahoo_ohlcv.parquet`
- **Universe:** `AAPL`, `BAC`, `GS`, `JPM`, `MSFT`, and `SPY` (S&P 500 Market Benchmark)
- **Time Range:** 2022-01-01 to 2024-12-31 (4,512 rows, 7 columns: `date`, `ticker`, `open`, `high`, `low`, `close`, `volume`)
- **Quality Invariants:** Validated via Pandera schemas: High $\ge \max(\text{Open}, \text{Close})$, Low $\le \min(\text{Open}, \text{Close})$, Volume $\ge 0$.
- **Role:** Econometric event studies, market model OLS regressions ($R_{it} = \alpha + \beta R_{mt} + \epsilon$), Cumulative Abnormal Returns (CAR), volatility anomaly detection.

### 1.2 FRED Macroeconomic Series
- **Location:** `data/raw/macro/`
- **Series Ingested:**
  - `DFF`: Federal Funds Effective Rate
  - `DTB3`: 3-Month Treasury Bill Secondary Market Rate
  - `T10Y2Y`: 10-Year Treasury Constant Maturity Minus 2-Year Treasury (Yield curve slope)
  - `CPIAUCSL`: Consumer Price Index for All Urban Consumers
  - `UNRATE`: Civilian Unemployment Rate
  - `INDPRO`: Industrial Production Index
- **Role:** Macro regime covariates, interest rate sensitivity modeling, event contextualization.

---

## 2. SEC EDGAR Document Intelligence Core

### 2.1 SEC Submissions & Public Filings
- **API Endpoint:** `https://data.sec.gov/submissions/CIK{10-digit-CIK}.json`
- **Rate Limit Compliance:** Throttled to $\le 5$ req/s (below SEC 10 req/s ceiling), User-Agent header with verified email.
- **Forms Ingested:** Form 10-K (Annual Disclosures), Form 10-Q (Quarterly Reports), Form 8-K (Material Events).
- **Processing:** HTML extraction via Trafilatura + BeautifulSoup, section tagging (Item 1, Item 1A, Item 7, Item 7A, Item 8), token chunking (512 tokens with 50-token overlap), SHA-256 cryptographic provenance hashing.
- **Location:** `data/processed/chunks.parquet`

### 2.2 Structured XBRL Company Facts
- **API Endpoint:** `https://data.sec.gov/api/xbrl/companyfacts/CIK{10-digit-CIK}.json`
- **Metrics Ingested:** Revenues, NetIncomeLoss, Assets, Liabilities, OperatingCashFlow.
- **Location:** `data/processed/xbrl_facts.parquet`
- **Role:** Structured financial metrics integrated into the Point-in-Time Temporal Knowledge Graph.

---

## 3. Knowledge Graph & Entity Resolution

### 3.1 Entity Registry
- **Location:** `data/processed/entity_registry.json`
- **Scale:** 50 key financial and corporate entities across S&P 500.
- **Identifiers:** Ticker, 10-digit padded CIK, PermID format validation (`4295907168`), ISIN crosswalk, Wikidata QID, sector classification, and verified alias lists.

### 3.2 Temporal Knowledge Graph
- **Location:** `data/processed/kg_nodes.parquet`, `data/processed/kg_edges.parquet`
- **Graph Topology:** MultiDiGraph connecting Company nodes, Filing disclosure nodes, and FinancialFact nodes with temporal `issues`, `mentions`, and `reports` edges.

---

## 4. Evaluation & Benchmarking

### 4.1 Custom Point-in-Time QA Benchmark
- **Location:** `data/benchmarks/custom_temporal_qa.jsonl`
- **Volume:** 200 curated financial queries:
  - 160 positive answerable queries across 40 financial topics.
  - 20 lookahead leakage queries (timestamped before filing date, asserting 100% negative abstention).
  - 20 out-of-domain unanswerable queries (testing hallucination defense).
