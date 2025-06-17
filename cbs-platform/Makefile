# Common development tasks and commands

.PHONY: help setup dev-up dev-down test lint format clean

# Default target
help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Setup
setup: ## Initial setup for development environment
	@echo "Setting up CBS Platform development environment..."
	cp .env.example .env
	python -m pip install --upgrade pip
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	pre-commit install
	@echo "Setup complete!"

# Development
dev-up: ## Start development environment
	@echo "Starting development environment..."
	docker-compose up -d
	@echo "Services started. Gateway available at http://localhost:8000"
	@echo "Admin portal available at http://localhost:8080"
	@echo "Web banking available at http://localhost:3000"

dev-down: ## Stop development environment
	@echo "Stopping development environment..."
	docker-compose down

dev-logs: ## View logs from all services
	docker-compose logs -f

dev-rebuild: ## Rebuild and restart services
	docker-compose down
	docker-compose build --no-cache
	docker-compose up -d

# Testing
test: ## Run all tests
	@echo "Running unit tests..."
	python -m pytest tests/unit -v
	@echo "Running integration tests..."
	python -m pytest tests/integration -v

test-unit: ## Run unit tests only
	python -m pytest tests/unit -v

test-integration: ## Run integration tests only
	python -m pytest tests/integration -v

test-e2e: ## Run end-to-end tests
	python -m pytest tests/e2e -v

test-coverage: ## Run tests with coverage report
	python -m pytest tests/ --cov=services --cov-report=html --cov-report=term

# Code Quality
lint: ## Run linting
	@echo "Running linting..."
	flake8 services/ platform/ applications/
	pylint services/ platform/ applications/
	mypy services/ platform/ applications/

format: ## Format code
	@echo "Formatting code..."
	black services/ platform/ applications/ tests/
	isort services/ platform/ applications/ tests/

check: ## Check code quality without fixing
	black --check services/ platform/ applications/ tests/
	isort --check-only services/ platform/ applications/ tests/
	flake8 services/ platform/ applications/

# Database
db-migrate: ## Run database migrations for all services
	@echo "Running database migrations..."
	cd services/customer-service && alembic upgrade head
	cd services/account-service && alembic upgrade head
	cd services/payment-service && alembic upgrade head
	cd services/transaction-service && alembic upgrade head
	cd services/loan-service && alembic upgrade head
	cd services/notification-service && alembic upgrade head
	cd services/audit-service && alembic upgrade head

db-reset: ## Reset all databases
	docker-compose down -v
	docker-compose up -d postgres redis
	sleep 10
	make db-migrate

# Documentation
docs: ## Generate documentation
	@echo "Generating documentation..."
	cd docs && mkdocs build

docs-serve: ## Serve documentation locally
	cd docs && mkdocs serve

# API Documentation
api-docs: ## Generate OpenAPI specifications
	@echo "Generating API documentation..."
	cd services/gateway-service && python generate_openapi.py
	cd services/customer-service && python generate_openapi.py
	cd services/account-service && python generate_openapi.py
	cd services/payment-service && python generate_openapi.py

# Monitoring
logs: ## View application logs
	docker-compose logs -f gateway customer-service account-service payment-service

monitor: ## Open monitoring dashboard
	@echo "Opening monitoring dashboard..."
	@echo "Prometheus: http://localhost:9090"
	@echo "Grafana: http://localhost:3001 (admin/admin)"

# Cleanup
clean: ## Clean up containers and volumes
	docker-compose down -v --remove-orphans
	docker system prune -f
	docker volume prune -f

clean-all: ## Clean everything including images
	make clean
	docker rmi $(docker images -q) || true

# Production
build: ## Build production images
	@echo "Building production images..."
	docker-compose -f docker-compose.prod.yml build

deploy-staging: ## Deploy to staging environment
	@echo "Deploying to staging..."
	# Add staging deployment commands here

deploy-prod: ## Deploy to production environment
	@echo "Deploying to production..."
	# Add production deployment commands here

# Security
security-scan: ## Run security scans
	@echo "Running security scans..."
	safety check
	bandit -r services/ platform/ applications/

# Performance
load-test: ## Run load tests
	@echo "Running load tests..."
	python tools/testing/load_test.py

benchmark: ## Run performance benchmarks
	@echo "Running benchmarks..."
	python tools/testing/benchmark.py

# Service Management
service-logs: ## View logs for specific service (usage: make service-logs SERVICE=customer-service)
	docker-compose logs -f $(SERVICE)

service-shell: ## Access shell for specific service (usage: make service-shell SERVICE=customer-service)
	docker-compose exec $(SERVICE) /bin/bash

service-restart: ## Restart specific service (usage: make service-restart SERVICE=customer-service)
	docker-compose restart $(SERVICE)

# Development Tools
generate-service: ## Generate new service template (usage: make generate-service NAME=new-service)
	python tools/cli/generate_service.py --name $(NAME)

generate-migration: ## Generate database migration (usage: make generate-migration SERVICE=customer-service MESSAGE="add new field")
	cd services/$(SERVICE) && alembic revision --autogenerate -m "$(MESSAGE)"

# Version Management
version: ## Show current version
	@echo "CBS Platform Version 2.0.0"

bump-version: ## Bump version (usage: make bump-version TYPE=patch|minor|major)
	bump2version $(TYPE)
	git push && git push --tags
