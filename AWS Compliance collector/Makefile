.PHONY: install test lint clean coverage help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies
	pip install -r requirements.txt

test: ## Run all tests
	python -m pytest tests/ -v

test-fast: ## Run tests without slow integration tests
	python -m pytest tests/ -v -m "not slow"

coverage: ## Run tests with coverage report
	python -m pytest tests/ --cov=src --cov-report=term-missing --cov-report=html

lint: ## Run linter
	ruff check src/ tests/

lint-fix: ## Run linter with auto-fix
	ruff check src/ tests/ --fix

clean: ## Remove build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name htmlcov -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	find . -name ".coverage" -delete 2>/dev/null || true

pipeline: ## Run the full pipeline demo (Phase 7 notebook logic)
	python -c "from tests.conftest import *; print('Pipeline imports OK')"
	python -m pytest tests/test_end_to_end.py -v
