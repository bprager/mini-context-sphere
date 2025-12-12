# Status

Version v0.4.0

Done:

- gRPC: Added initial MCP gRPC service and proto (`proto/mcp.proto`), async server startup helper, Makefile `proto` target, and an integration test with grpc.aio.
- HTTP: Optional gRPC bootstrap under FastAPI via `START_GRPC=true` and `GRPC_PORT` env var.
- Docs: New `docs/mcp-grpc.md` design doc; roadmap updated with high‑priority gRPC work; backend docs mention proto generation and gRPC toggle.
- QA: Deptry scoped to project paths; coverage config excludes generated files; `make qa` runs proto generation.

Next:

- Hypergraph: Landed hyperedge/link tables and batch upserts in the writer; extend tutorial/pipeline to populate them from markdown and schema roles.
- Query: Implemented FTS5 with triggers and neighbor expansion via a shared planner used by both HTTP `/mcp/query` and gRPC `Query`.
- gRPC: Service implements Query + UpsertNodes/Edges/Hyperedges and a simple Health RPC; tests cover query parity between HTTP and gRPC.
- Deploy: Consider running gRPC as a separate service if needed; keep HTTP JSON for the static site.
