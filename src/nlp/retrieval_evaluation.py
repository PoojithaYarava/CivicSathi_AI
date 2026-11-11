"""Evaluate lexical catalogue retrieval against reviewed record-ID judgments."""

from __future__ import annotations

import csv
from pathlib import Path

from .semantic_retrieval import GovernmentRetriever


def evaluate_retrieval(judgments_path="reports/retrieval_judgments.csv", data_dir="data/processed"):
    retriever = GovernmentRetriever(data_dir)
    rows = list(csv.DictReader(Path(judgments_path).open(encoding="utf-8-sig", newline="")))
    if not rows:
        raise ValueError("Retrieval judgments file is empty")
    record_ids = {record["record_id"] for record in retriever.records}
    output = []
    for row in rows:
        relevant = set(filter(None, row["relevant_record_ids"].split(";")))
        unknown = relevant - record_ids
        if unknown:
            raise ValueError(f"Judgment references unknown record IDs: {sorted(unknown)}")
        hits = [record["record_id"] for record in retriever.search(row["query"], top_k=5)]
        rank = next((index + 1 for index, item in enumerate(hits) if item in relevant), None)
        output.append({"query": row["query"], "language": row["language"], "relevant": relevant,
                       "hits": hits, "rank": rank})
    metrics = {}
    for k in (1, 3, 5):
        metrics[f"recall@{k}"] = sum(any(hit in r["relevant"] for hit in r["hits"][:k]) for r in output) / len(output)
    metrics["mrr"] = sum((1 / r["rank"]) if r["rank"] else 0 for r in output) / len(output)
    metrics["n_queries"] = len(output)
    metrics["by_language"] = {
        language: {"n_queries": sum(r["language"] == language for r in output),
                   "recall@3": sum(any(h in r["relevant"] for h in r["hits"][:3]) for r in output if r["language"] == language)
                   / sum(r["language"] == language for r in output)}
        for language in sorted({r["language"] for r in output})
    }
    return metrics, output


if __name__ == "__main__":
    import json
    scores, _ = evaluate_retrieval()
    print(json.dumps(scores, indent=2))
