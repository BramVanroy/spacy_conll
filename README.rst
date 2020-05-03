================================================
Parsing to CoNLL with spaCy or spacy-stanfordnlp
================================================
This module allows you to parse text into `CoNLL-U format`_. You can use it as a command line tool, or embed it in your
own scripts by adding it as a custom component to a spaCy, ``spacy-stanfordnlp``, ``spacy-stanza``, or ``spacy-udpipe``
pipeline.

Note that the module simply takes a parser's output and puts it in a formatted string adhering to the linked ConLL-U
format. The output tags depend on the spaCy model used. If you want Universal Depencies tags as output, I advise you to
use this library in combination with `spacy-stanza`_, which is a spaCy interface using ``stanza`` and its
models behind the scenes. Those models use the Universal Dependencies formalism and yield state-of-the-art performance.
``stanza`` is a new and improved version of ``stanfordnlp``. The spaCy wrapper for ``stanfordnlp``,
``spacy-stanfordnlp`` is also supported in this library but its development has been superseded by the ``stanza``
wrapper. Its use is not recommended. As an alternative to the Stanford models, you can use the spaCy
wrapper for ``UDPipe``, `spacy-udpipe`_, which is slightly less accurate than ``stanza`` but much faster.


.. _`CoNLL-U format`: https://universaldependencies.org/format.html
.. _`spacy-stanza`: https://github.com/explosion/spacy-stanza
.. _`spacy-udpipe`: https://github.com/TakeLab/spacy-udpipe

Installation
============
By default, this package automatically installs only `spaCy`_  and the ``packaging`` package as dependencies.

Because `spaCy's models`_ are not necessarily trained on Universal Dependencies conventions, their output labels are
not UD either. By using ``spacy-stanza`` or ``spacy-udpipe``, we get the easy-to-use interface of spaCy as a wrapper
around ``stanza`` and ``UDPipe`` respectively, including their models that *are* trained on UD data.

**NOTE**: ``spacy-stanfordnlp``, ``spacy-stanza`` and ``spacy-udpipe`` are not installed automatically as a dependency
for this library, because it might be too much overhead for those who don't need UD. If you wish to use their
functionality (e.g. better performance, real UD output), you have to install them manually.

If you want to retrieve CoNLL info as a ``pandas`` DataFrame, this library will automatically export it if it detects that
``pandas`` is installed. See the Usage section for more.

To install the library, simply use pip.

.. code:: bash

  pip install spacy_conll

.. _spaCy: https://spacy.io/usage/models#section-quickstart
.. _spaCy's models: https://spacy.io/usage/models


Usage
=====
When the :code:`ConllFormatter` is added to a spaCy pipeline, it adds CoNLL properties for :code:`Token`, sentence
:code:`Span` and :code:`Doc`. Note that arbitrary :code:`Span`'s are not included and do not receive these properties.

On all three of these levels, two custom properties are exposed by default, :code:`._.conll` and its string
representation :code:`._.conll_str`. However, if you have ``pandas`` installed, then :code:`._.conll_pd` will be added
automatically, too!

- :code:`._.conll`: raw CoNLL format
    - in :code:`Token`: a dictionary containing all the expected CoNLL fields as keys and the parsed properties as
      values.
    - in sentence :code:`Span`: a list of its tokens' :code:`._.conll` dictionaries (list of dictionaries).
    - in a :code:`Doc`: a list of its sentences' :code:`._.conll` lists (list of list of dictionaries).
- :code:`._.conll_str`: string representation of the CoNLL format
    - in :code:`Token`: tab-separated representation of the contents of the CoNLL fields ending with a newline.
    - in sentence :code:`Span`: the expected CoNLL format where each row represents a token. When
      :code:`ConllFormatter(include_headers=True)` is used, two header lines are included as well, as per the
      `CoNLL format`_.
    - in :code:`Doc`: all its sentences' :code:`._.conll_str` combined and separated by new lines.
- :code:`._.conll_pd`: ``pandas`` representation of the CoNLL format
    - in :code:`Token`: a :code:`Series` representation of this token's CoNLL properties.
    - in sentence :code:`Span`: a :code:`DataFrame` representation of this sentence, with the CoNLL names as column
      headers.
    - in :code:`Doc`: a concatenation of its sentences' :code:`DataFrame`'s, leading to a new a :code:`DataFrame` whose
      index is reset.


.. _`CoNLL format`: https://universaldependencies.org/format.html#sentence-boundaries-and-comments

You can use ``spacy_conll`` in your own Python code as a custom pipeline component, or you can use the built-in
command-line script which offers typically needed functionality. See the following section for more.

In Python
---------
This library offers the :code:`ConllFormatter` class which serves as a custom spaCy pipeline component. It can be
instantiated as follows.

.. code:: python

    nlp = <initialise parser>
    conllformatter = ConllFormatter(nlp)
    nlp.add_pipe(conllformatter, last=True)

Because this library supports different spaCy wrappers (``spacy``, ``stanfordnlp``, ``stanza``, and ``udpipe``), a
convenience function is available as well. With :code:`utils.init_parser` you can easily instantiate a parser with a
single line. You can find the function's signature below. Have a look at the `source code`_ to read more about all the
possible arguments or try out the `examples`_.

**NOTE**: :code:`is_tokenized` does not work for ``spacy-udpipe`` and :code:`disable_sbd` only works for ``spacy``.

.. code:: python

    def init_parser(parser: str = 'spacy',
                    model_or_lang: str = 'en',
                    *,
                    is_tokenized: bool = False,
                    disable_sbd: bool = False,
                    pipeline_opts: Optional[Dict] = None,
                    **kwargs) -> Language:

For instance, if you want to load a Dutch ``stanza`` model in silent mode with the CoNLL formatter already attached,
you can simply use the following snippet. :code:`pipeline_opts` is passed to the ``stanza`` pipeline initialisation
automatically. :code:`kwargs`, on the other hand, is passed to the :code:`ConllFormatter` initialisation.

.. code:: python

    from spacy_conll import init_parser

    nlp = init_parser('stanza', 'nl', pipeline_opts={'verbose': False})


The :code:`ConllFormatter` allows you to customize the extension names and you can also specify conversion maps for
the output properties.

To illustrate, here is an advanced example, showing the more complex options:

* :code:`ext_names`: changes the attribute names to a custom key by using a dictionary.
* :code:`conversion_maps`: a two-level dictionary that looks like :code:`{field_name: {tag_name: replacement}}`.
  In other words, you can specify in which field a certain value should be replaced by another. This is especially
  useful when you are not satisfied with the tagset of a model and wish to change some tags to an alternative

The example below

* shows how to manually add the component;
* changes the custom attribute :code:`conll_pd` to :code:`pandas` (:code:`conll_pd` only availabe if ``pandas`` is
  installed);
* converts any :code:`-PRON-` lemma to :code:`PRON`.

.. code:: python

    import spacy
    from spacy_conll import ConllFormatter


    nlp = spacy.load('en')
    conllformatter = ConllFormatter(nlp,
                                    ext_names={'conll_pd': 'pandas'},
                                    conversion_maps={'lemma': {'-PRON-': 'PRON'}})
    nlp.add_pipe(conllformatter, after='parser')
    doc = nlp('I like cookies.')
    print(doc._.pandas)

This is the same as:

.. code:: python

    from spacy_conll import init_parser


    nlp = init_parser(ext_names={'conll_pd': 'pandas'},
                      conversion_maps={'lemma': {'-PRON-': 'PRON'}})
    doc = nlp('I like cookies.')
    print(doc._.pandas)

The snippets above will output a pandas DataFrame by using :code:`._.pandas` rather than the standard :code:`conll_pd`,
and all occurrences of "-PRON-" in the lemma field are replaced by "PRON".

.. code:: text

       id     form word_lemma upostag  ... head deprel  deps misc
    0   1        I       PRON    PRON  ...    2  nsubj     _    _
    1   2     like       like    VERB  ...    0   ROOT     _    _
    2   3  cookies     cookie    NOUN  ...    2   dobj     _    _
    3   4        .          .   PUNCT  ...    2  punct     _    _

    [4 rows x 10 columns]


.. _`examples`: examples/
.. _`source code`: spacy_conll/utils.py

Command line
------------

Upon installation, a command-line script is added under tha alias :code:`parse-as-conll`. You can use it to parse a
string or file into CoNLL format given a number of options.

.. code:: bash

    > parse-as-conll  -h
    usage: parse-as-conll [-h] [-f INPUT_FILE] [-a INPUT_ENCODING] [-b INPUT_STR]
                          [-o OUTPUT_FILE] [-c OUTPUT_ENCODING] [-m MODEL_OR_LANG]
                          [-s] [-t] [-d] [-e] [-j N_PROCESS]
                          [-p {spacy,stanfordnlp,stanza,udpipe}] [-v]

    Parse an input string or input file to CoNLL-U format using a spaCy-wrapped
    parser.

    optional arguments:
      -h, --help            show this help message and exit
      -f INPUT_FILE, --input_file INPUT_FILE
                            Path to file with sentences to parse. Has precedence
                            over 'input_str'. (default: None)
      -a INPUT_ENCODING, --input_encoding INPUT_ENCODING
                            Encoding of the input file. Default value is system
                            default. (default: cp1252)
      -b INPUT_STR, --input_str INPUT_STR
                            Input string to parse. (default: None)
      -o OUTPUT_FILE, --output_file OUTPUT_FILE
                            Path to output file. If not specified, the output will
                            be printed on standard output. (default: None)
      -c OUTPUT_ENCODING, --output_encoding OUTPUT_ENCODING
                            Encoding of the output file. Default value is system
                            default. (default: cp1252)
      -m MODEL_OR_LANG, --model_or_lang MODEL_OR_LANG
                            spaCy or stanfordnlp model or language to use (must be
                            installed). (default: None)
      -s, --disable_sbd     Disables spaCy automatic sentence boundary detection.
                            In practice, disabling means that every line will be
                            parsed as one sentence, regardless of its actual
                            content. Only works when using 'spacy' as 'parser'.
                            (default: False)
      -t, --is_tokenized    Indicates whether your text has already been tokenized
                            (space-seperated). When used in conjunction with
                            spacy-stanfordnlp, it will also be assumed that the
                            text is sentence split by newline. Does not work for
                            'udpipe' as 'parser'. (default: False)
      -d, --include_headers
                            To include headers before the output of every
                            sentence. These headers include the sentence text and
                            the sentence ID as per the CoNLL format. (default:
                            False)
      -e, --no_force_counting
                            To disable force counting the 'sent_id', starting from
                            1 and increasing for each sentence. Instead, 'sent_id'
                            will depend on how spaCy returns the sentences. Must
                            have 'include_headers' enabled. (default: False)
      -j N_PROCESS, --n_process N_PROCESS
                            Number of processes to use in nlp.pipe(). -1 will use
                            as many cores as available. Requires spaCy v2.2.2.
                            Might not work for a 'parser' other than 'spacy'.
                            (default: 1)
      -p {spacy,stanfordnlp,stanza,udpipe}, --parser {spacy,stanfordnlp,stanza,udpipe}
                            Which parser to use. Parsers other than 'spacy' need
                            to be installed separately. So if you wish to use
                            'stanfordnlp' models, 'spacy-stanfordnlp' needs to be
                            installed. For 'stanza' you need 'spacy-stanza', and
                            for 'udpipe' the 'spacy-udpipe' library is required.
                            (default: spacy)
      -v, --verbose         To always print the output to stdout, regardless of
                            'output_file'. (default: False)


For example, parsing a single line, multi-sentence string:

.. code:: bash

    >  parse-as-conll --input_str "I like cookies . What about you ?" --is_tokenized --include_headers
    # sent_id = 1
    # text = I like cookies .
    1       I       -PRON-  PRON    PRP     PronType=prs    2       nsubj   _       _
    2       like    like    VERB    VBP     VerbForm=fin|Tense=pres 0       ROOT    _       _
    3       cookies cookie  NOUN    NNS     Number=plur     2       dobj    _       _
    4       .       .       PUNCT   .       PunctType=peri  2       punct   _       _

    # sent_id = 2
    # text = What about you ?
    1       What    what    PRON    WP      _       2       dep     _       _
    2       about   about   ADP     IN      _       0       ROOT    _       _
    3       you     -PRON-  PRON    PRP     PronType=prs    2       pobj    _       _
    4       ?       ?       PUNCT   .       PunctType=peri  2       punct   _       _

For example, parsing a large input file and writing output to a given output file, using four processes (multiprocessing
might be only supported in ``spacy``):

.. code:: bash

    > parse-as-conll --input_file large-input.txt --output_file large-conll-output.txt --include_headers --disable_sbd -j 4


=======
Credits
=======
Based on the `initial work by rgalhama`_.

.. _initial work by rgalhama: https://github.com/rgalhama/spaCy2CoNLLU
