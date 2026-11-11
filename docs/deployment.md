# Deployment and Local Startup

## Local demonstration

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m src.nlp.train
python -m src.app.server --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`. The server is restricted to loopback addresses. Stop with `Ctrl+C`.

## Deployment status

No production deployment is configured. Do not expose the development server directly to the internet. A public deployment requires a maintained production HTTP server, request throttling, deployment-specific privacy and retention decisions, security review, monitored source updates, secrets review, accessibility/browser testing, and an explicit decision about the external browser speech engine. No credentials are required by the current app. This document is not a claim of production readiness or a live public service.

## Telangana district directory

`data/processed/telangana_districts.csv` records the 33 district portals listed in the Government of Telangana district web directory (reviewed 2026-11-11). The app exposes this list at `GET /api/districts` and in the Districts view. It supports district selection/search and entity recognition. It does not provide complete mandal/village coverage, nor imply that every catalogue record or document checklist applies in all districts. Confirm service-specific requirements with the linked district or state source before relying on them.

## Language behavior

The homepage uses the project tagline **“Government services, made easier to understand.”** Citizens can choose English guidance, Telugu help, or bilingual checklist labels. The app retains official source names and records as published rather than automatically translating facts or source text. Telugu guidance is a manually written navigation/caution layer; it is not a substitute for an official Telugu translation or native-speaker QA. The interface itself remains predominantly English in this release.
