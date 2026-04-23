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
cp .env.example .env
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload --env-file .env
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
set -a
source .env
set +a
.venv/bin/python scripts/generate_openapi.py
```

Generated file path:

```text
openapi/openapi.json
```

Swagger UI servers dropdown uses the OpenAPI server settings:

```text
OPENAPI_SERVER_URL=http://127.0.0.1:8000
OPENAPI_SERVER_DESCRIPTION=Local development server
```

Admin endpoints require a bearer token. Local development uses this default token unless you override it:

```text
ADMIN_BEARER_TOKEN=local-admin-token
```

In Swagger UI, click `Authorize` and enter this token value:

```text
local-admin-token
```

Example admin request:

```bash
curl -H "Authorization: Bearer local-admin-token" http://127.0.0.1:8000/organizations
```

## Notes

- Data is stored in memory for the MVP sample.
- Admin auth is enforced with the `BearerAuth` scheme.
- Survey access is available through `/surveys/slug/{slug}` when the survey `isPublic` property is `true`.
