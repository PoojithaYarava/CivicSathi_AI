"""Officially sourced, scenario-aware document checklists."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = {
    "requirement_id", "service_id", "service_name", "scenario", "jurisdiction",
    "requirement", "item_type", "condition", "source_url", "source_title",
    "source_last_updated", "last_verified", "evidence_notes",
}


class DocumentRequirements:
    """Loads reviewed checklist rows and groups them by service and scenario."""

    def __init__(self, data_dir: str | Path = "data/processed"):
        path = Path(data_dir) / "service_document_requirements.csv"
        self.rows: list[dict] = []
        if not path.exists():
            return
        frame = pd.read_csv(path, keep_default_na=False)
        missing = REQUIRED_COLUMNS - set(frame.columns)
        if missing:
            raise ValueError(f"{path} is missing columns: {sorted(missing)}")
        self.rows = frame.to_dict(orient="records")

    def for_services(self, service_ids: list[str], query: str = "") -> list[dict]:
        wanted = set(service_ids)
        q = query.casefold()
        grouped: dict[tuple, list[dict]] = {}
        for row in self.rows:
            if row["service_id"] not in wanted:
                continue
            jurisdiction = row["jurisdiction"]
            # Never present the Suryapet-specific caste list as a Hyderabad checklist.
            if jurisdiction == "Suryapet District only" and "suryapet" not in q:
                continue
            key = (row["service_id"], row["service_name"], row["scenario"], jurisdiction,
                   row["source_url"], row["source_title"], row["source_last_updated"], row["last_verified"])
            grouped.setdefault(key, []).append({
                "text": row["requirement"], "type": row["item_type"],
                "condition": row["condition"], "evidence_notes": row["evidence_notes"],
            })
        checklists = []
        for key, items in grouped.items():
            service_id, service_name, scenario, jurisdiction, source_url, source_title, source_updated, verified = key
            checklists.append({
                "service_id": service_id, "service_name": service_name,
                "scenario": scenario, "jurisdiction": jurisdiction,
                "items": items, "source_url": source_url,
                "source_title": source_title, "source_last_updated": source_updated,
                "last_verified": verified,
                "notice": "Official source checklist; requirements can vary by case. Confirm the live service Requirements before visiting.",
            })
        return checklists
