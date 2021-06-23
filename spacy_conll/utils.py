from typing import Dict, Optional

from .tokenizer import SpacyPretokenizedTokenizer

import spacy
from spacy.language import Language
from spacy.tokens import Doc

try:
    import pandas as pd

    PD_AVAILABLE = True
except ImportError:
    PD_AVAILABLE = False


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
           'spacy', 'stanza', 'udpipe'. Note that the spacy-* wrappers of those libraries need to be
           installed, e.g. spacy-stanza. Defaults to 'spacy'
    :param model_or_lang: language model to use (must be installed). Defaults to an English model
    :param is_tokenized: indicates whether your text has already been tokenized (space-seperated). For stanza,
           this will also cause sentence segmentation *only* to be done by splitting on new lines.
           See the documentation: https://stanfordnlp.github.io/stanza/tokenize.html
    :param disable_sbd: disables spaCy automatic sentence boundary detection (only works for spaCy)
    :param parser_opts: will be passed to the core pipeline. For spacy and udpipe, it will be passed to their
           `.load()` initialisations, for stanza `pipeline_opts` is passed to to their `.Pipeline()`
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
    elif parser == "stanza":
        import stanza
        import spacy_stanza
        stanza.download(model_or_lang)
        nlp = spacy_stanza.load_pipeline(model_or_lang, tokenize_pretokenized=is_tokenized, **parser_opts)
    elif parser == "udpipe":
        import spacy_udpipe
        spacy_udpipe.download(model_or_lang)
        nlp = spacy_udpipe.load(model_or_lang)
    else:
        raise ValueError("Unexpected value for 'parser'. Options are: 'spacy', 'stanza', 'udpipe'")

    nlp.add_pipe("conll_formatter", config=kwargs, last=True)

    return nlp


def _prevent_sbd(doc: Doc):
    """Disables spaCy's sentence boundary detection."""
    for token in doc:
        token.is_sent_start = False
    return doc
