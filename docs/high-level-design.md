# High-Level Design

## Summary

The system is designed around one shared domain core (`FootballCatalog`) with two adapters:

1. MCP adapter for AI tool invocation
2. HTTP/UI adapter for browser-based workflows

This keeps ranking logic consistent across interfaces while allowing different interaction models.

## Architecture goals

- Single source of truth for parsing and ranking.
- Stable canonical metric names despite FM export header variance.
- Human-friendly natural-language prompt support.
- Optional LLM enrichment without making core ranking depend on external APIs.
- Lightweight deployability (local, Docker, EC2).

## Component model

### 1) Domain layer

- `catalog.py`
- `positions.py`
- `explanations.py`

Responsibilities:

- Parse, normalize, rank, filter, infer positions, build explanations.

### 2) Application/service layer

- `data_lifecycle.py`
- `_deps.py`

Responsibilities:

- Select active dataset, validate uploads, manage lifecycle state, inject dependencies.

### 3) Delivery layer

- MCP: `server.py`
- HTTP API: `ui.py` + `routes_*.py`
- Frontend: `frontend/index.html`, `frontend/app.js`, `frontend/styles.css`

Responsibilities:

- Transport concerns, request/response handling, rendering.

### 4) Infrastructure layer

- Container: `Dockerfile`
- IaC: `terraform/`
- CI/CD: `.github/workflows/` (deployment pipeline)

Responsibilities:

- Build, deploy, and runtime hosting.

## Logical data model

- `Player`
  - static identity and text fields (`name`, `club_name`, `position`, etc.)
  - `metrics` (raw string values)
  - `numeric_metrics` (parsed floats)
- `Club`
  - normalized club identity for squad lookup
- `MetricThreshold`
  - parsed comparator + numeric value constraints from free text

## Sequence flows

## Ranking request sequence

1. Prompt arrives (MCP or `/api/rank`).
2. Optional formation is resolved.
3. Prompt is optionally augmented with formation context.
4. Position terms are inferred/filtered by formation.
5. Metric aliases resolve prompt language to canonical headers.
6. Rank score computed from normalized metric values.
7. Prompt thresholds applied to ranked entries.
8. Explanations generated (rules, then optional LLM rewrite).
9. Top N returned.

## Upload sequence

1. Client posts `.html` to `/api/upload`.
2. Existing uploaded files are replaced.
3. New temporary catalog is built from uploaded file.
4. Required columns are validated.
5. On success, service switches active catalog to uploaded mode.
6. On failure, uploaded file is removed and validation error returned.

## Key design decisions

- Canonical metric names are enforced at parse time.
- Prompt understanding uses explicit alias dictionaries, not embeddings.
- Ranking uses simple min/max normalized scoring for transparency.
- Threshold parsing uses deterministic regex patterns.
- Explanation generation is deterministic-first with optional LLM enhancement.

## Trade-offs

- Pros:
  - easy to reason about and test
  - deterministic ranking behavior
  - low operational complexity
- Cons:
  - manual alias maintenance as schemas evolve
  - min/max scaling can be sensitive to outliers
  - static role alias dictionaries require periodic tuning

## Extensibility points

- Add new metric phrase aliases in `catalog.py`.
- Add new formations and lanes in `positions.py`.
- Add new API endpoints via `routes_*.py` and include router in `ui.py`.
- Add ranking strategies by extending `_rank_player` behavior.
- Replace/add explanation providers behind `build_entry_explanation`.

## Non-functional considerations

- Reliability:
  - deterministic fallback when LLM unavailable
  - upload validation prevents malformed datasets from becoming active
- Security:
  - API currently has no auth; deploy behind trusted network or add auth layer
- Performance:
  - in-memory processing is efficient for typical FM export sizes
  - ranking recomputes per request; acceptable for current scale
