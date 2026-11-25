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


def _sent_id_values(conll: str) -> list[str]:
    return [
        line.split(" = ", 1)[1]
        for line in conll.splitlines()
        if line.startswith("# sent_id")
    ]


@pytest.mark.parametrize("renumber_sent_ids", [True, False])
def test_sent_ids(spacy_conllparser, renumber_sent_ids):
    out = spacy_conllparser.parse_text_as_conll(
        TEXT,
        sent_ids=["008", "a\\1 b"],
        renumber_sent_ids=renumber_sent_ids,
    )

    assert _sent_id_values(out) == ["008", "a\\1 b"]


def test_sent_ids_accepts_ints_and_iterables(spacy_conllparser):
    out = spacy_conllparser.parse_text_as_conll(TEXT, sent_ids=iter([8, 9]))

    assert _sent_id_values(out) == ["8", "9"]


def test_sent_ids_file(spacy_conllparser, tmp_path):
    input_file = tmp_path / "input.txt"
    input_file.write_text(TEXT, encoding="utf-8")

    out = spacy_conllparser.parse_file_as_conll(
        input_file, sent_ids=["s1", "s2"]
    )

    assert _sent_id_values(out) == ["s1", "s2"]


@pytest.mark.parametrize("sent_ids", [["only-one"], ["a", "b", "c"]])
def test_sent_ids_count_mismatch(spacy_conllparser, sent_ids):
    with pytest.raises(ValueError, match="sent_ids"):
        spacy_conllparser.parse_text_as_conll(TEXT, sent_ids=sent_ids)


def test_sent_ids_require_headers():
    parser = ConllParser(init_parser("en_core_web_sm", "spacy"))

    with pytest.raises(ValueError, match="include_headers"):
        parser.parse_text_as_conll(TEXT, sent_ids=["a", "b"])


def test_sent_ids_disable_sbd_one_id_per_line():
    nlp = init_parser(
        "en_core_web_sm",
        "spacy",
        disable_sbd=True,
        formatter_config={"include_headers": True},
    )
    text = "One sentence. And another.\n\nNext line."

    out = ConllParser(nlp).parse_text_as_conll(text, sent_ids=["x1", "x2"])

    assert _sent_id_values(out) == ["x1", "x2"]


def test_sent_ids_round_trip(spacy_conllparser):
    out = spacy_conllparser.parse_text_as_conll(TEXT, sent_ids=["008", "009"])

    doc = spacy_conllparser.parse_conll_text_as_spacy(out)

    assert [s._.conll_metadata.splitlines()[0] for s in doc.sents] == [
        "# sent_id = 008",
        "# sent_id = 009",
    ]
    assert _sent_id_values(doc._.conll_str) == ["008", "009"]
