# CivicSathi AI Phase 2 NLP Evaluation

**Evaluation date:** 2026-10-09
**Status:** Baselines trained and evaluated; limitations below are material.

## Data inspected

All six processed Phase 1 CSVs were inspected. The citizen query table contains 1,296 rows and the actual fields `query_id, query, language, intent, service, department, entities, action, source_type`. All rows are marked `synthetic_annotated`; there are 12 supported intents with 108 examples each, and 432 examples each for English, Telugu, and Telugu-English. No empty query/intent labels, exact duplicate query strings, or PII-pattern matches were found by the training check. The data file SHA-256 is recorded in `models/nlp/intent_metrics.json`.

The source catalogues contain 23 services, 5 schemes, 6 forms, and 19 official-source records. Many description, eligibility, direct application URL, and Telugu-name fields are blank. The original processed datasets were not modified.

## Preprocessing and language handling

`src/nlp/preprocessing.py` applies NFC Unicode normalization, whitespace cleanup, and conservative zero-width/BOM removal. It preserves punctuation and Telugu script. Language detection is a lightweight script/romanized-Telugu heuristic; annotated labels are authoritative for model evaluation. It is not a standalone validated language-identification model.

Suspicious PII patterns are counted and excluded from classifier training; matched content is never logged. No rows matched in the inspected synthetic set. This simple scanner is not a guarantee that all personal data will be detected.

## Intent classification

Twelve observed labels were used. A deterministic grouped split (seed 42) produced 777 train, 260 validation, and 259 test records. Generated politeness variants are grouped by removing common English and Telugu prefixes/suffixes before splitting. Feature extraction combines word 1–2 grams and character 2–5 grams. Logistic Regression and sigmoid-calibrated Linear SVM were compared on validation macro F1; both scored 1.000, and Logistic Regression was selected by deterministic tie order. The final pipeline was refit on train plus validation once and evaluated on the held-out test set.

| Metric | Test result |
|---|---:|
| Accuracy | 1.000 |
| Macro precision | 1.000 |
| Macro recall | 1.000 |
| Macro F1 | 1.000 |
| Weighted F1 | 1.000 |

Macro F1 weights each class equally and is useful when class counts differ. This dataset is balanced, so it does not test how well the model handles rare intents. Every intent had test support of 21 or 22 and per-class precision, recall, and F1 of 1.000. The confusion matrix has only diagonal counts (21–22 per class); see `intent_confusion_matrix.csv` and the plot `intent_confusion_matrix.png`.

| Annotated language | Test rows | Accuracy | Macro F1 |
|---|---:|---:|---:|
| English | 88 | 1.000 | 1.000 |
| Telugu | 84 | 1.000 | 1.000 |
| Telugu-English | 87 | 1.000 | 1.000 |

These scores are not evidence of broad multilingual performance: the query data is synthetic, mechanically balanced, and follows repeated intent-specific templates. Grouping known suffix/prefix variants reduces direct leakage, but does not create independent human phrasing. There are no real citizen queries or fluent-speaker judgments. Confidence values are Logistic Regression probability estimates; calibration quality has not been evaluated. A 0.35 threshold is a conservative engineering fallback, not a validated operating point. Low-confidence queries return no intent label.

## Entity extraction

The extractor performs normalized exact dictionary matches from the actual service, document/form, scheme, department, location, and annotated complaint-category columns. Longest terms take precedence over overlapping shorter matches. Date patterns are returned as regex matches. No aliases were added unless grounded in a catalogue field. No gold span annotations exist, so entity precision/recall/F1 are not reported. Unit tests verify grounding and overlap behavior; this is not a trained NER model. Empty Telugu catalogue names limit Telugu entity coverage, and transliteration variants and ambiguous locations remain unsupported.

## Retrieval

The current retriever maps 62 records (23 services, 5 schemes, 6 forms, and 28 official sources) and applies a word-level TF-IDF cosine baseline. Each result retains its record ID, type, title, department, description, official URL (blank when absent), source URL, verification date, score, and freshness/source-status warnings. Identifiers are stable when present in source rows. No embedding model was downloaded or evaluated, so embedding-based retrieval is **not implemented**. Earlier versions of this report used an older source-record count.

Eight manually authored English query-to-record judgments are in `retrieval_judgments.csv`. On this small set, Recall@1, Recall@3, Recall@5, and MRR are all 1.000. This is a smoke evaluation authored against known catalogue titles, not an independent or multilingual benchmark; no Telugu or code-mixed judgments are available. URL presence does not establish that a service is active or its information current.

## Example behavior

- `income certificate ela apply cheyyali` → `APPLICATION_PROCEDURE` (probability estimate 0.868); retrieves the existing income certificate service record and preserves its source URL.
- `Where can I download the birth certificate form?` → `FORM_DOWNLOAD` (0.901); dictionary matching identifies `Birth Certificate` and retrieval returns records with their source metadata.
- `weather forecast for tomorrow` → no intent label (0.128, below threshold). The lexical retriever can still produce weak nonzero catalogue matches; consumers should inspect scores and warnings and must not treat every result as relevant.

## End-to-end local application

`src/app/server.py` serves a browser interface and JSON endpoint using Python's standard library. The application loads the classifier and catalogue indexes once at startup, binds to loopback, and handles each request in memory. Sensitive-pattern matches are rejected before classification and retrieval. The application does not log query bodies or keep a query history. Responses use a small extractive/template assembler over retrieved source fields; they do not use an LLM or invent missing eligibility, steps, or document requirements. The interface labels lexical scores, exposes source links, and warns users to confirm current details. This is a usable local lookup MVP, not a hosted production service or free-form RAG answer generator.

The added `service_document_requirements.csv` stores scenario-aware official checklists with source URLs, applicability, conditional/alternative labels, and review dates. Current reviewed coverage includes GHMC birth/death copy requests, child-name inclusion and non-availability cases; Telangana MeeSeva residence certificates; and a clearly Suryapet-only caste-certificate list. GHMC's registered-copy process is distinct from new registration and non-availability; the UI presents those paths separately. Suryapet requirements are shown only when the query explicitly names Suryapet. Other services return an explicit "not verified here" notice. Primary pages: [GHMC birth/death FAQ](https://www.ghmc.gov.in/faq_births.aspx), [GHMC home-event process](https://ghmc.gov.in/Birth.aspx), [Telangana MeeSeva FAQ](https://mgov.telangana.gov.in/faqnew.html), and [Suryapet caste-certificate page](https://suryapet.telangana.gov.in/service/caste-certificate/).

## Reproduction

```powershell
python -m pip install -r requirements.txt
python -m src.nlp.train
python -m src.nlp.retrieval_evaluation
pytest
jupyter notebook
python -m src.app.server
```

The local trained artifact is `models/nlp/intent_classifier.joblib` (ignored by Git). Model metadata, split sizes, class/language metrics, confusion matrix, random seed, and dataset fingerprint are saved as JSON/CSV. Run `analyze_citizen_query` from `src.nlp.pipeline` for an end-to-end result. With multiple Python installations, run through the same virtual environment used to install requirements.

## Next work and limits

Collect independently reviewed, privacy-safe intent examples and native-speaker annotations; validate performance on unseen phrasing and real language variation; add reviewed multilingual retrieval judgments; fill catalogue detail only from verified sources; and evaluate multilingual embeddings only after confirming supported languages, license, and availability. Phase 3 RAG, answer generation, application submission, and chatbot/UI work are outside this implementation.
