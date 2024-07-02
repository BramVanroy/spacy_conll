import re

from spacy_conll import init_parser


"""Example showing how to use spacy_conll to parse a text that already has IDs, and to replace those indices in the
 output of spacy-conll for the string representation."""


row = (
    "008\tA cookie is a baked or cooked food that is typically small, flat and sweet.\n009\tIt usually contains"
    " flour, sugar and some type of oil or fat.\n010\tIt may include other ingredients such as raisins, oats,"
    " chocolate chips, nuts, etc."
)


def main():
    # Extract sentences from flat string
    sentences = row.splitlines()
    idxs, sentences = zip(*[sent.split("\t", 1) for sent in sentences])
    text = " ".join(sentences)

    # Parse a given string
    nlp = init_parser("en_core_web_sm", "spacy", include_headers=True)
    doc = nlp(text)

    # Iterate over the original indices and the spaCy sentences
    for sent_idx, sent in zip(idxs, doc.sents):
        conll_repr = sent._.conll_str
        # In the CoNLL representation, replace the sentence ID with the original one
        conll_repr = re.sub(r"# sent_id = (\d+)", f"# sent_id = {sent_idx}", conll_repr)
        print(conll_repr)


if __name__ == "__main__":
    main()
