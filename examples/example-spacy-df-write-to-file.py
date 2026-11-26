"""Write the CoNLL-U table of every sentence to its own file. Needs pandas."""

from spacy_conll import init_parser


def main():
    """Run the example."""
    nlp = init_parser("en_core_web_sm", "spacy")
    doc = nlp(
        "A cookie is a baked or cooked food that is typically small, flat and sweet. It usually contains flour,"
        " sugar and some type of oil or fat. It may include other ingredients such as raisins, oats, chocolate"
        " chips, nuts, etc."
    )

    for sent_idx, sent in enumerate(doc.sents, 1):
        sent._.conll_pd.to_csv(
            f"sentence-{sent_idx}.txt", index=False, sep="\t"
        )


if __name__ == "__main__":
    main()
