# AI assistants: see .vibe/AI_DEV_INSTRUCTIONS.md and .vibe/API_SPEC.md

import logging
import sqlite3
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logger = logging.getLogger("mcp")
logger.setLevel(logging.INFO)

DB_PATH = Path(__file__).parent / "db" / "data.db"

app = FastAPI(title="FastMCP API")


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


class Query(BaseModel):
    query: str


class QueryResult(BaseModel):
    id: int
    content: str


class QueryResponse(BaseModel):
    results: list[QueryResult]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/mcp/query")
def mcp_query(payload: Query):
    logger.info("mcp_query_start", extra={"query": payload.query})
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, content FROM documents WHERE content LIKE ? LIMIT 10",
            (f"%{payload.query}%",),
        )
        rows = [dict(r) for r in cur.fetchall()]
    except Exception as exc:
        logger.exception("mcp_query_error")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        try:
            conn.close()
        except Exception:
            pass
    logger.info("mcp_query_ok", extra={"result_count": len(rows)})
    return QueryResponse(results=[QueryResult(**row) for row in rows])
