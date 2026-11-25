# Migrating from v4 to v5

v5 changes the signatures of `init_parser`, `ConllParser` methods and the command line options, and removes the stanza backend. The CoNLL-U output of a given pipeline stays the same.

## Requirements

- Python 3.11 or newer (v4: 3.8 or newer).
- spaCy 3.8 or newer.
- The package is built with hatchling and managed with uv. The version comes from git tags.

## The stanza backend is removed

`spacy-stanza` pins `stanza<1.7`, and those versions cannot load models under current versions of torch. `parser="stanza"` and the `spacy-conll[stanza]` extra are gone. Use `spacy` or `udpipe` instead:

```python
# v4
nlp = init_parser("en", "stanza")

# v5
nlp = init_parser("en", "udpipe")
```

The extras are now `udpipe`, `parsers` (the same as `udpipe`), `pd` and `all`.

## init_parser

The `**kwargs` that went to the formatter are replaced by the explicit argument `formatter_config`. `parser` is a `Literal["spacy", "udpipe"]`. `parser_opts` is not modified any more.

```python
# v4
nlp = init_parser("en_core_web_sm", "spacy", include_headers=True)

# v5
nlp = init_parser(
    "en_core_web_sm", "spacy", formatter_config={"include_headers": True}
)
```

The old keyword arguments `ext_names`, `field_names`, `conversion_maps` and `disable_pandas` move into `formatter_config` in the same way.

## ConllParser

`parse_text_as_conll` and `parse_file_as_conll` take keyword-only options. `no_force_counting` and `no_split_on_newline` are replaced by positive options.

| v4 | v5 |
| --- | --- |
| `no_force_counting=True` | `renumber_sent_ids=False` |
| `no_split_on_newline=True` | `split_on_newline=False` |
| `input_encoding` defaults to the system encoding | `input_encoding` defaults to `"utf-8"` |

```python
# v4
parser.parse_text_as_conll(
    text, n_process=4, no_force_counting=True, no_split_on_newline=True
)
parser.parse_file_as_conll("in.txt", "utf-8", no_force_counting=True)

# v5
parser.parse_text_as_conll(
    text, n_process=4, renumber_sent_ids=False, split_on_newline=False
)
parser.parse_file_as_conll("in.txt", renumber_sent_ids=False)
```

The signatures are now:

```python
parse_text_as_conll(text, *, n_process=1, renumber_sent_ids=True, ignore_pipe_errors=False, split_on_newline=True)
parse_file_as_conll(input_file, *, input_encoding="utf-8", n_process=1, renumber_sent_ids=True, ignore_pipe_errors=False, split_on_newline=True)
```

`parse_conll_text_as_spacy` and `parse_conll_file_as_spacy` also take keyword-only options, and `input_encoding` of the file method defaults to `"utf-8"`. The regular expression for entity tags is available as the constant `spacy_conll.parser.NER_TAG_PATTERN`.

```python
# v4
doc = parser.parse_conll_file_as_spacy("in.conllu", "utf-8")

# v5
doc = parser.parse_conll_file_as_spacy("in.conllu", input_encoding="utf-8")
```

## Token._.conll

`Token._.conll` is a plain `dict` instead of an `OrderedDict`. Dicts keep the insertion order, so the order of the fields is the same.

## DEPREL of the root token

The root token has the DEPREL `root` for every backend, as the CoNLL-U format requires. spaCy models gave `ROOT` before.

```python
# v4
"0\tROOT"

# v5
"0\troot"
```

To keep the old label, map it with `conversion_maps={"DEPREL": {"root": "ROOT"}}`.

## Command line

All multi-word options use hyphens instead of underscores, the single-letter flags `-a`, `-b`, `-c`, `-s`, `-t`, `-d`, `-e` and `-j` are removed, and the encoding defaults are `utf-8`. One of `-f/--input-file` and `--input-str` is required.

| v4 | v5 |
| --- | --- |
| `-f`, `--input_file` | `-f`, `--input-file` |
| `-b`, `--input_str` | `--input-str` |
| `-a`, `--input_encoding` | `--input-encoding` |
| `-o`, `--output_file` | `-o`, `--output-file` |
| `-c`, `--output_encoding` | `--output-encoding` |
| `-s`, `--disable_sbd` | `--disable-sbd` |
| `-t`, `--is_tokenized` | `--is-tokenized` |
| `-d`, `--include_headers` | `--include-headers` |
| `-e`, `--no_force_counting` | `--no-renumber-sent-ids` |
| `-j`, `--n_process` | `--n-process` |
| `--ignore_pipe_errors` | `--ignore-pipe-errors` |
| `--no_split_on_newline` | `--no-split-on-newline` |
| `-v`, `--verbose` | `-v`, `--verbose` |

```shell
# v4
parse-as-conll en_core_web_sm spacy -b "I like cookies." -d -j 2

# v5
parse-as-conll en_core_web_sm spacy --input-str "I like cookies." --include-headers --n-process 2
```

## Bug fixes that change behavior

- The command line script crashed on every run in 4.0.x. It works again.
- Adding `conll_formatter` to a pipeline failed config validation with recent spaCy versions because `field_names` was `None`.
- Pretokenized input with an empty string raised an `IndexError`. It gives an empty `Doc`.
- Empty docs with pandas installed raised an error. They give an empty `DataFrame`.
- CoNLL-U text that ends with a blank line raised an error.
- `n_process=-1` skipped the multiprocessing checks.
- Output no longer starts with a newline when the first line of the input is empty.
