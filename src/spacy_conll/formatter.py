"""The `conll_formatter` pipeline component."""

from dataclasses import dataclass, field

from spacy.language import Language
from spacy.tokens import Doc, Span, Token

from spacy_conll.utils import PD_AVAILABLE, merge_dicts_strict

if PD_AVAILABLE:
    import pandas as pd

CONLL_FIELD_NAMES = [
    "ID",
    "FORM",
    "LEMMA",
    "UPOS",
    "XPOS",
    "FEATS",
    "HEAD",
    "DEPREL",
    "DEPS",
    "MISC",
]

UD_WHITESPACE_ESCAPES = str.maketrans(
    {" ": "\\s", "\t": "\\t", "\n": "\\n", "\r": "\\r"}
)


def get_whitespace_misc(token: Token) -> str:
    r"""Describe the whitespace around a token in the MISC notation of UD.

    The whitespace after a token is its own trailing space plus the text of
    the whitespace tokens that follow it, also when these tokens belong to
    the next sentence. A single space gives `_`, no whitespace gives
    `SpaceAfter=No` and anything else gives `SpacesAfter` with the escapes
    `\s`, `\t`, `\n` and `\r`. Whitespace at the start of the doc gives
    `SpacesBefore` on the first token that is not whitespace. See
    https://universaldependencies.org/misc.html.

    Args:
        token: A token that is not whitespace.

    Returns:
        The MISC value.

    Examples:
        >>> import spacy
        >>> doc = spacy.blank("en")("\nHello  world.\t")
        >>> [t.text for t in doc]
        ['\n', 'Hello', ' ', 'world', '.', '\t']
        >>> [get_whitespace_misc(t) for t in doc if not t.is_space]
        ['SpacesAfter=\\s\\s|SpacesBefore=\\n', 'SpaceAfter=No', 'SpacesAfter=\\t']
    """
    spaces_after = token.whitespace_
    for next_token in token.doc[token.i + 1 :]:
        if not next_token.is_space:
            break
        spaces_after += next_token.text_with_ws

    misc = []
    if not spaces_after:
        misc.append("SpaceAfter=No")
    elif spaces_after != " ":
        misc.append(
            f"SpacesAfter={spaces_after.translate(UD_WHITESPACE_ESCAPES)}"
        )

    preceding = token.doc[: token.i]
    if len(preceding) and all(t.is_space for t in preceding):
        spaces_before = preceding.text_with_ws
        misc.append(
            f"SpacesBefore={spaces_before.translate(UD_WHITESPACE_ESCAPES)}"
        )

    return "|".join(misc) or "_"


@dataclass
class ConllFormatter:
    r"""spaCy component that adds CoNLL-U representations to docs, sentences and tokens.

    The extension `conll` holds a dict of field names to values on a
    `Token`, a list of those dicts on a sentence `Span`, and a list of
    sentence lists on a `Doc`. The extension `conll_str` holds the
    tab-separated CoNLL-U text, and `conll_pd` (when pandas is installed and
    `disable_pandas` is false) holds a pandas `Series` or `DataFrame`.
    Multi-word tokens and empty nodes are not supported.

    Args:
        conversion_maps: Maps a field name to a map of output values, for
            example `{"LEMMA": {"-PRON-": "PRON"}}` replaces the lemma
            `-PRON-` with `PRON`.
        ext_names: New names for the extensions `conll`, `conll_str` and
            `conll_pd`, for example `{"conll": "conll_dict"}`.
        field_names: New names for the CoNLL-U fields `ID`, `FORM`, `LEMMA`,
            `UPOS`, `XPOS`, `FEATS`, `HEAD`, `DEPREL`, `DEPS` and `MISC`,
            for example `{"UPOS": "upostag"}`.
        include_headers: Whether `conll_str` of a sentence starts with the
            `# sent_id` and `# text` comment lines.
        disable_pandas: Whether to skip the `conll_pd` extension even if
            pandas is installed. This avoids pickling problems with
            multiprocessing.

    Examples:
        >>> import spacy
        >>> nlp = spacy.blank("en")
        >>> _ = nlp.add_pipe("sentencizer")
        >>> _ = nlp.add_pipe(
        ...     "conll_formatter", config={"include_headers": True}
        ... )
        >>> doc = nlp("Hello world.")
        >>> doc[1]._.conll  # doctest: +NORMALIZE_WHITESPACE
        {'ID': 2, 'FORM': 'world', 'LEMMA': '_', 'UPOS': '_', 'XPOS': '_',
         'FEATS': '_', 'HEAD': 2, 'DEPREL': '_', 'DEPS': '_',
         'MISC': 'SpaceAfter=No'}
        >>> print(doc._.conll_str.replace("\t", " "))
        # sent_id = 1
        # text = Hello world.
        1 Hello _ _ _ _ 1 _ _ _
        2 world _ _ _ _ 2 _ _ SpaceAfter=No
        3 . _ _ _ _ 3 _ _ SpaceAfter=No
        <BLANKLINE>
    """

    conversion_maps: dict[str, dict[str, str]] | None = None
    ext_names: dict[str, str] = field(default_factory=dict)
    field_names: dict[str, str] = field(default_factory=dict)
    include_headers: bool = False
    disable_pandas: bool = False

    def __post_init__(self):
        """Merge the custom names into the defaults and register extensions."""
        default_ext_names = {
            "conll_str": "conll_str",
            "conll": "conll",
            "conll_pd": "conll_pd",
        }
        self.ext_names = merge_dicts_strict(default_ext_names, self.ext_names)
        default_field_names = {fname: fname for fname in CONLL_FIELD_NAMES}
        self.field_names = merge_dicts_strict(
            default_field_names, self.field_names
        )

        self._set_extensions()

    def __call__(self, doc: Doc) -> Doc:
        """Set the CoNLL extensions on `doc`, its sentences and its tokens.

        Args:
            doc: The input doc.

        Returns:
            The same doc with the extensions set.
        """
        # Worker processes on Windows do not inherit the registered
        # extensions (https://github.com/explosion/spaCy/issues/4903).
        self._set_extensions()

        sents = []
        for sent in doc.sents:
            if all(token.is_space for token in sent):
                self._set_span_conll(sent)
            else:
                sents.append(sent)
                self._set_span_conll(sent, len(sents))

        doc._.set(
            self.ext_names["conll"],
            [s._.get(self.ext_names["conll"]) for s in sents],
        )
        doc._.set(
            self.ext_names["conll_str"],
            "\n".join([s._.get(self.ext_names["conll_str"]) for s in sents]),
        )

        if PD_AVAILABLE and not self.disable_pandas:
            sent_dfs = [s._.get(self.ext_names["conll_pd"]) for s in sents]
            doc._.set(
                self.ext_names["conll_pd"],
                pd.concat(sent_dfs).reset_index(drop=True)
                if sent_dfs
                else pd.DataFrame(columns=list(self.field_names.values())),
            )

        return doc

    def _map_conll(
        self, token_conll_d: dict[str, str | int]
    ) -> dict[str, str | int]:
        """Replace values in `token_conll_d` according to `conversion_maps`.

        Args:
            token_conll_d: A token's CoNLL dict (field name to value). It is
                modified in place.

        Returns:
            The updated dict.
        """
        for k, v in token_conll_d.items():
            try:
                token_conll_d[k] = self.conversion_maps[k][v]
            except KeyError:
                continue

        return token_conll_d

    def _set_span_conll(self, span: Span, span_idx: int = 1):
        """Set the CoNLL extensions on a sentence and its tokens.

        Whitespace tokens get no CoNLL line and their extensions are `None`.
        Their whitespace goes to MISC of a neighbouring token (see
        `get_whitespace_misc`) and the IDs skip them. A sentence of only
        whitespace tokens gets an empty `conll_str` and no header.

        Args:
            span: A sentence.
            span_idx: The 1-based index of the sentence in its doc, used for
                `# sent_id` when the sentence has no `conll_metadata`.
        """
        words = [t for t in span if not t.is_space]
        token_ids = {t.i: idx for idx, t in enumerate(words, 1)}

        span_conll_str = ""
        if self.include_headers and words:
            if not (
                span.has_extension("conll_metadata") and span._.conll_metadata
            ):
                text = " ".join(span.text.split())
                span._.conll_metadata = (
                    f"# sent_id = {span_idx}\n# text = {text}\n"
                )

            span_conll_str += span._.conll_metadata

        for token in span:
            if token.is_space:
                for ext_name in self.ext_names.values():
                    if token.has_extension(ext_name):
                        token._.set(ext_name, None)
            else:
                self._set_token_conll(token, token_ids[token.i], token_ids)

        span._.set(
            self.ext_names["conll"],
            [t._.get(self.ext_names["conll"]) for t in words],
        )
        span_conll_str += "".join(
            [t._.get(self.ext_names["conll_str"]) for t in words]
        )
        span._.set(self.ext_names["conll_str"], span_conll_str)

        if PD_AVAILABLE and not self.disable_pandas:
            span._.set(
                self.ext_names["conll_pd"],
                pd.DataFrame(
                    [t._.get(self.ext_names["conll"]) for t in words],
                    columns=list(self.field_names.values()),
                ),
            )

    def _set_token_conll(
        self,
        token: Token,
        token_idx: int = 1,
        token_ids: dict[int, int] | None = None,
    ) -> Token:
        """Set the CoNLL extensions on a token that is not whitespace.

        A head that is a whitespace token is replaced by the nearest
        ancestor that is not whitespace. If there is none, the token becomes
        a root.

        Args:
            token: A token.
            token_idx: The 1-based index of the token in its sentence.
            token_ids: Maps the doc index of every token in the sentence that
                is not whitespace to its CoNLL ID. If not given, the IDs are
                the positions in the sentence.

        Returns:
            The same token.
        """
        head = token.head
        while head.is_space and head.head.i != head.i:
            head = head.head

        if token.dep_.lower().strip() == "root" or head.is_space:
            head_idx = 0
            deprel = "root"
        elif token_ids is None:
            head_idx = head.i + 1 - token.sent[0].i
            deprel = token.dep_ or "_"
        else:
            head_idx = token_ids[head.i]
            deprel = token.dep_ or "_"

        token._.conll_misc_field = get_whitespace_misc(token)

        token_conll = (
            token_idx,
            token.text,
            token.lemma_ or "_",
            token.pos_ or "_",
            token.tag_ or "_",
            str(token.morph) if token.has_morph and str(token.morph) else "_",
            head_idx,
            deprel,
            token._.conll_deps_graphs_field,
            token._.conll_misc_field,
        )

        token_conll_d = dict(
            zip(self.field_names.values(), token_conll, strict=True)
        )

        if self.conversion_maps:
            token_conll_d = self._map_conll(token_conll_d)

        token._.set(self.ext_names["conll"], token_conll_d)
        token_conll_str = "\t".join(map(str, token_conll_d.values())) + "\n"
        token._.set(self.ext_names["conll_str"], token_conll_str)

        if PD_AVAILABLE and not self.disable_pandas:
            token._.set(self.ext_names["conll_pd"], pd.Series(token_conll_d))

        return token

    def _set_extensions(self):
        """Register the extensions that do not exist yet."""
        for obj in Doc, Span, Token:
            if not obj.has_extension(self.ext_names["conll_str"]):
                obj.set_extension(self.ext_names["conll_str"], default=None)
            if not obj.has_extension(self.ext_names["conll"]):
                obj.set_extension(self.ext_names["conll"], default=None)

            if (
                PD_AVAILABLE
                and not self.disable_pandas
                and not obj.has_extension(self.ext_names["conll_pd"])
            ):
                obj.set_extension(self.ext_names["conll_pd"], default=None)

        # CoNLL-U fields that spaCy does not store. ConllParser fills them
        # when it reads CoNLL-U text.
        if not Token.has_extension("conll_deps_graphs_field"):
            Token.set_extension("conll_deps_graphs_field", default="_")
        if not Token.has_extension("conll_misc_field"):
            Token.set_extension("conll_misc_field", default="_")
        if not Span.has_extension("conll_metadata"):
            Span.set_extension("conll_metadata", default=None)


@Language.factory(
    "conll_formatter",
    default_config={
        "conversion_maps": None,
        "ext_names": None,
        "field_names": None,
        "include_headers": False,
        "disable_pandas": False,
    },
)
def create_conll_formatter(
    nlp: Language,
    name: str,
    conversion_maps: dict[str, dict[str, str]] | None = None,
    ext_names: dict[str, str] | None = None,
    field_names: dict[str, str] | None = None,
    include_headers: bool = False,
    disable_pandas: bool = False,
) -> ConllFormatter:
    """Create the `conll_formatter` pipeline component.

    Args:
        nlp: The pipeline, as required by spaCy.
        name: The component name, as required by spaCy.
        conversion_maps: See `ConllFormatter`.
        ext_names: See `ConllFormatter`.
        field_names: See `ConllFormatter`.
        include_headers: See `ConllFormatter`.
        disable_pandas: See `ConllFormatter`.

    Returns:
        The component.
    """
    return ConllFormatter(
        conversion_maps=conversion_maps,
        ext_names=ext_names or {},
        field_names=field_names or {},
        include_headers=include_headers,
        disable_pandas=disable_pandas,
    )
