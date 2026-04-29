from __future__ import annotations

import io
import json
import logging
import os
import threading
import zipfile
from collections.abc import Iterable
from pathlib import Path
from typing import Annotated, Any
from urllib import error, request
from urllib.parse import urlparse

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from football_manager_data_mcp.catalog import FootballCatalog

app = FastAPI(title="Make FM Scouting Data Again", version="0.1.0")
logger = logging.getLogger(__name__)
frontend_dir = Path(__file__).resolve().parent / "frontend"
package_root_dir = Path(__file__).resolve().parent
input_data_dir = Path(__file__).resolve().parents[2] / "input_data"
project_root_dir = Path(__file__).resolve().parents[2]
fm_views_dirs = [
    project_root_dir / "fm_views",
    package_root_dir / "fm_views",
]
required_view_files = [
    "General Metrics search.fmf",
    "General Metrics scouted.fmf",
]

# Auto-load local .env so runtime config works without sourcing shell vars.
load_dotenv(project_root_dir / ".env")

uploaded_data_dir = input_data_dir / "ui_uploads"
uploaded_data_dir.mkdir(parents=True, exist_ok=True)

catalog = FootballCatalog()

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
}


def _uploaded_html_files() -> list[Path]:
    return sorted(uploaded_data_dir.glob("*.html"))


def _delete_files(files: Iterable[Path]) -> int:
    removed = 0
    for file_path in files:
        if not file_path.exists():
            continue
        file_path.unlink()
        removed += 1
    return removed


def _build_catalog() -> FootballCatalog:
    if _uploaded_html_files():
        return FootballCatalog(input_data_dir=uploaded_data_dir)
    return FootballCatalog()


def _reload_catalog() -> None:
    global catalog
    catalog = _build_catalog()


def _active_mode() -> str:
    return "uploaded" if _uploaded_html_files() else "default"


def _validate_columns(new_catalog: FootballCatalog) -> list[str]:
    available_columns = {
        str(item["column"]) for item in new_catalog.list_available_columns() if "column" in item
    }
    return sorted(_REQUIRED_COLUMNS - available_columns)


def _resolve_required_view_file(filename: str) -> Path | None:
    for base_dir in fm_views_dirs:
        candidate = base_dir / filename
        if candidate.is_file():
            return candidate
    return None


_reload_catalog()

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

app.mount("/frontend", StaticFiles(directory=frontend_dir), name="frontend")

AUTO_CLEAR_UPLOADS = os.getenv("FM_AUTO_CLEAR_UPLOADS", "true").lower() in {
    "1",
    "true",
    "yes",
    "on",
}
AUTO_CLEAR_UPLOADS_INTERVAL_SECONDS = int(
    os.getenv("FM_AUTO_CLEAR_UPLOADS_INTERVAL_SECONDS", "3600")
)
_cleanup_stop_event = threading.Event()
_cleanup_thread: threading.Thread | None = None


def _llm_source_name() -> str:
    parsed_base_url = urlparse(LLM_BASE_URL)
    host = (parsed_base_url.netloc or "").lower()
    model_name = LLM_MODEL.lower()

    if "groq" in host or model_name.startswith("groq/"):
        return "Groq"
    if "ollama" in host or "127.0.0.1:11434" in host or "localhost:11434" in host:
        return "local llm"
    if "openai" in host or model_name.startswith("gpt-"):
        return "OpenAI-compatible"
    return "llm"


def _percentile_for_value(values: list[float], value: float, prefer_low: bool) -> int:
    if not values:
        return 0
    if prefer_low:
        worse_or_equal = sum(1 for item in values if item >= value)
    else:
        worse_or_equal = sum(1 for item in values if item <= value)
    percentile = (worse_or_equal / len(values)) * 100
    return round(percentile)


def _clean_player_text(value: Any, fallback: str = "") -> str:
    text = str(value or "").strip()
    if not text or text == "-" or text.lower() == "unknown":
        return fallback
    return text


def _format_fact_value(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, float):
        return str(int(value)) if value.is_integer() else f"{value:.2f}"
    text = _clean_player_text(value)
    return text or None


def _resolve_formation(formation: str | None) -> tuple[str | None, dict[str, Any] | None]:
    if not formation:
        return None, None
    formation_key = str(formation).strip().lower()
    if not formation_key:
        return None, None
    return formation_key, FORMATION_PRESETS.get(formation_key)


def _augment_prompt_with_formation(prompt: str, formation_label: str | None) -> str:
    base_prompt = prompt.strip()
    if not formation_label:
        return base_prompt
    return (
        f"{base_prompt}. Formation context: {formation_label}." if base_prompt else formation_label
    )


def _position_term_matches_slot(position_term: str, slot_code: str) -> bool:
    return bool(_term_capabilities(position_term) & _slot_capabilities(slot_code))


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
    if normalized_base == "gk":
        return {"GK"}
    return set()


def _text_position_capabilities(position_text: str) -> set[str]:
    text = str(position_text or "").strip().lower()
    if not text:
        return set()

    capabilities: set[str] = set()
    chunks = [part.strip() for part in text.split(",") if part.strip()]
    for chunk in chunks:
        if "(" in chunk and ")" in chunk:
            base, _, suffix = chunk.partition("(")
            sides = suffix.split(")", maxsplit=1)[0]
            capabilities.update(_parse_position_group(base, sides))
            continue

        token = chunk.strip()
        if token in {"gk", "dm", "st"}:
            capabilities.update(_parse_position_group(token, "c"))
            continue
        if token in {"wb", "d", "m", "am"}:
            capabilities.update(_parse_position_group(token, "rlc"))
            continue
        if token == "dc":
            capabilities.add("DC")
        if token == "mc":
            capabilities.add("MC")

    return capabilities


def _term_capabilities(position_term: str) -> set[str]:
    return _text_position_capabilities(position_term)


def _constrain_position_terms_to_formation(
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
    constrained_terms = [term for term in terms if _term_capabilities(term) & allowed_capabilities]
    if not constrained_terms:
        return None
    return "|".join(constrained_terms)


def _entry_matches_position_terms(entry: dict[str, Any], position_terms: str | None) -> bool:
    if not position_terms:
        return True
    player = entry.get("player", {})
    player_position = str(player.get("position", ""))
    terms = [part.strip().lower() for part in str(position_terms).split("|") if part.strip()]
    if not terms:
        return True

    player_capabilities = _text_position_capabilities(player_position)
    if not player_capabilities:
        return False
    return any(_term_capabilities(term) & player_capabilities for term in terms)


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


def _formation_advice(position_text: str, formation_key: str | None) -> dict[str, str] | None:
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


def _describe_score_band(score: float) -> str:
    if score >= 0.75:
        return "elite"
    if score >= 0.55:
        return "strong"
    if score >= 0.4:
        return "balanced"
    return "situational"


def _build_explanation_facts(
    entry: dict[str, Any],
    rank_index: int,
    total_ranked: int,
    ranked_pool: list[dict[str, Any]],
    prefer_low: bool,
    prompt: str,
) -> dict[str, Any]:
    player = entry.get("player", {})
    matched_metrics = entry.get("matched_metrics", {})
    numeric_metrics = player.get("numeric_metrics", {})

    metric_values_by_name: dict[str, list[float]] = {}
    for pool_entry in ranked_pool:
        for metric_name, metric_value in pool_entry.get("matched_metrics", {}).items():
            metric_values_by_name.setdefault(metric_name, []).append(float(metric_value))

    scored_metrics: list[dict[str, Any]] = []
    for metric_name, metric_value in matched_metrics.items():
        numeric_value = float(metric_value)
        percentile = _percentile_for_value(
            metric_values_by_name.get(metric_name, []),
            numeric_value,
            prefer_low=prefer_low,
        )
        scored_metrics.append(
            {
                "metric": metric_name,
                "value": round(numeric_value, 2),
                "percentile": percentile,
            }
        )

    scored_metrics.sort(key=lambda item: int(item["percentile"]), reverse=True)
    strengths = scored_metrics[:3]
    trade_off = scored_metrics[-1] if len(scored_metrics) > 2 else None
    score = round(float(entry.get("score", 0.0)), 4)

    player_context = []
    for value in (
        _clean_player_text(player.get("club_name")),
        _clean_player_text(player.get("nationality")),
        _clean_player_text(player.get("position")),
    ):
        if value and value not in player_context:
            player_context.append(value)

    minutes_value = _format_fact_value(numeric_metrics.get("Mins"))
    transfer_value = _format_fact_value(player.get("transfer_value"))
    wage = _format_fact_value(player.get("wage"))
    rec = _format_fact_value(player.get("rec"))
    potential = _format_fact_value(player.get("potential"))
    formation_key, formation = _resolve_formation(entry.get("formation"))
    formation_advice = _formation_advice(_clean_player_text(player.get("position")), formation_key)

    return {
        "player_name": player.get("name", "Unknown"),
        "club_name": _clean_player_text(player.get("club_name")),
        "nationality": _clean_player_text(player.get("nationality")),
        "position": _clean_player_text(player.get("position")),
        "search_brief": prompt.strip(),
        "evaluation_mode": "lower_better" if prefer_low else "higher_better",
        "rank": rank_index + 1,
        "total_ranked": total_ranked,
        "score": score,
        "score_band": _describe_score_band(score),
        "requested_metrics": entry.get("requested_metrics", []),
        "strengths": strengths,
        "trade_off": trade_off,
        "minutes": minutes_value,
        "transfer_value": transfer_value,
        "wage": wage,
        "recommendation": rec,
        "potential": potential,
        "player_context": player_context,
        "formation": str(formation["label"]) if formation else "",
        "formation_advice": formation_advice,
    }


def _deterministic_explanation(facts: dict[str, Any]) -> dict[str, str]:
    strengths = facts.get("strengths", [])
    requested = [str(item) for item in facts.get("requested_metrics", []) if str(item).strip()]
    requested_text = ", ".join(requested) if requested else "the requested profile"
    brief = str(facts.get("search_brief", "")).strip() or "the requested scouting brief"
    player_name = str(facts.get("player_name", "This player"))
    position = str(facts.get("position", "")).strip() or "multiple roles"
    club_name = _clean_player_text(facts.get("club_name"))
    nationality = _clean_player_text(facts.get("nationality"))
    score_band = str(facts.get("score_band", "balanced"))

    rank = int(facts.get("rank", 1))
    total = int(facts.get("total_ranked", 1))

    if rank == 1:
        lead = f"{player_name} is the strongest match in this result set"
    elif rank <= 3:
        lead = f"{player_name} profiles as a top-tier option at #{rank} of {total}"
    else:
        lead = f"{player_name} still offers a usable fit at #{rank} of {total}"

    context_bits: list[str] = []
    if nationality and club_name:
        context_bits.append(f"{nationality} at {club_name}")
    elif club_name:
        context_bits.append(f"At {club_name}")
    elif nationality:
        context_bits.append(nationality)
    if position:
        context_bits.append(position)
    minutes = facts.get("minutes")
    transfer_value = facts.get("transfer_value")
    if minutes:
        context_bits.append(f"{minutes} minutes")
    if transfer_value:
        context_bits.append(f"value {transfer_value}")
    context_text = (
        ", ".join(bit for bit in context_bits if bit) or "Limited club context in this export"
    )

    best_metric = strengths[0] if strengths else None
    support_metric = strengths[1] if len(strengths) > 1 else None
    evidence_text = (
        "The export does not include enough matched numeric evidence to isolate a clear edge."
    )
    if best_metric and support_metric:
        best_metric_text = (
            f"{best_metric['metric']} "
            f"({best_metric['value']}, {best_metric['percentile']}th percentile)"
        )
        support_metric_text = (
            f"{support_metric['metric']} "
            f"({support_metric['value']}, {support_metric['percentile']}th percentile)"
        )
        evidence_text = (
            f"{best_metric_text} and {support_metric_text} "
            f"are the clearest indicators for the brief."
        )
    elif best_metric:
        best_metric_text = (
            f"{best_metric['metric']} "
            f"({best_metric['value']}, {best_metric['percentile']}th percentile)"
        )
        evidence_text = f"{best_metric_text} stands out most strongly in this result set."

    market_bits = []
    if facts.get("recommendation"):
        market_bits.append(f"Rec {facts['recommendation']}")
    if facts.get("potential"):
        market_bits.append(f"Potential {facts['potential']}")
    if facts.get("wage"):
        market_bits.append(f"Wage {facts['wage']}")
    market_text = "; ".join(market_bits)

    why_fit = (
        f"{lead} for '{brief}'.\n"
        f"- Profile: {context_text}.\n"
        f"- Evidence: {evidence_text}.\n"
        f"- System fit: {score_band.capitalize()} match when the role leans on {requested_text}."
    )
    if market_text:
        why_fit = f"{why_fit}\n- Market snapshot: {market_text}."

    trade_off = facts.get("trade_off")
    if trade_off:
        trade_off_text = (
            f"{trade_off['metric']} ({trade_off['value']}, {trade_off['percentile']}th percentile)"
        )
        caveat = (
            "- Risk: profile drops off most on "
            f"{trade_off_text}, "
            "so the fit is stronger for systems that can live with that compromise."
        )
    else:
        caveat = (
            "- Risk: the data is broad rather than spiky, so role precision matters "
            "more than headline fit."
        )

    primary_metric = strengths[0]["metric"] if strengths else "the target metrics"
    supporting_metric = strengths[1]["metric"] if len(strengths) > 1 else requested_text
    formation = _clean_player_text(facts.get("formation"))
    formation_advice = facts.get("formation_advice") or {}
    slot_label = _clean_player_text(formation_advice.get("slot_label"))
    slot_code = _clean_player_text(formation_advice.get("slot_code"))

    usage_text = (
        f"deploy as {position} in a setup that leans on {primary_metric} "
        f"and gives him repeated {supporting_metric} actions"
    )
    if formation and slot_label and slot_code:
        usage_text = (
            f"in {formation}, use him as the {slot_label} ({slot_code}) "
            f"if you want those {primary_metric} "
            f"actions to show up consistently"
        )
    tactical_use = f"- Usage: {usage_text}."
    return {"why_fit": why_fit, "caveat": caveat, "tactical_use": tactical_use}


def _llm_rewrite_explanation(
    facts: dict[str, Any], fallback: dict[str, str]
) -> dict[str, str] | None:
    if not LLM_ENABLED_BY_DEFAULT or not LLM_API_KEY:
        return None

    prompt = (
        "You are a football recruitment analyst. "
        "Write a personalized scouting recommendation for the exact search brief. "
        "Use only supplied facts; do not invent or alter numbers. "
        "Return strict JSON with keys why_fit, caveat, tactical_use. "
        "Format each value as plain text with line breaks and '-' bullets "
        "(no markdown fences). "
        "why_fit must include: a one-line verdict, a 'Profile' bullet using club, "
        "nationality, position, minutes or market facts when supplied, "
        "an 'Evidence' bullet with at least two supplied metrics with values/percentiles "
        "and why they matter for the brief, "
        "and a 'System fit' bullet tied to the brief. "
        "caveat must contain exactly one risk bullet and must not include any "
        "'Check', 'Mitigation', or second bullet. "
        "If formation and formation_advice are supplied, tactical_use must mention "
        "the named formation "
        "slot and explain where to play the player inside that shape. "
        "tactical_use must contain exactly one usage bullet with system guidance.\n\n"
        f"FACTS:\n{json.dumps(facts, ensure_ascii=True)}\n\n"
        f"SAFE_FALLBACK:\n{json.dumps(fallback, ensure_ascii=True)}"
    )

    payload = {
        "model": LLM_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "Return strict JSON only. No markdown.",
            },
            {"role": "user", "content": prompt},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.6,
    }
    req = request.Request(
        url=f"{LLM_BASE_URL.rstrip('/')}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {LLM_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "football-manager-data-mcp/0.1",
        },
    )

    try:
        with request.urlopen(req, timeout=8) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (error.URLError, TimeoutError, json.JSONDecodeError):
        return None

    try:
        content = body["choices"][0]["message"]["content"]
        parsed = _parse_json_like_content(content)
        why_fit = str(parsed["why_fit"]).strip()
        caveat = str(parsed["caveat"]).strip()
        tactical_use = str(parsed["tactical_use"]).strip()
    except (KeyError, IndexError, TypeError, json.JSONDecodeError):
        return None

    if not why_fit or not caveat or not tactical_use:
        return None
    return {
        "why_fit": why_fit,
        "caveat": caveat,
        "tactical_use": tactical_use,
    }


def _parse_json_like_content(content: str) -> dict[str, Any]:
    text = str(content or "").strip()
    if not text:
        raise json.JSONDecodeError("Empty content", text, 0)

    # Some local models wrap JSON in markdown fences despite instructions.
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    # Handle language-prefixed fenced blocks like "json".
    if text.lower().startswith("json"):
        text = text[4:].strip()

    try:
        parsed = json.loads(text)
        if isinstance(parsed, str):
            parsed = json.loads(parsed)
        if not isinstance(parsed, dict):
            raise json.JSONDecodeError("JSON content is not an object", text, 0)
        return parsed
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        parsed = json.loads(text[start : end + 1])
        if isinstance(parsed, str):
            parsed = json.loads(parsed)
        if not isinstance(parsed, dict):
            raise json.JSONDecodeError("JSON content is not an object", text, start) from None
        return parsed


def _auto_cleanup_uploaded_data() -> None:
    interval = max(AUTO_CLEAR_UPLOADS_INTERVAL_SECONDS, 60)
    while not _cleanup_stop_event.wait(interval):
        removed = _delete_files(_uploaded_html_files())
        if removed > 0:
            _reload_catalog()
            logger.info("Auto-cleared %s uploaded file(s)", removed)


@app.on_event("startup")
def _startup_tasks() -> None:
    global _cleanup_thread
    if not AUTO_CLEAR_UPLOADS:
        logger.info("Auto-clear uploads disabled")
        return
    _cleanup_stop_event.clear()
    _cleanup_thread = threading.Thread(target=_auto_cleanup_uploaded_data, daemon=True)
    _cleanup_thread.start()


@app.on_event("shutdown")
def _shutdown_tasks() -> None:
    _cleanup_stop_event.set()
    if _cleanup_thread and _cleanup_thread.is_alive():
        _cleanup_thread.join(timeout=1)


@app.get("/")
def index() -> FileResponse:
    return FileResponse(frontend_dir / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/data-status")
def api_data_status() -> dict[str, Any]:
    uploaded_files = [file_path.name for file_path in _uploaded_html_files()]
    return {
        "mode": _active_mode(),
        "uploaded_files": uploaded_files,
        "player_count": len(catalog._players),
    }


@app.get("/api/download-required-views")
def api_download_required_views() -> Response:
    resolved_files = {name: _resolve_required_view_file(name) for name in required_view_files}
    missing_files = [name for name, path in resolved_files.items() if path is None]
    if missing_files:
        raise HTTPException(
            status_code=404,
            detail=("Required FM view files are missing: " + ", ".join(sorted(missing_files))),
        )

    archive_buffer = io.BytesIO()
    with zipfile.ZipFile(archive_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        for filename in required_view_files:
            archive.write(resolved_files[filename], arcname=filename)

    return Response(
        content=archive_buffer.getvalue(),
        media_type="application/zip",
        headers={
            "Content-Disposition": 'attachment; filename="fm-required-views.zip"',
        },
    )


@app.post("/api/upload")
async def api_upload(file: Annotated[UploadFile, File(...)]) -> dict[str, Any]:
    filename = file.filename or "upload.html"
    if not filename.lower().endswith(".html"):
        raise HTTPException(status_code=400, detail="Only .html files are supported.")

    raw_content = await file.read()
    if not raw_content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Keep only the latest upload so storage does not grow over time.
    _delete_files(_uploaded_html_files())
    destination = uploaded_data_dir / "uploaded.html"
    destination.write_bytes(raw_content)

    new_catalog = FootballCatalog(input_data_dir=uploaded_data_dir)
    if not new_catalog._players:
        destination.unlink(missing_ok=True)
        raise HTTPException(
            status_code=400,
            detail=(
                "No players could be parsed from this file. Use an FM player-search HTML export."
            ),
        )

    missing_columns = _validate_columns(new_catalog)
    if missing_columns:
        destination.unlink(missing_ok=True)
        raise HTTPException(
            status_code=400,
            detail=("Uploaded HTML is missing required columns: " + ", ".join(missing_columns)),
        )

    global catalog
    catalog = new_catalog
    return {
        "mode": "uploaded",
        "uploaded_files": [destination.name],
        "player_count": len(catalog._players),
    }


@app.post("/api/clear-data")
def api_clear_data() -> dict[str, Any]:
    removed = _delete_files(_uploaded_html_files())
    _reload_catalog()
    return {
        "removed_files": removed,
        "mode": _active_mode(),
        "player_count": len(catalog._players),
    }


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
    formation: str | None = Query(default=None),
    position: str | None = Query(default=None),
    country: str | None = Query(default=None),
    min_minutes: float | None = Query(default=None, ge=0),
    limit: int = Query(default=10, ge=1, le=200),
) -> list[dict[str, Any]]:
    if not prompt.strip():
        raise HTTPException(status_code=400, detail="Query parameter 'prompt' is required.")

    _formation_key, resolved_formation = _resolve_formation(formation)
    effective_prompt = _augment_prompt_with_formation(
        prompt,
        str(resolved_formation["label"]) if resolved_formation else None,
    )

    resolved_position = (
        position.strip().lower() if position else catalog._infer_position(effective_prompt)
    )
    resolved_position = _constrain_position_terms_to_formation(resolved_position, _formation_key)
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
            entry
            for entry in ranked_pool
            if _entry_matches_position_terms(entry, resolved_position)
        ]

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
        facts = _build_explanation_facts(
            entry=entry,
            rank_index=index,
            total_ranked=len(ranked_pool),
            ranked_pool=ranked_pool,
            prefer_low=prefer_low,
            prompt=effective_prompt,
        )
        fallback = _deterministic_explanation(facts)
        llm_result = _llm_rewrite_explanation(facts, fallback)
        if llm_result:
            entry["explanation"] = {**llm_result, "source": _llm_source_name(), "facts": facts}
        else:
            entry["explanation"] = {**fallback, "source": "rules", "facts": facts}

    return ranked_subset


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
    host = os.getenv("FM_UI_HOST", "0.0.0.0")
    try:
        port = int(os.getenv("FM_UI_PORT", "8000"))
    except ValueError:
        port = 8000
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
