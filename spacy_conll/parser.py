import os
import re
from dataclasses import dataclass, field
from locale import getpreferredencoding
from os import PathLike
from pathlib import Path
from typing import List, Union

from spacy import Errors, Language
from spacy_conll.utils import STANZA_AVAILABLE, UDPIPE_AVAILABLE


if STANZA_AVAILABLE:
    from spacy_stanza.tokenizer import StanzaTokenizer

if UDPIPE_AVAILABLE:
    from spacy_udpipe import UDPipeTokenizer


SENT_ID_RE = re.compile(r"(?<=# sent_id = )(\d+)")


@dataclass(eq=False, repr=False)
class ConllParser:
    """Constructor for a ConllParser, which is a wrapper around a spaCy-like parser with a ConllFormatter
    component. This class simply provides convenience methods to parse text according to some options.

    Constructor arguments:
    :param nlp: instantiated spaCy-like parser
    :param is_tokenized: whether or not the expected input format is pre-tokenized. This must correspond with how
    'nlp' was initialized! If you initialized the 'nlp' object with 'init_parser', make sure you used 'is_tokenized'
    in the same way
    """
    nlp: Language
    is_tokenized: bool = False
    parser: str = field(init=False, default=None)

    def __post_init__(self):
        if "conll_formatter" not in self.nlp.pipe_names:
            raise ValueError(Errors.E001.format(name="conll_formatter", opts=self.nlp.pipe_names))

        # Figure out what kind of parser was provided (needed during data preparation)
        if isinstance(self.nlp.tokenizer, StanzaTokenizer):
            self.parser = "stanza"
            import torch
            torch.set_num_threads(1)
        elif isinstance(self.nlp.tokenizer, UDPipeTokenizer):
            self.parser = "udpipe"
        else:
            self.parser = "spacy"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(is_tokenized={self.is_tokenized}, parser={self.parser})"

    def prepare_data(self, lines: List[str]) -> List[str]:
        """Prepares data according to whether or not is_tokenized was given and depending on the parser.
        Each parser requires a different type of input when the data is pre_tokenized.
        :param lines: a list of lines to process
        :return: the lines in the correct format for the parser
        """
        if self.is_tokenized:
            if self.parser == "spacy":
                lines = [l.split() for l in lines]
            elif self.parser == "udpipe":
                lines = [[l.split()] for l in lines]

        return lines

    def parse_file_as_conll(
        self,
        input_file: Union[PathLike, Path, str],
        input_encoding: str = getpreferredencoding(),
        **kwargs
    ) -> str:
        """Parses a given input file with self.parser and returns its CoNLL output.
        :param input_file: path to the input file to process
        :param input_encoding: encoding of 'input_file'
        :param kwargs: keyword arguments that will be passed to `parse_text_as_conll`
        """

        text = Path(input_file).resolve().read_text(encoding=input_encoding)

        return self.parse_text_as_conll(text, **kwargs)

    def parse_text_as_conll(self,
                            text: str,
                            n_process: int = 1,
                            no_force_counting: bool = False,
                            ignore_pipe_errors: bool = False,
                            no_split_on_newline: bool = False) -> str:
        """Parses a given text (string) with self.parser and returns its CoNLL output.
        :param text: input text (string) to process
        :param n_process: number of processes to use in nlp.pipe(). -1 will use as many cores as available. Might not
               work for a 'parser' other than 'spacy' depending on your environment
        :param no_force_counting: whether to  disable force counting the 'sent_id', starting from 1 and increasing for
               each sentence. Instead, 'sent_id' will depend on how spaCy returns the sentences. Must have
               'self.include_headers' enabled
        :param ignore_pipe_errors: whether to ignore a priori errors concerning 'n_process' By default we try to
               determine whether processing works on your system and stop execution if we think it doesn't. If you
               know what you are doing, you can ignore such pre-emptive errors, though, and run the code as-is, which
               will then throw the default Python errors when applicable
        :param no_split_on_newline: by default, the input text will be split on newlines for faster processing. This
               can be disabled with this option
        """
        if n_process > 1 and not ignore_pipe_errors:
            if not self.nlp.get_pipe("conll_formatter").disable_pandas:
                raise OSError(
                    "Due to pandas serialisation, 'n_process' > 1 is not supported when"
                    " 'disable_pandas' is False in the ConllFormatter. Set 'n_process' to 1 or"
                    " initialise the ConllFormatter with 'disable_pandas=True'"
                )

            # Seems that Windows only supports mp on spaCy. Both for UDPipe and Stanza the issue is
            # pickling of the models
            if os.name == "nt" and self.parser in ["udpipe", "stanza"]:
                raise OSError(
                    "'n_process' > 1 is not supported on all platforms/all parsers. Please try again with"
                    " the default value 'n_process' = 1. You can also try to run the code without this pre-emptive"
                    " error message by using the 'ignore_pipe_errors' option"
                )

        if not no_split_on_newline:
            text = text.splitlines()

        text = self.prepare_data(text)

        conll_idx = 0
        output = ""
        for doc_idx, doc in enumerate(self.nlp.pipe(text, n_process=n_process)):
            for sent in doc.sents:
                conll_idx += 1

                sent_as_conll = sent._.conll_str
                if self.nlp.get_pipe("conll_formatter").include_headers and not no_force_counting:
                    # nlp.pipe returns different docs, meaning that the generated sentence indices
                    # by ConllFormatter are not consecutive (they reset for each new doc)
                    # We can do a regex replace to fix that, though.
                    sent_as_conll = re.sub(SENT_ID_RE, str(conll_idx), sent_as_conll, 1)

                # Prepend additional newline for all except the very first string.
                if not (doc_idx == 0 and sent.start == 0):
                    sent_as_conll = "\n" + sent_as_conll

                output += sent_as_conll

        return output
