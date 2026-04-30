from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from football_manager_data_mcp.data_lifecycle import DataLifecycleService
from football_manager_data_mcp.explanations import (
    ExplanationSettings,
    build_explanation_facts,
    clean_player_text,
    deterministic_explanation,
    format_fact_value,
    llm_rewrite_explanation,
    llm_source_name,
    percentile_for_value,
)
from football_manager_data_mcp.positions import (
    FORMATION_PRESETS as _SHARED_FORMATION_PRESETS,
)
from football_manager_data_mcp.positions import (
    augment_prompt_with_formation as _shared_augment_prompt_with_formation,
)
from football_manager_data_mcp.positions import (
    constrain_position_terms_to_formation as _shared_constrain_position_terms_to_formation,
)
from football_manager_data_mcp.positions import (
    entry_matches_position_terms as _shared_entry_matches_position_terms,
)
from football_manager_data_mcp.positions import (
    formation_advice as _shared_formation_advice,
)
from football_manager_data_mcp.positions import (
    resolve_formation as _shared_resolve_formation,
)
from football_manager_data_mcp.routes_catalog import router as catalog_router
from football_manager_data_mcp.routes_data import router as data_router
from football_manager_data_mcp.routes_rank import router as rank_router


@asynccontextmanager
async def _lifespan(application: FastAPI):  # noqa: ARG001
    data_lifecycle.start_background_tasks()
    yield
    data_lifecycle.stop_background_tasks()


app = FastAPI(title="Make FM Scouting Data Again", version="0.1.0", lifespan=_lifespan)
logger = logging.getLogger(__name__)

_frontend_dir = Path(__file__).resolve().parent / "frontend"
_input_data_dir = Path(__file__).resolve().parents[2] / "input_data"
_project_root_dir = Path(__file__).resolve().parents[2]
_uploaded_data_dir = _input_data_dir / "ui_uploads"

# Auto-load local .env so runtime config works without sourcing shell vars.
load_dotenv(_project_root_dir / ".env")

_REQUIRED_COLUMNS = {
    "Player",
    "Club",
    "Mins",
    "Gls",
    "Ast",
    "Tck/90",
    "Tck R",
    "Hdrs W/90",
    "Hdr %",
    "Int/90",
    "Poss Won/90",
    "Poss Lost/90",
    "Pres C/90",
    "Pres A/90",
    "Pas %",
    "Pr passes/90",
    "Crs A/90",
    "Cr C/A",
    "K Ps/90",
    "OP-KP/90",
    "xA/90",
    "Drb/90",
    "Shot/90",
    "Shot %",
    "xG/90",
    "Gls/90",
    "Transfer Value",
}

FORMATION_PRESETS = _SHARED_FORMATION_PRESETS

LLM_ENABLED_BY_DEFAULT = os.getenv("FM_ENABLE_LLM_EXPLANATIONS", "true").lower() in {
    "1",
    "true",
    "yes",
    "on",
}
LLM_MODEL = os.getenv("FM_LLM_MODEL", "qwen2.5:7b-instruct")
# Prefer neutral Local LLM vars while keeping legacy OPENAI_* compatibility.
LLM_API_KEY = os.getenv("FM_LLM_API_KEY", os.getenv("OPENAI_API_KEY", ""))
LLM_BASE_URL = os.getenv(
    "FM_LLM_BASE_URL", os.getenv("OPENAI_BASE_URL", "http://127.0.0.1:11434/v1")
)
EXPLANATION_SETTINGS = ExplanationSettings(
    llm_enabled=LLM_ENABLED_BY_DEFAULT,
    llm_model=LLM_MODEL,
    llm_api_key=LLM_API_KEY,
    llm_base_url=LLM_BASE_URL,
)

AUTO_CLEAR_UPLOADS = os.getenv("FM_AUTO_CLEAR_UPLOADS", "true").lower() in {
    "1",
    "true",
    "yes",
    "on",
}
AUTO_CLEAR_UPLOADS_INTERVAL_SECONDS = int(
    os.getenv("FM_AUTO_CLEAR_UPLOADS_INTERVAL_SECONDS", "3600")
)

data_lifecycle = DataLifecycleService(
    input_data_dir=_input_data_dir,
    uploaded_data_dir=_uploaded_data_dir,
    required_columns=_REQUIRED_COLUMNS,
    auto_clear_uploads=AUTO_CLEAR_UPLOADS,
    auto_clear_uploads_interval_seconds=AUTO_CLEAR_UPLOADS_INTERVAL_SECONDS,
    logger=logger,
)

# Backward-compatible alias – tests may read ui_module.catalog.
catalog = data_lifecycle.catalog

# Expose shared state on app.state so route modules can access it via Depends.
app.state.data_lifecycle = data_lifecycle
app.state.explanation_settings = EXPLANATION_SETTINGS

app.mount("/frontend", StaticFiles(directory=_frontend_dir), name="frontend")
app.include_router(data_router)
app.include_router(rank_router)
app.include_router(catalog_router)


# ---------------------------------------------------------------------------
# Backward-compatible wrappers (imported by tests and external callers)
# ---------------------------------------------------------------------------


def _llm_source_name() -> str:
    return llm_source_name(EXPLANATION_SETTINGS)


def _percentile_for_value(values: list[float], value: float, prefer_low: bool) -> int:
    return percentile_for_value(values, value, prefer_low)


def _clean_player_text(value: Any, fallback: str = "") -> str:
    return clean_player_text(value, fallback)


def _format_fact_value(value: Any) -> str | None:
    return format_fact_value(value)


def _resolve_formation(formation: str | None) -> tuple[str | None, dict[str, Any] | None]:
    return _shared_resolve_formation(formation)


def _augment_prompt_with_formation(prompt: str, formation_label: str | None) -> str:
    return _shared_augment_prompt_with_formation(prompt, formation_label)


def _constrain_position_terms_to_formation(
    position: str | None, formation_key: str | None
) -> str | None:
    return _shared_constrain_position_terms_to_formation(position, formation_key)


def _entry_matches_position_terms(entry: dict[str, Any], position_terms: str | None) -> bool:
    return _shared_entry_matches_position_terms(entry, position_terms)


def _formation_advice(position_text: str, formation_key: str | None) -> dict[str, str] | None:
    return _shared_formation_advice(position_text, formation_key)


def _build_explanation_facts(
    entry: dict[str, Any],
    rank_index: int,
    total_ranked: int,
    ranked_pool: list[dict[str, Any]],
    prefer_low: bool,
    prompt: str,
) -> dict[str, Any]:
    return build_explanation_facts(
        entry=entry,
        rank_index=rank_index,
        total_ranked=total_ranked,
        ranked_pool=ranked_pool,
        prefer_low=prefer_low,
        prompt=prompt,
    )


def _deterministic_explanation(facts: dict[str, Any]) -> dict[str, str]:
    return deterministic_explanation(facts)


def _llm_rewrite_explanation(
    facts: dict[str, Any], fallback: dict[str, str]
) -> dict[str, str] | None:
    return llm_rewrite_explanation(facts, fallback, EXPLANATION_SETTINGS)


def main() -> None:
    host = os.getenv("FM_UI_HOST", "0.0.0.0")
    try:
        port = int(os.getenv("FM_UI_PORT", "8000"))
    except ValueError:
        port = 8000
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
