"""The `parse-as-conll` command."""

import argparse
import os
import sys
from pathlib import Path
from typing import Literal

from spacy_conll.parser import ConllParser
from spacy_conll.utils import init_parser


def run(
    *,
    model_or_lang: str,
    parser: Literal["spacy", "stanza", "udpipe"],
    input_file: str | os.PathLike[str] | None = None,
    input_str: str | None = None,
    input_encoding: str = "utf-8",
    output_file: str | os.PathLike[str] | None = None,
    output_encoding: str = "utf-8",
    disable_sbd: bool = False,
    is_tokenized: bool = False,
    include_headers: bool = False,
    renumber_sent_ids: bool = True,
    n_process: int = 1,
    ignore_pipe_errors: bool = False,
    split_on_newline: bool = True,
    verbose: bool = False,
) -> None:
    """Parse a file or string and write the CoNLL-U output.

    The output goes to `output_file`, or to stdout when no file is given.
    The formatter runs with `disable_pandas=True` so that `n_process` can be
    larger than 1.

    Args:
        model_or_lang: See `init_parser`.
        parser: See `init_parser`.
        input_file: Path to a text file to parse. Takes precedence over
            `input_str`.
        input_str: Text to parse.
        input_encoding: Encoding of `input_file`.
        output_file: Path to write the output to.
        output_encoding: Encoding of `output_file`.
        disable_sbd: See `init_parser`.
        is_tokenized: See `init_parser`.
        include_headers: Whether to write the `# sent_id` and `# text`
            comment lines before every sentence.
        renumber_sent_ids: See `ConllParser.parse_text_as_conll`.
        n_process: See `ConllParser.parse_text_as_conll`.
        ignore_pipe_errors: See `ConllParser.parse_text_as_conll`.
        split_on_newline: See `ConllParser.parse_text_as_conll`.
        verbose: Whether to also print the output to stdout when
            `output_file` is given.

    Raises:
        ValueError: If neither `input_file` nor `input_str` is given.
    """
    if not input_str and not input_file:
        raise ValueError("'input_str' or 'input_file' must be given")

    nlp = init_parser(
        model_or_lang,
        parser,
        is_tokenized=is_tokenized,
        disable_sbd=disable_sbd,
        formatter_config={
            "disable_pandas": True,
            "include_headers": include_headers,
        },
    )
    conll_parser = ConllParser(nlp)
    parse_opts = {
        "n_process": n_process,
        "renumber_sent_ids": renumber_sent_ids,
        "ignore_pipe_errors": ignore_pipe_errors,
        "split_on_newline": split_on_newline,
    }

    if input_file:
        conll_str = conll_parser.parse_file_as_conll(
            input_file, input_encoding=input_encoding, **parse_opts
        )
    else:
        conll_str = conll_parser.parse_text_as_conll(input_str, **parse_opts)

    if output_file is None:
        sys.stdout.write(conll_str)
    else:
        Path(output_file).write_text(conll_str, encoding=output_encoding)
        if verbose:
            print(conll_str, end="")


def main() -> None:
    """Parse the command-line arguments and call `run`."""
    cparser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Parse an input string or input file to CoNLL-U format"
        " with a spaCy, stanza or UDPipe pipeline. The output is written to"
        " stdout or to a file.",
    )

    cparser.add_argument(
        "model_or_lang",
        help="Model or language to use. spaCy models must be installed,"
        " stanza and UDPipe models are downloaded automatically.",
    )
    cparser.add_argument(
        "parser",
        choices=["spacy", "stanza", "udpipe"],
        help="Which parser to use. 'stanza' needs 'spacy-stanza' and 'udpipe'"
        " needs 'spacy-udpipe'.",
    )

    input_group = cparser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "-f",
        "--input-file",
        dest="input_file",
        help="Path to a text file to parse.",
    )
    input_group.add_argument(
        "--input-str",
        dest="input_str",
        help="Text to parse.",
    )
    cparser.add_argument(
        "--input-encoding",
        dest="input_encoding",
        default="utf-8",
        help="Encoding of the input file.",
    )

    cparser.add_argument(
        "-o",
        "--output-file",
        dest="output_file",
        help="Path to the output file. Without it, the output is printed to"
        " stdout.",
    )
    cparser.add_argument(
        "--output-encoding",
        dest="output_encoding",
        default="utf-8",
        help="Encoding of the output file.",
    )

    cparser.add_argument(
        "--disable-sbd",
        dest="disable_sbd",
        action="store_true",
        help="Disable automatic sentence boundary detection, so that every"
        " line is one sentence. '--is-tokenized' enables this as well."
        " Not supported for 'udpipe'.",
    )
    cparser.add_argument(
        "--is-tokenized",
        dest="is_tokenized",
        action="store_true",
        help="The text is already tokenized (tokens separated by whitespace)."
        " Sentences are then only split on newlines, so put one sentence on"
        " every line. Not supported for 'udpipe'.",
    )
    cparser.add_argument(
        "--include-headers",
        dest="include_headers",
        action="store_true",
        help="Write the '# sent_id' and '# text' comment lines before every"
        " sentence.",
    )
    cparser.add_argument(
        "--renumber-sent-ids",
        dest="renumber_sent_ids",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Number '# sent_id' consecutively over the whole input. Without"
        " it, the numbering restarts for every line of the input. Only"
        " applies with '--include-headers'.",
    )
    cparser.add_argument(
        "--n-process",
        dest="n_process",
        type=int,
        default=1,
        help="Number of processes for nlp.pipe(). -1 uses all cores. May not"
        " work for 'stanza' and 'udpipe'.",
    )
    cparser.add_argument(
        "--ignore-pipe-errors",
        dest="ignore_pipe_errors",
        action="store_true",
        help="Skip the checks that stop the program when '--n-process' is"
        " likely to fail on this system.",
    )
    cparser.add_argument(
        "--split-on-newline",
        dest="split_on_newline",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Split the input on newlines and process every line as a"
        " separate document, which is faster for long inputs.",
    )
    cparser.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        action="store_true",
        help="Also print the output to stdout when '--output-file' is given.",
    )

    run(**vars(cparser.parse_args()))


if __name__ == "__main__":
    main()
