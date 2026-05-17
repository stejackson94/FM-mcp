"""Routes for catalog queries: columns, clubs, player profiles."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query

from football_manager_data_mcp._deps import get_catalog
from football_manager_data_mcp.catalog import (
    _convert_player_dict_metrics,
    FootballCatalog,
)

router = APIRouter()


@router.get("/api/columns")
def api_columns(
    catalog: Annotated[FootballCatalog, Depends(get_catalog)],
) -> list[dict[str, Any]]:
    return catalog.list_available_columns()


@router.get("/api/clubs")
def api_clubs(
    catalog: Annotated[FootballCatalog, Depends(get_catalog)],
    country: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=500),
) -> list[dict[str, Any]]:
    return catalog.list_clubs(country=country, limit=limit)


@router.get("/api/player/{player_id}")
def api_player(
    player_id: str,
    catalog: Annotated[FootballCatalog, Depends(get_catalog)],
) -> dict[str, Any]:
    player = catalog.get_player_profile(player_id)
    if player is None:
        raise HTTPException(status_code=404, detail="Player not found.")
    return _convert_player_dict_metrics(player)
