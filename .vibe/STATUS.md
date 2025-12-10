# Status

Version v0.1.0

Done:
- Static site on Cloud Storage and FastAPI backend on Cloud Run with SQLite.
- Pipeline skeleton in `pipeline/` with config, schema loader, markdown loader and CLI.
- Generic `config/graph_schema.yaml` plus LinkedIn tutorial layout under `tutorials/linkedin/`.

Next:
- Add hyperedge and link tables in the SQLite hypergraph and wire them into `hypergraph_writer.py`.
- Make the LinkedIn tutorial run end to end and feed `/mcp/query`.

