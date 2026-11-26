# Examples

Each script runs with `uv run python examples/<script>.py` after `uv sync`. They use the model `en_core_web_sm`.

- `example-adding-conll-to-docbin.py`: add CoNLL-U to documents that are stored in a `DocBin`.
- `example-reading-conllu-file.py`: read a CoNLL-U file as a spaCy `Doc`.
- `example-spacy-df-write-to-file.py`: write the pandas table of every sentence to its own file.
- `example-use-own-indices.py`: write your own IDs in the `# sent_id` lines with the `sent_ids` option of `ConllParser.parse_text_as_conll`.

`init_parser` builds a pipeline that ends with the `conll_formatter` component. Options for the formatter go in `formatter_config`:

```python
from spacy_conll import init_parser

nlp = init_parser(
    "en_core_web_sm", "spacy", formatter_config={"include_headers": True}
)
```

You can also add the component to a pipeline yourself:

```python
import spacy

nlp = spacy.load("en_core_web_sm")
nlp.add_pipe("conll_formatter", last=True)
```
