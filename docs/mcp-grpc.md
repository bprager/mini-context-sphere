# gRPC MCP Service Design

This document proposes stable proto messages and services for the MCP server, optimized for the project’s SQLite hypergraph and the configurable `config/graph_schema.yaml`.

Goals

- Stable, generic API: work with the simple `nodes`/`edges` layout today and the planned `hyperedges` + `hyperedge_entities` model tomorrow.
- Efficient queries on SQLite: minimize round trips, keep payloads compact, and support streaming where it helps (long result sets or server-side expansion).
- Shared logic: HTTP JSON handlers call the same functions the gRPC handlers use, so behavior stays consistent.

______________________________________________________________________

## Schema Background and Implications

SQLite base today

- `nodes(id TEXT PRIMARY KEY, type TEXT, data JSON)`
- `edges(id TEXT PRIMARY KEY, type TEXT, source TEXT, target TEXT, data JSON)`

Planned additions

- `hyperedges(id TEXT PRIMARY KEY, type TEXT, data JSON)`
- `hyperedge_entities(hyperedge_id TEXT, entity_id TEXT, role TEXT, ordinal INT, ...)`

Implications for API design

- Node/edge types are string labels; primary keys come from `graph_schema.yaml`. The API should carry `type` and opaque `id` without assuming particular fields inside `data`.
- Responses should include enough context for clients to render or reason over small subgraphs:
  - nodes and edges, plus an optional “context” expansion (neighbors) with a budget.
  - for hyperedges, return the hyperedge and its participating entities (with roles), so a client can display an n‑ary fact concisely.

______________________________________________________________________

## Proto Sketch (service and core messages)

```proto
syntax = "proto3";
package mcp;

message NodeId { string id = 1; }
message EdgeId { string id = 1; }
message HyperedgeId { string id = 1; }

message Kv {
  string key = 1;
  string value = 2; // JSON-encoded scalar; for objects/arrays, use Json below
}

message Json { string raw = 1; } // canonical JSON string; server preserves as is

message Node {
  string id = 1;
  string type = 2;
  Json data = 3;
}

message Edge {
  string id = 1;
  string type = 2;
  string source = 3;
  string target = 4;
  Json data = 5;
}

message HyperedgeEntity {
  string entity_id = 1;
  string role = 2; // role label per schema (e.g., subject, object, employer)
  int32 ordinal = 3; // for ordered roles if needed
}

message Hyperedge {
  string id = 1;
  string type = 2;
  Json data = 3;
  repeated HyperedgeEntity participants = 4;
}

message QueryRequest {
  string query = 1;       // free text or structured query string
  int32 limit = 2;        // max results
  bool expand_neighbors = 3; // if true, return immediate neighbors for context
  int32 neighbor_budget = 4; // cap on neighbor count
}

message QueryResult {
  repeated Node nodes = 1;
  repeated Edge edges = 2;
  repeated Hyperedge hyperedges = 3; // optional for n-ary facts (future)
}

message UpsertNodesRequest { repeated Node nodes = 1; }
message UpsertEdgesRequest { repeated Edge edges = 1; }
message UpsertHyperedgesRequest { repeated Hyperedge hyperedges = 1; }

message Ack { bool ok = 1; string message = 2; }

service McpService {
  rpc Query (QueryRequest) returns (stream QueryResult);
  rpc UpsertNodes (UpsertNodesRequest) returns (Ack);
  rpc UpsertEdges (UpsertEdgesRequest) returns (Ack);
  rpc UpsertHyperedges (UpsertHyperedgesRequest) returns (Ack);
}
```

Design choices

- JSON passthrough: use `Json { string raw }` to preserve arbitrary shapes (matches SQLite JSON columns). Avoids repeated proto changes for schema tweaks.
- Streaming `Query`: supports progressive rendering on clients and large traversals while keeping single‑shot requests simple.
- Opaque IDs and labeled types: clients don’t rely on schema internals; they can still render with `type` and `data`.

______________________________________________________________________

## Mapping from SQLite to Proto

- `nodes.type` → `Node.type`; `nodes.data` (JSON) → `Node.data.raw` (unchanged string).
- `edges.source/target` are node IDs; keep as strings.
- For hyperedges, when the table lands, join on `hyperedge_entities` to populate `participants` with roles.

Query plan

- Start with simple full‑text LIKE on `nodes.data` or `edges.data` as a baseline.
- Later: add virtual table for FTS5 on key text fields or embeddings table for vector search.
- Neighbor expansion: after selecting seed nodes/edges/hyperedges, fetch limited neighbors within `neighbor_budget`.

______________________________________________________________________

## Service Implementation Plan

- Codegen: use `grpcio-tools` initially for simplicity; consider `betterproto` if you want dataclasses‑like ergonomics.
- Server: `grpc.aio` (asyncio) in the same process as FastAPI; run on a separate port. Keep HTTP 1.1 JSON on Uvicorn; gRPC over HTTP/2.
- Composition: implement query logic in a shared module so both gRPC and FastAPI call it.
- Health and observability: mirror the `mcp` logger style; add simple health RPC if needed.

______________________________________________________________________

## Testing Strategy

- Unit tests for the query planner and SQLite mappers.
- gRPC integration tests using an in‑process `grpc.aio` server fixture and an async client.
- Contract tests: ensure `/mcp/query` JSON and `Query` RPC return consistent result sets for equivalent requests.

______________________________________________________________________

## Open Questions / Future Enhancements

- Pagination semantics for streaming: include cursors or offsets in streamed `QueryResult` chunks if needed.
- Authn/z: keep gRPC internal at first; add interceptors or mTLS later.
- Backpressure: consider server‑side throttling when neighbor expansion is large.
