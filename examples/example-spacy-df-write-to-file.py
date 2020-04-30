from spacy_conll import init_parser

"""Example showing how to use spacy_conll to easily write the ConLL representations
   of sentences to their own files."""


def main():
    # Initialise English parser, already including the ConllFormatter as a pipeline component
    nlp = init_parser('spacy', 'en')
    # Parse a given string
    doc = nlp("A cookie is a baked or cooked food that is typically small, flat and sweet. It usually contains flour,"
              " sugar and some type of oil or fat. It may include other ingredients such as raisins, oats, chocolate"
              " chips, nuts, etc.")

    # Write the conll representation of each sentence to its own file
    # Note that .conll_pd is only present if pandas is installed
    for sent_idx, sent in enumerate(doc.sents, 1):
        sent._.conll_pd.to_csv(f"sentence-{sent_idx}.txt", index=False, sep='\t')


if __name__ == '__main__':
    main()
