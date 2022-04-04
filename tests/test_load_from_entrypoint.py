import spacy


def test_load_ext_from_entrypoint():
    """Test that we do not have to import spacy_conll, and that the component is indeed loaded from its entry-point"""
    nlp = spacy.load("en_core_web_sm")
    nlp.add_pipe("conll_formatter", last=True)
