from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Dict, Optional, Union

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
    conversion_maps: Optional[Dict[str, Dict[str, str]]] = None,
    ext_names: Optional[Dict[str, str]] = None,
    field_names: Dict[str, str] = None,
    include_headers: bool = False,
    disable_pandas: bool = False,
):
    return ConllFormatter(
        conversion_maps=conversion_maps,
        ext_names=ext_names if ext_names else {},
        field_names=field_names if field_names else {},
        include_headers=include_headers,
        disable_pandas=disable_pandas,
    )


@dataclass
class ConllFormatter:
    """Pipeline component for spaCy that adds CoNLL-U-style properties to a Doc, its sentence `Span`s, and Tokens.
    By default, the custom properties `conll` and `conll_str` are added. If `pandas` is installed,
    `conll_pd` is added as well.

    - `conll`: raw CoNLL format
        - in `Token`: a dictionary containing all the expected CoNLL fields as keys and the parsed properties as
          values.
        - in sentence `Span`: a list of its tokens' `conll` dictionaries (list of dictionaries).
        - in a `Doc`: a list of its sentences' `conll` lists (list of list of dictionaries).
    - `conll_str`: string representation of the CoNLL format
        - in `Token`: tab-separated representation of the contents of the CoNLL fields ending with a newline.
        - in sentence `Span`: the expected CoNLL format where each row represents a token. When
          `ConllFormatter(include_headers=True)` is used, two header lines are included as well, as per the
          `CoNLL format`_.
        - in `Doc`: all its sentences' `conll_str` combined and separated by new lines.
    - `conll_pd`: `pandas` representation of the CoNLL format
        - in `Token`: a `Series` representation of this token's CoNLL properties.
        - in sentence `Span`: a `DataFrame` representation of this sentence, with the CoNLL names as column
          headers.
        - in `Doc`: a concatenation of its sentences' `DataFrame`'s, leading to a new a `DataFrame` whose
          index is reset.

    Multi-word tokens and empty nodes are not supported. See: https://universaldependencies.org/format.html#words-tokens-and-empty-nodes

    Constructor arguments:
    :param nlp: an initialized spaCy-like nlp object
    :param name: a string, as reauired by spaCy
    :param conversion_maps: two-level dictionary that contains a field_name (e.g. 'lemma', 'upostag')
    on the first level, and the conversion map on the second.
    E.g. {'lemma': {'-PRON-': 'PRON'}} will map the lemma '-PRON-' to 'PRON'
    :param ext_names: dictionary containing names for the custom spaCy extensions. You can rename the following
    extensions (use as keys): 'conll', 'conll_pd', 'conll_str'. E.g. {'conll': 'conll_dict', 'conll_pd': 'conll_pandas'}
     will rename the properties accordingly
    :param field_names: dictionary containing names for custom field names in case you do not want to use default
     CoNLL-U field names. You can rename the following fields (use as keys): 'ID', 'FORM', 'LEMMA', 'UPOS', 'XPOS',
     'FEATS', 'HEAD', 'DEPREL', 'DEPS', 'MISC'. E.g. {'UPOS': 'upostag'} will rename the field name UPOS accordingly.
    :param include_headers: whether to include the CoNLL headers in the conll_str string output. These consist
    of two lines containing the sentence id and the text as per the CoNLL format
    https://universaldependencies.org/format.html#sentence-boundaries-and-comments.
    :param disable_pandas: whether to disable pandas integration even if it is installed. This is particularly
    useful to avoid issues when using multiprocessing.
    """

    conversion_maps: Optional[Dict[str, Dict[str, str]]] = None
    ext_names: Dict[str, str] = field(default_factory=dict)
    field_names: Dict[str, str] = field(default_factory=dict)
    include_headers: bool = False
    disable_pandas: bool = False

    def __post_init__(self):
        # Set custom attribute names so that users can access them with their own preference
        default_ext_names = {"conll_str": "conll_str", "conll": "conll", "conll_pd": "conll_pd"}
        self.ext_names = merge_dicts_strict(default_ext_names, self.ext_names)
        default_field_names = {fname: fname for fname in CONLL_FIELD_NAMES}
        self.field_names = merge_dicts_strict(default_field_names, self.field_names)

        # Initialize extensions
        self._set_extensions()

    def __call__(self, doc: Doc) -> Doc:
        """Runs the pipeline component, adding the extensions to Underscore ._.. Adds a string representation,
        string representation containing a header, and a tuple representation of the CoNLL format to the
        given Doc and its sentences.
        :param doc: the input Doc
        :return: the modified Doc containing the newly added extensions
        """
        # We need to hook the extensions again when using
        # multiprocessing in Windows
        # see: https://github.com/explosion/spaCy/issues/4903
        self._set_extensions()

        for sent_idx, sent in enumerate(doc.sents, 1):
            self._set_span_conll(sent, sent_idx)

        doc._.set(self.ext_names["conll"], [s._.get(self.ext_names["conll"]) for s in doc.sents])
        doc._.set(
            self.ext_names["conll_str"],
            "\n".join([s._.get(self.ext_names["conll_str"]) for s in doc.sents]),
        )

        if PD_AVAILABLE and not self.disable_pandas:
            doc._.set(
                self.ext_names["conll_pd"],
                pd.concat([s._.get(self.ext_names["conll_pd"]) for s in doc.sents]).reset_index(drop=True),
            )

        return doc

    def _map_conll(self, token_conll_d: Dict[str, Union[str, int]]) -> Dict[str, Union[str, int]]:
        """Maps labels according to a given `self._conversion_maps`.
        This can be useful when users want to change the output labels of a
        model to their own tagset.

        :param token_conll_d: a token's conll representation as dict (field_name: value)
        :return: the modified dict where the labels have been replaced according to the converison maps
        """
        for k, v in token_conll_d.items():
            try:
                token_conll_d[k] = self.conversion_maps[k][v]
            except KeyError:
                continue

        return token_conll_d

    def _set_span_conll(self, span: Span, span_idx: int = 1):
        """Sets a span's properties according to the CoNLL-U format.
        :param span: a spaCy Span
        :param span_idx: optional index, corresponding to the n-th sentence
                         in the parent Doc
        """
        span_conll_str = ""
        if self.include_headers:
            # Get metadata from custom extension or create it ourselves
            if not (span.has_extension("conll_metadata") and span._.conll_metadata):
                span._.conll_metadata = f"# sent_id = {span_idx}\n# text = {span.text}\n"

            span_conll_str += span._.conll_metadata

        for token_idx, token in enumerate(span, 1):
            self._set_token_conll(token, token_idx)

        span._.set(self.ext_names["conll"], [t._.get(self.ext_names["conll"]) for t in span])
        span_conll_str += "".join([t._.get(self.ext_names["conll_str"]) for t in span])
        span._.set(self.ext_names["conll_str"], span_conll_str)

        if PD_AVAILABLE and not self.disable_pandas:
            span._.set(
                self.ext_names["conll_pd"],
                pd.DataFrame([t._.get(self.ext_names["conll"]) for t in span]),
            )

    def _set_token_conll(self, token: Token, token_idx: int = 1) -> Token:
        """Sets a token's properties according to the CoNLL-U format.
        :param token: a spaCy Token
        :param token_idx: optional index, corresponding to the n-th token in the sentence Span
        """
        if token.dep_.lower().strip() == "root":
            head_idx = 0
        else:
            head_idx = token.head.i + 1 - token.sent[0].i

        token._.conll_misc_field = "_" if token.whitespace_ else "SpaceAfter=No"

        token_conll = (
            token_idx,
            token.text,
            token.lemma_,
            token.pos_,
            token.tag_,
            str(token.morph) if token.has_morph and str(token.morph) else "_",
            head_idx,
            token.dep_,
            token._.conll_deps_graphs_field,
            token._.conll_misc_field,
        )

        # turn field name values (keys) and token values (values) into dict
        token_conll_d = OrderedDict(zip(list(self.field_names.values()), token_conll))

        # convert properties if needed
        if self.conversion_maps:
            token_conll_d = self._map_conll(token_conll_d)

        token._.set(self.ext_names["conll"], token_conll_d)
        token_conll_str = "\t".join(map(str, token_conll_d.values())) + "\n"
        token._.set(self.ext_names["conll_str"], token_conll_str)

        if PD_AVAILABLE and not self.disable_pandas:
            token._.set(self.ext_names["conll_pd"], pd.Series(token_conll_d))

        return token

    def _set_extensions(self):
        """Sets the default extensions if they do not exist yet."""
        for obj in Doc, Span, Token:
            if not obj.has_extension(self.ext_names["conll_str"]):
                obj.set_extension(self.ext_names["conll_str"], default=None)
            if not obj.has_extension(self.ext_names["conll"]):
                obj.set_extension(self.ext_names["conll"], default=None)

            if PD_AVAILABLE and not self.disable_pandas:
                if not obj.has_extension(self.ext_names["conll_pd"]):
                    obj.set_extension(self.ext_names["conll_pd"], default=None)

        # Adds fields from the CoNLL-U format that are not available in spaCy
        # However, ConllParser might set these fields when it has read CoNLL_str->spaCy
        if not Token.has_extension("conll_deps_graphs_field"):
            Token.set_extension("conll_deps_graphs_field", default="_")
        if not Token.has_extension("conll_misc_field"):
            Token.set_extension("conll_misc_field", default="_")
        if not Span.has_extension("conll_metadata"):
            Span.set_extension("conll_metadata", default=None)
