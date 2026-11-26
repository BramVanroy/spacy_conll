from spacy_conll import init_parser


def test_conversion_map_pronoun(spacy_conversion_map_doc):
    pronoun = spacy_conversion_map_doc[0]
    # Verify that -PRON- was changed to PRON
    assert pronoun._.conll["LEMMA"] == "he"
    # lemma is the third column
    assert pronoun._.conll_str.split("\t")[2] == "he"
    assert pronoun._.conll_pd["LEMMA"] == "he"


def test_root_deprel_is_lowercase_and_mappable():
    nlp = init_parser("en_core_web_sm", "spacy")
    plain = nlp("He sleeps.")
    nlp_mapped = init_parser(
        "en_core_web_sm",
        "spacy",
        formatter_config={"conversion_maps": {"DEPREL": {"root": "ROOT"}}},
    )
    mapped = nlp_mapped("He sleeps.")

    assert "\t0\troot\t" in plain._.conll_str
    assert "\t0\tROOT\t" in mapped._.conll_str
