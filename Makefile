setup: ## Set up development environment
	@echo "Setting up development environment with uv..."
	@if ! command -v uv >/dev/null 2>&1; then \
		echo "uv is not installed. Please install it first:"; \
		echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"; \
		exit 1; \
	fi
	@make install-dev
	@make setup-hooks
	@echo "Development environment is ready."

install-dev: ## Install runtime and development dependencies
	@echo "Installing dependencies..."
	uv sync --extra dev

setup-hooks: ## Set up pre-commit hooks
	@echo "Installing pre-commit hooks..."
	uv run --extra dev pre-commit install

check: ## Run lock validation, lint, format check, and tests
	@echo "Checking lock file consistency with pyproject.toml"
	uv lock --locked
	@echo "Running Ruff lint checks"
	uv run --extra dev ruff check .
	@echo "Running Ruff format checks"
	uv run --extra dev ruff format . --check
	@echo "Running tests"
	uv run --extra dev pytest

format: ## Format code with Ruff
	@echo "Formatting code with Ruff"
	uv run --extra dev ruff format .

lint: ## Run Ruff linting and apply safe fixes
	@echo "Linting code with Ruff"
	uv run --extra dev ruff check . --fix

test: ## Run the test suite
	@echo "Running tests"
	uv run --extra dev pytest

run: ## Start the MCP server over stdio
	@echo "Starting football-manager-data-mcp"
	uv run football-manager-data-mcp

lock: ## Refresh the lockfile
	@echo "Refreshing uv.lock"
	uv lock
