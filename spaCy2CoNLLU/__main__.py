if __name__ == '__main__':
    import argparse
    from locale import getpreferredencoding
    from __init__ import Spacy2ConllParser

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--input_file", default=None, help="Path to file with sentences to parse.")
    parser.add_argument("--input_encoding", default=getpreferredencoding(), help="Encoding of the input file. Default"
                                                                                 " value is system default.")
    parser.add_argument("--input_str", default=None, help="Input string to parse.")
    parser.add_argument("--output_file", default=None, help="Path to output file. If not specified, the output will be"
                                                            " printed on standard output.")
    parser.add_argument("--output_encoding", default=getpreferredencoding(), help="Encoding of the output file. Default"
                                                                                  " value is system default.")
    parser.add_argument("--model", default='en_core_web_sm', help="spaCy model to use (e.g. 'es_core_news_md').")
    parser.add_argument("--nlp", default=None, help="Optional already initialised spaCy NLP model. Has precedence over"
                                                    " 'model'.")

    args = parser.parse_args()
    spacyconll = Spacy2ConllParser(**vars(args))
    spacyconll.parse()
