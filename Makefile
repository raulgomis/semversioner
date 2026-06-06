ENV='.venv'

all: setup lint test coverage

.PHONY: setup
setup:
	@uv sync --all-extras --dev

.PHONY: lint
lint:
	@uv run ruff check .
	@uv run ruff format --check .

.PHONY: test
test:
	@uv run pytest

.PHONY: coverage
coverage:
	@uv run pytest --cov=semversioner --cov-report=term-missing

.PHONY: clean
clean:
	@rm -vrf $(ENV)/
	@rm -vrf .mypy_cache .pytest_cache __pycache__/* .coverage coverage.xml junit/*
	@rm -vrf ./build ./dist ./*.pyc ./*.egg-info
