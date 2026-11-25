"""Read a CoNLL-U file as a spaCy Doc."""

from pathlib import Path

from spacy_conll import ConllParser, init_parser


def main():
    """Run the example."""
    nlp = init_parser(
        "en_core_web_sm", "spacy", formatter_config={"include_headers": True}
    )
    parser = ConllParser(nlp)
    path = (
        Path(__file__).parent.parent
        / "tests"
        / "en_ewt-ud-dev.conllu-sample.txt"
    )
    doc = parser.parse_conll_file_as_spacy(path)
    for sent in doc.sents:
        print(sent._.conll_str)
        for word in sent:
            print(word, word.dep_)
        print()


if __name__ == "__main__":
    main()
