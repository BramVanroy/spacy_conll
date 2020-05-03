import argparse
import re
from locale import getpreferredencoding
from pathlib import Path
from sys import stdout
from typing import Optional

import spacy
from packaging import version

# using absolute import, assuming the package has been installed!
from spacy_conll import init_parser

SENT_ID_RE = re.compile(r"(?<=# sent_id = )(\d+)")


def parse(
    input_file: Optional[str] = None,
    input_encoding: str = getpreferredencoding(),
    input_str: Optional[str] = None,
    is_tokenized: bool = False,
    output_file: Optional[str] = None,
    output_encoding: str = getpreferredencoding(),
    parser: str = "spacy",
    model_or_lang: Optional[str] = None,
    disable_sbd: bool = False,
    include_headers: bool = False,
    no_force_counting: bool = False,
    n_process: int = 1,
    verbose: bool = False,
):
    """ Parse an input string or input file to CoNLL-U format

        :param input_file: path to file with sentences to parse. Has precedence over 'input_str'
        :param input_encoding: encoding of the input file. Default value is system default
        :param input_str: input string to parse
        :param is_tokenized: indicates whether your text has already been tokenized (space-seperated)
        :param output_file: path to output file. If not specified, the output will be printed on standard output
        :param output_encoding: encoding of the output file. Default value is system default
        :param parser: which parser to use. Parsers other than 'spacy' need to be installed separately. Valid options are
            'spacy', 'stanfordnlp', 'stanza', 'udpipe'. Note that the spacy-* wrappers of those libraries need to be
            installed, e.g. spacy-stanza.
        :param model_or_lang: language model to use (must be installed). Defaults to an English model
        :param disable_sbd: disables spaCy automatic sentence boundary detection (only works for spaCy)
        :param include_headers: to include headers before the output of every sentence
        :param no_force_counting: to disable force counting the 'sent_id', starting from 1 and increasing for each sentence
        :param n_process: number of processes to use in nlp.pipe(). -1 will use as many cores as available
        :param verbose: to print the output to stdout, regardless of 'output_file'
        """
    if not input_str and not input_file:
        raise ValueError(
            "'input_file' or 'input_str' must be given. Use parse-as-conll -h for help."
        )

    nlp = init_parser(
        parser,
        model_or_lang,
        is_tokenized=is_tokenized,
        disable_sbd=disable_sbd,
        include_headers=include_headers,
    )

    # Gather input:
    # Collect lines in 'lines' variable, taking into account 'is_tokenized'
    lines = []
    if input_str:
        lines.append(
            input_str.strip().split(" ") if is_tokenized and parser in ["spacy"] else input_str
        )
    elif input_file:
        with Path(input_file).open(encoding=input_encoding) as fhin:
            lines = [l.strip() for l in fhin.readlines()]
            if is_tokenized and parser in ["spacy"]:
                lines = [l.split(" ") for l in lines]

    # Write to output:
    # If 'output_file' given, write to that file - if, also, 'verbose' is given, also write to stdout
    # Else write to stdout
    fhout = (
        Path(output_file).open("w", encoding=output_encoding)
        if output_file is not None
        else stdout
    )

    # 'n_process' argument is only supported from spaCy 2.2.2 onwards
    _nlpgen = None
    if version.parse(spacy.__version__) >= version.parse("2.2.2"):
        _nlpgen = nlp.pipe(lines, n_process=n_process)
    else:
        _nlpgen = nlp.pipe(lines)

    conll_idx = 0
    for doc_idx, doc in enumerate(_nlpgen):
        for sent in doc.sents:
            conll_idx += 1

            sent_as_conll = sent._.conll_str
            if include_headers and not no_force_counting:
                # nlp.pipe returns different docs, meaning that the generated sentence indices
                # by ConllFormatter are not consecutive (they reset for each new doc)
                # We can do a regex replace to fix that, though.
                sent_as_conll = re.sub(SENT_ID_RE, str(conll_idx), sent_as_conll, 1)

            # Newline madness dealing with writing to file and printing to stdout at the same time:
            # Prepend additional newline for all except the very first string.
            if not (doc_idx == 0 and sent.start == 0):
                sent_as_conll = "\n" + sent_as_conll

            fhout.write(sent_as_conll)
            if fhout is not stdout and verbose:
                # end='' to avoid adding yet another newline
                print(sent_as_conll, end="")

    fhout.close()


def main():
    cparser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Parse an input string or input file to CoNLL-U format using a"
        " spaCy-wrapped parser.",
    )

    # Input arguments
    cparser.add_argument(
        "-f",
        "--input_file",
        default=None,
        help="Path to file with sentences to parse. Has precedence over 'input_str'.",
    )
    cparser.add_argument(
        "-a",
        "--input_encoding",
        default=getpreferredencoding(),
        help="Encoding of the input file. Default value is system default.",
    )
    cparser.add_argument("-b", "--input_str", default=None, help="Input string to parse.")

    # Output arguments
    cparser.add_argument(
        "-o",
        "--output_file",
        default=None,
        help="Path to output file. If not specified, the output will be printed on standard output.",
    )
    cparser.add_argument(
        "-c",
        "--output_encoding",
        default=getpreferredencoding(),
        help="Encoding of the output file. Default value is system default.",
    )

    # Model/pipeline arguments
    cparser.add_argument(
        "-m",
        "--model_or_lang",
        default="en",
        help="language model to use (must be installed). Defaults to an English model",
    )
    cparser.add_argument(
        "-s",
        "--disable_sbd",
        default=False,
        action="store_true",
        help="Disables spaCy automatic sentence boundary detection. In practice, disabling means that"
        " every line will be parsed as one sentence, regardless of its actual content."
        " Only works when using 'spacy' as 'parser'.",
    )
    cparser.add_argument(
        "-t",
        "--is_tokenized",
        default=False,
        action="store_true",
        help="Indicates whether your text has already been tokenized (space-seperated)."
        " When used in conjunction with spacy-stanfordnlp, it will also be assumed that"
        " the text is sentence split by newline. Does not work for 'udpipe' as 'parser'.",
    )

    # Additional arguments
    cparser.add_argument(
        "-d",
        "--include_headers",
        default=False,
        action="store_true",
        help="To include headers before the output of every sentence. These headers include the"
        " sentence text and the sentence ID as per the CoNLL format.",
    )
    cparser.add_argument(
        "-e",
        "--no_force_counting",
        default=False,
        action="store_true",
        help="To disable force counting the 'sent_id', starting from 1 and increasing for each"
        " sentence. Instead, 'sent_id' will depend on how spaCy returns the sentences."
        " Must have 'include_headers' enabled.",
    )
    cparser.add_argument(
        "-j",
        "--n_process",
        type=int,
        default=1,
        help="Number of processes to use in nlp.pipe(). -1 will use as many cores as available."
        " Requires spaCy v2.2.2. Might not work for a 'parser' other than 'spacy'.",
    )
    cparser.add_argument(
        "-p",
        "--parser",
        default="spacy",
        choices=["spacy", "stanfordnlp", "stanza", "udpipe"],
        help="Which parser to use. Parsers other than 'spacy' need to be installed separately."
        " So if you wish to use 'stanfordnlp' models, 'spacy-stanfordnlp' needs to be installed."
        " For 'stanza' you need 'spacy-stanza', and for 'udpipe' the 'spacy-udpipe' library is"
        " required.",
    )
    cparser.add_argument(
        "-v",
        "--verbose",
        default=False,
        action="store_true",
        help="To always print the output to stdout, regardless of 'output_file'.",
    )

    args = cparser.parse_args()
    parse(**vars(args))


if __name__ == "__main__":
    main()
