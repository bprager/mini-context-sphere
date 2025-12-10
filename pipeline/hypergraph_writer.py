from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

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


class HypergraphWriter:
    """Tiny wrapper around a SQLite based hypergraph.

    This uses simple nodes and edges tables as a base. You can later extend
    this to use a SQLite graph extension and richer schema.
    """

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._conn: sqlite3.Connection | None = None

    def __enter__(self) -> "HypergraphWriter":
        self._conn = sqlite3.connect(self.db_path)
        self._conn.execute("PRAGMA foreign_keys = ON;")
        # If you use a graph extension, load it here:
        # self._conn.enable_load_extension(True)
        # self._conn.load_extension("mod_graph")  # example name
        self._ensure_schema()
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
        self.conn.commit()

    def upsert_node(self, node: Node) -> None:
        logger.info(
            "upsert_node", extra={"id": node.id, "type": node.type}
        )
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
        for node in nodes:
            self.upsert_node(node)

    def upsert_edges(self, edges: Iterable[Edge]) -> None:
        for edge in edges:
            self.upsert_edge(edge)


def json_dumps(data: dict[str, Any]) -> str:
    # Avoid adding a hard dependency on orjson here, plain json is fine.
    import json

    return json.dumps(data, ensure_ascii=False)

