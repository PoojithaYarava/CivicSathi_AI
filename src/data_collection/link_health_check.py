"""Rate-limited, manual HEAD checks for public URLs already in the source registry."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import time
from urllib.parse import urlparse

import pandas as pd
import requests


def check_registered_links(registry_path: str | Path = "data/processed/official_sources.csv",
                           limit: int = 10, interval_seconds: float = 1.0,
                           timeout_seconds: float = 8.0, session=None) -> list[dict]:
    if not 1 <= limit <= 100:
        raise ValueError("limit must be from 1 to 100")
    if interval_seconds < 1:
        raise ValueError("interval_seconds must be at least 1 second")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    frame = pd.read_csv(registry_path, keep_default_na=False)
    if not {"source_id", "url"}.issubset(frame.columns):
        raise ValueError("Source registry must contain source_id and url columns")
    unique = frame.drop_duplicates("url").head(limit)
    client = session or requests.Session()
    output = []
    for index, row in enumerate(unique.to_dict(orient="records")):
        url = row["url"]
        parsed = urlparse(url)
        result = {
            "source_id": row["source_id"], "url": url, "domain": parsed.netloc,
            "checked_at": datetime.now(timezone.utc).date().isoformat(),
            "http_status": "", "outcome": "", "interpretation": "Connectivity only; not a verification of official status or content.",
        }
        if parsed.scheme != "https" or not parsed.hostname:
            result["outcome"] = "skipped_non_https_or_invalid"
        else:
            try:
                response = client.head(url, timeout=timeout_seconds, allow_redirects=False,
                                       headers={"User-Agent": "CivicSathi-LinkCheck/1.0 (manual public-source check)"})
                result["http_status"] = str(response.status_code)
                result["outcome"] = "http_response"
            except requests.RequestException as error:
                result["outcome"] = f"connection_error:{type(error).__name__}"
        output.append(result)
        if index + 1 < len(unique):
            time.sleep(interval_seconds)
    return output


def main():
    parser = argparse.ArgumentParser(description="Manually check registered public source URLs with slow HEAD requests.")
    parser.add_argument("--limit", type=int, default=10, help="Maximum unique URLs to check (1-100; default 10)")
    parser.add_argument("--interval", type=float, default=1.0, help="Seconds between checks (minimum 1)")
    parser.add_argument("--timeout", type=float, default=8.0, help="Per-URL timeout in seconds")
    parser.add_argument("--output", default="reports/link_health_check.csv")
    args = parser.parse_args()
    results = check_registered_links(limit=args.limit, interval_seconds=args.interval,
                                     timeout_seconds=args.timeout)
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(results).to_csv(target, index=False, encoding="utf-8-sig")
    print(f"Wrote {len(results)} connectivity results to {target}. HTTP success does not verify source authenticity or content.")


if __name__ == "__main__":
    main()
