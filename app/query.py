from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from typing import Any


@dataclass
class QueryOpts:
    term: str
    limit: int = 10
    expand_neighbors: bool = False
    neighbor_budget: int = 0
    neighbor_ranking: str = "degree"  # "degree" or "none"


def _ensure_fts(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    # Create FTS table if missing
    cur.execute(
        """
        CREATE VIRTUAL TABLE IF NOT EXISTS nodes_fts
        USING fts5(id, content, tokenize='porter');
        """
    )
    # Triggers to keep FTS in sync
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
    # Backfill existing rows if FTS is empty
    cur.execute("SELECT COUNT(*) FROM nodes_fts")
    (count,) = cur.fetchone() or (0,)
    if count == 0:
        cur.execute(
            """
            INSERT INTO nodes_fts (id, content)
            SELECT id,
                   coalesce(json_extract(data, '$.name'), '') || ' ' ||
                   coalesce(json_extract(data, '$.about'), '') || ' ' ||
                   type
            FROM nodes
            """
        )
    conn.commit()


def run_query(conn: sqlite3.Connection, opts: QueryOpts) -> dict[str, Any]:
    term = opts.term or ""
    limit = int(opts.limit or 10)

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []

    cur = conn.cursor()

    try:
        # Prefer FTS if available
        try:
            _ensure_fts(conn)
            cur.execute(
                """
                SELECT n.id, n.type, json(n.data) as data
                FROM nodes n
                JOIN nodes_fts f ON f.id = n.id
                WHERE nodes_fts MATCH ?
                LIMIT ?
                """,
                (term, limit),
            )
        except sqlite3.DatabaseError:
            # Fallback to LIKE if FTS not available
            cur.execute(
                """
                SELECT id, type, json(data) as data
                FROM nodes
                WHERE json(data) LIKE ? OR type LIKE ?
                LIMIT ?
                """,
                (f"%{term}%", f"%{term}%", limit),
            )

        rows = cur.fetchall()
        nodes = [
            {"id": r["id"], "type": r["type"], "data": json.loads(r["data"]) if r["data"] else {}}
            for r in rows
        ]

        if opts.expand_neighbors and opts.neighbor_budget and nodes:
            seed_ids = {n["id"] for n in nodes}
            if opts.neighbor_ranking == "none":
                # Simple limit without ranking
                cur.execute(
                    """
                    SELECT id, type, source, target, json(data) as data
                    FROM edges
                    WHERE source IN ({qs}) OR target IN ({qs})
                    LIMIT ?
                    """.format(qs=",".join(["?"] * len(seed_ids))),
                    [*seed_ids, *seed_ids, int(opts.neighbor_budget)],
                )
                e_rows = cur.fetchall()
                edges = [
                    {
                        "id": r["id"],
                        "type": r["type"],
                        "source": r["source"],
                        "target": r["target"],
                        "data": json.loads(r["data"]) if r["data"] else {},
                    }
                    for r in e_rows
                ]
            else:
                # Degree-based ranking of neighbor edges
                cur.execute(
                    """
                    SELECT id, type, source, target, json(data) as data
                    FROM edges
                    WHERE source IN ({qs}) OR target IN ({qs})
                    """.format(qs=",".join(["?"] * len(seed_ids))),
                    [*seed_ids, *seed_ids],
                )
                e_rows = cur.fetchall()

                if e_rows:
                    candidate_nodes: set[str] = set()
                    for r in e_rows:
                        candidate_nodes.add(r["source"])  # type: ignore[index]
                        candidate_nodes.add(r["target"])  # type: ignore[index]

                    deg_map: dict[str, int] = {nid: 0 for nid in candidate_nodes}
                    qmarks = ",".join(["?"] * len(candidate_nodes))
                    cur.execute(
                        (
                            "SELECT source AS id, COUNT(*) AS cnt FROM edges "
                            f"WHERE source IN ({qmarks}) GROUP BY source"
                        ),
                        [*candidate_nodes],
                    )
                    for nid, cnt in cur.fetchall():
                        if nid in deg_map:
                            deg_map[nid] += int(cnt)
                    cur.execute(
                        (
                            "SELECT target AS id, COUNT(*) AS cnt FROM edges "
                            f"WHERE target IN ({qmarks}) GROUP BY target"
                        ),
                        [*candidate_nodes],
                    )
                    for nid, cnt in cur.fetchall():
                        if nid in deg_map:
                            deg_map[nid] += int(cnt)

                    ranked = sorted(
                        e_rows,
                        key=lambda r: (
                            -(deg_map.get(r["source"], 0) + deg_map.get(r["target"], 0)),  # type: ignore[index]
                            r["id"],
                        ),
                    )
                    e_rows = ranked[: int(opts.neighbor_budget)]

                    edges = [
                        {
                            "id": r["id"],
                            "type": r["type"],
                            "source": r["source"],
                            "target": r["target"],
                            "data": json.loads(r["data"]) if r["data"] else {},
                        }
                        for r in e_rows
                    ]

            # Fetch neighbor nodes not already included
            neighbor_ids: set[str] = set()
            for e in edges:
                if e["source"] not in seed_ids:
                    neighbor_ids.add(e["source"])
                if e["target"] not in seed_ids:
                    neighbor_ids.add(e["target"])
            if neighbor_ids:
                cur.execute(
                    """
                    SELECT id, type, json(data) as data
                    FROM nodes
                    WHERE id IN ({qs})
                    """.format(qs=",".join(["?"] * len(neighbor_ids))),
                    [*neighbor_ids],
                )
                for r in cur.fetchall():
                    nodes.append(
                        {
                            "id": r["id"],
                            "type": r["type"],
                            "data": json.loads(r["data"]) if r["data"] else {},
                        }
                    )

        return {"nodes": nodes, "edges": edges}
    finally:
        cur.close()
