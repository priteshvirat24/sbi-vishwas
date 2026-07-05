# =============================================================================
# SBI VISHWAS — Developer Commands
# =============================================================================

.PHONY: help dev dev-backend dev-frontend docker-up docker-down docker-rebuild \
        migrate migrate-create test test-unit test-integration test-api lint \
        format clean install logs db-shell redis-shell

# Default target
help: ## Show this help
	@echo "SBI Vishwas — Developer Commands"
	@echo "================================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ---------------------------------------------------------------------------
# Development
# ---------------------------------------------------------------------------

install: ## Install all dependencies
	cd backend && pip install -e ".[dev]"
	cd frontend && npm install

dev: ## Start full development stack (Docker)
	docker compose up -d
	@echo "\n✅ All services started:"
	@echo "   Backend:    http://localhost:8000"
	@echo "   Frontend:   http://localhost:3000"
	@echo "   API Docs:   http://localhost:8000/docs"
	@echo "   Prometheus: http://localhost:9090"
	@echo "   Grafana:    http://localhost:3001"

dev-backend: ## Start backend locally (requires DB/Redis running)
	cd backend && uvicorn src.api.main:create_app --factory --host 0.0.0.0 --port 8000 --reload --reload-dir src

dev-frontend: ## Start frontend locally
	cd frontend && npm run dev

dev-worker: ## Start Celery worker locally
	cd backend && celery -A src.workflows.celery_app worker --loglevel=info --concurrency=4

dev-beat: ## Start Celery beat locally
	cd backend && celery -A src.workflows.celery_app beat --loglevel=info

# ---------------------------------------------------------------------------
# Docker
# ---------------------------------------------------------------------------

docker-up: ## Start all Docker services
	docker compose up -d

docker-down: ## Stop all Docker services
	docker compose down

docker-rebuild: ## Rebuild and restart all Docker services
	docker compose down
	docker compose build --no-cache
	docker compose up -d

docker-logs: ## Follow Docker logs
	docker compose logs -f

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

migrate: ## Run database migrations
	cd backend && alembic upgrade head

migrate-create: ## Create new migration (usage: make migrate-create MSG="description")
	cd backend && alembic revision --autogenerate -m "$(MSG)"

migrate-rollback: ## Rollback last migration
	cd backend && alembic downgrade -1

db-shell: ## Open PostgreSQL shell
	docker compose exec postgres psql -U $${DATABASE_USER:-vishwas} -d $${DATABASE_NAME:-sbi_vishwas}

redis-shell: ## Open Redis shell
	docker compose exec redis redis-cli -a $${REDIS_PASSWORD:-vishwas_redis_dev}

# ---------------------------------------------------------------------------
# Testing
# ---------------------------------------------------------------------------

test: ## Run all tests
	cd backend && python -m pytest tests/ -v --cov=src --cov-report=term-missing

test-unit: ## Run unit tests only
	cd backend && python -m pytest tests/unit/ -v --cov=src

test-integration: ## Run integration tests (requires Docker services)
	cd backend && python -m pytest tests/integration/ -v

test-api: ## Run API tests
	cd backend && python -m pytest tests/api/ -v

test-agents: ## Run agent tests
	cd backend && python -m pytest tests/agents/ -v

test-frontend: ## Run frontend tests
	cd frontend && npm test

# ---------------------------------------------------------------------------
# Code Quality
# ---------------------------------------------------------------------------

lint: ## Run linters
	cd backend && ruff check src/ tests/
	cd frontend && npm run lint

lint-fix: ## Fix linting issues
	cd backend && ruff check --fix src/ tests/
	cd frontend && npm run lint -- --fix

format: ## Format code
	cd backend && ruff format src/ tests/
	cd frontend && npx prettier --write "src/**/*.{ts,tsx,css}"

typecheck: ## Run type checking
	cd backend && mypy src/
	cd frontend && npx tsc --noEmit

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

clean: ## Clean build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name node_modules -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .next -exec rm -rf {} + 2>/dev/null || true
	rm -rf backend/dist backend/build frontend/.next frontend/out

logs: ## View backend logs
	docker compose logs -f backend celery-worker

seed: ## Seed database with initial data
	cd backend && python -m src.database.seed

env: ## Copy .env.example to .env
	cp .env.example .env
	@echo "✅ Created .env from .env.example — fill in your credentials"
