from pathlib import Path

import pytest
import spacy

from spacy_conll.formatter import CONLL_FIELD_NAMES, check_columns
from spacy_conll.parser import ConllParser

SAMPLE = Path(__file__).parent.joinpath("conllu-plus-sample.txt")
HEADER = "# global.columns = "
TEXT = "He wanted to elaborate more on his grandma's cookie."
TEXT_2 = "A cookie is a baked food. It usually contains flour and sugar."


def blank_parser(**config) -> ConllParser:
    nlp = spacy.blank("en")
    nlp.add_pipe("conll_formatter", config=config)
    return ConllParser(nlp)


def plus_text(columns: str, *rows: str) -> str:
    lines = [HEADER + columns, "# sent_id = 1"]
    lines += ["\t".join(row.split()) for row in rows]
    return "\n".join(lines) + "\n"


def test_writing_subset_and_order(spacy_parser_with):
    columns = ["FORM", "ID", "HEAD", "DEPREL"]
    doc = spacy_parser_with(columns=columns)(TEXT)

    assert list(doc[0]._.conll) == columns
    assert list(doc._.conll_pd.columns) == columns
    lines = doc._.conll_str.splitlines()[1:]
    assert all(len(line.split("\t")) == 4 for line in lines)
    assert lines[0].split("\t")[:2] == ["He", "1"]


def test_header_only_on_doc(spacy_parser_with):
    doc = spacy_parser_with(columns=["ID", "FORM"])(TEXT)

    assert doc._.conll_str.startswith("# global.columns = ID FORM\n")
    assert HEADER not in doc[0]._.conll_str
    assert HEADER not in next(doc.sents)._.conll_str


def test_header_once_in_parse_text_as_conll(spacy_parser_with):
    parser = ConllParser(
        spacy_parser_with(columns=["ID", "FORM", "UPOS"], include_headers=True)
    )
    output = parser.parse_text_as_conll(
        f"{TEXT}\n{TEXT_2}", split_on_newline=True
    )

    assert output.startswith("# global.columns = ID FORM UPOS\n# sent_id = 1")
    assert output.count(HEADER) == 1


def test_default_has_no_header_and_all_fields(spacy_parser_with):
    doc = spacy_parser_with()(TEXT)

    assert HEADER not in doc._.conll_str
    assert list(doc[0]._.conll) == CONLL_FIELD_NAMES
    assert len(doc._.conll_str.splitlines()[0].split("\t")) == 10


def test_field_names_with_columns(spacy_parser_with):
    doc = spacy_parser_with(
        columns=["FORM", "UPOS"], field_names={"UPOS": "upostag"}
    )(TEXT)

    assert list(doc[0]._.conll) == ["FORM", "upostag"]
    assert list(doc._.conll_pd.columns) == ["FORM", "upostag"]
    assert doc._.conll_str.startswith("# global.columns = FORM UPOS\n")


def test_conversion_maps_with_columns(spacy_parser_with):
    doc = spacy_parser_with(
        columns=["FORM", "UPOS"],
        field_names={"UPOS": "upostag"},
        conversion_maps={"upostag": {"PRON": "P"}},
    )(TEXT)

    assert doc[0]._.conll["upostag"] == "P"
    assert doc._.conll_str.splitlines()[1].split("\t") == ["He", "P"]


def test_custom_column_from_extension_and_missing():
    nlp = blank_parser(columns=["FORM", "PARSEME:MWE"]).nlp
    doc = spacy.tokens.Doc(
        nlp.vocab,
        words=["a", "b"],
        heads=[0, 0],
        deps=["ROOT", "dep"],
    )
    doc[0]._.conll_custom_columns = {"PARSEME:MWE": "1:VID"}
    doc = nlp.get_pipe("conll_formatter")(doc)

    assert doc[0]._.conll["PARSEME:MWE"] == "1:VID"
    assert doc[1]._.conll["PARSEME:MWE"] == "_"
    assert doc._.conll_str.splitlines()[1:] == ["a\t1:VID", "b\t_"]


def test_empty_doc_pandas_columns_follow_columns(spacy_parser_with):
    doc = spacy_parser_with(columns=["FORM", "PARSEME:MWE"])("")

    assert list(doc._.conll_pd.columns) == ["FORM", "PARSEME:MWE"]


@pytest.mark.parametrize(
    "columns",
    [
        [],
        ["ID", "ID"],
        ["ID", "upos"],
        ["ID", "FOO"],
        ["ID", "parseme:mwe"],
        ["ID", "PARSEME:"],
    ],
)
def test_invalid_columns_raise(columns):
    with pytest.raises(ValueError):
        check_columns(columns)
    with pytest.raises(ValueError):
        blank_parser(columns=columns)


@pytest.mark.parametrize("columns", ["", "ID ID", "ID upos", "ID FOO"])
def test_invalid_header_raises(columns):
    with pytest.raises(ValueError):
        blank_parser().parse_conll_text_as_spacy(f"{HEADER}{columns}\n1\tHi\n")


def test_wrong_field_count_raises():
    text = plus_text("ID FORM HEAD DEPREL", "1 Hi 0 root", "2 there 1")

    with pytest.raises(ValueError, match=r"^Line 4: expected 4"):
        blank_parser().parse_conll_text_as_spacy(text)


def test_read_sample_file():
    doc = blank_parser().parse_conll_file_as_spacy(SAMPLE)

    assert [t.text for t in doc] == [
        "Slovenská",
        "ústava",
        ":",
        "pro",
        "i",
        "proti",
    ]
    assert doc[0].lemma_ == "slovenský"
    assert doc[0].pos_ == "ADJ"
    assert doc[0].tag_ == "AAFS1----1A----"
    assert doc[0].morph.get("Case") == ["Nom"]
    assert doc[3].dep_ == "appos"
    assert doc[3].head.i == 1
    assert doc[4]._.conll_custom_columns is None

    metadata = next(doc.sents)._.conll_metadata
    assert "# text_en = Slovak constitution: pros and cons" in metadata
    assert "# sent_id = mf920901-001-p1s1A" in metadata
    assert "global.columns" not in metadata


@pytest.mark.parametrize(
    "columns, row",
    [
        ("FORM HEAD DEPREL", "Hi 0 root"),
        ("DEPREL HEAD FORM", "root 0 Hi"),
        ("HEAD UPOS FORM LEMMA DEPREL", "0 INTJ Hi hi root"),
    ],
)
def test_read_subsets_in_any_order(columns, row):
    doc = blank_parser().parse_conll_text_as_spacy(plus_text(columns, row))

    assert doc[0].text == "Hi"
    assert doc[0].dep_ == "ROOT"
    assert doc[0].head.i == 0
    if "UPOS" in columns:
        assert doc[0].pos_ == "INTJ"
        assert doc[0].lemma_ == "hi"


def test_read_missing_id_uses_position():
    text = plus_text("FORM HEAD DEPREL", "Hi 2 intj", "there 0 root")
    doc = blank_parser(columns=CONLL_FIELD_NAMES).parse_conll_text_as_spacy(
        text
    )

    assert [t._.conll["ID"] for t in doc] == [1, 2]
    assert doc[0].head.i == 1


def test_read_missing_upos_is_empty():
    text = plus_text("ID FORM HEAD DEPREL", "1 Hi 0 root")
    doc = blank_parser().parse_conll_text_as_spacy(text)

    assert doc[0].pos_ == ""


def test_read_leading_blank_lines_before_header():
    text = "\n\n" + plus_text("ID FORM HEAD DEPREL", "1 Hi 0 root")
    doc = blank_parser().parse_conll_text_as_spacy(text)

    assert len(doc) == 1
    assert "global.columns" not in next(doc.sents)._.conll_metadata


def test_read_custom_column_stored_in_extension():
    text = plus_text(
        "ID FORM HEAD DEPREL PARSEME:MWE",
        "1 Hi 0 root 1:VID",
        "2 . 1 punct *",
    )
    doc = blank_parser().parse_conll_text_as_spacy(text)

    assert doc[0]._.conll_custom_columns == {"PARSEME:MWE": "1:VID"}
    assert doc[1]._.conll_custom_columns == {"PARSEME:MWE": "*"}


def test_read_plain_file_leaves_custom_columns_none():
    doc = blank_parser().parse_conll_file_as_spacy(
        Path(__file__).parent.joinpath("en_ewt-ud-dev.conllu-sample.txt")
    )

    assert all(t._.conll_custom_columns is None for t in doc)


def test_round_trip_with_custom_column():
    columns = ["FORM", "ID", "PARSEME:MWE", "HEAD", "DEPREL", "UPOS"]
    text = (
        HEADER + " ".join(columns) + "\n"
        "# sent_id = 1\n"
        "Hi\t1\t1:VID\t0\troot\tINTJ\n"
        "there\t2\t*\t1\tdiscourse\tADV"
    )
    parser = blank_parser(columns=columns, include_headers=True)

    doc = parser.parse_conll_text_as_spacy(text)

    assert doc._.conll_str.strip() == text


def test_header_once_with_sent_ids(spacy_parser_with):
    parser = ConllParser(
        spacy_parser_with(columns=["ID", "FORM"], include_headers=True)
    )
    output = parser.parse_text_as_conll(
        f"{TEXT}\n{TEXT}", sent_ids=["first", "second"]
    )

    assert output.startswith("# global.columns = ID FORM\n# sent_id = first\n")
    assert output.count(HEADER) == 1
    assert "# sent_id = second\n" in output


def test_round_trip_sample_file():
    columns = SAMPLE.read_text(encoding="utf-8").split("\n")[0].split()[3:]
    parser = blank_parser(columns=columns, include_headers=True)

    doc = parser.parse_conll_file_as_spacy(SAMPLE)

    assert doc._.conll_str == SAMPLE.read_text(encoding="utf-8")


def test_read_without_head_and_deprel_needs_strict_false():
    text = plus_text("ID FORM UPOS", "1 Hi INTJ", "2 there ADV")
    parser = blank_parser(columns=["ID", "FORM", "UPOS", "HEAD", "DEPREL"])

    with pytest.raises(ValueError, match=r"^Line 3: HEAD and DEPREL"):
        parser.parse_conll_text_as_spacy(text)

    doc = parser.parse_conll_text_as_spacy(text, strict=False)

    assert [t.pos_ for t in doc] == ["INTJ", "ADV"]
    assert not any(t.has_head() for t in doc)
    assert len(list(doc.sents)) == 1
    assert doc._.conll_str.split("\n")[1:3] == [
        "1\tHi\tINTJ\t_\t_",
        "2\tthere\tADV\t_\t_",
    ]


def test_read_sets_conll_columns_and_round_trips_without_formatter_columns():
    parser = blank_parser(include_headers=True)
    columns = SAMPLE.read_text(encoding="utf-8").split("\n")[0].split()[3:]

    doc = parser.parse_conll_file_as_spacy(SAMPLE)

    assert doc._.conll_columns == columns
    assert doc._.conll_str == SAMPLE.read_text(encoding="utf-8")
    assert list(doc[0]._.conll) == columns
    assert list(doc._.conll_pd.columns) == columns


def test_formatter_columns_override_doc_columns():
    parser = blank_parser(columns=["ID", "FORM"])

    doc = parser.parse_conll_file_as_spacy(SAMPLE)

    assert doc._.conll_columns is not None
    assert doc._.conll_str.startswith("# global.columns = ID FORM\n")
    assert list(doc[0]._.conll) == ["ID", "FORM"]
    assert list(doc._.conll_pd.columns) == ["ID", "FORM"]


def test_plain_conllu_leaves_conll_columns_none():
    doc = blank_parser().parse_conll_text_as_spacy(
        "1\tHi\thi\tINTJ\tUH\t_\t0\troot\t_\t_\n"
    )

    assert doc._.conll_columns is None
    assert "global.columns" not in doc._.conll_str


def test_invalid_doc_columns_raise(spacy_parser_with):
    parser = ConllParser(spacy_parser_with())
    doc = parser.nlp("Hello world.")
    doc._.conll_columns = ["ID", "upos"]

    with pytest.raises(ValueError, match="Invalid column name"):
        parser.nlp.get_pipe("conll_formatter")(doc)


def test_parse_text_as_conll_ignores_doc_columns(spacy_parser_with):
    parser = ConllParser(spacy_parser_with())
    parser.parse_conll_file_as_spacy(SAMPLE)

    assert "global.columns" not in parser.parse_text_as_conll(TEXT)
