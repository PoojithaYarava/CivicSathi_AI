"""Official source registry and conservative retrieval helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_COLUMNS = [
    "source_id", "organization", "department", "service", "source_type", "url",
    "description", "state", "district", "verification_status", "last_verified",
]


def load_sources(config_path: Path | None = None) -> dict:
    path = config_path or PROJECT_ROOT / "config" / "sources.yaml"
    with path.open(encoding="utf-8") as stream:
        return yaml.safe_load(stream)


def flatten_sources(config: dict) -> pd.DataFrame:
    verified = {
        "https://www.telangana.gov.in/": "verified",
        "https://www.telangana.gov.in/services/state-services/": "verified",
        "https://www.telangana.gov.in/services/public-utility-forms/": "verified",
        "https://www.telangana.gov.in/services/central-services/": "verified",
        "https://ts.meeseva.telangana.gov.in/TSDeptPortal/UserInterface/Services.html": "verified",
        "https://hyderabad.telangana.gov.in/": "verified",
        "https://data.gov.in/": "verified",
        "https://tgdex.telangana.gov.in/data-bank": "needs_review",
    }
    records = []
    for group, entries in config.items():
        for key, url in entries.items():
            records.append({
                "source_id": f"{group}_{key}".lower().replace("-", "_"),
                "organization": group.replace("_", " ").title(), "department": "", "service": "",
                "source_type": "Official Portal" if key in {"homepage", "open_data", "databank"} else "Official Form" if key == "forms" else "Official Service",
                "url": url, "description": "Configured public source; not yet fetched or independently verified.",
                "state": "Telangana" if group != "india" else "India",
                "district": "Hyderabad" if group == "hyderabad" else "",
                "verification_status": verified.get(url, "unverified"),
                "last_verified": "2026-10-08" if url in verified else "",
            })
    return pd.DataFrame(records, columns=SOURCE_COLUMNS)


def fetch_public_page(url: str, timeout: int = 20) -> tuple[str, str]:
    """Fetch public content only; never log in, submit forms, or bypass controls."""
    response = requests.get(url, timeout=timeout, headers={"User-Agent": "CivicSathi-DataFoundation/0.1 (public-source research)"})
    response.raise_for_status()
    return response.text, datetime.now(timezone.utc).isoformat()