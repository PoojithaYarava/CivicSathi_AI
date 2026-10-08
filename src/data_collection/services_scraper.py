"""Public-page snapshot and reviewable table extraction utilities."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup

from .source_registry import PROJECT_ROOT, fetch_public_page


def save_public_snapshot(url: str, source_name: str, raw_dir: Path | None = None) -> Path:
    content, retrieved_at = fetch_public_page(url)
    destination = raw_dir or PROJECT_ROOT / "data" / "raw" / "public"
    destination.mkdir(parents=True, exist_ok=True)
    path = destination / f"{source_name}_{date.today().isoformat()}.html"
    path.write_text(content, encoding="utf-8")
    (destination / f"{source_name}_{date.today().isoformat()}.retrieved_at.txt").write_text(retrieved_at, encoding="utf-8")
    return path


def extract_service_rows(html: str, source_url: str) -> pd.DataFrame:
    """Extract table rows as candidates; a human must verify before processed use."""
    soup = BeautifulSoup(html, "lxml")
    records = []
    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            cells = row.find_all(["th", "td"])
            values = [cell.get_text(" ", strip=True) for cell in cells]
            if len(values) < 2:
                continue
            links = [anchor.get("href", "").strip() for anchor in row.find_all("a") if anchor.get("href")]
            records.append({
                "department_candidate": values[-2] if len(values) >= 3 else "",
                "service_candidate": values[-1],
                "row_text": " | ".join(values),
                "linked_url_candidate": links[0] if links else "",
                "source_url": source_url,
                "review_status": "needs_review",
            })
    return pd.DataFrame(records, columns=["department_candidate", "service_candidate", "row_text", "linked_url_candidate", "source_url", "review_status"])


def save_candidates(frame: pd.DataFrame, filename: str, interim_dir: Path | None = None) -> Path:
    destination = interim_dir or PROJECT_ROOT / "data" / "interim"
    destination.mkdir(parents=True, exist_ok=True)
    path = destination / filename
    frame.to_csv(path, index=False, encoding="utf-8-sig")
    return path