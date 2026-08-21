VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
RUFF := $(VENV)/bin/ruff
RUMDL := $(VENV)/bin/rumdl
MYPY := $(VENV)/bin/mypy
DEEPEVAL := $(VENV)/bin/deepeval

TARGETS := help install install-test install-tools clean lint format typecheck test test-unit test-eval cursor-install cursor-uninstall

.PHONY: $(TARGETS)

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

$(VENV):
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip

install: install-test install-tools ## Set up everything (venv + deps)

install-test: $(VENV) ## Install test dependencies (deepeval)
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[test]"

install-tools: $(VENV) ## Install linting/formatting tools (ruff)
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[tools]"

clean: ## Remove virtual environment and local Cursor install
	-$(PYTHON) scripts/cursor.py uninstall
	rm -rf $(VENV) node_modules

cursor-install: $(VENV) ## Install this plugin into a local Cursor for development
	$(PYTHON) scripts/cursor.py install

cursor-uninstall: $(VENV) ## Uninstall this plugin from the local Cursor install
	$(PYTHON) scripts/cursor.py uninstall

lint: ## Run linter checks (ruff for Python, rumdl for Markdown)
	$(RUFF) check .
	$(RUMDL) check .

format: ## Auto-format code (ruff for Python, rumdl for Markdown)
	$(RUFF) format .
	$(RUFF) check --fix .
	$(RUMDL) check --fix .

typecheck: ## Run mypy static type checks
	$(MYPY)

test: ## Run all tests (set testdir=<path> to route to the matching runner)
ifdef testdir
	@if echo "$(testdir)" | grep -q "tests/eval"; then \
		$(MAKE) test-eval testdir="$(testdir)"; \
	else \
		$(MAKE) test-unit testdir="$(testdir)"; \
	fi
else
	@$(MAKE) test-unit
	@$(MAKE) test-eval
endif

test-unit: ## Run structural/unit validation tests (set testdir=<path> to target specific files)
	$(PYTHON) -m pytest $(or $(testdir),tests/unit/) -v

test-eval: ## Run LLM-judged tests (requires GEMINI_API_KEY & SLACK_MCP_TOKEN; set testdir=<path> to target specific files)
	$(DEEPEVAL) test run $(or $(testdir),tests/eval/) -v
