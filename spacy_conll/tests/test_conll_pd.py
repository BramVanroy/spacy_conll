from pandas import DataFrame, Series

from spacy_conll.formatter import CONLL_FIELD_NAMES


def test_doc_conll_pd(base_doc):
    assert base_doc.has_extension("conll_pd")
    assert base_doc._.conll_pd is not None
    assert isinstance(base_doc._.conll_pd, DataFrame)
    assert CONLL_FIELD_NAMES == list(base_doc._.conll_pd.columns)


def test_sents_conll_pd(base_doc):
    for sent in base_doc.sents:
        assert sent.has_extension("conll_pd")
        assert sent._.conll_pd is not None
        assert isinstance(sent._.conll_pd, DataFrame)
        assert CONLL_FIELD_NAMES == list(sent._.conll_pd.columns)


def test_token_conll_pd(base_doc):
    for token in base_doc:
        assert token.has_extension("conll_pd")
        assert token._.conll_pd is not None
        assert isinstance(token._.conll_pd, Series)
        assert CONLL_FIELD_NAMES == list(token._.conll_pd.index)
