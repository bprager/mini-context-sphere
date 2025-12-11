PYTEST_FLAGS = -q --maxfail=1 --disable-warnings --cov=. --cov-report=term-missing --cov-report=xml:coverage.xml

.PHONY: qa test lint fmt typecheck deps coverage-upload fmt-check mdlint mdfmt-fix mdfmt-check

qa: 
	@echo "==> Starting QA suite"
	$(MAKE) fmt-check
	$(MAKE) lint
	$(MAKE) mdfmt-check
	$(MAKE) mdlint
	$(MAKE) typecheck
	$(MAKE) deps
	$(MAKE) test
	$(MAKE) coverage-upload

test:
	@echo "==> Running tests (pytest)"
	uv run pytest $(PYTEST_FLAGS)

lint:
	@echo "==> Linting (ruff check)"
	uv run ruff check .

fmt:
	@echo "==> Formatting (ruff format)"
	uv run ruff format .

fmt-check:
	@echo "==> Formatting check (ruff format --check)"
	uv run ruff format --check .

MD_PATHS = README.md CHANGELOG.md docs .vibe tutorials static-site

mdfmt-fix:
	@echo "==> Markdown format (mdformat)"
	uv run mdformat $(MD_PATHS)

mdfmt-check:
	@echo "==> Markdown format check (mdformat --check)"
	uv run mdformat --check $(MD_PATHS)

mdlint:
	@echo "==> Markdown lint (pymarkdown)"
	uv run pymarkdown --config .pymarkdown.json scan $(MD_PATHS)

typecheck:
	@echo "==> Type checking (mypy)"
	uv run mypy app pipeline tests --ignore-missing-imports --python-version 3.14

deps:
	@echo "==> Dependency analysis (deptry)"
	uv run deptry .

coverage-upload:
	@echo "==> Coverage upload (codecov)"; \
	if [ -n "$(CODECOV_TOKEN)" ]; then \
		SHA=$$(git rev-parse HEAD 2>/dev/null || echo 0000000000000000000000000000000000000000); \
		uv run codecovcli upload-coverage -C "$$SHA" -t "$(CODECOV_TOKEN)" -f coverage.xml --disable-search --handle-no-reports-found || echo "Codecov upload skipped"; \
	else \
		echo "CODECOV_TOKEN not set; skipping Codecov upload"; \
	fi
