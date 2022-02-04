TESTS = tests

VENV ?= .venv_ubuntu
CODE = app

.PHONY: venv
.PHONY: test
test:
	pytest -v tests

.PHONY: lint
lint:
	flake8 --jobs 4 --statistics --show-source $(CODE)
	pylint --jobs 4 --rcfile=setup.cfg $(CODE)
	mypy $(CODE)
	black --skip-string-normalization --check $(CODE)

.PHONY: format
format:
	isort $(CODE)
	black --skip-string-normalization $(CODE)
	autoflake --recursive --in-place --remove-all-unused-imports $(CODE)
	unify --in-place --recursive $(CODE)

.PHONY: ci
ci:	lint test