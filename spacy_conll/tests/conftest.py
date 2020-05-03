import pytest

from spacy_conll import init_parser

# flow inspired by https://stackoverflow.com/a/61486898/1150683
# pass (uninvoked) function as a parameter to fixtures

PARSERS = {}

def spacy_en():
    if 'spacy' not in PARSERS:
        PARSERS['spacy'] = init_parser('spacy')
    return PARSERS['spacy']

def spacy_stanfordnlp_en():
    if 'stanfordnlp' not in PARSERS:
        PARSERS['stanfordnlp'] = init_parser('stanfordnlp')
    return PARSERS['stanfordnlp']

def spacy_stanza_en():
    if 'stanza' not in PARSERS:
        PARSERS['stanza'] = init_parser('stanza')
    return PARSERS['stanza']

def spacy_udpipe_en():
    if 'udpipe' not in PARSERS:
        PARSERS['udpipe'] = init_parser('udpipe')
    return PARSERS['udpipe']

@pytest.fixture(params=[spacy_en, spacy_stanfordnlp_en, spacy_stanza_en, spacy_udpipe_en])
def parser(request):
    yield request.param

@pytest.fixture
def spacy_ext_names():
    nlp = init_parser(ext_names={'conll': 'conllu',
                                 'conll_str': 'conll_text',
                                 'conll_pd': 'pandas'})
    return nlp

@pytest.fixture
def spacy_conversion_map():
    nlp = init_parser(conversion_maps={'lemma': {'-PRON-': 'PRON'}})
    return nlp

def single_sent():
    return "He wanted to elaborate more on the cookie."

def multi_sent():
    return "A cookie is a baked or cooked food that is typically small, flat and sweet. It usually contains flour, sugar and some type of oil or fat. It may include other ingredients such as raisins, oats, chocolate chips, nuts, etc."

@pytest.fixture(params=[single_sent, multi_sent])
def text(request):
    yield request.param

@pytest.fixture
def doc(parser, text):
    yield parser()(text())

@pytest.fixture
def spacy_ext_names_doc(spacy_ext_names):
    return spacy_ext_names(single_sent())

@pytest.fixture
def spacy_conversion_map_doc(spacy_conversion_map):
    return spacy_conversion_map(single_sent())
