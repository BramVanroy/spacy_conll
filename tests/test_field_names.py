def test_fields_names_doc_pd(spacy_fields_names_doc):
    assert spacy_fields_names_doc._.conll_pd.columns[3] == "upostag"


def test_fields_names_sents_conll(spacy_fields_names_doc):
    for sent in spacy_fields_names_doc.sents:
        assert sent._.conll_pd.columns[3] == "upostag"


def test_fields_names_token_conll(spacy_fields_names_doc):
    for token in spacy_fields_names_doc:
        assert "UPOS" not in token._.conll
        assert "upostag" in token._.conll
        assert token._.conll_pd.index[3] == "upostag"
