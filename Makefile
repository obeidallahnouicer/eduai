# =============================================================================
# StudyOS — Makefile
# =============================================================================

.DEFAULT_GOAL := help
PYTHON        := python
UVICORN_APP   := app.main:app

# ---------------------------------------------------------------------------
# Colours (used only in the help target)
# ---------------------------------------------------------------------------
RESET  := \033[0m
BOLD   := \033[1m
CYAN   := \033[36m

# =============================================================================
# Help
# =============================================================================
.PHONY: help
help: ## Show this help message
	@printf '$(BOLD)StudyOS Backend — available targets$(RESET)\n\n'
	@grep -E '^[a-zA-Z_-]+:.*## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*## "}; {printf "  $(CYAN)%-24s$(RESET) %s\n", $$1, $$2}'
	@printf '\n'

# =============================================================================
# Development
# =============================================================================
.PHONY: dev
dev: ## Run the API with hot-reload (requires .env)
	uvicorn $(UVICORN_APP) --reload --host 0.0.0.0 --port 8000

.PHONY: install
install: ## Install all dependencies including dev extras
	pip install -e ".[dev]"

.PHONY: install-prod
install-prod: ## Install production dependencies only
	pip install -e "."

# =============================================================================
# Docker
# =============================================================================
.PHONY: up
up: ## Build and start all Docker Compose services (detached)
	docker compose up --build -d

.PHONY: up-logs
up-logs: ## Build and start all services, follow logs
	docker compose up --build

.PHONY: down
down: ## Stop and remove all containers
	docker compose down

.PHONY: down-volumes
down-volumes: ## Stop containers and remove named volumes (wipes DB & Redis)
	docker compose down -v

.PHONY: restart
restart: down up ## Full restart of the Docker stack

.PHONY: logs
logs: ## Tail logs for the api service
	docker compose logs -f api

.PHONY: ps
ps: ## Show running container status
	docker compose ps

# =============================================================================
# Database migrations
# =============================================================================
.PHONY: migrate
migrate: ## Apply all pending Alembic migrations
	alembic upgrade head

.PHONY: migrate-down
migrate-down: ## Downgrade one Alembic revision
	alembic downgrade -1

.PHONY: migrate-new
migrate-new: ## Generate a new migration (use: make migrate-new MSG="describe change")
	@test -n "$(MSG)" || (echo "Error: MSG is required. Example: make migrate-new MSG='add index'" && exit 1)
	alembic revision --autogenerate -m "$(MSG)"

.PHONY: migrate-current
migrate-current: ## Show the current Alembic revision
	alembic current

.PHONY: migrate-history
migrate-history: ## Show full Alembic migration history
	alembic history --verbose

# =============================================================================
# Code quality
# =============================================================================
.PHONY: lint
lint: ## Run Ruff linter (check only)
	ruff check app/ tests/

.PHONY: lint-fix
lint-fix: ## Run Ruff linter and auto-fix
	ruff check --fix app/ tests/

.PHONY: fmt
fmt: ## Format code with Ruff formatter
	ruff format app/ tests/

.PHONY: fmt-check
fmt-check: ## Check formatting without making changes
	ruff format --check app/ tests/

.PHONY: typecheck
typecheck: ## Run mypy static type checking
	mypy app/

.PHONY: check
check: lint fmt-check typecheck ## Run all checks (lint + format + types)

# =============================================================================
# Tests
# =============================================================================
.PHONY: test
test: ## Run the full test suite
	pytest tests/ -v

.PHONY: test-unit
test-unit: ## Run unit tests only
	pytest tests/unit/ -v

.PHONY: test-integration
test-integration: ## Run integration tests only
	pytest tests/integration/ -v

.PHONY: test-cov
test-cov: ## Run tests with HTML coverage report
	pytest tests/ --cov=app --cov-report=term-missing --cov-report=html
	@echo "Coverage report: htmlcov/index.html"

.PHONY: test-fast
test-fast: ## Run tests, stop at first failure
	pytest tests/ -x -v

# =============================================================================
# Frontend
# =============================================================================
.PHONY: fe-install
fe-install: ## Install frontend dependencies
	cd frontend && npm install

.PHONY: fe-dev
fe-dev: ## Start the frontend Vite dev server
	cd frontend && npm run dev

.PHONY: fe-build
fe-build: ## Build the frontend for production
	cd frontend && npm run build

.PHONY: fe-preview
fe-preview: ## Preview the production frontend build
	cd frontend && npm run preview

.PHONY: fe-lint
fe-lint: ## Lint the frontend with ESLint
	cd frontend && npm run lint

.PHONY: fe-typecheck
fe-typecheck: ## Type-check the frontend with tsc
	cd frontend && npm run typecheck

# =============================================================================
# Clean
# =============================================================================
.PHONY: clean
clean: ## Remove Python cache, coverage artefacts, and build files
	find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete
	rm -rf .mypy_cache .ruff_cache .pytest_cache htmlcov .coverage dist build

.PHONY: clean-uploads
clean-uploads: ## Remove all files from the uploads directory
	rm -rf uploads/*

.PHONY: clean-all
clean-all: clean clean-uploads ## Clean everything including uploads
