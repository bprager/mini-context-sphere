# Status

Version v0.3.1

Done:

- CI/QA: Makefile one‑command suite (`make qa`) with ruff, mypy, deptry, pytest+coverage and Codecov upload; GitHub Actions runs the same checks.
- Tests: Comprehensive pytest suite across `app/` and `pipeline/`, coverage >90% (currently ~97%).
- Docs: README streamlined for GitHub front page; testing details moved to `docs/testing-qa.md`; badges added (CI, CodeQL, Coverage, Release, Version, License, Python, mypy, ruff, pre-commit, Dependabot).
- Releases: `release-notes` workflow generates notes from CHANGELOG and updates a version badge; v0.3.0 Release created; CHANGELOG includes 0.3.1 patch.
- Tooling: Markdown formatter (mdformat) and linter (PyMarkdown) integrated; VS Code workspace configured for `.venv` and new Ruff extension.

Next:

- Hypergraph: Add hyperedge/link tables to the SQLite model and complete wiring in `pipeline/hypergraph_writer.py`; extend tests to cover error branches.
- Pipeline: Validate end‑to‑end run with the LinkedIn tutorial and feed `/mcp/query`.
- Runtime alignment: Align Docker base image with Python 3.14 to match `pyproject.toml` (or relax the version bound).
- Packaging: Update `[project].version` in `pyproject.toml` alongside CHANGELOG entries to keep metadata in sync.
