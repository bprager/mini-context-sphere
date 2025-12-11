# Serverless FastMCP Starter

<!-- Badges: Release, License, Python, CI, Coverage, mypy, ruff -->

## Badges

[![CI](https://github.com/bprager/mini-context-sphere/actions/workflows/ci.yml/badge.svg)](https://github.com/bprager/mini-context-sphere/actions/workflows/ci.yml)
[![CodeQL](https://github.com/bprager/mini-context-sphere/actions/workflows/codeql.yml/badge.svg)](https://github.com/bprager/mini-context-sphere/actions/workflows/codeql.yml)
[![Coverage](https://codecov.io/gh/bprager/mini-context-sphere/branch/main/graph/badge.svg)](https://codecov.io/gh/bprager/mini-context-sphere)
[![Version](docs/badges/version.svg)](CHANGELOG.md)
[![Release](https://img.shields.io/github/v/release/bprager/mini-context-sphere?include_prereleases&sort=semver)](https://github.com/bprager/mini-context-sphere/releases)
[![License](https://img.shields.io/github/license/bprager/mini-context-sphere)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.14%2B-blue)](pyproject.toml)
[![mypy](https://img.shields.io/badge/type_check-mypy-blue)](docs/testing-qa.md)
[![ruff](https://img.shields.io/badge/lint-ruff-000000?logo=ruff&logoColor=white)](docs/testing-qa.md)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](.pre-commit-config.yaml)
[![Dependabot](https://img.shields.io/badge/dependabot-enabled-brightgreen?logo=dependabot)](.github/dependabot.yml)

Minimal starter for a static site plus FastAPI plus gRPC MCP backend on Google Cloud Run, with SQLite for local data and Terraform for infra. Designed to stay in the free tier for small workloads.

See the full feature roadmap in [docs/roadmap.md](docs/roadmap.md).

For planned features and future directions see `docs/roadmap.md`.

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

Then open http://localhost:8000 and hit `/health` or the JSON facade used by the static site.

## Docs

- Overview: [docs/index.md](docs/index.md)
- Backend: [docs/backend.md](docs/backend.md)
- Static site: [docs/static-site.md](docs/static-site.md)
- Infra: [docs/infra.md](docs/infra.md)
- Dev env: [docs/dev-env.md](docs/dev-env.md)
- Testing & QA: [docs/testing-qa.md](docs/testing-qa.md)
- Roadmap: [docs/roadmap.md](docs/roadmap.md)
- Design and AI guidance: see `.vibe/` for deeper architecture notes and API specs

## Deploy to GCP

Use Terraform in `infra/` to create the Cloud Run service and public bucket, then sync the `static-site/` folder to the bucket. See [docs/infra.md](docs/infra.md) for the full deploy flow.
