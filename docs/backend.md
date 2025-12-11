# Backend: FastAPI, gRPC MCP and SQLite

The backend is a small Python service that

- exposes a gRPC MCP service for tools and agents
- exposes a thin HTTP JSON facade for the static site and simple clients
- reads from a local SQLite database baked into the container image

Everything lives under `app/` and is designed to run on Google Cloud Run and locally via uv.

______________________________________________________________________

## Layout of the backend

```text
app/
  main.py          FastAPI app entry point, wiring, HTTP JSON routes
  mcp_service.py   gRPC MCP service implementation (async, grpc.aio)
  db/
    data.db        SQLite database (read heavy)
```

You can keep everything in `main.py` at first, then split into modules as the project grows.

Key ideas

- gRPC defines the canonical MCP API
- HTTP JSON endpoints are a thin wrapper on top of the gRPC calls
- SQLite file is read only or read mostly in production

See `.vibe/API_SPEC.md` for the exact request and response shapes.

______________________________________________________________________

## FastAPI app and HTTP JSON facade

`app/main.py` creates a FastAPI instance and defines simple routes:

- `GET /health` returns a small status object
- `POST /mcp/query` accepts a JSON body with a single `query` field and returns a list of results

Minimal pattern:

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
from .db_utils import query_documents  # optional helper

logger = logging.getLogger("mcp")

app = FastAPI(title="FastMCP API")


class QueryRequest(BaseModel):
    query: str


class QueryResult(BaseModel):
    id: int
    content: str


class QueryResponse(BaseModel):
    results: list[QueryResult]


@app.get("/health")
def health():
    return {"status": "ok", "version": "0.1.0"}


@app.post("/mcp/query", response_model=QueryResponse)
def mcp_query(payload: QueryRequest):
    logger.info("mcp_query_start", extra={"query": payload.query})
    try:
        rows = query_documents(payload.query)
        logger.info("mcp_query_ok", extra={"result_count": len(rows)})
        return QueryResponse(results=[QueryResult(**row) for row in rows])
    except Exception:
        logger.exception("mcp_query_error")
        raise HTTPException(status_code=500, detail="Internal error")
```

The HTTP handler should stay small and delegate to the MCP service or a shared query function.

______________________________________________________________________

## gRPC MCP service

The gRPC MCP service is the internal backbone for tools and agent clients.

Typical layout:

```text
app/
  proto/
    mcp.proto      gRPC service and messages
  mcp_service.py   Python implementation generated from proto
```

Proto sketch (simplified excerpt, full in `proto/mcp.proto`):

```proto
service McpService {
  rpc Query(QueryRequest) returns (QueryResponse);
}

message QueryRequest {
  string query = 1;
}

message QueryResult {
  int64 id = 1;
  string content = 2;
}

message QueryResponse {
  repeated QueryResult results = 1;
}
```

Implementation notes:

- keep the business logic in shared helpers used by both gRPC and HTTP
- HTTP JSON handlers should call the same query method that the gRPC handler uses
- proto code generation is wired via `make proto` (grpcio‑tools)
- generated files are excluded from lint and coverage
 
Enable local gRPC alongside FastAPI by setting `START_GRPC=true` and optionally `GRPC_PORT`.
- follow `.vibe/API_SPEC.md` so JSON and gRPC stay consistent

If you run gRPC and HTTP in the same process, ensure the server supports HTTP 2 for gRPC while still serving HTTP 1.1 JSON routes. Cloud Run can do this with a gRPC capable server stack.

______________________________________________________________________

## SQLite database and query timing

The SQLite file lives at `app/db/data.db` inside the image. The main goals are:

- keep reads fast and predictable
- avoid external state for small deployments
- make schema changes and data updates via a new image build

Basic connection pattern:

```python
import sqlite3
import time
import logging
from pathlib import Path

logger = logging.getLogger("mcp")
DB_PATH = Path(__file__).parent / "db" / "data.db"


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def query_documents(term: str):
    start = time.perf_counter()
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, content FROM documents WHERE content LIKE ? LIMIT 10",
            (f"%{term}%",),
        )
        rows = [dict(row) for row in cur.fetchall()]
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "db_query",
            extra={"elapsed_ms": round(elapsed_ms, 2), "row_count": len(rows)},
        )
        return rows
    finally:
        conn.close()
```

Good practices:

- open a fresh connection per request for low traffic setups
- use `row_factory = sqlite3.Row` so results can be converted to dicts easily
- create indexes that match your query patterns in the build step that generates `data.db`

______________________________________________________________________

## Logging and health

Observability is intentionally minimal and based on Cloud Run logging and metrics.

Guidelines:

- use the `mcp` logger for all app logs
- log an INFO line when a request starts and when it completes
- log an ERROR with `logger.exception` when a request fails
- include a few business fields in `extra` (for example `result_count`, `elapsed_ms`) so Cloud Logging filters and simple charts are easy

Health endpoints:

- `/health` returns a small object with `status` and `version`
- you can later add `/ready` if you need more detailed readiness checks

______________________________________________________________________

## Docker and runtime expectations

The backend runs in a Python container on Cloud Run, listening on port `8080`.

Typical Dockerfile outline:

```dockerfile
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir uv \
 && uv pip install --system -r requirements.txt

COPY app ./app

ENV PORT=8080
EXPOSE 8080

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

Key points:

- dependencies are installed with uv using `requirements.txt`
- `uv run uvicorn ...` is used both locally and in the container
- Cloud Run sets `PORT`, but the default `8080` works for local dev

______________________________________________________________________

## Local development

For backend only development:

```bash
uv venv
uv pip install -r requirements.txt
uv run uvicorn app.main:app --reload
```

Then:

- open `http://localhost:8000/health` to check the service
- test `POST /mcp/query` with `curl` or a small client
- run gRPC clients against the gRPC endpoint if you expose one locally

See `docs/dev-env.md` for tests, type checking and linters when those are in place.

______________________________________________________________________

## Where to look next

- API contracts and expectations
  `.vibe/API_SPEC.md`

- Overall architecture and flows
  `docs/index.md` and `.vibe/ARCHITECTURE.md`

- Infra and deployment
  `docs/infra.md` and `.vibe/INFRA_NOTES.md`
