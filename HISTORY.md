# History

## 3.1.0 (October 31st, 2021)

- **[conllparser]** The CoNLLParser can now parse a given CoNLL string or text file into a spaCy Doc.
  ([#14](https://github.com/BramVanroy/spacy_conll/pull/14) Parse conllu 2 spacy object, contributed by
  [shaked571](https://github.com/shaked571))


## 3.0.2 (July 14th, 2021)

- **[conllparser]** Fix: fixed an issue with no_split_on_newline in combination with `nlp.pipe`


## 3.0.1 (July 14th, 2021)

- **[conllparser]** Fix: make sure the parser also runs if stanza and UDPipe are not installed


## 3.0.0 (July 12th, 2021)

- **[general]** Breaking change: spaCy v3 required (closes [#8](https://github.com/BramVanroy/spacy_conll/issues/8))
- **[init_parser]** Breaking change: in all cases, `is_tokenized` now disables sentence segmentation
- **[init_parser]** Breaking change: no more default values for parser or model anywhere. Important to note here that
  spaCy does not work with short-hand codes such as `en` any more. You have to provide the full model name, e.g.
  ``en_core_web_sm``
- **[init_parser]** Improvement: models are automatically downloaded for Stanza and UDPipe
- **[cli]** Reworked the position of the CLI script in the directory structure as well as the arguments. Run
  `parse-as-conll -h` for more information.
- **[conllparser]** Made the [`ConllParser`](spacy_conll/parser.py) class available as a utility to easily create a 
  wrapper for a spaCy-like
  parser which can return the parsed CoNLL output of a given file or text
- **[conllparser,cli]** Improvements to usability of `n_process`. Will try to figure out whether multiprocessing
  is available for your platform and if not, tell you so. Such a priori error messages can be disabled, with
  `ignore_pipe_errors`, both on the command line as in ConllParser's parse methods
  


## 2.1.0 (June 23rd, 2021)

Preparing for v3 release

- Last version to support spaCy v2. New versions will require spaCy v3
- Last version to support ``spacy-stanfordnlp``. ``spacy-stanza`` is still supported


## 2.0.0 (May 11th, 2020)

**Fully reworked version!**

- Tested support for both `spacy-stanza` and `spacy-udpipe`! (Not included as a dependency, install manually)
- Added a useful utility function `init_parser` that can easily initialise a parser together with the custom
  pipeline component. (See the README or [`examples`](examples/).)
- Added the `disable_pandas` flag the formatter class in case you would want to disable setting the pandas
  attribute even when pandas is installed.
- Added custom properties for Tokens as well. So now a Doc, its sentence Spans as well as Tokens have custom attributes
- Reworked datatypes of output. In version 2.0.0 the data types are as follows:
    - `._.conll`: raw CoNLL format
        - in `Token`: a dictionary containing all the expected CoNLL fields as keys and the parsed properties as
          values.
        - in sentence `Span`: a list of its tokens' `._.conll` dictionaries (list of dictionaries).
        - in a `Doc`: a list of its sentences' `._.conll` lists (list of list of dictionaries).
    - `._.conll_str`: string representation of the CoNLL format
        - in `Token`: tab-separated representation of the contents of the CoNLL fields ending with a newline.
        - in sentence `Span`: the expected CoNLL format where each row represents a token. When
          `ConllFormatter(include_headers=True)` is used, two header lines are included as well, as per the
          [`CoNLL format`](https://universaldependencies.org/format.html#sentence-boundaries-and-comments).
        - in `Doc`: all its sentences' `._.conll_str` combined and separated by new lines.
    - `._.conll_pd`: ``pandas`` representation of the CoNLL format
        - in `Token`: a `Series` representation of this token's CoNLL properties.
        - in sentence `Span`: a `DataFrame` representation of this sentence, with the CoNLL names as column
          headers.
        - in `Doc`: a concatenation of its sentences' `DataFrame`'s, leading to a new a `DataFrame` whose
          index is reset.
- `field_names` has been removed, assuming that you do not need to change the column names of the CoNLL properties
- Removed the `Spacy2ConllParser` class
- Many doc changes, added tests, and a few examples


## 1.3.0 (April 28th, 2020)

- **IMPORTANT**: This will be the last release that supports the deprecated `Spacy2ConllParser` class!
- Community addition (@KoichiYasuoka): add `SpaceAfter=No` to the Misc field when applicable.
- Fixed failing tests


## 1.2.0 (February 2nd, 2020)

- **BREAKING**: `._.conll` now outputs a dictionary for sentences `fieldname: [value1, value2...]`, and
  a list of such dictionaries for a `Doc`
- Added a `conversion_maps` argument where one can define a mapping to have better control over the model's tagset
  (see the advanced example in README.md)
- Tests for usage with `spacy-stanfordnlp`
- Better documentation, including advanced example


## 1.1.0 (January 21st, 2020)

Include dependencies in `setup.py` rather than expecting users to install dependencies manually.


## 1.0.1 (January 15th, 2020)

Minor documentation changes for PyPi.


## 1.0.0 (January 13th, 2020)

- Complete overhaul. Can now be used a custom pipeline component in spaCy.
- `Spacy2ConllParser` is now deprecated.
- The CLI interface does not rely on `Spacy2ConllParser` anymore but uses the custom pipeline component instead.
- Added `-e|--no_force_counting` to the CLI options. By default, when using `-d|--include_headers`,
  parsed sentence will be numbered incrementally. This can be disabled so that the sentence numbering depends on how
  spaCy segments the sentences.


## 0.1.6 (January 17th, 2019)

Minor bugfix.


## 0.1.5 (January 17th, 2019)

Added the `-s|--disable_sbd` flag. By default, spaCy does automatic sentence boundary detection. You may not
always want this. When you want to parse every line explicitly as one sentence, you can disable this functionality.


## 0.1.0 (January 16th, 2019)

Added the `-t|--is_tokenized` flag. It indicates that your text has already been tokenized and that it should not
be tokenized again. The tokens should be space-separated, e.g. `I like grandma 's cookies !`.


## 0.0.3 (January 14th, 2019)

Initial commit.