import pytest
import spacy

from spacy_conll import ConllParser, init_parser

TEXT = "First one.\nSecond one."


@pytest.fixture
def parser_with_pandas() -> ConllParser:
    return ConllParser(init_parser("en_core_web_sm", "spacy"))


def test_n_process_with_pandas_raises(parser_with_pandas):
    with pytest.raises(OSError, match="pandas serialisation"):
        parser_with_pandas.parse_text_as_conll(TEXT, n_process=2)


def test_ignore_pipe_errors_skips_guard(parser_with_pandas):
    # Past the guard, spaCy fails to pickle the pandas objects for the workers.
    with pytest.raises(ValueError, match="serialize"):
        parser_with_pandas.parse_text_as_conll(
            TEXT, n_process=2, ignore_pipe_errors=True
        )


def test_n_process_without_pandas_works():
    nlp = init_parser(
        "en_core_web_sm",
        "spacy",
        formatter_config={"disable_pandas": True},
    )

    out = ConllParser(nlp).parse_text_as_conll(TEXT, n_process=2)

    assert out.count("\n1\t") + out.startswith("1\t") == 2


def test_requires_conll_formatter():

    with pytest.raises(ValueError):
        ConllParser(spacy.blank("en"))


@pytest.mark.parametrize(
    ("split_on_newline", "n_sents"), [(True, 2), (False, 1)]
)
def test_split_on_newline(spacy_conllparser, split_on_newline, n_sents):
    out = spacy_conllparser.parse_text_as_conll(
        "Hello there\nfriend", split_on_newline=split_on_newline
    )

    assert out.count("# sent_id") == n_sents


@pytest.mark.parametrize(
    ("renumber_sent_ids", "expected"),
    [(True, ["1", "2"]), (False, ["1", "1"])],
)
def test_renumber_sent_ids(spacy_conllparser, renumber_sent_ids, expected):
    out = spacy_conllparser.parse_text_as_conll(
        TEXT, renumber_sent_ids=renumber_sent_ids
    )

    sent_ids = [
        line.split(" = ")[1]
        for line in out.splitlines()
        if line.startswith("# sent_id")
    ]
    assert sent_ids == expected
