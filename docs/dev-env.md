# Dev environment

This document describes how to work on the project locally, using uv for Python environment management and keeping the flow consistent with the deployment setup. The root README has a shorter quickstart version.

---

## Goals

* One way to manage Python deps: uv
* Simple local run of the backend and static site
* Clear places for tests, type checking and linting
* Smooth path toward CI, coverage, mypy and ruff badges later

---

## Requirements

* Python 3.13 installed
* `uv` installed globally
* `gcloud` and Terraform only needed for deploy work

---

## Python environment with uv

All Python work uses uv and `requirements.txt`.

Create a virtual environment and install deps

```bash
uv venv
uv pip install -r requirements.txt
```

Activate the venv if your shell does not auto detect it (for example `source .venv/bin/activate`), or let `uv run` handle it on demand.

Upgrade deps after changes to `requirements.txt`

```bash
uv pip install -r requirements.txt
```

---

## Running the backend locally

Start the FastAPI app with uv and uvicorn

```bash
uv run uvicorn app.main:app --reload
```

Then

* `http://localhost:8000/health` should return a small status JSON
* `POST http://localhost:8000/mcp/query` should hit the JSON facade

This is the same app that runs in the Cloud Run container.

---

## Working on the static site locally

For quick work

1. Run the backend as above
2. Set `API_BASE` in `static-site/assets/app.js` to `http://localhost:8000`
3. Open `static-site/index.html` directly in your browser

Or serve the static site with a small HTTP server

```bash
cd static-site
python -m http.server 8081
```

Then open `http://localhost:8081`. If you use a different origin than the backend, add CORS settings to the FastAPI app during development.

---

## Suggested project scripts

You can add a small `Makefile` or simple shell scripts, for example

```makefile
run-backend:
	uv run uvicorn app.main:app --reload

run-static:
	cd static-site && python -m http.server 8081
```

or equivalent `.sh` files in a `scripts/` folder. This keeps commands discoverable for humans and AI assistants.

---

## Tests and quality checks

When you add test and quality tooling, keep it aligned with future badges

Recommended layout

* `tests/` for pytest
* mypy config in `mypy.ini` or `pyproject.toml`
* ruff config in `ruff.toml` or `pyproject.toml`

Typical commands

```bash
# run tests
uv run pytest

# type checking
uv run mypy app tests

# lint or format
uv run ruff check .
uv run ruff format .
```

Once these are in place, your CI workflow can call the same commands and you can add CI, coverage, mypy and ruff badges to the README.

---

## Using AI assistants

For code generation or refactors

* read `.vibe/AI_DEV_INSTRUCTIONS.md` first
* then open the relevant doc in `docs/`
* keep `.vibe/STATUS.md` updated so assistants see the current state

This keeps the dev environment, infra and docs in sync and makes AI suggestions more reliable.

