"""Parse a text that has its own sentence IDs and write those IDs in the CoNLL-U output."""

import re

from spacy_conll import init_parser

ROW = (
    "008\tA cookie is a baked or cooked food that is typically small, flat and sweet.\n009\tIt usually contains"
    " flour, sugar and some type of oil or fat.\n010\tIt may include other ingredients such as raisins, oats,"
    " chocolate chips, nuts, etc."
)


def main():
    """Run the example."""
    idxs, sentences = zip(
        *[sent.split("\t", 1) for sent in ROW.splitlines()], strict=True
    )
    text = " ".join(sentences)

    nlp = init_parser(
        "en_core_web_sm", "spacy", formatter_config={"include_headers": True}
    )
    doc = nlp(text)

    for sent_idx, sent in zip(idxs, doc.sents, strict=True):
        print(
            re.sub(
                r"# sent_id = (\d+)",
                f"# sent_id = {sent_idx}",
                sent._.conll_str,
            )
        )


if __name__ == "__main__":
    main()
