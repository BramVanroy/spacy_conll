from typing import Dict, List, Optional

import spacy
from spacy.language import Language
from spacy.tokens import Doc
from spacy.vocab import Vocab


try:
    import pandas as pd  # noqa: F401

    PD_AVAILABLE = True
except ImportError:
    PD_AVAILABLE = False

try:
    import spacy_stanza  # noqa: F401

    STANZA_AVAILABLE = True
except ImportError:
    STANZA_AVAILABLE = False

try:
    import spacy_udpipe  # noqa: F401

    UDPIPE_AVAILABLE = True
except ImportError:
    UDPIPE_AVAILABLE = False


def init_parser(
    model_or_lang: str,
    parser: str,
    *,
    is_tokenized: bool = False,
    disable_sbd: bool = False,
    exclude_spacy_components: Optional[List[str]] = None,
    parser_opts: Optional[Dict] = None,
    **kwargs,
) -> Language:
    """Initialise a spacy-wrapped parser given a language or model and some options.
    :param model_or_lang: language model to use (must be installed for spaCy but will be automatically downloaded for
           stanza and UDPipe)
    :param parser: which parser to use. Parsers other than 'spacy' need to be installed separately. Valid options are
           'spacy', 'stanza', 'udpipe'. Note that the spacy-* wrappers of those libraries need to be
           installed, e.g. spacy-stanza
    :param is_tokenized: indicates whether your text has already been tokenized (space-seperated). When using 'spacy',
           this option also disabled sentence segmentation completely. For stanza, sentence segmentation will *only*
           be done by splitting on new lines.

           See the stanza documentation for more:
           https://stanfordnlp.github.io/stanza/tokenize.html#start-with-pretokenized-text

           This option is not supported in UDPipe.
    :param disable_sbd: disables automatic sentence boundary detection in spaCy and stanza. For stanza, make sure that
           your input is in the correct format, that is: sentences must be separated by two new lines. If you want to
           disable both tokenization and sentence segmentation in stanza, do not enable this option but instead only
           use `is_tokenized` and make sure your sentences are separated by only one new line.

           See the stanza documentation for more:
           https://stanfordnlp.github.io/stanza/tokenize.html#tokenization-without-sentence-segmentation

           This option is not supported in UDPipe.
    :param exclude_spacy_components: spaCy components to exclude from the pipeline, which can greatly improve
           processing speed. Only works when using spaCy as a parser.
    :param parser_opts: will be passed to the core pipeline. For spacy, it will be passed to its
           `.load()` initialisations, for stanza `pipeline_opts` is passed to its `.load_pipeline()`
           initialisations. UDPipe does not have any keyword arguments
    :param kwargs: options to be passed to the ConllFormatter initialisation
    :return: an initialised Language object; the parser
    """
    parser_opts = {} if parser_opts is None else parser_opts

    if parser == "spacy":
        exclude = ["senter", "sentencizer"] if disable_sbd or is_tokenized else []
        exclude = exclude + exclude_spacy_components if exclude_spacy_components is not None else exclude
        nlp = spacy.load(model_or_lang, exclude=exclude, **parser_opts)
        if is_tokenized:
            nlp.tokenizer = SpacyPretokenizedTokenizer(nlp.vocab)
        if disable_sbd or is_tokenized:
            try:
                nlp.add_pipe("disable_sbd", before="parser")
            except ValueError:
                nlp.add_pipe("disable_sbd", first=True)
    elif parser == "stanza":
        import spacy_stanza  # noqa: F811
        import stanza

        verbose = parser_opts.pop("verbose", False)
        stanza.download(model_or_lang, verbose=verbose)
        nlp = spacy_stanza.load_pipeline(
            model_or_lang,
            verbose=verbose,
            tokenize_no_ssplit=disable_sbd,
            tokenize_pretokenized=is_tokenized,
            **parser_opts,
        )
    elif parser == "udpipe":
        import spacy_udpipe  # noqa: F811

        spacy_udpipe.download(model_or_lang)
        nlp = spacy_udpipe.load(model_or_lang)
    else:
        raise ValueError("Unexpected value for 'parser'. Options are: 'spacy', 'stanza', 'udpipe'")

    nlp.add_pipe("conll_formatter", config=kwargs, last=True)

    return nlp


def merge_dicts_strict(d1: Dict, d2: Dict) -> Dict:
    """Merge two dicts in a strict manner, i.e. the second dict overwrites keys
    of the first dict but all keys in the second dict have to be present in
    the first dict.
    :param d1: base dict which will be overwritten
    :param d2: dict with new values that will overwrite d1
    :return: the merged dict (but d1 will be modified in-place anyway!)
    """
    for k, v in d2.items():
        if k not in d1:
            raise KeyError(f"This key does not exist in the original dict. Valid keys are {list(d1.keys())}")
        d1[k] = v

    return d1


class SpacyPretokenizedTokenizer:
    """Custom tokenizer to be used in spaCy when the text is already pretokenized."""

    def __init__(self, vocab: Vocab):
        """Initialize tokenizer with a given vocab
        :param vocab: an existing vocabulary (see https://spacy.io/api/vocab)
        """
        self.vocab = vocab

    def __call__(self, inp: str) -> Doc:
        """Call the tokenizer on input `inp`.
        :param inp: a string to be split on whitespaces
        :return: the created Doc object
        """
        if isinstance(inp, str):
            words = inp.split()
            spaces = [True] * (len(words) - 1) + ([True] if inp[-1].isspace() else [False])
            return Doc(self.vocab, words=words, spaces=spaces)
        else:
            raise ValueError("Unexpected input format. Expected string to be split on whitespace.")


@Language.factory("disable_sbd")
def create_spacy_disable_sentence_segmentation(nlp: Language, name: str):
    return SpacyDisableSentenceSegmentation()


class SpacyDisableSentenceSegmentation:
    """Disables spaCy's dependency-based sentence boundary detection. In addition, senter and sentencizer components
    need to be disabled as well."""

    def __call__(self, doc: Doc) -> Doc:
        for token in doc:
            token.is_sent_start = False
        return doc
