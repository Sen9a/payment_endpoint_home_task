.PHONY: help install db-upgrade db-migrate run test build up down logs clean

PYTEST ?= .venv/bin/pytest

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# --- Local development ------------------------------------------------------

install: ## Install dependencies with Poetry
	poetry install

db-upgrade: ## Apply Alembic migrations (base schema + payments table)
	.venv/bin/alembic upgrade head

db-migrate: ## Autogenerate a new migration after model changes (MSG="...")
	.venv/bin/alembic revision --autogenerate -m "$(MSG)"

run: ## Run the dev server locally on :8080
	.venv/bin/python server.py

test: ## Run the pytest suite (starts the Postgres container if needed)
	docker compose up -d db --wait
	$(PYTEST) -v

# --- Docker -----------------------------------------------------------------

build: ## Build the Docker image
	docker compose build

up: ## Build (if needed) and start the stack in the background
	docker compose up -d --build --wait

down: ## Stop the stack
	docker compose down

logs: ## Follow API container logs
	docker compose logs -f api

clean: ## Stop the stack and delete the database volume (DATA LOSS)
	docker compose down -v
