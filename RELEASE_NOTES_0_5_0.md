### Added

- Neighbor ranking option for query expansion: HTTP `/mcp/query` accepts `neighbor_ranking` ("degree" or "none"); default is degree-based ranking by node degrees.
- Pipeline CLI flag `--content-hash-ids` and `CONTENT_HASH_IDS` env var to generate stable content-hash IDs when no front-matter `id` is present.
- Tests: coverage for ranking modes, CLI flag/env handling, rollback paths in `HypergraphWriter`, FTS creation, and PRAGMA error handling.

### Changed

- SQLite ingest tuning: added page size, cache, and mmap PRAGMAs for faster local builds; documented in `docs/pipeline-optimization.md`.
- Docs: updated README, backend, and pipeline docs to reflect new options and flows; ensured Markdown formatting and lint.
- QA: expanded test suite; overall coverage ~98%.
