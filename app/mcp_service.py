from __future__ import annotations

import logging
import sqlite3
from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import grpc

from . import mcp_pb2, mcp_pb2_grpc

logger = logging.getLogger("mcp.grpc")


@dataclass
class QueryOptions:
    limit: int = 10
    expand_neighbors: bool = False
    neighbor_budget: int = 0


def _row_to_node(row: sqlite3.Row) -> Any:
    # mypy: generated module has dynamic attributes
    return mcp_pb2.Node(  # type: ignore[attr-defined]
        id=row["id"],
        type=row["type"],
        data=mcp_pb2.Json(raw=row["data"] or "{}"),  # type: ignore[attr-defined]
    )


class McpService(mcp_pb2_grpc.McpServiceServicer):
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    async def Query(self, request: Any, context: grpc.aio.ServicerContext) -> AsyncIterator[Any]:
        # Very simple baseline: search nodes by LIKE on JSON data
        limit = request.limit or 10
        # opts retained for future expansion (neighbors/FTS), avoid unused for now
        try:
            conn = self._connect()
            cur = conn.cursor()
            cur.execute(
                "SELECT id, type, json(data) as data FROM nodes WHERE json(data) LIKE ? LIMIT ?",
                (f"%{request.query}%", limit),
            )
            nodes = [_row_to_node(r) for r in cur.fetchall()]
            # For now, do not expand neighbors; that is a later optimization
            # mypy: generated module has dynamic attributes
            yield mcp_pb2.QueryResult(nodes=nodes)  # type: ignore[attr-defined]
        except Exception as exc:  # pragma: no cover - mapped to gRPC status
            logger.exception("grpc_query_error")
            await context.abort(grpc.StatusCode.INTERNAL, str(exc))
        finally:
            try:
                conn.close()
            except Exception:
                pass

    async def UpsertNodes(self, request: Any, context: grpc.aio.ServicerContext) -> Any:
        try:
            conn = self._connect()
            cur = conn.cursor()
            for n in request.nodes:
                cur.execute(
                    """
                    INSERT INTO nodes (id, type, data)
                    VALUES (?, ?, json(?))
                    ON CONFLICT(id) DO UPDATE SET
                        type = excluded.type,
                        data = excluded.data
                    """,
                    (n.id, n.type, n.data.raw or "{}"),
                )
            conn.commit()
            # mypy: generated module has dynamic attributes
            return mcp_pb2.Ack(  # type: ignore[attr-defined]
                ok=True, message=f"upserted {len(request.nodes)} nodes"
            )
        except Exception as exc:  # pragma: no cover
            logger.exception("grpc_upsert_nodes_error")
            await context.abort(grpc.StatusCode.INTERNAL, str(exc))
        finally:
            try:
                conn.close()
            except Exception:
                pass


async def serve_grpc(
    db_path: Path, host: str = "0.0.0.0", port: int = 50051
) -> tuple[grpc.aio.Server, int]:
    server = grpc.aio.server()
    mcp_pb2_grpc.add_McpServiceServicer_to_server(McpService(db_path), server)
    bound_port = server.add_insecure_port(f"{host}:{port}")
    await server.start()
    logger.info("grpc_server_started", extra={"host": host, "port": bound_port})
    return server, bound_port
