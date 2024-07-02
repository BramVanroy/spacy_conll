from pathlib import Path

from spacy_conll.parser import ConllParser


def test_conllf_to_spacy(spacy_conllparser: ConllParser, conll_testfile: Path):
    doc = spacy_conllparser.parse_conll_file_as_spacy(conll_testfile, input_encoding="utf-8")

    assert len(list(doc.sents)) == 2
    assert doc.has_annotation("DEP")
    assert doc.has_annotation("TAG")
    assert doc.has_annotation("MORPH")


def test_conllstr_to_spacy(spacy_conllparser: ConllParser, conll_testfile: Path):
    text = conll_testfile.read_text(encoding="utf-8")
    doc = spacy_conllparser.parse_conll_text_as_spacy(text)

    assert len(list(doc.sents)) == 2
    assert doc.has_annotation("DEP")
    assert doc.has_annotation("TAG")
    assert doc.has_annotation("MORPH")
