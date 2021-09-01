from pathlib import Path

from spacy_conll import init_parser
from spacy_conll.parser import ConllParser


"""Example showing how to use spacy_conll to read a ConLL file as a spaCy doc."""


def main():
    # Initialise English spaCy parser, already including the ConllFormatter as a pipeline component
    nlp = init_parser("en_core_web_sm", "spacy", include_headers=True)
    parser = ConllParser(nlp)
    # Path to a CoNLL-U test file
    path = Path(__file__).parent.parent / "tests" / "en_ewt-ud-dev.conllu-sample.txt"
    doc = parser.parse_conll_file_as_spacy(path, "utf-8")
    for sent_id, sent in enumerate(doc.sents, 1):
        print(sent._.conll_str)
        for word in sent:
            print(word, word.dep_)
        print()


if __name__ == "__main__":
    main()
