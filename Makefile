PYTHON ?= python
PIP ?= $(PYTHON) -m pip
SRC := eda_aap_demo
TESTS := tests
CONTROLLER_ARGS ?=

.PHONY: help install install-dev install-eda run-eda format format-check lint typecheck security test compile quality clean

help:
	@echo "Targets: install install-dev install-eda run-eda format format-check lint typecheck security test compile quality clean"

install:
	$(PIP) install -r requirements.txt

install-dev: install
	$(PIP) install -r requirements-dev.txt

install-eda:
	$(PIP) install -r requirements-eda.txt

run-eda:
	ansible-rulebook --rulebook rulebooks/route_operational_requests.yml -i localhost, $(CONTROLLER_ARGS)

format:
	$(PYTHON) -m ruff format $(SRC) $(TESTS)
	$(PYTHON) -m ruff check --fix $(SRC) $(TESTS)

format-check:
	$(PYTHON) -m ruff format --check $(SRC) $(TESTS)

lint:
	$(PYTHON) -m ruff check $(SRC) $(TESTS)

typecheck:
	$(PYTHON) -m mypy $(SRC)

security:
	$(PYTHON) -m bandit -q -r $(SRC)

test:
	$(PYTHON) -m unittest discover

compile:
	$(PYTHON) -m compileall $(SRC)

quality: format-check lint typecheck security test compile

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type d -name .mypy_cache -prune -exec rm -rf {} +
	find . -type d -name .ruff_cache -prune -exec rm -rf {} +
