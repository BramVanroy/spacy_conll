def test_disabled_pandas(spacy_disabled_pandas_doc):
    # ensure that pandas extension is not set
    assert not spacy_disabled_pandas_doc.has_extension("conll_pd")
    for sent in spacy_disabled_pandas_doc.sents:
        assert not sent.has_extension("conll_pd")

    for token in spacy_disabled_pandas_doc:
        assert not token.has_extension("conll_pd")
