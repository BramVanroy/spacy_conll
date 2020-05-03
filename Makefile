# Format source code automatically
style:
	black --line-length 96 --target-version py36 spacy_conll examples
	isort --recursive spacy_conll examples

# Control quality
quality:
	black --check --line-length 96 --target-version py36 spacy_conll examples
	isort --check-only --recursive spacy_conll examples
	flake8 spacy_conll examples --exclude __pycache__,__init__.py

# Run tests
test:
	pytest spacy_conll/tests
