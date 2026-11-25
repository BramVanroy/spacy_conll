import sys

import pytest

from spacy_conll.cli.parse import main, run

TEXT = "He wanted to elaborate more on his grandma's cookie."


def test_run_input_str_to_stdout(capsys):
    run(model_or_lang="en_core_web_sm", parser="spacy", input_str=TEXT)

    out = capsys.readouterr().out
    assert out.startswith("1\tHe\the\t")
    assert not out.startswith("#")


def test_run_input_file_to_stdout(tmp_path, capsys):
    input_file = tmp_path / "in.txt"
    input_file.write_text(TEXT, encoding="utf-8")

    run(
        model_or_lang="en_core_web_sm",
        parser="spacy",
        input_file=input_file,
        include_headers=True,
    )

    out = capsys.readouterr().out
    assert out.startswith("# sent_id = 1\n# text = He wanted")


@pytest.mark.parametrize("verbose", [False, True])
def test_run_output_file(tmp_path, capsys, verbose):
    output_file = tmp_path / "out.conllu"

    run(
        model_or_lang="en_core_web_sm",
        parser="spacy",
        input_str=TEXT,
        output_file=output_file,
        verbose=verbose,
    )

    written = output_file.read_text(encoding="utf-8")
    assert written.startswith("1\tHe\the\t")
    assert capsys.readouterr().out == (written if verbose else "")


@pytest.mark.parametrize(
    ("renumber_sent_ids", "expected"),
    [(True, ["1", "2"]), (False, ["1", "1"])],
)
def test_run_renumber_sent_ids(capsys, renumber_sent_ids, expected):
    run(
        model_or_lang="en_core_web_sm",
        parser="spacy",
        input_str="First one.\nSecond one.",
        include_headers=True,
        renumber_sent_ids=renumber_sent_ids,
    )

    sent_ids = [
        line.split(" = ")[1]
        for line in capsys.readouterr().out.splitlines()
        if line.startswith("# sent_id")
    ]
    assert sent_ids == expected


def test_run_requires_input():
    with pytest.raises(ValueError, match="'input_str' or 'input_file'"):
        run(model_or_lang="en_core_web_sm", parser="spacy")


def test_main(monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "parse-as-conll",
            "en_core_web_sm",
            "spacy",
            "--input-str",
            TEXT,
            "--include-headers",
        ],
    )

    main()

    assert capsys.readouterr().out.startswith("# sent_id = 1\n# text = He")


def test_main_input_file_and_input_str_are_exclusive(monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "parse-as-conll",
            "en_core_web_sm",
            "spacy",
            "-f",
            "x",
            "--input-str",
            "y",
        ],
    )

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 2
    assert "not allowed with argument" in capsys.readouterr().err
