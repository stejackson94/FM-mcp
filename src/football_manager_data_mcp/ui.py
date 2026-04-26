from __future__ import annotations

from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from football_manager_data_mcp.catalog import FootballCatalog

app = FastAPI(title="Football Manager Data UI", version="0.1.0")
catalog = FootballCatalog()
frontend_dir = Path(__file__).resolve().parent / "frontend"

app.mount("/frontend", StaticFiles(directory=frontend_dir), name="frontend")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(frontend_dir / "index.html")


@app.get("/api/search")
def api_search(
    query: str = Query(default=""),
    position: str | None = Query(default=None),
    country: str | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=200),
) -> list[dict[str, Any]]:
    return catalog.search_players(query=query, position=position, country=country, limit=limit)


@app.get("/api/rank")
def api_rank(
    prompt: str = Query(default=""),
    position: str | None = Query(default=None),
    country: str | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=200),
) -> list[dict[str, Any]]:
    if not prompt.strip():
        raise HTTPException(status_code=400, detail="Query parameter 'prompt' is required.")
    return catalog.rank_players_by_preferences(
        prompt=prompt,
        position=position,
        country=country,
        limit=limit,
    )


@app.get("/api/columns")
def api_columns() -> list[dict[str, Any]]:
    return catalog.list_available_columns()


@app.get("/api/clubs")
def api_clubs(
    country: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=500),
) -> list[dict[str, Any]]:
    return catalog.list_clubs(country=country, limit=limit)


@app.get("/api/player/{player_id}")
def api_player(player_id: str) -> dict[str, Any]:
    player = catalog.get_player_profile(player_id)
    if player is None:
        raise HTTPException(status_code=404, detail="Player not found.")
    return player


def main() -> None:
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
