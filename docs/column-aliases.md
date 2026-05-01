# Column Aliases Guide

This document explains exactly where to update column aliases and metric phrase matching when Football Manager export headers change.

## Why aliases exist

FM HTML exports vary by view/version. The app normalizes these differences so ranking and filtering logic can rely on stable internal names.

There are two alias layers:

1. Raw header normalization (table parsing)
2. Natural-language metric phrase mapping (prompt -> metric header)

## 1) Raw header normalization

File: `src/football_manager_data_mcp/catalog.py`

Location:

- `_COLUMN_ALIASES` dictionary near the top of the file.

What it does:

- Converts incoming HTML table header labels into canonical column names before rows are built.

Current examples:

- `Name -> Player`
- `Pres C -> Pres C/90`

When to edit:

- FM export header changed spelling/format.
- You imported a different view that uses another label for an existing metric.

Example update:

```python
_COLUMN_ALIASES = {
    "Name": "Player",
    "Pres C": "Pres C/90",
    "xG per 90": "xG/90",
}
```

## 2) Natural-language metric alias mapping

File: `src/football_manager_data_mcp/catalog.py`

Location:

- `FootballCatalog._build_metric_aliases()`

What it does:

- Builds phrase aliases used to map free-text prompts to real numeric metric headers.
- Supports both generic normalization and manual football-specific phrases.

Examples already present:

- `"shot accuracy" -> "Shot %"`
- `"crosses per 90" -> "Crs A/90"`
- `"progressive passes" -> "Pr passes/90"`

When to edit:

- Users ask with a phrase that should map to a metric but does not.
- You add a new metric column and want prompt matching coverage.

Example update:

```python
if header == "xA/90":
    alias_set.update(
        {
            "expected assists per 90",
            "xa per 90",
            "expected assists",
            "xa",
        }
    )
```

## 3) Threshold parsing behavior

File: `src/football_manager_data_mcp/catalog.py`

Location:

- `FootballCatalog._extract_metric_thresholds()`

What it does:

- Parses constraints like:
  - `more than 5 assists`
  - `xg of 0.20`
  - `at least 80 pass percent`

Important implementation note:

- Alias matching uses regex word boundaries (`r"\b"`) and spacing-tolerant matching.
- If this is changed incorrectly, threshold filters can silently stop applying.

## 4) Required columns for uploaded files

File: `src/football_manager_data_mcp/ui.py`

Location:

- `_REQUIRED_COLUMNS` set.

What it does:

- Defines required headers that uploaded UI HTML files must contain.
- Enforced by `DataLifecycleService.validate_columns()` in `src/football_manager_data_mcp/data_lifecycle.py`.

When to edit:

- You intentionally changed supported metrics.
- You changed canonical column names in parser logic.

Warning:

- If you add aliases in `catalog.py` but do not align `_REQUIRED_COLUMNS`, uploads may be rejected unexpectedly.

## 5) FM view files that shape export headers

Files:

- `fm_views/General Metrics search.fmf`
- `fm_views/General Metrics scouted.fmf`
- package copies in `src/football_manager_data_mcp/fm_views/`

Why this matters:

- These views define which columns users export from FM.
- If you alter required columns, update these files and docs together.

## Safe change checklist

1. Add/adjust raw header alias in `_COLUMN_ALIASES` if header label changed.
2. Add prompt synonyms in `_build_metric_aliases` for user phrasing.
3. Ensure metric exists in exported data and is numeric where needed.
4. Align `_REQUIRED_COLUMNS` in `ui.py` if support contract changed.
5. Validate with tests:

```bash
make test
```

6. Add/adjust tests in:

- `src/test/test_catalog.py`
- `src/test/test_ui.py`

## Common symptom -> likely fix

- Prompt returns results but ignores threshold (`more than`, `at least`):
  - Check `_extract_metric_thresholds()` alias coverage and regex boundary behavior.
- Uploaded HTML rejected for missing columns:
  - Check `_REQUIRED_COLUMNS` and `_COLUMN_ALIASES` alignment.
- Metric never appears in ranking:
  - Verify it is parsed as numeric in `_parse_numeric()` and included in prompt aliases.
