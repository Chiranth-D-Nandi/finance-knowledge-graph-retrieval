"""End-to-End Validation Smoke Test."""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from api.main import app
from api.state import app_state

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("financial_platform.validate_e2e")


def main() -> None:
    logger.info("Initializing system for live end-to-end validation...")
    if not app_state.is_initialized:
        app_state.initialize()

    client = TestClient(app)

    # 1. Health check
    logger.info("Step 1: Validating GET /health...")
    t0 = time.perf_counter()
    h_resp = client.get("/health")
    h_latency = (time.perf_counter() - t0) * 1000
    assert h_resp.status_code == 200, f"Health check failed: {h_resp.text}"
    h_data = h_resp.json()
    logger.info("Health Status: %s, Docs: %d, Nodes: %d (Latency: %.2fms)", h_data["status"], h_data["index_docs"], h_data["kg_nodes"], h_latency)

    # 2. Hybrid Search
    logger.info("Step 2: Validating GET /search (JPM credit risk before 2024-03-01)...")
    t0 = time.perf_counter()
    s_resp = client.get("/search?q=credit%20risk%20allowance&entity=JPM&before=2024-03-01&limit=5")
    s_latency = (time.perf_counter() - t0) * 1000
    assert s_resp.status_code == 200, f"Search failed: {s_resp.text}"
    s_data = s_resp.json()
    assert len(s_data["results"]) > 0, "No search results returned!"
    logger.info("Search returned %d results (Server latency: %.2fms, Client: %.2fms)", len(s_data["results"]), s_data["latency_ms"], s_latency)

    # 3. Grounded QA
    logger.info("Step 3: Validating POST /qa (Grounded answer with citations)...")
    t0 = time.perf_counter()
    qa_resp = client.post("/qa", json={
        "question": "What did JPMorgan say about credit risk allowance in 2023?",
        "entity": "JPM",
        "before": "2024-03-01",
        "limit": 5,
    })
    qa_latency = (time.perf_counter() - t0) * 1000
    assert qa_resp.status_code == 200, f"QA failed: {qa_resp.text}"
    qa_data = qa_resp.json()
    assert len(qa_data["citations"]) > 0, "No citations in QA response!"
    logger.info("QA generated answer with %d citations, confidence %.2f (Latency: %.2fms)", len(qa_data["citations"]), qa_data["confidence"], qa_latency)

    # 4. Timeline
    logger.info("Step 4: Validating GET /timeline/JPM...")
    t0 = time.perf_counter()
    tl_resp = client.get("/timeline/JPM")
    tl_latency = (time.perf_counter() - t0) * 1000
    assert tl_resp.status_code == 200, f"Timeline failed: {tl_resp.text}"
    tl_data = tl_resp.json()
    assert tl_data["events_count"] > 0, "No timeline events returned!"
    logger.info("Timeline returned %d events (Latency: %.2fms)", tl_data["events_count"], tl_latency)

    # 5. Market Impact
    logger.info("Step 5: Validating GET /impact/filing:JPM:10-K:2024-02-16...")
    t0 = time.perf_counter()
    im_resp = client.get("/impact/filing:JPM:10-K:2024-02-16")
    im_latency = (time.perf_counter() - t0) * 1000
    assert im_resp.status_code == 200, f"Impact failed: {im_resp.text}"
    im_data = im_resp.json()
    assert "car" in im_data, "Missing CAR in impact data!"
    logger.info("Impact computed CAR: %.4f (p=%.3f, Chart points: %d, Latency: %.2fms)", im_data["car"], im_data["p_value"], len(im_data["chart_points"]), im_latency)

    logger.info("ALL END-TO-END VALIDATION GATES PASSED CLEANLY.")


if __name__ == "__main__":
    main()
