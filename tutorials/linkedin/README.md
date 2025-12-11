````md
# LinkedIn tutorial

Turn your LinkedIn profile into a small hypergraph plus a runtime SQLite snapshot used by the `/mcp/query` endpoint.

You will

- save your LinkedIn profile as HTML
- generate markdown for jobs, companies and skills
- build the SQLite hypergraph
- export a new `app/db/data.db`
- query it from a tiny HTML page

---

## 1. Prerequisites

- Python and `uv` installed
- This repo checked out
- Basic config via environment variables:

```bash
export HYPERGRAPH_DB_PATH="hypergraph.db"
export AI_PROVIDER="openai"      # or gemini or ollama
export AI_MODEL="gpt-4.1-mini"   # or your preferred model
export MARKDOWN_ROOT="knowledge"
export PROFILE_NAME="profile"
````

______________________________________________________________________

## 2. Save your LinkedIn profile as HTML

1. Open your LinkedIn profile in the browser.
1. Use "Save page as" and choose **Web page, HTML only**.
1. Rename the file to `profile.html`.
1. Put it here:

```text
tutorials/linkedin/profile.html
```

Do not export as PDF. The bootstrap script expects HTML.

______________________________________________________________________

## 3. Generate markdown from your profile

Run:

```bash
uv run -m tutorials.linkedin.linkedin_bootstrap \
  --input tutorials/linkedin/profile.html \
  --out knowledge/profile
```

This will

- parse your profile HTML
- create markdown under `knowledge/profile/...` for jobs, companies and skills

You can edit these files at any time.

______________________________________________________________________

## 4. Build or update the hypergraph

Use the LinkedIn tuned schema:

```bash
export SCHEMA_PATH="tutorials/linkedin/graph_schema.yaml"
```

Initial load:

```bash
uv run -m pipeline.cli init-from-markdown --profile profile
```

Later, after editing markdown:

```bash
uv run -m pipeline.cli update-from-markdown --profile profile
```

The pipeline reads markdown, applies the schema and writes nodes and hyperedges into the SQLite hypergraph database.

______________________________________________________________________

## 5. Export runtime SQLite snapshot

Refresh the runtime database used by the FastAPI backend:

```bash
uv run -m pipeline.cli export-sqlite --profile profile
```

This writes a new `app/db/data.db` snapshot.

______________________________________________________________________

## 6. Run the backend

For local testing:

```bash
uv venv
uv pip install -r requirements.txt
uv run uvicorn app.main:app --reload
```

Note the base URL:

- local: `http://localhost:8000`
- Cloud Run: the URL from Terraform outputs (`cloud_run_url`)

______________________________________________________________________

## 7. Try it from the browser

1. Save `tutorials/linkedin/demo.html` from this repo.
1. Open it in your browser.
1. Set `API_BASE` in the script to your backend URL.

Then ask questions like:

- `Which roles did I have at <Organization>?`
- `Which skills show up across all my jobs?`

The form sends a POST request to `/mcp/query` and shows the JSON response from your LinkedIn based hypergraph.

```
::contentReference[oaicite:0]{index=0}
```
