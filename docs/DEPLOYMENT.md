# Deployment, Operations & Production Readiness Guide
## Financial Knowledge Graph & Temporal Retrieval Platform

This guide details the steps to deploy, run, monitor, and maintain the the platform financial intelligence platform in local workstation and production containerized environments.

---

## 1. Hardware & Software Prerequisites

- **Operating System:** Windows 10/11 64-bit or Linux (Ubuntu 22.04 LTS / Debian 12 recommended)
- **CPU:** 8 cores minimum (Intel Core i7/i9 or AMD Ryzen 7/9)
- **RAM:** 16 GB minimum (32 GB recommended)
- **GPU:** NVIDIA GeForce RTX 4060 (8GB VRAM) or higher; RTX 3060/4070/A10/A100 supported
- **CUDA & Drivers:** NVIDIA Driver $\ge 550.x$, CUDA Toolkit 12.1 or 12.4
- **Python:** Python 3.10, 3.11, 3.12, or 3.13
- **Node.js:** Node.js $\ge 18.17.0$ and npm $\ge 9.x$

---

## 2. Environment Setup

### 2.1 Clone Repository & Configure Environment Variables
```bash
git clone <repo-url> fin-nexus
cd fin-nexus

# Copy environment template
cp .env.example .env
```

Edit `.env` to configure your credentials:
```ini
ENVIRONMENT=production
DEBUG=false
HOST=0.0.0.0
PORT=8000
FRONTEND_PORT=3000

# SEC EDGAR Mandatory Compliance Header (Format: Name AdminContact@domain.com)
SEC_USER_AGENT_EMAIL=AnalystUser admin@fin-nexus-ai.internal

# Optional External API Keys
FRED_API_KEY=your_fred_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

### 2.2 Python Dependencies Installation
```bash
# Create and activate virtual environment (optional if using conda)
python -m venv .venv
# Linux / macOS:
source .venv/bin/activate
# Windows PowerShell:
# .venv\Scripts\Activate.ps1

# Install PyTorch with CUDA 12.4
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124

# Install pinned dependencies
pip install -r requirements.txt
```

### 2.3 Frontend Dependencies Installation
```bash
cd frontend
npm install
npm run build
cd ..
```

---

## 3. Data Ingestion & Index Construction

Execute the automated data acquisition and indexing pipeline:

```bash
# 1. Ingest public S&P 50 disclosures and market prices
python scripts/acquire_data.py --tickers JPM,AAPL,MSFT,NVDA,BAC

# 2. Build and persist Lexical, Dense BGE, and Temporal Knowledge Graph indices
python scripts/build_indexes.py
```
This produces persistent Parquet artifacts in `data/processed/`:
- `data/processed/chunks.parquet`
- `data/processed/xbrl_facts.parquet`
- `data/processed/kg_nodes.parquet`
- `data/processed/kg_edges.parquet`

---

## 4. Running the System

### 4.1 Development Mode
**Terminal 1 (FastAPI Backend):**
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 (Next.js 14 Frontend):**
```bash
cd frontend
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

### 4.2 Production Mode
**Terminal 1 (FastAPI Production Worker):**
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 2 --loop uvloop --http httptools
```

**Terminal 2 (Next.js Production Server):**
```bash
cd frontend
npm run start
```

---

## 5. Docker Containerization

the platform includes container configurations for standalone deployment.

### 5.1 Docker Compose Deployment
```bash
docker-compose up --build -d
```
Services spun up:
- `fin-nexus-api`: FastAPI backend running on port 8000 with CUDA GPU passthrough.
- `fin-nexus-frontend`: Optimized Next.js 14 Node server running on port 3000.

---

## 6. System Verification & Healthcheck

### 6.1 API Healthcheck
```bash
curl -s http://localhost:8000/health | jq .
```
Expected output:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "cuda_available": true
}
```

### 6.2 End-to-End Validation Script
Run the automated live smoke verification test:
```bash
python scripts/validate_e2e.py
```
This executes a full synthetic trace across `/health`, `/search`, `/qa`, `/timeline`, and `/impact`.

### 6.3 Automated Test Suite
```bash
pytest -v --cov=src --cov=api
```
All 72 tests in `tests/` must pass.
