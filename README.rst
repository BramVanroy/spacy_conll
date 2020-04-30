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
.. _installed spaCy language model: https://spacy.io/usage/models
.. _`a corresponding model`: https://stanfordnlp.github.io/stanfordnlp/models.html


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


Command line
------------

Upon installation, a command-line script is added under tha alias :code:`parse_as_conll`. You can use it to parse a
string or file into CoNLL format given a number of options.

.. code:: bash

    > parse_as_conll  -h
    usage: parse_as_conll [-h] [-f INPUT_FILE] [-a INPUT_ENCODING] [-b INPUT_STR]
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

    >  parse_as_conll --input_str "I like cookies . What about you ?" --is_tokenized --include_headers
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

For example, parsing a large input file and writing output to a given output file, using four processes:

.. code:: bash

    > parse_as_conll --input_file large-input.txt --output_file large-conll-output.txt --include_headers --disable_sbd -j 4

You can also use Stanford NLP's models to retrieve UD tags. You can do this by using the :code:`-u` flag. **NOTE**:
Using Stanford's models has limited options due to the API of :code:`stanfordnlp`. It is not possible to disable
sentence segmentation and control the tokenisation at the same time. When using the :code:`-u` flag you can only enable
the :code:`--is_tokenized` flag which behaves different when used with spaCy. With spaCy, it will simply not try to
tokenize the text and use spaces as token separators. When using :code:`spacy-stanfordnlp`, it will also be assumed that
the text is sentence split by newline. No further sentence segmentation is done.

In Python
---------
spaCy
+++++

:code:`spacy_conll` is intended to be used a custom pipeline component in spaCy. Three custom extensions are accessible,
by default named :code:`conll_str`, :code:`conll_str_headers`, and :code:`conll`.

- :code:`conll_str`: returns the string representation of the CoNLL format
- :code:`conll_str_headers`: returns the string representation of the CoNLL format including headers. These headers
  consist of two lines, namely :code:`# sent_id = <i>`, indicating which sentence it is in the overall document, and
  :code:`# text = <sentence>`, which simply shows the original sentence's text
- :code:`conll`: returns the output as (a list of) tuple(s) where each line is a tuple of its column values

When adding the component to the spaCy pipeline, it is important to insert it *after* the parser, as shown in the
example below.

.. code:: python

    import spacy
    from spacy_conll import ConllFormatter

    nlp = spacy.load('en')
    conllformatter = ConllFormatter(nlp)
    nlp.add_pipe(conllformatter, after='parser')
    doc = nlp('I like cookies. Do you?')
    print(doc._.conll_str_headers)

The snippet above will return (and print) the following string:

.. code:: text

    # sent_id = 1
    # text = I like cookies.
    1	I	-PRON-	PRON	PRP	PronType=prs	2	nsubj	_	_
    2	like	like	VERB	VBP	VerbForm=fin|Tense=pres	0	ROOT	_	_
    3	cookies	cookie	NOUN	NNS	Number=plur	2	dobj	_	_
    4	.	.	PUNCT	.	PunctType=peri	2	punct	_	_

    # sent_id = 2
    # text = Do you?
    1	Do	do	AUX	VBP	VerbForm=fin|Tense=pres	0	ROOT	_	_
    2	you	-PRON-	PRON	PRP	PronType=prs	1	nsubj	_	_
    3	?	?	PUNCT	.	PunctType=peri	1	punct	_	_


An advanced example, showing the more complex options:

* :code:`ext_names`: changes the attribute names to a custom key by using a dictionary. You can change:

  * :code:`conll_str`: a string representation of the CoNLL format
  * :code:`conll_str_headers`: the same as :code:`conll_str` but with leading lines containing sentence index
    and sentence text
  * :code:`conll`: a dictionary containing the field names and their values. For a :code:`Doc` object, this returns a list
    of dictionaries where each dictionary is a sentence

* :code:`field_names`: a dictionary containing a mapping of field names so that you can name them as you wish
* :code:`conversion_maps`: a two-level dictionary that looks like :code:`{field_name: {tag_name: replacement}}`.
  In other words, you can specify in which field a certain value should be replaced by another. This is especially
  useful when you are not satisfied with the tagset of a model and wish to change some tags to an alternative

The example below

* changes the custom attribute :code:`conll` to :code:`connl_for_pd`;
* changes the :code:`lemma` field to :code:`word_lemma`;
* converts any :code:`-PRON-` to :code:`PRON`;
* as a bonus: uses the output dictionary to create a pandas DataFrame.

.. code:: python

    import pandas as pd
    import spacy
    from spacy_conll import ConllFormatter


    nlp = spacy.load('en')
    conllformatter = ConllFormatter(nlp,
                                    ext_names={'conll': 'connl_for_pd'},
                                    field_names={'lemma': 'word_lemma'},
                                    conversion_maps={'word_lemma': {'-PRON-': 'PRON'}})
    nlp.add_pipe(conllformatter, after='parser')
    doc = nlp('I like cookies.')
    df = pd.DataFrame.from_dict(doc._.connl_for_pd[0])
    print(df)

The snippet above will output a pandas DataFrame:

.. code:: text

       id     form word_lemma upostag  ... head deprel  deps misc
    0   1        I       PRON    PRON  ...    2  nsubj     _    _
    1   2     like       like    VERB  ...    0   ROOT     _    _
    2   3  cookies     cookie    NOUN  ...    2   dobj     _    _
    3   4        .          .   PUNCT  ...    2  punct     _    _

    [4 rows x 10 columns]

spacy-stanfordnlp
+++++++++++++++++

Using :code:`spacy_conll` in conjunction with :code:`spacy-stanfordnlp` is similar to using it with :code:`spacy`:
in practice we are still simply adding a custom component pipeline to the existing pipeline, but this time that pipeline
is a Stanford NLP pipeline that is wrapped in spaCy's API.

.. code:: python

    from spacy_stanfordnlp import StanfordNLPLanguage
    import stanfordnlp

    from spacy_conll import ConllFormatter


    snlp = stanfordnlp.Pipeline(lang='en')
    nlp = StanfordNLPLanguage(snlp)
    conllformatter = ConllFormatter(nlp)
    nlp.add_pipe(conllformatter, last=True)

    s = 'A cookie is a baked or cooked food that is typically small, flat and sweet.'

    doc = nlp(s)
    print(doc._.conll_str)

Output:

.. code:: text

    1	A	a	DET	DT	_	2	det	_	_
    2	cookie	cookie	NOUN	NN	Number=sing	8	nsubj	_	_
    3	is	be	AUX	VBZ	VerbForm=fin|Tense=pres|Number=sing|Person=three	8	cop	_	_
    4	a	a	DET	DT	_	8	det	_	_
    5	baked	bake	VERB	VBN	VerbForm=part|Tense=past|Aspect=perf	8	amod	_	_
    6	or	or	CCONJ	CC	ConjType=comp	7	cc	_	_
    7	cooked	cook	VERB	VBN	VerbForm=part|Tense=past|Aspect=perf	5	conj	_	_
    8	food	food	NOUN	NN	Number=sing	0	root	_	_
    9	that	that	PRON	WDT	_	12	nsubj	_	_
    10	is	be	AUX	VBZ	VerbForm=fin|Tense=pres|Number=sing|Person=three	12	cop	_	_
    11	typically	typically	ADV	RB	Degree=pos	12	advmod	_	_
    12	small	small	ADJ	JJ	Degree=pos	8	acl:relcl	_	_
    13	,	,	PUNCT	,	PunctType=comm	14	punct	_	_
    14	flat	flat	ADJ	JJ	Degree=pos	12	conj	_	_
    15	and	and	CCONJ	CC	ConjType=comp	16	cc	_	_
    16	sweet	sweet	ADJ	JJ	Degree=pos	12	conj	_	_
    17	.	.	PUNCT	.	PunctType=peri	8	punct	_	_

.. _`spaCy's models`: https://spacy.io/models

----

**DEPRECATED:** :code:`Spacy2ConllParser`
+++++++++++++++++++++++++++++++++++++++++

There are two main methods, :code:`parse()` and :code:`parseprint()`. The latter is a convenience method for printing the output of
:code:`parse()` to stdout (default) or a file.

.. code:: python

    from spacy_conll import Spacy2ConllParser
    spacyconll = Spacy2ConllParser()

    # `parse` returns a generator of the parsed sentences
    for parsed_sent in spacyconll.parse(input_str="I like cookies.\nWhat about you?\nI don't like 'em!"):
        do_something_(parsed_sent)

    # `parseprint` prints output to stdout (default) or a file (use `output_file` parameter)
    # This method is called when using the command line
    spacyconll.parseprint(input_str='I like cookies.')


=======
Credits
=======
Based on the `initial work by rgalhama`_.

.. _initial work by rgalhama: https://github.com/rgalhama/spaCy2CoNLLU
