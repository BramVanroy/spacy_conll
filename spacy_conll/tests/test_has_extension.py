# Doc: single sentence
def test_doc_has_conll_str_single_sentence(en_small_with_formatter, single_string_single_sentence):
    doc = en_small_with_formatter(single_string_single_sentence)
    assert doc.has_extension('conll_str')
    assert doc._.conll_str is not None
    assert isinstance(doc._.conll_str, str)

def test_doc_has_conll_str_headers_single_sentence(en_small_with_formatter, single_string_single_sentence):
    doc = en_small_with_formatter(single_string_single_sentence)
    assert doc.has_extension('conll_str_headers')
    assert doc._.conll_str_headers is not None
    assert isinstance(doc._.conll_str_headers, str)

def test_doc_has_conll_single_sentence(en_small_with_formatter, single_string_single_sentence):
    doc = en_small_with_formatter(single_string_single_sentence)
    assert doc.has_extension('conll')
    assert doc._.conll is not None
    assert isinstance(doc._.conll, list)

# Doc: multi-sentence
def test_doc_has_conll_str_multi_sentence(en_small_with_formatter, single_string_multi_sentence):
    doc = en_small_with_formatter(single_string_multi_sentence)
    assert doc.has_extension('conll_str')
    assert doc._.conll_str is not None
    assert isinstance(doc._.conll_str, str)

def test_doc_has_conll_str_headers_multi_sentence(en_small_with_formatter, single_string_multi_sentence):
    doc = en_small_with_formatter(single_string_multi_sentence)
    assert doc.has_extension('conll_str_headers')
    assert doc._.conll_str_headers is not None
    assert isinstance(doc._.conll_str_headers, str)

def test_doc_has_conll_multi_sentence(en_small_with_formatter, single_string_multi_sentence):
    doc = en_small_with_formatter(single_string_multi_sentence)
    assert doc.has_extension('conll')
    assert doc._.conll is not None
    assert isinstance(doc._.conll, list)


# Sents
def test_sents_has_conll_str_single_sentence(en_small_with_formatter, single_string_single_sentence):
    doc = en_small_with_formatter(single_string_single_sentence)
    for sent in doc.sents:
        assert sent.has_extension('conll_str')
        assert sent._.conll_str is not None
        assert isinstance(sent._.conll_str, str)

def test_sents_has_conll_str_headers_single_sentence(en_small_with_formatter, single_string_single_sentence):
    doc = en_small_with_formatter(single_string_single_sentence)
    for sent in doc.sents:
        assert sent.has_extension('conll_str_headers')
        assert sent._.conll_str_headers is not None
        assert isinstance(sent._.conll_str_headers, str)

def test_sents_has_conll_single_sentence(en_small_with_formatter, single_string_single_sentence):
    doc = en_small_with_formatter(single_string_single_sentence)
    for sent in doc.sents:
        assert sent.has_extension('conll')
        assert sent._.conll is not None
        assert isinstance(sent._.conll, list)

# Sents: multi-sentence
def test_sents_has_conll_str_multi_sentence(en_small_with_formatter, single_string_multi_sentence):
    doc = en_small_with_formatter(single_string_multi_sentence)
    for sent in doc.sents:
        assert sent.has_extension('conll_str')
        assert sent._.conll_str is not None
        assert isinstance(sent._.conll_str, str)

def test_sents_has_conll_str_headers_multi_sentence(en_small_with_formatter, single_string_multi_sentence):
    doc = en_small_with_formatter(single_string_multi_sentence)
    for sent in doc.sents:
        assert sent.has_extension('conll_str_headers')
        assert sent._.conll_str_headers is not None
        assert isinstance(sent._.conll_str_headers, str)

def test_sents_has_conll_multi_sentence(en_small_with_formatter, single_string_multi_sentence):
    doc = en_small_with_formatter(single_string_multi_sentence)
    for sent in doc.sents:
        assert sent.has_extension('conll')
        assert sent._.conll is not None
        assert isinstance(sent._.conll, list)