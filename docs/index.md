# spacy-conll

spacy-conll converts the output of a spaCy pipeline to [CoNLL-U](https://universaldependencies.org/format.html) and reads CoNLL-U back into spaCy `Doc` objects. It is a spaCy pipeline component (`conll_formatter`), a `ConllParser` class for text and files, and a command line tool (`parse-as-conll`).

The library formats what a parser predicts. The tags in the output come from the model that you use. The English spaCy models do not use Universal Dependencies labels. If you need UD labels, use the UDPipe backend (`spacy-udpipe`), which loads models that are trained on UD data.

## Installation

```shell
pip install spacy-conll
```

This installs spaCy as the only dependency. Extras add optional features:

```shell
pip install "spacy-conll[udpipe]"  # UDPipe backend through spacy-udpipe
pip install "spacy-conll[pd]"      # pandas DataFrames in `._.conll_pd`
pip install "spacy-conll[all]"     # udpipe and pandas
```

`spacy-conll[parsers]` is an alias of `spacy-conll[udpipe]`. spacy-conll needs Python 3.11 or newer and spaCy 3.8 or newer.

spaCy models are not part of the install. Download the model that you want to use, for example:

```shell
python -m spacy download en_core_web_sm
```

## Quickstart

Add `conll_formatter` as the last component of a pipeline and read the CoNLL-U output from the `Doc`:

```python
import spacy

nlp = spacy.load("en_core_web_sm")
nlp.add_pipe("conll_formatter", last=True)

doc = nlp("I like cookies. What about you?")
print(doc._.conll_str)
```

```text
1	I	I	PRON	PRP	Case=Nom|Number=Sing|Person=1|PronType=Prs	2	nsubj	_	_
2	like	like	VERB	VBP	Tense=Pres|VerbForm=Fin	0	root	_	_
3	cookies	cooky	NOUN	NNS	Number=Plur	2	dobj	_	SpaceAfter=No
4	.	.	PUNCT	.	PunctType=Peri	2	punct	_	_

1	What	what	PRON	WP	_	2	dep	_	_
2	about	about	ADP	IN	_	0	root	_	_
3	you	you	PRON	PRP	Case=Acc|Person=2|PronType=Prs	2	pobj	_	SpaceAfter=No
4	?	?	PUNCT	.	PunctType=Peri	2	punct	_	SpaceAfter=No
```

`init_parser` builds a pipeline with the formatter in one call, and the command line tool parses text without any Python code:

```shell
parse-as-conll en_core_web_sm spacy --input-str "I like cookies." --include-headers
```

The [usage guide](usage.md) describes all options. Coming from v4? Read the [migration guide](migration.md).

## Acknowledgements

The first version of this library was inspired by the work of [rgalhama](https://github.com/rgalhama/spaCy2CoNLLU) and has changed a lot since then.
