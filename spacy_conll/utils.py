from typing import Dict, List, Optional, Union

import spacy
from spacy.language import Language
from spacy.tokens import Doc
from spacy.vocab import Vocab

from . import ConllFormatter


class SpacyPretokenizedTokenizer:
    """Custom tokenizer to be used in spaCy when the text is already pretokenized."""

    def __init__(self, vocab: Vocab):
        """Initialize tokenizer with a given vocab
        :param vocab: an existing vocabulary (see https://spacy.io/api/vocab)
        """
        self.vocab = vocab

    def __call__(self, inp: Union[List[str], str]) -> Doc:
        """Call the tokenizer on input `inp`.
        :param inp: either a string to be split on whitespace, or a list of tokens
        :return: the created Doc object
        """
        if isinstance(inp, str):
            words = inp.split()
            spaces = [True] * (len(words) - 1) + ([True] if inp[-1].isspace() else [False])
            return Doc(self.vocab, words=words, spaces=spaces)
        elif isinstance(inp, list):
            return Doc(self.vocab, words=inp)
        else:
            raise ValueError("Unexpected input format. Expected string to be split on whitespace, or list of tokens.")


def init_parser(
    parser: str = "spacy",
    model_or_lang: str = "en",
    *,
    is_tokenized: bool = False,
    disable_sbd: bool = False,
    parser_opts: Optional[Dict] = None,
    **kwargs,
) -> Language:
    """Initialise a spacy-wrapped parser given a language or model and some options.
    :param parser: which parser to use. Parsers other than 'spacy' need to be installed separately. Valid options are
           'spacy', 'stanfordnlp', 'stanza', 'udpipe'. Note that the spacy-* wrappers of those libraries need to be
           installed, e.g. spacy-stanza. Defaults to 'spacy'
    :param model_or_lang: language model to use (must be installed). Defaults to an English model
    :param is_tokenized: indicates whether your text has already been tokenized (space-seperated). For stanza and
           stanfordnlp, this will also cause sentence segmentation *only* to be done by splitting on new lines.
           See the documentation: https://stanfordnlp.github.io/stanfordnlp/tokenize.html
           See the documentation: https://stanfordnlp.github.io/stanza/tokenize.html
    :param disable_sbd: disables spaCy automatic sentence boundary detection (only works for spaCy)
    :param parser_opts: will be passed to the core pipeline. For spacy and udpipe, it will be passed to their
           `.load()` initialisations, for stanfordnlp and stanza `pipeline_opts` is passed to to their `.Pipeline()`
           initialisations
    :param kwargs: options to be passed to the ConllFormatter initialisation
    :return: an initialised Language object; the parser
    """
    parser_opts = {} if parser_opts is None else parser_opts

    if parser == "spacy":
        nlp = spacy.load(model_or_lang, **parser_opts)
        if is_tokenized:
            nlp.tokenizer = SpacyPretokenizedTokenizer(nlp.vocab)
        if disable_sbd:
            nlp.add_pipe(_prevent_sbd, name="prevent-sbd", before="parser")
    elif parser == "stanfordnlp":
        import stanfordnlp
        from spacy_stanfordnlp import StanfordNLPLanguage

        snlp = stanfordnlp.Pipeline(lang=model_or_lang, tokenize_pretokenized=is_tokenized, **parser_opts)
        nlp = StanfordNLPLanguage(snlp)
    elif parser == "stanza":
        import stanza
        from spacy_stanza import StanzaLanguage

        snlp = stanza.Pipeline(lang=model_or_lang, tokenize_pretokenized=is_tokenized, **parser_opts)
        nlp = StanzaLanguage(snlp)
    elif parser == "udpipe":
        import spacy_udpipe

        nlp = spacy_udpipe.load(model_or_lang, **parser_opts)
    else:
        raise ValueError("Unexpected value for 'parser'. Options are: 'spacy', 'stanfordnlp', 'stanza', 'udpipe'")

    conllformatter = ConllFormatter(nlp, **kwargs)
    nlp.add_pipe(conllformatter, last=True)

    return nlp


def _prevent_sbd(doc: Doc):
    """Disables spaCy's sentence boundary detection."""
    for token in doc:
        token.is_sent_start = False
    return doc
