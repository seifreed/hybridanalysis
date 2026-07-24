.PHONY: install format lint type security test gate

install:
	pip install -e ".[dev]"

format:
	black .

lint:
	black --check .
	ruff check .

type:
	mypy

security:
	bandit -r src
	pip-audit

test:
	pytest

gate: lint type security test
