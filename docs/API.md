# REST API Reference & Integration Guide
## Financial Knowledge Graph & Temporal Retrieval Platform

The REST API is built on FastAPI with full asynchronous support, Pydantic v2 schema validation, structured error responses, and low-latency response delivery.

- **Base URL:** `http://localhost:8000`
- **Interactive OpenAPI Documentation:** `http://localhost:8000/docs`
- **Raw OpenAPI Schema:** `http://localhost:8000/openapi.json`

---

## 1. System Health & Observability Endpoints

### 1.1 `GET /health`
Returns system operational status, model availability, GPU acceleration status, and real-time VRAM allocation.

**Response (HTTP 200 OK):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-11-16T14:40:00Z",
  "cuda_available": true,
  "device": "NVIDIA GeForce RTX 4060 Laptop GPU",
  "vram_allocated_mb": 1420.5,
  "vram_reserved_mb": 2048.0,
  "models_loaded": {
    "embedding": "BAAI/bge-base-en-v1.5",
    "reranker": "cross-encoder/ms-marco-MiniLM-L6-v2",
    "kg_nodes": 50,
    "indexed_chunks": 8
  }
}
```

### 1.2 `GET /metrics`
Returns system performance telemetry, request counts, error rates, and p50/p95 latency measurements.

**Response (HTTP 200 OK):**
```json
{
  "total_requests": 1420,
  "active_sessions": 4,
  "retrieval_latency_ms": {
    "p50": 142.5,
    "p95": 185.2,
    "max": 310.8
  },
  "qa_latency_ms": {
    "p50": 1120.0,
    "p95": 1640.0
  },
  "temporal_violations_detected": 0
}
```

---

## 2. Core Financial Intelligence Endpoints

### 2.1 `GET /search`
Executes 5-stage hybrid retrieval (Entity Linker $\to$ BM25 + BGE $\to$ Reciprocal Rank Fusion $\to$ Cross-Encoder $\to$ PIT Filter).

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `q` | `string` | **Yes** | - | Natural language or keyword search query |
| `ticker` | `string` | No | `null` | Target equity ticker (e.g. `JPM`, `AAPL`) |
| `as_of_date` | `string` | No | `null` | ISO date (`YYYY-MM-DD`). Strict PIT lookahead filter |
| `form` | `string` | No | `null` | Filing form filter (`10-K`, `10-Q`, `8-K`) |
| `top_k` | `integer`| No | `10` | Number of ranked results to return |

**Example Request:**
```bash
curl -X GET "http://localhost:8000/search?q=credit%20loss%20provisions&ticker=JPM&as_of_date=2024-03-01&top_k=5"
```

**Response (HTTP 200 OK):**
```json
{
  "query": "credit loss provisions",
  "ticker": "JPM",
  "as_of_date": "2024-03-01",
  "results_count": 1,
  "results": [
    {
      "chunk_id": "chunk_jpm_2023_10k_credit_risk",
      "ticker": "JPM",
      "cik": "0000019617",
      "form": "10-K",
      "filing_date": "2024-02-16",
      "section": "Item 1A",
      "score": 0.8842,
      "text": "JPMorgan Chase & Co. Item 1A. Risk Factors. Credit Risk: The firm's allowance for credit losses was $14.3 billion...",
      "source_url": "https://www.sec.gov/ix?doc=/Archives/edgar/data/19617/000001961724000267/jpm-20231231.htm"
    }
  ]
}
```

---

### 2.2 `POST /qa`
Performs grounded financial question answering with sentence-level citation references, confidence estimation, and negative query abstention.

**Request Body:**
```json
{
  "question": "What was JPMorgan's allowance for credit losses reported in the 2023 10-K before March 2024?",
  "ticker": "JPM",
  "as_of_date": "2024-03-01",
  "max_evidence": 5
}
```

**Response (HTTP 200 OK):**
```json
{
  "answer_text": "JPMorgan Chase & Co. reported an allowance for credit losses of $14.3 billion in its 2023 Form 10-K filed on February 16, 2024 [1]. The firm noted credit risk exposures across commercial real estate and consumer lending portfolios [1].",
  "citations": [
    {
      "citation_id": 1,
      "chunk_id": "chunk_jpm_2023_10k_credit_risk",
      "ticker": "JPM",
      "form": "10-K",
      "filing_date": "2024-02-16",
      "section": "Item 1A",
      "source_url": "https://www.sec.gov/ix?doc=/Archives/edgar/data/19617/000001961724000267/jpm-20231231.htm"
    }
  ],
  "confidence": 0.884,
  "no_evidence": false
}
```

**Abstention Behavior (Out-of-Universe or Negative Query):**
When asked an unsupported query (e.g. `"What was Tesla's commercial aircraft revenue?"`):
```json
{
  "answer_text": "No evidence found in disclosed filings.",
  "citations": [],
  "confidence": 0.0,
  "no_evidence": true
}
```

---

### 2.3 `GET /timeline/{ticker}`
Retrieves the Point-in-Time Knowledge Graph chronological sequence of corporate events, filing disclosures, and XBRL revisions.

**Example Request:**
```bash
curl -X GET "http://localhost:8000/timeline/JPM?start_date=2023-01-01&end_date=2024-03-31"
```

**Response (HTTP 200 OK):**
```json
{
  "ticker": "JPM",
  "events_count": 2,
  "events": [
    {
      "event_id": "jpm_2023_10k",
      "date": "2024-02-16",
      "event_type": "10-K Filing",
      "title": "Annual Report Form 10-K (FY 2023)",
      "summary": "Full year 2023 financial statements, credit risk disclosures ($14.3B allowance), and Item 7 MD&A.",
      "source_url": "https://www.sec.gov/ix?doc=/Archives/edgar/data/19617/000001961724000267/jpm-20231231.htm"
    }
  ]
}
```

---

### 2.4 `GET /impact/{event_id}`
Computes the econometric market impact of a corporate disclosure via OLS Market Model vs. SPY, Cumulative Abnormal Return (CAR), EGARCH volatility bands, and Isolation Forest anomaly flags.

**Example Request:**
```bash
curl -X GET "http://localhost:8000/impact/jpm_2023_10k"
```

**Response (HTTP 200 OK):**
```json
{
  "event_id": "jpm_2023_10k",
  "ticker": "JPM",
  "target_event_date": "2024-02-16",
  "actual_event_date": "2024-02-16",
  "car": 0.0035,
  "t_stat": 0.582,
  "p_value": 0.561,
  "statistically_significant": false,
  "vol_flag": false,
  "isolation_forest_anomaly": false,
  "alpha": 0.00042,
  "beta": 1.145,
  "r_squared": 0.582,
  "timeline_points": [
    {"date": "2024-02-15", "t": -1, "close": 182.1, "abnormal_return": -0.0012, "car": -0.0012},
    {"date": "2024-02-16", "t": 0, "close": 183.8, "abnormal_return": 0.0041, "car": 0.0029},
    {"date": "2024-02-20", "t": 1, "close": 184.2, "abnormal_return": 0.0006, "car": 0.0035}
  ]
}
```

---

### 2.5 `GET /entity/{ticker}`
Retrieves canonical mastered entity symbology from the Entity Registry.

**Example Request:**
```bash
curl -X GET "http://localhost:8000/entity/JPM"
```

**Response (HTTP 200 OK):**
```json
{
  "ticker": "JPM",
  "cik": "0000019617",
  "legal_name": "JPMorgan Chase & Co.",
  "aliases": ["JPMorgan", "J.P. Morgan", "Chase", "JPMorgan Chase"],
  "isin": "US46625H1005",
  "sector": "Financials",
  "industry": "Diversified Banking",
  "wikidata_qid": "Q134149",
  "permid": "4295904307"
}
```
