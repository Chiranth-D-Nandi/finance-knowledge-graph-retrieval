# Dataset Provenance, Schemas & Temporal Split Boundaries
## Financial Knowledge Graph & Temporal Retrieval Platform

This document provides exhaustive documentation of all datasets (D1 through D12) ingested, processed, and evaluated within the platform, including source APIs, licensing, rate limits, schema definitions, point-in-time constraints, and lookahead leakage prevention mechanisms.

---

## 1. Dataset Catalog (D1 - D12)

| ID | Dataset Name | Primary Source / API | License / Terms | Modality | Role in the platform |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **D1** | SEC EDGAR Submissions API | `data.sec.gov/submissions/CIK{cik.zfill(10)}.json` | Public Domain (US Gov) | JSON Metadata | Entity mastering, filing history, accession numbers |
| **D2** | SEC EDGAR Company Facts | `data.sec.gov/api/xbrl/companyfacts/CIK{...}.json` | Public Domain (US Gov) | Structured XBRL | Multi-year US-GAAP line items, revisions, audit trail |
| **D3** | SEC EDGAR Full Filings | `www.sec.gov/Archives/edgar/data/...` | Public Domain (US Gov) | HTML / TXT | Item 1, 1A, 7, 7A disclosure chunks, NER & embedding |
| **D4** | S&P 500 Historical Universe | S&P Historical Lists / SEC | Public Research | Tabular CSV | Universe selection (S&P 50 focus), point-in-time tracking |
| **D5** | Equity Market Prices & Volume | Yahoo Finance (`yfinance`) | Public Yahoo ToS (Research) | Time-Series OHLCV | Market model OLS, event study CAR, EGARCH volatility |
| **D6** | Macroeconomic Time Series | FRED API (Federal Reserve) | Open Data (St. Louis Fed) | Time-Series | Macro factors (DFF, CPIAUCSL, DGS10, VIXCLS) |
| **D7** | Wikidata Financial Entities | Wikidata SPARQL / REST API | CC0 (Public Domain) | Knowledge Graph | QIDs, aliases, ISIN, LEI, PermID entity identifier alignment |
| **D8** | FiQA-2018 Benchmark | BEIR Benchmark / HuggingFace | Academic Research | IR Benchmark | 5-way retrieval ablation (BM25, Dense, Hybrid, Rerank) |
| **D9** | FinanceBench | Patronus AI / HuggingFace | Open Evaluation | Grounded QA | Financial reasoning & tabular verification evaluation |
| **D10** | SEC Restatements & Anomalies | SEC AAERs & XBRL Revisions | Public Domain / Research | Event Series | XBRL data quality, change-point detection (PELT) |
| **D11** | Temporal Leakage Harness | Internal Test Fixtures | Proprietary / Apache 2.0 | Test Fixtures | 20-fixture temporal boundary regression test suite |
| **D12** | Custom PIT QA Benchmark | Curated S&P 50 Filings QA | Apache 2.0 | QA Pairs (200) | Point-in-time grounded QA evaluation (180 pos, 20 neg) |

---

## 2. Ingestion Protocols & Rate Limit Compliance

### 2.1 SEC EDGAR Fair Access Compliance
SEC EDGAR enforces a mandatory rate limit of **10 requests per second** and requires a custom `User-Agent` string formatted as `Sample Company Name AdminContact@domain.com`.
- Implemented in `src/ingest/sec_fetcher.py`.
- Enforces an automated leaky-bucket / token-bucket rate limiter set to 8 req/sec maximum (20% safety margin).
- Configurable via `.env` parameter `SEC_USER_AGENT_EMAIL`.
- Returns structured JSON or raw text with exponential backoff and jitter on HTTP 429.

### 2.2 Yahoo Finance (`yfinance`) ToS Adherence
- Market data is queried with cached SQLite backends to prevent redundant egress.
- OHLCV ingestion is constrained to S&P 50 focus tickers and benchmark ETF `SPY`.
- Historical price adjustments (splits and dividends) are explicitly handled via `yfinance` adjusted prices.

### 2.3 FRED API (St. Louis Fed)
- Standard FRED API key configuration via `FRED_API_KEY`.
- Series ingested: Effective Federal Funds Rate (`DFF`), Consumer Price Index (`CPIAUCSL`), 10-Year Treasury Yield (`DGS10`), CBOE Volatility Index (`VIXCLS`).

---

## 3. Data Schemas & Pandera Validation Rules

All tabular and time-series data undergo strict runtime validation before reaching the storage or indexing layers (`src/ingest/validators.py`).

### 3.1 OHLCV Data Schema (`OHLCVSchema`)
```python
class OHLCVSchema(pa.DataFrameModel):
    date: pa.typing.Series[pd.Timestamp] = pa.Field(coerce=True)
    open: pa.typing.Series[float] = pa.Field(ge=0.0)
    high: pa.typing.Series[float] = pa.Field(ge=0.0)
    low: pa.typing.Series[float] = pa.Field(ge=0.0)
    close: pa.typing.Series[float] = pa.Field(ge=0.0)
    volume: pa.typing.Series[float] = pa.Field(ge=0.0)
    adjusted_close: pa.typing.Series[float] = pa.Field(ge=0.0, nullable=True)

    @pa.dataframe_check
    def check_high_low_invariants(cls, df: pd.DataFrame) -> pd.Series:
        # High must be greater than or equal to Open, Close, and Low
        return (df["high"] >= df["low"]) & \
               (df["high"] >= df["open"]) & \
               (df["high"] >= df["close"])
```

### 3.2 Filing Chunk Schema (`FilingChunkSchema`)
- `chunk_id`: Unique deterministic hash `doc_{cik}_{form}_{filing_date}_{idx}`.
- `cik`: 10-digit zero-padded string (e.g. `0000019617`).
- `ticker`: 1-5 character uppercase ticker symbol.
- `form`: Filing type (`10-K`, `10-Q`, `8-K`).
- `filing_date`: ISO format date string (`YYYY-MM-DD`).
- `section`: Identified disclosure section (`Item 1`, `Item 1A`, `Item 7`, `Item 7A`, `Other`).
- `token_count`: Integer bounded between 50 and 600 tokens.
- `source_url`: Canonical SEC EDGAR accession URL for end-to-end auditability.
- `sha256`: Cryptographic hash of raw chunk text.

### 3.3 XBRL Fact Record Schema (`XBRLFactSchema`)
- `cik`: 10-digit zero-padded SEC identifier.
- `ticker`: Issuer ticker.
- `taxonomy`: US-GAAP or IFRS taxonomy identifier.
- `tag`: Standardized XBRL concept (e.g., `Revenues`, `NetIncomeLoss`, `Assets`).
- `period_start`: Reporting period start date (`YYYY-MM-DD`).
- `period_end`: Reporting period end date (`YYYY-MM-DD`).
- `val`: Floating point numerical value.
- `unit`: Currency or unit code (`USD`, `shares`).
- `filing_date`: Official SEC acceptance date.
- `is_restated`: Boolean flag indicating subsequent revision.

---

## 4. Temporal Split Boundaries & Lookahead Leakage Prevention

Financial ML pipelines that fail to respect temporal point-in-time constraints suffer from disastrous lookahead bias (e.g., predicting 2023 performance using disclosures filed in May 2024).

### 4.1 Temporal Splitting Architecture
the platform configures immutable temporal boundaries in `data/splits/split_config.json`:
- **Training & Historical Knowledge Base:** Filings and market data filed $\le$ **2023-12-31**.
- **Validation Period:** Filings accepted between **2024-01-01** and **2024-03-31**.
- **Out-of-Sample Test Period:** Filings accepted between **2024-04-01** and **2024-09-30**.

### 4.2 Candidate-Level Point-in-Time (PIT) Filtering
In naive RAG implementations, retrieval engines score all documents and filter post-hoc. This breaks top-K pagination and risks information leakage.
the platform enforces point-in-time validity at the **candidate selection phase**:
$$\mathcal{D}_{\text{eligible}}(t) = \{ d \in \mathcal{D} \mid \text{FilingDate}(d) \le t_{\text{as\_of}} \}$$

Any filing published after $t_{\text{as\_of}}$ is strictly excluded prior to ranking, BM25 indexing, and vector similarity scoring.

---

## 5. Entity Resolution & PermID Harmonization

The canonical entity mastering table (`data/raw/entities/sp500_constituents_20230101.csv`) binds fragmented corporate symbologies:
1. **SEC CIK:** Legal regulatory entity identifier.
2. **Ticker Symbol:** Market trading symbol.
3. **Wikidata QID:** Global public knowledge base identifier.
4. **PermID entity identifier:** Institutional Financial Infrastructure global entity master identifier (cross-referenced via PermID).
5. **Corporate Aliases:** Acronyms, operating subsidiaries, previous names (e.g., "Google" $\to$ Alphabet, "Facebook" $\to$ Meta, "JPMorgan Chase & Co." $\to$ JPM).
