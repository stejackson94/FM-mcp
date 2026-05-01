# Operations and Maintenance

This document covers practical runbooks for operating, testing, and maintaining the service.

## Local developer workflow

1. Install dependencies and hooks:

```bash
make setup
```

2. Run checks:

```bash
make check
```

3. Run MCP server:

```bash
make run
```

4. Run browser UI:

```bash
make run-ui
```

## Data source modes

The UI supports two data modes managed by `DataLifecycleService`:

- `default`: reads from `input_data/*.html`
- `uploaded`: reads from `input_data/ui_uploads/*.html`

Status endpoint:

- `GET /api/data-status`

Switching behavior:

- Uploading a valid file activates `uploaded` mode.
- Clearing uploaded files reverts to `default` mode.

## Common runbooks

## Runbook: FM upload fails with missing columns

Symptoms:

- `POST /api/upload` returns 400 with missing columns list.

Actions:

1. Verify user exported with the required FM view files.
2. Check parser alias normalization in `catalog.py` (`_COLUMN_ALIASES`).
3. Confirm `ui.py` `_REQUIRED_COLUMNS` is aligned to canonical names.
4. Re-upload after fixing view or alias mapping.

## Runbook: Prompt does not map to expected metric

Symptoms:

- Ranking results do not reflect requested stat.

Actions:

1. Check phrase coverage in `FootballCatalog._build_metric_aliases()`.
2. Confirm target metric appears in `/api/columns` and is numeric.
3. Add alias phrases and tests.

## Runbook: Threshold phrase ignored

Symptoms:

- Query like `assist more than 5` returns unfiltered results.

Actions:

1. Inspect `_extract_metric_thresholds()` alias and comparator regex behavior.
2. Ensure regex word boundary behavior is intact.
3. Add a test in `src/test/test_catalog.py` for the exact phrase.

## Runbook: LLM explanations not used

Symptoms:

- Explanation source always reports `rules`.

Actions:

1. Check `.env` values:
   - `FM_ENABLE_LLM_EXPLANATIONS=true`
   - `FM_LLM_API_KEY` is set
   - `FM_LLM_BASE_URL` reachable
2. Validate provider/model values.
3. Confirm network reachability from runtime host.

## Release checklist

1. Run `make check`.
2. Verify both entry points:
   - `make run`
   - `make run-ui`
3. Validate upload flow and rank flow in UI.
4. Validate one MCP prompt in Copilot tools.
5. Confirm docs updates for changed aliases/formations/columns.

## Testing map

- Unit/integration tests:

```bash
make test
```

Primary files:

- `src/test/test_catalog.py`
- `src/test/test_ui.py`

Recommended when changing aliases or scoring:

- Add one positive phrase-match test.
- Add one threshold-filter test.
- Add one upload validation test (if required columns changed).

## Deployment notes

- Docker build/runtime is defined by `Dockerfile`.
- Infrastructure provisioning is in `terraform/`.
- Keep runtime env vars consistent between local and deployed environments.

## Maintenance cadence suggestion

- After each FM major update:
  - verify export headers against `_COLUMN_ALIASES`
  - verify required columns and FM view files
  - run full tests and a real upload/rank smoke test
