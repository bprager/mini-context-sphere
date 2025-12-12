import sqlite3
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("grpc")


@pytest.mark.asyncio
async def test_grpc_query_basic(tmp_path: Path):
    # Prepare DB
    db_path = tmp_path / "data.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE nodes (id TEXT PRIMARY KEY, type TEXT, data TEXT)")
    conn.execute(
        "INSERT INTO nodes (id, type, data) VALUES (?, ?, json(?))",
        ("n1", "Person", '{"name": "Alice", "about": "hello world"}'),
    )
    conn.commit()
    conn.close()

    # Start gRPC server
    from app.mcp_service import serve_grpc

    server, port = await serve_grpc(db_path, host="127.0.0.1", port=0)

    import grpc
    from app import mcp_pb2, mcp_pb2_grpc

    pb2: Any = mcp_pb2  # satisfy mypy: generated module attributes are dynamic
    Stub: Any = mcp_pb2_grpc.McpServiceStub

    async with grpc.aio.insecure_channel(f"127.0.0.1:{port}") as channel:
        stub = Stub(channel)
        req = pb2.QueryRequest(query="hello", limit=5)
        results = []
        async for chunk in stub.Query(req):
            results.extend(chunk.nodes)
        assert any("hello" in (n.data.raw or "") for n in results)

    await server.stop(0)


@pytest.mark.asyncio
async def test_grpc_upserts(tmp_path: Path):
    # Prepare DB
    db_path = tmp_path / "data.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE nodes (id TEXT PRIMARY KEY, type TEXT, data TEXT)")
    conn.execute(
        "CREATE TABLE edges (id TEXT PRIMARY KEY, type TEXT, source TEXT, target TEXT, data TEXT)"
    )
    conn.execute("CREATE TABLE hyperedges (id TEXT PRIMARY KEY, type TEXT, data TEXT)")
    conn.execute(
        """
        CREATE TABLE hyperedge_entities (
            hyperedge_id TEXT NOT NULL,
            entity_id    TEXT NOT NULL,
            role         TEXT NOT NULL DEFAULT '',
            ordinal      INTEGER NOT NULL DEFAULT 0,
            data         TEXT,
            PRIMARY KEY (hyperedge_id, entity_id, role, ordinal)
        )
        """
    )
    conn.commit()
    conn.close()

    # Start gRPC server
    from app.mcp_service import serve_grpc

    server, port = await serve_grpc(db_path, host="127.0.0.1", port=0)

    import grpc
    from app import mcp_pb2 as pb2
    from app import mcp_pb2_grpc as pb2_grpc

    pb2_any: Any = pb2

    async with grpc.aio.insecure_channel(f"127.0.0.1:{port}") as channel:
        stub = pb2_grpc.McpServiceStub(channel)
        # Upsert nodes
        ack1 = await stub.UpsertNodes(
            pb2_any.UpsertNodesRequest(
                nodes=[
                    pb2_any.Node(id="n1", type="Person", data=pb2_any.Json(raw='{"name":"Alice"}')),
                    pb2_any.Node(
                        id="n2", type="Organization", data=pb2_any.Json(raw='{"name":"Acme"}')
                    ),
                ]
            )
        )
        assert ack1.ok
        # Upsert edges
        ack2 = await stub.UpsertEdges(
            pb2_any.UpsertEdgesRequest(
                edges=[
                    pb2_any.Edge(
                        id="e1",
                        type="Employment",
                        source="n1",
                        target="n2",
                        data=pb2_any.Json(raw='{"title":"Engineer"}'),
                    )
                ]
            )
        )
        assert ack2.ok
        # Upsert hyperedges
        ack3 = await stub.UpsertHyperedges(
            pb2_any.UpsertHyperedgesRequest(
                hyperedges=[
                    pb2_any.Hyperedge(
                        id="he1",
                        type="Employment",
                        data=pb2_any.Json(raw='{"title":"Engineer"}'),
                        participants=[
                            pb2_any.HyperedgeEntity(entity_id="n1", role="subject", ordinal=0),
                            pb2_any.HyperedgeEntity(entity_id="n2", role="employer", ordinal=0),
                        ],
                    )
                ]
            )
        )
        assert ack3.ok

    await server.stop(0)


@pytest.mark.asyncio
async def test_grpc_health(tmp_path: Path):
    db_path = tmp_path / "h.db"
    db_path.touch()
    from app.mcp_service import serve_grpc

    server, port = await serve_grpc(db_path, host="127.0.0.1", port=0)
    import grpc
    from app import mcp_pb2 as pb2
    from app import mcp_pb2_grpc as pb2_grpc

    async with grpc.aio.insecure_channel(f"127.0.0.1:{port}") as channel:
        stub = pb2_grpc.McpServiceStub(channel)
        hs = await stub.Health(pb2.HealthRequest())  # type: ignore[attr-defined]
        assert hs.ok

    await server.stop(0)
