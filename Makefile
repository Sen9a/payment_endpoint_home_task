.PHONY: help install db-upgrade db-migrate run test test-unit build up up-db up-api down logs clean

PYTEST ?= .venv/bin/pytest

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# --- Local development ------------------------------------------------------

install: ## Install dependencies with Poetry
	poetry install

db-upgrade: ## Apply Alembic migrations (base schema + payments table)
	alembic upgrade head

db-migrate: ## Autogenerate a new migration after model changes (MSG="...")
	alembic revision --autogenerate -m "$(MSG)"

run: ## Run the dev server locally on :8080
	python server.py

test: ## Run the pytest suite (starts the Postgres container if needed)
	docker compose up -d db --wait
	$(PYTEST) -v

test-unit: ## Run only the database-free unit tests (no containers needed)
	$(PYTEST) unit_tests/ -v

# --- Docker -----------------------------------------------------------------

build: ## Build the Docker image
	docker compose build

up: ## Build (if needed) and start the stack in the background
	docker compose up -d --build --wait

up-db: ## Start only the Postgres container in the background
	docker compose up -d db --wait

up-api: ## Build (if needed) and start only the API container (requires db)
	docker compose up -d --build --wait api

down: ## Stop the stack
	docker compose down

logs: ## Follow API container logs
	docker compose logs -f api

clean: ## Stop the stack and delete the database volume (DATA LOSS)
	docker compose down -v
