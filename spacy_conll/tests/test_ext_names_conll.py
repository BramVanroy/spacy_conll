from spacy_conll.formatter import CONLL_FIELD_NAMES


def test_ext_names_doc_conll(spacy_ext_names_doc):
    assert spacy_ext_names_doc.has_extension('conllu')
    assert spacy_ext_names_doc._.conllu is not None
    assert isinstance(spacy_ext_names_doc._.conllu, list)


def test_ext_names_sents_conll(spacy_ext_names_doc):
    for sent in spacy_ext_names_doc.sents:
        assert sent.has_extension('conllu')
        assert sent._.conllu is not None
        assert isinstance(sent._.conllu, list)


def test_ext_names_token_conll(spacy_ext_names_doc):
    for token in spacy_ext_names_doc:
        assert token.has_extension('conllu')
        assert token._.conllu is not None
        assert isinstance(token._.conllu, dict)
        assert CONLL_FIELD_NAMES == list(token._.conllu.keys())
