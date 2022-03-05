Usage examples ``spacy_conll``
==============================
It is recommended to initialise your parser with the :code:`init_nlp()` function as a handy shortcut. It allows you to
initialise any parser (`spacy`, `spacy-stanza`, `spacy-udpipe`) given a specific language
or model. Any keyword arguments passed to it will be passed down to the initialisation process. See the examples
in this directory to see how to correctly use it.

If you want to, you can also manually add the component to the parser. That would look something like this:

```python
import spacy
import spacy_conll
nlp = spacy.load("en_core_web_sm")
nlp.add_pipe("conll_formatter", last=True)
```
