# Data Dictionary

The exact required column lists are declared in `src/data_processing/validation.py` (`SCHEMAS`). Dataset owner, record count, access class, publication status, provenance, and licence/terms caveats are in `data/dataset_manifest.csv`.

| File | Key contents | Record meaning |
| --- | --- | --- |
| `service_catalog.csv` | `service_id`, service name, department, category, optional process/eligibility/URLs, source and date | Listing-derived public service metadata; blank fields are not requirements. |
| `government_schemes.csv` | `scheme_id`, name, department, target group, optional details/URLs, source and date | Scheme names and links from official listings; many detailed fields are unreviewed/blank. |
| `documents_and_forms.csv` | `document_id`, optional service linkage, name, purpose, type, download/source URLs | Listed form/portal metadata; the target file/link may need review. |
| `official_sources.csv` | `source_id`, owner, type, URL, scope, verification state, date | Registry of official source pages; `verified` means the source page was reviewed, not that every service claim is current. |
| `service_document_requirements.csv` | Requirement ID, service, scenario, jurisdiction, item/type/condition, source and review date | Manually reviewed checklist statements; `item_type` is required, conditional, alternative, prerequisite, or format note. |
| `telangana_districts.csv` | District name, district portal, state directory, review date | All 33 districts and portal links listed in the Government of Telangana district web directory; not evidence of district-specific service coverage. |
| `citizen_queries.csv` | Query ID, query, language, intent, service, department, entities, action | Synthetic, template-authored NLP labels; not real citizen traffic. |
| `complaint_queries.csv` | Complaint ID, query, language, issue/category, optional location, urgency, information/action labels | Synthetic examples for intent/category experiments; not official instructions or citizen complaints. |

IDs are stable within their CSV. The manifest's `record_count` must match the processed file. `source_url` records attribution; `last_verified` records the project's review date, not a government guarantee. Do not add citizen PII to query datasets or source metadata.
