from pathlib import Path

import pytest

from football_manager_data_mcp.catalog import FootballCatalog

_EXAMPLE_HTML = Path(__file__).resolve().parents[2] / "example_data" / "103.html"


@pytest.fixture
def catalog() -> FootballCatalog:
    return FootballCatalog(players_html_path=_EXAMPLE_HTML)


def test_catalog_loads_players_from_html(catalog: FootballCatalog) -> None:
    results = catalog.search_players(query="")

    assert results
    assert "Tck/90" in results[0]["metrics"]
    assert "Shot %" in results[0]["metrics"]
    assert "xG/90" in results[0]["metrics"]


def test_get_player_profile_returns_none_for_unknown_player(
    catalog: FootballCatalog,
) -> None:
    result = catalog.get_player_profile("missing-player")

    assert result is None


def test_get_club_squad_returns_matching_players(catalog: FootballCatalog) -> None:
    clubs = catalog.list_clubs(limit=1)
    club_id = str(clubs[0]["club_id"])
    club_name = str(clubs[0]["name"])
    squad = catalog.get_club_squad(club_id)

    assert squad
    assert all(player["club_name"] == club_name for player in squad)


def test_rank_players_by_preferences_uses_requested_metrics(
    catalog: FootballCatalog,
) -> None:
    ranked = catalog.rank_players_by_preferences(
        prompt="I value high xG per 90 and shot percent",
        limit=5,
    )

    assert ranked
    assert ranked[0]["score"] >= ranked[-1]["score"]
    assert set(ranked[0]["requested_metrics"]) >= {"xG/90", "Shot %"}


def test_rank_players_by_preferences_supports_wing_back_prompt(
    catalog: FootballCatalog,
) -> None:
    ranked = catalog.rank_players_by_preferences(
        prompt=(
            "find me a wing back with high crosses attempted per 90 "
            "and high progressive passes per 90"
        ),
        limit=10,
    )

    assert ranked
    assert all("wb" in ranked_player["player"]["position"].lower() for ranked_player in ranked)
    assert set(ranked[0]["requested_metrics"]) >= {"Crs A/90", "Pr passes/90"}


def test_role_prompt_false_nine_resolves_to_forward_positions(
    catalog: FootballCatalog,
) -> None:
    ranked = catalog.rank_players_by_preferences(
        prompt="find me a false nine with high goals per 90",
        limit=10,
    )

    assert ranked
    assert all(
        any(token in ranked_player["player"]["position"].lower() for token in ["st", "am (c)"])
        for ranked_player in ranked
    )


def test_role_prompt_mezzala_resolves_to_central_midfield_positions(
    catalog: FootballCatalog,
) -> None:
    ranked = catalog.rank_players_by_preferences(
        prompt="find me a mezzala with high progressive passes per 90",
        limit=10,
    )

    assert ranked
    assert all("m (c)" in ranked_player["player"]["position"].lower() for ranked_player in ranked)


def test_catalog_normalizes_name_and_pressing_headers(tmp_path: Path) -> None:
    html_path = tmp_path / "variant.html"
    html_path.write_text(
        """
        <html><body><table>
        <tr>
            <th>Name</th>
            <th>Club</th>
            <th>Pres C</th>
            <th>Mins</th>
            <th>Transfer Value</th>
        </tr>
        <tr>
            <td>Giovanni Di Lorenzo</td>
            <td>Napoli</td>
            <td>4.11</td>
            <td>1050</td>
            <td>45M € - 64M €</td>
        </tr>
        </table></body></html>
        """,
        encoding="utf-8",
    )

    variant_catalog = FootballCatalog(players_html_path=html_path)
    players = variant_catalog.search_players(query="Giovanni")

    assert players
    assert players[0]["name"] == "Giovanni Di Lorenzo"
    assert "Player" in players[0]["metrics"]
    assert "Pres C/90" in players[0]["metrics"]
