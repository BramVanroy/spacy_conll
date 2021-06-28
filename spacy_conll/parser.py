import re
from dataclasses import dataclass, field
from locale import getpreferredencoding
from os import PathLike
from pathlib import Path
from pickle import PickleError
from typing import Union

from spacy import Errors, Language
from spacy_stanza.tokenizer import StanzaTokenizer
from spacy_udpipe import UDPipeTokenizer


SENT_ID_RE = re.compile(r"(?<=# sent_id = )(\d+)")


@dataclass
class ConllParser:
    """Parse an input string or input file to CoNLL-U format

    :param nlp: an instantiated NLP pipeline that includes the CoNLL Formatter component
    :param is_tokenized: indicates whether your text has already been tokenized (space-seperated). Setting this
           option has difference consequences for different parsers:
           - SpaCy will simply not do any further tokenisation: we simply split the tokens on whitespace, sentence
             segmentation still works as usual
           - Stanza will not tokenize but in addition, will also only do sentence splitting on
             newlines. No additional sentence segmentation is done.
           - For UDpipe we also simply disable tokenisation and use white-spaced tokens. No further sentence
             segmentation is done.
    :param include_headers: to include headers before the output of every sentence
    :param no_force_counting: to disable force counting the 'sent_id', starting from 1 and increasing for each
           sentence
    :param n_process: number of processes to use in nlp.pipe(). -1 will use as many cores as available
    """
    nlp: Language
    is_tokenized: bool = False
    parser: str = field(init=False, default=None)

    def __post_init__(self):
        if "conll_formatter" not in self.nlp.pipe_names:
            raise ValueError(Errors.E001.format(name="conll_formatter", opts=self.nlp.pipe_names))

        # throw error if pandas is enabled and n_process > 1? Might lead to errors

        # Figure out what kind of parser was provided (neede during data preparation)
        if isinstance(self.nlp.tokenizer, StanzaTokenizer):
            self.parser = "stanza"
        elif isinstance(self.nlp.tokenizer, UDPipeTokenizer):
            self.parser = "udpipe"
        else:
            self.parser = "spacy"

    def prepare_data(self, lines):
        if self.is_tokenized:
            if self.parser == "spacy":
                lines = [l.split() for l in lines]
            elif self.parser == "udpipe":
                lines = [[l.split()] for l in lines]

        return lines

    def parse_as_conll(self,
                       input_file: Union[PathLike, Path, str],
                       input_encoding: str = getpreferredencoding(),
                       n_process: int = 1,
                       include_headers: bool = False,
                       no_force_counting: bool = False
                       ):
        if n_process > 1 and not self.nlp.get_pipe("conll_formatter").disable_pandas:
            raise ValueError("Due to pandas serialisation issues, 'n_process' > 1 is not supported when"
                             " 'disable_pandas' is False in the ConllFormatter. Set 'n_process' to 1 or"
                             " initialise the ConllFormatter with 'disable_pandas=True'")

        lines = Path(input_file).resolve().read_text(encoding=input_encoding).splitlines()
        lines = self.prepare_data(lines)

        conll_idx = 0
        output = ""
        try:
            for doc_idx, doc in enumerate(self.nlp.pipe(lines, n_process=n_process)):
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

                    output += sent_as_conll
        except (EOFError, TypeError, PickleError) as exc:
            if n_process > 1:
                raise ValueError("It seems that something went wrong when processing with 'n_process' > 1. This is not"
                                 " supported on all platforms/all parsers. Please try again with the default value"
                                 " 'n_process' = 1.") from exc
            else:
                raise exc

        return output
