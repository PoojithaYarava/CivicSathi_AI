"""Source-preserving lexical retrieval over existing government catalogues."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Iterable

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .preprocessing import normalize_text


def _value(row, *keys):
    return next((str(row.get(k, "")).strip() for k in keys if str(row.get(k, "")).strip()), "")


class GovernmentRetriever:
    def __init__(self, data_dir: str | Path = "data/processed", freshness_days: int = 365):
        self.data_dir = Path(data_dir)
        self.freshness_days = freshness_days
        self.records = self._build_records()
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, analyzer="word",
                                          token_pattern=r"(?u)\b\w+\b", strip_accents=None)
        self.matrix = self.vectorizer.fit_transform([r["search_text"] for r in self.records]) if self.records else None

    def _build_records(self):
        records = []
        specs = [
            ("service_catalog.csv", "Service", "service_id", ("service_name",), ("department",), ("description", "eligibility", "required_documents", "application_steps", "category"), ("official_application_url", "official_form_url", "status_tracking_url")),
            ("government_schemes.csv", "Scheme", "scheme_id", ("scheme_name", "scheme_name_telugu"), ("department",), ("description", "eligibility", "benefits", "target_group", "required_documents", "application_process"), ("application_url",)),
            ("documents_and_forms.csv", "Document/Form", "document_id", ("document_name",), ("department",), ("description", "purpose", "document_type", "service_name"), ("download_url",)),
            ("official_sources.csv", "Official Source", "source_id", ("organization", "service"), ("department",), ("description", "source_type", "verification_status"), ("url",)),
        ]
        for filename, kind, id_col, title_cols, dept_cols, desc_cols, official_cols in specs:
            path = self.data_dir / filename
            if not path.exists():
                continue
            df = pd.read_csv(path, keep_default_na=False)
            for i, raw in df.iterrows():
                row = raw.to_dict()
                title = _value(row, *title_cols)
                if not title:
                    continue
                description = " ".join(_value(row, col) for col in desc_cols if _value(row, col))
                official_url = _value(row, *official_cols)
                source_url = _value(row, "source_url", "url")
                last_verified = _value(row, "last_verified")
                verified = _value(row, "verification_status").casefold() == "verified"
                searchable = " ".join([title, _value(row, *dept_cols), description])
                records.append({"record_id": _value(row, id_col) or f"{kind[:3].upper()}-{i+1:04d}",
                                "service_id": _value(row, "service_id") or (_value(row, id_col) if kind == "Service" else ""),
                                "record_type": kind, "title": title, "department": _value(row, *dept_cols),
                                "description": description, "eligibility": _value(row, "eligibility"),
                                "required_documents": _value(row, "required_documents"),
                                "category": _value(row, "category", "document_type", "source_type"),
                                "district": _value(row, "district"), "state": _value(row, "state"),
                                "purpose": _value(row, "purpose"),
                                "official_url": official_url, "source_url": source_url,
                                "last_verified": last_verified, "source_verified": verified,
                                "search_text": normalize_text(searchable)})
        return records

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        text = normalize_text(query)
        if not text or self.matrix is None or top_k < 1:
            return []
        scores = cosine_similarity(self.vectorizer.transform([text]), self.matrix).ravel()
        ranked = sorted(range(len(scores)), key=lambda i: (-scores[i], self.records[i]["record_id"]))
        results = []
        today = date.today()
        for i in ranked:
            if scores[i] <= 0:
                continue
            row = self.records[i]
            result = {k: v for k, v in row.items() if k != "search_text"}
            result["score"] = float(scores[i])
            result["warnings"] = []
            if row["last_verified"]:
                try:
                    verified_date = datetime.strptime(row["last_verified"][:10], "%Y-%m-%d").date()
                    age = (today - verified_date).days
                    if age > self.freshness_days:
                        result["warnings"].append(f"Source was last verified {age} days ago; recheck before relying on current details.")
                except ValueError:
                    result["warnings"].append("Last-verified date is not in a recognized format.")
            else:
                result["warnings"].append("No last-verified date is recorded.")
            if not row["source_verified"]:
                result["warnings"].append("Source record is not marked verified in the source registry.")
            results.append(result)
            if len(results) >= top_k:
                break
        return results


def retrieve(query: str, top_k: int = 5, retriever: GovernmentRetriever | None = None,
             data_dir: str | Path = "data/processed") -> list[dict]:
    return (retriever or GovernmentRetriever(data_dir)).search(query, top_k)
