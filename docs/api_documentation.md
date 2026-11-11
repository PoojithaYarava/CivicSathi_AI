# Local API

Start with `python -m src.app.server --port 8000`. Server binds to loopback only. JSON responses are UTF-8; query/draft bodies are processed in memory and are not logged.

| Method and route | Purpose |
| --- | --- |
| `GET /health` or `/api/health` | Health and storage mode. |
| `GET /api` | Route directory. |
| `GET /api/services` | Browse services. Optional `q`, `department`, `category`, `district`, `limit`. |
| `GET /api/schemes` | Browse schemes with same filters. |
| `GET /api/documents` | Browse forms/documents with same filters. |
| `GET /api/services/{id}`, `/api/schemes/{id}`, `/api/documents/{id}` | Read a single catalogue record. |
| `GET /api/sources` | Source registry with display verification state and domain. |
| `GET /api/search?q=...` | Ranked lexical catalogue search. |
| `GET /api/complaints` | Source-backed complaint routing and preparation guidance. |
| `POST /api/query` or `/api/analyze` | Analyze `{ "query": "...", "context_service_id": "optional catalogue ID" }`. |
| `POST /api/complaints/analyze` or `/api/complaints/draft` | Analyze `{ "description": "..." }` into an unsent structured draft. |

POST bodies must be JSON with string query/description under 2,000 characters; requests larger than 10 KB are rejected. Sensitive-pattern matches in query and complaint descriptions are withheld/rejected. Invalid shape/content type returns 400/415, missing records return 404, and oversized requests return 413. No task endpoints exist because tasks are deliberately client-local and unauthenticated.
