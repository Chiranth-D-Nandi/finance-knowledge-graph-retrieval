# Interactive Demonstration Guide & Workflows
## Financial Knowledge Graph & Temporal Retrieval Platform

Welcome to the the platform Financial Intelligence Terminal demonstration walkthrough. This document guides evaluators, hiring managers, and quantitative researchers through the 4 core workflows and presents 10 curated test queries.

---

## 1. UI Overview & Workspace Aesthetics

The the platform frontend (`http://localhost:3000`) is styled according to the **Institutional Market Terminal (Bloomberg / Refinitiv style)** design language:
- **Base Canvas:** Deep institutional navy (`#0a1628` / `#0f1f38`).
- **Accent & Highlights:** High-contrast quantitative teal (`#00d4aa`).
- **Typography:** JetBrains Mono for numbers, identifiers, and tickers; Inter for prose disclosures.
- **Header Telemetry:** Live GPU device indicator, VRAM usage monitor, active model status, and sub-150ms search latency gauge.

---

## 2. Walkthrough of the 4 Core Workflows

### Workflow 1: Hybrid Multi-Stage Financial Retrieval
1. Navigate to the **Search** tab in the top navigation bar.
2. In the query box, enter:
   ```text
   What are JPMorgan's credit risk disclosures and loan loss provisions?
   ```
3. Set the **Point-in-Time Cutoff** to `2024-03-01`.
4. Click **Search Disclosures**.
5. **Observed System Execution:**
   - The *Hybrid Entity Linker* detects `"JPMorgan"` and maps it to canonical ticker `JPM` and `CIK 0000019617`.
   - The *Temporal Candidate Filter* restricts search candidate documents to filings accepted on or before March 1, 2024.
   - Dual candidate channels (BM25 lexical + BGE-base dense vectors) retrieve top-100 candidates.
   - *Reciprocal Rank Fusion (RRF, k=60)* combines rankings.
   - *Cross-Encoder (`ms-marco-MiniLM-L6-v2`)* reranks top candidates with full attention, outputting sigmoid-calibrated relevance scores.
   - The top result displays JPMorgan's 2023 10-K Item 1A Risk Factors with direct SEC EDGAR accession URL.

---

### Workflow 2: Grounded QA with Sentence-Level Citations & Abstention
1. Select the **Grounded QA** tab.
2. Enter the prompt:
   ```text
   What was JPMorgan's allowance for credit losses reported in the 2023 10-K before March 2024?
   ```
3. Click **Ask Assistant**.
4. **Observed Output:**
   - The model generates an exact factual synthesis:
     > *"JPMorgan Chase & Co. reported an allowance for credit losses of $14.3 billion in its 2023 Form 10-K filed on February 16, 2024 [1]. The firm noted credit risk exposures across commercial real estate and consumer lending portfolios [1]."*
   - Every sentence is bound to citation badge `[1]`.
   - Clicking citation `[1]` scrolls directly to the verified SEC excerpt and opens the official SEC EDGAR accession document.
   - Calibrated Confidence Score: `88.4%`.
5. **Abstention Demonstration (Zero-Hallucination Invariant):**
   - In the query box, ask an unsupported or fictitious query:
     ```text
     What were Tesla's commercial aircraft deliveries in 2023?
     ```
   - **Result:** The system strictly refuses to extrapolate or hallucinate, outputting:
     > *"No evidence found in disclosed filings."* (Confidence: 0.0%, Citations: []).

---

### Workflow 3: Point-in-Time Knowledge Graph Timeline
1. Select the **Timeline** tab.
2. Select target ticker **`JPM`** (or `AAPL`, `MSFT`, `NVDA`, `BAC`).
3. Set date window from `2023-01-01` to `2024-03-31`.
4. **Observed Visual Graph:**
   - An interactive chronological tree renders filing nodes (`10-K`, `10-Q`, `8-K`) connected to XBRL financial fact nodes.
   - Demonstrates strict point-in-time state: filings submitted after March 2024 (such as the Q1 10-Q in May 2024) are completely absent from the graph, preventing temporal leakage.

---

### Workflow 4: Econometric Market Impact & Event Study Analytics
1. Select the **Market Impact** tab.
2. Select event: **`JPM 2023 10-K Filing (2024-02-16)`**.
3. **Observed Quantitative Analytics:**
   - **Cumulative Abnormal Return (CAR):** Interactive chart displaying abnormal returns over event window $t \in [-1, +10]$ days relative to S&P 500 benchmark (`SPY`).
   - **OLS Estimation Statistics:** $\alpha = 0.00042$, $\beta = 1.145$, $R^2 = 0.582$.
   - **Hypothesis Test:** $CAR[-1, +10] = +0.35\%$, $t$-stat $= 0.582$, $p$-value $= 0.561$ (labeled *"Not Statistically Significant"* at $\alpha=0.05$).
   - **Volatility Envelope:** EGARCH(1,1) conditional volatility bands with Isolation Forest microstructure anomaly flag (`Normal`).

---

## 3. Curated 10 Seed Evaluation Questions

| # | Benchmark Category | Query Text | Target Ticker | PIT As-Of Date | Expected Answer / Behavior |
| :-: | :--- | :--- | :---: | :---: | :--- |
| **1** | Credit Risk Disclosures | "What was JPMorgan's allowance for credit losses in 2023?" | JPM | 2024-03-01 | $14.3 Billion [1] |
| **2** | Supply Chain Risks | "How does Apple manage manufacturing concentration in China?" | AAPL | 2024-03-01 | Outsourced assembly risks in Item 1A [1] |
| **3** | AI Revenue Streams | "What cloud revenue growth did Microsoft attribute to Copilot in late 2023?" | MSFT | 2024-03-01 | Azure cloud AI services growth [1] |
| **4** | Semiconductor Demand | "Why did Nvidia's Compute & Networking segment revenue surge in FY2024?" | NVDA | 2024-03-01 | H100 GPU hyperscaler demand [1] |
| **5** | Net Interest Yields | "How did Bank of America describe deposit repricing pressures?" | BAC | 2024-03-01 | Higher interest rate environment costs [1] |
| **6** | Temporal Lookahead Test | "What did JPMorgan disclose in its Q1 2024 10-Q?" (As of 2024-03-01) | JPM | 2024-03-01 | **Abstain** (Q1 filed May 2024) |
| **7** | Out-of-Corpus Negative | "What was Amazon's lunar mining capital expenditure in 2023?" | AMZN | 2024-03-01 | **Abstain** ("No evidence found") |
| **8** | Segment Disclosures | "What are Nvidia's two primary reportable business segments?" | NVDA | 2024-03-01 | Compute & Networking, Graphics [1] |
| **9** | Regulatory Compliance | "What anti-money laundering investigations did major US banks disclose?" | JPM | 2024-03-01 | Item 1A / Legal Proceedings [1] |
| **10**| Event Study Verification | "Did the 2023 10-K filing produce significant abnormal return for JPM?" | JPM | 2024-03-01 | CAR = +0.35%, $p=0.561$ (Not Sig) |
