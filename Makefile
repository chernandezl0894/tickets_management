.DEFAULT_GOAL := help

.PHONY: help install run lint format typecheck test test-cov check up down logs clean

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| sort \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install:  ## Sync dependencies and install pre-commit hooks
	uv sync
	uv run pre-commit install

run:  ## Run the API with auto-reload
	uv run uvicorn tickets_management.main:app --reload

lint:  ## Run Ruff lint checks
	uv run ruff check .

format:  ## Format code with Ruff
	uv run ruff format .

typecheck:  ## Run mypy strict type checks
	uv run mypy .

test:  ## Run the test suite
	uv run pytest

test-cov:  ## Run tests with coverage
	uv run pytest --cov=tickets_management

check: lint typecheck test  ## Run lint, typecheck and tests (CI)

up:  ## Start the Docker Compose stack
	docker compose up -d

down:  ## Stop the Docker Compose stack
	docker compose down

logs:  ## Follow the Docker Compose logs
	docker compose logs -f

clean:  ## Remove Python and tool caches
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache .mypy_cache
