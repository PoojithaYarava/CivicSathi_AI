# CivicSathi AI

CivicSathi AI is a multilingual citizen-service information assistant for Hyderabad and Telangana. It is an independent project and is not an official government application.

## Current Phase

**Phase 1: Project Setup & Data Foundation**

**Status: Completed (initial foundation; government details remain subject to source revalidation).**

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

The local repository can be initialized with `git init`. To publish it, create an empty GitHub repository, then add its URL with `git remote add origin <repository-url>` and push the reviewed branch. No GitHub remote or credentials are configured in this workspace.

The source collection helpers only fetch public pages and save raw snapshots/candidate extracts to ignored folders. Review candidate records before placing anything in `data/processed/`. No credentials or API keys are needed.

## Languages

English, Telugu, and Telugu-English code-mixed text are supported. Cleaning preserves Telugu Unicode and does not transliterate code-mixed examples.

## Data Quality

The project validates CSV schemas, identifiers, approved labels, URL formats, provenance registration, text normalization, and common PII-like patterns before synthetic outputs are saved. Review `reports/data_quality_report.md` and run `notebooks/03_data_understanding.ipynb` / `notebooks/04_data_cleaning.ipynb` to inspect current outputs. Listing names are not a substitute for individually verified service, scheme, or form details.

## Notebooks

1. `01_project_setup.ipynb`
2. `02_data_collection.ipynb`
3. `03_data_understanding.ipynb`
4. `04_data_cleaning.ipynb`

## Next Phase

**Phase 2: Multilingual NLP Intent Classification, Entity Extraction & Semantic Retrieval.** No classifier, NER, RAG, embeddings, vector database, chatbot, voice system, web UI, or portal automation is included in this phase.