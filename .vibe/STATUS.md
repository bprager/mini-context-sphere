# Status

Version v0.5.0

Done:

- Query: Degree-based neighbor ranking for expansion, optional `neighbor_ranking: "none"` in HTTP payload.
- Pipeline: Content-hash ID option (`--content-hash-ids` or `CONTENT_HASH_IDS`) for deterministic IDs without front-matter.
- SQLite: Added build-time PRAGMAs (page size, cache, mmap) and documented them in `docs/pipeline-optimization.md`.
- Docs: README, backend, and pipeline docs refreshed to reflect features; mdformat/pymarkdown green.
- QA: 44 tests, ~98% coverage; added tests for rollback, FTS creation, PRAGMA error path, CLI flags.

Next:

- RAG features: token-aware chunking and LLM-driven entity/hyperedge extraction from markdown.
- Vector search: optional lightweight embeddings for entities and hyperedges.
- gRPC parity: add neighbor ranking and future query params to the gRPC `Query` message.
