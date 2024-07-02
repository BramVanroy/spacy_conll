style:
	black src/spacy_conll tests
	isort src/spacy_conll tests

quality:
	black --check --diff src/spacy_conll tests
	isort --check-only src/spacy_conll tests
	flake8 src/spacy_conll tests

test:
	pytest tests
