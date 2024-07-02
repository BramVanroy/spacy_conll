from pathlib import Path

import pytest


def test_conllparser(conllparser_conllstr):
    # five sentences, each with one # for sent id and one # for text
    # (only four lines but last line consists of two sentences)
    assert conllparser_conllstr.count("#") == 10


def test_pretokenized_conllparser(pretokenized_conllparser_conllstr):
    # pretokenized disables sentence segmentation, so only four sentences
    # instead of the real five, each with one # for sent id and one # for text
    assert pretokenized_conllparser_conllstr.count("#") == 8
    # Because it is pretokenised, we need exactly 30 tokens all the time
    assert pretokenized_conllparser_conllstr.count("\n") == 30


def test_conllparser_n_process(conllparser):
    # error due to pandas
    with pytest.raises(OSError) as e_info:
        conllparser.parse_file_as_conll(
            Path(__file__).parent.joinpath("test.txt"), input_encoding="utf-8", n_process=2
        )
