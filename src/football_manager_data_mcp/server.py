from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from football_manager_data_mcp.catalog import (
    FootballCatalog,
    _METRIC_DISPLAY_NAMES,
    _convert_player_dict_metrics,
)

catalog = FootballCatalog()
mcp = FastMCP("football-manager-data")


@mcp.tool()
def search_players(
    query: str = "",
    position: str | None = None,
    country: str | None = None,
    limit: int = 10,
) -> list[dict[str, object]]:
    results = catalog.search_players(query=query, position=position, country=country, limit=limit)
    return [_convert_player_dict_metrics(player) for player in results]


@mcp.tool()
def get_player_profile(player_id: str) -> dict[str, object] | None:
    player = catalog.get_player_profile(player_id=player_id)
    return _convert_player_dict_metrics(player) if player else None


@mcp.tool()
def list_clubs(country: str | None = None, limit: int = 20) -> list[dict[str, object]]:
    return catalog.list_clubs(country=country, limit=limit)


@mcp.tool()
def get_club_squad(club_id: str) -> list[dict[str, object]]:
    results = catalog.get_club_squad(club_id=club_id)
    return [_convert_player_dict_metrics(player) for player in results]


@mcp.tool()
def rank_players_by_preferences(
    prompt: str,
    position: str | None = None,
    country: str | None = None,
    limit: int = 10,
) -> list[dict[str, object]]:
    results = catalog.rank_players_by_preferences(
        prompt=prompt,
        position=position,
        country=country,
        limit=limit,
    )
    # Convert player metrics and matched_metrics
    for entry in results:
        entry["player"] = _convert_player_dict_metrics(entry["player"])
        if "matched_metrics" in entry:
            entry["matched_metrics"] = {
                _METRIC_DISPLAY_NAMES.get(name, name): value
                for name, value in entry["matched_metrics"].items()
            }
    return results


@mcp.tool()
def list_available_columns() -> list[dict[str, object]]:
    return catalog.list_available_columns()


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
