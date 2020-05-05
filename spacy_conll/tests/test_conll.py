from spacy_conll.formatter import CONLL_FIELD_NAMES


def test_doc_conll(base_doc):
    assert base_doc.has_extension("conll")
    assert base_doc._.conll is not None
    assert isinstance(base_doc._.conll, list)


def test_sents_conll(base_doc):
    for sent in base_doc.sents:
        assert sent.has_extension("conll")
        assert sent._.conll is not None
        assert isinstance(sent._.conll, list)


def test_token_conll(base_doc):
    for token in base_doc:
        assert token.has_extension("conll")
        assert token._.conll is not None
        assert isinstance(token._.conll, dict)
        assert CONLL_FIELD_NAMES == list(token._.conll.keys())
