## Testing and QA

This project uses a lightweight, fast QA stack. You can run everything locally with one command, and CI enforces the same checks on every push and PR.

### One‑Command Suite

```bash
uv venv
uv sync --group dev
make qa
```

Runs, in order:

- ruff format check and lint
- Markdown format (mdformat) check and Markdown lint (PyMarkdown)
- mypy type checking
- deptry dependency analysis
- pytest with coverage (XML written to `coverage.xml`)
- Codecov upload (skipped locally unless `CODECOV_TOKEN` is set)

### Individual Targets

- Format (Python): `make fmt` or `make fmt-check`
- Lint (Python): `make lint`
- Format (Markdown): `make mdfmt-fix` or `make mdfmt-check`
- Lint (Markdown): `make mdlint`
- Type check: `make typecheck`
- Dependencies: `make deps`
- Tests + coverage: `make test`
- Coverage upload: `make coverage-upload` (requires `CODECOV_TOKEN`)

Makefile: see `Makefile` for the exact commands and options.

### Continuous Integration

- CI: GitHub Actions runs the same suite with announce-style logs
  - Workflow: [.github/workflows/ci.yml](../.github/workflows/ci.yml)
  - Coverage threshold: 90% (build fails below this)
- Coverage: Codecov upload with badge on README

### Pre‑commit Hooks (optional)

Enable local checks on commit:

```bash
uv run pre-commit install
uv run pre-commit run --all-files
```

Configuration lives in `.pre-commit-config.yaml`.
