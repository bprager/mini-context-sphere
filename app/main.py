# AI assistants: see .vibe/AI_DEV_INSTRUCTIONS.md and .vibe/API_SPEC.md

import logging
import os
import sqlite3
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

LOGGER_NAME = "mcp"
DEFAULT_LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


def get_logger(name=LOGGER_NAME, level=DEFAULT_LOG_LEVEL):
    """
    Returns a configured logger with the specified name and level.
    Ensures handlers are not duplicated and applies a consistent formatter.
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level, logging.INFO))

    # Prevent adding multiple handlers if already configured
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False  # Prevent double logging if root logger is configured

    return logger


logger = get_logger()

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
    conn = None
    try:
        conn = connect()
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
        if conn:
            try:
                conn.close()
            except Exception:
                pass
    logger.info("mcp_query_ok", extra={"result_count": len(rows)})
    return QueryResponse(results=[QueryResult(**row) for row in rows])
