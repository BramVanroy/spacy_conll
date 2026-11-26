"""Add CoNLL-U representations to documents that are already in a DocBin."""

import spacy
from spacy.tokens import DocBin

from spacy_conll import ConllFormatter


def main():
    """Run the example."""
    nlp = spacy.load("en_core_web_sm")
    docs = nlp.pipe(
        ["This is a document to serialize.", "Another one (bites the dust)."]
    )
    doc_bin = DocBin(docs=docs)

    formatter = ConllFormatter()
    conll_docs = [formatter(doc) for doc in doc_bin.get_docs(nlp.vocab)]
    conll_doc_bin = DocBin(docs=conll_docs, store_user_data=True)

    for conll_doc in conll_doc_bin.get_docs(nlp.vocab):
        print(conll_doc._.conll_str)


if __name__ == "__main__":
    main()
