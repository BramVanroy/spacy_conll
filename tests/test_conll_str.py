def test_doc_conll_str(base_doc):
    assert base_doc.has_extension("conll_str")
    assert base_doc._.conll_str is not None
    assert isinstance(base_doc._.conll_str, str)


def test_sents_conll_str(base_doc):
    for sent in base_doc.sents:
        assert sent.has_extension("conll_str")
        assert sent._.conll_str is not None
        assert isinstance(sent._.conll_str, str)


def test_token_conll_str(base_doc):
    for token in base_doc:
        assert token.has_extension("conll_str")
        assert token._.conll is not None
        assert isinstance(token._.conll_str, str)
