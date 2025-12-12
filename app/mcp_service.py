from __future__ import annotations

import json as _json
import logging
import sqlite3
from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import grpc

from . import mcp_pb2, mcp_pb2_grpc
from .query import QueryOpts, run_query

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

    async def Health(self, request: Any, context: grpc.aio.ServicerContext) -> Any:
        try:
            # Simple check: try to open a connection and query sqlite version
            conn = self._connect()
            conn.execute("SELECT sqlite_version()")
            return mcp_pb2.HealthStatus(ok=True, message="ok")  # type: ignore[attr-defined]
        except Exception as exc:  # pragma: no cover
            return mcp_pb2.HealthStatus(ok=False, message=str(exc))  # type: ignore[attr-defined]
        finally:
            try:
                conn.close()
            except Exception:
                pass

    async def Query(self, request: Any, context: grpc.aio.ServicerContext) -> AsyncIterator[Any]:
        # Very simple baseline: search nodes by LIKE on JSON data
        limit = request.limit or 10
        # opts retained for future expansion (neighbors/FTS), avoid unused for now
        try:
            conn = self._connect()
            result = run_query(
                conn,
                QueryOpts(
                    term=str(request.query or ""),
                    limit=limit,
                    expand_neighbors=bool(getattr(request, "expand_neighbors", False)),
                    neighbor_budget=int(getattr(request, "neighbor_budget", 0) or 0),
                ),
            )
            pb2_any: Any = mcp_pb2
            nodes = [
                pb2_any.Node(
                    id=n["id"], type=n["type"], data=pb2_any.Json(raw=_json.dumps(n["data"]))
                )
                for n in result["nodes"]
            ]
            edges = [
                pb2_any.Edge(
                    id=e["id"],
                    type=e["type"],
                    source=e["source"],
                    target=e["target"],
                    data=pb2_any.Json(raw=_json.dumps(e["data"])),
                )
                for e in result["edges"]
            ]
            yield pb2_any.QueryResult(nodes=nodes, edges=edges)
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

    async def UpsertEdges(self, request: Any, context: grpc.aio.ServicerContext) -> Any:
        try:
            conn = self._connect()
            cur = conn.cursor()
            for e in request.edges:
                cur.execute(
                    """
                    INSERT INTO edges (id, type, source, target, data)
                    VALUES (?, ?, ?, ?, json(?))
                    ON CONFLICT(id) DO UPDATE SET
                        type   = excluded.type,
                        source = excluded.source,
                        target = excluded.target,
                        data   = excluded.data
                    """,
                    (e.id, e.type, e.source, e.target, e.data.raw or "{}"),
                )
            conn.commit()
            return mcp_pb2.Ack(  # type: ignore[attr-defined]
                ok=True, message=f"upserted {len(request.edges)} edges"
            )
        except Exception as exc:  # pragma: no cover
            logger.exception("grpc_upsert_edges_error")
            await context.abort(grpc.StatusCode.INTERNAL, str(exc))
        finally:
            try:
                conn.close()
            except Exception:
                pass

    async def UpsertHyperedges(self, request: Any, context: grpc.aio.ServicerContext) -> Any:
        try:
            conn = self._connect()
            cur = conn.cursor()
            for he in request.hyperedges:
                cur.execute(
                    """
                    INSERT INTO hyperedges (id, type, data)
                    VALUES (?, ?, json(?))
                    ON CONFLICT(id) DO UPDATE SET
                        type = excluded.type,
                        data = excluded.data
                    """,
                    (he.id, he.type, he.data.raw or "{}"),
                )
                for p in he.participants:
                    cur.execute(
                        """
                        INSERT INTO hyperedge_entities (
                            hyperedge_id, entity_id, role, ordinal, data
                        )
                        VALUES (?, ?, ?, ?, json(?))
                        ON CONFLICT(hyperedge_id, entity_id, role, ordinal) DO UPDATE SET
                            data = excluded.data
                        """,
                        (
                            he.id,
                            p.entity_id,
                            p.role or "",
                            int(getattr(p, "ordinal", 0) or 0),
                            (
                                p.data.raw
                                if getattr(p, "data", None) and hasattr(p.data, "raw")
                                else "{}"
                            ),
                        ),
                    )
            conn.commit()
            return mcp_pb2.Ack(  # type: ignore[attr-defined]
                ok=True, message=f"upserted {len(request.hyperedges)} hyperedges"
            )
        except Exception as exc:  # pragma: no cover
            logger.exception("grpc_upsert_hyperedges_error")
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
