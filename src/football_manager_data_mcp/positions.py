from __future__ import annotations

from typing import Any

FORMATION_PRESETS: dict[str, dict[str, Any]] = {
    "4-3-3-dm-wide": {
        "label": "4-3-3 DM Wide",
        "lanes": [
            ("GK", "Goalkeeper"),
            ("DR", "Right back"),
            ("DCR", "Right centre-back"),
            ("DCL", "Left centre-back"),
            ("DL", "Left back"),
            ("DM", "Holding midfielder"),
            ("MCR", "Right central midfielder"),
            ("MCL", "Left central midfielder"),
            ("AMR", "Right winger"),
            ("ST", "Striker"),
            ("AML", "Left winger"),
        ],
    },
    "4-2-3-1-wide": {
        "label": "4-2-3-1 Wide",
        "lanes": [
            ("GK", "Goalkeeper"),
            ("DR", "Right back"),
            ("DCR", "Right centre-back"),
            ("DCL", "Left centre-back"),
            ("DL", "Left back"),
            ("MCR", "Right pivot"),
            ("MCL", "Left pivot"),
            ("AMR", "Right attacking flank"),
            ("AMC", "Central creator"),
            ("AML", "Left attacking flank"),
            ("ST", "Lone striker"),
        ],
    },
    "4-4-2": {
        "label": "4-4-2",
        "lanes": [
            ("GK", "Goalkeeper"),
            ("DR", "Right back"),
            ("DCR", "Right centre-back"),
            ("DCL", "Left centre-back"),
            ("DL", "Left back"),
            ("MR", "Right midfield"),
            ("MCR", "Right central midfield"),
            ("MCL", "Left central midfield"),
            ("ML", "Left midfield"),
            ("STR", "Right striker"),
            ("STL", "Left striker"),
        ],
    },
    "4-4-2-diamond-narrow": {
        "label": "4-4-2 Diamond Narrow",
        "lanes": [
            ("GK", "Goalkeeper"),
            ("DR", "Right back"),
            ("DCR", "Right centre-back"),
            ("DCL", "Left centre-back"),
            ("DL", "Left back"),
            ("DM", "Base of midfield diamond"),
            ("MCR", "Right shuttler"),
            ("MCL", "Left shuttler"),
            ("AMC", "Tip of the diamond"),
            ("STR", "Right striker"),
            ("STL", "Left striker"),
        ],
    },
    "3-4-3-dm-wide": {
        "label": "3-4-3 DM Wide",
        "lanes": [
            ("GK", "Goalkeeper"),
            ("DCR", "Right centre-back"),
            ("DC", "Central stopper"),
            ("DCL", "Left centre-back"),
            ("WBR", "Right wing-back"),
            ("DM", "Holding midfielder"),
            ("MC", "Central midfielder"),
            ("WBL", "Left wing-back"),
            ("AMR", "Right inside-forward lane"),
            ("ST", "Central striker"),
            ("AML", "Left inside-forward lane"),
        ],
    },
    "3-5-2": {
        "label": "3-5-2",
        "lanes": [
            ("GK", "Goalkeeper"),
            ("DCR", "Right centre-back"),
            ("DC", "Central stopper"),
            ("DCL", "Left centre-back"),
            ("WBR", "Right wing-back"),
            ("MCR", "Right central midfield"),
            ("MC", "Central midfield hub"),
            ("MCL", "Left central midfield"),
            ("WBL", "Left wing-back"),
            ("STR", "Right striker"),
            ("STL", "Left striker"),
        ],
    },
    "5-2-3-wb": {
        "label": "5-2-3 WB",
        "lanes": [
            ("GK", "Goalkeeper"),
            ("WBR", "Right wing-back"),
            ("DCR", "Right centre-back"),
            ("DC", "Central centre-back"),
            ("DCL", "Left centre-back"),
            ("WBL", "Left wing-back"),
            ("MCR", "Right central midfield"),
            ("MCL", "Left central midfield"),
            ("AMR", "Right forward"),
            ("ST", "Central striker"),
            ("AML", "Left forward"),
        ],
    },
    # --- Formations from guidetofm.com/tactics/formations/ ---
    "4-2-4-wide": {
        "label": "4-2-4 Wide",
        "lanes": [
            ("GK", "Goalkeeper"),
            ("DR", "Right back"),
            ("DCR", "Right centre-back"),
            ("DCL", "Left centre-back"),
            ("DL", "Left back"),
            ("MCR", "Right central midfielder"),
            ("MCL", "Left central midfielder"),
            ("AMR", "Right winger"),
            ("STR", "Right striker"),
            ("STL", "Left striker"),
            ("AML", "Left winger"),
        ],
    },
    "4-2-2-2-narrow": {
        "label": "4-2-2-2 Narrow",
        "lanes": [
            ("GK", "Goalkeeper"),
            ("DR", "Right back"),
            ("DCR", "Right centre-back"),
            ("DCL", "Left centre-back"),
            ("DL", "Left back"),
            ("MCR", "Right central midfielder"),
            ("MCL", "Left central midfielder"),
            ("AMC", "Right attacking midfielder"),
            ("AMC", "Left attacking midfielder"),
            ("STR", "Right striker"),
            ("STL", "Left striker"),
        ],
    },
    "4-2-3-1-narrow": {
        "label": "4-2-3-1 Narrow",
        "lanes": [
            ("GK", "Goalkeeper"),
            ("DR", "Right back"),
            ("DCR", "Right centre-back"),
            ("DCL", "Left centre-back"),
            ("DL", "Left back"),
            ("MCR", "Right central midfielder"),
            ("MCL", "Left central midfielder"),
            ("AMC", "Right attacking midfielder"),
            ("AMC", "Central attacking midfielder"),
            ("AMC", "Left attacking midfielder"),
            ("ST", "Striker"),
        ],
    },
    "4-3-1-2-narrow": {
        "label": "4-3-1-2 Narrow",
        "lanes": [
            ("GK", "Goalkeeper"),
            ("DR", "Right back"),
            ("DCR", "Right centre-back"),
            ("DCL", "Left centre-back"),
            ("DL", "Left back"),
            ("MCR", "Right central midfielder"),
            ("MC", "Central midfielder"),
            ("MCL", "Left central midfielder"),
            ("AMC", "Attacking midfielder"),
            ("STR", "Right striker"),
            ("STL", "Left striker"),
        ],
    },
    "5-2-2-1-wb": {
        "label": "5-2-2-1 WB",
        "lanes": [
            ("GK", "Goalkeeper"),
            ("WBR", "Right wing-back"),
            ("DCR", "Right centre-back"),
            ("DC", "Central centre-back"),
            ("DCL", "Left centre-back"),
            ("WBL", "Left wing-back"),
            ("MCR", "Right central midfielder"),
            ("MCL", "Left central midfielder"),
            ("AMC", "Right attacking midfielder"),
            ("AMC", "Left attacking midfielder"),
            ("ST", "Striker"),
        ],
    },
    "5-3-2": {
        "label": "5-3-2 WB",
        "lanes": [
            ("GK", "Goalkeeper"),
            ("WBR", "Right wing-back"),
            ("DCR", "Right centre-back"),
            ("DC", "Central centre-back"),
            ("DCL", "Left centre-back"),
            ("WBL", "Left wing-back"),
            ("MCR", "Right central midfielder"),
            ("MC", "Central midfielder"),
            ("MCL", "Left central midfielder"),
            ("STR", "Right striker"),
            ("STL", "Left striker"),
        ],
    },
    "5-4-1-wb-wide": {
        "label": "5-4-1 WB Wide",
        "lanes": [
            ("GK", "Goalkeeper"),
            ("WBR", "Right wing-back"),
            ("DCR", "Right centre-back"),
            ("DC", "Central centre-back"),
            ("DCL", "Left centre-back"),
            ("WBL", "Left wing-back"),
            ("MCR", "Right central midfielder"),
            ("MCL", "Left central midfielder"),
            ("AMR", "Right winger"),
            ("AML", "Left winger"),
            ("ST", "Striker"),
        ],
    },
    "4-1-4-1-dm-wide": {
        "label": "4-1-4-1 DM Wide",
        "lanes": [
            ("GK", "Goalkeeper"),
            ("DR", "Right back"),
            ("DCR", "Right centre-back"),
            ("DCL", "Left centre-back"),
            ("DL", "Left back"),
            ("DM", "Defensive midfielder"),
            ("MCR", "Right central midfielder"),
            ("MCL", "Left central midfielder"),
            ("AMR", "Right winger"),
            ("AML", "Left winger"),
            ("ST", "Striker"),
        ],
    },
    "4-3-3-wide": {
        "label": "4-3-3 Wide",
        "lanes": [
            ("GK", "Goalkeeper"),
            ("DR", "Right back"),
            ("DCR", "Right centre-back"),
            ("DCL", "Left centre-back"),
            ("DL", "Left back"),
            ("MCR", "Right central midfielder"),
            ("MC", "Central midfielder"),
            ("MCL", "Left central midfielder"),
            ("AMR", "Right winger"),
            ("ST", "Striker"),
            ("AML", "Left winger"),
        ],
    },
    "4-3-2-1-narrow": {
        "label": "4-3-2-1 Narrow",
        "lanes": [
            ("GK", "Goalkeeper"),
            ("DR", "Right back"),
            ("DCR", "Right centre-back"),
            ("DCL", "Left centre-back"),
            ("DL", "Left back"),
            ("MCR", "Right central midfielder"),
            ("MC", "Central midfielder"),
            ("MCL", "Left central midfielder"),
            ("AMC", "Right attacking midfielder"),
            ("AMC", "Left attacking midfielder"),
            ("ST", "Striker"),
        ],
    },
    "4-2-4-dm-wide": {
        "label": "4-2-4 DM Wide",
        "lanes": [
            ("GK", "Goalkeeper"),
            ("DR", "Right back"),
            ("DCR", "Right centre-back"),
            ("DCL", "Left centre-back"),
            ("DL", "Left back"),
            ("DM", "Right defensive midfielder"),
            ("DM", "Left defensive midfielder"),
            ("AMR", "Right winger"),
            ("STR", "Right striker"),
            ("STL", "Left striker"),
            ("AML", "Left winger"),
        ],
    },
    "4-2-2-2-dm-am-narrow": {
        "label": "4-2-2-2 DM AM Narrow",
        "lanes": [
            ("GK", "Goalkeeper"),
            ("DR", "Right back"),
            ("DCR", "Right centre-back"),
            ("DCL", "Left centre-back"),
            ("DL", "Left back"),
            ("DM", "Right defensive midfielder"),
            ("DM", "Left defensive midfielder"),
            ("AMC", "Right attacking midfielder"),
            ("AMC", "Left attacking midfielder"),
            ("STR", "Right striker"),
            ("STL", "Left striker"),
        ],
    },
    "5-3-1-1-wb": {
        "label": "5-3-1-1 WB",
        "lanes": [
            ("GK", "Goalkeeper"),
            ("WBR", "Right wing-back"),
            ("DCR", "Right centre-back"),
            ("DC", "Central centre-back"),
            ("DCL", "Left centre-back"),
            ("WBL", "Left wing-back"),
            ("MCR", "Right central midfielder"),
            ("MC", "Central midfielder"),
            ("MCL", "Left central midfielder"),
            ("AMC", "Attacking midfielder"),
            ("ST", "Striker"),
        ],
    },
    "5-1-2-2-dm-wb": {
        "label": "5-1-2-2 DM WB",
        "lanes": [
            ("GK", "Goalkeeper"),
            ("WBR", "Right wing-back"),
            ("DCR", "Right centre-back"),
            ("DC", "Central centre-back"),
            ("DCL", "Left centre-back"),
            ("WBL", "Left wing-back"),
            ("DM", "Defensive midfielder"),
            ("MCR", "Right central midfielder"),
            ("MCL", "Left central midfielder"),
            ("STR", "Right striker"),
            ("STL", "Left striker"),
        ],
    },
    "4-4-1-1": {
        "label": "4-4-1-1",
        "lanes": [
            ("GK", "Goalkeeper"),
            ("DR", "Right back"),
            ("DCR", "Right centre-back"),
            ("DCL", "Left centre-back"),
            ("DL", "Left back"),
            ("MR", "Right midfielder"),
            ("MCR", "Right central midfielder"),
            ("MCL", "Left central midfielder"),
            ("ML", "Left midfielder"),
            ("AMC", "Support striker"),
            ("ST", "Striker"),
        ],
    },
    "4-1-2-3-dm-am-narrow": {
        "label": "4-1-2-3 DM AM Narrow",
        "lanes": [
            ("GK", "Goalkeeper"),
            ("DR", "Right back"),
            ("DCR", "Right centre-back"),
            ("DCL", "Left centre-back"),
            ("DL", "Left back"),
            ("DM", "Defensive midfielder"),
            ("MCR", "Right central midfielder"),
            ("MCL", "Left central midfielder"),
            ("AMC", "Right attacking midfielder"),
            ("AMC", "Left attacking midfielder"),
            ("ST", "Striker"),
        ],
    },
    "4-1-4-1-dm-asymmetric": {
        "label": "4-1-4-1 DM Asymmetric",
        "lanes": [
            ("GK", "Goalkeeper"),
            ("DR", "Right back"),
            ("DCR", "Right centre-back"),
            ("DCL", "Left centre-back"),
            ("DL", "Left back"),
            ("DM", "Defensive midfielder"),
            ("MC", "Central midfielder"),
            ("MR", "Wide midfielder"),
            ("AMC", "Attacking midfielder"),
            ("AMR", "Wide attacker"),
            ("ST", "Striker"),
        ],
    },
    "4-1-3-2-dm-narrow": {
        "label": "4-1-3-2 DM Narrow",
        "lanes": [
            ("GK", "Goalkeeper"),
            ("DR", "Right back"),
            ("DCR", "Right centre-back"),
            ("DCL", "Left centre-back"),
            ("DL", "Left back"),
            ("DM", "Defensive midfielder"),
            ("MCR", "Right central midfielder"),
            ("MC", "Central midfielder"),
            ("MCL", "Left central midfielder"),
            ("STR", "Right striker"),
            ("STL", "Left striker"),
        ],
    },
    "4-2-3-1-dm-am-wide": {
        "label": "4-2-3-1 DM AM Wide",
        "lanes": [
            ("GK", "Goalkeeper"),
            ("DR", "Right back"),
            ("DCR", "Right centre-back"),
            ("DCL", "Left centre-back"),
            ("DL", "Left back"),
            ("DM", "Right defensive midfielder"),
            ("DM", "Left defensive midfielder"),
            ("AMR", "Right attacker"),
            ("AMC", "Central attacker"),
            ("AML", "Left attacker"),
            ("ST", "Striker"),
        ],
    },
    "4-2-3-1-dm-am-narrow": {
        "label": "4-2-3-1 DM AM Narrow",
        "lanes": [
            ("GK", "Goalkeeper"),
            ("DR", "Right back"),
            ("DCR", "Right centre-back"),
            ("DCL", "Left centre-back"),
            ("DL", "Left back"),
            ("DM", "Right defensive midfielder"),
            ("DM", "Left defensive midfielder"),
            ("AMC", "Right attacking midfielder"),
            ("AMC", "Central attacking midfielder"),
            ("AMC", "Left attacking midfielder"),
            ("ST", "Striker"),
        ],
    },
    "5-4-1-diamond-wb": {
        "label": "5-4-1 Diamond WB",
        "lanes": [
            ("GK", "Goalkeeper"),
            ("WBR", "Right wing-back"),
            ("DCR", "Right centre-back"),
            ("DC", "Central centre-back"),
            ("DCL", "Left centre-back"),
            ("WBL", "Left wing-back"),
            ("DM", "Defensive midfielder"),
            ("MCR", "Right central midfielder"),
            ("MCL", "Left central midfielder"),
            ("AMC", "Attacking midfielder"),
            ("ST", "Striker"),
        ],
    },
    "3-4-2-1-dm-am": {
        "label": "3-4-2-1 DM AM",
        "lanes": [
            ("GK", "Goalkeeper"),
            ("WBR", "Right wing-back"),
            ("DCR", "Right centre-back"),
            ("DC", "Central centre-back"),
            ("DCL", "Left centre-back"),
            ("WBL", "Left wing-back"),
            ("DM", "Right defensive midfielder"),
            ("DM", "Left defensive midfielder"),
            ("AMC", "Right attacking midfielder"),
            ("AMC", "Left attacking midfielder"),
            ("ST", "Striker"),
        ],
    },
    "4-5-1": {
        "label": "4-5-1",
        "lanes": [
            ("GK", "Goalkeeper"),
            ("DR", "Right back"),
            ("DCR", "Right centre-back"),
            ("DCL", "Left centre-back"),
            ("DL", "Left back"),
            ("MR", "Right midfielder"),
            ("MCR", "Right central midfielder"),
            ("MC", "Central midfielder"),
            ("MCL", "Left central midfielder"),
            ("ML", "Left midfielder"),
            ("ST", "Striker"),
        ],
    },
    "4-1-3-1-1-dm-am-narrow": {
        "label": "4-1-3-1-1 DM AM Narrow",
        "lanes": [
            ("GK", "Goalkeeper"),
            ("DR", "Right back"),
            ("DCR", "Right centre-back"),
            ("DCL", "Left centre-back"),
            ("DL", "Left back"),
            ("DM", "Defensive midfielder"),
            ("MCR", "Right central midfielder"),
            ("MC", "Central midfielder"),
            ("MCL", "Left central midfielder"),
            ("AMC", "Attacking midfielder"),
            ("ST", "Striker"),
        ],
    },
    "4-2-1-3-dm-wide": {
        "label": "4-2-1-3 DM Wide",
        "lanes": [
            ("GK", "Goalkeeper"),
            ("DR", "Right back"),
            ("DCR", "Right centre-back"),
            ("DCL", "Left centre-back"),
            ("DL", "Left back"),
            ("DM", "Right defensive midfielder"),
            ("DM", "Left defensive midfielder"),
            ("MC", "Central midfielder"),
            ("AMR", "Right attacker"),
            ("AML", "Left attacker"),
            ("ST", "Striker"),
        ],
    },
    "4-2-2-2-dm": {
        "label": "4-2-2-2 DM",
        "lanes": [
            ("GK", "Goalkeeper"),
            ("DR", "Right back"),
            ("DCR", "Right centre-back"),
            ("DCL", "Left centre-back"),
            ("DL", "Left back"),
            ("DM", "Right defensive midfielder"),
            ("DM", "Left defensive midfielder"),
            ("MR", "Right midfielder"),
            ("ML", "Left midfielder"),
            ("STR", "Right striker"),
            ("STL", "Left striker"),
        ],
    },
    "4-2-2-2-dm-narrow": {
        "label": "4-2-2-2 DM Narrow",
        "lanes": [
            ("GK", "Goalkeeper"),
            ("DR", "Right back"),
            ("DCR", "Right centre-back"),
            ("DCL", "Left centre-back"),
            ("DL", "Left back"),
            ("DM", "Right defensive midfielder"),
            ("DM", "Left defensive midfielder"),
            ("MCR", "Right central midfielder"),
            ("MCL", "Left central midfielder"),
            ("STR", "Right striker"),
            ("STL", "Left striker"),
        ],
    },
    "5-1-3-1-dm-wb": {
        "label": "5-1-3-1 DM WB",
        "lanes": [
            ("GK", "Goalkeeper"),
            ("WBR", "Right wing-back"),
            ("DCR", "Right centre-back"),
            ("DC", "Central centre-back"),
            ("DCL", "Left centre-back"),
            ("WBL", "Left wing-back"),
            ("DM", "Defensive midfielder"),
            ("MCR", "Right central midfielder"),
            ("MC", "Central midfielder"),
            ("MCL", "Left central midfielder"),
            ("ST", "Striker"),
        ],
    },
    "4-1-4-1-dm": {
        "label": "4-1-4-1 DM",
        "lanes": [
            ("GK", "Goalkeeper"),
            ("DR", "Right back"),
            ("DCR", "Right centre-back"),
            ("DCL", "Left centre-back"),
            ("DL", "Left back"),
            ("DM", "Defensive midfielder"),
            ("MR", "Right midfielder"),
            ("MCR", "Right central midfielder"),
            ("MCL", "Left central midfielder"),
            ("ML", "Left midfielder"),
            ("ST", "Striker"),
        ],
    },
    "4-4-1-1-2dm": {
        "label": "4-4-1-1 2DM",
        "lanes": [
            ("GK", "Goalkeeper"),
            ("DR", "Right back"),
            ("DCR", "Right centre-back"),
            ("DCL", "Left centre-back"),
            ("DL", "Left back"),
            ("DM", "Right defensive midfielder"),
            ("DM", "Left defensive midfielder"),
            ("MR", "Right midfielder"),
            ("ML", "Left midfielder"),
            ("AMC", "Support striker"),
            ("ST", "Striker"),
        ],
    },
    "4-2-2-1-1-dm-am-narrow": {
        "label": "4-2-2-1-1 DM AM Narrow",
        "lanes": [
            ("GK", "Goalkeeper"),
            ("DR", "Right back"),
            ("DCR", "Right centre-back"),
            ("DCL", "Left centre-back"),
            ("DL", "Left back"),
            ("DM", "Right defensive midfielder"),
            ("DM", "Left defensive midfielder"),
            ("MCR", "Right central midfielder"),
            ("MCL", "Left central midfielder"),
            ("AMC", "Support striker"),
            ("ST", "Striker"),
        ],
    },
    "3-4-2-1-dm": {
        "label": "3-4-2-1 DM",
        "lanes": [
            ("GK", "Goalkeeper"),
            ("WBR", "Right wing-back"),
            ("DCR", "Right centre-back"),
            ("DC", "Central centre-back"),
            ("DCL", "Left centre-back"),
            ("WBL", "Left wing-back"),
            ("DM", "Right defensive midfielder"),
            ("DM", "Left defensive midfielder"),
            ("MCR", "Right central midfielder"),
            ("MCL", "Left central midfielder"),
            ("ST", "Striker"),
        ],
    },
    "4-2-3-1-dm": {
        "label": "4-2-3-1 DM",
        "lanes": [
            ("GK", "Goalkeeper"),
            ("DR", "Right back"),
            ("DCR", "Right centre-back"),
            ("DCL", "Left centre-back"),
            ("DL", "Left back"),
            ("DM", "Right defensive midfielder"),
            ("DM", "Left defensive midfielder"),
            ("MCR", "Right central midfielder"),
            ("MC", "Central midfielder"),
            ("MCL", "Left central midfielder"),
            ("ST", "Striker"),
        ],
    },
}


def resolve_formation(formation: str | None) -> tuple[str | None, dict[str, Any] | None]:
    if not formation:
        return None, None
    formation_key = str(formation).strip().lower()
    if not formation_key:
        return None, None
    return formation_key, FORMATION_PRESETS.get(formation_key)


def _slot_capabilities(slot_code: str) -> set[str]:
    slot = str(slot_code or "").upper().strip()
    if not slot:
        return set()

    if slot == "GK":
        return {"GK"}
    if slot in {"WBR"}:
        return {"WBR"}
    if slot in {"WBL"}:
        return {"WBL"}
    if slot in {"DR"}:
        return {"DR"}
    if slot in {"DL"}:
        return {"DL"}
    if slot in {"DC", "DCR", "DCL"}:
        return {"DC"}
    if slot == "DM":
        return {"DM"}
    if slot in {"MR"}:
        return {"MR"}
    if slot in {"ML"}:
        return {"ML"}
    if slot in {"MC", "MCR", "MCL"}:
        return {"MC"}
    if slot == "AMR":
        return {"AMR"}
    if slot == "AML":
        return {"AML"}
    if slot == "AMC":
        return {"AMC"}
    if slot.startswith("ST"):
        return {"ST"}
    return set()


def _parse_position_group(base: str, sides: str) -> set[str]:
    normalized_base = base.strip().lower()
    letters = {char for char in sides.upper() if char in {"R", "L", "C"}}
    if not letters:
        letters = {"C"}

    if normalized_base == "wb":
        return ({"WBR"} if "R" in letters else set()) | ({"WBL"} if "L" in letters else set())
    if normalized_base == "d":
        return (
            ({"DR"} if "R" in letters else set())
            | ({"DL"} if "L" in letters else set())
            | ({"DC"} if "C" in letters else set())
        )
    if normalized_base == "m":
        return (
            ({"MR"} if "R" in letters else set())
            | ({"ML"} if "L" in letters else set())
            | ({"MC"} if "C" in letters else set())
        )
    if normalized_base == "am":
        return (
            ({"AMR"} if "R" in letters else set())
            | ({"AML"} if "L" in letters else set())
            | ({"AMC"} if "C" in letters else set())
        )
    if normalized_base == "st":
        return {"ST"}
    if normalized_base == "dm":
        return {"DM"}
    if normalized_base == "dc":
        return {"DC"}
    if normalized_base == "mc":
        return {"MC"}
    if normalized_base == "gk":
        return {"GK"}
    return set()


def text_position_capabilities(position_text: str) -> set[str]:
    text = str(position_text or "").strip().lower()
    if not text:
        return set()

    capabilities: set[str] = set()
    chunks = [part.strip() for part in text.split(",") if part.strip()]
    for chunk in chunks:
        if "(" in chunk and ")" in chunk:
            base, _, suffix = chunk.partition("(")
            sides = suffix.split(")", maxsplit=1)[0]
            base_variants = [part.strip() for part in base.split("/") if part.strip()]
            for base_variant in base_variants:
                capabilities.update(_parse_position_group(base_variant, sides))
            continue

        token = chunk.strip()
        if token in {"gk", "dm", "st", "dc", "mc"}:
            capabilities.update(_parse_position_group(token, "c"))
            continue
        if token in {"wb", "d", "m", "am"}:
            capabilities.update(_parse_position_group(token, "rlc"))

    return capabilities


def constrain_position_terms_to_formation(
    position: str | None, formation_key: str | None
) -> str | None:
    if not position or not formation_key:
        return position

    formation = FORMATION_PRESETS.get(formation_key)
    if not formation:
        return position

    terms = [part.strip().lower() for part in str(position).split("|") if part.strip()]
    if not terms:
        return position

    allowed_capabilities = {
        capability
        for slot_code, _slot_label in formation.get("lanes", [])
        for capability in _slot_capabilities(slot_code)
    }
    constrained_terms = [
        term for term in terms if text_position_capabilities(term) & allowed_capabilities
    ]
    if not constrained_terms:
        return None
    return "|".join(constrained_terms)


def entry_matches_position_terms(entry: dict[str, Any], position_terms: str | None) -> bool:
    if not position_terms:
        return True
    player = entry.get("player", {})
    player_position = str(player.get("position", ""))
    terms = [part.strip().lower() for part in str(position_terms).split("|") if part.strip()]
    if not terms:
        return True

    player_capabilities = text_position_capabilities(player_position)
    if not player_capabilities:
        return False
    return any(text_position_capabilities(term) & player_capabilities for term in terms)


def _position_tokens(position_text: str) -> set[str]:
    normalized = str(position_text or "").upper()
    tokens: set[str] = set()
    if not normalized:
        return tokens

    for token in ("GK", "WB", "DM", "AM", "ST", "DC", "MC", "MR", "ML", "DR", "DL"):
        if token in normalized:
            tokens.add(token)
    for token in ("R", "L", "C"):
        if f"({token}" in normalized or token + ")" in normalized or f", {token}" in normalized:
            tokens.add(token)
    if "WBR" in normalized or "WB (R" in normalized:
        tokens.update({"WB", "R"})
    if "WBL" in normalized or "WB (L" in normalized:
        tokens.update({"WB", "L"})
    return tokens


def _formation_slot_match_score(slot_code: str, position_tokens: set[str]) -> int:
    score = 0
    slot = slot_code.upper()
    if not position_tokens:
        return score

    if slot.startswith("GK") and "GK" in position_tokens:
        score += 10
    if slot.startswith("WB") and "WB" in position_tokens:
        score += 9
    if slot.startswith("DC") and "DC" in position_tokens:
        score += 8
    if (
        slot.startswith("D")
        and not slot.startswith("DC")
        and any(token in position_tokens for token in {"DR", "DL"})
    ):
        score += 7
    if slot.startswith("DM") and "DM" in position_tokens:
        score += 8
    if slot.startswith("MC") and "MC" in position_tokens:
        score += 8
    if slot.startswith("M") and any(token in position_tokens for token in {"MR", "ML"}):
        score += 7
    if slot.startswith("AM") and "AM" in position_tokens:
        score += 8
    if slot.startswith("ST") and "ST" in position_tokens:
        score += 9

    if "R" in slot and "R" in position_tokens:
        score += 2
    if "L" in slot and "L" in position_tokens:
        score += 2
    if "C" in slot and "C" in position_tokens:
        score += 1
    if slot in {"DC", "MC", "ST"}:
        score += 1
    return score


def formation_advice(position_text: str, formation_key: str | None) -> dict[str, str] | None:
    if not formation_key:
        return None
    formation = FORMATION_PRESETS.get(formation_key)
    if not formation:
        return None

    position_tokens = _position_tokens(position_text)
    if not position_tokens:
        return None

    ranked_slots = sorted(
        (
            (slot_code, slot_label, _formation_slot_match_score(slot_code, position_tokens))
            for slot_code, slot_label in formation["lanes"]
        ),
        key=lambda item: item[2],
        reverse=True,
    )
    best_slot_code, best_slot_label, best_score = ranked_slots[0]
    if best_score <= 0:
        return None

    return {
        "slot_code": best_slot_code,
        "slot_label": best_slot_label,
        "formation_label": str(formation["label"]),
    }


def augment_prompt_with_formation(prompt: str, formation_label: str | None) -> str:
    """Append formation context to a prompt string if a formation label is provided."""
    base_prompt = prompt.strip()
    if not formation_label:
        return base_prompt
    return (
        f"{base_prompt}. Formation context: {formation_label}." if base_prompt else formation_label
    )
