"""Build schema-only official datasets and reproducible synthetic NLP examples."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .validation import SCHEMAS, scan_sensitive_text, validate_complaints, validate_queries, validate_source_registry
from ..data_collection.source_registry import flatten_sources, load_sources

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
VERIFIED_ON = "2026-10-08"
STATE_SERVICES_URL = "https://www.telangana.gov.in/services/state-services/"
FORMS_URL = "https://www.telangana.gov.in/services/public-utility-forms/"
HYDERABAD_URL = "https://hyderabad.telangana.gov.in/"

OFFICIAL_SERVICES = [
    ("Birth Certificate", "Commissioner & Director of Municipal Administration", "Certificates"),
    ("Death Certificate", "Commissioner & Director of Municipal Administration", "Certificates"),
    ("Property tax online payment", "Commissioner & Director of Municipal Administration", "Property Services"),
    ("Permission for Water Connections", "Commissioner & Director of Municipal Administration", "Water Services"),
    ("Issuance of statutory forms", "Department of Commercial Taxes", "Business Services"),
    ("e-Return Filing", "Department of Commercial Taxes", "Business Services"),
    ("Online Registration System for OPD Appointment", "Department of Health, Medical and Family Welfare", "Health Services"),
    ("Patient Registration", "Department of Health, Medical and Family Welfare", "Health Services"),
    ("e-Payment of Bills / ePayment of Water Bill", "HMWSSB", "Water Services"),
    ("Application for Water Connection (business)", "HMWSSB, Commissioner & Director of Municipal Administration", "Water Services"),
    ("Building or development permit", "Municipal Administration & Urban Development Department", "Municipal Services"),
    ("Occupancy Certificate", "Municipal Administration & Urban Development Department", "Certificates"),
    ("Request for FIR copy", "Police Department", "Police Services"),
    ("Online application of Marriage Certificate", "Registration & Stamps Department", "Certificates"),
    ("Apply online for Encumbrance Certificate", "Registration & Stamps Department", "Property Services"),
    ("Record of Rights (ROR)", "Revenue Department", "Revenue Services"),
    ("Mutation of Revenue Records", "Revenue Department", "Revenue Services"),
    ("Domicile Certificate / Residence Certificate", "Revenue Department", "Certificates"),
    ("Online application of Caste Certificate", "Revenue Department", "Certificates"),
    ("Online application of Income certificate", "Revenue Department", "Certificates"),
    ("Scholarships for students", "Social Welfare Department", "Education"),
    ("Online application for Scholarship", "Social Welfare Department", "Education"),
    ("e-Payment of Electricity Bills (Citizen)", "TSSPDCL, TSNPDCL", "Payments"),
]

OFFICIAL_SCHEMES = [
    ("Saakshar Bharat program", "https://hyderabad.telangana.gov.in/scheme/saakshar-bharat-program/"),
    ("T-Fiber", "https://hyderabad.telangana.gov.in/scheme/t-fiber/"),
    ("SoFTNET", "https://hyderabad.telangana.gov.in/scheme/softnet/"),
    ("Strengthening security apparatus", "https://hyderabad.telangana.gov.in/scheme/strengthening-security-apparatus/"),
    ("Rice distribution", "https://hyderabad.telangana.gov.in/scheme/rice-distribution/"),
]

OFFICIAL_FORMS = [
    ("Application Form for Birth Certificate", "Certificates", "https://ts.meeseva.telangana.gov.in/meeseva/downloadzip.htm?filename=CDMAAPPLICATIONFORBIRTHCERTIFICATE.pdf", "Commissioner & Director of Municipal Administration"),
    ("Application Form for Death Registration", "Certificates", "https://ts.meeseva.telangana.gov.in/meeseva/downloadzip.htm?filename=CDMAAPPLICATIONFORDEATHCERTIFICATE.pdf", "Commissioner & Director of Municipal Administration"),
    ("Application Form for Name Inclusion in Electoral Rolls", "Identity", "https://ts.meeseva.telangana.gov.in/meeseva/downloadzip.htm?filename=InclusionOfName.pdf", "Election Department"),
    ("Application Form for Driving License", "Transport", "http://transport.telangana.gov.in/html/driving-licence.html", "Transport Department"),
    ("Form for Income Certificate", "Certificates", "https://ts.meeseva.telangana.gov.in/meeseva/downloadzip.htm?filename=IncomeGeneralApplicationForm.pdf", "Revenue Department"),
    ("Pre-Matric scholarship form portal", "Education", "https://telanganaepass.cgg.gov.in/", "Social Welfare Department"),
]

SERVICES = [
    ("income certificate", "ఆదాయ ధృవీకరణ పత్రం", "Revenue"),
    ("birth certificate", "జనన ధృవీకరణ పత్రం", "Municipal Administration"),
    ("caste certificate", "కుల ధృవీకరణ పత్రం", "Revenue"),
    ("residence certificate", "నివాస ధృవీకరణ పత్రం", "Revenue"),
    ("property tax", "ఆస్తి పన్ను", "Municipal Administration"),
    ("water connection", "నీటి కనెక్షన్", "Water Services"),
    ("driving licence", "డ్రైవింగ్ లైసెన్స్", "Transport"),
    ("scholarship", "విద్యార్థి వేతనం", "Education"),
    ("pension", "పెన్షన్", "Welfare"),
    ("ration card", "రేషన్ కార్డు", "Civil Supplies"),
    ("trade licence", "ట్రేడ్ లైసెన్స్", "Municipal Administration"),
    ("land record", "భూమి రికార్డు", "Revenue"),
]

INTENT_TEMPLATES = {
    "SERVICE_DISCOVERY": ["Where can I find information about {service}?", "{telugu} సేవ ఎక్కడ లభిస్తుంది?", "{service} service details ekkada dorukutayi?"],
    "APPLICATION_PROCEDURE": ["How do I apply for {service}?", "{telugu} కోసం ఎలా దరఖాస్తు చేయాలి?", "{service} ki ela apply cheyyali?"],
    "DOCUMENT_REQUIREMENTS": ["What documents are needed for {service}?", "{telugu} కోసం ఏ పత్రాలు కావాలి?", "{service} ki em documents kavali?"],
    "ELIGIBILITY": ["Who is eligible for {service}?", "{telugu} పొందడానికి అర్హత ఏమిటి?", "{service} ki eligibility enti?"],
    "FORM_DOWNLOAD": ["Where can I download the {service} form?", "{telugu} దరఖాస్తు ఫారం ఎక్కడ దొరుకుతుంది?", "{service} form ekkada download cheyyali?"],
    "OFFICIAL_LINK": ["What is the official website for {service}?", "{telugu} అధికారిక వెబ్‌సైట్ ఏది?", "{service} official link pampandi"],
    "COMPLAINT_REGISTRATION": ["How can I report an issue related to {service}?", "{telugu} సమస్యపై ఫిర్యాదు ఎలా చేయాలి?", "{service} gurinchi complaint ela ivvali?"],
    "COMPLAINT_TRACKING": ["Where can I track a complaint about {service}?", "{telugu} ఫిర్యాదు స్థితి ఎలా తెలుసుకోవాలి?", "{service} complaint status ela check cheyyali?"],
    "PAYMENT": ["How can I pay for {service} online?", "{telugu} రుసుమును ఆన్‌లైన్‌లో ఎలా చెల్లించాలి?", "{service} online lo ela pay cheyyali?"],
    "SCHEME_DISCOVERY": ["Which government schemes support {service}?", "{telugu}కు సంబంధించిన ప్రభుత్వ పథకాలు ఏమిటి?", "{service} related schemes em unnayi?"],
    "SCHEME_ELIGIBILITY": ["What are the eligibility rules for schemes related to {service}?", "{telugu} పథకాలకు అర్హత ఏమిటి?", "{service} scheme ki eligibility enti?"],
    "STATUS_CHECK": ["How do I check my {service} application status?", "{telugu} దరఖాస్తు స్థితిని ఎలా చూడాలి?", "{service} application status ela check cheyyali?"],
}

COMPLAINT_TEMPLATES = {
    "Street Light": ["The street light is not working", "వీధి దీపం పని చేయడం లేదు", "maa veedhi street light pani cheyyatledu"],
    "Road Damage": ["The road is damaged", "రోడ్డు దెబ్బతింది", "maa area lo road damage ayyindi"],
    "Garbage": ["Garbage has not been collected", "చెత్త సేకరించడం లేదు", "maa area lo garbage collect cheyyatledu"],
    "Drainage": ["The drainage is blocked", "మురుగు కాలువ మూసుకుపోయింది", "maa veedhi drainage block ayyindi"],
    "Water Supply": ["There is no water supply", "నీటి సరఫరా లేదు", "maa area lo water supply ledu"],
    "Water Leakage": ["Water is leaking from a pipe", "పైపు నుంచి నీరు కారుతోంది", "pipe nunchi water leakage avutondi"],
    "Sewage": ["Sewage is overflowing", "మురుగు నీరు పొంగిపోతోంది", "maa area lo sewage overflow avutondi"],
    "Illegal Dumping": ["Waste is being dumped in a public place", "బహిరంగ ప్రదేశంలో చెత్త వేస్తున్నారు", "public place lo illegal dumping chestunnaru"],
    "Public Toilet": ["The public toilet needs maintenance", "ప్రజా మరుగుదొడ్డికి మరమ్మతులు అవసరం", "public toilet maintenance kavali"],
    "Traffic Signal": ["The traffic signal is not working", "ట్రాఫిక్ సిగ్నల్ పని చేయడం లేదు", "traffic signal pani cheyyatledu"],
    "Stray Animals": ["Stray animals are creating a civic issue", "వీధి జంతువుల వల్ల సమస్య ఉంది", "stray animals valla problem avutondi"],
    "Noise Complaint": ["There is excessive noise", "అధిక శబ్దం వల్ల ఇబ్బంది ఉంది", "maa area lo noise ekkuvaga undi"],
    "Other Civic Issue": ["I need to report another civic issue", "మరొక పౌర సమస్యను నివేదించాలి", "oka civic issue report cheyyali"],
}


def build_queries() -> pd.DataFrame:
    records = []
    number = 1
    for intent, templates in INTENT_TEMPLATES.items():
        for service_name, telugu, department in SERVICES:
            for language_index, template in enumerate(templates):
                for variant in range(3):
                    query = template.format(service=service_name, telugu=telugu)
                    if variant == 1:
                        query += {0: " please", 1: " దయచేసి", 2: " please"}[language_index]
                    elif variant == 2:
                        query = {0: f"Please help me: {query}", 1: f"దయచేసి చెప్పండి: {query}", 2: f"Please cheppandi: {query}"}[language_index]
                    records.append({
                        "query_id": f"CQ{number:05d}", "query": query,
                        "language": ["English", "Telugu", "Telugu-English"][language_index],
                        "intent": intent, "service": service_name, "department": department,
                        "entities": f"service={service_name}", "action": intent.lower(),
                        "source_type": "synthetic_annotated",
                    })
                    number += 1
    return pd.DataFrame(records, columns=SCHEMAS["citizen_queries.csv"])


def build_complaints() -> pd.DataFrame:
    records = []
    number = 1
    suffixes = {
        0: ["", " please", " needs attention", " reported", " kindly resolve", " please help", " I need assistance", " please address this", " can this be fixed", " requesting support", " this is causing inconvenience", " please inspect", " it remains unresolved", " please take action", " seeking a resolution", " kindly look into this"],
        1: ["", " దయచేసి", " సమస్య ఉంది", " పరిష్కరించండి", " గమనించండి", " సహాయం కావాలి", " దయచేసి చూడండి", " పరిష్కారం కావాలి", " చర్య తీసుకోండి", " దృష్టి పెట్టండి", " ఇంకా సమస్య ఉంది", " పరిశీలించండి", " త్వరగా పరిష్కరించండి", " సహాయం చేయండి", " ఫిర్యాదు నమోదు చేయండి", " దయచేసి స్పందించండి"],
        2: ["", " please", " issue undi", " resolve cheyyandi", " help kavali", " konchem chudandi", " action teesukondi", " problem continue avutondi", " complaint register cheyyandi", " please respond", " urgent ga chudandi", " support kavali", " check cheyyandi", " inka fix avvaledu", " solution ivvandi", " dayachesi help cheyyandi"],
    }
    for category, templates in COMPLAINT_TEMPLATES.items():
        department = "Water Services" if category in {"Water Supply", "Water Leakage"} else "Municipal Administration"
        for language_index, template in enumerate(templates):
            for variant in range(16):
                query = template + suffixes[language_index][variant % len(suffixes[language_index])]
                records.append({
                    "complaint_id": f"CC{number:05d}", "query": query,
                    "language": ["English", "Telugu", "Telugu-English"][language_index],
                    "complaint_category": category, "issue_type": "Needs review", "location": "",
                    "urgency": "Medium", "department": department,
                    "required_information": "location,description", "action": "raise_complaint",
                    "source_type": "synthetic_annotated",
                })
                number += 1
    return pd.DataFrame(records, columns=SCHEMAS["complaint_queries.csv"])


def build_official_services() -> pd.DataFrame:
    records = []
    for number, (name, department, category) in enumerate(OFFICIAL_SERVICES, start=1):
        records.append({
            "service_id": f"TS{number:04d}", "service_name": name, "service_name_telugu": "",
            "department": department, "category": category, "description": "", "eligibility": "",
            "required_documents": "", "application_steps": "", "application_mode": "",
            "service_charge": "", "sla": "", "official_application_url": "", "official_form_url": "",
            "status_tracking_url": "", "complaint_url": "", "state": "Telangana",
            "district": "", "source_url": STATE_SERVICES_URL, "last_verified": VERIFIED_ON,
        })
    return pd.DataFrame(records, columns=SCHEMAS["service_catalog.csv"])


def build_official_schemes() -> pd.DataFrame:
    records = []
    for number, (name, url) in enumerate(OFFICIAL_SCHEMES, start=1):
        records.append({
            "scheme_id": f"HYD{number:04d}", "scheme_name": name, "scheme_name_telugu": "",
            "department": "", "target_group": "", "description": "", "eligibility": "",
            "benefits": "", "required_documents": "", "application_process": "",
            "application_url": "", "source_url": url, "state": "Telangana", "district": "Hyderabad",
            "last_verified": VERIFIED_ON,
        })
    return pd.DataFrame(records, columns=SCHEMAS["government_schemes.csv"])


def build_official_forms() -> pd.DataFrame:
    records = []
    for number, (name, category, url, department) in enumerate(OFFICIAL_FORMS, start=1):
        records.append({
            "document_id": f"DOC{number:04d}", "service_id": "", "service_name": "",
            "document_name": name, "document_type": "Official form or portal", "purpose": category,
            "mandatory": "", "description": "Listed on Telangana Public Utility Forms page; destination not downloaded.",
            "download_url": url, "source_url": FORMS_URL, "department": department,
            "last_verified": VERIFIED_ON,
        })
    return pd.DataFrame(records, columns=SCHEMAS["documents_and_forms.csv"])


def add_observed_links_to_registry(registry: pd.DataFrame) -> pd.DataFrame:
    additions = []
    for source_type, entries in (("Official Scheme", OFFICIAL_SCHEMES), ("Official Form", OFFICIAL_FORMS)):
        for index, entry in enumerate(entries, start=1):
            if source_type == "Official Scheme":
                name, url = entry
                organization, district = "Hyderabad District Government", "Hyderabad"
            else:
                name, _, url, _ = entry
                organization, district = "Telangana Government", ""
            additions.append({
                "source_id": f"observed_{source_type.split()[1].lower()}_{index:03d}",
                "organization": organization, "department": "", "service": name,
                "source_type": source_type, "url": url,
                "description": "Link observed on an official listing page; destination needs individual review.",
                "state": "Telangana", "district": district, "verification_status": "needs_review",
                "last_verified": VERIFIED_ON,
            })
    additions.extend([
        {"source_id": "telangana_state_services_listing", "organization": "Telangana Government", "department": "", "service": "State Services", "source_type": "Official Service", "url": STATE_SERVICES_URL, "description": "Listing page checked; individual service details were not independently verified.", "state": "Telangana", "district": "", "verification_status": "verified", "last_verified": VERIFIED_ON},
        {"source_id": "telangana_public_utility_forms_listing", "organization": "Telangana Government", "department": "", "service": "Public Utility Forms", "source_type": "Official Form", "url": FORMS_URL, "description": "Official forms listing page checked.", "state": "Telangana", "district": "", "verification_status": "verified", "last_verified": VERIFIED_ON},
    ])
    return pd.concat([registry, pd.DataFrame(additions)], ignore_index=True).drop_duplicates(subset="url", keep="first")


def build_all() -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    queries = build_queries()
    complaints = build_complaints()
    if errors := validate_queries(queries):
        raise ValueError(f"Synthetic query validation failed: {errors}")
    if errors := validate_complaints(complaints):
        raise ValueError(f"Synthetic complaint validation failed: {errors}")
    privacy_findings = scan_sensitive_text(queries, ["query"]) + scan_sensitive_text(complaints, ["query"])
    if privacy_findings:
        raise ValueError(f"Sensitive-looking text must be reviewed before save: {privacy_findings[:10]}")
    registry = flatten_sources(load_sources()).pipe(add_observed_links_to_registry)
    if errors := validate_source_registry(registry):
        raise ValueError(f"Source registry validation failed: {errors}")
    registry.to_csv(PROCESSED / "official_sources.csv", index=False, encoding="utf-8-sig")
    build_official_services().to_csv(PROCESSED / "service_catalog.csv", index=False, encoding="utf-8-sig")
    build_official_schemes().to_csv(PROCESSED / "government_schemes.csv", index=False, encoding="utf-8-sig")
    build_official_forms().to_csv(PROCESSED / "documents_and_forms.csv", index=False, encoding="utf-8-sig")
    queries.to_csv(PROCESSED / "citizen_queries.csv", index=False, encoding="utf-8-sig")
    complaints.to_csv(PROCESSED / "complaint_queries.csv", index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    build_all()