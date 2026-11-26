"""MkDocs hook: render doctest Examples sections as clean, syntax-highlighted Python.

Docstrings use ``>>>`` prompts so that ``pytest --doctest-modules`` can run them.
This hook post-processes the rendered HTML: it finds the plain-text blocks that
mkdocstrings generates for ``Examples::`` sections, strips the ``>>>`` / ``...``
prompts, then re-highlights the resulting code with Pygments as Python: giving
readers a clean, copyable, syntax-coloured block.

It also rewrites API source links so versioned docs point at the Git tag used
to build that release instead of always pointing at ``main``.

Doctests in source files are NOT modified: only the rendered HTML differs.
"""

from __future__ import annotations

import html as html_lib
import os
import re
from collections.abc import Mapping
from urllib.parse import quote

from pygments import highlight as pyg_highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import PythonLexer

_lexer = PythonLexer()
_formatter = HtmlFormatter(nowrap=True)
_SOURCE_LINK_PATTERN = re.compile(
    r'(?P<prefix><a\b[^>]*\bdata-source-link="github"[^>]*\bhref=")'
    r'(?P<source>[^"]+)'
    r'(?P<suffix>"[^>]*>)'
)


# Doctest examples are rendered as `pycon` (current mkdocstrings) or
# `text` (older versions) code blocks.
_DOCTEST_BLOCK_PATTERN = re.compile(
    r'<div class="language-(?:pycon|text) highlight">'
    r"<pre[^>]*><span></span><code>(.*?)</code></pre></div>",
    flags=re.DOTALL,
)
_TAG_PATTERN = re.compile(r"<[^>]+>")


def _strip_doctest_prompts(code: str) -> str:
    """Turn a doctest example into plain, copyable Python.

    Strips the ``>>> `` and ``... `` prompts and turns the expected output
    lines into ``# comments``.
    """
    result: list[str] = []
    in_example = False

    for line in code.split("\n"):
        if line.startswith(">>> ") or line == ">>>":
            result.append(line[4:])
            in_example = True
        elif in_example and (line.startswith("... ") or line == "..."):
            result.append(line[4:])
        elif in_example and line.strip():
            # Expected output: everything up to the next prompt or blank line.
            result.append("# " + line)
        else:
            result.append(line)
            in_example = False

    return "\n".join(result).strip()


def _get_docs_source_ref() -> str:
    """Return the Git ref that source links should point to."""
    git_ref = os.environ.get("DOCS_SOURCE_REF", "main").strip()
    return git_ref or "main"


def _get_repo_url(config: object | None) -> str | None:
    """Return the repository URL from MkDocs config when available."""
    if config is None:
        return None

    if isinstance(config, Mapping):
        repo_url = config.get("repo_url")
    else:
        repo_url = getattr(config, "repo_url", None)
        if repo_url is None:
            try:
                repo_url = config["repo_url"]  # type: ignore[index]
            except (KeyError, TypeError):
                repo_url = None

    if not repo_url:
        return None

    normalised_repo_url = str(repo_url).rstrip("/")
    if normalised_repo_url.endswith(".git"):
        normalised_repo_url = normalised_repo_url[:-4]
    return normalised_repo_url


def _build_github_source_url(
    repo_url: str,
    git_ref: str,
    source_target: str,
) -> str:
    """Build a GitHub source URL from a repo URL and relative source target."""
    unescaped = html_lib.unescape(source_target)
    filepath, hash_sep, fragment = unescaped.partition("#")
    quoted_ref = quote(git_ref, safe="/")
    quoted_filepath = quote(filepath, safe="/")
    url = f"{repo_url}/blob/{quoted_ref}/{quoted_filepath}"
    if hash_sep:
        url += f"#{fragment}"
    return url


def _rewrite_source_links(
    html: str,
    repo_url: str,
    git_ref: str,
) -> str:
    """Rewrite API source links to the requested GitHub ref."""

    def transform_link(match: re.Match[str]) -> str:
        source_target = match.group("source")
        source_url = _build_github_source_url(
            repo_url=repo_url,
            git_ref=git_ref,
            source_target=source_target,
        )
        return (
            f"{match.group('prefix')}{html_lib.escape(source_url, quote=True)}"
            f"{match.group('suffix')}"
        )

    return _SOURCE_LINK_PATTERN.sub(transform_link, html)


def on_page_content(html: str, **kwargs) -> str:
    """Post-process rendered page HTML for doctests and GitHub source links."""

    def transform_block(m: re.Match[str]) -> str:
        """Re-highlight a doctest block as plain Python."""
        # Drop pygments' token spans and line anchors to recover the text.
        raw_code = html_lib.unescape(_TAG_PATTERN.sub("", m.group(1)))
        if not raw_code.lstrip().startswith(">>>"):
            return m.group(0)
        clean = _strip_doctest_prompts(raw_code)
        inner = pyg_highlight(clean, _lexer, _formatter)
        return (
            '<div class="language-python highlight">'
            "<pre><span></span><code>" + inner + "</code></pre></div>"
        )

    html = _DOCTEST_BLOCK_PATTERN.sub(transform_block, html)

    repo_url = _get_repo_url(kwargs.get("config"))
    if repo_url is None:
        return html

    return _rewrite_source_links(
        html=html,
        repo_url=repo_url,
        git_ref=_get_docs_source_ref(),
    )
