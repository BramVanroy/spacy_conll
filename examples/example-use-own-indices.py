"""Parse a text that has its own sentence IDs and write those IDs in the CoNLL-U output."""

from spacy_conll import ConllParser, init_parser

ROWS = (
    "008\tA cookie is a baked or cooked food that is typically small, flat and sweet.\n009\tIt usually contains"
    " flour, sugar and some type of oil or fat.\n010\tIt may include other ingredients such as raisins, oats,"
    " chocolate chips, nuts, etc."
)


def main():
    """Run the example."""
    sent_ids, sentences = zip(
        *[row.split("\t", 1) for row in ROWS.splitlines()], strict=True
    )

    # disable_sbd keeps every line as one sentence, so there is one ID per line.
    nlp = init_parser(
        "en_core_web_sm",
        "spacy",
        disable_sbd=True,
        formatter_config={"include_headers": True},
    )
    parser = ConllParser(nlp)
    print(parser.parse_text_as_conll("\n".join(sentences), sent_ids=sent_ids))


if __name__ == "__main__":
    main()
