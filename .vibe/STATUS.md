# Status

Version v0.4.0

Done:

- gRPC: Added initial MCP gRPC service and proto (`proto/mcp.proto`), async server startup helper, Makefile `proto` target, and an integration test with grpc.aio.
- HTTP: Optional gRPC bootstrap under FastAPI via `START_GRPC=true` and `GRPC_PORT` env var.
- Docs: New `docs/mcp-grpc.md` design doc; roadmap updated with high‑priority gRPC work; backend docs mention proto generation and gRPC toggle.
- QA: Deptry scoped to project paths; coverage config excludes generated files; `make qa` runs proto generation.

Next:

- Hypergraph: Add hyperedge/link tables to the SQLite model and extend the gRPC API with `UpsertEdges`/`UpsertHyperedges`.
- Query: Implement FTS5 and neighbor expansion; unify HTTP `/mcp/query` and gRPC `Query` via a shared planner.
- Deploy: Optionally split gRPC into a separate Cloud Run service; add a health RPC.
