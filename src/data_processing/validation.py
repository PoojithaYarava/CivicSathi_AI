"""Dataset schemas and validation rules for the Phase 1 data package."""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

from .normalization import find_sensitive_patterns, normalize_url

VALID_LANGUAGES = ["English", "Telugu", "Telugu-English", "Unknown"]
VALID_INTENTS = ["SERVICE_DISCOVERY", "APPLICATION_PROCEDURE", "DOCUMENT_REQUIREMENTS", "ELIGIBILITY", "FORM_DOWNLOAD", "OFFICIAL_LINK", "COMPLAINT_REGISTRATION", "COMPLAINT_TRACKING", "PAYMENT", "SCHEME_DISCOVERY", "SCHEME_ELIGIBILITY", "STATUS_CHECK"]
VALID_COMPLAINT_CATEGORIES = ["Street Light", "Road Damage", "Garbage", "Drainage", "Water Supply", "Water Leakage", "Sewage", "Illegal Dumping", "Public Toilet", "Traffic Signal", "Stray Animals", "Noise Complaint", "Other Civic Issue"]
VALID_SOURCE_TYPES = ["Official Service", "Official Form", "Official Scheme", "Official Document", "Official Portal", "Official Dataset"]
VALID_VERIFICATION_STATUSES = ["unverified", "verified", "needs_review", "unavailable"]

SCHEMAS = {
    "service_catalog.csv": ["service_id", "service_name", "service_name_telugu", "department", "category", "description", "eligibility", "required_documents", "application_steps", "application_mode", "service_charge", "sla", "official_application_url", "official_form_url", "status_tracking_url", "complaint_url", "state", "district", "source_url", "last_verified"],
    "citizen_queries.csv": ["query_id", "query", "language", "intent", "service", "department", "entities", "action", "source_type"],
    "complaint_queries.csv": ["complaint_id", "query", "language", "complaint_category", "issue_type", "location", "urgency", "department", "required_information", "action", "source_type"],
    "government_schemes.csv": ["scheme_id", "scheme_name", "scheme_name_telugu", "department", "target_group", "description", "eligibility", "benefits", "required_documents", "application_process", "application_url", "source_url", "state", "district", "last_verified"],
    "documents_and_forms.csv": ["document_id", "service_id", "service_name", "document_name", "document_type", "purpose", "mandatory", "description", "download_url", "source_url", "department", "last_verified"],
    "official_sources.csv": ["source_id", "organization", "department", "service", "source_type", "url", "description", "state", "district", "verification_status", "last_verified"],
}


def validate_unique_nonempty(frame: pd.DataFrame, id_column: str, required: Iterable[str]) -> list[str]:
    errors = []
    if id_column not in frame:
        return [f"Missing required column: {id_column}"]
    if frame[id_column].isna().any() or frame[id_column].astype(str).str.strip().eq("").any():
        errors.append(f"{id_column} contains empty values")
    if frame[id_column].duplicated().any():
        errors.append(f"{id_column} contains duplicates")
    for column in required:
        if column not in frame:
            errors.append(f"Missing required column: {column}")
        elif frame[column].isna().any() or frame[column].astype(str).str.strip().eq("").any():
            errors.append(f"{column} contains empty values")
    return errors


def validate_queries(frame: pd.DataFrame) -> list[str]:
    errors = validate_unique_nonempty(frame, "query_id", ["query"])
    if "language" in frame and not frame["language"].isin(VALID_LANGUAGES).all():
        errors.append("language contains unsupported values")
    if "intent" in frame and not frame["intent"].isin(VALID_INTENTS).all():
        errors.append("intent contains unsupported values")
    if "source_type" in frame and not frame["source_type"].eq("synthetic_annotated").all():
        errors.append("synthetic query records must use source_type=synthetic_annotated")
    return errors


def validate_complaints(frame: pd.DataFrame) -> list[str]:
    errors = validate_unique_nonempty(frame, "complaint_id", ["query"])
    if "language" in frame and not frame["language"].isin(VALID_LANGUAGES).all():
        errors.append("language contains unsupported values")
    if "complaint_category" in frame and not frame["complaint_category"].isin(VALID_COMPLAINT_CATEGORIES).all():
        errors.append("complaint_category contains unsupported values")
    if "action" in frame and not frame["action"].eq("raise_complaint").all():
        errors.append("action contains unsupported values")
    if "source_type" in frame and not frame["source_type"].eq("synthetic_annotated").all():
        errors.append("synthetic complaint records must use source_type=synthetic_annotated")
    return errors


def validate_urls(frame: pd.DataFrame, column: str) -> list[str]:
    if column not in frame:
        return [f"Missing URL column: {column}"]
    invalid = [value for value in frame[column].dropna() if str(value).strip() and not normalize_url(value)]
    return [f"{len(invalid)} invalid URL(s) in {column}"] if invalid else []


def validate_source_registry(frame: pd.DataFrame) -> list[str]:
    errors = validate_unique_nonempty(frame, "source_id", ["url"])
    errors.extend(validate_urls(frame, "url"))
    if "source_type" in frame and not frame["source_type"].isin(VALID_SOURCE_TYPES).all():
        errors.append("source_type contains unsupported values")
    if "verification_status" in frame and not frame["verification_status"].isin(VALID_VERIFICATION_STATUSES).all():
        errors.append("verification_status contains unsupported values")
    return errors


def scan_sensitive_text(frame: pd.DataFrame, text_columns: Iterable[str]) -> list[tuple[int, str, list[str]]]:
    findings = []
    for column in text_columns:
        if column not in frame:
            continue
        for index, value in frame[column].items():
            patterns = find_sensitive_patterns(value)
            if patterns:
                findings.append((index, column, patterns))
    return findings