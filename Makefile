UV ?= uv

.DEFAULT_GOAL := help
.PHONY: help setup lint format test validate sync sync-check scorecard migrate up run-api run-viewer

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

validate: ## R1: validate theses/ against schema/
	$(UV) run python -m turtle_insight.services.validation

sync: ## Sync theses files into the DB index (files -> db, one-way)
	$(UV) run python -m turtle_insight.storage.sync

sync-check: ## Verify theses files are DB-round-trippable (CI)
	$(UV) run python -m turtle_insight.storage.sync --check

scorecard: ## R4: print the calibration track-record scorecard
	$(UV) run python -m turtle_insight.services.reporting

migrate: ## Apply DB migrations (alembic upgrade head; respects TI_DB_URL)
	$(UV) run --extra pg alembic upgrade head

up: ## Start backing services (postgres + redis) via docker compose
	docker compose up -d

run-api: ## Run FastAPI locally (extra: api)
	$(UV) run --extra api uvicorn turtle_insight.api.app:app --reload

run-viewer: ## Run Streamlit viewer (extra: viewer)
	$(UV) run --extra viewer streamlit run src/turtle_insight/viewer/app.py
