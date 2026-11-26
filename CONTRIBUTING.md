# Contributing to spacy-conll

If you want to fix a bug, first open [an issue](https://github.com/BramVanroy/spacy_conll/issues) and say that you are working on it. Other people with the same problem then know that a fix is on the way.

If you want to add a feature, discuss the approach first in the [Discussions](https://github.com/BramVanroy/spacy_conll/discussions).

## Setup

The project uses [uv](https://docs.astral.sh/uv/). Clone the repository and install the package with all development tools. This also installs the English spaCy model `en_core_web_sm` that the tests need.

```shell
git clone https://github.com/BramVanroy/spacy_conll.git
cd spacy_conll
uv sync
uv run pre-commit install
```

## Checks

```shell
make style    # fix lint issues and format with ruff
make quality  # check lint and formatting without changing files
make test     # pytest with coverage, including the doctests in src/
```

Some tests download UDPipe models on first use. Skip them with `uv run pytest -m "not udpipe"`. Preview the documentation with `make docs` and check it with `uv run mkdocs build --strict`.

The code style is described in `AGENTS.md`. In short: Google-style docstrings, modern type hints (`list[str]`, `X | None`) and plain prose without dashes as punctuation.

## Pull requests

- Open pull requests against the `main` branch.
- Add `[WIP]` to the title of a pull request that is not ready for review and remove it when it is.
- If the pull request solves an issue, add `closes <link to the issue>` to the description.
- Add tests for new behavior and update the docs and docstrings.
- Run `make quality` and `make test` before you ask for a review.
- If nobody has responded after a week, tag the maintainer.
