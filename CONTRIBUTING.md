# Contributing to `spacy_conll`

If you want to contribute to `spacy_conll`, it is recommended that you clone and install the repository with
 the `dev` option, which will install all required dependencies.

```bash
git clone https://github.com/BramVanroy/spacy_conll.git
cd spacy_conll
pip install -e .[dev]
```

You'll also need to install the basic English spaCy model to successfully run the tests.

```bash
python -m spacy download en_core_web_sm
```

You are now ready to start working on your issue. If you are solving a bug, please first create [an issue](https://github.com/BramVanroy/spacy_conll/issues)
 and mention that you are working on it. This way, other people with the same issue know that it is being worked on.
 Then, you can start your [pull request](https://github.com/BramVanroy/spacy_conll/pulls) from your cloned branch.

**Important notes**
- If you are still working on a PR, add `[WIP]` to the front of the title of the PR!
- If your PR solves an issue, add `closes <link to the issue>` to the PR text so that the issue is closed automatically
- Run the tests before finalizing the PR to make sure that everything is running as expected with `pytest tests/`
- Ensure style is as expected with `make style` and `make quality`. We use black and isort for formatting.
- When your PR is ready to be reviewed, remove `[WIP]` from the title. If you have not received any response after a
  week, feel free to tag me on Github.
