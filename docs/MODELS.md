# Model Cards, Hyperparameters & Inference Specifications
## Financial Knowledge Graph & Temporal Retrieval Platform

This document catalogs every machine learning and deep learning model integrated into the platform, including model provenance, architecture, hyperparameters, precision, loss functions, and runtime constraints.

---

## 1. Dense Embedding Model: BAAI/bge-base-en-v1.5

- **HuggingFace Hub ID:** `BAAI/bge-base-en-v1.5`
- **Architecture:** 12-layer, 768-hidden dimension BERT-based bi-encoder
- **Parameter Count:** 109M parameters
- **License:** Apache 2.0
- **Primary Function:** Dense passage and query representation for semantic financial retrieval.

### Hyperparameters & Invariants
- **Max Sequence Length:** 512 tokens
- **Pooling Strategy:** `[CLS]` token pooling followed by $L_2$ vector normalization
- **Query Instruction Prefix:**
  ```
  Represent this sentence for searching relevant passages: 
  ```
  *(Passages are encoded raw without prefix, per BGE author specifications)*
- **Similarity Metric:** Dot product over normalized vectors (equivalent to Cosine Similarity bounded in $[-1.0, 1.0]$)
- **Runtime Precision:** fp16 under `torch.inference_mode()`
- **VRAM Footprint:** ~880 MiB allocated, ~1.42 GB peak during batch encoding.

---

## 2. Cross-Encoder Reranker: cross-encoder/ms-marco-MiniLM-L6-v2

- **HuggingFace Hub ID:** `cross-encoder/ms-marco-MiniLM-L6-v2`
- **Architecture:** 6-layer, 384-hidden dimension MiniLM cross-encoder
- **Parameter Count:** 22.7M parameters
- **License:** Apache 2.0
- **Primary Function:** Deep cross-attention reranking of fused candidate passages.

### Cross-Attention Mechanism
Unlike bi-encoders which project queries and passages into independent vector spaces, the cross-encoder feeds the concatenation `[CLS] query [SEP] passage [SEP]` into all transformer layers simultaneously:
$$\text{Logit}(q, d) = \mathbf{W} \cdot \text{Transformer}(\text{Concat}(q, d))_{[\text{CLS}]}$$
The raw logit is passed through a logistic sigmoid function:
$$\text{Score}(q, d) = \frac{1}{1 + e^{-\text{Logit}(q, d)}} \in [0.0, 1.0]$$
- **Runtime Precision:** fp16 on CUDA device 0.
- **VRAM Footprint:** ~540 MiB allocated, ~980 MiB peak for batch size 16.

---

## 3. Financial Sentiment Model: ProsusAI/finbert

- **HuggingFace Hub ID:** `ProsusAI/finbert`
- **Architecture:** 12-layer BERT-base model fine-tuned on Financial PhraseBank
- **Parameter Count:** 110M parameters
- **License:** Apache 2.0
- **Output Classes:** `positive`, `negative`, `neutral` (softmax probability distribution)
- **Fallback Architecture:** When running in low-resource CPU mode, `src/processing/sentiment.py` seamlessly falls back to a high-speed Loughran-McDonald financial dictionary sentiment parser.

---

## 4. Grounded Generative LLM: Qwen2.5-3B-Instruct

- **HuggingFace Hub ID:** `Qwen/Qwen2.5-3B-Instruct`
- **Architecture:** Dense auto-regressive transformer with RoPE, SwiGLU, and Grouped Query Attention (GQA)
- **Parameter Count:** 3.09 Billion parameters
- **Quantization:** 4-bit AWQ / GGUF (consumes ~2.1 GB VRAM)
- **Context Window:** Up to 32,768 tokens (configured for 4,096 tokens in this deployment)

### Strict Grounded Prompt Contract
The prompt template enforces zero-hallucination citation bounds:
```text
<|im_start|>system
You are an institutional quantitative research analyst.
Answer the question using ONLY the retrieved financial evidence below.
Rules:
1. Every claim must cite the evidence source [1], [2], etc.
2. If the answer cannot be determined strictly from the evidence, state:
   "No evidence found in disclosed filings."
3. Never use external knowledge or invent numbers.
4. Output structured JSON with keys: "answer_text", "citations", "confidence".
<|im_end|>
```

---

## 5. Econometric & Statistical Time-Series Models

### 5.1 Market Model Ordinary Least Squares (OLS)
- **Equation:** $R_{i,t} = \alpha_i + \beta_i R_{m,t} + \epsilon_{i,t}$
- **Benchmark ($R_m$):** S&P 500 ETF (`SPY`) daily log returns
- **Estimation Window:** $T \in [-250, -30]$ trading days relative to filing date $t=0$
- **Event Window:** $\tau \in [-1, +10]$ trading days
- **Abnormal Return:** $AR_{i,\tau} = R_{i,\tau} - (\hat{\alpha}_i + \hat{\beta}_i R_{m,\tau})$
- **Cumulative Abnormal Return (CAR):**
  $$CAR[-1, +10] = \sum_{\tau=-1}^{10} AR_{i,\tau}, \quad \text{Var}(CAR) = \sigma_\epsilon^2 \sum (1 + \dots)$$
- **Hypothesis Test:** $H_0: CAR = 0$ via two-tailed $t$-statistic and p-value.

### 5.2 Exponential GARCH: EGARCH(1,1)
- **Library:** `arch` package (`arch_model`)
- **Specification:** $p=1, o=1, q=1$ with Student's $t$ distributed errors:
  $$\ln(\sigma_t^2) = \omega + \beta \ln(\sigma_{t-1}^2) + \alpha \left(\left|\frac{\epsilon_{t-1}}{\sigma_{t-1}}\right| - \sqrt{\frac{2}{\pi}}\right) + \gamma \frac{\epsilon_{t-1}}{\sigma_{t-1}}$$
- **Purpose:** Captures volatility clustering and asymmetric leverage effects (market declines increase volatility more than gains).
- **Volatility Anomaly Flag:** Triggered when actual post-event volatility exceeds $2.5\times$ conditional volatility $\sigma_t$.

### 5.3 Isolation Forest Anomaly Detection
- **Library:** `scikit-learn` (`sklearn.ensemble.IsolationForest`)
- **Features:** Normalized volume ratio, daily return deviation, and bid-ask proxy spread.
- **Contamination:** 0.05.
- **Purpose:** Identifies abnormal market microstructure behavior on filing day.
