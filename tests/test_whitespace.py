"""Tests for whitespace tokens and MISC (https://github.com/BramVanroy/spacy_conll/issues/35)."""

import pytest
import spacy

from spacy_conll import ConllParser, init_parser
from spacy_conll.utils import PD_AVAILABLE

ISSUE_TEXT = (
    "The motivation for using a global shared memory to help coordination"
    " and the idea of using the transformer to implement it are clear.\n2.\t"
)


def assert_valid_conllu(conll_str: str):
    """Check the CoNLL-U structure of every sentence block in `conll_str`."""
    blocks = [b for b in conll_str.split("\n\n") if b.strip()]
    assert blocks
    for block in blocks:
        lines = block.strip("\n").split("\n")
        token_lines = [line for line in lines if not line.startswith("#")]
        assert token_lines
        for line in lines:
            if line.startswith("# text = "):
                assert "\t" not in line
        ids = []
        heads = []
        for line in token_lines:
            fields = line.split("\t")
            assert len(fields) == 10, repr(line)
            for value in fields:
                assert value
                assert value == value.strip()
                assert "\n" not in value
                assert "\r" not in value
            ids.append(int(fields[0]))
            if fields[6] != "_":
                heads.append(int(fields[6]))
        assert ids == list(range(1, len(ids) + 1))
        assert all(0 <= head <= len(ids) for head in heads)


@pytest.fixture(scope="module")
def header_nlp():
    return init_parser(
        "en_core_web_sm", "spacy", formatter_config={"include_headers": True}
    )


def test_issue_reproduction(header_nlp):
    doc = header_nlp(ISSUE_TEXT)
    assert_valid_conllu(doc._.conll_str)
    for sent in doc.sents:
        assert_valid_conllu(sent._.conll_str)

    lines = doc._.conll_str.splitlines()
    text_lines = [line for line in lines if line.startswith("# text = ")]
    assert text_lines[0].endswith("are clear.")
    assert text_lines[-1] == "# text = 2."
    assert "SpacesAfter=\\n" in doc._.conll_str
    assert "SpacesAfter=\\t" in doc._.conll_str


@pytest.mark.parametrize(
    "text",
    [
        "\n\nHello  world.\t\tBye \n",
        " a",
        "Hello\r\nworld.\n\n\nNext   one.",
        "A.\n\n\n",
    ],
)
def test_whitespace_variants(header_nlp, text):
    doc = header_nlp(text)
    assert_valid_conllu(doc._.conll_str)


def test_misc_values(header_nlp):
    doc = header_nlp("\n\nHello  world.\t\tBye \n")
    miscs = [t._.conll["MISC"] for t in doc if not t.is_space]
    assert miscs == [
        "SpacesAfter=\\s\\s|SpacesBefore=\\n\\n",
        "SpaceAfter=No",
        "SpacesAfter=\\t\\t",
        "SpacesAfter=\\s\\n",
    ]


def test_space_token_extensions(header_nlp):
    doc = header_nlp("Hello\n\nworld.")
    space_tokens = [t for t in doc if t.is_space]
    assert space_tokens
    for token in space_tokens:
        assert token._.conll is None
        assert token._.conll_str is None
        if PD_AVAILABLE:
            assert token._.conll_pd is None

    words = [t for t in doc if not t.is_space]
    sent_conll = [row for sent in doc._.conll for row in sent]
    assert len(sent_conll) == len(words)
    if PD_AVAILABLE:
        assert len(doc._.conll_pd) == len(words)


def test_whitespace_only_doc(header_nlp):
    doc = header_nlp("   \n\t ")
    assert doc._.conll_str == ""
    assert doc._.conll == []
    if PD_AVAILABLE:
        assert doc._.conll_pd.empty


def test_whitespace_only_sentence_skipped():
    nlp = spacy.blank("en")
    nlp.add_pipe("conll_formatter", config={"include_headers": True})
    doc = nlp.make_doc("Hi. \n\n Bye.")
    assert doc[2].is_space
    for token in doc:
        token.is_sent_start = token.i in (0, 2, 3)
    doc = nlp.get_pipe("conll_formatter")(doc)
    assert_valid_conllu(doc._.conll_str)
    assert len(doc._.conll) == 2
    assert "# sent_id = 2\n# text = Bye." in doc._.conll_str
    assert doc[1]._.conll["MISC"] == "SpacesAfter=\\s\\n\\n\\s"


@pytest.mark.parametrize(
    ("heads", "deps", "expected"),
    [
        (
            [1, 1, 1],
            ["dep", "ROOT", "dep"],
            [(1, 0, "root"), (2, 0, "root")],
        ),
        (
            [0, 0, 1],
            ["ROOT", "dep", "dep"],
            [(1, 0, "root"), (2, 1, "dep")],
        ),
    ],
)
def test_head_on_space_token(heads, deps, expected):
    nlp = spacy.blank("en")
    nlp.add_pipe("conll_formatter")
    doc = nlp.make_doc("a \n b")
    for token, head, dep in zip(doc, heads, deps, strict=True):
        token.head = doc[head]
        token.dep_ = dep
    doc = nlp.get_pipe("conll_formatter")(doc)
    rows = [t._.conll for t in doc if not t.is_space]
    assert [(r["ID"], r["HEAD"], r["DEPREL"]) for r in rows] == expected


def test_parse_text_as_conll_skips_blank_lines(header_nlp):
    parser = ConllParser(header_nlp)
    conll = parser.parse_text_as_conll("Hello world.\n   \n\t\nBye.")
    assert_valid_conllu(conll)
    assert "# sent_id = 2\n# text = Bye." in conll
    assert "\n\n\n" not in conll


def test_read_back_whitespace_output(header_nlp):
    conll = header_nlp(ISSUE_TEXT)._.conll_str
    doc = ConllParser(header_nlp).parse_conll_text_as_spacy(conll)
    assert doc._.conll_str == conll


def test_misc_round_trip():
    nlp = spacy.blank("en")
    nlp.add_pipe("conll_formatter", config={"include_headers": True})
    conll = (
        "# sent_id = 1\n"
        "# text = Hi there\n"
        "1\tHi\thi\tINTJ\tUH\t_\t0\troot\t_\tSpaceAfter=No|Translit=x\n"
        "2\tthere\tthere\tADV\tRB\t_\t1\tadvmod\t_\tTranslit=y\n"
    )
    doc = ConllParser(nlp).parse_conll_text_as_spacy(conll)
    assert doc._.conll_str == conll
