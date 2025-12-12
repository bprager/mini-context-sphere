# Serverless FastMCP Starter

<!-- Badges: Release, License, Python, CI, Coverage, mypy, ruff -->

## Badges

[![CI](https://github.com/bprager/mini-context-sphere/actions/workflows/ci.yml/badge.svg)](https://github.com/bprager/mini-context-sphere/actions/workflows/ci.yml)
[![CodeQL](https://github.com/bprager/mini-context-sphere/actions/workflows/codeql.yml/badge.svg)](https://github.com/bprager/mini-context-sphere/actions/workflows/codeql.yml)
[![Coverage](https://codecov.io/gh/bprager/mini-context-sphere/branch/main/graph/badge.svg)](https://codecov.io/gh/bprager/mini-context-sphere)
[![Release](https://img.shields.io/github/v/release/bprager/mini-context-sphere?include_prereleases&sort=semver)](https://github.com/bprager/mini-context-sphere/releases)
[![License](https://img.shields.io/github/license/bprager/mini-context-sphere)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.14%2B-blue)](pyproject.toml)
[![mypy](https://img.shields.io/badge/type_check-mypy-blue)](docs/testing-qa.md)
[![ruff](https://img.shields.io/badge/lint-ruff-000000?logo=ruff&logoColor=white)](docs/testing-qa.md)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](.pre-commit-config.yaml)
[![Dependabot](https://img.shields.io/badge/dependabot-enabled-brightgreen?logo=dependabot)](.github/dependabot.yml)

Minimal starter for a static site plus FastAPI plus gRPC MCP backend on Google Cloud Run, with SQLite for local data and Terraform for infra. Designed to stay in the free tier for small workloads.

See the [roadmap](docs/roadmap.md) for planned features and future direction.

## Quick Links

- Run locally: `uv venv && uv pip install -r requirements.txt && uv run uvicorn app.main:app --reload`
- Full QA suite: `uv sync --group dev && make qa` (details in the [testing & QA guide](docs/testing-qa.md))
- Start with gRPC enabled: `START_GRPC=true uv run uvicorn app.main:app --reload` (see the [backend guide](docs/backend.md))
- Generate gRPC stubs: `make proto` (proto in `proto/mcp.proto`)
- Deploy to Cloud Run/GCS: follow the [infra guide](docs/infra.md)

## Features

- Static site on Google Cloud Storage
- FastAPI backend with gRPC MCP service and HTTP JSON facade
- SQLite database baked into the container
- Terraform for Cloud Run service and public bucket
- Python env managed with uv

## Quick Start (Local Dev)

```
uv venv
uv pip install -r requirements.txt
uv run uvicorn app.main:app --reload
```

Then open <http://localhost:8000> and hit `/health` or the JSON facade used by the static site.

## Docs

- Big picture: start with the project overview.
  See the overview to understand components and flow (docs/index.md).
- Backend: how the FastAPI + gRPC MCP server and SQLite DB fit together.
  Learn how to run locally and generate stubs (docs/backend.md).
- Static site: how to build and ship the UI.
  Steps to tweak the frontend and connect to the API (docs/static-site.md).
- Infra: deploy on Google Cloud using Terraform.
  From Cloud Run to a public bucket (docs/infra.md).
- Dev environment: get your machine ready.
  Tools, Python env, and editor setup (docs/dev-env.md).
- Testing & QA: the one‑command quality gate.
  What `make qa` runs and how CI enforces it (docs/testing-qa.md).
- Pipeline optimization: faster ingest and queries on SQLite.
  Pragmas, indexes, FTS, batching (docs/pipeline-optimization.md).
- Roadmap: what’s next and why.
  Priorities and milestones (docs/roadmap.md).
- Deep dives: design notes and API contracts.
  Explore the `.vibe/` folder for architecture and specs.

## Deploy to GCP

Use Terraform in `infra/` to create the Cloud Run service and public bucket, then sync the `static-site/` folder to the bucket. See [docs/infra.md](docs/infra.md) for the full deploy flow.
