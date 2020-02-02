def test_spacy_has_component(spacy_en_small_with_formatter):
    assert 'conll_formatter' in spacy_en_small_with_formatter.pipe_names

def test_spacy_stanfordnlp_has_component(spacy_stanfordnlp_en_with_formatter):
    assert 'conll_formatter' in spacy_stanfordnlp_en_with_formatter.pipe_names
