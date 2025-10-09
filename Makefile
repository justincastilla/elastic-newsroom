.PHONY: help install install-dev format lint test test-cov clean start stop

help:
	@echo "Elastic Newsroom - Development Commands"
	@echo "========================================"
	@echo ""
	@echo "Setup:"
	@echo "  make install        Install production dependencies"
	@echo "  make install-dev    Install development dependencies"
	@echo ""
	@echo "Code Quality:"
	@echo "  make format         Format code with black and isort"
	@echo "  make lint          Run linters (flake8, mypy)"
	@echo "  make test          Run tests"
	@echo "  make test-cov      Run tests with coverage report"
	@echo ""
	@echo "Agents:"
	@echo "  make start         Start all agents"
	@echo "  make stop          Stop all agents"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean         Clean temporary files"
	@echo ""

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

format:
	@echo "Formatting with black..."
	black agents/ tests/ scripts/
	@echo "Sorting imports with isort..."
	isort agents/ tests/ scripts/

lint:
	@echo "Running flake8..."
	flake8 agents/ tests/ scripts/
	@echo "Running mypy..."
	mypy agents/ --ignore-missing-imports

test:
	pytest tests/

test-cov:
	pytest tests/ --cov=agents --cov-report=html --cov-report=term-missing
	@echo ""
	@echo "Coverage report generated in htmlcov/index.html"

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache htmlcov .coverage
	@echo "Cleaned temporary files"

start:
	./start_newsroom.sh

stop:
	./start_newsroom.sh --stop
