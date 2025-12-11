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
