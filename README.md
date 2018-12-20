# spaCy2CoNLLU
Simple script to parse text with spaCy and print the output in [CoNLL-U format](http://universaldependencies.org/docs/format.html).

### Requirements

* Python >=3.6
* [spaCy](https://spacy.io/usage/#installation)
* a spaCy language model

### Usage as command line script
```
usage: __init__.py [-h] [--input_file INPUT_FILE]
                   [--input_encoding INPUT_ENCODING] [--input_str INPUT_STR]
                   [--output_file OUTPUT_FILE]
                   [--output_encoding OUTPUT_ENCODING] [--model MODEL]
                   [--nlp NLP]

optional arguments:
  -h, --help            show this help message and exit
  --input_file INPUT_FILE
                        Path to file with sentences to parse. (default: None)
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

```
