# NLP Pipeline

1. Normalize Unicode and whitespace without transliteration.
2. Detect language with script and romanized-Telugu heuristics. This is not an independently validated language-ID model.
3. Reject queries matching common sensitive-data patterns.
4. Predict one of the 12 trained intent labels using the saved TF-IDF Logistic Regression artifact; low confidence returns fallback.
5. Extract longest dictionary matches grounded in catalogue fields and supported date patterns.
6. Rank service, scheme, form, and source rows by TF-IDF cosine similarity.
7. Attach a document checklist only when a matched service and its scope allow it.
8. Assemble a template/extractive summary with source metadata and uncertainty notes.

For contextual follow-up, the browser may send an active service ID from the current tab. The server resolves that ID against its service catalogue and uses it to augment retrieval while preserving the original user query. Context is cleared when the citizen starts a new search. No conversation text is stored server-side.

Model metrics are in `models/nlp/intent_metrics.json` and their synthetic-data caveats are in `docs/model_evaluation.md` and `reports/nlp_evaluation_report.md`.
