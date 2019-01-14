def main():
    import argparse
    from locale import getpreferredencoding
    from spacy_conll import Spacy2ConllParser
    # Input arguments
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     description='Parse an input string or input file to CoNLL format.')
    parser.add_argument('-f', '--input_file', default=None,
                        help="Path to file with sentences to parse. Has precedence over 'input_str'.")
    parser.add_argument('-a', '--input_encoding', default=getpreferredencoding(),
                        help="Encoding of the input file. Default value is system default.")
    parser.add_argument('-b', '--input_str', default=None, help="Input string to parse.")
    # Output arguments
    parser.add_argument('-o', '--output_file', default=None,
                        help="Path to output file. If not specified, the output will be printed on standard output.")
    parser.add_argument('-c', '--output_encoding', default=getpreferredencoding(),
                        help="Encoding of the output file. Default value is system default.")
    # Model arguments
    parser.add_argument('-m', '--model', default='en_core_web_sm', help="spaCy model to use.")
    parser.add_argument('-n', '--nlp', default=None,
                        help="Optional already initialised spaCy NLP model. Has precedence over 'model'.")
    # Additional arguments
    parser.add_argument('-v', '--verbose', default=False, action="store_true",
                        help="To print the output to stdout, regardless of 'output_file'.")
    parser.add_argument('-d', '--include_headers', default=False, action="store_true",
                        help="To include headers before every sentence's output. These headers include the sentence"
                             " text and the sentence ID.")

    args = parser.parse_args()

    spacyconll = Spacy2ConllParser(model=args.model, nlp=args.nlp, verbose=args.verbose)

    args = vars(args)
    # Remove 'model' and 'nlp' from the arguments
    for k in ['model', 'nlp', 'verbose']:
        args.pop(k, None)

    spacyconll.parseprint(**args)


if __name__ == '__main__':
    main()
