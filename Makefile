# Format source code automatically
style:
	black --line-length 119 --target-version py36 spacy_conll examples
	isort spacy_conll examples

# Control quality
quality:
	black --check --line-length 119 --target-version py36 spacy_conll examples
	isort --check-only spacy_conll examples
	flake8 spacy_conll examples --exclude __pycache__,__init__.py

# Run tests
test:
	pytest tests
