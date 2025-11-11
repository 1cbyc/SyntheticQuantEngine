PYTHON ?= python3
PIP ?= pip

VENV_DIR := .venv
ACTIVATE := . $(VENV_DIR)/bin/activate

.PHONY: help setup install fmt lint test fetch-data notebook clean

help:
	@echo "Common commands:"
	@echo "  make setup       Create virtualenv and install project (editable)."
	@echo "  make lint        Run ruff linting."
	@echo "  make test        Run pytest test suite."
	@echo "  make fmt         Run ruff format."
	@echo "  make fetch-data  Fetch latest Volatility 25 hourly candles."
	@echo "  make notebook    Launch Jupyter Lab inside venv."
	@echo "  make clean       Remove build artifacts."

setup:
	$(PYTHON) -m venv $(VENV_DIR)
	$(ACTIVATE) && $(PIP) install --upgrade pip
	$(ACTIVATE) && $(PIP) install -e ".[dev]"

fmt:
	$(ACTIVATE) && ruff format src tests

lint:
	$(ACTIVATE) && ruff check src tests

test:
	$(ACTIVATE) && pytest

fetch-data:
	$(ACTIVATE) && $(PYTHON) -m synthetic_quant_engine.cli fetch-data --symbol R_25 --granularity 3600 --count 1000

notebook:
	$(ACTIVATE) && jupyter lab

clean:
	rm -rf $(VENV_DIR) build dist *.egg-info .pytest_cache .ruff_cache

