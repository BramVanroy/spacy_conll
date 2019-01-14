===========================
Parsing to CoNLL with spaCy
===========================
This module allows you to parse a text to `CoNLL-U format`_. You can use it as a command line tool, or embed it in your own
scripts.

.. _`CoNLL-U format`: https://universaldependencies.org/format.html

============
Installation
============

Requires `spacy`_ and an `installed spaCy language model`_.

.. code:: bash

  pip install spacy_conll

.. _spacy: https://spacy.io/usage/models#section-quickstart
.. _installed spaCy language model: https://spacy.io/usage/models

=====
Usage
=====
Command line
------------
.. code:: bash

    usage: __main__.py [-h] [--input_file INPUT_FILE]
                       [--input_encoding INPUT_ENCODING] [--input_str INPUT_STR]
                       [--output_file OUTPUT_FILE]
                       [--output_encoding OUTPUT_ENCODING] [--model MODEL]
                       [--nlp NLP]

    optional arguments:
      -h, --help            show this help message and exit
      --input_file INPUT_FILE
                            Path to file with sentences to parse. Has precedence
                            over 'input_str'. (default: None)
      --input_encoding INPUT_ENCODING
                            Encoding of the input file. Default value is system
                            default. (default: cp1252)
      --input_str INPUT_STR
                            Input string to parse. (default: None)
      --output_file OUTPUT_FILE
                            Path to output file. If not specified, the output will
                            be printed on standard output. (default: None)
      --output_encoding OUTPUT_ENCODING
                            Encoding of the output file. Default value is system
                            default. (default: cp1252)
      --model MODEL         spaCy model to use (e.g. 'es_core_news_md'). (default:
                            en_core_web_sm)
      --nlp NLP             Optional already initialised spaCy NLP model. Has
                            precedence over 'model'. (default: None)

For example, parsing a sentence:

.. code:: bash

    > python -m spacy_conll --input_str "I like cookies."
    # sent_id = 1
    # text = I like cookies.
    1       I       -PRON-  PRON    PRP     PronType=prs    2       nsubj   _       _
    2       like    like    VERB    VBP     VerbForm=fin|Tense=pres 0       ROOT    _       _
    3       cookies cookie  NOUN    NNS     Number=plur     2       dobj    _       _
    4       .       .       PUNCT   .       PunctType=peri  2       punct   _       _

For example, parsing an input file and writing output to output file:

.. code:: bash

    > python -m spacy_conll --input_file large-input.txt --output_file large-conll-output.txt

In Python
------------
There are two main methods, `parse` and `parseprint()`. The latter is a convenience method for printing the output of
`parse()` to a file or stdout.

.. code:: python

    from spacy_conll import Spacy2ConllParser
    spacyconll = Spacy2ConllParser()

    # `parse` returns a generator of the parsed sentences
    for parsed_sent in spacyconll.parse(input_str='I like cookies.\nWhat about you?\nI don't like 'em!'):
        do_something_(parsed_sent)

    # `parseprint` prints output to stdout (default) or a file (use `output_file` parameter)
    # This method is called when using the command line
    spacyconll.parseprint(input_str='I like cookies.')


=======
Credits
=======
Based on the `initial work by rgalhama`_.

.. _initial work by rgalhama: https://github.com/rgalhama/spaCy2CoNLLU

