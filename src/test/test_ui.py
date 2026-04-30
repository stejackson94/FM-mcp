from __future__ import annotations

import io
import zipfile
from typing import Any

from fastapi.testclient import TestClient

from football_manager_data_mcp.ui import (
    _augment_prompt_with_formation,
    _build_explanation_facts,
    _constrain_position_terms_to_formation,
    _deterministic_explanation,
    _entry_matches_position_terms,
    _formation_advice,
    app,
)


def test_player_explanation_uses_player_specific_context() -> None:
    ranked_pool = [
        {
            "score": 0.81,
            "matched_metrics": {"xG/90": 0.52, "Shot %": 48.0, "Drb/90": 2.1},
            "requested_metrics": ["xG/90", "Shot %", "Drb/90"],
            "player": {
                "name": "Alex Finley",
                "club_name": "Hibernian",
                "nationality": "Scotland",
                "position": "AM (RLC), ST (C)",
                "transfer_value": "£4.2M",
                "wage": "£12K p/w",
                "rec": "A",
                "potential": "A-",
                "numeric_metrics": {"Mins": 1432.0},
            },
        },
        {
            "score": 0.63,
            "matched_metrics": {"xG/90": 0.31, "Shot %": 39.0, "Drb/90": 1.2},
            "requested_metrics": ["xG/90", "Shot %", "Drb/90"],
            "player": {
                "name": "Ben Morris",
                "club_name": "Aberdeen",
                "nationality": "Wales",
                "position": "ST (C)",
                "transfer_value": "£2.1M",
                "wage": "£8K p/w",
                "rec": "B",
                "potential": "B+",
                "numeric_metrics": {"Mins": 1180.0},
            },
        },
    ]

    facts = _build_explanation_facts(
        entry=ranked_pool[0],
        rank_index=0,
        total_ranked=len(ranked_pool),
        ranked_pool=ranked_pool,
        prefer_low=False,
        prompt="Need a direct forward who can finish and beat people off the dribble",
    )

    explanation = _deterministic_explanation(facts)

    assert facts["minutes"] == "1432"
    assert facts["transfer_value"] == "£4.2M"
    assert explanation["why_fit"].startswith(
        "Alex Finley is the strongest match in this result set for "
        "'Need a direct forward who can finish and beat people off the dribble'."
    )
    assert (
        "- Profile: Scotland at Hibernian, AM (RLC), ST (C), 1432 minutes, value £4.2M."
        in explanation["why_fit"]
    )
    assert (
        "- Evidence: xG/90 (0.52, 100th percentile) and Shot % (48.0, 100th percentile)"
        in explanation["why_fit"]
    )
    assert "Key metrics" not in explanation["why_fit"]
    assert "- Market snapshot: Rec A; Potential A-; Wage £12K p/w." in explanation["why_fit"]
    assert "Check:" not in explanation["caveat"]
    assert explanation["caveat"].startswith("- Risk: profile drops off most on ")
    assert explanation["tactical_use"].startswith(
        "- Usage: deploy as AM (RLC), ST (C) in a setup that leans on xG/90"
    )
    assert "Coaching note" not in explanation["tactical_use"]


def test_player_explanation_omits_unknown_club_context() -> None:
    ranked_pool = [
        {
            "score": 0.58,
            "matched_metrics": {"Tck/90": 3.2, "Int/90": 2.4},
            "requested_metrics": ["Tck/90", "Int/90"],
            "player": {
                "name": "Milan Costa",
                "club_name": "",
                "nationality": "Portugal",
                "position": "WB (R)",
                "numeric_metrics": {"Mins": 980.0},
            },
        }
    ]

    facts = _build_explanation_facts(
        entry=ranked_pool[0],
        rank_index=0,
        total_ranked=1,
        ranked_pool=ranked_pool,
        prefer_low=False,
        prompt="Need an aggressive right wing-back who wins the ball back",
    )

    explanation = _deterministic_explanation(facts)

    assert facts["club_name"] == ""
    assert "Unknown" not in explanation["why_fit"]
    assert "- Profile: Portugal, WB (R), 980 minutes." in explanation["why_fit"]


def test_formation_advice_matches_player_position() -> None:
    advice = _formation_advice("WB (R)", "3-5-2")

    assert advice is not None
    assert advice["formation_label"] == "3-5-2"
    assert advice["slot_code"] == "WBR"
    assert advice["slot_label"] == "Right wing-back"


def test_player_explanation_uses_formation_slot_when_available() -> None:
    ranked_pool = [
        {
            "score": 0.71,
            "matched_metrics": {"Crs A/90": 4.8, "Pr passes/90": 7.4},
            "requested_metrics": ["Crs A/90", "Pr passes/90"],
            "formation": "3-5-2",
            "player": {
                "name": "Rico Vale",
                "club_name": "Braga",
                "nationality": "Portugal",
                "position": "WB (R), RM",
                "numeric_metrics": {"Mins": 1640.0},
            },
        }
    ]

    facts = _build_explanation_facts(
        entry=ranked_pool[0],
        rank_index=0,
        total_ranked=1,
        ranked_pool=ranked_pool,
        prefer_low=False,
        prompt="Need an aggressive right-sided carrier and crosser",
    )

    explanation = _deterministic_explanation(facts)

    assert facts["formation"] == "3-5-2"
    assert facts["formation_advice"] is not None
    assert "in 3-5-2, use him as the Right wing-back (WBR)" in explanation["tactical_use"]


def test_augment_prompt_with_formation_appends_context() -> None:
    prompt = _augment_prompt_with_formation(
        "Need a goalkeeper who can start attacks",
        "4-2-3-1 Wide",
    )

    assert prompt == "Need a goalkeeper who can start attacks. Formation context: 4-2-3-1 Wide."


def test_constrain_position_terms_to_formation_for_433_wingers() -> None:
    constrained = _constrain_position_terms_to_formation(
        "am (l)|am (r)|m (l)|m (r)",
        "4-3-3-dm-wide",
    )

    assert constrained == "am (l)|am (r)"


def test_constrain_position_terms_to_formation_for_all_lane_types() -> None:
    constrained_back_four = _constrain_position_terms_to_formation(
        "d (l)|d (r)|wb|dm",
        "4-4-2",
    )
    constrained_diamond_mid = _constrain_position_terms_to_formation(
        "dm|m (c)|am (c)|m (r)",
        "4-4-2-diamond-narrow",
    )
    constrained_back_five = _constrain_position_terms_to_formation(
        "wb (l)|wb (r)|m (l)|am (r)",
        "5-2-3-wb",
    )
    constrained_front_three = _constrain_position_terms_to_formation(
        "st|am (r)|am (l)|m (r)",
        "3-4-3-dm-wide",
    )

    assert constrained_back_four == "d (l)|d (r)"
    assert constrained_diamond_mid == "dm|m (c)|am (c)"
    assert constrained_back_five == "wb (l)|wb (r)|am (r)"
    assert constrained_front_three == "st|am (r)|am (l)"


def test_entry_position_matching_handles_grouped_sides() -> None:
    entry = {
        "player": {
            "position": "AM (RLC), ST (C)",
        }
    }

    assert _entry_matches_position_terms(entry, "am (r)|am (l)")
    assert _entry_matches_position_terms(entry, "am (c)")
    assert _entry_matches_position_terms(entry, "st")
    assert not _entry_matches_position_terms(entry, "m (r)")
    assert not _entry_matches_position_terms(entry, "wb")


def test_api_rank_appends_selected_formation_to_prompt(monkeypatch: Any) -> None:
    captured: dict[str, Any] = {}

    class StubCatalog:
        _players = [object()]

        def _infer_position(self, prompt: str) -> str | None:
            captured["infer_prompt"] = prompt
            return "wb"

        def _prefer_low(self, prompt: str) -> bool:
            captured["prefer_low_prompt"] = prompt
            return False

        def rank_players_by_preferences(
            self,
            prompt: str,
            position: str | None = None,
            country: str | None = None,
            limit: int = 10,
        ) -> list[dict[str, Any]]:
            captured["rank_prompt"] = prompt
            captured["rank_position"] = position
            return [
                {
                    "score": 0.66,
                    "matched_metrics": {"Crs A/90": 4.1, "Pr passes/90": 6.8},
                    "requested_metrics": ["Crs A/90", "Pr passes/90"],
                    "player": {
                        "name": "Leo Hart",
                        "club_name": "Hearts",
                        "nationality": "Scotland",
                        "position": "WB (R)",
                        "numeric_metrics": {"Mins": 1200.0},
                    },
                }
            ]

    monkeypatch.setattr(app.state.data_lifecycle, "catalog", StubCatalog())
    client = TestClient(app)

    response = client.get(
        "/api/rank",
        params={
            "prompt": "Need a right-sided runner with crossing output",
            "formation": "3-5-2",
            "limit": 1,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert captured["rank_prompt"] == (
        "Need a right-sided runner with crossing output. Formation context: 3-5-2."
    )
    assert captured["infer_prompt"] == captured["rank_prompt"]
    assert captured["rank_position"] == "wb"
    assert "Right wing-back (WBR)" in payload[0]["explanation"]["tactical_use"]


def test_api_rank_uses_formation_specific_wide_lanes(monkeypatch: Any) -> None:
    captured: dict[str, Any] = {}

    class StubCatalog:
        _players = [object(), object()]

        def _infer_position(self, prompt: str) -> str | None:
            captured["infer_prompt"] = prompt
            return "am (l)|am (r)|m (l)|m (r)"

        def _prefer_low(self, prompt: str) -> bool:
            return False

        def rank_players_by_preferences(
            self,
            prompt: str,
            position: str | None = None,
            country: str | None = None,
            limit: int = 10,
        ) -> list[dict[str, Any]]:
            captured["rank_position"] = position
            return [
                {
                    "score": 0.68,
                    "matched_metrics": {"Crs A/90": 4.2},
                    "requested_metrics": ["Crs A/90"],
                    "player": {
                        "name": "Byron Pendleton",
                        "club_name": "North End",
                        "nationality": "England",
                        "position": "M (R)",
                        "numeric_metrics": {"Mins": 1500.0},
                    },
                },
                {
                    "score": 0.66,
                    "matched_metrics": {"Crs A/90": 4.0},
                    "requested_metrics": ["Crs A/90"],
                    "player": {
                        "name": "Alex Wide",
                        "club_name": "North End",
                        "nationality": "England",
                        "position": "AM (R)",
                        "numeric_metrics": {"Mins": 1500.0},
                    },
                },
            ]

    monkeypatch.setattr(app.state.data_lifecycle, "catalog", StubCatalog())
    client = TestClient(app)

    response = client.get(
        "/api/rank",
        params={
            "prompt": "Need wingers with crossing output",
            "formation": "4-3-3-dm-wide",
            "limit": 10,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert captured["rank_position"] == "am (l)|am (r)"
    assert [row["player"]["name"] for row in payload] == ["Alex Wide"]


def test_download_required_views_returns_zip_archive() -> None:
    client = TestClient(app)

    response = client.get("/api/download-required-views")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    assert response.headers["content-disposition"] == 'attachment; filename="fm-required-views.zip"'

    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        assert sorted(archive.namelist()) == [
            "General Metrics scouted.fmf",
            "General Metrics search.fmf",
        ]
