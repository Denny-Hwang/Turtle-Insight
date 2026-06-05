UV ?= uv

.DEFAULT_GOAL := help
.PHONY: help setup lint format test validate run-api run-viewer

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

setup: ## Install deps (core+dev) and pre-commit hooks
	$(UV) sync --extra dev
	$(UV) run pre-commit install

lint: ## ruff check + format check + mypy (strict)
	$(UV) run ruff check src tests
	$(UV) run ruff format --check src tests
	$(UV) run mypy

format: ## Auto-format and fix with ruff
	$(UV) run ruff format src tests
	$(UV) run ruff check --fix src tests

test: ## Run pytest
	$(UV) run pytest

validate: ## R1: validate theses/ against schema/ (R1 logic lands in P1)
	$(UV) run python -m turtle_insight.services.validation

run-api: ## Run FastAPI locally (extra: api)
	$(UV) run --extra api uvicorn turtle_insight.api.app:app --reload

run-viewer: ## Run Streamlit viewer (extra: viewer)
	$(UV) run --extra viewer streamlit run src/turtle_insight/viewer/app.py
