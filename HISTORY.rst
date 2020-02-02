#######
History
#######

**************************
1.2.0 (February 2nd, 2020)
**************************
* **BREAKING**: :code:`._.conll` now outputs a dictionary for sentences :code:`fieldname: [value1, value2...]`, and
  a list of such dictionaries for a Doc
* Added a :code:`conversion_maps` argument where one can define a mapping to have better control over the model's tagset
  (see the advanced example in README.rst)
* Tests for usage with :code:`spacy-stanfordnlp`
* Better documentation, including advanced example

**************************
1.1.0 (January 21st, 2020)
**************************
Include dependencies in :code:`setup.py` rather than expecting users to install dependencies manually.

**************************
1.0.1 (January 15th, 2020)
**************************
Minor documentation changes for PyPi.

**************************
1.0.0 (January 13th, 2020)
**************************
* Complete overhaul. Can now be used a custom pipeline component in spaCy.
* Spacy2ConllParser is now deprecated.
* The CLI interface does not rely on Spacy2ConllParser anymore but uses the custom pipeline component instead.
* Added :code:`-e|--no_force_counting` to the CLI options. By default, when using :code:`-d|--include_headers`,
  parsed sentence will be numbered incrementally. This can be disabled so that the sentence numbering depends on how
  spaCy segments the sentences.

**************************
0.1.6 (January 17th, 2019)
**************************
Minor bugfix.

**************************
0.1.5 (January 17th, 2019)
**************************
Added the :code:`-s|--disable_sbd` flag. By default, spaCy does automatic sentence boundary detection. You may not
always want this. When you want to parse every line explicitly as one sentence, you can disable this functionality.

**************************
0.1.0 (January 16th, 2019)
**************************
Added the :code:`-t|--is_tokenized` flag. It indicates that your text has already been tokenized and that it should not
be tokenized again. The tokens should be space-separated, e.g. :code:`I like grandma 's cookies !`.

**************************
0.0.3 (January 14th, 2019)
**************************
Initial commit.