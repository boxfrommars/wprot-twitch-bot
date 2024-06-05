.PHONY: all
all: qual test

.PHONY: qual
qual: flake8 lint mypy

.PHONY: flake8
flake8:
	@flake8 .

.PHONY: lint
lint:
	@find . -name "*.py" -not -path "./env/*" -exec pylint '{}' +

.PHONY: mypy
mypy:
	@mypy --explicit-package-bases .

.PHONY: deps
deps:
	@pip3 install -r requirements-dev.txt

.PHONY: test
test:
	@pytest tests
