===========================
Parsing to CoNLL with spaCy
===========================
This module allows you to parse a text to `CoNLL-U format`_. You can use it as a command line tool, or embed it in your
own scripts by adding it as a custom component to a spaCy pipeline. 

Note that the module simply takes spaCy output and puts it in a formatted string adhering to the linked ConLL-U format. It does not as of yet do an explicit tagset mapping of spaCy to UD tags. The output tags depend on the spaCy model used.

.. _`CoNLL-U format`: https://universaldependencies.org/format.html

============
Installation
============

Requires `spaCy`_ and an `installed spaCy language model`_. When using the module from the command line, you also need the :code:`packaging` package.

.. code:: bash

  pip install spacy_conll

.. _spaCy: https://spacy.io/usage/models#section-quickstart
.. _installed spaCy language model: https://spacy.io/usage/models

=====
Usage
=====
Command line
------------
.. code:: bash

    > python -m spacy_conll -h
    usage: [-h] [-f INPUT_FILE] [-a INPUT_ENCODING] [-b INPUT_STR]
           [-t] [-o OUTPUT_FILE] [-c OUTPUT_ENCODING] [-m MODEL] [-s]
           [-d] [-e] [-j N_PROCESS] [-v]

    Parse an input string or input file to CoNLL-U format.

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
      -t, --is_tokenized    Indicates whether your text has already been tokenized
                            (space-seperated). (default: False)
      -o OUTPUT_FILE, --output_file OUTPUT_FILE
                            Path to output file. If not specified, the output will
                            be printed on standard output. (default: None)
      -c OUTPUT_ENCODING, --output_encoding OUTPUT_ENCODING
                            Encoding of the output file. Default value is system
                            default. (default: cp1252)
      -m MODEL, --model MODEL
                            spaCy model to use (must be installed). (default:
                            en_core_web_sm)
      -s, --disable_sbd     Disables spaCy automatic sentence boundary detection.
                            In practice, disabling means that every line will be
                            parsed as one sentence, regardless of its actual
                            content. (default: False)
      -d, --include_headers
                            To include headers before the output of every
                            sentence. These headers include the sentence text and
                            the sentence ID. (default: False)
      -e, --no_force_counting
                            To disable force counting the 'sent_id', starting from
                            1 and increasing for each sentence. Instead, 'sent_id'
                            will depend on how spaCy returns the sentences. Must
                            have 'include_headers' enabled. (default: False)
      -j N_PROCESS, --n_process N_PROCESS
                            Number of processes to use in nlp.pipe(). -1 will use
                            as many cores as available. Requires spaCy v2.2.2.
                            (default: 1)
      -v, --verbose         To print the output to stdout, regardless of
                            'output_file'. (default: False)


For example, parsing a sentence:

.. code:: bash

    >  python -m spacy_conll --input_str "I like cookies . What about you ?" --is_tokenized --include_headers
    # sent_id = 1
    # text = I like cookies .
    1       I       -PRON-  PRON    PRP     PronType=prs    2       nsubj   _       _
    2       like    like    VERB    VBP     VerbForm=fin|Tense=pres 0       ROOT    _       _
    3       cookies cookie  NOUN    NNS     Number=plur     2       dobj    _       _
    4       .       .       PUNCT   .       PunctType=peri  2       punct   _       _

    # sent_id = 2
    # text = What about you ?
    1       What    what    NOUN    WP      PronType=int|rel        2       dep     _       _
    2       about   about   ADP     IN      _       0       ROOT    _       _
    3       you     -PRON-  PRON    PRP     PronType=prs    2       pobj    _       _
    4       ?       ?       PUNCT   .       PunctType=peri  2       punct   _       _

For example, parsing a large input file and writing output to output file, using four processes:

.. code:: bash

    > python -m spacy_conll --input_file large-input.txt --output_file large-conll-output.txt --include_headers --disable_sbd -j 4

In Python
---------

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

**DEPRECATED:** :code:`Spacy2ConllParser`

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
