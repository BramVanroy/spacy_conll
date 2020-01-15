def test_nlp_has_component(en_small_with_formatter):
    assert 'conll_formatter' in en_small_with_formatter.pipe_names