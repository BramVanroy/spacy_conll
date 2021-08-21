from spacy_conll import init_parser
from spacy_conll.parser import ConllParser
import os

"""Example showing how to use spacy_conll to easily read a ConLL doc"""


def main():
    # Initialise English parser, already including the ConllFormatter as a pipeline component
    nlp = init_parser("en_core_web_sm", "spacy")
    parser = ConllParser(nlp)
    # Path to a conllu file
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tests", "data_file",
                        "en_ewt-ud-dev.conllu-sample.txt")
    docs = parser.parse_conll_as_spacy(path, "utf-8", merge_subtoken=False)
    for d in docs:
        print(d)


if __name__ == "__main__":
    main()
