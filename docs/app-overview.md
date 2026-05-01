# App Overview

This project is a Football Manager data query engine with two interfaces:

1. MCP server for Copilot/AI tool use
2. FastAPI browser UI

Both interfaces share the same catalog parsing and ranking core.

## Core purpose

- Load one or more FM HTML exports.
- Parse players and metrics.
- Normalize metric names and natural-language metric phrases.
- Rank/search/filter players.
- Return structured results and explanations.

## Main modules

- `src/football_manager_data_mcp/catalog.py`
  - Core parsing, metric normalization, search, ranking, threshold filtering.
- `src/football_manager_data_mcp/positions.py`
  - Role and formation capabilities, formation constraint helpers.
- `src/football_manager_data_mcp/explanations.py`
  - Deterministic explanation builder plus optional LLM rewrite layer.
- `src/football_manager_data_mcp/data_lifecycle.py`
  - Upload/default dataset switching, column validation, cleanup lifecycle.
- `src/football_manager_data_mcp/routes_*.py`
  - UI HTTP route handlers.
- `src/football_manager_data_mcp/server.py`
  - MCP tool endpoint definitions.
- `src/football_manager_data_mcp/ui.py`
  - FastAPI app composition and runtime configuration.
- `src/football_manager_data_mcp/frontend/*`
  - Browser UI static assets.

## End-to-end data flow

### A) Data ingestion

1. FM export HTML files are read from:
   - default: `input_data/*.html`
   - uploaded mode: `input_data/ui_uploads/*.html`
2. `FootballCatalog` reads table rows and headers.
3. Headers are canonicalized via `_COLUMN_ALIASES`.
4. Numeric values are parsed into `numeric_metrics`.
5. Player and club models are built.

### B) Query and ranking

1. User prompt enters via MCP tool or `/api/rank`.
2. Prompt metric terms are mapped to headers using `_build_metric_aliases`.
3. Position intent is inferred from role aliases.
4. Optional formation context constrains position terms.
5. Ranking score is computed by normalized per-metric min/max scaling.
6. Optional threshold filters (`more than`, `at least`, etc.) are applied.
7. Top N entries are returned.

### C) Explanation generation

1. Deterministic facts are built from rank context.
2. Deterministic text is generated as fallback.
3. If LLM is enabled and configured, explanation may be rewritten.
4. Response includes source marker (`rules`, `local llm`, `Groq`, etc.).

## Two runtime surfaces

## MCP mode

Entry point:

- Script: `football-manager-data-mcp`
- Module: `src/football_manager_data_mcp/server.py`

Exposed tools:

- `search_players`
- `get_player_profile`
- `list_clubs`
- `get_club_squad`
- `rank_players_by_preferences`
- `list_available_columns`

Behavior note:

- MCP server builds a catalog at process start from default input files.

## Browser UI mode

Entry point:

- Script: `football-manager-data-ui`
- Module: `src/football_manager_data_mcp/ui.py`

Key endpoints:

- `GET /api/rank`
- `GET /api/search`
- `GET /api/columns`
- `GET /api/clubs`
- `GET /api/player/{player_id}`
- `POST /api/upload`
- `POST /api/clear-data`
- `GET /api/data-status`
- `GET /api/download-required-views`

Behavior note:

- UI runtime uses `DataLifecycleService` to switch between default and uploaded datasets.

## Configuration model

Environment is loaded from `.env` by `ui.py`.

Main variables:

- `FM_ENABLE_LLM_EXPLANATIONS`
- `FM_LLM_MODEL`
- `FM_LLM_BASE_URL`
- `FM_LLM_API_KEY`
- `FM_AUTO_CLEAR_UPLOADS`
- `FM_AUTO_CLEAR_UPLOADS_INTERVAL_SECONDS`
- `FM_UI_HOST`
- `FM_UI_PORT`

## Operational boundaries

- Parsing/ranking is deterministic and local.
- LLM use is optional and only impacts explanation phrasing.
- Uploaded data is transient and can auto-clear on interval.

## Test coverage anchors

- `src/test/test_catalog.py`
  - parser behavior, alias normalization, ranking/filter behavior.
- `src/test/test_ui.py`
  - API/formations/explanation integration behavior.
