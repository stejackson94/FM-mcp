setup: ## Set up development environment
	@echo "Setting up development environment with uv..."
	@if ! command -v uv >/dev/null 2>&1; then \
		echo "uv is not installed. Please install it first:"; \
		echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"; \
		exit 1; \
	fi
	@make environment
	@make install-dev
	@make setup-hooks
	@echo "Development environment is ready."

environment: ## Create local .env file from .env.example if missing
	@if [ -f .env ]; then \
		echo ".env already exists. Skipping."; \
	else \
		cp .env.example .env; \
		echo "Created .env from .env.example"; \
		echo "Set FM_LLM_API_KEY in .env before running LLM explanations."; \
	fi

local-llm: ## Configure .env for local LLM via Ollama
	@make environment
	@if ! command -v ollama >/dev/null 2>&1; then \
		echo "Ollama is not installed. Install it from https://ollama.com"; \
		exit 1; \
	fi
	@if ! ollama list | awk 'NR>1 {print $$1}' | grep -qx 'qwen2.5:7b-instruct'; then \
		echo "Pulling local model qwen2.5:7b-instruct..."; \
		ollama pull qwen2.5:7b-instruct; \
	fi
	@grep -q '^FM_ENABLE_LLM_EXPLANATIONS=' .env \
		&& sed -i 's|^FM_ENABLE_LLM_EXPLANATIONS=.*|FM_ENABLE_LLM_EXPLANATIONS=true|' .env \
		|| echo 'FM_ENABLE_LLM_EXPLANATIONS=true' >> .env
	@grep -q '^FM_LLM_MODEL=' .env \
		&& sed -i 's|^FM_LLM_MODEL=.*|FM_LLM_MODEL=qwen2.5:7b-instruct|' .env \
		|| echo 'FM_LLM_MODEL=qwen2.5:7b-instruct' >> .env
	@grep -q '^FM_LLM_BASE_URL=' .env \
		&& sed -i 's|^FM_LLM_BASE_URL=.*|FM_LLM_BASE_URL=http://127.0.0.1:11434/v1|' .env \
		|| echo 'FM_LLM_BASE_URL=http://127.0.0.1:11434/v1' >> .env
	@grep -q '^FM_LLM_API_KEY=' .env \
		&& sed -i 's|^FM_LLM_API_KEY=.*|FM_LLM_API_KEY=local-dev|' .env \
		|| echo 'FM_LLM_API_KEY=local-dev' >> .env
	@echo "Local LLM defaults written to .env"
	@echo "Start Ollama (if needed), then run: make run-ui"

install-dev: ## Install runtime and development dependencies
	@echo "Installing dependencies..."
	uv sync --extra dev

setup-hooks: ## Set up pre-commit hooks
	@echo "Installing pre-commit hooks (pre-commit + commit-msg)..."
	@-git config --unset-all core.hooksPath
	@uv run --extra dev pre-commit install --hook-type pre-commit --hook-type commit-msg
	@echo "Installed pre-commit-managed hooks for code quality and commit messages"

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

run-ui: ## Start the browser UI server
	@echo "Starting football-manager-data-ui on http://127.0.0.1:8000"
	@set -a; \
	if [ -f .env ]; then . ./.env; fi; \
	set +a; \
	uv run football-manager-data-ui

stop-local: ## Stop local UI server and Ollama daemon
	@echo "Stopping local UI server processes..."
	@if pgrep -f 'football-manager-data-ui|football_manager_data_mcp.ui:app|uvicorn.*127.0.0.1:8000' >/dev/null 2>&1; then \
		pkill -f 'football-manager-data-ui|football_manager_data_mcp.ui:app|uvicorn.*127.0.0.1:8000'; \
		echo "UI server stopped."; \
	else \
		echo "No matching UI server process found."; \
	fi
	@echo "Stopping Ollama daemon..."
	@if pgrep -x ollama >/dev/null 2>&1; then \
		pkill -x ollama; \
		echo "Ollama stopped."; \
	else \
		echo "No Ollama process found."; \
	fi

lock: ## Refresh the lockfile
	@echo "Refreshing uv.lock"
	uv lock
