# Usage

## The pipeline component

`conll_formatter` is a spaCy factory. spaCy finds it through an entry point, so `import spacy_conll` is not needed before `nlp.add_pipe("conll_formatter")`. Add it after all components that set tags, lemmas, morphology and dependencies:

```python
import spacy

nlp = spacy.load("en_core_web_sm")
nlp.add_pipe("conll_formatter", last=True)
doc = nlp("I like cookies.")
```

`init_parser` loads a model and adds the formatter in one call. Options for the formatter go in `formatter_config`:

```python
from spacy_conll import init_parser

nlp = init_parser(
    "en_core_web_sm", "spacy", formatter_config={"include_headers": True}
)
```

The options of `init_parser` are:

- `model_or_lang`: the spaCy model name or, for UDPipe, a language code such as `"en"`. Models are downloaded automatically for UDPipe only.
- `parser`: `"spacy"` or `"udpipe"`.
- `is_tokenized`: the input is a string of tokens that are separated by whitespace. Sentences are then split on newlines only (spaCy) and UDPipe does not support this.
- `disable_sbd`: disable sentence boundary detection, so that every input text is one sentence. Only for spaCy.
- `exclude_spacy_components`: names of spaCy components to leave out of the pipeline.
- `parser_opts`: extra keyword arguments for the loader of the backend (`spacy.load`). The dict is not modified.
- `formatter_config`: the config of `conll_formatter`, see below.

### Formatter options

- `include_headers`: start every sentence with `# sent_id = ...` and `# text = ...` comment lines. Default `False`.
- `ext_names`: new names for the extensions `conll`, `conll_str` and `conll_pd`.
- `field_names`: new names for the CoNLL-U fields `ID`, `FORM`, `LEMMA`, `UPOS`, `XPOS`, `FEATS`, `HEAD`, `DEPREL`, `DEPS` and `MISC`. These are the dict keys of `._.conll` and the column names of `._.conll_pd`.
- `conversion_maps`: a dict of the form `{field_name: {old_value: new_value}}` that replaces output values. The field name is the name after `field_names` was applied.
- `disable_pandas`: do not set `conll_pd`, even if pandas is installed.
- `columns`: a list of CoNLL-U Plus column names that selects and orders the output columns. Default `None` (plain CoNLL-U). See [CoNLL-U Plus](#conll-u-plus).

Unknown keys in `ext_names` and `field_names` raise a `KeyError`.

This example renames `conll_pd` to `pandas` and replaces the dependency label `nsubj` with `subj`:

```python
from spacy_conll import init_parser

nlp = init_parser(
    "en_core_web_sm",
    "spacy",
    formatter_config={
        "ext_names": {"conll_pd": "pandas"},
        "conversion_maps": {"DEPREL": {"nsubj": "subj"}},
    },
)
doc = nlp("I like cookies.")
print(doc._.pandas)
```

```text
   ID     FORM  LEMMA   UPOS  ...  HEAD DEPREL DEPS           MISC
0   1        I      I   PRON  ...     2   subj    _              _
1   2     like   like   VERB  ...     0   root    _              _
2   3  cookies  cooky   NOUN  ...     2   dobj    _  SpaceAfter=No
3   4        .      .  PUNCT  ...     2  punct    _  SpaceAfter=No
```

The same config works with `nlp.add_pipe("conll_formatter", config={...}, last=True)`. Renaming fields changes the keys of the output:

```python
from spacy_conll import init_parser

nlp = init_parser(
    "en_core_web_sm",
    "spacy",
    formatter_config={"field_names": {"UPOS": "upostag", "XPOS": "xpostag"}},
)
doc = nlp("I like cookies.")
print(doc._.conll_pd.columns.tolist())
```

```text
['ID', 'FORM', 'LEMMA', 'upostag', 'xpostag', 'FEATS', 'HEAD', 'DEPREL', 'DEPS', 'MISC']
```

## Extensions

The formatter sets three extensions on every `Token`, on every sentence `Span` and on the `Doc`. Other spans do not get them.

- `._.conll`: the raw data.
    - `Token`: a dict with the CoNLL-U fields as keys.
    - Sentence `Span`: a list of the dicts of its tokens.
    - `Doc`: a list of the lists of its sentences.
- `._.conll_str`: the CoNLL-U text.
    - `Token`: one tab-separated line that ends with a newline.
    - Sentence `Span`: one line per token. With `include_headers=True` the `# sent_id` and `# text` lines come first.
    - `Doc`: the strings of all sentences, separated by an empty line.
- `._.conll_pd`: a pandas object, only available if pandas is installed and `disable_pandas` is false.
    - `Token`: a `Series`.
    - Sentence `Span`: a `DataFrame` with the field names as columns.
    - `Doc`: the `DataFrame` of all sentences with a new index. A `Doc` without tokens gives an empty `DataFrame` with the field columns.

```python
import spacy

nlp = spacy.load("en_core_web_sm")
nlp.add_pipe("conll_formatter", last=True)
doc = nlp("I like cookies.")
print(doc[0]._.conll)
print(repr(doc[0]._.conll_str))
```

```text
{'ID': 1, 'FORM': 'I', 'LEMMA': 'I', 'UPOS': 'PRON', 'XPOS': 'PRP', 'FEATS': 'Case=Nom|Number=Sing|Person=1|PronType=Prs', 'HEAD': 2, 'DEPREL': 'nsubj', 'DEPS': '_', 'MISC': '_'}
'1\tI\tI\tPRON\tPRP\tCase=Nom|Number=Sing|Person=1|PronType=Prs\t2\tnsubj\t_\t_\n'
```

Empty values are written as `_`. `HEAD` is the position of the head within its sentence, `0` for the root, and `_` for a token without a head (for example in a pipeline without a parser). `MISC` is `SpaceAfter=No` for tokens that are not followed by whitespace. Other whitespace is described below.

### Newlines, tabs and other whitespace

spaCy keeps newlines, tabs and repeated spaces as separate tokens with the tag `_SP`. The formatter leaves these whitespace tokens out of the output, because a CoNLL-U field cannot contain a tab or a newline. It follows the [UD convention](https://universaldependencies.org/misc.html) and records the whitespace in `MISC` of the token before it:

- a single space: no entry (`_`)
- no whitespace: `SpaceAfter=No`
- any other whitespace: `SpacesAfter` with the escapes `\s` (space), `\t` (tab), `\n` (newline) and `\r` (carriage return)
- whitespace at the start of the doc: `SpacesBefore` on the first token

The IDs and heads are renumbered without the whitespace tokens. A token whose head is a whitespace token gets the nearest ancestor that is not whitespace as its head, or becomes a root if there is none. The `# text` line has its whitespace collapsed to single spaces. A sentence that only contains whitespace has no output and does not count for `# sent_id`.

```python
import spacy

nlp = spacy.load("en_core_web_sm")
nlp.add_pipe("conll_formatter", last=True, config={"include_headers": True})
doc = nlp("Results are clear.\n2.\t")
print(doc._.conll_str)
```

```text
# sent_id = 1
# text = Results are clear.
1	Results	result	NOUN	NNS	Number=Plur	2	nsubj	_	_
2	are	be	AUX	VBP	Mood=Ind|Tense=Pres|VerbForm=Fin	0	root	_	_
3	clear	clear	ADJ	JJ	Degree=Pos	2	acomp	_	SpaceAfter=No
4	.	.	PUNCT	.	PunctType=Peri	2	punct	_	SpacesAfter=\n

# sent_id = 2
# text = 2.
1	2	2	X	LS	NumType=Ord	0	root	_	SpaceAfter=No
2	.	.	PUNCT	.	PunctType=Peri	1	punct	_	SpacesAfter=\t
```

The whitespace tokens themselves have `None` as `._.conll`, `._.conll_str` and `._.conll_pd`. The sentence and doc extensions only contain the other tokens, so `doc[4]._.conll` is `None` here (the token `"\n"`), and `len(doc._.conll_pd)` is 6 for the 8 tokens of the doc.

## Parsing text and files

`ConllParser` wraps a pipeline that contains `conll_formatter`, for example the output of `init_parser`. It raises a `ValueError` if the component is missing.

```python
from spacy_conll import ConllParser, init_parser

nlp = init_parser(
    "en_core_web_sm", "spacy", formatter_config={"include_headers": True}
)
parser = ConllParser(nlp)
conll = parser.parse_text_as_conll("I like cookies. What about you?")
print(conll)
```

```text
# sent_id = 1
# text = I like cookies.
1	I	I	PRON	PRP	Case=Nom|Number=Sing|Person=1|PronType=Prs	2	nsubj	_	_
2	like	like	VERB	VBP	Tense=Pres|VerbForm=Fin	0	root	_	_
3	cookies	cooky	NOUN	NNS	Number=Plur	2	dobj	_	SpaceAfter=No
4	.	.	PUNCT	.	PunctType=Peri	2	punct	_	_

# sent_id = 2
# text = What about you?
1	What	what	PRON	WP	_	2	dep	_	_
2	about	about	ADP	IN	_	0	root	_	_
3	you	you	PRON	PRP	Case=Acc|Person=2|PronType=Prs	2	pobj	_	SpaceAfter=No
4	?	?	PUNCT	.	PunctType=Peri	2	punct	_	SpaceAfter=No
```

`parse_file_as_conll(input_file)` does the same for a text file (`input_encoding` defaults to `"utf-8"`). Both methods take these keyword-only options:

- `n_process`: number of processes for `nlp.pipe`. `-1` uses all cores. Default `1`.
- `renumber_sent_ids`: number `# sent_id` over the whole input. Every line of the input is a separate `Doc` and spaCy would restart the numbering at 1 for each. Default `True`. This only matters with `include_headers=True`.
- `ignore_pipe_errors`: skip the checks that raise an `OSError` when `n_process` is not 1 and the setup is likely to fail. Default `False`.
- `split_on_newline`: process every line of the input as its own `Doc`, which is faster for long input. Without it, the whole input is one text. Default `True`.
- `sent_ids`: your own IDs for the `# sent_id` lines, one per output sentence. Default `None`. See below.

### Your own sentence IDs

If your sentences already have IDs, pass them as `sent_ids`. They replace the generated numbers, so `renumber_sent_ids` has no effect. This requires `include_headers=True`. An ID cannot be empty or contain whitespace. The number of IDs must equal the number of sentences in the output, otherwise you get a `ValueError`. With `disable_sbd=True` every line of the input is one sentence (empty lines are skipped), so you give one ID per non-empty line:

```python
from spacy_conll import ConllParser, init_parser

nlp = init_parser(
    "en_core_web_sm",
    "spacy",
    disable_sbd=True,
    formatter_config={"include_headers": True},
)
parser = ConllParser(nlp)
conll = parser.parse_text_as_conll(
    "I like cookies.\nWhat about you?", sent_ids=["chat-008", "chat-009"]
)
print(conll)
```

```text
# sent_id = chat-008
# text = I like cookies.
1	I	I	PRON	PRP	Case=Nom|Number=Sing|Person=1|PronType=Prs	2	nsubj	_	_
...

# sent_id = chat-009
# text = What about you?
...
```

`parse_file_as_conll` takes the same option. When you read the output back with `parse_conll_text_as_spacy`, the IDs stay in `Span._.conll_metadata` of every sentence.

### Pretokenized input

With `is_tokenized=True` spaCy splits the text on whitespace only and every line is one sentence:

```python
from spacy_conll import init_parser

nlp = init_parser("en_core_web_sm", "spacy", is_tokenized=True)
doc = nlp("This is , a pretokenized sentence .")
print(doc._.conll_str)
```

An empty string gives an empty `Doc` and no output.

## Reading CoNLL-U into spaCy

`parse_conll_text_as_spacy(text)` and `parse_conll_file_as_spacy(input_file)` build a `Doc` from CoNLL-U. Sentences are separated by an empty line and `#` comment lines are allowed. The formatter has already run on the returned `Doc`, so all extensions are available.

```python
from spacy_conll import ConllParser, init_parser

nlp = init_parser(
    "en_core_web_sm", "spacy", formatter_config={"include_headers": True}
)
parser = ConllParser(nlp)

conll = """# sent_id = a1
# text = From the AP comes this story
1\tFrom\tfrom\tADP\tIN\t_\t3\tcase\t3:case\t_
2\tthe\tthe\tDET\tDT\tDefinite=Def|PronType=Art\t3\tdet\t3:det\t_
3\tAP\tAP\tPROPN\tNNP\tNumber=Sing\t4\tobl\t4:obl:from\t_
4\tcomes\tcome\tVERB\tVBZ\tMood=Ind|Number=Sing|Person=3|Tense=Pres|VerbForm=Fin\t0\troot\t0:root\t_
5\tthis\tthis\tDET\tDT\tNumber=Sing|PronType=Dem\t6\tdet\t6:det\t_
6\tstory\tstory\tNOUN\tNN\tNumber=Sing\t4\tnsubj\t4:nsubj\tSpaceAfter=No
"""
doc = parser.parse_conll_text_as_spacy(conll)
for token in doc:
    print(token.text, token.dep_, token.pos_, token.head.text)
```

```text
From case ADP AP
the det DET AP
AP obl PROPN comes
comes ROOT VERB comes
this det DET story
story nsubj NOUN comes
```

Both methods have two more keyword-only options for named entities that are stored in the MISC field. `ner_tag_pattern` is the regular expression that matches the BILUO tag (the default is the constant `spacy_conll.parser.NER_TAG_PATTERN`) and `ner_map` renames labels. A label that maps to `""` becomes `O`.

Multi-word tokens and empty nodes (IDs such as `1-2` or `2.1`) raise a `NotImplementedError`. A `ValueError` names the line of the problem. It is raised for a line without 10 tab-separated fields, an empty field, a space in a field other than FORM, LEMMA and MISC, an ID or HEAD that is not a valid number, a HEAD or DEPREL that is `_`, and a sentence whose HEAD values do not form one tree. A trailing blank line and Windows line endings are allowed.

A `_` in LEMMA, UPOS, XPOS or FEATS is a missing value: the spaCy attribute stays empty (`token.pos_ == ""`), and the formatter writes `_` again.

### Sentences without dependencies

Use `strict=False` for CoNLL-U that is tagged but not (completely) parsed. HEAD and DEPREL may then be `_`, as long as both are `_` on the same line. Such a token has no head in spaCy (`token.has_head()` is false and `token.dep_` is `""`), and the formatter writes `_` for both fields. Every sentence block still becomes one spaCy sentence, and a round trip gives the same CoNLL-U.

```python
conll = """1\tana\tana\tADP\tPRP\t_\t_\t_\t_\t_
2\tŠumaya\tŠumaya\tPROPN\tPN\t_\t_\t_\t_\t_
3\tummā\tummu\tNOUN\tN\t_\t_\t_\t_\t_
"""
doc = parser.parse_conll_text_as_spacy(conll, strict=False)
print(
    [(token.text, token.pos_, token.dep_, token.has_head()) for token in doc]
)
```

```text
[('ana', 'ADP', '', False), ('Šumaya', 'PROPN', '', False), ('ummā', 'NOUN', '', False)]
```

A pipeline can then add the missing annotation to the returned `Doc`. Pass the `Doc` to `nlp` and enable only the components that you need, so that the tags from the file are kept. The parser keeps the sentence boundaries of the file. This example runs the parser of `en_core_web_sm` (which needs `tok2vec`) on tagged text:

```python
import spacy
from spacy_conll import ConllParser

nlp = spacy.load("en_core_web_sm")
nlp.add_pipe("conll_formatter", last=True)
parser = ConllParser(nlp)

conll = """1\tI\tI\tPRON\tPRP\t_\t_\t_\t_\t_
2\tlike\tlike\tVERB\tVBP\t_\t_\t_\t_\t_
3\tcookies\tcookie\tNOUN\tNNS\t_\t_\t_\t_\tSpaceAfter=No
4\t.\t.\tPUNCT\t.\t_\t_\t_\t_\t_
"""
doc = parser.parse_conll_text_as_spacy(conll, strict=False)
with nlp.select_pipes(enable=["tok2vec", "parser", "conll_formatter"]):
    doc = nlp(doc)
print(doc._.conll_str)
```

```text
1	I	I	PRON	PRP	_	2	nsubj	_	_
2	like	like	VERB	VBP	_	0	root	_	_
3	cookies	cookie	NOUN	NNS	_	2	dobj	_	SpaceAfter=No
4	.	.	PUNCT	.	_	2	punct	_	_
```

### Fields that spaCy does not store

`DEPS`, `MISC` and the comment lines have no spaCy equivalent. They are kept in custom extensions, which are registered by the formatter and by `ConllParser`:

- `Token._.conll_deps_graphs_field`: the `DEPS` value of the token. Default `"_"`.
- `Token._.conll_misc_field`: the `MISC` value of the token. Default `"_"`.
- `Token._.conll_custom_columns`: a dict with the values of custom CoNLL-U Plus columns, see [CoNLL-U Plus](#conll-u-plus). Default `None`.
- `Span._.conll_metadata`: the comment lines of a sentence, with a trailing newline. Default `None`.

```python
sent = next(doc.sents)
print(repr(sent._.conll_metadata))
print(doc[2]._.conll_deps_graphs_field, doc[5]._.conll_misc_field)
```

```text
'# sent_id = a1\n# text = From the AP comes this story\n'
4:obl:from SpaceAfter=No
```

A round trip from CoNLL-U to spaCy and back keeps these values. When the formatter writes `MISC`, it only sets or removes the entries `SpaceAfter`, `SpacesAfter` and `SpacesBefore` and keeps all other entries in their order. An existing `SpacesAfter` stays when spaCy has a space after the token, because spaCy cannot store other whitespace between tokens of a doc that is read from CoNLL-U. With `include_headers=True`, the formatter writes an existing `conll_metadata` as the header of a sentence instead of generating `# sent_id` and `# text`.

## CoNLL-U Plus

[CoNLL-U Plus](https://universaldependencies.org/ext-format.html) files have a `# global.columns` line that lists the columns of the file. The columns can be any subset of the ten CoNLL-U fields in any order, plus custom columns.

### Writing

Set `columns` in the formatter config. The names are the canonical CoNLL-U names (`ID`, `FORM`, `LEMMA`, `UPOS`, `XPOS`, `FEATS`, `HEAD`, `DEPREL`, `DEPS`, `MISC`) or custom names with a namespace, such as `PARSEME:MWE`. Custom names consist of uppercase letters and colons. A list that is empty, has duplicates or has another kind of name raises a `ValueError`.

```python
from spacy_conll import ConllParser, init_parser

nlp = init_parser(
    "en_core_web_sm",
    "spacy",
    formatter_config={"columns": ["ID", "FORM", "UPOS", "HEAD", "DEPREL"]},
)
doc = nlp("I like cookies.")
print(doc._.conll_str)
print(doc[1]._.conll)
print(doc._.conll_pd.columns.tolist())
```

```text
# global.columns = ID FORM UPOS HEAD DEPREL
1	I	PRON	2	nsubj
2	like	VERB	0	root
3	cookies	NOUN	2	dobj
4	.	PUNCT	2	punct

{'ID': 2, 'FORM': 'like', 'UPOS': 'VERB', 'HEAD': 0, 'DEPREL': 'root'}
['ID', 'FORM', 'UPOS', 'HEAD', 'DEPREL']
```

The `conll`, `conll_str` and `conll_pd` extensions of tokens, sentences and docs only have the selected columns. The `conll_str` of a `Doc` and the output of `ConllParser.parse_text_as_conll` start with the `# global.columns` line. It is written whenever `columns` is set, also if the list has all ten columns.

A custom column takes its value from the dict `Token._.conll_custom_columns` and is `_` for tokens without that key:

```python
doc[1]._.conll_custom_columns = {"PARSEME:MWE": "1:VID"}
```

`field_names` and `columns` are independent. `field_names` renames the dict keys and the pandas columns only. `columns` and the `# global.columns` line always use the canonical names. With `field_names={"UPOS": "upostag"}` and `columns=["FORM", "UPOS"]`, the keys of `._.conll` are `FORM` and `upostag` and the header is `# global.columns = FORM UPOS`.

### Reading

`parse_conll_text_as_spacy` and `parse_conll_file_as_spacy` read a `# global.columns` first line. Every line must have as many tab-separated fields as there are columns, otherwise a `ValueError` is raised.

- A standard column that is missing is read as `_`. A missing `ID` is the position of the token in its sentence.
- Custom columns are stored in `Token._.conll_custom_columns`.
- The `# global.columns` line is not part of `Span._.conll_metadata`.
- Without `HEAD` and `DEPREL` columns, the tokens have no dependency annotation. This needs `strict=False`, as for `_` in these fields.

```python
from spacy_conll import ConllParser, init_parser

nlp = init_parser(
    "en_core_web_sm",
    "spacy",
    formatter_config={"columns": ["FORM", "HEAD", "DEPREL", "PARSEME:MWE"]},
)
parser = ConllParser(nlp)
text = """# global.columns = FORM HEAD DEPREL PARSEME:MWE
I\t2\tnsubj\t*
take\t0\troot\t1:VID
a\t4\tdet\t1
look\t2\tobj\t1
"""
doc = parser.parse_conll_text_as_spacy(text)
print([(t.i, t.text, t.dep_, t.head.i) for t in doc])
print(doc[1]._.conll_custom_columns)
print(doc._.conll_str)
```

```text
[(0, 'I', 'nsubj', 1), (1, 'take', 'ROOT', 1), (2, 'a', 'det', 3), (3, 'look', 'obj', 1)]
{'PARSEME:MWE': '1:VID'}
# global.columns = FORM HEAD DEPREL PARSEME:MWE
I	2	nsubj	*
take	0	root	1:VID
a	4	det	1
look	2	obj	1
```

The reader does not configure the formatter. To write a Plus file back, as in the example, give the formatter the same `columns`. A formatter without `columns` writes all ten standard columns and drops the custom ones.

## Pandas and multiprocessing

If pandas is installed, `conll_pd` is set automatically. pandas objects cannot be passed between processes, so `n_process` other than 1 requires `disable_pandas=True`. Otherwise `parse_text_as_conll` raises an `OSError` (unless `ignore_pipe_errors=True`):

```python
from spacy_conll import ConllParser, init_parser

nlp = init_parser(
    "en_core_web_sm", "spacy", formatter_config={"disable_pandas": True}
)
parser = ConllParser(nlp)
conll = parser.parse_text_as_conll(
    "I like cookies.\nWhat about you?", n_process=2
)
```

`n_process=-1` uses all cores and goes through the same check. On Windows, UDPipe pipelines also fail the check, because the models cannot be pickled.

Put the code that starts processes under `if __name__ == "__main__":`, as for any use of `multiprocessing` on Windows and macOS.

## UDPipe backend

Install the extra with `pip install "spacy-conll[udpipe]"`. The model for a language is downloaded on first use:

```python
from spacy_conll import ConllParser, init_parser

nlp = init_parser("en", "udpipe", formatter_config={"include_headers": True})
print(ConllParser(nlp))
print(nlp("I like cookies.")._.conll_str)
```

```text
ConllParser(parser=udpipe)
# sent_id = 1
# text = I like cookies.
1	I	I	PRON	PRP	Case=Nom|Number=Sing|Person=1|PronType=Prs	2	nsubj	_	_
2	like	like	VERB	VBP	Mood=Ind|Tense=Pres|VerbForm=Fin	0	root	_	_
3	cookies	cookie	NOUN	NNS	Number=Plur	2	obj	_	SpaceAfter=No
4	.	.	PUNCT	.	PunctType=Peri	2	punct	_	SpaceAfter=No
```

`is_tokenized` and `disable_sbd` are not supported for UDPipe. The stanza backend was removed in v5, see the [migration guide](migration.md).

## Command line

The installation adds the script `parse-as-conll`. It takes a model or language and a backend, plus either `-f/--input-file` or `--input-str`:

```shell
parse-as-conll en_core_web_sm spacy --input-str "I like cookies. What about you?" --include-headers
```

```text
# sent_id = 1
# text = I like cookies.
1	I	I	PRON	PRP	Case=Nom|Number=Sing|Person=1|PronType=Prs	2	nsubj	_	_
2	like	like	VERB	VBP	Tense=Pres|VerbForm=Fin	0	root	_	_
3	cookies	cooky	NOUN	NNS	Number=Plur	2	dobj	_	SpaceAfter=No
4	.	.	PUNCT	.	PunctType=Peri	2	punct	_	_

# sent_id = 2
# text = What about you?
...
```

Parse a file with four processes and write the result to another file:

```shell
parse-as-conll en_core_web_sm spacy -f large-input.txt -o large-output.conll --include-headers --n-process 4
```

The script runs the formatter with `disable_pandas=True`, so `--n-process` works without further setup. Options:

- `-f, --input-file` and `--input-str`: the input. One of them is required.
- `--input-encoding`: encoding of the input file. Default `utf-8`.
- `-o, --output-file`: write to a file. Without it, the output goes to stdout.
- `--output-encoding`: encoding of the output file. Default `utf-8`.
- `--disable-sbd`: every line is one sentence. Not for UDPipe.
- `--is-tokenized`: tokens are separated by whitespace and every line is one sentence. Not for UDPipe.
- `--include-headers`: write `# sent_id` and `# text` lines.
- `--renumber-sent-ids` and `--no-renumber-sent-ids`: see `renumber_sent_ids`. On by default.
- `--n-process`: number of processes. `-1` uses all cores.
- `--ignore-pipe-errors`: skip the multiprocessing checks.
- `--split-on-newline` and `--no-split-on-newline`: see `split_on_newline`. On by default.
- `--columns NAME [NAME ...]`: write CoNLL-U Plus with only these columns, in this order, and a `# global.columns` line. Invalid names end the program with an error message.
- `--sent-ids-file`: a UTF-8 text file with one sentence ID per line (blank lines are ignored). The IDs replace the numbers in the `# sent_id` lines and the file needs one ID per output sentence. This implies `--include-headers`.
- `-v, --verbose`: also print to stdout when `--output-file` is set.

Select columns and use your own sentence IDs (`ids.txt` has the lines `doc1-008` and `doc1-009`):

```shell
parse-as-conll en_core_web_sm spacy --input-str "First one.
Second one." --disable-sbd --columns ID FORM UPOS --sent-ids-file ids.txt
```

```text
# global.columns = ID FORM UPOS
# sent_id = doc1-008
# text = First one.
1	First	ADJ
2	one	NUM
3	.	PUNCT

# sent_id = doc1-009
# text = Second one.
...
```

Run `parse-as-conll -h` for the full help text.
