"""SEC EDGAR Data Fetcher with strict Fair Access Compliance (<= 10 req/s, User-Agent header)."""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import httpx

from src.config import settings

logger = logging.getLogger("fin_nexus.sec_fetcher")


class SECFetcher:
    """
    Client for SEC EDGAR API respecting SEC Fair Access policy:
    - User-Agent header in format: 'Sample Company Name AdminContact@<sample company domain>.com'
    - Request rate strictly throttled to <= 10 req/sec (default 5 req/sec for safety)
    - Full retry logic with exponential backoff on HTTP 429
    """

    def __init__(
        self,
        user_agent_email: Optional[str] = None,
        requests_per_second: float = 5.0,
        output_dir: Optional[Path] = None,
    ):
        self.email = user_agent_email or settings.SEC_USER_AGENT_EMAIL
        self.headers = {
            "User-Agent": f"FinNexus Research Platform ({self.email})",
            "Accept-Encoding": "gzip, deflate",
            "Host": "data.sec.gov",
        }
        self.sec_files_headers = {
            "User-Agent": f"FinNexus Research Platform ({self.email})",
            "Accept-Encoding": "gzip, deflate",
        }
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = 0.0
        self.output_dir = output_dir or settings.EDGAR_RAW_DIR
        self.submissions_dir = self.output_dir / "submissions"
        self.filings_dir = self.output_dir / "filings"
        self.xbrl_dir = self.output_dir / "xbrl"

        self.submissions_dir.mkdir(parents=True, exist_ok=True)
        self.filings_dir.mkdir(parents=True, exist_ok=True)
        self.xbrl_dir.mkdir(parents=True, exist_ok=True)

    def _throttle(self) -> None:
        """Enforce rate limit interval between outgoing requests."""
        now = time.time()
        elapsed = now - self.last_request_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request_time = time.time()

    def _get(self, url: str, headers: Optional[Dict[str, str]] = None, max_retries: int = 3) -> httpx.Response:
        """Execute HTTP GET with throttling and retry backoff on 429 / network errors."""
        req_headers = headers or self.headers
        for attempt in range(1, max_retries + 1):
            self._throttle()
            timestamp = datetime.now(timezone.utc).isoformat()
            try:
                with httpx.Client(timeout=30.0, follow_redirects=True) as client:
                    resp = client.get(url, headers=req_headers)
                    logger.info("SEC GET: %s [HTTP %d] at %s", url, resp.status_code, timestamp)
                    if resp.status_code == 200:
                        return resp
                    elif resp.status_code == 429:
                        wait = attempt * 3.0
                        logger.warning("SEC 429 Rate Limit hit. Backing off %f seconds...", wait)
                        time.sleep(wait)
                    else:
                        resp.raise_for_status()
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                logger.warning("Attempt %d failed for %s: %s", attempt, url, str(e))
                if attempt == max_retries:
                    raise
                time.sleep(attempt * 2.0)
        raise RuntimeError(f"Failed to fetch {url} after {max_retries} retries")

    def fetch_company_tickers(self) -> Dict[str, Any]:
        """Fetch canonical SEC company_tickers.json mapping (CIK to Ticker)."""
        url = "https://www.sec.gov/files/company_tickers.json"
        target_path = self.output_dir / "company_tickers.json"
        resp = self._get(url, headers={"User-Agent": f"FinNexus ({self.email})", "Host": "www.sec.gov"})
        data = resp.json()
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return data

    def fetch_submissions(self, cik: str) -> Dict[str, Any]:
        """Fetch SEC submissions metadata for a 10-digit padded CIK."""
        cik_10 = cik.strip().zfill(10)
        target_path = self.submissions_dir / f"CIK{cik_10}.json"
        if target_path.exists():
            with open(target_path, "r", encoding="utf-8") as f:
                return json.load(f)

        url = f"https://data.sec.gov/submissions/CIK{cik_10}.json"
        resp = self._get(url)
        data = resp.json()
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return data

    def fetch_xbrl_companyfacts(self, cik: str) -> Dict[str, Any]:
        """Fetch structured XBRL facts JSON for a given CIK."""
        cik_10 = cik.strip().zfill(10)
        target_path = self.xbrl_dir / f"CIK{cik_10}.json"
        if target_path.exists():
            with open(target_path, "r", encoding="utf-8") as f:
                return json.load(f)

        url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik_10}.json"
        resp = self._get(url)
        data = resp.json()
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return data

    def fetch_filing_document(
        self,
        cik: str,
        ticker: str,
        form: str,
        filing_date: str,
        accession_number: str,
        primary_doc_name: str,
    ) -> Path:
        """Download raw filing HTML document from SEC EDGAR archive."""
        cik_clean = str(int(cik.strip()))  # Archive paths use unpadded CIK
        acc_no_dashes = accession_number.replace("-", "")
        url = f"https://www.sec.gov/Archives/edgar/data/{cik_clean}/{acc_no_dashes}/{primary_doc_name}"

        ticker_dir = self.filings_dir / ticker.upper()
        ticker_dir.mkdir(parents=True, exist_ok=True)
        safe_form = form.replace("/", "-")
        target_file = ticker_dir / f"{safe_form}_{filing_date}_{acc_no_dashes}.html"

        if target_file.exists() and target_file.stat().st_size > 500:
            return target_file

        resp = self._get(
            url,
            headers={
                "User-Agent": f"FinNexus Research Platform ({self.email})",
                "Host": "www.sec.gov",
                "Accept-Encoding": "gzip, deflate",
            },
        )
        content = resp.text
        with open(target_file, "w", encoding="utf-8", errors="replace") as f:
            f.write(content)
        return target_file
