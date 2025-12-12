import sqlite3
from pathlib import Path
from typing import Any

import pytest


@pytest.mark.asyncio
async def test_http_grpc_query_parity(tmp_path: Path):
    # Prepare DB with two nodes and one edge
    db_path = tmp_path / "parity.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE nodes (id TEXT PRIMARY KEY, type TEXT, data TEXT)")
    conn.execute(
        "INSERT INTO nodes (id, type, data) VALUES (?, ?, json(?))",
        ("n1", "Person", '{"name": "Alice", "about": "hello world"}'),
    )
    conn.execute(
        "INSERT INTO nodes (id, type, data) VALUES (?, ?, json(?))",
        ("n2", "Person", '{"name": "Bob"}'),
    )
    conn.execute(
        "CREATE TABLE edges (id TEXT PRIMARY KEY, type TEXT, source TEXT, target TEXT, data TEXT)"
    )
    conn.execute(
        "INSERT INTO edges (id, type, source, target, data) VALUES (?, ?, ?, ?, json(?))",
        ("e1", "Knows", "n1", "n2", '{"since": 2020}'),
    )
    conn.commit()
    conn.close()

    # Import app and point to temp DB
    from app import main as app_main

    app_main.DB_PATH = db_path

    # HTTP call via FastAPI TestClient
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient

    http_client = TestClient(app_main.app)
    body = {
        "query": "Alice",
        "limit": 10,
        "expand_neighbors": True,
        "neighbor_budget": 10,
    }
    http_resp = http_client.post("/mcp/query", json=body)
    assert http_resp.status_code == 200
    http_data = http_resp.json()

    http_nodes = {n["id"] for n in http_data.get("nodes", [])}
    http_edges = {(e["id"], e.get("source"), e.get("target")) for e in http_data.get("edges", [])}

    # gRPC call against in-process server
    from app.mcp_service import serve_grpc

    server, port = await serve_grpc(db_path, host="127.0.0.1", port=0)
    import grpc
    from app import mcp_pb2, mcp_pb2_grpc

    pb2: Any = mcp_pb2  # generated module attributes are dynamic
    async with grpc.aio.insecure_channel(f"127.0.0.1:{port}") as channel:
        stub = mcp_pb2_grpc.McpServiceStub(channel)
        req = pb2.QueryRequest(query="Alice", limit=10, expand_neighbors=True, neighbor_budget=10)
        grpc_nodes: set[str] = set()
        grpc_edges: set[tuple[str, str, str]] = set()
        async for chunk in stub.Query(req):
            for n in chunk.nodes:
                grpc_nodes.add(n.id)
            for e in chunk.edges:
                grpc_edges.add((e.id, e.source, e.target))

    await server.stop(0)

    # Compare sets
    assert http_nodes == grpc_nodes
    assert http_edges == grpc_edges
