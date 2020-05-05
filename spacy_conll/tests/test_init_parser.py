from spacy_conll import init_parser

# Basic initialisation already tested indirectly in conftest.py

def test_is_tokenized(pretokenized_doc):
    # tokenized length = 11, untokenized == 9
    assert len(pretokenized_doc) == 9

