"""Parser initialization, pretokenization and sentence segmentation helpers."""

from typing import Any, Literal

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
    parser: Literal["spacy", "stanza", "udpipe"],
    *,
    is_tokenized: bool = False,
    disable_sbd: bool = False,
    exclude_spacy_components: list[str] | None = None,
    parser_opts: dict[str, Any] | None = None,
    formatter_config: dict[str, Any] | None = None,
) -> Language:
    """Load a spaCy, stanza or UDPipe pipeline and add `conll_formatter` last.

    The stanza and UDPipe backends need `spacy-stanza` or `spacy-udpipe` and
    download their model automatically. A spaCy model must be installed.

    Args:
        model_or_lang: Name of a spaCy model (`"en_core_web_sm"`) or a
            language code for stanza and UDPipe (`"en"`).
        parser: The backend to use.
        is_tokenized: Whether the input text is already split into tokens
            separated by whitespace. For spaCy this also disables sentence
            segmentation. For stanza, sentences are then only split on
            newlines. UDPipe does not support this option.
        disable_sbd: Whether to disable automatic sentence boundary
            detection in spaCy and stanza. Stanza then expects sentences
            that are separated by two newlines. UDPipe does not support this
            option.
        exclude_spacy_components: spaCy components to exclude from the
            pipeline, which speeds up processing. Only used for spaCy.
        parser_opts: Keyword arguments for `spacy.load` (spaCy) or
            `spacy_stanza.load_pipeline` (stanza). The stanza option
            `verbose` is also passed to `stanza.download`. Ignored for
            UDPipe.
        formatter_config: Config for the `conll_formatter` component, for
            example `{"include_headers": True}`. See `ConllFormatter`.

    Returns:
        The pipeline with `conll_formatter` as its last component.

    Raises:
        ValueError: If `parser` is not one of the supported backends.

    Examples:
        >>> nlp = init_parser(
        ...     "en_core_web_sm",
        ...     "spacy",
        ...     formatter_config={"include_headers": True},
        ... )
        >>> nlp.pipe_names[-1]
        'conll_formatter'
    """
    parser_opts = dict(parser_opts or {})

    if parser == "spacy":
        exclude = (
            ["senter", "sentencizer"] if disable_sbd or is_tokenized else []
        )
        exclude += exclude_spacy_components or []
        nlp = spacy.load(model_or_lang, exclude=exclude, **parser_opts)
        if is_tokenized:
            nlp.tokenizer = SpacyPretokenizedTokenizer(nlp.vocab)
        if disable_sbd or is_tokenized:
            try:
                nlp.add_pipe("disable_sbd", before="parser")
            except ValueError:
                nlp.add_pipe("disable_sbd", first=True)
    elif parser == "stanza":
        import spacy_stanza
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
        import spacy_udpipe

        spacy_udpipe.download(model_or_lang)
        nlp = spacy_udpipe.load(model_or_lang)
    else:
        raise ValueError(
            f"Unexpected value {parser!r} for 'parser'. Options are: 'spacy',"
            " 'stanza', 'udpipe'"
        )

    nlp.add_pipe("conll_formatter", config=formatter_config or {}, last=True)

    return nlp


def merge_dicts_strict(d1: dict, d2: dict) -> dict:
    """Overwrite the values of `d1` with those of `d2`, in place.

    Every key of `d2` must already exist in `d1`.

    Args:
        d1: The base dict. It is modified in place.
        d2: The new values.

    Returns:
        The updated `d1`.

    Raises:
        KeyError: If `d2` has a key that is not in `d1`.

    Examples:
        >>> merge_dicts_strict({"conll": "conll"}, {"conll": "conllu"})
        {'conll': 'conllu'}
        >>> merge_dicts_strict({"conll": "conll"}, {"conlll": "conllu"})
        Traceback (most recent call last):
        ...
        KeyError: "Unknown key 'conlll'. Valid keys are ['conll']"
    """
    for k, v in d2.items():
        if k not in d1:
            raise KeyError(f"Unknown key {k!r}. Valid keys are {list(d1)}")
        d1[k] = v

    return d1


class SpacyPretokenizedTokenizer:
    """spaCy tokenizer that splits text on whitespace only.

    Args:
        vocab: The vocab of the pipeline.

    Examples:
        >>> tokenizer = SpacyPretokenizedTokenizer(Vocab())
        >>> [t.text for t in tokenizer("He 's here .")]
        ['He', "'s", 'here', '.']
        >>> len(tokenizer(""))
        0
    """

    def __init__(self, vocab: Vocab):
        """Store the vocab."""
        self.vocab = vocab

    def __call__(self, inp: str) -> Doc:
        """Split `inp` on whitespace into a `Doc`.

        Args:
            inp: The text to split.

        Returns:
            A `Doc` with one token per whitespace-separated part. The last
            token has trailing whitespace only if `inp` ends with
            whitespace.

        Raises:
            ValueError: If `inp` is not a string.
        """
        if not isinstance(inp, str):
            raise ValueError(
                "Unexpected input format. Expected string to be split on"
                " whitespace."
            )

        words = inp.split()
        spaces = [True] * len(words)
        if words and not inp[-1].isspace():
            spaces[-1] = False
        return Doc(self.vocab, words=words, spaces=spaces)


class SpacyDisableSentenceSegmentation:
    """spaCy component that marks every token as not starting a sentence.

    This disables the sentence boundaries of the dependency parser. The
    `senter` and `sentencizer` components must be excluded as well.
    """

    def __call__(self, doc: Doc) -> Doc:
        """Set `is_sent_start` to `False` for every token.

        Args:
            doc: The input doc.

        Returns:
            The same doc.
        """
        for token in doc:
            token.is_sent_start = False
        return doc


@Language.factory("disable_sbd")
def create_spacy_disable_sentence_segmentation(
    nlp: Language, name: str
) -> SpacyDisableSentenceSegmentation:
    """Create the `disable_sbd` pipeline component.

    Args:
        nlp: The pipeline, as required by spaCy.
        name: The component name, as required by spaCy.

    Returns:
        The component.
    """
    return SpacyDisableSentenceSegmentation()
