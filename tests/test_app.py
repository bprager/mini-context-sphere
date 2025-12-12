import importlib
import sqlite3
from pathlib import Path

import pytest


def make_temp_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "data.db"
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("CREATE TABLE nodes (id TEXT PRIMARY KEY, type TEXT, data TEXT)")
        conn.execute(
            "INSERT INTO nodes (id, type, data) VALUES (?, ?, json(?))",
            ("n1", "Doc", '{"name": "hello world"}'),
        )
        conn.execute(
            "INSERT INTO nodes (id, type, data) VALUES (?, ?, json(?))",
            ("n2", "Doc", '{"name": "another doc"}'),
        )
        conn.commit()
    finally:
        conn.close()
    return db_path


def _get_testclient():
    # Ensure httpx dependency is present; otherwise skip these API tests
    pytest.importorskip("httpx")
    try:
        mod = importlib.import_module("fastapi.testclient")
        return mod.TestClient
    except Exception:  # pragma: no cover - fallback
        mod = importlib.import_module("starlette.testclient")
        return mod.TestClient


def test_health_ok(tmp_path: Path):
    # Import after patching DB path for isolation
    from app import main as app_main

    TestClient = _get_testclient()
    client = TestClient(app_main.app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json().get("status") == "ok"


def test_mcp_query_returns_results(tmp_path: Path):
    from app import main as app_main

    # Point the app at a temporary DB with a documents table
    db_path = make_temp_db(tmp_path)
    app_main.DB_PATH = db_path

    TestClient = _get_testclient()
    client = TestClient(app_main.app)

    # Query that matches a row
    resp = client.post("/mcp/query", json={"query": "hello"})
    assert resp.status_code == 200
    data = resp.json()
    assert "nodes" in data
    assert isinstance(data["nodes"], list)
    assert any("hello" in n["data"].get("name", "") for n in data["nodes"])  # one row matches


def test_mcp_query_no_match_and_error(tmp_path: Path):
    from app import main as app_main

    # DB with table but no match
    db_path = make_temp_db(tmp_path)
    app_main.DB_PATH = db_path
    TestClient = _get_testclient()
    client = TestClient(app_main.app)

    resp = client.post("/mcp/query", json={"query": "zzz-not-found"})
    assert resp.status_code == 200
    assert resp.json()["nodes"] == []

    # Point to a DB with missing table to exercise error path
    bad_db = tmp_path / "empty.db"
    bad_conn = sqlite3.connect(bad_db)
    bad_conn.close()
    app_main.DB_PATH = bad_db
    resp2 = client.post("/mcp/query", json={"query": "anything"})
    # Depending on SQLite error, FastAPI returns 500 with error detail
    assert resp2.status_code == 500


def test_connect_and_health_direct(tmp_path: Path):
    from app import main as app_main

    # Prepare empty SQLite file, just to open/close
    db_path = tmp_path / "simple.db"
    db_path.touch()
    app_main.DB_PATH = db_path

    # connect() returns a connection with row_factory set
    conn = app_main.connect()
    try:
        import sqlite3 as _sqlite3

        assert conn.row_factory is _sqlite3.Row
    finally:
        conn.close()

    # Directly call health() to exercise the function body
    out = app_main.health()
    assert out.get("status") == "ok"


def test_mcp_query_direct_success(tmp_path: Path):
    from app import main as app_main

    # DB with match
    db_path = make_temp_db(tmp_path)
    app_main.DB_PATH = db_path

    result = app_main.mcp_query(app_main.Query(query="hello")).model_dump()
    assert "nodes" in result and isinstance(result["nodes"], list)
    assert any("hello" in n["data"].get("name", "") for n in result["nodes"])


def test_mcp_query_direct_error(tmp_path: Path):
    from app import main as app_main

    # DB exists but missing required table triggers error path
    bad_db = tmp_path / "bad.db"
    bad_db.touch()
    app_main.DB_PATH = bad_db
    from fastapi import HTTPException

    with pytest.raises(HTTPException):
        app_main.mcp_query(app_main.Query(query="anything"))
