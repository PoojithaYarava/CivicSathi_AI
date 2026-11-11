import json
from http.server import HTTPServer
from threading import Thread
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

import pytest

from src.app.server import CivicSathiHandler
from src.app.service import CivicSathiService


@pytest.fixture(scope="module")
def app_url():
    server = HTTPServer(("127.0.0.1", 0), CivicSathiHandler)
    server.civicsathi = CivicSathiService()
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    server.server_close()
    thread.join(timeout=2)


def get_json(url):
    with urlopen(url, timeout=10) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def test_catalogue_browse_endpoints_return_source_records(app_url):
    for endpoint, expected_type in (("services", "Service"), ("schemes", "Scheme"), ("documents", "Document/Form")):
        status, payload = get_json(f"{app_url}/api/{endpoint}")
        assert status == 200
        assert payload["record_type"] == expected_type
        assert payload["count"] > 0
        assert all(row["record_type"] == expected_type for row in payload["items"])


def test_browse_filters_and_search_validation(app_url):
    status, api_docs = get_json(f"{app_url}/api")
    assert status == 200
    assert "GET /api/complaints" in api_docs["routes"]

    status, payload = get_json(f"{app_url}/api/services?q={quote('birth certificate')}&limit=2")
    assert status == 200
    assert len(payload["items"]) <= 2
    status, filtered = get_json(f"{app_url}/api/services?department=Revenue&category=Certificates")
    assert status == 200
    assert filtered["items"]
    assert all("Revenue" in item["department"] and "Certificates" in item["category"] for item in filtered["items"])
    with pytest.raises(HTTPError) as error:
        urlopen(f"{app_url}/api/search", timeout=10)
    assert error.value.code == 400
    with pytest.raises(HTTPError) as error:
        urlopen(f"{app_url}/api/search?q={quote('Aadhaar 1234 5678 9012')}", timeout=10)
    assert error.value.code == 400
    with pytest.raises(HTTPError) as error:
        urlopen(f"{app_url}/api/services?limit=invalid", timeout=10)
    assert error.value.code == 400


def test_complaint_guidance_is_source_backed_and_non_submitting(app_url):
    status, payload = get_json(f"{app_url}/api/complaints")
    assert status == 200
    assert "does not register" in payload["disclaimer"]
    assert {channel["url"] for channel in payload["channels"]} >= {
        "https://ghmc.gov.in/", "https://prajavani.cgg.gov.in/"
    }
    assert payload["form_source"]["url"].endswith("General_Grievances.pdf")


def test_official_district_directory_covers_all_33_districts(app_url):
    status, payload = get_json(f"{app_url}/api/districts")
    assert status == 200
    assert payload["count"] == 33
    assert len({row["district"] for row in payload["items"]}) == 33
    assert all(row["state_portal_directory"] == "https://www.telangana.gov.in/district-web-directory/" for row in payload["items"])


def test_query_endpoint_alias_and_sensitive_input(app_url):
    body = json.dumps({"query": "documents required for residence certificate"}).encode("utf-8")
    request = Request(f"{app_url}/api/query", data=body, headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(request, timeout=10) as response:
        result = json.loads(response.read().decode("utf-8"))
    assert result["documents_requested"] is True
    assert result["document_checklists"]

    sensitive = json.dumps({"query": "Aadhaar 1234 5678 9012"}).encode("utf-8")
    request = Request(f"{app_url}/api/analyze", data=sensitive, headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(request, timeout=10) as response:
        result = json.loads(response.read().decode("utf-8"))
    assert result["query"] == "[withheld]"
    assert result["results"] == []


def test_contextual_followup_uses_only_the_explicit_service_context(app_url):
    body = json.dumps({"query": "What documents are needed?", "context_service_id": "TS0001"}).encode("utf-8")
    request = Request(f"{app_url}/api/query", data=body, headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(request, timeout=10) as response:
        result = json.loads(response.read().decode("utf-8"))
    assert result["query"] == "What documents are needed?"
    assert result["document_checklists"]
    assert all(item["service_id"] == "TS0001" for item in result["document_checklists"])


def test_complaint_draft_is_structured_sensitive_safe_and_never_submitted(app_url):
    body = json.dumps({"description": "Garbage has not been collected near Hyderabad for three days"}).encode("utf-8")
    request = Request(f"{app_url}/api/complaints/draft", data=body, headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(request, timeout=10) as response:
        result = json.loads(response.read().decode("utf-8"))
    assert result["category"] == "Garbage"
    assert result["location"] == "Hyderabad"
    assert "has not submitted" in result["suggested_next_action"]
    assert result["official_channels"]

    sensitive = json.dumps({"description": "Street light issue phone 9876543210"}).encode("utf-8")
    request = Request(f"{app_url}/api/complaints/analyze", data=sensitive, headers={"Content-Type": "application/json"}, method="POST")
    with pytest.raises(HTTPError) as error:
        urlopen(request, timeout=10)
    assert error.value.code == 400
