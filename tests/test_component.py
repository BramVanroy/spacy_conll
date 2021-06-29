def test_component_in_pipeline(base_parser):
    assert "conll_formatter" in base_parser.pipe_names, (
        f"{'conll_formatter'} is not a component in the parser's pipeline."
        " This indicates that something went wrong while registering the component in the utils.init_nlp function."
        " This does not necessarily mean that the component itself is broken, but rather that it was not successfully"
        " added to the parser's pipeline for the testing procedure."
    )
