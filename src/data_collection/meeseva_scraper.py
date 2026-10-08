"""Small wrapper for collecting the publicly listed MeeSeva service table."""

from __future__ import annotations

from .services_scraper import extract_service_rows, save_candidates, save_public_snapshot
from .source_registry import load_sources


def collect_meeseva_candidates():
    url = load_sources()["meeseva"]["services"]
    snapshot = save_public_snapshot(url, "meeseva_services")
    html = snapshot.read_text(encoding="utf-8")
    return save_candidates(extract_service_rows(html, url), "meeseva_service_candidates.csv")