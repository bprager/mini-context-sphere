# Changelog
All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, https://keepachangelog.com/en/1.1.0/,
and this project adheres to Semantic Versioning, https://semver.org/spec/v2.0.0.html.

## [Unreleased]

## [0.2.0] - 2025-12-10
### Added
- Data pipeline skeleton for building a SQLite based hypergraph from markdown, including the `pipeline/` package and schema configuration in `config/graph_schema.yaml`.
- LinkedIn based tutorial and example HTML client for bootstrapping a personal knowledge graph under `tutorials/linkedin/`.
- Roadmap documentation in `docs/roadmap.md` and updated `.vibe` guidance for AI assisted development.

### Changed
- Expanded documentation for the pipeline and hypergraph construction hints.
- Updated Python dependencies in `pyproject.toml` and `uv.lock`.

## [0.1.0] - 2025-12-10
### Added
- Initial serverless FastMCP starter layout (FastAPI backend with gRPC MCP, HTTP JSON facade and SQLite database).
- Static site frontend, Terraform infra for Cloud Run and Cloud Storage, and uv based Python environment.
- Documentation structure (README, docs and .vibe guidance) plus minimal logging, health and observability setup.

