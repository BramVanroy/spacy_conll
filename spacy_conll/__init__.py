from spacy.tokens import Doc, Span

# NOTE: DEPRECATED: import here for backward-compatibility
from spacy_conll.SpacyConllParser import Spacy2ConllParser


class ConllFormatter:
    """ Pipeline component for spaCy that adds CoNLL-U properties to a Doc and
        its sentences. A string representation, representation including a
        header, and the CoNLL-U format in tuples, are added as custom attributes."""
    name = 'conll_formatter'

    def __init__(self,
                 nlp,
                 *,
                 conll_str_attr='conll_str',
                 conll_str_headers_attr='conll_str_headers',
                 conll_attr='conll'
                 ):
        """ ConllFormatter constructor. The names of the extensions that are set
            can be changed with '*_attr' arguments.

        :param nlp: an initialized spaCy nlp object
        :param conll_str_attr: an optional string to use as the extension name for conll_str
        :param conll_str_headers_attr: an optional string to use as the extension name for conll_str_headers
        :param conll_attr: an optional string to use as the extension name for conll
        """
        # To get the morphological info, we need a tag map
        self._tagmap = nlp.Defaults.tag_map

        # Set custom attribute names
        self._attrs = {
            'conll_str': conll_str_attr,
            'conll_str_headers': conll_str_headers_attr,
            'conll': conll_attr
        }
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

            sent._.set(self._attrs['conll_str'], conll_str)
            sent._.set(self._attrs['conll_str_headers'], conll_str_w_headers)
            sent._.set(self._attrs['conll'], conll)

        doc._.set(self._attrs['conll_str'], '\n'.join(conll_strs))
        doc._.set(self._attrs['conll_str_headers'], '\n'.join(conll_strs_w_headers))
        doc._.set(self._attrs['conll'], conlls)

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
        conll = []
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
            conll.append(token_conll)
            conll_str += '\t'.join(map(str, token_conll)) + '\n'

        conll_str_w_headers += conll_str

        return conll_str, conll_str_w_headers, conll

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

    def _set_extensions(self):
        """ Sets the default extensions if they do not exist yet. """
        for obj in Span, Doc:
            if not obj.has_extension(self._attrs['conll_str']):
                obj.set_extension(self._attrs['conll_str'], default=None)
            if not obj.has_extension(self._attrs['conll_str_headers']):
                obj.set_extension(self._attrs['conll_str_headers'], default=None)
            if not obj.has_extension(self._attrs['conll']):
                obj.set_extension(self._attrs['conll'], default=None)


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
