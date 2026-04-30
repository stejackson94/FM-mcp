from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib import error, request
from urllib.parse import urlparse

from football_manager_data_mcp.positions import formation_advice, resolve_formation


@dataclass(frozen=True)
class ExplanationSettings:
    llm_enabled: bool
    llm_model: str
    llm_api_key: str
    llm_base_url: str


def llm_source_name(settings: ExplanationSettings) -> str:
    parsed_base_url = urlparse(settings.llm_base_url)
    host = (parsed_base_url.netloc or "").lower()
    model_name = settings.llm_model.lower()

    if "groq" in host or model_name.startswith("groq/"):
        return "Groq"
    if "ollama" in host or "127.0.0.1:11434" in host or "localhost:11434" in host:
        return "local llm"
    if "openai" in host or model_name.startswith("gpt-"):
        return "OpenAI-compatible"
    return "llm"


def percentile_for_value(values: list[float], value: float, prefer_low: bool) -> int:
    if not values:
        return 0
    if prefer_low:
        worse_or_equal = sum(1 for item in values if item >= value)
    else:
        worse_or_equal = sum(1 for item in values if item <= value)
    percentile = (worse_or_equal / len(values)) * 100
    return round(percentile)


def clean_player_text(value: Any, fallback: str = "") -> str:
    text = str(value or "").strip()
    if not text or text == "-" or text.lower() == "unknown":
        return fallback
    return text


def format_fact_value(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, float):
        return str(int(value)) if value.is_integer() else f"{value:.2f}"
    text = clean_player_text(value)
    return text or None


def describe_score_band(score: float) -> str:
    if score >= 0.75:
        return "elite"
    if score >= 0.55:
        return "strong"
    if score >= 0.4:
        return "balanced"
    return "situational"


def build_explanation_facts(
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
        percentile = percentile_for_value(
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
        clean_player_text(player.get("club_name")),
        clean_player_text(player.get("nationality")),
        clean_player_text(player.get("position")),
    ):
        if value and value not in player_context:
            player_context.append(value)

    minutes_value = format_fact_value(numeric_metrics.get("Mins"))
    transfer_value = format_fact_value(player.get("transfer_value"))
    wage = format_fact_value(player.get("wage"))
    rec = format_fact_value(player.get("rec"))
    potential = format_fact_value(player.get("potential"))
    formation_key, formation = resolve_formation(entry.get("formation"))
    role_advice = formation_advice(clean_player_text(player.get("position")), formation_key)

    return {
        "player_name": player.get("name", "Unknown"),
        "club_name": clean_player_text(player.get("club_name")),
        "nationality": clean_player_text(player.get("nationality")),
        "position": clean_player_text(player.get("position")),
        "search_brief": prompt.strip(),
        "evaluation_mode": "lower_better" if prefer_low else "higher_better",
        "rank": rank_index + 1,
        "total_ranked": total_ranked,
        "score": score,
        "score_band": describe_score_band(score),
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
        "formation_advice": role_advice,
    }


def deterministic_explanation(facts: dict[str, Any]) -> dict[str, str]:
    strengths = facts.get("strengths", [])
    requested = [str(item) for item in facts.get("requested_metrics", []) if str(item).strip()]
    requested_text = ", ".join(requested) if requested else "the requested profile"
    brief = str(facts.get("search_brief", "")).strip() or "the requested scouting brief"
    player_name = str(facts.get("player_name", "This player"))
    position = str(facts.get("position", "")).strip() or "multiple roles"
    club_name = clean_player_text(facts.get("club_name"))
    nationality = clean_player_text(facts.get("nationality"))
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
    formation = clean_player_text(facts.get("formation"))
    role_advice = facts.get("formation_advice") or {}
    slot_label = clean_player_text(role_advice.get("slot_label"))
    slot_code = clean_player_text(role_advice.get("slot_code"))

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


def parse_json_like_content(content: str) -> dict[str, Any]:
    text = str(content or "").strip()
    if not text:
        raise json.JSONDecodeError("Empty content", text, 0)

    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

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


def llm_rewrite_explanation(
    facts: dict[str, Any],
    fallback: dict[str, str],
    settings: ExplanationSettings,
) -> dict[str, str] | None:
    if not settings.llm_enabled or not settings.llm_api_key:
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
        "model": settings.llm_model,
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
        url=f"{settings.llm_base_url.rstrip('/')}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {settings.llm_api_key}",
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
        parsed = parse_json_like_content(content)
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


def build_entry_explanation(
    entry: dict[str, Any],
    rank_index: int,
    total_ranked: int,
    ranked_pool: list[dict[str, Any]],
    prefer_low: bool,
    prompt: str,
    settings: ExplanationSettings,
) -> dict[str, Any]:
    facts = build_explanation_facts(
        entry=entry,
        rank_index=rank_index,
        total_ranked=total_ranked,
        ranked_pool=ranked_pool,
        prefer_low=prefer_low,
        prompt=prompt,
    )
    fallback = deterministic_explanation(facts)
    llm_result = llm_rewrite_explanation(facts, fallback, settings)
    if llm_result:
        return {**llm_result, "source": llm_source_name(settings), "facts": facts}
    return {**fallback, "source": "rules", "facts": facts}
