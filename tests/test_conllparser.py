def test_conllparser(conllparser_conllstr):
    # three sentence, each with one # for sent id and one # for text
    assert conllparser_conllstr.count("#") == 6


def test_pretokenized_conllparser(pretokenized_conllparser_conllstr):
    # pretokenized disables sentence segmentation, so only one sentence
    # one sentence, each with one # for sent id and one # for text
    assert pretokenized_conllparser_conllstr.count("#") == 2
    # Because it is pretokenised, we need exactly 42 tokens all the time
    assert pretokenized_conllparser_conllstr.count("\n") == 42
