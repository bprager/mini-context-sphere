import sqlite3
from pathlib import Path

from app.query import QueryOpts, run_query


def _setup_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "q.db"
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("CREATE TABLE nodes (id TEXT PRIMARY KEY, type TEXT, data TEXT)")
        conn.execute(
            "CREATE TABLE edges (\n"
            "  id TEXT PRIMARY KEY,\n"
            "  type TEXT,\n"
            "  source TEXT,\n"
            "  target TEXT,\n"
            "  data TEXT\n"
            ")"
        )
        conn.execute(
            "INSERT INTO nodes (id, type, data) VALUES (?, ?, json(?))",
            ("n1", "Person", '{"name": "Alice"}'),
        )
        conn.execute(
            "INSERT INTO nodes (id, type, data) VALUES (?, ?, json(?))",
            ("n2", "Person", '{"name": "Bob"}'),
        )
        conn.execute(
            "INSERT INTO edges (id, type, source, target, data) VALUES (?, ?, ?, ?, json(?))",
            ("e1", "Knows", "n1", "n2", '{"since": 2020}'),
        )
        conn.commit()
    finally:
        conn.close()
    return db_path


def test_run_query_without_neighbors(tmp_path: Path):
    db_path = _setup_db(tmp_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        result = run_query(conn, QueryOpts(term="Alice", limit=10, expand_neighbors=False))
        node_ids = {n["id"] for n in result["nodes"]}
        assert "n1" in node_ids
        assert "edges" in result and result["edges"] == []
    finally:
        conn.close()


def test_run_query_with_neighbors(tmp_path: Path):
    db_path = _setup_db(tmp_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        result = run_query(
            conn,
            QueryOpts(term="Alice", limit=10, expand_neighbors=True, neighbor_budget=10),
        )
        node_ids = {n["id"] for n in result["nodes"]}
        assert {"n1", "n2"}.issubset(node_ids)
        edges = {(e["id"], e["source"], e["target"]) for e in result["edges"]}
        assert ("e1", "n1", "n2") in edges
    finally:
        conn.close()
