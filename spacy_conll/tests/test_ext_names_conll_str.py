def test_ext_names_doc_conll_str(spacy_ext_names_doc):
    assert spacy_ext_names_doc.has_extension('conll_text')
    assert spacy_ext_names_doc._.conll_text is not None
    assert isinstance(spacy_ext_names_doc._.conll_text, str)


def test_ext_names_sents_conll_str(spacy_ext_names_doc):
    for sent in spacy_ext_names_doc.sents:
        assert sent.has_extension('conll_text')
        assert sent._.conll_text is not None
        assert isinstance(sent._.conll_text, str)


def test_ext_names_token_conll_str(spacy_ext_names_doc):
    for token in spacy_ext_names_doc:
        assert token.has_extension('conll_text')
        assert token._.conll_text is not None
        assert isinstance(token._.conll_text, str)
