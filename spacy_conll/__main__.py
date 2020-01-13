import argparse
from locale import getpreferredencoding
from pathlib import Path
import re
from sys import stdout

from packaging import version
import spacy

from spacy_conll import ConllFormatter

SENT_ID_RE = re.compile(r"(?<=# sent_id = )(\d+)")


def main(input_file=None,
         input_encoding=getpreferredencoding(),
         input_str=None,
         is_tokenized=False,
         output_file=None,
         output_encoding=getpreferredencoding(),
         model='en_core_web_sm',
         disable_sbd=False,
         include_headers=False,
         no_force_counting=False,
         n_process=1,
         verbose=False
         ):

    # Init model:
    # Initialize model, with custom pipe
    # taking into account 'is_tokenized', 'disable_sbd', and 'include_headers'
    nlp = spacy.load(model)
    if is_tokenized:
        nlp.tokenizer = nlp.tokenizer.tokens_from_list
    if disable_sbd:
        nlp.add_pipe(_prevent_sbd, name='prevent-sbd', before='parser')
    conllformatter = ConllFormatter(nlp, include_headers=include_headers)
    nlp.add_pipe(conllformatter, after='parser')

    # Gather input:
    # Collect lines in 'lines' variable, taking into account 'is_tokenized'
    lines = []
    if input_str is not None:
        lines.append(input_str.strip().split(' ') if is_tokenized else input_str)
    elif input_file is not None:
        with Path(input_file).open(encoding=input_encoding) as fhin:
            lines = [l.strip() for l in fhin.readlines()]
            if is_tokenized:
                lines = [l.split(' ') for l in lines]
    else:
        raise ValueError("'input_file' or 'input_str' must be given.")

    # Write to output:
    # If 'output_file' given, write to that file - if, also, 'verbose' is given, also write to stdout
    # Else write to stdout
    fhout = Path(output_file).open('w', encoding=output_encoding) if output_file is not None else stdout
    conll_idx = 0

    _gen = nlp.pipe(lines, n_process=n_process) if version.parse(spacy.__version__) >= version.parse('2.2.2') else nlp.pipe(lines)

    for doc_idx, doc in enumerate(_gen):
        for sent in doc.sents:
            conll_idx += 1
            sent_as_conll = sent._.conll_format

            if include_headers and not no_force_counting:
                sent_as_conll = re.sub(SENT_ID_RE, str(conll_idx), sent_as_conll, 1)

            # Newline madness:
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
    # Input arguments
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     description='Parse an input string or input file to CoNLL-U format.')
    parser.add_argument('-f', '--input_file', default=None,
                        help="Path to file with sentences to parse. Has precedence over 'input_str'.")
    parser.add_argument('-a', '--input_encoding', default=getpreferredencoding(),
                        help="Encoding of the input file. Default value is system default.")
    parser.add_argument('-b', '--input_str', default=None, help="Input string to parse.")
    parser.add_argument('-t', '--is_tokenized', default=False, action="store_true",
                        help="Enable this option when your text has already been tokenized (space-seperated).")
    # Output arguments
    parser.add_argument('-o', '--output_file', default=None,
                        help="Path to output file. If not specified, the output will be printed on standard output.")
    parser.add_argument('-c', '--output_encoding', default=getpreferredencoding(),
                        help="Encoding of the output file. Default value is system default.")
    # Model arguments
    parser.add_argument('-m', '--model', default='en_core_web_sm', help="spaCy model to use.")
    parser.add_argument('-s', '--disable_sbd', default=False, action="store_true",
                        help="Disables spaCy automatic sentence boundary detection. In practice, disabling means that"
                             " every line will be parsed as one sentence, regardless of its actual content.")

    # Additional arguments
    parser.add_argument('-d', '--include_headers', default=False, action='store_true',
                        help="To include headers before the output of every sentence. These headers include the"
                             " sentence text and the sentence ID.")
    parser.add_argument('-e', '--no_force_counting', default=False, action="store_true",
                        help="To disable force counting the 'sent_id', starting from 1 and increasing for each"
                             " sentence. Instead, 'sent_id' will depend on how spaCy returns the sentences."
                             " Must have 'include_headers' enabled.")
    parser.add_argument('-v', '--verbose', default=False, action='store_true',
                        help="To print the output to stdout, regardless of 'output_file'.")
    parser.add_argument('-j', '--n_process', type=int, default=1,
                        help='Number of processors to use in nlp.pipe(). -1 will use as many cores as available.'
                             ' Requires spaCy v2.2.2.')

    args = parser.parse_args()
    main(**vars(args))
