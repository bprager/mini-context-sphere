### Added

- Comprehensive test suite across app and pipeline with pytest; coverage now >90%.
- CI enhancements: mypy, ruff, coverage threshold, Codecov upload, and announce-style step logs.
- Markdown QA: mdformat (formatter) and PyMarkdown (linter) with Makefile targets and CI integration.
- Pre-commit setup for ruff, mdformat, pymarkdown, and mypy hooks.
- Makefile `qa` target running full local QA (format, lint, typecheck, deps, tests, coverage upload).
- Docs: `docs/testing-qa.md` with one-command QA and CI details; README reorganized for GitHub front page with direct doc links and badges.
- Security & maintenance: Dependabot config and CodeQL workflow.

### Changed

- FastAPI `/mcp/query` now ensures SQLite connections are closed reliably.
- Moved `pyyaml` to runtime dependencies and configured deptry ignore for `uvicorn`.
- README badges updated (CI, coverage, release, license, Python, mypy, ruff, pre-commit).
