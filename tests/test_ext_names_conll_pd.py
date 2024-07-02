from pandas import DataFrame, Series
from spacy_conll.formatter import CONLL_FIELD_NAMES


def test_ext_names_doc_conll_pd(spacy_ext_names_doc):
    assert spacy_ext_names_doc.has_extension("pandas")
    assert spacy_ext_names_doc._.pandas is not None
    assert isinstance(spacy_ext_names_doc._.pandas, DataFrame)
    assert CONLL_FIELD_NAMES == list(spacy_ext_names_doc._.pandas.columns)


def test_ext_names_sents_conll_pd(spacy_ext_names_doc):
    for sent in spacy_ext_names_doc.sents:
        assert sent.has_extension("pandas")
        assert sent._.pandas is not None
        assert isinstance(sent._.pandas, DataFrame)
        assert CONLL_FIELD_NAMES == list(sent._.pandas.columns)


def test_ext_names_token_conll_pd(spacy_ext_names_doc):
    for token in spacy_ext_names_doc:
        assert token.has_extension("pandas")
        assert token._.pandas is not None
        assert isinstance(token._.pandas, Series)
        assert CONLL_FIELD_NAMES == list(token._.pandas.index)
