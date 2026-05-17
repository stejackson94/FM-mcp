"""Routes for player search and ranking."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query

from football_manager_data_mcp._deps import get_catalog, get_explanation_settings
from football_manager_data_mcp.catalog import (
    _METRIC_DISPLAY_NAMES,
    FootballCatalog,
    _convert_player_dict_metrics,
)
from football_manager_data_mcp.explanations import ExplanationSettings, build_entry_explanation
from football_manager_data_mcp.positions import (
    augment_prompt_with_formation,
    constrain_position_terms_to_formation,
    entry_matches_position_terms,
    resolve_formation,
)

router = APIRouter()


@router.get("/api/search")
def api_search(
    catalog: Annotated[FootballCatalog, Depends(get_catalog)],
    query: str = Query(default=""),
    position: str | None = Query(default=None),
    country: str | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=200),
) -> list[dict[str, Any]]:
    results = catalog.search_players(query=query, position=position, country=country, limit=limit)
    # Convert metric names to display names before returning
    return [_convert_player_dict_metrics(player) for player in results]


@router.get("/api/rank")
def api_rank(
    catalog: Annotated[FootballCatalog, Depends(get_catalog)],
    explanation_settings: Annotated[ExplanationSettings, Depends(get_explanation_settings)],
    prompt: str = Query(default=""),
    formation: str | None = Query(default=None),
    position: str | None = Query(default=None),
    country: str | None = Query(default=None),
    min_minutes: float | None = Query(default=None, ge=0),
    limit: int = Query(default=10, ge=1, le=200),
) -> list[dict[str, Any]]:
    if not prompt.strip():
        raise HTTPException(status_code=400, detail="Query parameter 'prompt' is required.")

    _formation_key, resolved_formation = resolve_formation(formation)
    effective_prompt = augment_prompt_with_formation(
        prompt,
        str(resolved_formation["label"]) if resolved_formation else None,
    )

    resolved_position = (
        position.strip().lower() if position else catalog._infer_position(effective_prompt)
    )
    resolved_position = constrain_position_terms_to_formation(resolved_position, _formation_key)
    if formation and resolved_position is None:
        return []

    normalized_country = country.strip().lower() if country else None
    prefer_low = catalog._prefer_low(effective_prompt)

    ranked_pool = catalog.rank_players_by_preferences(
        prompt=effective_prompt,
        position=resolved_position,
        country=normalized_country,
        limit=max(len(catalog._players), 1),
    )

    if resolved_position:
        ranked_pool = [
            entry for entry in ranked_pool if entry_matches_position_terms(entry, resolved_position)
        ]

    ranked_pool = catalog.filter_ranked_players_by_prompt_thresholds(
        ranked_players=ranked_pool,
        prompt=effective_prompt,
    )

    if min_minutes is not None:
        filtered_pool: list[dict[str, Any]] = []
        for entry in ranked_pool:
            player = entry.get("player", {})
            numeric_metrics = player.get("numeric_metrics", {})
            minutes_value = numeric_metrics.get("Mins")
            if minutes_value is None:
                continue
            if float(minutes_value) >= float(min_minutes):
                filtered_pool.append(entry)
        ranked_pool = filtered_pool

    ranked_subset = ranked_pool[:limit]

    for entry in ranked_subset:
        entry["formation"] = formation

    for index, entry in enumerate(ranked_subset):
        entry["explanation"] = build_entry_explanation(
            entry=entry,
            rank_index=index,
            total_ranked=len(ranked_pool),
            ranked_pool=ranked_pool,
            prefer_low=prefer_low,
            prompt=effective_prompt,
            settings=explanation_settings,
        )

    # Convert metric names to display names for the API response
    for entry in ranked_subset:
        # Convert player metrics
        entry["player"] = _convert_player_dict_metrics(entry["player"])
        # Convert matched_metrics
        if "matched_metrics" in entry:
            entry["matched_metrics"] = {
                _METRIC_DISPLAY_NAMES.get(name, name): value
                for name, value in entry["matched_metrics"].items()
            }

    return ranked_subset
