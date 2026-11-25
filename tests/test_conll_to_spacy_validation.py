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

    with pytest.raises(
        ValueError,
        match="Line 1: the HEAD values of this sentence do not form one tree",
    ):
        spacy_conllparser.parse_conll_text_as_spacy(two_roots)


def test_trailing_blank_lines_are_accepted(spacy_conllparser: ConllParser):
    doc = spacy_conllparser.parse_conll_text_as_spacy(f"{ROW}\n\n")

    assert len(list(doc.sents)) == 1


def test_sample_file_round_trip(spacy_conllparser: ConllParser):
    path = Path(__file__).parent / "en_ewt-ud-dev.conllu-sample.txt"
    doc = spacy_conllparser.parse_conll_file_as_spacy(path)

    expected = path.read_text(encoding="utf-8")
    assert doc._.conll_str.rstrip("\n") == expected.rstrip("\n")


ISSUE_34_SAMPLE = "\n".join(
    [
        "# P311545 = dubsar 3, 001",
        "1\tana\tana\tADP\tPRP\t_\t_\t_\tto\ta-na",
        "2\tŠumaya\tŠumaya\tPROPN\tPN\t_\t_\t_\tŠumaya\t{m}šu-ma-a",
        "3\tummā\tummu\tNOUN\tN\t_\t_\t_\tmother\tum-ma-a",
        "",
    ]
)

UNPARSED_AND_PARTIAL = "\n".join(
    [
        "# sent_id = 1",
        "1\tana\tana\tADP\tPRP\t_\t_\t_\tto\t_",
        "2\tŠumaya\tŠumaya\tPROPN\tPN\t_\t_\t_\t_\tSpaceAfter=No",
        "3\tummā\t_\t_\t_\t_\t_\t_\t_\t_",
        "",
        "# sent_id = 2",
        "1\tana\tana\tADP\tPRP\t_\t0\troot\t_\t_",
        "2\tŠumaya\tŠumaya\tPROPN\tPN\t_\t1\tchild\t_\t_",
        "3\tummā\tummu\tNOUN\tN\t_\t_\t_\t_\t_",
        "",
        "# sent_id = 3",
        "1\tana\tana\tADP\tPRP\t_\t_\t_\t_\t_",
        "2\tŠumaya\tŠumaya\tPROPN\tPN\tNumber=Sing\t3\tnmod\t_\t_",
        "3\tummā\tummu\tNOUN\tN\t_\t0\troot\t_\t_",
        "",
    ]
)


def test_strict_rejects_missing_head_and_deprel(
    spacy_conllparser: ConllParser,
):
    with pytest.raises(
        ValueError, match="Line 2: HEAD and DEPREL must be filled in"
    ):
        spacy_conllparser.parse_conll_text_as_spacy(ISSUE_34_SAMPLE)


def test_non_strict_reads_sentence_without_dependencies(
    spacy_conllparser: ConllParser,
):
    doc = spacy_conllparser.parse_conll_text_as_spacy(
        ISSUE_34_SAMPLE, strict=False
    )

    assert len(list(doc.sents)) == 1
    assert not doc.has_annotation("DEP")
    assert [t.dep_ for t in doc] == ["", "", ""]
    assert [t.has_head() for t in doc] == [False, False, False]
    assert [t.pos_ for t in doc] == ["ADP", "PROPN", "NOUN"]
    assert [t.tag_ for t in doc] == ["PRP", "PN", "N"]
    assert [t._.conll_deps_graphs_field for t in doc] == [
        "to",
        "Šumaya",
        "mother",
    ]


def test_non_strict_keeps_one_sentence_per_block(
    spacy_conllparser: ConllParser,
):
    doc = spacy_conllparser.parse_conll_text_as_spacy(
        UNPARSED_AND_PARTIAL, strict=False
    )
    sents = list(doc.sents)

    assert [len(s) for s in sents] == [3, 3, 3]
    assert [(t.dep_, t.head.i) for t in sents[1]] == [
        ("ROOT", 3),
        ("child", 3),
        ("", 5),
    ]
    assert [(t.dep_, t.head.i) for t in sents[2]] == [
        ("", 6),
        ("nmod", 8),
        ("ROOT", 8),
    ]


def test_underscore_is_a_missing_value(spacy_conllparser: ConllParser):
    doc = spacy_conllparser.parse_conll_text_as_spacy(
        UNPARSED_AND_PARTIAL, strict=False
    )

    assert (doc[2].lemma_, doc[2].pos_, doc[2].tag_) == ("", "", "")


def test_non_strict_round_trip_is_exact(spacy_conllparser: ConllParser):
    doc = spacy_conllparser.parse_conll_text_as_spacy(
        UNPARSED_AND_PARTIAL, strict=False
    )

    assert doc._.conll_str == UNPARSED_AND_PARTIAL


def test_non_strict_round_trip_keeps_misc(spacy_conllparser: ConllParser):
    doc = spacy_conllparser.parse_conll_text_as_spacy(
        ISSUE_34_SAMPLE, strict=False
    )

    assert doc._.conll_str == ISSUE_34_SAMPLE


def test_file_reader_passes_strict(spacy_conllparser: ConllParser, tmp_path):
    path = tmp_path / "sample.conllu"
    path.write_text(ISSUE_34_SAMPLE, encoding="utf-8")

    with pytest.raises(ValueError, match="HEAD and DEPREL"):
        spacy_conllparser.parse_conll_file_as_spacy(path)
    doc = spacy_conllparser.parse_conll_file_as_spacy(path, strict=False)

    assert len(doc) == 3


def test_strict_rejects_partial_tree(spacy_conllparser: ConllParser):
    with pytest.raises(ValueError, match="Line 4: HEAD and DEPREL"):
        spacy_conllparser.parse_conll_text_as_spacy(
            UNPARSED_AND_PARTIAL.split("\n\n", 1)[1]
        )


@pytest.mark.parametrize(
    ("head", "deprel", "strict", "message"),
    [
        ("0", "_", False, "Line 1: HEAD is '0' and DEPREL is '_'"),
        ("_", "root", False, "Line 1: HEAD is '_' and DEPREL is 'root'"),
        ("0", "_", True, "Line 1: HEAD and DEPREL must be filled in"),
        ("2", "dep", True, "Line 1: HEAD must be 0 or the ID"),
        ("x", "dep", False, "Line 1: HEAD must be 0 or the ID"),
    ],
)
def test_invalid_head_or_deprel_raises(
    spacy_conllparser: ConllParser, head, deprel, strict, message
):
    with pytest.raises(ValueError, match=message):
        spacy_conllparser.parse_conll_text_as_spacy(
            make_row(head=head, deprel=deprel), strict=strict
        )


@pytest.mark.parametrize(
    ("row", "message"),
    [
        ("1\tHi\thi\tINTJ\tUH\t_\t0\troot\t_", "found 9"),
        (make_row(id="x"), "ID must be a number"),
        (make_row(feats=""), "the FEATS field is empty"),
        (make_row(xpos="a b"), "the XPOS field contains a space"),
    ],
)
def test_error_names_line_and_field(
    spacy_conllparser: ConllParser, row, message
):
    with pytest.raises(ValueError, match=f"Line 3: .*{message}"):
        spacy_conllparser.parse_conll_text_as_spacy(f"{ROW}\n\n{row}")


def test_crlf_line_endings(spacy_conllparser: ConllParser):
    text = f"{ROW}\n\n{make_row(form='there', lemma='there')}\n"
    doc = spacy_conllparser.parse_conll_text_as_spacy(
        text.replace("\n", "\r\n")
    )

    assert [len(s) for s in doc.sents] == [1, 1]


@pytest.mark.parametrize(
    "text", ["", "\n\n", "  \n\t\n", "# sent_id = 1\n# text = Hi\n"]
)
@pytest.mark.parametrize("strict", [True, False])
def test_text_without_tokens_gives_empty_doc(
    spacy_conllparser: ConllParser, text, strict
):
    doc = spacy_conllparser.parse_conll_text_as_spacy(text, strict=strict)

    assert len(doc) == 0
    assert doc._.conll_str == ""
