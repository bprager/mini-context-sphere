# Architecture

Backend exposes a gRPC MCP service and an HTTP JSON endpoint that wraps it.
Static site calls the HTTP JSON endpoint, MCP clients use gRPC directly.
Backend uses SQLite file app/db/data.db (read heavy).
Infra folder defines GCP resources:
- Cloud Run service for backend
- Public bucket for static site

