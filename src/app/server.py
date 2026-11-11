"""Start the local CivicSathi web app: python -m src.app.server."""

from __future__ import annotations

import argparse
import json
import re
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from .service import CivicSathiService
from src.data_processing.normalization import find_sensitive_patterns

STATIC_DIR = Path(__file__).parent / "static"
MAX_BODY_BYTES = 10_240


class CivicSathiHandler(BaseHTTPRequestHandler):
    server_version = "CivicSathiLocal/1.0"

    def _headers(self, status: int, content_type: str, length: int):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(length))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data:")
        self.end_headers()

    def _json(self, status: int, value: dict):
        data = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self._headers(status, "application/json; charset=utf-8", len(data))
        self.wfile.write(data)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query, keep_blank_values=False)
        if path in {"/api", "/api/"}:
            self._json(200, {"name": "CivicSathi local read-only API", "routes": {
                "GET /api/health": "Readiness and storage mode",
                "GET /api/services": "Browse service records",
                "GET /api/services/{service_id}": "Read one service record",
                "GET /api/schemes": "Browse scheme records",
                "GET /api/schemes/{scheme_id}": "Read one scheme record",
                "GET /api/documents": "Browse forms and document records",
                "GET /api/sources": "Read official source records and verification states",
                "GET /api/districts": "Read the official directory of all Telangana districts",
                "GET /api/search?q=...": "Ranked lexical catalogue search",
                "GET /api/complaints": "Source-backed guidance; no submission",
                "POST /api/complaints/analyze": "Analyze an issue description into an unsent draft",
                "POST /api/complaints/draft": "Alias for complaint analysis; does not submit",
                "POST /api/query": "Analyze a citizen query (also /api/analyze)",
            }})
            return
        if path in {"/health", "/api/health"}:
            self._json(200, {"status": "ok", "storage": "in_memory_only", "version": "1.1"})
            return
        if path == "/api/complaints":
            self._json(200, self.server.civicsathi.complaint_guidance())
            return
        if path == "/api/sources":
            items = self.server.civicsathi.source_directory()
            self._json(200, {"count": len(items), "items": items})
            return
        if path == "/api/districts":
            district_file = self.server.civicsathi.data_dir / "telangana_districts.csv"
            if not district_file.exists():
                self._json(503, {"error": "Telangana district directory is not installed"})
                return
            import pandas as pd
            items = pd.read_csv(district_file, keep_default_na=False).to_dict(orient="records")
            self._json(200, {"count": len(items), "items": items,
                             "scope_note": "District coverage directory only. Checklist availability remains limited to individually researched official sources."})
            return
        detail_route = re.fullmatch(r"/api/(services|schemes|documents)/([^/]+)", path)
        if detail_route:
            item_type = {"services": "Service", "schemes": "Scheme", "documents": "Document/Form"}[detail_route.group(1)]
            item = self.server.civicsathi.get_catalogue_record(item_type, unquote(detail_route.group(2)))
            if item is None:
                self._json(404, {"error": "Catalogue record not found"})
            else:
                self._json(200, item)
            return
        browse_routes = {
            "/api/services": "Service",
            "/api/schemes": "Scheme",
            "/api/documents": "Document/Form",
        }
        if path in browse_routes:
            if any(len(values[0]) > 200 for values in params.values() if values):
                self._json(400, {"error": "Filter values must be 200 characters or fewer"})
                return
            filter_text = " ".join(value for values in params.values() for value in values)
            if find_sensitive_patterns(filter_text):
                self._json(400, {"error": "A filter may contain sensitive information. Remove it and search by public service details."})
                return
            try:
                limit = int(params.get("limit", ["100"])[0])
                items = self.server.civicsathi.browse_catalogue(
                    browse_routes[path], query=params.get("q", [""])[0],
                    department=params.get("department", [""])[0],
                    category=params.get("category", [""])[0],
                    district=params.get("district", [""])[0], limit=limit,
                )
            except (TypeError, ValueError):
                self._json(400, {"error": "limit must be an integer from 1 to 100"})
                return
            self._json(200, {"record_type": browse_routes[path], "count": len(items), "items": items})
            return
        if path == "/api/search":
            query = params.get("q", [""])[0]
            if not query.strip() or len(query) > 2000:
                self._json(400, {"error": "Provide q with a search query of 1 to 2000 characters"})
                return
            if find_sensitive_patterns(query):
                self._json(400, {"error": "This query may contain sensitive information. Remove it and search by public service details."})
                return
            try:
                limit = max(1, min(int(params.get("limit", ["10"])[0]), 50))
            except ValueError:
                self._json(400, {"error": "limit must be an integer"})
                return
            results = self.server.civicsathi.retriever.search(query, top_k=limit)
            kind = params.get("type", [""])[0].casefold()
            if kind:
                results = [row for row in results if row["record_type"].casefold() == kind]
            self._json(200, {"query": query, "count": len(results), "results": results})
            return
        if path not in ("/", "/index.html"):
            self._json(404, {"error": "Not found"})
            return
        data = (STATIC_DIR / "index.html").read_bytes()
        self._headers(200, "text/html; charset=utf-8", len(data))
        self.wfile.write(data)

    def do_POST(self):
        path = urlparse(self.path).path
        is_complaint = path in {"/api/complaints/analyze", "/api/complaints/draft"}
        if path not in ("/api/analyze", "/api/query") and not is_complaint:
            self._json(404, {"error": "Not found"})
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._json(400, {"error": "Invalid request length"})
            return
        if size < 1 or size > MAX_BODY_BYTES:
            self._json(413 if size > MAX_BODY_BYTES else 400, {"error": "Request must contain a query under 10 KB"})
            return
        if "application/json" not in self.headers.get("Content-Type", "").lower():
            self._json(415, {"error": "Use application/json"})
            return
        try:
            payload = json.loads(self.rfile.read(size).decode("utf-8"))
            query = (payload.get("description", payload.get("query")) if is_complaint
                     else payload.get("query")) if isinstance(payload, dict) else None
            if not isinstance(query, str):
                raise ValueError
            if len(query) > 2000:
                self._json(413, {"error": "Query must be 2000 characters or fewer"})
                return
            if is_complaint:
                try:
                    response = self.server.civicsathi.analyze_complaint(query)
                except ValueError as error:
                    self._json(400, {"error": str(error)})
                    return
            else:
                context_service_id = payload.get("context_service_id", "")
                if not isinstance(context_service_id, str) or len(context_service_id) > 64:
                    self._json(400, {"error": "context_service_id must be a short string"})
                    return
                response = self.server.civicsathi.analyze(query, context_service_id=context_service_id)
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError, TypeError):
            self._json(400, {"error": "Request must be JSON with a string 'query' field"})
            return
        except Exception:
            # Do not return query text, source rows, or stack traces to the browser.
            self._json(500, {"error": "The request could not be processed. Check local app setup and logs."})
            return
        self._json(200, response)

    def log_message(self, fmt, *args):
        # Avoid default request logs that could include user-provided URLs or data.
        return


def main():
    parser = argparse.ArgumentParser(description="Run the local CivicSathi read-only assistant")
    parser.add_argument("--host", default="127.0.0.1", help="Bind address (default: localhost only)")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    if args.host not in {"127.0.0.1", "localhost", "::1"}:
        parser.error("For privacy, the development server only binds to loopback addresses")
    app = CivicSathiService()
    server = HTTPServer((args.host, args.port), CivicSathiHandler)
    server.civicsathi = app
    print(f"CivicSathi is ready at http://{args.host}:{args.port}")
    print("Queries are processed in memory only; press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
