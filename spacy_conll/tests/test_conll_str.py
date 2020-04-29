def test_doc_conll_str(doc):
    assert doc.has_extension('conll_str')
    assert doc._.conll_str is not None
    assert isinstance(doc._.conll_str, str)


def test_sents_conll_str(doc):
    for sent in doc.sents:
        assert sent.has_extension('conll_str')
        assert sent._.conll_str is not None
        assert isinstance(sent._.conll_str, str)


def test_token_conll_str(doc):
    for token in doc:
        assert token.has_extension('conll_str')
        assert token._.conll is not None
        assert isinstance(token._.conll_str, str)
