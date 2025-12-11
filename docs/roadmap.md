# Roadmap

This file sketches where the project is heading. It focuses on the hypergraph pipeline on top of the serverless FastMCP starter on Cloud Run with SQLite.

______________________________________________________________________

## Now - 0.2 series

- Finalize the SQLite hypergraph schema with explicit hyperedges and a bipartite `hyperedge_entities` link table.
- Extend `pipeline/hypergraph_writer.py` to create nodes, hyperedges and links from markdown, using `config/graph_schema.yaml` or `SCHEMA_PATH` for labels and primary keys.
- Implement the first useful `/mcp/query` path that reads from the hypergraph instead of the stub `documents` table.
- Complete the LinkedIn tutorial path: `tutorials/linkedin/linkedin_bootstrap.py` turns `profile.html` into markdown plus a small set of hyperedges and the pipeline runs end to end for that profile.

______________________________________________________________________

## Next - 0.3 series

- Add optional embeddings for entities and hyperedges plus a simple vector index, so retrieval can rank nodes and hyperedges by similarity in one space.
- Introduce a light retrieval flow that
  - extracts entities from the query,
  - looks up related nodes and hyperedges,
  - expands neighbors,
  - returns a compact set of n ary facts plus one or two raw markdown chunks.
- Make the AI backend for the pipeline fully pluggable: OpenAI, Gemini or local Ollama, configured via env and `pipeline/config.py`.
- Add a tiny evaluation harness with a few hand written questions and expected answers for the LinkedIn tutorial profile, tracking simple F1 and retrieval quality.

______________________________________________________________________

## Later

These items are out of scope for the starter but good to keep in mind.

- Multimodal hyperedges that can point to images, charts or external files.
- Smarter retrieval that can be tuned with feedback, for example simple bandit or reinforcement learning ideas around which nodes or hyperedges to keep.
- Support for multiple profiles and projects in one hypergraph plus light access control.
- More serious evaluation and benchmark datasets once the core starter feels stable.
