# Format source code automatically
style:
	black --line-length 119 --target-version py38 --exclude src\/spacy_conll\/version.py src/spacy_conll examples
	isort src/spacy_conll examples

# Control quality
quality:
	black --check --line-length 119 --target-version py38 --exclude src\/spacy_conll\/version.py src/spacy_conll examples
	isort --check-only src/spacy_conll examples
	flake8 src/spacy_conll examples --exclude __pycache__,__init__.py

# Run tests
test:
	pytest tests
