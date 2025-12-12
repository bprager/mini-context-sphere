# Pipeline optimization (SQLite)

This note collects practical tips to speed up ingest and queries when using SQLite as a hypergraph store. It complements docs/pipeline.md and reflects what the code already does.

Goals

- Faster bulk ingest for local builds or CI
- Keep runtime queries snappy without extra services
- Keep everything idempotent and easy to reason about

Ingest mode

- Enable a light “build mode” during pipeline runs:
  - `PRAGMA journal_mode=WAL;`
  - `PRAGMA synchronous=NORMAL;`
  - `PRAGMA temp_store=MEMORY;`
    These reduce fs syncs and keep temp data in memory. See `HypergraphWriter(build_mode=True)`.

Indexes

- Create a few helpful indexes once (idempotent):
  - `nodes(type)`
  - `edges(source)`, `edges(target)`
  - `hyperedge_entities(hyperedge_id)`, `hyperedge_entities(entity_id)`
    This is handled by `HypergraphWriter.ensure_indexes()`.

FTS5 for text search

- Precompute a virtual table `nodes_fts(id, content)` with triggers to keep it in sync.
- Backfill after ingest (full refresh) via `finalize_fts()` so runtime doesn’t pay setup cost.
- Query planner prefers FTS when present and falls back to `LIKE` otherwise.

Batch upserts

- Use `executemany` for nodes and edges to reduce round trips during ingest (`upsert_nodes`, `upsert_edges`).
- Hyperedges are upserted with their participants in a single transaction.

Deterministic IDs

- Prefer stable IDs assembled from `type` and schema PK fields (see `config/graph_schema.yaml`) to keep upserts idempotent across runs.

Connection tips

- Use a single connection per pipeline step; commit once per batch.
- Keep `row_factory = sqlite3.Row` for convenience in tests and utilities.

Troubleshooting

- If FTS isn’t available at runtime, queries still work via `LIKE` but will be slower.
- For very large datasets, consider splitting ingest and runtime databases or moving to a dedicated graph extension.
