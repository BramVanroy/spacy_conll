import argparse
from locale import getpreferredencoding
from pathlib import Path
import re
from sys import stdout

from packaging import version
import spacy

from spacy_conll import ConllFormatter

SENT_ID_RE = re.compile(r"(?<=# sent_id = )(\d+)")


def _init_nlp(model_or_lang, is_tokenized, disable_sbd, use_stanfordnlp):
    if model_or_lang is None:
        model_or_lang = 'en' if use_stanfordnlp else 'en_core_web_sm'

    nlp = None
    if use_stanfordnlp:
        from spacy_stanfordnlp import StanfordNLPLanguage
        import stanfordnlp

        snlp = stanfordnlp.Pipeline(lang=model_or_lang, tokenize_pretokenized=is_tokenized)
        nlp = StanfordNLPLanguage(snlp)
    else:
        # Init model:
        # Initialize model, with custom pipe
        # taking into account 'is_tokenized', 'disable_sbd', and 'include_headers'
        nlp = spacy.load(model_or_lang)
        if is_tokenized:
            nlp.tokenizer = nlp.tokenizer.tokens_from_list
        if disable_sbd:
            nlp.add_pipe(_prevent_sbd, name='prevent-sbd', before='parser')

    conllformatter = ConllFormatter(nlp)
    nlp.add_pipe(conllformatter, last=True)

    return nlp


def main(input_file=None,
         input_encoding=getpreferredencoding(),
         input_str=None,
         is_tokenized=False,
         output_file=None,
         output_encoding=getpreferredencoding(),
         model_or_lang=None,
         disable_sbd=False,
         include_headers=False,
         no_force_counting=False,
         n_process=1,
         use_stanfordnlp=False,
         verbose=False
         ):
    """ Parse an input string or input file to CoNLL-U format

    :param input_file: path to file with sentences to parse. Has precedence over 'input_str'
    :param input_encoding: encoding of the input file. Default value is system default
    :param input_str: input string to parse
    :param is_tokenized: indicates whether your text has already been tokenized (space-seperated)
    :param output_file: path to output file. If not specified, the output will be printed on standard output
    :param output_encoding: encoding of the output file. Default value is system default
    :param model_or_lang: spaCy or stanfordnlp model or language to use (must be installed)
    :param disable_sbd: disables spaCy automatic sentence boundary detection (only works for spaCy)
    :param include_headers: to include headers before the output of every sentence
    :param no_force_counting: to disable force counting the 'sent_id', starting from 1 and increasing for each sentence
    :param n_process: number of processes to use in nlp.pipe(). -1 will use as many cores as available
    :param use_stanfordnlp: whether to use stanfordnlp models rather than spaCy models
    :param verbose: to print the output to stdout, regardless of 'output_file'
    :return:
    """

    nlp = _init_nlp(model_or_lang, is_tokenized, disable_sbd, use_stanfordnlp)

    # Gather input:
    # Collect lines in 'lines' variable, taking into account 'is_tokenized'
    lines = []
    if input_str is not None:
        lines.append(input_str.strip().split(' ') if is_tokenized and not use_stanfordnlp else input_str)
    elif input_file is not None:
        with Path(input_file).open(encoding=input_encoding) as fhin:
            lines = [l.strip() for l in fhin.readlines()]
            if is_tokenized and not use_stanfordnlp:
                lines = [l.split(' ') for l in lines]
    else:
        raise ValueError("'input_file' or 'input_str' must be given.")

    # Write to output:
    # If 'output_file' given, write to that file - if, also, 'verbose' is given, also write to stdout
    # Else write to stdout
    fhout = Path(output_file).open('w', encoding=output_encoding) if output_file is not None else stdout

    # 'n_process' argument is only supported from spaCy 2.2.2 onwards
    _nlpgen = None
    if version.parse(spacy.__version__) >= version.parse('2.2.2'):
        _nlpgen = nlp.pipe(lines, n_process=n_process)
    else:
        _nlpgen = nlp.pipe(lines)

    conll_idx = 0
    for doc_idx, doc in enumerate(_nlpgen):
        for sent in doc.sents:
            conll_idx += 1

            if include_headers:
                sent_as_conll = sent._.conll_str_headers
                if not no_force_counting:
                    sent_as_conll = re.sub(SENT_ID_RE, str(conll_idx), sent_as_conll, 1)
            else:
                sent_as_conll = sent._.conll_str

            # Newline madness dealing with writing and printing at the same time:
            # Prepend additional newline for all except the very first
            if not (doc_idx == 0 and sent.start == 0):
                sent_as_conll = '\n' + sent_as_conll

            fhout.write(sent_as_conll)
            if fhout is not stdout and verbose:
                # end='' to avoid adding yet another newline
                print(sent_as_conll, end='')

    fhout.close()


def _prevent_sbd(doc):
    """ Disables spaCy's sentence boundary detection """
    for token in doc:
        token.is_sent_start = False
    return doc


if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     description='Parse an input string or input file to CoNLL-U format.')

    # Input arguments
    parser.add_argument('-f', '--input_file', default=None,
                        help="Path to file with sentences to parse. Has precedence over 'input_str'.")
    parser.add_argument('-a', '--input_encoding', default=getpreferredencoding(),
                        help='Encoding of the input file. Default value is system default.')
    parser.add_argument('-b', '--input_str', default=None, help='Input string to parse.')

    # Output arguments
    parser.add_argument('-o', '--output_file', default=None,
                        help='Path to output file. If not specified, the output will be printed on standard output.')
    parser.add_argument('-c', '--output_encoding', default=getpreferredencoding(),
                        help='Encoding of the output file. Default value is system default.')

    # Model/pipeline arguments
    parser.add_argument('-m', '--model_or_lang', default=None,
                        help='spaCy or stanfordnlp model or language to use (must be installed).')
    parser.add_argument('-s', '--disable_sbd', default=False, action='store_true',
                        help='Disables spaCy automatic sentence boundary detection. In practice, disabling means that'
                             ' every line will be parsed as one sentence, regardless of its actual content.'
                             ' Only works when using spaCy.')
    parser.add_argument('-t', '--is_tokenized', default=False, action='store_true',
                        help='Indicates whether your text has already been tokenized (space-seperated).'
                             ' When used in conjunction with spacy-stanfordnlp, it will also be assumed that'
                             ' the text is sentence split by newline.')

    # Additional arguments
    parser.add_argument('-d', '--include_headers', default=False, action='store_true',
                        help='To include headers before the output of every sentence. These headers include the'
                             ' sentence text and the sentence ID.')
    parser.add_argument('-e', '--no_force_counting', default=False, action='store_true',
                        help="To disable force counting the 'sent_id', starting from 1 and increasing for each"
                             " sentence. Instead, 'sent_id' will depend on how spaCy returns the sentences."
                             " Must have 'include_headers' enabled.")
    parser.add_argument('-j', '--n_process', type=int, default=1,
                        help='Number of processes to use in nlp.pipe(). -1 will use as many cores as available.'
                             ' Requires spaCy v2.2.2.')
    parser.add_argument('-u', '--use_stanfordnlp', default=False, action='store_true',
                        help='Use stanfordnlp models rather than spaCy models. Requires spacy-stanfordnlp.')
    parser.add_argument('-v', '--verbose', default=False, action='store_true',
                        help="To print the output to stdout, regardless of 'output_file'.")

    args = parser.parse_args()
    main(**vars(args))
