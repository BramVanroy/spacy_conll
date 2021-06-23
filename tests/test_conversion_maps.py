def test_conversion_map_pronoun(spacy_conversion_map_doc):
    pronoun = spacy_conversion_map_doc[0]
    # Verify that -PRON- was changed to PRON
    assert pronoun._.conll["lemma"] == "he"
    # lemma is the third column
    assert pronoun._.conll_str.split("\t")[2] == "he"
    assert pronoun._.conll_pd["lemma"] == "he"
