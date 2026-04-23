.PHONY: help test test-fast test-all test-unit test-integration test-workflow test-archivist test-verbose validate install clean start start-logs stop logs logs-color

# Default target
help:
	@echo "Elastic News - Makefile Commands"
	@echo "================================="
	@echo ""
	@echo "Testing:"
	@echo "  make test              - Run fast tests (excludes slow tests)"
	@echo "  make test-fast         - Same as 'make test'"
	@echo "  make test-all          - Run all tests including slow ones"
	@echo "  make test-unit         - Run only unit tests"
	@echo "  make test-integration  - Run integration tests"
	@echo "  make test-workflow     - Run full workflow test"
	@echo "  make test-archivist    - Run Archivist A2A integration tests"
	@echo "  make test-verbose      - Run tests with verbose output"
	@echo "  make test-coverage     - Run tests with coverage report"
	@echo "  make validate          - Validate all API keys and endpoints"
	@echo ""
	@echo "Development:"
	@echo "  make install           - Install dependencies"
	@echo "  make start             - Start all agents"
	@echo "  make start-logs        - Start agents + UI + show colorized logs"
	@echo "  make start-ui          - Start agents + React UI"
	@echo "  make stop              - Stop all agents"
	@echo "  make clean             - Clean up generated files"
	@echo ""
	@echo "Agent Management:"
	@echo "  make logs              - View all agent logs (plain)"
	@echo "  make logs-color        - View colorized agent logs (recommended)"
	@echo "  make status            - Check agent health"

# Testing targets
test:
	@echo "🧪 Running fast tests (excluding slow tests)..."
	pytest -v -m "not slow"

test-fast: test

test-all:
	@echo "🧪 Running all tests (including slow tests)..."
	pytest -v

test-unit:
	@echo "🧪 Running unit tests..."
	pytest -v -m unit

test-integration:
	@echo "🧪 Running integration tests..."
	pytest -v -m integration

test-workflow:
	@echo "🧪 Running workflow tests..."
	pytest -v -m workflow tests/test_workflow_pytest.py

test-archivist:
	@echo "🧪 Running Archivist A2A integration tests..."
	pytest -v tests/test_archivist_a2a.py

test-verbose:
	@echo "🧪 Running tests with verbose output..."
	pytest -vv -s

test-coverage:
	@echo "🧪 Running tests with coverage..."
	pytest --cov=agents --cov=utils --cov-report=html --cov-report=term

validate:
	@echo "🔑 Validating API keys and endpoints..."
	pytest -v -s tests/test_validate_config.py

# Development targets
install:
	@echo "📦 Installing dependencies..."
	pip install -r requirements.txt
	@echo "✅ Dependencies installed"

start:
	@echo "🚀 Starting all agents..."
	./scripts/start_newsroom.sh --reload

start-logs:
	@echo "🚀 Starting all agents + UI with colorized logs..."
	@./scripts/start_newsroom.sh --with-ui --reload
	@sleep 3
	@echo ""
	@python scripts/view_logs.py

start-ui:
	@echo "🚀 Starting agents + React UI..."
	./scripts/start_newsroom.sh --with-ui --reload

stop:
	@echo "🛑 Stopping all agents..."
	./scripts/start_newsroom.sh --stop

clean:
	@echo "🧹 Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf htmlcov/ .coverage 2>/dev/null || true
	@echo "✅ Cleanup complete"

# Agent management
logs:
	@echo "📋 Viewing agent logs (Ctrl+C to stop)..."
	tail -f logs/*.log

logs-color:
	@python scripts/view_logs.py

status:
	@echo "🔍 Checking agent health..."
	@python -c "import asyncio; from tests.conftest import AGENT_URLS; import httpx; from a2a.client import A2ACardResolver; \
	async def check(): \
	    async with httpx.AsyncClient(timeout=5.0) as client: \
	        for name, url in AGENT_URLS.items(): \
	            try: \
	                card_resolver = A2ACardResolver(client, url); \
	                await card_resolver.get_agent_card(); \
	                print(f'  ✅ {name:15s} {url}'); \
	            except Exception as e: \
	                print(f'  ❌ {name:15s} {url} - {str(e)[:50]}'); \
	asyncio.run(check())"
