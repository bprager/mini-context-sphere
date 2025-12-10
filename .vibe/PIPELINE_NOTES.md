# Pipeline notes for AI assistants

Goal: build and maintain a SQLite based hypergraph, using a SQLite graph extension, from user markdown, then optionally export a SQLite snapshot for the runtime backend.

Code layout:
- pipeline/config.py reads env (HYPERGRAPH_DB_PATH, AI_PROVIDER, AI_MODEL, MARKDOWN_ROOT, PROFILE_NAME)
- pipeline/ai_client.py defines AiBackend.complete(prompt) and adapters for openai, gemini, ollama
- pipeline/markdown_loader.py discovers and parses markdown under MARKDOWN_ROOT
- pipeline/hypergraph_writer.py writes nodes and edges into the SQLite graph database
- pipeline/cli.py provides commands: init-from-markdown, update-from-markdown, export-sqlite

Schema:
- config/graph_schema.yaml describes entity types (label, primary keys, examples)
- pipeline/schema_loader.py reads this file and exposes it as GraphSchema
- AI prompts and node construction should be driven by GraphSchema instead of hard coded labels

Tutorial:
- tutorials/linkedin/linkedin_bootstrap.py reads a saved LinkedIn profile.html and emits markdown under knowledge/profile
- user runs pipeline CLI to load that markdown into the SQLite hypergraph and export app/db/data.db

Design rules:
- markdown is the source of truth, SQLite hypergraph and runtime snapshot are generated
- keep dependencies small, avoid heavy scraping or PDF parsing
- do not call external sites, operate only on local files provided by the user

