import pytest
import spacy
from spacy.vocab import Vocab

from spacy_conll import ConllFormatter, init_parser
from spacy_conll.utils import SpacyPretokenizedTokenizer, merge_dicts_strict


def test_merge_dicts_strict_unknown_key():
    with pytest.raises(KeyError, match="Unknown key 'c'"):
        merge_dicts_strict({"a": 1}, {"c": 2})


def test_formatter_unknown_field_name_raises():
    with pytest.raises(KeyError, match="Unknown key"):
        init_parser(
            "en_core_web_sm",
            "spacy",
            formatter_config={"field_names": {"NOPE": "x"}},
        )


def test_init_parser_invalid_parser():
    with pytest.raises(ValueError, match="Unexpected value 'nope'"):
        init_parser("en_core_web_sm", "nope")


def test_init_parser_exclude_spacy_components():
    nlp = init_parser(
        "en_core_web_sm", "spacy", exclude_spacy_components=["ner"]
    )

    assert "ner" not in nlp.pipe_names
    assert "parser" in nlp.pipe_names


def test_init_parser_disable_sbd_gives_one_sentence_per_line():
    nlp = init_parser("en_core_web_sm", "spacy", disable_sbd=True)

    doc = nlp("First sentence. Second sentence.")

    assert len(list(doc.sents)) == 1


def test_init_parser_without_sbd_still_splits_by_default():
    nlp = init_parser("en_core_web_sm", "spacy")

    assert len(list(nlp("First sentence. Second sentence.").sents)) == 2


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("", []),
        ("   \n\t ", []),
        ("a b", ["a", "b"]),
    ],
)
def test_pretokenized_tokenizer_whitespace(text, expected):
    doc = SpacyPretokenizedTokenizer(Vocab())(text)

    assert [t.text for t in doc] == expected


def test_pretokenized_tokenizer_rejects_non_string():
    with pytest.raises(ValueError, match="Expected string"):
        SpacyPretokenizedTokenizer(Vocab())(["a", "b"])


def test_formatter_is_registered_after_blank_pipeline():
    nlp = spacy.blank("en")
    nlp.add_pipe("conll_formatter")

    assert isinstance(nlp.get_pipe("conll_formatter"), ConllFormatter)
