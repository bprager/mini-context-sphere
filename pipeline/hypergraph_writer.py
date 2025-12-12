from __future__ import annotations

import logging
import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger("pipeline.hypergraph")


@dataclass
class Node:
    id: str
    type: str
    data: dict[str, Any]


@dataclass
class Edge:
    id: str
    type: str
    source: str
    target: str
    data: dict[str, Any]


@dataclass
class HyperedgeParticipant:
    entity_id: str
    role: str = ""
    ordinal: int = 0
    data: dict[str, Any] | None = None


@dataclass
class Hyperedge:
    id: str
    type: str
    data: dict[str, Any]
    participants: list[HyperedgeParticipant] = field(default_factory=list)


class HypergraphWriter:
    """Tiny wrapper around a SQLite based hypergraph.

    This uses simple nodes and edges tables as a base. You can later extend
    this to use a SQLite graph extension and richer schema.
    """

    def __init__(self, db_path: Path, *, build_mode: bool = False) -> None:
        self.db_path = db_path
        self.build_mode = build_mode
        self._conn: sqlite3.Connection | None = None

    def __enter__(self) -> HypergraphWriter:
        self._conn = sqlite3.connect(self.db_path)
        self._conn.execute("PRAGMA foreign_keys = ON;")
        if self.build_mode:
            # Speed up batch ingestion while keeping durability reasonable.
            self._conn.execute("PRAGMA journal_mode=WAL;")
            self._conn.execute("PRAGMA synchronous=NORMAL;")
            self._conn.execute("PRAGMA temp_store=MEMORY;")
        # If you use a graph extension, load it here:
        # self._conn.enable_load_extension(True)
        # self._conn.load_extension("mod_graph")  # example name
        self._ensure_schema()
        if self.build_mode:
            self.ensure_indexes()
        logger.info("hypergraph_opened", extra={"db_path": str(self.db_path)})
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._conn is not None:
            if exc is None:
                self._conn.commit()
            else:
                self._conn.rollback()
            self._conn.close()
            logger.info("hypergraph_closed", extra={"db_path": str(self.db_path)})
        self._conn = None

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            raise RuntimeError("HypergraphWriter must be used as a context manager")
        return self._conn

    def _ensure_schema(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS nodes (
                id    TEXT PRIMARY KEY,
                type  TEXT NOT NULL,
                data  TEXT
            );
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS edges (
                id      TEXT PRIMARY KEY,
                type    TEXT NOT NULL,
                source  TEXT NOT NULL,
                target  TEXT NOT NULL,
                data    TEXT,
                FOREIGN KEY (source) REFERENCES nodes(id) ON DELETE CASCADE,
                FOREIGN KEY (target) REFERENCES nodes(id) ON DELETE CASCADE
            );
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS hyperedges (
                id    TEXT PRIMARY KEY,
                type  TEXT NOT NULL,
                data  TEXT
            );
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS hyperedge_entities (
                hyperedge_id TEXT NOT NULL,
                entity_id    TEXT NOT NULL,
                role         TEXT NOT NULL DEFAULT '',
                ordinal      INTEGER NOT NULL DEFAULT 0,
                data         TEXT,
                PRIMARY KEY (hyperedge_id, entity_id, role, ordinal),
                FOREIGN KEY (hyperedge_id) REFERENCES hyperedges(id) ON DELETE CASCADE,
                FOREIGN KEY (entity_id) REFERENCES nodes(id) ON DELETE CASCADE
            );
            """
        )
        self.conn.commit()

    def ensure_indexes(self) -> None:
        """Create useful indexes for query performance (idempotent)."""
        cur = self.conn.cursor()
        cur.execute("CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(type);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target);")
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_he_by_hyperedge ON hyperedge_entities(hyperedge_id);"
        )
        cur.execute("CREATE INDEX IF NOT EXISTS idx_he_by_entity ON hyperedge_entities(entity_id);")
        self.conn.commit()

    def upsert_node(self, node: Node) -> None:
        logger.info("upsert_node", extra={"id": node.id, "type": node.type})
        self.conn.execute(
            """
            INSERT INTO nodes (id, type, data)
            VALUES (?, ?, json(?))
            ON CONFLICT(id) DO UPDATE SET
                type = excluded.type,
                data = excluded.data;
            """,
            (node.id, node.type, json_dumps(node.data)),
        )

    def upsert_edge(self, edge: Edge) -> None:
        logger.info(
            "upsert_edge",
            extra={
                "id": edge.id,
                "type": edge.type,
                "source": edge.source,
                "target": edge.target,
            },
        )
        self.conn.execute(
            """
            INSERT INTO edges (id, type, source, target, data)
            VALUES (?, ?, ?, ?, json(?))
            ON CONFLICT(id) DO UPDATE SET
                type   = excluded.type,
                source = excluded.source,
                target = excluded.target,
                data   = excluded.data;
            """,
            (edge.id, edge.type, edge.source, edge.target, json_dumps(edge.data)),
        )

    def upsert_nodes(self, nodes: Iterable[Node]) -> None:
        batch = [(n.id, n.type, json_dumps(n.data)) for n in nodes]
        if not batch:
            return
        self.conn.executemany(
            """
            INSERT INTO nodes (id, type, data)
            VALUES (?, ?, json(?))
            ON CONFLICT(id) DO UPDATE SET
                type = excluded.type,
                data = excluded.data;
            """,
            batch,
        )

    def upsert_edges(self, edges: Iterable[Edge]) -> None:
        batch = [(e.id, e.type, e.source, e.target, json_dumps(e.data)) for e in edges]
        if not batch:
            return
        self.conn.executemany(
            """
            INSERT INTO edges (id, type, source, target, data)
            VALUES (?, ?, ?, ?, json(?))
            ON CONFLICT(id) DO UPDATE SET
                type   = excluded.type,
                source = excluded.source,
                target = excluded.target,
                data   = excluded.data;
            """,
            batch,
        )

    def upsert_hyperedge(self, hyperedge: Hyperedge) -> None:
        logger.info("upsert_hyperedge", extra={"id": hyperedge.id, "type": hyperedge.type})
        self.conn.execute(
            """
            INSERT INTO hyperedges (id, type, data)
            VALUES (?, ?, json(?))
            ON CONFLICT(id) DO UPDATE SET
                type = excluded.type,
                data = excluded.data;
            """,
            (hyperedge.id, hyperedge.type, json_dumps(hyperedge.data)),
        )
        if hyperedge.participants:
            part_batch = [
                (
                    hyperedge.id,
                    p.entity_id,
                    p.role or "",
                    int(p.ordinal or 0),
                    json_dumps(p.data or {}),
                )
                for p in hyperedge.participants
            ]
            self.conn.executemany(
                """
                INSERT INTO hyperedge_entities (hyperedge_id, entity_id, role, ordinal, data)
                VALUES (?, ?, ?, ?, json(?))
                ON CONFLICT(hyperedge_id, entity_id, role, ordinal) DO UPDATE SET
                    data = excluded.data;
                """,
                part_batch,
            )

    def upsert_hyperedges(self, hyperedges: Iterable[Hyperedge]) -> None:
        for he in hyperedges:
            self.upsert_hyperedge(he)

    def finalize_fts(self) -> None:
        """Create and backfill FTS indexes for text search on nodes."""
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS nodes_fts
            USING fts5(id, content, tokenize='porter');
            """
        )
        # Full refresh
        cur.execute("DELETE FROM nodes_fts;")
        cur.execute(
            """
            INSERT INTO nodes_fts (id, content)
            SELECT id,
                   coalesce(json_extract(data, '$.name'), '') || ' ' ||
                   coalesce(json_extract(data, '$.about'), '') || ' ' ||
                   type
            FROM nodes;
            """
        )
        # Keep in sync after build
        cur.execute(
            """
            CREATE TRIGGER IF NOT EXISTS nodes_ai AFTER INSERT ON nodes BEGIN
                INSERT INTO nodes_fts (id, content)
                VALUES (
                  NEW.id,
                  coalesce(json_extract(NEW.data, '$.name'), '') || ' ' ||
                  coalesce(json_extract(NEW.data, '$.about'), '') || ' ' ||
                  NEW.type
                );
            END;
            """
        )
        cur.execute(
            """
            CREATE TRIGGER IF NOT EXISTS nodes_au AFTER UPDATE ON nodes BEGIN
                DELETE FROM nodes_fts WHERE id = OLD.id;
                INSERT INTO nodes_fts (id, content)
                VALUES (
                  NEW.id,
                  coalesce(json_extract(NEW.data, '$.name'), '') || ' ' ||
                  coalesce(json_extract(NEW.data, '$.about'), '') || ' ' ||
                  NEW.type
                );
            END;
            """
        )
        cur.execute(
            """
            CREATE TRIGGER IF NOT EXISTS nodes_ad AFTER DELETE ON nodes BEGIN
                DELETE FROM nodes_fts WHERE id = OLD.id;
            END;
            """
        )
        self.conn.commit()


def json_dumps(data: dict[str, Any]) -> str:
    # Avoid adding a hard dependency on orjson here, plain json is fine.
    import json

    return json.dumps(data, ensure_ascii=False)
