# Development setup
install: ## Install dependencies
	poetry install --with dev

# Testing commands
test: ## Run all tests
	poetry run pytest

test-verbose: ## Run tests with verbose output
	poetry run pytest -v

# Code quality
pre-commit: ## Run pre-commit hooks on all files
	poetry run pre-commit run --all-files

# Docker commands
local_run: ## Start containers
	docker compose -f docker-compose.yaml up

local_build: ## Build and start containers
	docker compose -f docker-compose.yaml up --build

local_build_no_cache: ## Build without cache and start containers
	docker compose -f docker-compose.yaml build --no-cache && docker compose -f docker-compose.yaml up

local_stop: ## Stop containers
	docker compose -f docker-compose.yaml stop

local_down: ## Stop and remove containers
	docker compose -f docker-compose.yaml down

local_logs: ## Show container logs
	docker compose -f docker-compose.yaml logs -f

