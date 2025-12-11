# Roadmap notes for AI assistants

High level:

- Repo is a minimal serverless FastMCP starter on GCP with SQLite plus a small hypergraph pipeline.
- Human friendly roadmap lives in `docs/roadmap.md`.

Now:

- Extend `pipeline/hypergraph_writer.py` to create nodes, hyperedges and `hyperedge_entities` tables in the SQLite db.
- Wire markdown docs plus `config/graph_schema.yaml` or `SCHEMA_PATH` into node and hyperedge creation.
- Finish `tutorials/linkedin/linkedin_bootstrap.py` so `profile.html` produces markdown plus at least one hyperedge per role and organization and the pipeline CLI can populate the db and export `app/db/data.db`.

Next:

- Add embeddings for entities and hyperedges and a small vector index so retrieval can use similarity search.
- Implement a basic retrieval flow for `/mcp/query` that extracts entities from the query, fetches related nodes and hyperedges and returns a small set of n ary facts plus a bit of raw text.
- Make AI backend configuration solid (env driven OpenAI, Gemini, Ollama) and start using prompts informed by `config/graph_schema.yaml` and `tutorials/linkedin/graph_schema.yaml`.

Later:

- Explore hybrid retrieval (hypergraph plus chunks) and simple evaluation for a few example profiles.
- Consider multimodal hyperedges, feedback driven ranking and more advanced evaluation only when the starter feels stable.
