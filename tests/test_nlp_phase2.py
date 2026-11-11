from pathlib import Path

import numpy as np
import pytest

from src.nlp.entity_extractor import EntityExtractor
from src.nlp.intent_classifier import load_intent_model, predict_intent, SUPPORTED_INTENTS
from src.nlp.pipeline import analyze_citizen_query
from src.nlp.preprocessing import detect_language, normalize_text
from src.nlp.semantic_retrieval import GovernmentRetriever


def test_preprocessing_and_script_detection():
    assert normalize_text("  hello\n  world ") == "hello world"
    assert normalize_text("నాకు ఆదాయ ధృవీకరణ పత్రం కావాలి") == "నాకు ఆదాయ ధృవీకరణ పత్రం కావాలి"
    assert detect_language("income certificate ela apply cheyyali") == "Telugu-English"
    assert detect_language("నాకు income certificate కావాలి") == "Telugu-English"
    assert detect_language("నాకు ఆదాయ ధృవీకరణ పత్రం కావాలి") == "Telugu"
    assert detect_language("!!!") == "Unknown"
    with pytest.raises(TypeError, match="query must be str"):
        normalize_text(None)


def test_model_loads_and_returns_supported_intent():
    model = load_intent_model()
    prediction = predict_intent("How do I apply for income certificate?", model=model)
    assert prediction["label"] in SUPPORTED_INTENTS
    assert 0 <= prediction["confidence"] <= 1
    assert prediction["model_version"] == "civicsathi-intent-v1"


def test_missing_model_and_low_confidence_fallback(tmp_path):
    with pytest.raises(FileNotFoundError, match="Train it with"):
        load_intent_model(tmp_path / "missing.joblib")

    class Uncertain:
        classes_ = np.array(["PAYMENT", "STATUS_CHECK"])
        def predict_proba(self, _):
            return np.array([[0.51, 0.49]])

    result = predict_intent("something", model=Uncertain(), threshold=0.9)
    assert result["label"] is None
    assert result["fallback"] == "low_confidence"


def test_catalogue_entities_longest_and_unknown():
    extractor = EntityExtractor()
    entities = extractor.extract("Please help with Online application of Income certificate")
    service = [x for x in entities if x["type"] == "SERVICE"]
    assert any(x["canonical_name"] == "Online application of Income certificate" for x in service)
    assert not any(x["canonical_name"] == "Certificate" for x in service)
    assert any(x["canonical_name"] == "Form for Income Certificate" for x in extractor.extract("Form for Income Certificate"))
    assert any(x["canonical_name"] == "T-Fiber" for x in extractor.extract("Tell me about T-Fiber"))
    unknown = extractor.extract("Zylarion civic service")
    assert unknown == []


def test_retrieval_keeps_source_fields_and_stable_ids():
    retriever = GovernmentRetriever()
    first = retriever.search("birth certificate application form", top_k=3)
    second = retriever.search("birth certificate application form", top_k=3)
    assert first and first[0]["record_id"] == "DOC0001"
    assert [r["record_id"] for r in first] == [r["record_id"] for r in second]
    assert first[0]["source_url"].startswith("https://")
    assert first[0]["official_url"].startswith("https://")
    no_link = next(r for r in retriever.records if r["record_id"] == "TS0001")
    assert no_link["official_url"] == ""
    assert retriever.search(" \n ") == []


def test_pipeline_schema_and_empty_fallback():
    response = analyze_citizen_query("How do I apply for income certificate?")
    assert set(response) == {"query", "language", "intent", "entities", "results", "warnings"}
    assert response["intent"]["label"] in SUPPORTED_INTENTS
    assert all("source_url" in row and "last_verified" in row for row in response["results"])
    empty = analyze_citizen_query("  ")
    assert empty["intent"]["fallback"] == "empty_query"
    assert empty["results"] == []
