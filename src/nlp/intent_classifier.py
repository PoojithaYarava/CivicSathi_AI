"""Train, save, load, and query TF-IDF intent-classification baselines."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, classification_report, confusion_matrix,
                             f1_score, precision_score, recall_score)
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.svm import LinearSVC

from .preprocessing import normalize_text

SEED = 42
SUPPORTED_INTENTS = {
    "SERVICE_DISCOVERY", "APPLICATION_PROCEDURE", "DOCUMENT_REQUIREMENTS",
    "ELIGIBILITY", "FORM_DOWNLOAD", "OFFICIAL_LINK", "COMPLAINT_REGISTRATION",
    "COMPLAINT_TRACKING", "PAYMENT", "SCHEME_DISCOVERY", "SCHEME_ELIGIBILITY",
    "STATUS_CHECK",
}
ARTIFACT_DIR = Path("models/nlp")


def _group_key(query: str) -> str:
    """Collapse generated politeness suffix variants before split assignment."""
    value = normalize_text(query).casefold()
    value = re.sub(r"[.!?]+$", "", value)
    value = re.sub(r"^(please help me:\s*|help me:\s*|ଦయచేసి చెప్పండి:\s*)", "", value)
    value = re.sub(r"\s+(please|kindly|thanks|thank you|needs attention|దయచేసి)$", "", value)
    return value


def _pipeline(estimator: Any) -> Pipeline:
    features = FeatureUnion([
        ("word", TfidfVectorizer(ngram_range=(1, 2), strip_accents=None,
                                  sublinear_tf=True, max_features=50000,
                                  token_pattern=r"(?u)\b\w+\b")),
        ("char", TfidfVectorizer(analyzer="char", ngram_range=(2, 5),
                                 sublinear_tf=True, max_features=50000)),
    ])
    return Pipeline([("features", features), ("classifier", estimator)])


def _grouped_splits(frame: pd.DataFrame):
    labels = frame["intent"].to_numpy()
    groups = frame["split_group"].to_numpy()
    outer = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=SEED)
    trainval, test = next(outer.split(frame, labels, groups))
    inner = StratifiedGroupKFold(n_splits=4, shuffle=True, random_state=SEED + 1)
    train_rel, val_rel = next(inner.split(frame.iloc[trainval], labels[trainval], groups[trainval]))
    train = trainval[train_rel]
    validation = trainval[val_rel]
    return train, validation, test


def evaluate_predictions(y_true, y_pred, labels) -> dict[str, Any]:
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_precision": float(precision_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)),
        "macro_recall": float(recall_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)),
        "macro_f1": float(f1_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)),
        "weighted_f1": float(f1_score(y_true, y_pred, labels=labels, average="weighted", zero_division=0)),
        "per_class": classification_report(y_true, y_pred, labels=labels, output_dict=True, zero_division=0),
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=labels).tolist(),
    }


def train_and_evaluate(data_path: str | Path = "data/processed/citizen_queries.csv",
                       artifact_dir: str | Path = ARTIFACT_DIR) -> dict[str, Any]:
    path, out_dir = Path(data_path), Path(artifact_dir)
    if not path.exists():
        raise FileNotFoundError(f"Citizen query dataset not found: {path}")
    frame = pd.read_csv(path, keep_default_na=False)
    required = {"query", "language", "intent", "source_type"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"{path} missing required columns: {sorted(missing)}")
    frame["query"] = frame["query"].map(normalize_text)
    invalid_labels = sorted(set(frame["intent"]) - SUPPORTED_INTENTS)
    if invalid_labels:
        raise ValueError(f"Unsupported or missing intent labels in {path}: {invalid_labels}")
    empty_query_count = int((frame["query"] == "").sum())
    frame = frame[frame["query"] != ""].copy()
    if frame.empty:
        raise ValueError("No non-empty rows with supported intent labels")
    if (frame.source_type != "synthetic_annotated").any():
        raise ValueError("Training is restricted to explicitly annotated/synthetic records")
    if frame.groupby("query")["intent"].nunique().gt(1).any():
        raise ValueError("Conflicting labels found for duplicate normalized queries")
    frame["split_group"] = frame["query"].map(_group_key)
    # Synthetic data only; suspicious PII patterns are excluded without exposing values.
    pii = frame["query"].str.contains(r"(?i)(?:\b\d{10,12}\b|\b[A-Z]{5}\d{4}[A-Z]\b|\b[^\s@]+@[^\s@]+\.[^\s@]+)", regex=True)
    dropped_pii = int(pii.sum())
    frame = frame.loc[~pii].copy()
    labels = sorted(frame.intent.unique())
    train_idx, val_idx, test_idx = _grouped_splits(frame)
    x = frame["query"].to_numpy()
    y = frame["intent"].to_numpy()
    models = {
        "logistic_regression": _pipeline(LogisticRegression(max_iter=3000, class_weight="balanced", random_state=SEED)),
        "linear_svm": _pipeline(CalibratedClassifierCV(LinearSVC(class_weight="balanced", random_state=SEED), cv=3, method="sigmoid")),
    }
    validation = {}
    for name, model in models.items():
        model.fit(x[train_idx], y[train_idx])
        validation[name] = evaluate_predictions(y[val_idx], model.predict(x[val_idx]), labels)
    winner = max(models, key=lambda name: validation[name]["macro_f1"])
    # Lock selection on validation, then refit once on train+validation and evaluate test once.
    chosen = models[winner]
    fit_idx = sorted([*train_idx.tolist(), *val_idx.tolist()])
    chosen.fit(x[fit_idx], y[fit_idx])
    test_pred = chosen.predict(x[test_idx])
    metrics = evaluate_predictions(y[test_idx], test_pred, labels)
    by_language = {}
    for language in sorted(frame.language.unique()):
        mask = frame.iloc[test_idx].language.to_numpy() == language
        if int(mask.sum()) >= 5:
            by_language[language] = {
                "n": int(mask.sum()),
                "accuracy": float(accuracy_score(y[test_idx][mask], test_pred[mask])),
                "macro_f1": float(f1_score(y[test_idx][mask], test_pred[mask], labels=labels, average="macro", zero_division=0)),
            }
    out_dir.mkdir(parents=True, exist_ok=True)
    artifact = out_dir / "intent_classifier.joblib"
    joblib.dump(chosen, artifact)
    import hashlib
    fingerprint = hashlib.sha256(path.read_bytes()).hexdigest()
    metadata = {
        "model_version": "civicsathi-intent-v1",
        "selected_model": winner,
        "labels": labels,
        "decision_threshold": 0.35,
        "random_seed": SEED,
        "dataset_path": str(path),
        "dataset_sha256": fingerprint,
        "dataset_rows": int(len(frame)),
        "dropped_empty_queries": empty_query_count,
        "dropped_pii_suspects": dropped_pii,
        "split_rows": {"train": len(train_idx), "validation": len(val_idx), "test": len(test_idx)},
        "validation": {name: {k: v for k, v in m.items() if k not in {"per_class", "confusion_matrix"}} for name, m in validation.items()},
        "test": metrics,
        "per_language_test": by_language,
    }
    (out_dir / "intent_metrics.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / "intent_config.json").write_text(json.dumps({k: v for k, v in metadata.items() if k not in {"test", "validation", "per_language_test"}}, indent=2), encoding="utf-8")
    return metadata


def load_intent_model(model_path: str | Path = ARTIFACT_DIR / "intent_classifier.joblib"):
    path = Path(model_path)
    if not path.exists():
        raise FileNotFoundError(f"Intent model artifact not found: {path}. Train it with python -m src.nlp.train")
    return joblib.load(path)


def predict_intent(query: str, model=None, model_path: str | Path = ARTIFACT_DIR / "intent_classifier.joblib",
                   threshold: float = 0.35) -> dict[str, Any]:
    original = query
    normalized = normalize_text(query)
    if not normalized:
        return {"query": original, "label": None, "confidence": None, "alternatives": [], "model_version": "civicsathi-intent-v1", "fallback": "empty_query"}
    clf = model if model is not None else load_intent_model(model_path)
    probs = clf.predict_proba([normalized])[0]
    classes = clf.classes_
    order = probs.argsort()[::-1]
    confidence = float(probs[order[0]])
    fallback = "low_confidence" if confidence < threshold else None
    return {
        "query": original,
        "label": None if fallback else str(classes[order[0]]),
        "confidence": confidence,
        "alternatives": [{"label": str(classes[i]), "score": float(probs[i])} for i in order[1:4]],
        "model_version": "civicsathi-intent-v1",
        "fallback": fallback,
    }
