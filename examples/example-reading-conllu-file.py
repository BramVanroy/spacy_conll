from spacy_conll import init_parser
from spacy_conll.parser import ConllParser

"""Example showing how to use spacy_conll to easily read a ConLL doc"""


def main():
    # Initialise English parser, already including the ConllFormatter as a pipeline component
    nlp = init_parser("en_core_web_sm", "spacy")
    # Parse a given string
    parser = ConllParser(nlp)
    docs = parser.parse_conll_as_spacy(
        r"C:\Dev\spacy_conll\tests\en_ewt-ud-dev.conllu-sample.txt",
        "utf-8",
        merge_subtoken=False)
    for d in docs:
        print(d)


if __name__ == "__main__":
    main()
