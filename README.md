# Customer Feedback Backend

MVP backend for customer feedback collection.

This first iteration focuses on:
- OpenAPI 3.1 contract generation
- Swagger UI
- REST endpoint definitions for admin flows and survey access by slug
- local development without external services

## Stack

- Python
- FastAPI
- Uvicorn

## Run locally

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

OpenAPI JSON from runtime:

```text
http://127.0.0.1:8000/openapi.json
```

Generate a repo copy of the OpenAPI document:

```bash
.venv/bin/python scripts/generate_openapi.py
```

Generated file path:

```text
openapi/openapi.json
```

## Notes

- Data is stored in memory for the MVP sample.
- Admin auth is documented as a placeholder `BearerAuth` scheme, but not enforced yet.
- Survey access is available through `/surveys/slug/{slug}` when the survey `isPublic` property is `true`.
