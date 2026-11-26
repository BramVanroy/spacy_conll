# spacy-conll

[![CI](https://github.com/BramVanroy/spacy_conll/actions/workflows/ci.yml/badge.svg)](https://github.com/BramVanroy/spacy_conll/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/BramVanroy/spacy_conll/branch/main/graph/badge.svg)](https://codecov.io/gh/BramVanroy/spacy_conll)
[![PyPI](https://img.shields.io/pypi/v/spacy-conll)](https://pypi.org/project/spacy-conll/)
[![Docs](https://img.shields.io/badge/docs-bramvanroy.github.io-blue)](https://bramvanroy.github.io/spacy_conll)

spacy-conll is a spaCy pipeline component that formats parsed documents as [CoNLL-U](https://universaldependencies.org/format.html). It also reads CoNLL-U into spaCy `Doc` objects and includes the command line tool `parse-as-conll`. It works with spaCy models and, as an optional backend, with [spacy-udpipe](https://github.com/TakeLab/spacy-udpipe).

The output labels are those of the model that you use. For Universal Dependencies labels, use the UDPipe backend. `spacy-stanza` is not supported anymore since it has been unmaintained for a while now.

## Installation

```shell
pip install spacy-conll
pip install "spacy-conll[udpipe]"  # adds the UDPipe backend
pip install "spacy-conll[all]"     # adds the UDPipe backend and pandas
```

spacy-conll needs Python 3.11 or newer. Install a spaCy model as well, for example `python -m spacy download en_core_web_sm`.

## Example

```python
import spacy

nlp = spacy.load("en_core_web_sm")
nlp.add_pipe("conll_formatter", last=True)

doc = nlp("I like cookies.")
print(doc._.conll_str)
```

```text
1	I	I	PRON	PRP	Case=Nom|Number=Sing|Person=1|PronType=Prs	2	nsubj	_	_
2	like	like	VERB	VBP	Tense=Pres|VerbForm=Fin	0	ROOT	_	_
3	cookies	cooky	NOUN	NNS	Number=Plur	2	dobj	_	SpaceAfter=No
4	.	.	PUNCT	.	PunctType=Peri	2	punct	_	_
```

The same from the command line:

```shell
parse-as-conll en_core_web_sm spacy --input-str "I like cookies."
```

## Documentation

The [documentation](https://bramvanroy.github.io/spacy_conll) has a usage guide, the API reference and a [migration guide](https://bramvanroy.github.io/spacy_conll/migration/) for v4 users. See `examples/` for runnable scripts and the [changelog](CHANGELOG.md) for the release history.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Credits

The first version of this library was inspired by the work of [rgalhama](https://github.com/rgalhama/spaCy2CoNLLU) and has changed a lot since then.

## License

BSD 2-Clause. See [LICENSE](LICENSE).
