# Privacy and Data Governance

## Data classes

- Processed service, scheme, form, and source CSVs contain public catalogue metadata with government source URLs.
- `citizen_queries.csv` and `complaint_queries.csv` contain synthetic examples authored for NLP work; they are not real submissions.
- `service_document_requirements.csv` contains public document requirements, jurisdiction, conditions, and attribution.
- Raw snapshots, intermediate files, downloaded documents, model binaries, databases, logs, and environment secrets are ignored by Git as appropriate.

## User query handling

The local app handles queries in memory. It does not write query history, complaint text, checklists, or checked-item states to disk. The app rejects common patterns for phone, email, Aadhaar-like, PAN-like, OTP-like, and payment-card identifiers before model/retrieval work. This scanner is a best-effort guard, not a guarantee of PII detection. The UI tells users not to enter identifiers, credentials, OTPs, financial details, or private complaint information.

The complaint guidance view does not collect complaint narratives or personal/contact details. The official GHMC form may request information that CivicSathi deliberately does not request; citizens should review the official site's own privacy and form instructions before entering details there.

## Access and publication

The loopback server is for local development. No authentication, multi-user service, external model API, or public deployment is configured. Keep secrets in local environment files; `.env.example` contains placeholders only. Review all Git changes before publication and exclude raw/PII data, model binaries when unsuitable, and downloaded documents.

## Source terms and freshness

The dataset manifest does not claim an external open-data licence where one has not been checked. Respect source terms and preserve attribution. A source being reachable or marked reviewed does not prove all linked information is current. Requirements vary by service, jurisdiction, and case; check the live government page before acting.

## Retention and deletion

The application has no user-query database or retention job because it does not persist user input. To discard local derived state, remove local ignored model binaries/caches using ordinary file management; do not delete source records without reviewing their provenance and Git changes.
