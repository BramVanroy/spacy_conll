from pathlib import Path

import pytest

from spacy_conll.parser import ConllParser

ROW = "1\tHi\thi\tINTJ\tUH\t_\t0\troot\t0:root\t_"


def make_row(**overrides: str) -> str:
    fields = dict(
        zip(
            [
                "id",
                "form",
                "lemma",
                "upos",
                "xpos",
                "feats",
                "head",
                "deprel",
                "deps",
                "misc",
            ],
            ROW.split("\t"),
            strict=True,
        )
    )
    fields.update(overrides)
    return "\t".join(fields.values())


@pytest.mark.parametrize(
    "row",
    [make_row(lemma=""), make_row(misc="")],
)
def test_empty_field_raises(spacy_conllparser: ConllParser, row):
    with pytest.raises(ValueError, match="cannot be empty"):
        spacy_conllparser.parse_conll_text_as_spacy(row)


@pytest.mark.parametrize("field", ["upos", "xpos", "feats", "deprel", "deps"])
def test_space_in_restricted_field_raises(
    spacy_conllparser: ConllParser, field
):
    with pytest.raises(ValueError, match="only FORM, LEMMA, and MISC"):
        spacy_conllparser.parse_conll_text_as_spacy(make_row(**{field: "a b"}))


@pytest.mark.parametrize("field", ["form", "lemma", "misc"])
def test_space_in_free_field_is_accepted(
    spacy_conllparser: ConllParser, field
):
    doc = spacy_conllparser.parse_conll_text_as_spacy(
        make_row(**{field: "a b"})
    )

    assert len(doc) == 1


@pytest.mark.parametrize("id_", ["1-2", "1.1"])
def test_multiword_token_and_empty_node_raise(
    spacy_conllparser: ConllParser, id_
):
    with pytest.raises(NotImplementedError):
        spacy_conllparser.parse_conll_text_as_spacy(make_row(id=id_))


def test_chunk_that_is_not_one_sentence_raises(spacy_conllparser: ConllParser):
    two_roots = "\n".join(
        [ROW, "2\tthere\tthere\tADV\tRB\t_\t0\troot\t0:root\t_"]
    )

    with pytest.raises(ValueError, match="unexpected format"):
        spacy_conllparser.parse_conll_text_as_spacy(two_roots)


def test_trailing_blank_lines_are_accepted(spacy_conllparser: ConllParser):
    doc = spacy_conllparser.parse_conll_text_as_spacy(f"{ROW}\n\n")

    assert len(list(doc.sents)) == 1


@pytest.mark.xfail(
    strict=True,
    reason="The converter maps DEPREL 'root' to spaCy's 'ROOT' and the"
    " formatter writes it back as 'ROOT'",
)
def test_sample_file_round_trip(spacy_conllparser: ConllParser):
    path = Path(__file__).parent / "en_ewt-ud-dev.conllu-sample.txt"
    doc = spacy_conllparser.parse_conll_file_as_spacy(path)

    expected = path.read_text(encoding="utf-8")
    assert doc._.conll_str.rstrip("\n") == expected.rstrip("\n")
