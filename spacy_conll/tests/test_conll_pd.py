from pandas import DataFrame, Series

from spacy_conll.formatter import CONLL_FIELD_NAMES


def test_doc_conll_pd(doc):
    assert doc.has_extension('conll_pd')
    assert doc._.conll_pd is not None
    assert isinstance(doc._.conll_pd, DataFrame)
    assert CONLL_FIELD_NAMES == list(doc._.conll_pd.columns)


def test_sents_conll_pd(doc):
    for sent in doc.sents:
        assert sent.has_extension('conll_pd')
        assert sent._.conll_pd is not None
        assert isinstance(sent._.conll_pd, DataFrame)
        assert CONLL_FIELD_NAMES == list(sent._.conll_pd.columns)


def test_token_conll_pd(doc):
    for token in doc:
        assert token.has_extension('conll_pd')
        assert token._.conll_pd is not None
        assert isinstance(token._.conll_pd, Series)
        assert CONLL_FIELD_NAMES == list(token._.conll_pd.index)
