# CivicSathi AI

CivicSathi AI is a multilingual citizen-service information assistant for all 33 districts of Telangana. It is an independent project and is not an official government application.

## Current Phase

**End-to-end local MVP: data foundation, multilingual NLP, grounded lookup, and read-only web app**

**Status: Implemented locally.** Phase 1 and Phase 2 are complete; a source-grounded response layer and browser interface complete the usable MVP. It is an independent project, not a government application.

The repository establishes source provenance, multilingual-safe cleaning, privacy checks, and synthetic NLP examples. It includes service names/departments and scheme/form names or links explicitly visible on government listing pages. Unknown eligibility, fees, steps, benefits, and active status remain empty; destination links are marked `needs_review` until assessed individually.

## Data Governance

The project follows **public government information + synthetic/annotated NLP data + zero real citizen PII**. It does not intentionally collect personal citizen data, access authenticated portals, submit applications or complaints, make payments, bypass CAPTCHA, or store credentials. Never add Aadhaar/PAN, phone, email, OTP, financial, exact-address, or private complaint data.

Raw snapshots go under `data/raw/public/`; external research inputs go under `data/raw/external/`; temporary extraction files go under `data/interim/`. All are ignored by Git. Processed CSVs are UTF-8 with exact, documented schemas. Downloaded documents are excluded from Git; prefer metadata and official links.

## Sources

Configured official starting points are in `config/sources.yaml`. The source registry records the source type and verification state. As checked on 2026-10-08, Telangana state services, forms and central services pages, the Telangana home page, MeeSeva, Hyderabad District, and data.gov.in pages were accessible. Service names/departments and listed form/scheme links were transcribed from those pages; this does not verify destination links, service details, or current activity. TGDeX is marked `needs_review`: its bank describes health and demographic record-level data, which this project must not download without a privacy review.

## Dataset Structure

- `service_catalog.csv`: 23 service names/departments observed on the state listing; details and direct application URLs are blank pending verification.
- `citizen_queries.csv`: 1,296 deterministic synthetic examples across English, Telugu and Telugu-English, labeled `synthetic_annotated`.
- `complaint_queries.csv`: 624 synthetic civic complaint examples, with location deliberately blank.
- `government_schemes.csv`: 5 scheme names and links listed by Hyderabad District; scheme details are blank pending page review.
- `documents_and_forms.csv`: 6 form/portal names and links listed by Telangana; links are not downloaded and destinations remain under review.
- `official_sources.csv`: configured source URLs and observed listing links with review status.
- `service_document_requirements.csv`: scenario-specific document checklist entries transcribed from official MeeSeva/GHMC/district pages, with jurisdiction, conditions, and verification dates. It covers researched services only; a missing checklist means CivicSathi has not verified the requirements.
- `data/dataset_manifest.csv`: record counts, data owner, provenance, access/publication state, and unassessed licence/terms notes for every processed dataset.

Every government-derived record must preserve `source_url` and `last_verified`; manually written information must never be presented as official. The synthetic language distribution is balanced by construction, not an estimate of citizen behavior.

## Setup

Use Python 3.11 or later. Create and activate an environment, then install dependencies:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Build the initial CSV package and run checks:

```powershell
python -m src.data_processing.build_datasets
pytest
```

The `origin` remote points to the CivicSathi GitHub repository. Review changes on `main` before publishing updates.

The source collection helpers only fetch public pages and save raw snapshots/candidate extracts to ignored folders. Review candidate records before placing anything in `data/processed/`. No credentials or API keys are needed.

## Languages

Queries may be entered in English, Telugu, or Telugu-English code-mixed text. Cleaning preserves Telugu Unicode and does not transliterate. The UI offers English, Telugu, or bilingual guidance. Official record titles, document names, and quoted source data remain in the language published by the government so translations are not misrepresented as official text. Language identification is heuristic; Telugu and code-mixed quality has not been independently evaluated by native speakers.

The district directory and location selector include all 33 districts from the Government of Telangana district directory. This is geographic navigation, not a claim that every service or document checklist has been researched for every district. Local checklist coverage remains explicitly limited to the official records available in `service_document_requirements.csv`.

## Data Quality

The project validates CSV schemas, identifiers, approved labels, URL formats, provenance registration, text normalization, and common PII-like patterns before synthetic outputs are saved. Review `reports/data_quality_report.md` and run `notebooks/03_data_understanding.ipynb` / `notebooks/04_data_cleaning.ipynb` to inspect current outputs. Listing names are not a substitute for individually verified service, scheme, or form details.

## Phase 2 NLP

The `src/nlp/` package includes Unicode-safe normalization and script heuristics, two TF-IDF classification baselines (word and character features), catalogue-grounded dictionary entities, a TF-IDF retrieval baseline, and an orchestration function. The actual Phase 1 schemas are mapped explicitly. No embedding model, trained NER model, RAG, chatbot, or government transaction feature is included.

Train and evaluate the classifier, build its local artifact, evaluate the small reviewed retrieval set, run tests, and try the integrated pipeline:

```powershell
python -m src.nlp.train
python -m src.nlp.retrieval_evaluation
pytest
python -c "from src.nlp.pipeline import analyze_citizen_query; print(analyze_citizen_query('income certificate ela apply cheyyali'))"
```

Use the project virtual environment interpreter for these commands if `python` or `pytest` resolves outside it. The classifier joblib file is stored under `models/nlp/` and ignored by Git; JSON configuration and evaluation metrics are retained. See [the Phase 2 evaluation report](reports/nlp_evaluation_report.md) and `notebooks/05`–`08` for inspection and plots.

The held-out score is perfect on the generated dataset. This is a narrow template-based evaluation, not evidence of production performance. The dataset has limited linguistic diversity and no independent real-citizen evaluation. Telugu-script and code-mixed quality needs review by fluent speakers. Dictionary entity coverage is limited by blank Telugu catalogue names. Retrieval is lexical only, and catalogue descriptions and direct application links are often missing or unverified.

## Local Application

Homepage tagline: **Government services, made easier to understand.**

The read-only browser app searches and browses services, schemes, and forms; shows source URLs and review warnings; and displays reviewed, scenario-specific checklists where available. It also provides editable complaint drafts with official GHMC and Telangana grievance links, plus a personal task dashboard saved only in browser local storage after the citizen chooses Save. Active service context lasts only in the current tab. The complaint view does not submit or track grievances; the task dashboard does not track live government application status. Optional browser speech recognition may process audio externally; Telugu-English accuracy is not verified. The answer is an extractive/template summary, not an LLM answer. Sensitive-pattern matches are rejected before intent classification or retrieval. Requests are handled in memory only; no query history is written. The development server binds to loopback only.

Read-only local API routes are available at `/api/health`, `/api/services`, `/api/schemes`, `/api/documents`, `/api/sources`, `/api/search?q=...`, and `/api/complaints`; query analysis accepts `POST /api/query` (also `/api/analyze`). Complaint draft analysis accepts `POST /api/complaints/draft` or `/api/complaints/analyze` and returns an unsent draft. Browse endpoints accept optional `q`, `department`, `category`, `district`, and `limit` filters where those fields exist in the catalogue. There is intentionally no server-side task API or government submission route.

Build the Phase 1 data if needed, train the local model, then start CivicSathi:

```powershell
python -m src.data_processing.build_datasets
python -m src.nlp.train
python -m src.app.server
```

Open `http://127.0.0.1:8000`. Stop the server with `Ctrl+C`. The first two commands are required after cloning because processed datasets and the binary model artifact are local and are not committed. A clean setup and evaluation commands are in the sections above.

This MVP does not include generated natural-language advice, multilingual embeddings, an unattended source-crawling/update service, a hosted production deployment, account login, complaint/application submission, payment, or status lookup. Optional browser speech-to-text and text-to-speech are implemented in the UI; recognition may send audio outside the device, depends on the selected locale/browser service, and Telugu-English code-mix is best effort. There is no local speech model. Data gaps and source freshness remain visible and must be resolved before relying on a record.

## Architecture and Governance

See [architecture](docs/project_architecture.md), [system flow](docs/system_flow.md), [data dictionary](docs/data_dictionary.md), [privacy and data governance](docs/privacy_and_data_governance.md), and [model evaluation](docs/model_evaluation.md).

Additional feature/API notes are in [complaint assistant](docs/complaint_assistant.md), [task tracking](docs/task_tracking.md), [voice processing](docs/voice_processing.md), [service and scheme discovery](docs/service_and_scheme_discovery.md), [document management](docs/document_management.md), [NLP pipeline](docs/nlp_pipeline.md), [API documentation](docs/api_documentation.md), and [deployment](docs/deployment.md).

## Tests

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest -q
```

The suite covers data schemas, manifest counts, multilingual normalization, classifier fallback, dictionary matching, retrieval provenance, browse and complaint API routes, query handling, and sensitive-input rejection.

## Notebooks

1. `01_project_setup.ipynb`
2. `02_data_collection.ipynb`
3. `03_data_understanding.ipynb`
4. `04_data_cleaning.ipynb`
5. `05_nlp_preprocessing.ipynb`
6. `06_intent_classification.ipynb`
7. `07_entity_extraction.ipynb`
8. `08_semantic_retrieval.ipynb`

## Project Boundary

The local project is complete as a privacy-preserving information lookup MVP. A production RAG/LLM service or hosted public deployment would require independently reviewed multilingual quality data, verified and maintained government records, an explicit hosting/privacy design, and a separate deployment decision. These are not silently enabled by the local application.
