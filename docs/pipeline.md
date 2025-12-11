# Data pipeline and hypergraph

This document describes the data pipeline that turns user provided markdown into a SQLite based hypergraph knowledge base, using a SQLite graph extension, and optionally into the SQLite snapshot used by the runtime backend. The pipeline is small, easy to customize and optional, so the core starter remains minimal.

______________________________________________________________________

## Goals

- Let users define their knowledge as markdown files under version control
- Use a pluggable AI backend (OpenAI, Gemini, Ollama, etc.) to build or update a hypergraph
- Store the hypergraph in a dedicated SQLite database that has a graph extension enabled
- Optionally export a compact `app/db/data.db` snapshot for the runtime backend
- Provide a tutorial based on a personal LinkedIn profile to make the system instantly tangible

______________________________________________________________________

## High level architecture

```text
markdown sources ─► AI builder ─► hypergraph (SQLite + graph extension)
       ▲                                       │
       │                                 optional export
LinkedIn tutorial bootstrap                   ▼
                                     runtime SQLite snapshot (data.db)


```

- A dedicated SQLite file (for example hypergraph.db) is the long lived hypergraph store
- `app/db/data.db` is a generated snapshot for the FastAPI runtime, if you choose to keep them separate
- The pipeline is responsible for reading markdown, calling AI backends where needed, and writing nodes and edges into the SQLite graph database

______________________________________________________________________

## Repository layout

Pipeline code lives in separate folders, next to the runtime and docs:

```text
pipeline/
  __init__.py
  config.py            # configuration and environment loading
  ai_client.py         # AI backend abstraction and adapters
  markdown_loader.py   # load and validate markdown templates
  hypergraph_writer.py # write nodes and edges to SQLite graph db
  cli.py               # command line entry points

tutorials/
  linkedin/
    README.md
    linkedin_bootstrap.py
    examples/
      profile.html     # sample or template profile export

```

The runtime backend and static site remain unchanged:

- `app/` for FastAPI, gRPC MCP and SQLite
- `static-site/` for the frontend
- `infra/` for Terraform and GCP resources

______________________________________________________________________

## Configuration

Pipeline behavior is controlled by a small set of configuration values, read from environment variables or a simple config file in `pipeline/config.py`.

Suggested variables:

- `HYPERGRAPH_DB_DSN` PostgreSQL connection string
- `AI_PROVIDER` one of `openai`, `gemini`, `ollama`
- `AI_MODEL` model name for the selected provider
- `MARKDOWN_ROOT` base folder with user markdown sources, for example `knowledge/`
- `PROFILE_NAME` logical profile name, for example `profile`, `portfolio`, `interests`

`config.py` should expose a single function, for example:

```python
def load_config() -> PipelineConfig:
    ...
```

so both the CLI and tutorials can build on it.

______________________________________________________________________

## AI backend abstraction

The AI backend is intentionally small and pluggable.

`ai_client.py` defines a minimal interface:

```python
class AiBackend(Protocol):
    def complete(self, prompt: str) -> str: ...
```

Concrete implementations:

- `OpenAiBackend` for OpenAI models
- `GeminiBackend` for Google Gemini
- `OllamaBackend` for local models

`config.py` chooses the correct implementation based on `AI_PROVIDER`.

At first, the pipeline can work without any AI calls, for example by only parsing markdown, then AI steps can be layered in as needed (normalizing titles, building richer node attributes, deriving edges).

______________________________________________________________________

## Markdown as the source of truth

User knowledge is represented as markdown files under a configurable root folder, for example:

```text
knowledge/
  profile/
    jobs/
      2018_acme_senior_engineer.md
      2021_neo_product_lead.md
    companies/
      acme_corp.md
      neo_labs.md
    skills/
      backend_python.md
      cloud_architecture.md
```

Each file can follow a simple pattern:

```md
---
type: job
id: job_2018_acme_senior_engineer
company: Acme Corp
start: 2018-01-01
end: 2020-06-30
---

Short description in free text.

Bullet points of responsibilities.

Any extra details you want to capture.
```

`markdown_loader.py` should:

- discover files under `MARKDOWN_ROOT`
- parse optional front matter and body
- yield a neutral internal representation for `hypergraph_writer.py`

The exact schema can evolve, as long as `hypergraph_writer.py` knows how to map it to nodes and edges.

______________________________________________________________________

## Hypergraph writer

`hypergraph_writer.py` is responsible for talking to PostgreSQL. It should hide table structure behind simple helpers, such as:

- `upsert_node(node)`
- `upsert_edge(edge)`
- `upsert_hyperedge(hyperedge)`

For the starter, you can keep the hypergraph tables very simple:

- `nodes(id text primary key, type text, data jsonb)`
- `edges(id text primary key, type text, source text, target text, data jsonb)`

Later, you can refine this schema without changing the rest of the pipeline interface.

______________________________________________________________________

## Pipeline CLI

`pipeline/cli.py` provides a few entry points using `uv run -m`:

- `init-from-markdown` read all markdown for a given profile, create or update the hypergraph in the SQLite graph database
- `update-from-markdown` incremental update for an existing hypergraph
- `export-sqlite` optional step that reads from PostgreSQL and writes a new `app/db/data.db` snapshot

Example commands:

```bash
# initialize hypergraph from markdown
uv run -m pipeline.cli init-from-markdown --profile profile

# update an existing hypergraph
uv run -m pipeline.cli update-from-markdown --profile profile

# export runtime SQLite snapshot for the backend
uv run -m pipeline.cli export-sqlite --profile profile
```

The CLI can start as stubs that log what they would do, then be filled in gradually.

______________________________________________________________________

## LinkedIn based tutorial

To make the system instantly relatable, there is a LinkedIn based tutorial in `tutorials/linkedin/`.

The flow is:

1. User exports or saves a copy of their LinkedIn profile page and places it as `tutorials/linkedin/profile.html` (or similar).
1. `linkedin_bootstrap.py` parses that file and generates a set of markdown files under `knowledge/profile/` (jobs, companies, skills).
1. The user runs `init-from-markdown` for that profile.
1. The hypergraph in the SQLite database now reflects their career path, and a new app/db/data.db snapshot can be exported for the backend.

Example:

```bash
# from repo root

uv run -m tutorials.linkedin.linkedin_bootstrap \
  --input tutorials/linkedin/profile.html \
  --out knowledge/profile

uv run -m pipeline.cli init-from-markdown --profile profile

uv run -m pipeline.cli export-sqlite --profile profile
```

After this, the backend runtime has:

- a `data.db` snapshot generated from the user’s own profile,
- a SQLite hypergraph database that can be explored and updated via markdown edits and pipeline runs

______________________________________________________________________

## Where this fits in the project

- `docs/index.md` gives the high level architecture
- `docs/backend.md` covers the runtime FastAPI and SQLite snapshot
- `docs/pipeline.md` (this file) explains how data gets into the SQLite hypergraph and the runtime database
- `.vibe/API_SPEC.md` and `.vibe/INFRA_NOTES.md` capture deeper design considerations and contracts for AI assistants

The pipeline is optional. If you ignore it, the starter still works with the existing SQLite file. If you use it, you get a repeatable and AI assisted way to maintain a hypergraph knowledge base behind the minimal runtime.
