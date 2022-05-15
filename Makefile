ENV='venv'

all: setup lint test

.PHONY: setup
setup:
	@# It assumes the default python3 installation for Mac OS is pyhton 3
	@test -d $(ENV) || python3 -m venv $(ENV)
	@$(ENV)/bin/python3 -m pip install --upgrade pip
	@$(ENV)/bin/python3 -m pip install -r requirements-dev.txt
	@$(ENV)/bin/python3 -m pip install -r requirements.txt
	@# make the project packages discoverable (it uses the setup.py to install)
	@$(ENV)/bin/python3 -m pip install -e .

.PHONY: lint
lint:
	@$(ENV)/bin/flake8

.PHONY: test
test:
	@$(ENV)/bin/python -m pytest

.PHONY: clean
clean:
	@rm -vrf venv/
	@rm -vrf .mypy_cache .pytest_cache __pycache__/*