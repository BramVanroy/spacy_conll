from spacy.tokens import Doc

def test_parsed_sents(conllparser_parse_conllfile):
    #  There is 2 sents in doc
    assert len(list(conllparser_parse_conllfile)) == 2

def test_a_spacy_doc(conllparser_parse_conllfile):
    #  There is 2 sents in doc
    for doc in  conllparser_parse_conllfile:
        assert type(doc) == Doc

def test_a_spacy_doc(conllparser_parse_conllfile):
    #  There is 2 sents in doc
    for doc in  conllparser_parse_conllfile:
        assert type(doc) == Doc
