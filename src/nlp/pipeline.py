"""End-to-end orchestration for classification, entities, and retrieval."""

from __future__ import annotations

from pathlib import Path

from .entity_extractor import EntityExtractor
from .intent_classifier import predict_intent
from .preprocessing import detect_language, normalize_text
from .semantic_retrieval import GovernmentRetriever


def analyze_citizen_query(query: str, model=None, data_dir: str | Path = "data/processed",
                          model_path: str | Path = "models/nlp/intent_classifier.joblib",
                          top_k: int = 5) -> dict:
    normalized = normalize_text(query)
    language = detect_language(normalized)
    warnings = []
    if not normalized:
        return {"query": query, "language": language,
                "intent": {"label": None, "confidence": None, "fallback": "empty_query"},
                "entities": [], "results": [], "warnings": ["Please provide a non-empty query."]}
    intent = predict_intent(normalized, model=model, model_path=model_path)
    if intent["fallback"]:
        warnings.append("Intent is below the confidence threshold; check the query or collect reviewed examples.")
    entities = EntityExtractor(data_dir).extract(normalized)
    retriever = GovernmentRetriever(data_dir)
    results = retriever.search(normalized, top_k=top_k)
    if not results:
        warnings.append("No matching catalogue record was found. Consult the official source registry.")
    for record in results:
        warnings.extend(record.get("warnings", []))
    return {"query": query, "language": language,
            "intent": {"label": intent["label"], "confidence": intent["confidence"],
                       "alternatives": intent["alternatives"], "fallback": intent["fallback"],
                       "model_version": intent["model_version"]},
            "entities": entities, "results": results, "warnings": list(dict.fromkeys(warnings))}
