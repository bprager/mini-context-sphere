# Serverless FastMCP Starter

<!-- Badges: Release, License, Python, CI, Coverage, mypy, ruff -->

Minimal starter for a static site plus FastAPI plus gRPC MCP backend on Google Cloud Run, with SQLite for local data and Terraform for infra. Designed to stay in the free tier for small workloads.

## Features

- Static site on Google Cloud Storage
- FastAPI backend with gRPC MCP service and HTTP JSON facade
- SQLite database baked into the container
- Terraform for Cloud Run service and public bucket
- Python env managed with uv

## Quick start (local dev)

    uv venv
    uv pip install -r requirements.txt
    uv run uvicorn app.main:app --reload

Then open http://localhost:8000 and hit `/health` or the JSON facade used by the static site.

## Docs

- Project docs: see `docs/` (architecture, backend, infra, static site, dev env)
- Design and AI guidance: see `.vibe/`
  - `.vibe/AI_DEV_INSTRUCTIONS.md`
  - `.vibe/API_SPEC.md`
  - `.vibe/ARCHITECTURE.md`
  - `.vibe/INFRA_NOTES.md`
  - `.vibe/STATIC_SITE.md`
  - `.vibe/STATUS.md`

## Deploy to GCP

Use Terraform in `infra/` to create the Cloud Run service and public bucket, then sync the `static-site/` folder to the bucket. See `docs/infra.md` for the full deploy flow.

