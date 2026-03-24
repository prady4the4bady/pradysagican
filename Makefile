# ══════════════════════════════════════════════════════════════════════════
#                    PRADYSAGICAN — Project Commands
# ══════════════════════════════════════════════════════════════════════════

.PHONY: install test serve chat status benchmark evolve lint clean help

# Default target
help: ## Show this help
	@echo "PRADYSAGICAN v6.0 — Available Commands"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## One-command install (creates venv, installs deps, runs tests)
	@bash setup.sh

test: ## Run all 138 tests
	python -m pytest tests/ -v --tb=short

serve: ## Start the API server on port 8000
	pradysagican serve --port 8000

chat: ## Start interactive chat mode
	pradysagican chat

status: ## Show system health (40/40 subsystems)
	pradysagican status

benchmark: ## Run all 31 benchmarks
	pradysagican benchmark

evolve: ## Start self-evolution cycle
	pradysagican evolve

lint: ## Run code quality checks
	ruff check pradysagican/ tests/

clean: ## Remove build artifacts and caches
	rm -rf __pycache__ .pytest_cache .ruff_cache dist/ build/ *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

docker-build: ## Build Docker image
	docker build -t pradysagican:v6 .

docker-run: ## Run in Docker container
	docker run -p 8000:8000 pradysagican:v6
