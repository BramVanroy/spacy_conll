import re
from dataclasses import dataclass
from locale import getpreferredencoding
from pathlib import Path
from sys import stdout
from typing import Dict, Optional, Union

from spacy import Errors, Language
from spacy_stanza.tokenizer import StanzaTokenizer
from spacy_udpipe import UDPipeTokenizer

from spacy_conll import init_parser

SENT_ID_RE = re.compile(r"(?<=# sent_id = )(\d+)")


@dataclass
class ConllParser:
    """Parse an input string or input file to CoNLL-U format

    :param model_or_lang_or_nlp: model or language to use with the given 'parser'. SpaCy models must be pre-installed,
           stanza and udpipe models will be downloaded automatically. Alternatively, an instantiated NLP pipeline
           that includes the CoNLL Formatter component can be passed as well. In that case, 'parser' will be ignored.
    :param parser: which parser to use. Parsers other than 'spacy' need to be installed separately. Valid options
           are 'spacy', 'stanza', 'udpipe'. Note that the spacy-* wrappers of those libraries need
           to be installed, e.g. spacy-stanza.
    :param is_tokenized: indicates whether your text has already been tokenized (space-seperated). Setting this
           option has difference consequences for different parsers:
           - SpaCy will simply not do any further tokenisation: we simply split the tokens on whitespace, sentence
             segmentation still works as usual
           - Stanza will not tokenize but in addition, will also only do sentence splitting on
             newlines. No additional sentence segmentation is done.
           - For UDpipe we also simply disable tokenisation and use white-spaced tokens (works from 0.3.0 upwards).
             No further sentence segmentation is done.
    :param disable_sbd: disables spaCy automatic sentence boundary detection (works for spaCy)
    :param include_headers: to include headers before the output of every sentence
    :param no_force_counting: to disable force counting the 'sent_id', starting from 1 and increasing for each
           sentence
    :param n_process: number of processes to use in nlp.pipe(). -1 will use as many cores as available
    :param verbose: to print the output to stdout, regardless of 'output_file'
    """
    model_or_lang_or_nlp: Union[str, Language]
    parser: str = None
    is_tokenized: bool = False
    disable_sbd: bool = False
    conversion_maps: Optional[Dict[str, Dict[str, str]]] = None,
    ext_names: Optional[Dict[str, str]] = None,
    include_headers: bool = False,
    disable_pandas: bool = False,
    no_force_counting: bool = False
    n_process: int = 1
    verbose: bool = False
    nlp: Language = None

    def __post_init__(self):
        if isinstance(self.model_or_lang_or_nlp, Language):
            if "conll_formatter" not in self.model_or_lang_or_nlp.pipe_names:
                raise ValueError(Errors.E001.format(name="conll_formatter", opts=self.model_or_lang_or_nlp.pipe_names))
            self.nlp = self.model_or_lang_or_nlp

            # Figure out what kind of parser was provided (neede during data preparation)
            if isinstance(self.nlp.tokenizer, StanzaTokenizer):
                self.parser = "stanza"
            elif isinstance(self.nlp.tokenizer, UDPipeTokenizer):
                self.parser = "udpipe"
            else:
                self.parser = "spacy"
        else:
            # disable_pandas to prevent multiprocessing issues
            self.nlp = init_parser(
                self.model_or_lang_or_nlp,
                self.parser,
                is_tokenized=self.is_tokenized,
                disable_sbd=self.disable_sbd,
                conversion_maps=self.conversion_maps,
                ext_names=self.ext_names,
                include_headers=self.include_headers,
                disable_pandas=self.disable_pandas
            )

    def prepare_data(self, lines):
        if self.is_tokenized:
            if self.parser == "spacy":
                lines = [l.split() for l in lines]
            elif self.parser == "udpipe":
                lines = [[l.split()] for l in lines]

        return lines

    def parse_as_conll(self,
                       input_file: Optional[str] = None,
                       input_encoding: str = getpreferredencoding(),
                       input_str: Optional[str] = None):
        if not input_str and not input_file:
            raise ValueError("'input_file' or 'input_str' must be given. Use parse-as-conll -h for help.")

        # Gather input:
        # Collect lines in 'lines' variable, taking into account 'is_tokenized'
        if input_str:
            lines = [l.strip() for l in input_str.split("\n")]
        else:
            lines = Path(input_file).read_text(encoding=input_encoding).splitlines()

        lines = self.prepare_data(lines)

        conll_idx = 0
        output = ""
        for doc_idx, doc in enumerate(self.nlp.pipe(lines, n_process=self.n_process)):
            for sent in doc.sents:
                conll_idx += 1

                sent_as_conll = sent._.conll_str
                if self.include_headers and not self.no_force_counting:
                    # nlp.pipe returns different docs, meaning that the generated sentence indices
                    # by ConllFormatter are not consecutive (they reset for each new doc)
                    # We can do a regex replace to fix that, though.
                    sent_as_conll = re.sub(SENT_ID_RE, str(conll_idx), sent_as_conll, 1)

                # Newline madness dealing with writing to file and printing to stdout at the same time:
                # Prepend additional newline for all except the very first string.
                if not (doc_idx == 0 and sent.start == 0):
                    sent_as_conll = "\n" + sent_as_conll

                if self.verbose:
                    # end='' to avoid adding yet another newline
                    print(sent_as_conll, end="")

                output += sent_as_conll

        return output
