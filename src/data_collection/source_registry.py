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
        "https://mgov.telangana.gov.in/faqnew.html": "verified",
        "https://www.ghmc.gov.in/faq_births.aspx": "verified",
        "https://ghmc.gov.in/Birth.aspx": "verified",
        "https://suryapet.telangana.gov.in/service/caste-certificate/": "verified",
        "https://prajavani.cgg.gov.in/": "verified",
        "https://www.ghmc.gov.in/howdoi.aspx": "verified",
        "https://www.ghmc.gov.in/CSC_Applications/General_Grievances.pdf": "verified",
    }
    reviewed_dates = {
        "https://mgov.telangana.gov.in/faqnew.html": "2026-11-10",
        "https://www.ghmc.gov.in/faq_births.aspx": "2026-11-10",
        "https://ghmc.gov.in/Birth.aspx": "2026-11-10",
        "https://suryapet.telangana.gov.in/service/caste-certificate/": "2026-11-10",
        "https://prajavani.cgg.gov.in/": "2026-11-10",
        "https://www.ghmc.gov.in/howdoi.aspx": "2026-11-10",
        "https://www.ghmc.gov.in/CSC_Applications/General_Grievances.pdf": "2026-11-10",
        "https://hyderabad.telangana.gov.in/": "2026-11-10",
    }
    reviewed_descriptions = {
        "https://mgov.telangana.gov.in/faqnew.html": "Government of Telangana MeeSeva FAQ consulted for residence-certificate documents and upload rules.",
        "https://www.ghmc.gov.in/faq_births.aspx": "GHMC FAQ consulted for registered certificate requests, child-name inclusion, and non-availability checklists.",
        "https://ghmc.gov.in/Birth.aspx": "GHMC process page consulted for home-birth and home-death evidence.",
        "https://suryapet.telangana.gov.in/service/caste-certificate/": "District-specific caste-certificate list; do not generalize it to Hyderabad or other districts.",
        "https://prajavani.cgg.gov.in/": "Official Telangana grievance portal linked from Hyderabad District Government; registration flow not automated or independently tested.",
        "https://www.ghmc.gov.in/howdoi.aspx": "GHMC FAQ consulted for municipal grievance routing and status lookup information.",
        "https://www.ghmc.gov.in/CSC_Applications/General_Grievances.pdf": "Official GHMC general-grievance form; fields were reviewed only to describe preparation information.",
        "https://hyderabad.telangana.gov.in/": "Hyderabad District Government page reviewed for its Public Grievance / Prajavani quick link.",
    }
    organizations = {
        "telangana": "Government of Telangana",
        "meeseva": "MeeSeva, Government of Telangana",
        "ghmc": "Greater Hyderabad Municipal Corporation",
        "suryapet": "Suryapet District Government",
    }
    records = []
    for group, entries in config.items():
        for key, url in entries.items():
            records.append({
                "source_id": f"{group}_{key}".lower().replace("-", "_"),
                "organization": organizations.get(group, group.replace("_", " ").title()), "department": "", "service": "",
                "source_type": "Official Portal" if key in {"homepage", "open_data", "databank", "prajavani"} else "Official Form" if key in {"forms", "general_grievance_form"} else "Official Service",
                "url": url, "description": reviewed_descriptions.get(url, "Configured public source; not yet fetched or independently verified."),
                "state": "Telangana" if group != "india" else "India",
                "district": {"hyderabad": "Hyderabad", "suryapet": "Suryapet"}.get(group, ""),
                "verification_status": verified.get(url, "unverified"),
                "last_verified": reviewed_dates.get(url, "2026-10-08" if url in verified else ""),
            })
    return pd.DataFrame(records, columns=SOURCE_COLUMNS)


def fetch_public_page(url: str, timeout: int = 20) -> tuple[str, str]:
    """Fetch public content only; never log in, submit forms, or bypass controls."""
    response = requests.get(url, timeout=timeout, headers={"User-Agent": "CivicSathi-DataFoundation/0.1 (public-source research)"})
    response.raise_for_status()
    return response.text, datetime.now(timezone.utc).isoformat()
