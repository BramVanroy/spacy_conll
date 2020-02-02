__version__ = '1.2.0'

from collections import OrderedDict, defaultdict

from spacy.tokens import Doc, Span

# NOTE: SpacyConllParser is deprecated
# import here for backward-compatibility
from spacy_conll.SpacyConllParser import Spacy2ConllParser


class ConllFormatter:
    """ Pipeline component for spaCy that adds CoNLL-U properties to a Doc and
        its sentences. A string representation, representation including a
        header, and the CoNLL-U format in tuples, are added as custom attributes."""
    name = 'conll_formatter'

    def __init__(self,
                 nlp,
                 *,
                 ext_names=None,
                 field_names=None,
                 conversion_maps=None
                 ):
        """ ConllFormatter constructor. The names of the extensions that are set
            can be changed with '*_attr' arguments.

        :param nlp: an initialized spaCy nlp object
        :param ext_names: dictionary containing names for the custom spaCy extensions
        :param field_names: dictionary containing names for the CoNLL fields
        :param conversion_maps: two-level dictionary that contains a field_name (e.g. 'lemma', 'upostag')
               on the first level, and the conversion map on the second.
               E.g. {'lemma': {'-PRON-': 'PRON'}} will map the lemma '-PRON-' to 'PRON'
        """
        # To get the morphological info, we need a tag map
        self._tagmap = nlp.Defaults.tag_map

        # Set custom attribute names
        self._ext_names = {
            'conll_str': 'conll_str',
            'conll_str_headers': 'conll_str_headers',
            'conll': 'conll'
        }
        if ext_names:
            self._ext_names = self._merge_dicts_strict(self._ext_names, ext_names)

        self._field_names = OrderedDict({
            'id': 'id',
            'form': 'form',
            'lemma': 'lemma',
            'upostag': 'upostag',
            'xpostag': 'xpostag',
            'feats': 'feats',
            'head': 'head',
            'deprel': 'deprel',
            'deps': 'deps',
            'misc': 'misc'
        })

        if field_names:
            self._field_names = self._merge_dicts_strict(self._field_names, field_names)

        self._conversion_maps = conversion_maps

        # Initialize extensions
        self._set_extensions()

    def __call__(self, doc):
        """ Runs the pipeline component, adding the extensions to ._..
            Adds a string representation, string representation containing a header,
            and a tuple representation of the CoNLL format to the given Doc and its
            sentences.

        :param doc: the input Doc
        :return: the modified Doc containing the newly added extensions
        """
        # We need to hook the extensions again when using
        # multiprocessing in Windows
        # see: https://github.com/explosion/spaCy/issues/4903
        self._set_extensions()

        conll_strs = []
        conll_strs_w_headers = []
        conlls = []
        for sent_idx, sent in enumerate(doc.sents, 1):
            conll_str, conll_str_w_headers, conll = self._get_span_conll(sent, sent_idx)
            conll_strs.append(conll_str)
            conll_strs_w_headers.append(conll_str_w_headers)
            conlls.append(conll)

            sent._.set(self._ext_names['conll_str'], conll_str)
            sent._.set(self._ext_names['conll_str_headers'], conll_str_w_headers)
            sent._.set(self._ext_names['conll'], conll)

        doc._.set(self._ext_names['conll_str'], '\n'.join(conll_strs))
        doc._.set(self._ext_names['conll_str_headers'], '\n'.join(conll_strs_w_headers))
        doc._.set(self._ext_names['conll'], conlls)

        return doc

    def _get_span_conll(self, span, span_idx=1):
        """ Converts a span's properties into CoNLL-U format.

        :param span: a spaCy Span
        :param span_idx: optional index, corresponding to the n-th sentence
                         in the parent Doc
        :return: a string representation, string representation containing a header,
                 and a list of tuples representation of the CoNLL format of 'span'
        """
        conll_str_w_headers = f"# sent_id = {span_idx}\n# text = {span.text}\n"

        conll_str = ''
        conll = defaultdict(list)
        for word_idx, word in enumerate(span, 1):
            if word.dep_.lower().strip() == 'root':
                head_idx = 0
            else:
                head_idx = word.head.i + 1 - span[0].i

            token_conll = (
                word_idx,
                word.text,
                word.lemma_,
                word.pos_,
                word.tag_,
                self._get_morphology(word.tag_),
                head_idx,
                word.dep_,
                '_',
                '_'
            )

            token_conll_d = dict(zip(self._field_names.values(), token_conll))

            if self._conversion_maps:
                token_conll_d = self._map_conll(token_conll_d)
                token_conll = token_conll_d.values()

            for column_name, v in token_conll_d.items():
                conll[column_name].append(v)

            conll_str += '\t'.join(map(str, token_conll)) + '\n'

        conll_str_w_headers += conll_str

        return conll_str, conll_str_w_headers, dict(conll)

    def _get_morphology(self, tag):
        """ Expands a tag into its morphological features by using a tagmap.

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

    def _map_conll(self, token_conll_d):
        """ Maps labels according to a given `self._conversion_maps`.
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
        for obj in Span, Doc:
            if not obj.has_extension(self._ext_names['conll_str']):
                obj.set_extension(self._ext_names['conll_str'], default=None)
            if not obj.has_extension(self._ext_names['conll_str_headers']):
                obj.set_extension(self._ext_names['conll_str_headers'], default=None)
            if not obj.has_extension(self._ext_names['conll']):
                obj.set_extension(self._ext_names['conll'], default=None)


    @staticmethod
    def _is_number(s):
        """ Checks whether a string is actually a number.
        :param s: string to test
        :return: whether or not 's' is a number
        """
        try:
            float(s)
            return True
        except ValueError:
            return False

    @staticmethod
    def _merge_dicts_strict(d1, d2):
        """ Merge two dicts in a strict manner, i.e. the second dict overwrites keys
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
