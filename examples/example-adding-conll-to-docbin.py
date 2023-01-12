import spacy
from spacy.tokens import DocBin
from spacy_conll import ConllFormatter


"""Example showing how to use spacy_conll to on existing DocBins so that you can add CoNLL to already annotated data."""


def main():
    # Regular spaCy parsing (no CoNLL formatter)
    nlp = spacy.load("en_core_web_sm")
    docs = nlp.pipe(["This is a document to serialize.", "Anoter one (bites the dust)."])
    doc_bin = DocBin(docs=docs)

    # Adding CoNLL formatter
    formatter = ConllFormatter()
    # Read the docs that are in the doc_bin, and add the CoNLL representation to them
    conll_docs = [formatter(doc) for doc in doc_bin.get_docs(nlp.vocab)]
    conll_doc_bin = DocBin(docs=conll_docs, store_user_data=True)

    # Check that it is indeed there in the new doc_bin
    for conll_doc in conll_doc_bin.get_docs(nlp.vocab):
        print(conll_doc._.conll_str)


if __name__ == "__main__":
    main()
