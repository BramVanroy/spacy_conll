def test_has_component(parser):
    assert 'conll_formatter' in parser().pipe_names
