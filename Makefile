.PHONY: quality style test docs serve-docs

# Lint and format checks (no changes made).
quality:
	uv run ruff check .
	uv run ruff format --check .

# Auto-fix lint violations and reformat.
style:
	uv run ruff check --fix .
	uv run ruff format .

# Run tests and doctests with coverage (also used by CI).
test:
	uv run pytest --cov --cov-report=term-missing --cov-report=xml

# Live-reloading preview of the current working tree.
docs:
	uv run mkdocs serve

DOCS_BRANCH ?= tmp-gh-pages
DOCS_VERSION ?= 0.0.0
DOCS_ALIAS ?= latest
DOCS_ADDR ?= 127.0.0.1:8000
DOCS_SOURCE_REF ?= main

# Preview the versioned (mike) site on a throwaway local branch.
serve-docs:
	DOCS_SOURCE_REF=$(DOCS_SOURCE_REF) uv run mike deploy --branch $(DOCS_BRANCH) --update-aliases $(DOCS_VERSION) $(DOCS_ALIAS)
	uv run mike set-default --branch $(DOCS_BRANCH) $(DOCS_ALIAS)
	uv run mike serve --branch $(DOCS_BRANCH) --dev-addr $(DOCS_ADDR)
