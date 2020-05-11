import pytest
from spacy.tokens.underscore import Underscore

from spacy_conll import init_parser

# flow inspired by https://stackoverflow.com/a/61486898/1150683
# pass (uninvoked) function as a parameter to fixtures

PARSERS = {}


def get_parser(name, **kwargs):
    if f"{name}-{kwargs}" not in PARSERS:
        PARSERS[f"{name}-{kwargs}"] = init_parser(name, **kwargs)

    return PARSERS[f"{name}-{kwargs}"]


@pytest.fixture(scope="function", autouse=True)
def clean_underscore():
    # reset the Underscore object after the test, to avoid having state copied across tests
    # this irequired if we want to test things such as disable_pandas: if we don't do this
    # conll_pd will be set in one test and cannot be unset in another so `has_extension` will
    # always return true.
    # see https://github.com/explosion/spaCy/issues/5424#issuecomment-626773933
    yield
    Underscore.doc_extensions = {}
    Underscore.span_extensions = {}
    Underscore.token_extensions = {}


@pytest.fixture(params=["spacy", "stanfordnlp", "stanza", "udpipe"])
def base_parser(request):
    yield get_parser(request.param)

# Not testing with UDPipe, which does not support this
@pytest.fixture(params=["spacy", "stanfordnlp", "stanza"])
def pretokenized_parser(request):
    yield get_parser(request.param, is_tokenized=True), request.param


@pytest.fixture
def spacy_ext_names():
    nlp = init_parser(
        ext_names={"conll": "conllu", "conll_str": "conll_text", "conll_pd": "pandas"}
    )
    return nlp


@pytest.fixture
def spacy_conversion_map():
    nlp = init_parser(conversion_maps={"lemma": {"-PRON-": "PRON"}})
    return nlp


@pytest.fixture
def spacy_disabled_pandas():
    nlp = init_parser(disable_pandas=True)
    return nlp


def single_sent():
    return "He wanted to elaborate more on his grandma's cookie."


def multi_sent():
    return "A cookie is a baked or cooked food that is typically small, flat and sweet. It usually contains flour, sugar and some type of oil or fat. It may include other ingredients such as raisins, oats, chocolate chips, nuts, etc."


@pytest.fixture(params=[single_sent, multi_sent])
def text(request):
    yield request.param


@pytest.fixture
def base_doc(base_parser, text):
    yield base_parser(text())


@pytest.fixture
def pretokenized_doc(pretokenized_parser):
    name = pretokenized_parser[1]
    if name == 'spacy':
        yield pretokenized_parser[0](single_sent().split())
    else:
        yield pretokenized_parser[0](single_sent())


@pytest.fixture
def spacy_ext_names_doc(spacy_ext_names):
    return spacy_ext_names(single_sent())


@pytest.fixture
def spacy_conversion_map_doc(spacy_conversion_map):
    return spacy_conversion_map(single_sent())


@pytest.fixture
def spacy_disabled_pandas_doc(spacy_disabled_pandas):
    return spacy_disabled_pandas(single_sent())
