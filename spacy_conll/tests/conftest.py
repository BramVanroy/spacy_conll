import pytest

import spacy
from spacy_stanfordnlp import StanfordNLPLanguage
import stanfordnlp

from spacy_conll import ConllFormatter


@pytest.fixture(scope='session')
def spacy_en_small_with_formatter():
    nlp = spacy.load('en_core_web_sm')
    conllformatter = ConllFormatter(nlp)
    nlp.add_pipe(conllformatter, after='parser')
    return nlp

@pytest.fixture(scope='session')
def spacy_stanfordnlp_en_with_formatter():
    snlp = stanfordnlp.Pipeline(lang='en')
    nlp = StanfordNLPLanguage(snlp)
    conllformatter = ConllFormatter(nlp)
    nlp.add_pipe(conllformatter, last=True)
    return nlp

@pytest.fixture(scope='session')
def single_string_single_sentence():
    return 'A cookie is a baked or cooked food that is typically small, flat and sweet.'

@pytest.fixture(scope='session')
def single_string_multi_sentence():
    return 'A cookie is a baked or cooked food that is typically small, flat and sweet. It usually contains flour, sugar and some type of oil or fat. It may include other ingredients such as raisins, oats, chocolate chips, nuts, etc.'
