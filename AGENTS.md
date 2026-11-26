# AGENTS.md

Rules for anyone (human or agent) who changes code or text in this repository.

## Commands

```bash
uv sync --locked              # install the package, dev tools and en_core_web_sm
make style                    # ruff check --fix + ruff format
make quality                  # ruff check + ruff format --check
make test                     # pytest with coverage (includes doctests in src/)
uv run pytest -m "not udpipe"   # skip backends that download models
uv run pytest tests/test_formatter.py::test_name
uv run mkdocs build --strict  # docs
```

## Code style

- Python 3.11+. Use built-in generics and `X | None`, never `typing.List`, `Optional` and so on.
- Google-style docstrings: one short paragraph, then `Args`, `Returns` and `Raises`. Add an `Examples` section with doctests when the behavior is not obvious. Doctests run in `make test`.
- Imports at the top of the module. Optional backends (`spacy_udpipe`, `pandas`) are imported lazily or behind the `*_AVAILABLE` flags in `utils.py`.
- Never pass an `argparse.Namespace` into a function. `main()` parses the arguments and calls the core function with explicit keyword arguments.
- No single-line wrapper functions, no banner comments, no comments that narrate the code or refer to old code or bugs.
- Do not change `pyproject.toml` dependencies without approval from the maintainer.

## Writing style

This applies to docs, README, changelog, commit messages and docstrings.

- State facts directly. No filler, no hype, no hedging.
- Avoid dashes as punctuation. Use a period, a comma or parentheses instead.
- Lists use `-`. No bold list headers, no emojis, straight quotes only, sentence case headings.
- Explain behavior with short examples.
- Commit messages and pull request text read like a human wrote them and do not mention AI tools or agents.

## Work rules for agents

- Commit after every finished item. Stage whole files.
- Report back in at most 400 words: what changed, anything unexpected, open questions, what was not run, and the literal test results.
