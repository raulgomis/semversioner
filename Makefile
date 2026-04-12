ENV='venv'

all: setup lint test coverage

.PHONY: setup
setup:
	@# It assumes the default python3 installation for Mac OS is python 3
	@test -d $(ENV) || python3 -m venv $(ENV)
	@$(ENV)/bin/python3 -m pip install --upgrade pip
	@$(ENV)/bin/python3 -m pip install -e .[dev]

.PHONY: lint
lint:
	@$(ENV)/bin/ruff check .
	@$(ENV)/bin/ruff format --check .

.PHONY: test
test:
	@$(ENV)/bin/python -m pytest

.PHONY: coverage
coverage:
	@$(ENV)/bin/python -m pytest --cov=semversioner --cov-report=term-missing

.PHONY: clean
clean:
	@rm -vrf $(ENV)/
	@rm -vrf .mypy_cache .pytest_cache __pycache__/* .coverage coverage.xml junit/*
	@rm -vrf ./build ./dist ./*.pyc ./*.egg-info
