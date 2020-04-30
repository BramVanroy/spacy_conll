from typing import Optional, Dict, Union

from spacy.language import Language
from spacy.tokens import Doc, Span, Token

COMPONENT_NAME = 'conll_formatter'
CONLL_FIELD_NAMES = ['id', 'form', 'lemma', 'upostag', 'xpostag', 'feats', 'head', 'deprel', 'deps', 'misc']

try:
    import pandas as pd
    PD_AVAILABLE = True
except ImportError:
    PD_AVAILABLE = False


class ConllFormatter:
    """Pipeline component for spaCy that adds CoNLL-U properties to a Doc and
       its sentences. A string representation, representation including a
       header, and the CoNLL-U format in tuples, are added as custom attributes."""
    name = COMPONENT_NAME

    def __init__(self,
                 nlp: Language,
                 *,
                 ext_names: Optional[Dict[str, str]] = None,
                 conversion_maps: Optional[Dict[str, str]] = None,
                 include_headers: bool = False
                 ):
        """ ConllFormatter constructor. The names of the extensions that are set
            can be changed with '*_attr' arguments.

        :param nlp: an initialized spaCy nlp object
        :param ext_names: dictionary containing names for the custom spaCy extensions. You can rename the following
               extensions: conll, conll_pd, conll_str.
               E.g. {'conll': 'conll_dict', 'conll_pd': 'conll_pandas'} will rename the properties accordingly
        :param conversion_maps: two-level dictionary that contains a field_name (e.g. 'lemma', 'upostag')
               on the first level, and the conversion map on the second.
               E.g. {'lemma': {'-PRON-': 'PRON'}} will map the lemma '-PRON-' to 'PRON'
        :param include_headers: whether to include the CoNLL headers in the conll_str string output. These consist
               of two lines containing the sentence id and the text as per the CoNLL format
               https://universaldependencies.org/format.html#sentence-boundaries-and-comments
        """
        # To get the morphological info, we need a tag map
        self._tagmap = nlp.Defaults.tag_map

        # Set custom attribute names
        self._ext_names = {
            'conll_str': 'conll_str',
            'conll': 'conll',
            'conll_pd': 'conll_pd'
        }
        if ext_names:
            self._ext_names = self._merge_dicts_strict(self._ext_names, ext_names)

        self._conversion_maps = conversion_maps

        self.include_headers = include_headers

        # Initialize extensions
        self._set_extensions()

    def __call__(self, doc: Doc):
        """Runs the pipeline component, adding the extensions to ._..
           Adds a string representation, string representation containing a header,
           and a tuple representation of the CoNLL format to the given Doc and its
           sentences.

        :param doc: the input Doc
        :return: the modified Doc containing the newly added extensions
        """
        # We need to hook the extensions again when using
        # multiprocessing in Windows
        # see: https://github.com/explosion/spaCy/issues/4903
        # fixed in: https://github.com/explosion/spaCy/pull/5006
        # Leaving this here for now, for older versions of spaCy
        self._set_extensions()

        for sent_idx, sent in enumerate(doc.sents, 1):
            self._set_span_conll(sent, sent_idx)

        doc._.set(self._ext_names['conll'], [s._.conll for s in doc.sents])
        doc._.set(self._ext_names['conll_str'], "\n".join([s._.conll_str for s in doc.sents]))

        if PD_AVAILABLE:
            doc._.set(self._ext_names['conll_pd'], pd.concat([s._.conll_pd for s in doc.sents]).reset_index(drop=True))

        return doc

    def _get_morphology(self, tag: str):
        """Expands a tag into its morphological features by using a tagmap.

        :param tag: the tag to expand
        :return: a string entailing the tag's morphological features
        """
        if not self._tagmap or tag not in self._tagmap:
            return '_'
        else:
            feats = [f"{prop}={val}" for prop, val in self._tagmap[tag].items() if not self._is_number(prop)]
            if feats:
                return '|'.join(feats)
            else:
                return '_'

    def _map_conll(self, token_conll_d: Dict[str, Union[str, int]]):
        """Maps labels according to a given `self._conversion_maps`.
            This can be useful when users want to change the output labels of a
            model to their own tagset.

        :param token_conll_d: a token's conll representation as dict (field_name: value)
        :return: the modified dict where the labels have been replaced according to the converison maps
        """
        for k, v in token_conll_d.items():
            try:
                token_conll_d[k] = self._conversion_maps[k][v]
            except KeyError:
                continue

        return token_conll_d

    def _set_extensions(self):
        """ Sets the default extensions if they do not exist yet. """
        for obj in Doc, Span, Token:
            if not obj.has_extension(self._ext_names['conll_str']):
                obj.set_extension(self._ext_names['conll_str'], default=None)
            if not obj.has_extension(self._ext_names['conll']):
                obj.set_extension(self._ext_names['conll'], default=None)

            if PD_AVAILABLE:
                if not obj.has_extension(self._ext_names['conll_pd']):
                    obj.set_extension(self._ext_names['conll_pd'], default=None)

    def _set_span_conll(self, span: Span, span_idx: int = 1):
        """Sets a span's properties according to the CoNLL-U format.

        :param span: a spaCy Span
        :param span_idx: optional index, corresponding to the n-th sentence
                         in the parent Doc
        """
        span_conll_str = ''
        if self.include_headers:
            span_conll_str += f"# sent_id = {span_idx}\n# text = {span.text}\n"

        for token_idx, token in enumerate(span, 1):
            self._set_token_conll(token, token_idx)

        span._.set(self._ext_names['conll'], [t._.conll for t in span])
        span_conll_str += "".join([t._.conll_str for t in span])
        span._.set(self._ext_names['conll_str'], span_conll_str)

        if PD_AVAILABLE:
            span._.set(self._ext_names['conll_pd'], pd.DataFrame([t._.conll for t in span]))

    def _set_token_conll(self, token: Token, token_idx: int = 1):
        """Sets a token's properties according to the CoNLL-U format.

        :param token: a spaCy Token
        :param token_idx: optional index, corresponding to the n-th token
                          in the sentence Span
        """
        if token.dep_.lower().strip() == 'root':
            head_idx = 0
        else:
            head_idx = token.head.i + 1 - token.sent[0].i

        token_conll = (
            token_idx,
            token.text,
            token.lemma_,
            token.pos_,
            token.tag_,
            self._get_morphology(token.tag_),
            head_idx,
            token.dep_,
            '_',
            '_' if token.whitespace_ else 'SpaceAfter=No'
        )

        # turn field name values (keys) and token values (values) into dict
        token_conll_d = dict(zip(CONLL_FIELD_NAMES, token_conll))

        # convert proeprties if needed
        if self._conversion_maps:
            token_conll_d = self._map_conll(token_conll_d)

        token._.set(self._ext_names['conll'], token_conll_d)
        token_conll_str = "\t".join(map(str, token_conll)) + "\n"
        token._.set(self._ext_names['conll_str'], token_conll_str)

        if PD_AVAILABLE:
            token._.set(self._ext_names['conll_pd'], pd.Series(token_conll_d))

        return token

    @staticmethod
    def _is_number(s: str):
        """Checks whether a string is actually a number.
        :param s: string to test
        :return: whether or not 's' is a number
        """
        try:
            float(s)
            return True
        except ValueError:
            return False

    @staticmethod
    def _merge_dicts_strict(d1: Dict, d2: Dict):
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
