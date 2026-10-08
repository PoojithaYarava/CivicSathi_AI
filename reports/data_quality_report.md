# Data Quality Report

Generated from current processed CSVs. Rows before/after cleaning match because these files are already the cleaned outputs.

| dataset | rows_before_cleaning | rows_after_cleaning | columns | duplicate_rows | missing_values | missing_percentage | unique_ids | categorical_columns |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| citizen_queries.csv | 1296 | 1296 | 9 | 0 | 0 | 0.0 | 1296 | language, intent, service, department, entities, action, source_type |
| complaint_queries.csv | 624 | 624 | 11 | 0 | 624 | 9.09 | 624 | language, complaint_category, issue_type, location, urgency, department, required_information, action, source_type |
| documents_and_forms.csv | 6 | 6 | 12 | 0 | 18 | 25.0 | 6 | document_id, service_id, service_name, document_name, document_type, purpose, mandatory, description, download_url, source_url, department, last_verified |
| government_schemes.csv | 5 | 5 | 15 | 0 | 45 | 60.0 | 5 | scheme_id, scheme_name, scheme_name_telugu, department, target_group, description, eligibility, benefits, required_documents, application_process, application_url, source_url, state, district, last_verified |
| official_sources.csv | 19 | 19 | 11 | 0 | 40 | 19.14 | 19 | source_id, organization, department, service, source_type, url, description, state, district, verification_status, last_verified |
| service_catalog.csv | 23 | 23 | 20 | 0 | 299 | 65.0 | 23 | service_id, service_name, service_name_telugu, department, category, description, eligibility, required_documents, application_steps, application_mode, service_charge, sla, official_application_url, official_form_url, status_tracking_url, complaint_url, state, district, source_url, last_verified |

- Invalid URLs: 0
- Invalid categories/language/intent labels: 0

## Language, Intent, and Complaint Category Distributions

### citizen_queries.csv: language

| language | count |
| --- | --- |
| English | 432 |
| Telugu | 432 |
| Telugu-English | 432 |

### citizen_queries.csv: intent

| intent | count |
| --- | --- |
| SERVICE_DISCOVERY | 108 |
| APPLICATION_PROCEDURE | 108 |
| DOCUMENT_REQUIREMENTS | 108 |
| ELIGIBILITY | 108 |
| FORM_DOWNLOAD | 108 |
| OFFICIAL_LINK | 108 |
| COMPLAINT_REGISTRATION | 108 |
| COMPLAINT_TRACKING | 108 |
| PAYMENT | 108 |
| SCHEME_DISCOVERY | 108 |
| SCHEME_ELIGIBILITY | 108 |
| STATUS_CHECK | 108 |

### complaint_queries.csv: complaint_category

| complaint_category | count |
| --- | --- |
| Street Light | 48 |
| Road Damage | 48 |
| Garbage | 48 |
| Drainage | 48 |
| Water Supply | 48 |
| Water Leakage | 48 |
| Sewage | 48 |
| Illegal Dumping | 48 |
| Public Toilet | 48 |
| Traffic Signal | 48 |
| Stray Animals | 48 |
| Noise Complaint | 48 |
| Other Civic Issue | 48 |

## Data Quality Issues
- Official metadata is limited to names and listing links; unsupported detail fields remain blank.
- Direct form and scheme destinations need individual review.
- Synthetic examples do not represent measured citizen behavior.

## Cleaning Actions
- Synthetic datasets are normalized, deduplicated, validated, and privacy-scanned before saving.
- Telugu Unicode and code-mixed text are preserved.

## Remaining Limitations
- Source pages may change; each service detail and destination link requires its own review.
- TGDeX record-level health/demographic datasets are excluded pending privacy review.
