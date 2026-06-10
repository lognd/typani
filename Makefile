VENV    := .venv
PYTHON  := $(VENV)/bin/python
PIP     := $(VENV)/bin/pip
RUFF    := $(VENV)/bin/ruff
BLACK   := $(VENV)/bin/black
ISORT   := $(VENV)/bin/isort
MYPY    := $(VENV)/bin/mypy
PYTEST  := $(VENV)/bin/pytest

.PHONY: all venv install lint format typecheck test clean

all: lint typecheck test

$(VENV)/bin/activate:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip --quiet

venv: $(VENV)/bin/activate

install: venv
	$(PIP) install -e ".[dev]" --quiet

lint: install
	$(RUFF) check src/ tests/
	$(BLACK) --check src/ tests/

format: install
	$(BLACK) src/ tests/
	$(ISORT) src/ tests/

typecheck: install
	$(MYPY) --config-file mypy-py310.ini src/

test: install
	$(PYTEST)

clean:
	rm -rf $(VENV) .mypy_cache .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
