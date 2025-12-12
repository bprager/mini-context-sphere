import json
import sqlite3
from pathlib import Path

from pipeline.hypergraph_writer import (
    Edge,
    Hyperedge,
    HyperedgeParticipant,
    HypergraphWriter,
    Node,
)


def read_all(conn: sqlite3.Connection, table: str):
    return [dict(r) for r in conn.execute(f"SELECT * FROM {table}")]


def test_writer_creates_schema_and_upserts(tmp_path: Path):
    db_path = tmp_path / "hg.db"
    with HypergraphWriter(db_path) as writer:
        writer.upsert_node(Node(id="n1", type="Person", data={"name": "Alice"}))
        writer.upsert_node(Node(id="n2", type="Organization", data={"name": "Acme"}))
        writer.upsert_edge(
            Edge(
                id="e1",
                type="Employment",
                source="n1",
                target="n2",
                data={"title": "Engineer"},
            )
        )

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        nodes = read_all(conn, "nodes")
        edges = read_all(conn, "edges")
        assert len(nodes) == 2
        assert len(edges) == 1
        # Upsert edge and nodes again to ensure ON CONFLICT works
        with HypergraphWriter(db_path) as writer:
            writer.upsert_node(Node(id="n1", type="Person", data={"name": "Alice"}))
            writer.upsert_edge(
                Edge(
                    id="e1",
                    type="Employment",
                    source="n1",
                    target="n2",
                    data={"title": "Engineer"},
                )
            )
        # Update edge data and verify change persisted
        with HypergraphWriter(db_path) as writer:
            writer.upsert_edge(
                Edge(
                    id="e1",
                    type="Employment",
                    source="n1",
                    target="n2",
                    data={"title": "Senior Engineer"},
                )
            )
        data_row = conn.execute("SELECT data FROM edges WHERE id='e1'").fetchone()
        edge_data = json.loads(data_row[0]) if data_row and data_row[0] else {}
        assert edge_data.get("title") == "Senior Engineer"
    finally:
        conn.close()


def test_hyperedge_and_participants(tmp_path: Path):
    db_path = tmp_path / "hg2.db"
    with HypergraphWriter(db_path) as writer:
        # Create two entities
        writer.upsert_node(Node(id="p1", type="Person", data={"name": "Alice"}))
        writer.upsert_node(Node(id="o1", type="Organization", data={"name": "Acme"}))

        he = Hyperedge(
            id="he1",
            type="Employment",
            data={"title": "Engineer"},
            participants=[
                HyperedgeParticipant(entity_id="p1", role="subject", ordinal=0),
                HyperedgeParticipant(entity_id="o1", role="employer", ordinal=0),
            ],
        )
        writer.upsert_hyperedge(he)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        he_rows = read_all(conn, "hyperedges")
        hp_rows = read_all(conn, "hyperedge_entities")
        assert len(he_rows) == 1
        assert len(hp_rows) == 2
        # Update participant data
        with HypergraphWriter(db_path) as writer:
            he2 = Hyperedge(
                id="he1",
                type="Employment",
                data={"title": "Senior Engineer"},
                participants=[
                    HyperedgeParticipant(
                        entity_id="p1", role="subject", ordinal=0, data={"tenure": 24}
                    ),
                    HyperedgeParticipant(entity_id="o1", role="employer", ordinal=0),
                ],
            )
            writer.upsert_hyperedge(he2)
        data_row = conn.execute("SELECT data FROM hyperedges WHERE id='he1'").fetchone()
        edge_data = json.loads(data_row[0]) if data_row and data_row[0] else {}
        assert edge_data.get("title") == "Senior Engineer"
        part = conn.execute(
            """
            SELECT json_extract(data, '$.tenure') AS tenure
            FROM hyperedge_entities
            WHERE hyperedge_id='he1' AND entity_id='p1' AND role='subject' AND ordinal=0
            """
        ).fetchone()
        assert (part[0] or 0) == 24
    finally:
        conn.close()
