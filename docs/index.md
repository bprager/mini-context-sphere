# Serverless FastMCP Starter docs

This project is a small, opinionated starter for

- Static site on Google Cloud Storage
- FastAPI backend with gRPC MCP service and HTTP JSON facade
- SQLite database baked into the container
- Terraform managed infra on Google Cloud Run
- Python environment managed with uv

Use this as a template for lightweight tools, internal dashboards or agent backends that should stay cheap and easy to reason about.

______________________________________________________________________

## High level architecture

```text
+----------------------+        +-------------------------------+
|  Cloud Storage       |        |  Cloud Run (FastAPI + SQLite) |
|----------------------|        |-------------------------------|
| Static Site (HTML/JS)| <----> | gRPC MCP + HTTP JSON facade   |
| Public HTTPS URL     |        | Container stored data.db      |
+----------------------+        +-------------------------------+
```

Flow in one sentence

The static site calls a JSON endpoint, that endpoint delegates to the MCP gRPC service and the service reads from the local SQLite database.

______________________________________________________________________

## Repository layout

Top level

```text
.
├── app/            # FastAPI + gRPC MCP backend, SQLite
├── static-site/    # Frontend assets
├── infra/          # Terraform for GCP
├── .vibe/          # Design and AI guidance
└── docs/           # Human facing docs (this folder)
```

Backend

- `app/main.py` FastAPI app entry point
- gRPC service for MCP, HTTP JSON routes that wrap MCP calls
- `app/db/data.db` SQLite file, read heavy

Frontend

- `static-site/index.html` simple UI
- JavaScript that calls the HTTP JSON facade on the backend

Infra

- `infra/main.tf`, `variables.tf`, `outputs.tf`
- Creates a public bucket with website config
- Creates a Cloud Run v2 service with public invoker role

Guidance

- `.vibe/AI_DEV_INSTRUCTIONS.md` instructions for AI assistants
- `.vibe/API_SPEC.md` request and response contracts
- `.vibe/ARCHITECTURE.md`, `.vibe/INFRA_NOTES.md`, `.vibe/STATIC_SITE.md`
- `.vibe/STATUS.md` short current state log

______________________________________________________________________

## Core concepts

### Static site

The static site is intentionally simple

- Served from a public bucket
- Talks only to the HTTP JSON facade on the backend
- No direct gRPC calls from the browser

For implementation details see `docs/static-site.md` and `.vibe/STATIC_SITE.md`.

### Backend, FastAPI, gRPC and SQLite

The backend has two faces

- gRPC MCP service, the internal protocol for tools and agent clients
- HTTP JSON endpoints, a thin wrapper for the static site and simple scripts

SQLite lives inside the container image as `app/db/data.db`. This keeps reads fast and avoids external state for small deployments. When the data changes, rebuild the image.

For code level documentation see `docs/backend.md`.

### Infra on Google Cloud

Terraform describes

- Google Cloud Storage bucket for the static site
- Google Cloud Run v2 service for the backend
- IAM bindings for public access in demo setups
- Outputs for the site URL and Cloud Run URL

Start without a custom domain. Add Cloud Run domain mapping and a load balancer plus CDN for the bucket later, once you need a stable external URL.

For full infra details see `docs/infra.md`.

______________________________________________________________________

## Development workflow

### Python with uv

Local setup

```bash
uv venv
uv pip install -r requirements.txt
uv run uvicorn app.main:app --reload
```

This keeps the environment consistent across local dev and containers.

See `docs/dev-env.md` for more on tooling, tests, mypy and ruff once they are wired.

### Frontend

During early development you can

- Open `static-site/index.html` directly in the browser and point its API base URL to `http://localhost:8000`
- Or serve the static directory with a simple HTTP server

Later you deploy the static site to the bucket and the backend to Cloud Run.

______________________________________________________________________

## Deploy overview

Short version

1. Build and push the backend image with Cloud Build

1. Use Terraform in `infra/` to create or update

   - Cloud Run service
   - Static site bucket

1. Sync `static-site/` to the bucket with `gsutil rsync`

Detailed commands, variables and examples live in `docs/infra.md`.

______________________________________________________________________

## How to navigate the docs

Start here, then

- To change the API or data model
  see `docs/backend.md` and `.vibe/API_SPEC.md`

- To adjust Terraform or add resources
  see `docs/infra.md` and `.vibe/INFRA_NOTES.md`

- To tweak the UI or add pages
  see `docs/static-site.md`

- When using an AI assistant
  open `.vibe/AI_DEV_INSTRUCTIONS.md` first, then the relevant doc above

- For testing, QA and CI details
  see `docs/testing-qa.md`

<!-- :contentReference[oaicite:0]{index=0} -->
