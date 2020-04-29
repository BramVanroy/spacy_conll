from spacy_conll.formatter import CONLL_FIELD_NAMES


def test_doc_conll(doc):
    assert doc.has_extension('conll')
    assert doc._.conll is not None
    assert isinstance(doc._.conll, list)


def test_sents_conll(doc):
    for sent in doc.sents:
        assert sent.has_extension('conll')
        assert sent._.conll is not None
        assert isinstance(sent._.conll, list)


def test_token_conll(doc):
    for token in doc:
        assert token.has_extension('conll')
        assert token._.conll is not None
        assert isinstance(token._.conll, dict)
        assert CONLL_FIELD_NAMES == list(token._.conll.keys())
