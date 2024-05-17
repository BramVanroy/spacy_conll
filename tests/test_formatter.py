from collections import OrderedDict

from spacy_conll.formatter import ConllFormatter
from spacy.tokens import Token


def test_set_token_conll(spacy_token: Token):
    """Test for https://github.com/BramVanroy/spacy_conll/issues/29"""
    formatter = ConllFormatter()
    assert formatter._set_token_conll(spacy_token)._.get("conll") == OrderedDict(
        [
             ('ID', 1),
             ('FORM', 'world'),
             ('LEMMA', '_'),
             ('UPOS', '_'),
             ('XPOS', '_'),
             ('FEATS', '_'),
             ('HEAD', 2),
             ('DEPREL', '_'),
             ('DEPS', '_'),
             ('MISC', 'SpaceAfter=No'),
        ]
    )
    assert formatter._set_token_conll(spacy_token)._.get("conll_str") == "1\tworld\t_\t_\t_\t_\t2\t_\t_\tSpaceAfter=No\n"
