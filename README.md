# Parsing to CoNLL with spaCy, spacy-stanza, and spacy-udpipe

**The last version to support spaCy v2 can be found** [here](<https://github.com/BramVanroy/spacy_conll/tree/v2.1.0>).
 The current version only supports v3.

This module allows you to parse text into CoNLL-U format\_. You can use it as a command line tool, or embed it in your
 own scripts by adding it as a custom pipeline component to a spaCy, `spacy-stanza`, or `spacy-udpipe` pipeline. It 
 also provides an easy-to-use function to quickly initialize a parser as well as a ConllParser class with built-in 
 functionality to parse files or text.

Note that the module simply takes a parser's output and puts it in a formatted string adhering to the linked ConLL-U 
 format. The output tags depend on the spaCy model used. If you want Universal Depencies tags as output, I advise you 
 to use this library in combination with [spacy-stanza](https://github.com/explosion/spacy-stanza), which is a spaCy 
 interface using `stanza` and its models behind the scenes. Those models use the Universal Dependencies formalism and 
 yield state-of-the-art performance. `stanza` is a new and improved version of `stanfordnlp`. As an alternative to the 
 Stanford models, you can use the spaCy wrapper for `UDPipe`, [spacy-udpipe](https://github.com/TakeLab/spacy-udpipe), 
 which is slightly less accurate than `stanza` but much faster.


## Installation

By default, this package automatically installs only [spaCy](https://spacy.io/usage/models#section-quickstart) as 
 dependency. Because [spaCy's models](https://spacy.io/usage/models) are not necessarily trained on Universal 
 Dependencies conventions, their output labels are not UD either. By using `spacy-stanza` or `spacy-udpipe`, we get 
 the easy-to-use interface of spaCy as a wrapper around `stanza` and `UDPipe` respectively, including their models that
 *are* trained on UD data.

**NOTE**: `spacy-stanza` and `spacy-udpipe` are not installed automatically as a dependency for this library, because 
 it might be too much overhead for those who don't need UD. If you wish to use their functionality (e.g. better 
 performance, real UD output), you have to install them manually or use one of the available options as described 
 below.

If you want to retrieve CoNLL info as a `pandas` DataFrame, this library will automatically export it if it detects 
 that `pandas` is installed. See the Usage section for more.

To install the library, simply use pip.

```bash
# only includes spacy by default
pip install spacy_conll
```

A number of options are available to make installation of additional dependencies easier:

```bash
# include spacy-stanza and spacy-udpipe
pip install spacy_conll[parsers]
# include pandas
pip install spacy_conll[pd]
# include pandas, spacy-stanza and spacy-udpipe
pip install spacy_conll[all]
# include pandas, spacy-stanza and spacy-udpipe and additional libaries for testing and formatting
pip install spacy_conll[dev]
```


## Usage

When the ConllFormatter is added to a spaCy pipeline, it adds CoNLL properties for `Token`, sentence `Span` and `Doc`.
 Note that arbitrary Span's are not included and do not receive these properties.

On all three of these levels, two custom properties are exposed by default, `._.conll`{:.python} and its string 
 representation `._.conll_str`{:.python}. However, if you have `pandas` installed, then `._.conll_pd`{:.python} will
 be added automatically, too!

-   `._.conll`{:.python}: raw CoNLL format  
    -   in Token: a dictionary containing all the expected CoNLL fields as keys and the parsed properties as values.
    -   in sentence Span: a list of its tokens' `._.conll`{:.python} dictionaries (list of dictionaries).
    -   in a Doc: a list of its sentences' `._.conll`{:.python} lists (list of list of dictionaries).

-   `._.conll_str`{:.python}: string representation of the CoNLL format  
    -   in Token: tab-separated representation of the contents of the CoNLL fields ending with a newline.
    -   in sentence Span: the expected CoNLL format where each row represents a token. When 
        `ConllFormatter(include_headers=True)`{:.python} is used, two header lines are included as well, as per the
        [CoNLL format](https://universaldependencies.org/format.html#sentence-boundaries-and-comments).
    -   in Doc: all its sentences' `._.conll_str`{:.python} combined and separated by new lines.

-   `._.conll_pd`{:.python}: `pandas` representation of the CoNLL format  
    -   in Token: a Series representation of this token's CoNLL properties.
    -   in sentence Span: a DataFrame representation of this sentence, with the CoNLL names as column headers.
    -   in Doc: a concatenation of its sentences' DataFrame's, leading to a new a DataFrame whose index is reset.

You can use `spacy_conll` in your own Python code as a custom pipeline component, or you can use the built-in
 command-line script which offers typically needed functionality. See the following section for more.


### In Python

This library offers the ConllFormatter class which serves as a custom spaCy pipeline component. It can be instantiated
 as follows. It is important that you import `spacy_conll` before adding the pipe!

```python
import spacy_conll
nlp = <initialise parser>
nlp.add_pipe("conll_formatter", last=True)
```

Because this library supports different spaCy wrappers (`spacy`, `stanza`, and `udpipe`), a convenience function is
 available as well. With `utils.init_parser`{:.python} you can easily instantiate a parser with a single line. You can
 find the function's signature below. Have a look at the [source code](spacy_conll/utils.py) to read more about all the
 possible arguments or try out the [examples](examples/).

**NOTE**: `is_tokenized` does not work for `spacy-udpipe` and `disable_sbd` only works for `spacy`. `spacy-udpipe` has
 made a change to allow pretokenized text, but it depends on the input format and cannot be fixed at initialisation of
 the parser. See release v0.3.0 of spacy-udpipe or [this PR](https://github.com/TakeLab/spacy-udpipe/pull/19). Using
 `is_tokenized` for `spacy-stanza` also effects sentence segmentation, effectively *only* splitting on new
 lines. With `spacy`, `is_tokenized` disables sentence splitting completely.

```python
def init_parser(
    model_or_lang: str,
    parser: str,
    *,
    is_tokenized: bool = False,
    disable_sbd: bool = False,
    parser_opts: Optional[Dict] = None,
    **kwargs,
) -> Language:
```

For instance, if you want to load a Dutch `stanza` model in silent mode with the CoNLL formatter already attached, you
 can simply use the following snippet. `parser_opts` is passed to the `stanza` pipeline initialisation automatically. 
 Any other keyword arguments (`kwargs`), on the other hand, are passed to the `ConllFormatter` initialisation.

```python
from spacy_conll import init_parser

nlp = init_parser("nl", "stanza", parser_opts={"verbose": False})
```

The `ConllFormatter` allows you to customize the extension names, and you can also specify conversion maps for the
output properties.

To illustrate, here is an advanced example, showing the more complex options:

- `ext_names`: changes the attribute names to a custom key by using a dictionary.
-  `conversion_maps`: a two-level dictionary that looks like `{field_name: {tag_name: replacement}}`{:.python}. In 
   other words, you can specify in which field a certain value should be replaced by another. This is especially useful
   when you are not satisfied with the tagset of a model and wish to change some tags to an alternative0. 

The example below

- shows how to manually add the component;
- changes the custom attribute `conll_pd` to pandas (`conll_pd` only availabe if `pandas` is installed);
- converts any `nsubj` deprel tag to `subj`.

```python
import spacy
import spacy_conll


nlp = spacy.load("en_core_web_sm")
config = {"ext_names": {"conll_pd": "pandas"},
          "conversion_maps": {"deprel": {"nsubj": "subj"}}}
nlp.add_pipe("conll_formatter", config=config, last=True)
doc = nlp("I like cookies.")
print(doc._.pandas)
```

This is the same as:

```python
from spacy_conll import init_parser

nlp = init_parser("en_core_web_sm",
                  "spacy",
                  ext_names={"conll_pd": "pandas"},
                  conversion_maps={"deprel": {"nsubj": "subj"}})
doc = nlp("I like cookies.")
print(doc._.pandas)
```


The snippets above will output a pandas DataFrame by using `._.pandas`{:.python} rather than the standard
`._.conll_pd`{:.python}, and all occurrences of `nsubj` in the deprel field are replaced by `subj`.

```
   id     form   lemma upostag xpostag                                       feats  head deprel deps           misc
0   1        I       I    PRON     PRP  Case=Nom|Number=Sing|Person=1|PronType=Prs     2   subj    _              _
1   2     like    like    VERB     VBP                     Tense=Pres|VerbForm=Fin     0   ROOT    _              _
2   3  cookies  cookie    NOUN     NNS                                 Number=Plur     2   dobj    _  SpaceAfter=No
3   4        .       .   PUNCT       .                              PunctType=Peri     2  punct    _  SpaceAfter=No
```


### Command line

Upon installation, a command-line script is added under tha alias `parse-as-conll`. You can use it to parse a
string or file into CoNLL format given a number of options.

```bash
> parse-as-conll -h
usage: parse-as-conll [-h] [-f INPUT_FILE] [-a INPUT_ENCODING] [-b INPUT_STR] [-o OUTPUT_FILE]
                  [-c OUTPUT_ENCODING] [-s] [-t] [-d] [-e] [-j N_PROCESS] [-v]
                  [--ignore_pipe_errors] [--no_split_on_newline]
                  model_or_lang {spacy,stanza,udpipe}

Parse an input string or input file to CoNLL-U format using a spaCy-wrapped parser. The output
can be written to stdout or a file, or both.

positional arguments:
  model_or_lang         Model or language to use. SpaCy models must be pre-installed, stanza
                        and udpipe models will be downloaded automatically
  {spacy,stanza,udpipe}
                        Which parser to use. Parsers other than 'spacy' need to be installed
                        separately. For 'stanza' you need 'spacy-stanza', and for 'udpipe' the
                        'spacy-udpipe' library is required.

optional arguments:
  -h, --help            show this help message and exit
  -f INPUT_FILE, --input_file INPUT_FILE
                        Path to file with sentences to parse. Has precedence over 'input_str'.
                        (default: None)
  -a INPUT_ENCODING, --input_encoding INPUT_ENCODING
                        Encoding of the input file. Default value is system default. (default:
                        cp1252)
  -b INPUT_STR, --input_str INPUT_STR
                        Input string to parse. (default: None)
  -o OUTPUT_FILE, --output_file OUTPUT_FILE
                        Path to output file. If not specified, the output will be printed on
                        standard output. (default: None)
  -c OUTPUT_ENCODING, --output_encoding OUTPUT_ENCODING
                        Encoding of the output file. Default value is system default. (default:
                        cp1252)
  -s, --disable_sbd     Whether to disable spaCy automatic sentence boundary detection. In
                        practice, disabling means that every line will be parsed as one
                        sentence, regardless of its actual content. When 'is_tokenized' is
                        enabled, 'disable_sbd' is enabled automatically (see 'is_tokenized').
                        Only works when using 'spacy' as 'parser'. (default: False)
  -t, --is_tokenized    Whether your text has already been tokenized (space-seperated). Setting
                        this option has as an important consequence that no sentence splitting
                        at all will be done except splitting on new lines. So if your input is
                        a file, and you want to use pretokenised text, make sure that each line
                        contains exactly one sentence. (default: False)
  -d, --include_headers
                        Whether to include headers before the output of every sentence. These
                        headers include the sentence text and the sentence ID as per the CoNLL
                        format. (default: False)
  -e, --no_force_counting
                        Whether to disable force counting the 'sent_id', starting from 1 and
                        increasing for each sentence. Instead, 'sent_id' will depend on how
                        spaCy returns the sentences. Must have 'include_headers' enabled.
                        (default: False)
  -j N_PROCESS, --n_process N_PROCESS
                        Number of processes to use in nlp.pipe(). -1 will use as many cores as
                        available. Might not work for a 'parser' other than 'spacy' depending
                        on your environment. (default: 1)
  -v, --verbose         Whether to always print the output to stdout, regardless of
                        'output_file'. (default: False)
  --ignore_pipe_errors  Whether to ignore a priori errors concerning 'n_process' By default we
                        try to determine whether processing works on your system and stop
                        execution if we think it doesn't. If you know what you are doing, you
                        can ignore such pre-emptive errors, though, and run the code as-is,
                        which will then throw the default Python errors when applicable.
                        (default: False)
  --no_split_on_newline
                        By default, the input file or string is split on newlines for faster
                        processing of the split up parts. If you want to disable that behavior,
                        you can use this flag. (default: False)
```


For example, parsing a single line, multi-sentence string:

```bash
>  parse-as-conll en_core_web_sm spacy --input_str "I like cookies. What about you?" --include_headers

# sent_id = 1
# text = I like cookies.
1       I       I       PRON    PRP     Case=Nom|Number=Sing|Person=1|PronType=Prs      2       nsubj   _       _
2       like    like    VERB    VBP     Tense=Pres|VerbForm=Fin 0       ROOT    _       _
3       cookies cookie  NOUN    NNS     Number=Plur     2       dobj    _       SpaceAfter=No
4       .       .       PUNCT   .       PunctType=Peri  2       punct   _       _

# sent_id = 2
# text = What about you?
1       What    what    PRON    WP      _       2       dep     _       _
2       about   about   ADP     IN      _       0       ROOT    _       _
3       you     you     PRON    PRP     Case=Acc|Person=2|PronType=Prs  2       pobj    _       SpaceAfter=No
4       ?       ?       PUNCT   .       PunctType=Peri  2       punct   _       SpaceAfter=No
```

For example, parsing a large input file and writing output to a given output file, using four processes:

```bash
> parse-as-conll en_core_web_sm spacy --input_file large-input.txt --output_file large-conll-output.txt --include_headers --disable_sbd -j 4
```


## Credits

The first version of this library was inspired by initial work by [rgalhama](https://github.com/rgalhama/spaCy2CoNLLU)
 and has evolved a lot since then.
