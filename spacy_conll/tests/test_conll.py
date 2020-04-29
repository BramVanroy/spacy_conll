def test_doc_has_conll(doc):
    assert doc.has_extension('conll')
    assert doc._.conll is not None
    assert isinstance(doc._.conll, list)


def test_sents_has_conll_single_sentence(doc):
    for sent in doc.sents:
        assert sent.has_extension('conll')
        assert sent._.conll is not None
        assert isinstance(sent._.conll, list)


def test_token_has_conll_single_sentence(doc):
    for token in doc:
        assert token.has_extension('conll')
        assert token._.conll is not None
        assert isinstance(token._.conll, dict)
