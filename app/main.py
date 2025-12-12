"""FastAPI app and optional gRPC bootstrap.

AI assistants: see `.vibe/AI_DEV_INSTRUCTIONS.md` and `.vibe/API_SPEC.md`.
"""

import asyncio
import logging
import os
import sqlite3
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .query import QueryOpts, run_query

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
    limit: int = 10
    expand_neighbors: bool = False
    neighbor_budget: int = 0


class GraphNode(BaseModel):
    id: str
    type: str
    data: dict[str, Any]


class GraphEdge(BaseModel):
    id: str
    type: str
    source: str
    target: str
    data: dict[str, Any]


class GraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/mcp/query")
def mcp_query(payload: Query) -> GraphResponse:
    logger.info("mcp_query_start", extra={"query": payload.query})
    conn = None
    try:
        conn = connect()
        result = run_query(
            conn,
            QueryOpts(
                term=payload.query,
                limit=payload.limit,
                expand_neighbors=payload.expand_neighbors,
                neighbor_budget=payload.neighbor_budget,
            ),
        )
    except Exception as exc:
        logger.exception("mcp_query_error")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass
    logger.info(
        "mcp_query_ok",
        extra={
            "node_count": len(result.get("nodes", [])),
            "edge_count": len(result.get("edges", [])),
        },
    )
    return GraphResponse(
        nodes=[GraphNode(**n) for n in result.get("nodes", [])],
        edges=[GraphEdge(**e) for e in result.get("edges", [])],
    )


# Optional: start gRPC server when running under uvicorn, if enabled by env
_START_GRPC = os.getenv("START_GRPC", "false").lower() in {"1", "true", "yes"}
_GRPC_PORT = int(os.getenv("GRPC_PORT", "50051"))
if _START_GRPC:
    try:
        # Lazy import so running the HTTP app does not require grpcio unless enabled
        from .mcp_service import serve_grpc

        async def _start():
            await serve_grpc(DB_PATH, port=_GRPC_PORT)

        asyncio.get_event_loop().create_task(_start())
        logger.info("grpc_bootstrap", extra={"port": _GRPC_PORT})
    except Exception:  # pragma: no cover
        logger.exception("grpc_bootstrap_error")
