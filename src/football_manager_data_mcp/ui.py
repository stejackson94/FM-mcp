from __future__ import annotations

import json
import os
from collections.abc import Iterable
from pathlib import Path
from typing import Annotated, Any
from urllib import error, request
from urllib.parse import urlparse

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from football_manager_data_mcp.catalog import FootballCatalog

app = FastAPI(title="Make FM Scouting Data Again", version="0.1.0")
frontend_dir = Path(__file__).resolve().parent / "frontend"
input_data_dir = Path(__file__).resolve().parents[2] / "input_data"
project_root_dir = Path(__file__).resolve().parents[2]

# Auto-load local .env so runtime config works without sourcing shell vars.
load_dotenv(project_root_dir / ".env")

uploaded_data_dir = input_data_dir / "ui_uploads"
uploaded_data_dir.mkdir(parents=True, exist_ok=True)

catalog = FootballCatalog()

_REQUIRED_COLUMNS = {
    "Player",
    "Club",
    "Nat",
    "Position",
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
    strengths = scored_metrics[:2]
    trade_off = scored_metrics[-1] if len(scored_metrics) > 2 else None

    return {
        "player_name": player.get("name", "Unknown"),
        "club_name": player.get("club_name", "Unknown"),
        "position": player.get("position", ""),
        "search_brief": prompt.strip(),
        "evaluation_mode": "lower_better" if prefer_low else "higher_better",
        "rank": rank_index + 1,
        "total_ranked": total_ranked,
        "score": round(float(entry.get("score", 0.0)), 4),
        "requested_metrics": entry.get("requested_metrics", []),
        "strengths": strengths,
        "trade_off": trade_off,
    }


def _deterministic_explanation(facts: dict[str, Any]) -> dict[str, str]:
    strengths = facts.get("strengths", [])
    strength_bits = [
        f"{item['metric']} ({item['value']}, {item['percentile']}th percentile)"
        for item in strengths
    ]
    strength_text = ", ".join(strength_bits) if strength_bits else "consistent all-round output"
    requested = [str(item) for item in facts.get("requested_metrics", []) if str(item).strip()]
    requested_text = ", ".join(requested) if requested else "the requested profile"
    brief = str(facts.get("search_brief", "")).strip() or "the requested scouting brief"
    player_name = str(facts.get("player_name", "This player"))
    position = str(facts.get("position", "")).strip() or "multiple roles"

    rank = int(facts.get("rank", 1))
    total = int(facts.get("total_ranked", 1))

    if rank == 1:
        lead = "Best fit in this result set"
    elif rank <= 3:
        lead = f"Top-tier option (ranked #{rank} of {total})"
    else:
        lead = f"Useful profile (ranked #{rank} of {total})"

    why_fit = (
        f"{player_name}: {lead} for '{brief}'.\n"
        f"- Key metrics: {strength_text}.\n"
        f"- System fit: profile aligns with {requested_text}.\n"
        f"- Role context: {position}."
    )

    trade_off = facts.get("trade_off")
    if trade_off:
        trade_off_text = (
            f"{trade_off['metric']} ({trade_off['value']}, {trade_off['percentile']}th percentile)"
        )
        caveat = (
            "- Risk: weakest requested indicator is "
            f"{trade_off_text}.\n"
            "- Check: confirm this trade-off is acceptable for your tactical plan."
        )
    else:
        caveat = "- Risk: validate role familiarity and tactical fit before final decision."

    primary_metric = strengths[0]["metric"] if strengths else "the target metrics"
    tactical_use = (
        f"- Usage: deploy as {position} in a setup that leans on {primary_metric}.\n"
        "- Coaching note: pair with nearby support roles to protect weaker phases."
    )
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
        "why_fit must include: a one-line verdict, a 'Key metrics' bullet "
        "with at least two supplied metrics with values/percentiles, "
        "a 'System fit' bullet tied to the brief, and a 'Role context' bullet. "
        "caveat must include a clear risk bullet and one mitigation/check bullet. "
        "tactical_use must include a usage bullet and a coaching-note bullet "
        "with system guidance.\n\n"
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
            raise json.JSONDecodeError("JSON content is not an object", text, start)
        return parsed


@app.get("/")
def index() -> FileResponse:
    return FileResponse(frontend_dir / "index.html")


@app.get("/api/data-status")
def api_data_status() -> dict[str, Any]:
    uploaded_files = [file_path.name for file_path in _uploaded_html_files()]
    return {
        "mode": _active_mode(),
        "uploaded_files": uploaded_files,
        "player_count": len(catalog._players),
    }


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
    position: str | None = Query(default=None),
    country: str | None = Query(default=None),
    min_minutes: float | None = Query(default=None, ge=0),
    limit: int = Query(default=10, ge=1, le=200),
) -> list[dict[str, Any]]:
    if not prompt.strip():
        raise HTTPException(status_code=400, detail="Query parameter 'prompt' is required.")

    resolved_position = position.strip().lower() if position else catalog._infer_position(prompt)
    normalized_country = country.strip().lower() if country else None
    prefer_low = catalog._prefer_low(prompt)

    ranked_pool = catalog.rank_players_by_preferences(
        prompt=prompt,
        position=resolved_position,
        country=normalized_country,
        limit=max(len(catalog._players), 1),
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

    for index, entry in enumerate(ranked_subset):
        facts = _build_explanation_facts(
            entry=entry,
            rank_index=index,
            total_ranked=len(ranked_pool),
            ranked_pool=ranked_pool,
            prefer_low=prefer_low,
            prompt=prompt,
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
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
