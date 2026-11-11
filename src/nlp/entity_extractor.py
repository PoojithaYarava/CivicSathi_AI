"""Catalogue-grounded longest-match entity extraction."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

import pandas as pd

from .preprocessing import normalize_text


def _norm(value: str) -> str:
    return " ".join(normalize_text(value).casefold().split())


class EntityExtractor:
    def __init__(self, data_dir: str | Path = "data/processed"):
        root = Path(data_dir)
        self.entries: list[tuple[str, str, str]] = []
        self._load(root / "service_catalog.csv", "service_name", "SERVICE")
        self._load(root / "service_catalog.csv", "department", "DEPARTMENT")
        self._load(root / "documents_and_forms.csv", "document_name", "DOCUMENT")
        self._load(root / "government_schemes.csv", "scheme_name", "SCHEME")
        # The complete state district directory is an official reference list.
        self._load(root / "telangana_districts.csv", "district", "LOCATION")
        # Locations only come from explicit catalogue fields, not guessed addresses.
        for name in ("service_catalog.csv", "government_schemes.csv", "official_sources.csv"):
            path = root / name
            if path.exists():
                df = pd.read_csv(path, keep_default_na=False)
                for col in ("state", "district"):
                    if col in df:
                        self.entries.extend((str(v), "LOCATION", str(v)) for v in df[col].unique() if str(v).strip())
        complaints = root / "complaint_queries.csv"
        if complaints.exists():
            df = pd.read_csv(complaints, keep_default_na=False)
            if "complaint_category" in df:
                self.entries.extend((str(v), "ISSUE_TYPE", str(v)) for v in df.complaint_category.unique() if str(v).strip())
        dedup = {}
        for surface, kind, canonical in self.entries:
            if surface.strip():
                dedup[(_norm(surface), kind, canonical)] = (surface, kind, canonical)
        self.entries = sorted(dedup.values(), key=lambda row: len(_norm(row[0])), reverse=True)

    def _load(self, path: Path, column: str, kind: str):
        if not path.exists():
            return
        df = pd.read_csv(path, keep_default_na=False)
        if column not in df:
            return
        for value in df[column].unique():
            value = str(value).strip()
            if value:
                self.entries.append((value, kind, value))
                if kind == "SERVICE":
                    # Search aliases are transparent inflections/short forms derived from
                    # official catalogue titles, not invented government names.
                    short = re.sub(r"^(?:online application of|apply online for)\s+", "", value, flags=re.I)
                    if _norm(short) != _norm(value):
                        self.entries.append((short, kind, value))
                    if short.casefold().endswith(" certificate"):
                        self.entries.append((short + "s", kind, value))
                    # Common citizen shorthand for the service titles in the
                    # official catalogue. Keep the canonical title as the match.
                    certificate = re.sub(r"\s+certificate$", "", short, flags=re.I)
                    if certificate != short:
                        self.entries.append((certificate + " cert", kind, value))
                        self.entries.append((certificate + " certificate", kind, value))
                    # A slash in a government catalogue title often lists two
                    # names for the same service (for example domicile/residence).
                    for part in re.split(r"\s*/\s*", value):
                        part = part.strip()
                        if part and _norm(part) != _norm(value):
                            self.entries.append((part, kind, value))
                            if part.casefold().endswith(" certificate"):
                                self.entries.append((re.sub(r"\s+certificate$", " cert", part, flags=re.I), kind, value))

    def extract(self, query: str) -> list[dict]:
        text = normalize_text(query)
        folded = text.casefold()
        results = []
        occupied: list[tuple[int, int]] = []
        # Prefer longest dictionary terms; avoid partial word matches.
        for surface, kind, canonical in self.entries:
            needle = _norm(surface)
            pattern = re.compile(r"(?<!\w)" + re.escape(needle) + r"(?!\w)", re.IGNORECASE)
            for match in pattern.finditer(folded):
                start, end = match.span()
                if any(start < b and end > a for a, b in occupied):
                    continue
                results.append({"text": text[start:end], "type": kind, "canonical_name": canonical,
                                "start": start, "end": end, "method": "catalogue_dictionary",
                                "match_status": "exact_normalized"})
                occupied.append((start, end))
        for match in re.finditer(r"\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}-\d{2}-\d{2})\b", text):
            results.append({"text": match.group(), "type": "DATE", "canonical_name": None,
                            "start": match.start(), "end": match.end(), "method": "regex", "match_status": "pattern"})
        return sorted(results, key=lambda item: (item["start"], -(item["end"] - item["start"])))


def extract_entities(query: str, extractor: EntityExtractor | None = None,
                     data_dir: str | Path = "data/processed") -> list[dict]:
    return (extractor or EntityExtractor(data_dir)).extract(query)
