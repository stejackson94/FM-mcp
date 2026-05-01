from pathlib import Path

import pytest

from football_manager_data_mcp.catalog import FootballCatalog, _position_capabilities

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
        bool(_position_capabilities(str(ranked_player["player"]["position"])) & {"ST", "AMC"})
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
    assert all(
        "MC" in _position_capabilities(str(ranked_player["player"]["position"]))
        for ranked_player in ranked
    )


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


def test_match_position_handles_multi_role_grouped_sides(tmp_path: Path) -> None:
    html_path = tmp_path / "positions.html"
    html_path.write_text(
        """
        <html><body><table>
        <tr>
            <th>Player</th>
            <th>Club</th>
            <th>Position</th>
            <th>Mins</th>
            <th>xG/90</th>
            <th>Pas %</th>
            <th>Transfer Value</th>
        </tr>
        <tr>
            <td>David Wide</td>
            <td>Sample FC</td>
            <td>AM (RLC), ST (C)</td>
            <td>1200</td>
            <td>0.30</td>
            <td>82</td>
            <td>£4.0M</td>
        </tr>
        <tr>
            <td>Byron Mid</td>
            <td>Sample FC</td>
            <td>M (R)</td>
            <td>1200</td>
            <td>0.25</td>
            <td>79</td>
            <td>£2.0M</td>
        </tr>
        </table></body></html>
        """,
        encoding="utf-8",
    )

    position_catalog = FootballCatalog(players_html_path=html_path)
    results = position_catalog.search_players(query="", position="am (l)|am (r)", limit=10)

    assert [player["name"] for player in results] == ["David Wide"]


def test_filter_ranked_players_by_prompt_thresholds_assists_more_than(tmp_path: Path) -> None:
    html_path = tmp_path / "threshold_assists.html"
    html_path.write_text(
        """
        <html><body><table>
        <tr>
            <th>Player</th>
            <th>Club</th>
            <th>Position</th>
            <th>Nat</th>
            <th>Mins</th>
            <th>Ast</th>
            <th>xG/90</th>
            <th>Transfer Value</th>
        </tr>
        <tr>
            <td>Adam Creator</td>
            <td>Sample FC</td>
            <td>ST (C)</td>
            <td>England</td>
            <td>1500</td>
            <td>6</td>
            <td>0.22</td>
            <td>£5.0M</td>
        </tr>
        <tr>
            <td>Ben Support</td>
            <td>Sample FC</td>
            <td>ST (C)</td>
            <td>England</td>
            <td>1500</td>
            <td>4</td>
            <td>0.24</td>
            <td>£4.0M</td>
        </tr>
        </table></body></html>
        """,
        encoding="utf-8",
    )

    threshold_catalog = FootballCatalog(players_html_path=html_path)
    ranked = threshold_catalog.rank_players_by_preferences(prompt="high assists", limit=10)

    filtered = threshold_catalog.filter_ranked_players_by_prompt_thresholds(
        ranked,
        "i want players who assist more than 5 goals",
    )

    assert [entry["player"]["name"] for entry in filtered] == ["Adam Creator"]


def test_filter_ranked_players_by_prompt_thresholds_xg_of_value(tmp_path: Path) -> None:
    html_path = tmp_path / "threshold_xg.html"
    html_path.write_text(
        """
        <html><body><table>
        <tr>
            <th>Player</th>
            <th>Club</th>
            <th>Position</th>
            <th>Nat</th>
            <th>Mins</th>
            <th>Ast</th>
            <th>xG/90</th>
            <th>Transfer Value</th>
        </tr>
        <tr>
            <td>Chris Finisher</td>
            <td>Sample FC</td>
            <td>ST (C)</td>
            <td>Spain</td>
            <td>1400</td>
            <td>3</td>
            <td>0.20</td>
            <td>£7.0M</td>
        </tr>
        <tr>
            <td>Danny Runner</td>
            <td>Sample FC</td>
            <td>ST (C)</td>
            <td>Spain</td>
            <td>1400</td>
            <td>2</td>
            <td>0.18</td>
            <td>£3.0M</td>
        </tr>
        </table></body></html>
        """,
        encoding="utf-8",
    )

    threshold_catalog = FootballCatalog(players_html_path=html_path)
    ranked = threshold_catalog.rank_players_by_preferences(
        prompt="find strikers with high xg",
        limit=10,
    )

    filtered = threshold_catalog.filter_ranked_players_by_prompt_thresholds(
        ranked,
        "i want strikers with xg of 0.20",
    )

    assert [entry["player"]["name"] for entry in filtered] == ["Chris Finisher"]


def test_rank_players_prompt_players_word_does_not_match_name_column(
    catalog: FootballCatalog,
) -> None:
    ranked = catalog.rank_players_by_preferences(
        prompt="i want players who assist more than 2",
        limit=20,
    )

    assert ranked
    assert "Ast" in ranked[0]["requested_metrics"]
    assert "Player" not in ranked[0]["requested_metrics"]
