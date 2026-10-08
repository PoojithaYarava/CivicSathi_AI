from pathlib import Path
import json
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data_processing.normalization import clean_text, detect_language, find_sensitive_patterns, normalize_url
from src.data_processing.validation import SCHEMAS, scan_sensitive_text, validate_complaints, validate_queries, validate_source_registry

DATA = ROOT / "data" / "processed"


def load_dataset(filename: str) -> pd.DataFrame:
    return pd.read_csv(DATA / filename, keep_default_na=False)


def test_all_expected_processed_datasets_have_exact_columns():
    for filename, columns in SCHEMAS.items():
        frame = load_dataset(filename)
        assert frame.columns.tolist() == columns


def test_service_ids_and_required_public_fields():
    frame = load_dataset("service_catalog.csv")
    assert frame["service_id"].is_unique
    assert frame["service_name"].str.strip().ne("").all()
    assert frame["department"].str.strip().ne("").all()
    assert frame["source_url"].str.strip().ne("").all()


def test_synthetic_queries_are_unique_annotated_and_valid():
    frame = load_dataset("citizen_queries.csv")
    assert frame["query_id"].is_unique
    assert len(frame) >= 1000
    assert validate_queries(frame) == []


def test_synthetic_complaints_are_unique_annotated_and_valid():
    frame = load_dataset("complaint_queries.csv")
    assert frame["complaint_id"].is_unique
    assert len(frame) >= 500
    assert validate_complaints(frame) == []


def test_source_registry_urls_and_verification_values():
    frame = load_dataset("official_sources.csv")
    assert frame["source_id"].is_unique
    assert frame["verification_status"].isin(["unverified", "verified", "needs_review", "unavailable"]).all()
    assert validate_source_registry(frame) == []
    assert frame["url"].map(lambda value: bool(normalize_url(value))).all()
    registered_urls = set(frame["url"])
    assert set(load_dataset("service_catalog.csv")["source_url"]).issubset(registered_urls)
    schemes = load_dataset("government_schemes.csv")
    forms = load_dataset("documents_and_forms.csv")
    assert set(schemes["source_url"]).issubset(registered_urls)
    assert set(forms["source_url"]).issubset(registered_urls)
    assert set(forms["download_url"]).issubset(registered_urls)


def test_multilingual_normalization_and_privacy_scanner():
    assert clean_text("  income certificate\n ela   apply cheyyali ") == "income certificate ela apply cheyyali"
    assert detect_language("నాకు ఆదాయ ధృవీకరణ పత్రం కావాలి") == "Telugu"
    assert detect_language("income certificate ela apply cheyyali") == "Telugu-English"
    assert detect_language("income certificate దరఖాస్తు") == "Telugu-English"
    assert "email" in find_sensitive_patterns("contact someone@example.com")
    assert "phone" in find_sensitive_patterns("call 9876543210")
    assert "aadhaar_like" in find_sensitive_patterns("Aadhaar 1234 5678 9012")
    assert "pan_like" in find_sensitive_patterns("PAN ABCDE1234F")
    assert "otp_like" in find_sensitive_patterns("OTP: 123456")
    assert "card_like" in find_sensitive_patterns("card 4111 1111 1111 1111")


def test_processed_synthetic_text_has_no_sensitive_pattern_matches():
    for filename in SCHEMAS:
        frame = load_dataset(filename)
        assert scan_sensitive_text(frame, frame.select_dtypes(include=["object", "category"]).columns) == []


def test_notebooks_are_valid_json_with_language_metadata():
    for path in (ROOT / "notebooks").glob("*.ipynb"):
        notebook = json.loads(path.read_text(encoding="utf-8"))
        assert notebook["nbformat"] == 4
        ids = []
        for cell in notebook["cells"]:
            assert cell["metadata"].get("language") in {"markdown", "python"}
            if "id" in cell["metadata"]:
                ids.append(cell["metadata"]["id"])
            if cell["cell_type"] == "code":
                source = cell.get("source", "")
                code = source if isinstance(source, str) else "".join(source)
                compile(code, f"{path.name}:cell", "exec")
        assert len(ids) == len(set(ids))