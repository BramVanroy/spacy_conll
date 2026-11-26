from pandas import DataFrame, Series
from spacy.tokens import DocBin

from spacy_conll.formatter import CONLL_FIELD_NAMES


def test_doc_conll_pd(base_doc):
    assert base_doc.has_extension("conll_pd")
    assert base_doc._.conll_pd is not None
    assert isinstance(base_doc._.conll_pd, DataFrame)
    assert list(base_doc._.conll_pd.columns) == CONLL_FIELD_NAMES


def test_sents_conll_pd(base_doc):
    for sent in base_doc.sents:
        assert sent.has_extension("conll_pd")
        assert sent._.conll_pd is not None
        assert isinstance(sent._.conll_pd, DataFrame)
        assert list(sent._.conll_pd.columns) == CONLL_FIELD_NAMES


def test_token_conll_pd(base_doc):
    for token in base_doc:
        assert token.has_extension("conll_pd")
        assert token._.conll_pd is not None
        assert isinstance(token._.conll_pd, Series)
        assert list(token._.conll_pd.index) == CONLL_FIELD_NAMES


def test_conll_pd_not_stored_in_user_data(base_doc):
    assert not any(
        isinstance(value, Series | DataFrame)
        for value in base_doc.user_data.values()
    )


def test_conll_pd_matches_conll(base_doc):
    expected = DataFrame(
        [token._.conll for sent in base_doc.sents for token in sent]
    )

    assert base_doc._.conll_pd.equals(expected)
    assert base_doc[0]._.conll_pd.to_dict() == base_doc[0]._.conll


def test_docbin_round_trip(base_doc):
    doc = base_doc

    doc_bin = DocBin(docs=[doc], store_user_data=True)
    new_doc = next(DocBin().from_bytes(doc_bin.to_bytes()).get_docs(doc.vocab))

    assert [list(sent) for sent in new_doc._.conll] == doc._.conll
    assert new_doc._.conll_str == doc._.conll_str
    assert new_doc._.conll_pd.equals(doc._.conll_pd)


def test_docbin_round_trip_ext_names(spacy_ext_names_doc):
    doc = spacy_ext_names_doc

    doc_bin = DocBin(docs=[doc], store_user_data=True)
    new_doc = next(DocBin().from_bytes(doc_bin.to_bytes()).get_docs(doc.vocab))

    assert new_doc._.pandas.equals(doc._.pandas)
    assert new_doc[0]._.pandas.equals(doc[0]._.pandas)


def test_whitespace_token_conll_pd_is_none(spacy_parser_with):
    doc = spacy_parser_with()("Hello  world.")

    assert [t._.conll_pd is None for t in doc] == [False, True, False, False]
    assert len(doc._.conll_pd) == 3
