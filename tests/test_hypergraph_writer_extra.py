import sqlite3
from pathlib import Path

import pytest
from pipeline.hypergraph_writer import Edge, HypergraphWriter, Node


def test_writer_conn_property_outside_context_raises(tmp_path: Path):
    writer = HypergraphWriter(tmp_path / "x.db")
    with pytest.raises(RuntimeError):
        _ = writer.conn  # access without entering context


def test_writer_rollback_on_exception(tmp_path: Path):
    db_path = tmp_path / "hg.db"
    try:
        with HypergraphWriter(db_path) as writer:
            writer.upsert_node(Node(id="n1", type="Doc", data={"name": "x"}))
            # Force an exception to trigger rollback in __exit__
            raise RuntimeError("fail to trigger rollback")
    except RuntimeError:
        pass

    # Node should not be persisted due to rollback path
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute("SELECT COUNT(*) FROM nodes WHERE id='n1'")
        count = cur.fetchone()[0]
        assert count == 0
    finally:
        conn.close()


def test_writer_empty_batch_upserts_are_noops(tmp_path: Path):
    db_path = tmp_path / "hg2.db"
    with HypergraphWriter(db_path) as writer:
        # Should not raise
        writer.upsert_nodes([])
        writer.upsert_edges([])


def test_writer_finalize_fts_creates_fts_table(tmp_path: Path):
    db_path = tmp_path / "hg3.db"
    with HypergraphWriter(db_path) as writer:
        writer.upsert_node(Node(id="n1", type="Doc", data={"name": "hello", "about": "world"}))
        writer.finalize_fts()

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        # Ensure the FTS virtual table exists and has content for n1
        exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='nodes_fts'"
        ).fetchone()
        assert exists is not None
        row = conn.execute("SELECT id, content FROM nodes_fts WHERE id='n1'").fetchone()
        assert row is not None
        assert "hello" in row[1]
    finally:
        conn.close()


def test_writer_pragmas_error_path_is_ignored(monkeypatch, tmp_path: Path):
    # Patch sqlite3.connect to return a proxy connection that fails for a PRAGMA
    orig_connect = sqlite3.connect

    class ConnProxy:
        def __init__(self, real):
            self._real = real
            self._failed = False

        def execute(self, sql, *args, **kwargs):
            # Raise once when setting a PRAGMA to enter the except block
            if ("PRAGMA cache_size" in sql) and not self._failed:
                self._failed = True
                raise sqlite3.DatabaseError("simulated pragma failure")
            return self._real.execute(sql, *args, **kwargs)

        def cursor(self):
            return self._real.cursor()

        def commit(self):
            return self._real.commit()

        def rollback(self):
            return self._real.rollback()

        def close(self):
            return self._real.close()

        def __getattr__(self, name):
            return getattr(self._real, name)

    def patched_connect(path):  # type: ignore[no-untyped-def]
        return ConnProxy(orig_connect(path))

    monkeypatch.setattr(sqlite3, "connect", patched_connect)

    # Should not raise; except path in __enter__ swallows pragma errors
    with HypergraphWriter(tmp_path / "hg4.db") as writer:
        writer.upsert_node(Node(id="n1", type="Doc", data={}))
        writer.upsert_edge(Edge(id="e1", type="rel", source="n1", target="n1", data={}))
