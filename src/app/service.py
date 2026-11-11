"""In-memory application service; requests are never persisted."""

from __future__ import annotations

from pathlib import Path
import re
from datetime import date, datetime
from urllib.parse import urlparse

import pandas as pd

from src.nlp.entity_extractor import EntityExtractor
from src.nlp.intent_classifier import ARTIFACT_DIR, load_intent_model, predict_intent
from src.nlp.preprocessing import detect_language, normalize_text
from src.nlp.semantic_retrieval import GovernmentRetriever
from src.nlp.document_requirements import DocumentRequirements
from src.data_processing.normalization import find_sensitive_patterns


class CivicSathiService:
    """Loads the NLP components once and returns source-grounded summaries."""

    def __init__(self, data_dir: str | Path = "data/processed",
                 model_path: str | Path = ARTIFACT_DIR / "intent_classifier.joblib",
                 minimum_match_score: float = 0.22):
        self.model = load_intent_model(model_path)
        self.entities = EntityExtractor(data_dir)
        self.retriever = GovernmentRetriever(data_dir)
        self.document_requirements = DocumentRequirements(data_dir)
        self.minimum_match_score = minimum_match_score
        self.data_dir = Path(data_dir)

    def browse_catalogue(self, record_type: str, query: str = "", department: str = "",
                         category: str = "", district: str = "", limit: int = 100) -> list[dict]:
        """Return a filtered, read-only view of records already in the catalogues."""
        allowed = {"Service", "Scheme", "Document/Form"}
        if record_type not in allowed:
            raise ValueError("Unsupported catalogue type")
        limit = max(1, min(int(limit), 100))
        if query.strip():
            candidates = self.retriever.search(query, top_k=max(100, limit))
        else:
            candidates = []
            for row in self.retriever.records:
                item = {key: value for key, value in row.items() if key != "search_text"}
                item["score"] = None
                item["warnings"] = []
                if not item.get("source_verified"):
                    item["warnings"].append("Source record is not marked verified in the source registry.")
                if not item.get("last_verified"):
                    item["warnings"].append("No last-verified date is recorded.")
                candidates.append(item)
        filtered = []
        for row in candidates:
            if row["record_type"] != record_type:
                continue
            if department and department.casefold() not in row.get("department", "").casefold():
                continue
            if category and category.casefold() not in row.get("category", "").casefold() \
                    and category.casefold() not in row.get("title", "").casefold():
                continue
            if district:
                # Keep explicitly scoped district rows and state-level catalogue rows;
                # do not turn missing district metadata into a local claim.
                record_district = row.get("district", "")
                if record_district and district.casefold() not in record_district.casefold():
                    continue
                if not record_district and row.get("state", "").casefold() not in {"telangana", "india"}:
                    continue
            filtered.append(row)
            if len(filtered) >= limit:
                break
        return filtered

    def complaint_guidance(self) -> dict:
        """Return source-backed complaint routing without collecting complaint content."""
        return {
            "disclaimer": "CivicSathi does not register, send, or track complaints. Use the official channel directly.",
            "issue_categories": [
                "Street light", "Road damage", "Garbage", "Drainage", "Water supply",
                "Water leakage", "Sewage", "Illegal dumping", "Public toilet",
                "Traffic signal", "Stray animals", "Noise complaint", "Other civic issue",
            ],
            "category_note": "These are example labels from CivicSathi's synthetic query dataset; the official portal may use different categories.",
            "preparation": [
                "Describe the issue briefly and factually.",
                "Note the location and a nearby landmark. The GHMC general grievance form asks for complaint nature and exact location; an assessment number may apply to property-related cases.",
                "Do not enter personal details in CivicSathi. The official channel may ask for contact information; provide it only on the official government service if required.",
            ],
            "channels": [
                {
                    "name": "GHMC grievance service",
                    "applies_to": "Civic issues within GHMC limits; confirm which local body serves your address.",
                    "url": "https://ghmc.gov.in/",
                    "action": "Open the official GHMC website and choose Lodge Grievance / e-Complaints.",
                    "source_url": "https://www.ghmc.gov.in/howdoi.aspx",
                    "source_title": "GHMC grievance FAQs and official portal",
                },
                {
                    "name": "Telangana Prajavani",
                    "applies_to": "Telangana's public grievance system; choose the relevant state, district, revenue division, or mandal level on the official portal.",
                    "url": "https://prajavani.cgg.gov.in/",
                    "action": "Review the current portal instructions. It provides registration and grievance-status features; CivicSathi does not submit or track requests.",
                    "source_url": "https://prajavani.cgg.gov.in/",
                    "source_title": "Prajavani Government of Telangana",
                },
            ],
            "form_source": {
                "url": "https://www.ghmc.gov.in/CSC_Applications/General_Grievances.pdf",
                "title": "GHMC Application Form for General Grievances",
            },
            "status_note": "CivicSathi cannot check a grievance status. Use the reference number and status facility provided by the official channel.",
        }

    def get_catalogue_record(self, record_type: str, record_id: str) -> dict | None:
        for row in self.retriever.records:
            if row["record_type"] == record_type and row["record_id"].casefold() == record_id.casefold():
                return {key: value for key, value in row.items() if key != "search_text"}
        return None

    def source_directory(self) -> list[dict]:
        path = self.data_dir / "official_sources.csv"
        if not path.exists():
            return []
        today = date.today()
        output = []
        for row in pd.read_csv(path, keep_default_na=False).to_dict(orient="records"):
            raw_status = row.get("verification_status", "unverified").casefold()
            status_map = {
                "verified": "verified",
                "unverified": "not_yet_verified",
                "needs_review": "manual_review_required",
                "unavailable": "unavailable",
            }
            status = status_map.get(raw_status, "not_yet_verified")
            last_checked = row.get("last_verified", "")
            if status == "verified" and last_checked:
                try:
                    checked = datetime.strptime(last_checked[:10], "%Y-%m-%d").date()
                    if (today - checked).days > self.retriever.freshness_days:
                        status = "verification_overdue"
                except ValueError:
                    status = "manual_review_required"
            parsed = urlparse(row.get("url", ""))
            output.append({
                **row,
                "domain": parsed.netloc,
                "verification_status_display": status,
                "verification_basis": row.get("description", ""),
            })
        return output

    def analyze_complaint(self, query: str) -> dict:
        """Prepare an editable complaint draft using conservative issue-keyword matches."""
        normalized = normalize_text(query)
        if not normalized:
            raise ValueError("Enter a brief civic issue description first.")
        if find_sensitive_patterns(normalized):
            raise ValueError("This description may contain sensitive information. Remove personal identifiers and try again.")
        text = normalized.casefold()
        patterns = [
            ("Street Light", ("street light", "streetlight", "street lights", "streetlights", "light not working")),
            ("Road Damage", ("road damage", "damaged road", "broken road", "pothole", "potholes")),
            ("Garbage", ("garbage", "trash", "waste collection", "waste not collected")),
            ("Drainage", ("drainage", "drain overflow", "storm drain")),
            ("Water Supply", ("water supply", "no water", "water shortage")),
            ("Water Leakage", ("water leak", "water leakage", "pipe burst", "leaking pipe")),
            ("Sewage", ("sewage", "sewer", "sewage overflow")),
            ("Illegal Dumping", ("illegal dumping", "dumped waste", "dumping")),
            ("Public Toilet", ("public toilet", "public restroom")),
            ("Traffic Signal", ("traffic signal", "signal not working", "traffic light")),
            ("Stray Animals", ("stray animal", "stray dog", "stray cattle")),
            ("Noise Complaint", ("noise complaint", "loud noise", "noise pollution")),
        ]
        matched = next(((category, term) for category, terms in patterns for term in terms if term in text), None)
        entities = self.entities.extract(normalized)
        locations = [item["canonical_name"] for item in entities if item["type"] == "LOCATION"]
        location = locations[0] if locations else None
        category = matched[0] if matched else None
        if category:
            title = f"{category} issue"
            basis = "keyword_match_to_synthetic_example_categories"
        else:
            title = "Civic issue report"
            basis = "no_supported_category_match"
        missing = []
        if not location:
            missing.append("If useful, add the relevant district or local body directly on the official channel; CivicSathi did not infer a location.")
        missing.append("Consider adding when the issue began and any useful non-sensitive context before using an official form.")
        channels = self.complaint_guidance()["channels"]
        preferred = [channel for channel in channels if channel["name"].startswith("GHMC")]
        if location and location.casefold() == "hyderabad":
            suggested_channels = preferred
        else:
            suggested_channels = channels
        return {
            "complaint_title": title,
            "category": category,
            "category_match": basis,
            "original_query": query,
            "description": query,
            "location": location,
            "department": None,
            "date_or_duration": None,
            "missing_information": missing,
            "suggested_next_action": "Review the official channel and enter any additional information there. CivicSathi has not submitted a complaint.",
            "official_channels": suggested_channels,
            "source_information": [
                {"title": "GHMC grievance FAQs", "url": "https://www.ghmc.gov.in/howdoi.aspx", "last_verified": "2026-11-10"},
                {"title": "Prajavani Government of Telangana", "url": "https://prajavani.cgg.gov.in/", "last_verified": "2026-11-10"},
            ],
            "privacy_note": "This draft exists only in the current response/page unless you copy it. Do not include identifiers or sensitive personal details.",
        }

    def analyze(self, query: str, context_service_id: str = "") -> dict:
        normalized = normalize_text(query)
        language = detect_language(normalized)
        if not normalized:
            return {
                "query": query, "language": language,
                "intent": {"label": None, "confidence": None, "fallback": "empty_query"},
                "entities": [], "results": [],
                "answer": "Enter a service, scheme, document, or civic issue to search the catalogues.",
                "warnings": [],
            }
        if find_sensitive_patterns(normalized):
            return {
                "query": "[withheld]", "language": language,
                "intent": {"label": None, "confidence": None, "fallback": "sensitive_input"},
                "entities": [], "results": [],
                "answer": "This query may contain personal or sensitive information, so CivicSathi did not process it. Remove those details and try again.",
                "warnings": ["The query was rejected before classification and retrieval; it was not stored."],
            }

        intent = predict_intent(normalized, model=self.model)
        context_record = self.get_catalogue_record("Service", context_service_id) if context_service_id else None
        contextual_query = normalized
        if context_record and re.search(r"\b(it|that|this|documents?|where|apply|eligib|form|fee|cost|how)\b", normalized, re.I):
            contextual_query = f"{normalized} {context_record['title']}"
        results = self.retriever.search(contextual_query, top_k=10)
        results = [row for row in results if row["score"] >= self.minimum_match_score]
        entities = self.entities.extract(contextual_query)
        documents_requested = (
            intent["label"] == "DOCUMENT_REQUIREMENTS"
            or bool(re.search(r"\b(documents?|papers?|proofs?|checklist|requirements?)\b", normalized, re.I))
            or bool(re.search(r"(?:పత్రాలు|డాక్యుమెంట్లు|ఏమి\s+తీసుకెళ్లాలి)", normalized))
        )
        entity_service_names = {
            item["canonical_name"] for item in entities
            if item["type"] == "SERVICE" and item.get("canonical_name")
        }
        # Keep an explicitly named service visible even when generic FAQ text
        # wins the lexical ranking or a shorthand has a low TF-IDF score.
        for row in self.retriever.records:
            if (row["record_type"] == "Service" and row["title"] in entity_service_names
                    and not any(existing["record_id"] == row["record_id"] for existing in results)):
                entity_result = {key: value for key, value in row.items() if key != "search_text"}
                entity_result["warnings"] = []
                entity_result["match_basis"] = "Service name recognized in query"
                results.append(entity_result)
        # A catalogue entity match is stronger than a generic FAQ's lexical
        # score. Resolve it first, then use service records as a fallback.
        service_ids = list(dict.fromkeys(
            row["service_id"] for row in self.retriever.records
            if row["record_type"] == "Service" and row["title"] in entity_service_names
            and row.get("service_id")
        ))
        service_ids.extend(
            row["service_id"] for row in results
            if row["record_type"] == "Service" and row.get("service_id")
            and row["service_id"] not in service_ids
        )
        # Put the actual service ahead of broad help pages in document queries.
        if documents_requested:
            results.sort(key=lambda row: (row["record_type"] != "Service", -row.get("score", 0)))
        checklists = self.document_requirements.for_services(service_ids, contextual_query) if documents_requested else []
        warnings = []
        if intent["fallback"]:
            warnings.append("The intent classifier is uncertain. Treat the intent as unclassified.")
        if not results:
            warnings.append("No catalogue record passed the minimum lexical match threshold.")
            answer = (
                "I couldn't find a sufficiently close match in the current catalogues. "
                "Try a service, scheme, or document name. The catalogue may not contain the information you need."
            )
        else:
            # This is an extractive summary of stored fields, not generated guidance.
            first = results[0]
            answer = f'The catalogue lists {first["record_type"].lower()}: “{first["title"]}”.'
            if first["department"]:
                answer += f' Department listed: {first["department"]}.'
            available = []
            for field, label in (("description", "Description"), ("eligibility", "Eligibility"),
                                 ("required_documents", "Required documents")):
                value = first.get(field, "").strip()
                if value:
                    available.append(f"{label} as recorded: {value}")
            if available:
                answer += " " + " ".join(available) + "."
            else:
                if documents_requested and checklists:
                    answer += " The base service record is sparse; see the separately sourced checklist below."
                else:
                    answer += " The catalogue has no description, eligibility, or document requirements for this record."
            if first.get("official_url"):
                answer += " A direct official link is listed below; confirm its current status before use."
            elif first.get("source_url"):
                answer += " No direct application link is recorded; the source page is provided for checking."
            warnings.extend(first.get("warnings", []))
            if intent["fallback"]:
                warnings.append("Retrieved records are lexical candidates only because intent confidence is low.")
        if documents_requested and not checklists:
            if service_ids:
                document_notice = (
                    "CivicSathi does not have a verified document checklist for this service and location yet. "
                    "Open the service's Requirements section on the official MeeSeva portal or ask the MeeSeva centre before travelling."
                )
            else:
                document_notice = (
                    "CivicSathi could not identify a service with a verified checklist. Include the service name "
                    "and district (for example, 'residence certificate' or 'caste certificate in Suryapet'). "
                    "Requirements can differ by certificate type and district; confirm them with the official MeeSeva service."
                )
        elif documents_requested:
            document_notice = (
                "These items are copied from the linked government source and are specific to the scenario and area shown. "
                "Confirm the current Requirements at MeeSeva before travelling."
            )
        else:
            document_notice = ""
        if documents_requested:
            if checklists:
                answer += f" I found {len(checklists)} official checklist scenario(s) below. Choose the one that matches your case."
            else:
                answer += " A verified document checklist is not available for this service and location yet."

        return {
            "query": query,
            "language": language,
            "intent": {
                "label": intent["label"], "confidence": intent["confidence"],
                "alternatives": intent["alternatives"], "fallback": intent["fallback"],
                "model_version": intent["model_version"],
            },
            "entities": entities,
            "results": results,
            "documents_requested": documents_requested,
            "document_checklists": checklists,
            "document_notice": document_notice,
            "answer": answer,
            "warnings": list(dict.fromkeys(warnings)),
        }
