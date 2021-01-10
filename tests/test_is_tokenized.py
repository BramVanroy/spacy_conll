def test_is_tokenized(pretokenized_doc):
    # tokenized length = 11, un/pretokenized == 9
    assert len(pretokenized_doc) == 9
