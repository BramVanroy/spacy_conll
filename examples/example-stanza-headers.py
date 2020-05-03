from spacy_conll import init_parser

"""Example showing how to use spacy_conll to get a CoNLL string representation including headers."""


def main():
    # Initialise English parser, already including the ConllFormatter as a pipeline component.
    # Indicate that we want to get the CoNLL headers in the string output.
    # `use_gpu` and `verbose` are specific to stanza (and stanfordnlp). These keywords arguments
    # are passed onto their Pipeline() initialisation
    nlp = init_parser('stanza', 'en', parser_opts={'use_gpu': True, 'verbose': False}, include_headers=True)
    # Parse a given string
    doc = nlp("A cookie is a baked or cooked food that is typically small, flat and sweet. It usually contains flour,"
              " sugar and some type of oil or fat. It may include other ingredients such as raisins, oats, chocolate"
              " chips, nuts, etc.")

    # Get the CoNLL representation of the whole document, including headers
    conll = doc._.conll_str
    print(conll)


if __name__ == '__main__':
    main()
