from football_manager_data_mcp.ui import _build_explanation_facts, _deterministic_explanation


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
        "Alex Finley: Best fit in this result set for "
        "'Need a direct forward who can finish and beat people off the dribble'."
    )
    assert (
        "- Player context: Scotland at Hibernian, AM (RLC), ST (C), 1432 minutes, value £4.2M."
        in explanation["why_fit"]
    )
    assert "- Market snapshot: Rec A; Potential A-; Wage £12K p/w." in explanation["why_fit"]
    assert "Check:" not in explanation["caveat"]
    assert explanation["caveat"].startswith("- Risk: profile drops off most on ")
    assert "Alex Finley's output at Hibernian" in explanation["tactical_use"]
