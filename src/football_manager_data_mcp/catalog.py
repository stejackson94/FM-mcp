from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from html import unescape
from pathlib import Path

_COLUMN_ALIASES = {
    "Name": "Player",
    "Pres C": "Pres C/90",
}


def _normalize_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _parse_numeric(value: str) -> float | None:
    text = value.strip()
    if not text or text == "-" or text.lower() == "unknown":
        return None

    text = text.replace(",", "")

    if text.startswith("£") and "p/w" in text:
        compact = text.removeprefix("£").replace("p/w", "").strip()
        suffix = compact[-1:] if compact else ""
        amount = compact[:-1] if suffix in {"K", "M"} else compact
        try:
            number = float(amount)
        except ValueError:
            return None
        if suffix == "K":
            return number * 1_000
        if suffix == "M":
            return number * 1_000_000
        return number

    if text.startswith("£") and " - " in text:
        low, _, high = text.partition(" - ")
        low_val = _parse_numeric(low)
        high_val = _parse_numeric(high)
        if low_val is not None and high_val is not None:
            return (low_val + high_val) / 2
        return low_val if low_val is not None else high_val

    if text.startswith("£"):
        try:
            return float(text.removeprefix("£"))
        except ValueError:
            return None

    if text.endswith("%"):
        try:
            return float(text.removesuffix("%"))
        except ValueError:
            return None

    try:
        return float(text)
    except ValueError:
        return None


def _split_player_name(player_cell: str) -> str:
    primary, _, _rest = player_cell.partition(" - ")
    return primary.strip()


def _split_club_name(club_cell: str) -> str:
    primary, _, _rest = club_cell.partition(" - ")
    return primary.strip()


def _read_players_table(players_html_path: Path) -> list[dict[str, str]]:
    html = players_html_path.read_text(encoding="utf-8")

    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", html, flags=re.IGNORECASE | re.DOTALL)
    if not rows:
        return []

    header_cells = re.findall(
        r"<th[^>]*>(.*?)</th>",
        rows[0],
        flags=re.IGNORECASE | re.DOTALL,
    )
    headers = [
        re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", "", cell))).strip() for cell in header_cells
    ]
    headers = [_COLUMN_ALIASES.get(header, header) for header in headers]

    table_rows: list[dict[str, str]] = []
    for row in rows[1:]:
        data_cells = re.findall(
            r"<td[^>]*>(.*?)</td>",
            row,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if len(data_cells) != len(headers):
            continue
        values = [
            re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", "", cell))).strip()
            for cell in data_cells
        ]
        table_rows.append(dict(zip(headers, values, strict=True)))

    return table_rows


@dataclass(frozen=True)
class Player:
    player_id: str
    name: str
    club_name: str
    nationality: str
    position: str
    rec: str
    inf: str
    ability: str
    potential: str
    wage: str
    transfer_value: str
    metrics: dict[str, str]
    numeric_metrics: dict[str, float]


@dataclass(frozen=True)
class Club:
    club_id: str
    name: str
    country: str
    league: str | None


class FootballCatalog:
    _POSITION_ALIASES = {
        # Goalkeeper roles
        "goalkeeper": ["gk"],
        "keeper": ["gk"],
        "sweeper keeper": ["gk"],
        "sweeper-keeper": ["gk"],
        # Full-back / wing-back roles
        "wing back": ["wb"],
        "wingback": ["wb"],
        "full back": ["d (l)", "d (r)", "wb"],
        "fullback": ["d (l)", "d (r)", "wb"],
        "inverted wing back": ["wb", "d (l)", "d (r)"],
        "inverted wingback": ["wb", "d (l)", "d (r)"],
        "inverted full back": ["d (l)", "d (r)", "wb"],
        "inverted fullback": ["d (l)", "d (r)", "wb"],
        "complete wing back": ["wb"],
        "complete wingback": ["wb"],
        "no nonsense full back": ["d (l)", "d (r)", "wb"],
        "no-nonsense full-back": ["d (l)", "d (r)", "wb"],
        # Centre-back roles
        "center back": ["d (c)"],
        "centre back": ["d (c)"],
        "central defender": ["d (c)"],
        "ball playing defender": ["d (c)"],
        "ball-playing defender": ["d (c)"],
        "no nonsense centre back": ["d (c)"],
        "no-nonsense centre-back": ["d (c)"],
        "wide centre back": ["d (c)", "d (l)", "d (r)"],
        "wide center back": ["d (c)", "d (l)", "d (r)"],
        "libero": ["d (c)", "dm"],
        # Defensive midfield roles
        "defensive midfielder": ["dm"],
        "deep lying playmaker": ["dm", "m (c)"],
        "deep-lying playmaker": ["dm", "m (c)"],
        "ball winning midfielder": ["dm", "m (c)"],
        "ball-winning midfielder": ["dm", "m (c)"],
        "anchor": ["dm"],
        "half back": ["dm"],
        "half-back": ["dm"],
        "regista": ["dm", "m (c)"],
        "roaming playmaker": ["dm", "m (c)"],
        "segundo volante": ["dm"],
        # Central midfield roles
        "central midfielder": ["m (c)"],
        "box to box midfielder": ["m (c)"],
        "box-to-box midfielder": ["m (c)"],
        "advanced playmaker": ["m (c)", "am (c)"],
        "mezzala": ["m (c)"],
        "carrilero": ["m (c)"],
        # Wide midfield / winger roles
        "wide midfielder": ["m (l)", "m (r)", "am (l)", "am (r)"],
        "winger": ["am (l)", "am (r)", "m (l)", "m (r)"],
        "defensive winger": ["m (l)", "m (r)", "am (l)", "am (r)"],
        "wide playmaker": ["m (l)", "m (r)", "am (l)", "am (r)"],
        "inverted winger": ["am (l)", "am (r)", "m (l)", "m (r)"],
        "inside forward": ["am (l)", "am (r)", "st"],
        "wide target forward": ["am (l)", "am (r)", "st"],
        "raumdeuter": ["am (l)", "am (r)", "st"],
        # Attacking midfield / striker roles
        "attacking midfielder": ["am (c)", "am"],
        "shadow striker": ["am (c)", "st"],
        "trequartista": ["am (c)", "am (l)", "am (r)", "st"],
        "enganche": ["am (c)"],
        "striker": ["st"],
        "forward": ["st"],
        "advanced forward": ["st"],
        "target forward": ["st"],
        "poacher": ["st"],
        "complete forward": ["st"],
        "pressing forward": ["st"],
        "false nine": ["st", "am (c)"],
        "false 9": ["st", "am (c)"],
        "deep lying forward": ["st", "am (c)"],
        "deep-lying forward": ["st", "am (c)"],
    }

    def __init__(
        self,
        players_html_path: Path | None = None,
        input_data_dir: Path | None = None,
    ) -> None:
        root = Path(__file__).resolve().parents[2]

        if players_html_path is not None:
            html_files = [players_html_path]
        else:
            data_dir = input_data_dir or root / "input_data"
            html_files = sorted(data_dir.glob("*.html"))

        table_rows: list[dict[str, str]] = []
        for html_file in html_files:
            table_rows.extend(_read_players_table(html_file))

        self._players = self._build_players(table_rows)
        self._clubs = self._build_clubs(self._players)
        self._metric_aliases = self._build_metric_aliases(self._players)

    def _build_players(self, table_rows: list[dict[str, str]]) -> list[Player]:
        players: list[Player] = []
        for index, row in enumerate(table_rows, start=1):
            metrics: dict[str, str] = {}
            numeric_metrics: dict[str, float] = {}
            for key, value in row.items():
                parsed = _parse_numeric(value)
                metrics[key] = value
                if parsed is not None:
                    numeric_metrics[key] = parsed

            player_name = _split_player_name(row.get("Player", "Unknown Player"))
            club_name = _split_club_name(row.get("Club", "Unknown Club"))
            player_slug = _normalize_text(player_name).replace(" ", "-") or f"player-{index}"

            players.append(
                Player(
                    player_id=f"player-{player_slug}-{index}",
                    name=player_name,
                    club_name=club_name,
                    nationality=row.get("Nat", ""),
                    position=row.get("Position", ""),
                    rec=row.get("Rec", ""),
                    inf=row.get("Inf", ""),
                    ability=row.get("Ability", ""),
                    potential=row.get("Potential", ""),
                    wage=row.get("Wage", ""),
                    transfer_value=row.get("Transfer Value", ""),
                    metrics=metrics,
                    numeric_metrics=numeric_metrics,
                )
            )

        return players

    def _build_clubs(self, players: list[Player]) -> list[Club]:
        clubs_by_name: dict[str, Club] = {}
        for player in players:
            club_key = _normalize_text(player.club_name)
            if club_key in clubs_by_name:
                continue
            club_id = f"club-{club_key.replace(' ', '-') or 'unknown'}"
            clubs_by_name[club_key] = Club(
                club_id=club_id,
                name=player.club_name,
                country="",
                league=None,
            )

        return list(clubs_by_name.values())

    def _build_metric_aliases(self, players: list[Player]) -> dict[str, set[str]]:
        aliases: dict[str, set[str]] = {}
        all_headers: set[str] = set()
        for player in players:
            all_headers.update(player.metrics.keys())

        for header in all_headers:
            normalized = _normalize_text(header)
            alias_set = {normalized, normalized.replace(" ", "")}
            if "/90" in header:
                base = _normalize_text(header.replace("/90", " per 90"))
                alias_set.add(base)
            if "%" in header:
                base = _normalize_text(header.replace("%", " percent"))
                alias_set.add(base)

            # Manual aliases for common football phrasing.
            if header == "Shot %":
                alias_set.update(
                    {
                        "shot percentage",
                        "shot percent",
                        "shot accuracy",
                        "shooting",
                        "shooting accuracy",
                    }
                )
            if header == "Crs A/90":
                alias_set.update(
                    {
                        "crosses attempted per 90",
                        "crosses per 90",
                        "crosses attempted",
                        "crossing",
                        "crosses",
                    }
                )
            if header == "Pr passes/90":
                alias_set.update(
                    {
                        "progressive passes per 90",
                        "progressive passes",
                        "progressive pass per 90",
                    }
                )
            if header == "Tck/90":
                alias_set.update(
                    {
                        "tackles per 90",
                        "tackles",
                        "tackling per 90",
                        "tackling",
                    }
                )
            if header == "Tck R":
                alias_set.update(
                    {
                        "tackle completion",
                        "tackle success",
                        "tackle rate",
                        "tackling",
                    }
                )
            if header == "Hdrs W/90":
                alias_set.update(
                    {
                        "headers won per 90",
                        "headers won",
                        "aerial won per 90",
                        "aerial duels won",
                        "aerial wins per 90",
                        "headers",
                        "heading",
                    }
                )
            if header == "Int/90":
                alias_set.update({"interceptions per 90", "interceptions"})
            if header == "Poss Won/90":
                alias_set.update(
                    {
                        "possession won per 90",
                        "possession won",
                        "possessions won per 90",
                        "ball recoveries per 90",
                        "ball recoveries",
                    }
                )
            if header == "Poss Lost/90":
                alias_set.update(
                    {
                        "possession lost per 90",
                        "possession lost",
                        "possessions lost per 90",
                    }
                )
            if header == "Pres C/90":
                alias_set.update(
                    {
                        "pressures completed per 90",
                        "successful pressures per 90",
                        "press completion per 90",
                        "successful pressing",
                    }
                )
            if header == "Pres A/90":
                alias_set.update(
                    {
                        "pressures attempted per 90",
                        "pressures per 90",
                        "pressing attempts per 90",
                        "pressing per 90",
                    }
                )
            if header == "K Ps/90":
                alias_set.update({"key passes per 90", "key passes"})
            if header == "xG/90":
                alias_set.update(
                    {
                        "expected goals per 90",
                        "xg per 90",
                        "expected goals",
                        "xg",
                    }
                )
            if header == "Gls/90":
                alias_set.update(
                    {
                        "goals per 90",
                        "goals scored per 90",
                        "goals per game",
                        "scoring rate",
                    }
                )
            if header == "Shot/90":
                alias_set.update({"shots per 90", "shots", "shooting", "shooting accuracy"})
            if header == "Gls":
                alias_set.update({"goals", "total goals"})
            if header == "Ast":
                alias_set.update({"assists", "total assists"})
            if header == "Mins":
                alias_set.update(
                    {
                        "minutes",
                        "minutes played",
                        "mins",
                    }
                )

            aliases[header] = alias_set

        return aliases

    def _infer_position(self, query: str) -> str | None:
        normalized = _normalize_text(query)
        matched: list[tuple[str, list[str]]] = []
        for role_name, aliases in self._POSITION_ALIASES.items():
            if role_name in normalized:
                matched.append((role_name, aliases))

        if not matched:
            return None

        # Prefer longer phrase matches (e.g. "false nine") while still
        # allowing compatible overlaps (e.g. "wing back" and "inverted wing back").
        matched.sort(key=lambda item: len(item[0]), reverse=True)
        merged_terms: list[str] = []
        seen_terms: set[str] = set()
        for _role_name, aliases in matched:
            for alias in aliases:
                if alias in seen_terms:
                    continue
                seen_terms.add(alias)
                merged_terms.append(alias)

        return "|".join(merged_terms)

    def _resolve_requested_metrics(self, prompt: str) -> list[str]:
        normalized_prompt = _normalize_text(prompt)
        requested: list[str] = []
        for header, aliases in self._metric_aliases.items():
            if any(alias and alias in normalized_prompt for alias in aliases):
                requested.append(header)
        return requested

    def _prefer_low(self, prompt: str) -> bool:
        normalized = _normalize_text(prompt)
        return any(token in normalized for token in ["low", "lower", "min", "minimum", "least"])

    def _match_position(self, player: Player, position: str | None) -> bool:
        if not position:
            return True
        terms = [part.strip().lower() for part in position.split("|") if part.strip()]
        player_position = player.position.lower()
        return any(term in player_position for term in terms)

    def _rank_player(
        self,
        player: Player,
        metric_names: list[str],
        prefer_low: bool,
    ) -> tuple[float, dict[str, float]] | None:
        values: dict[str, float] = {}
        for metric in metric_names:
            if metric not in player.numeric_metrics:
                return None
            values[metric] = player.numeric_metrics[metric]

        if not metric_names:
            return 0.0, {}

        normalized_scores: list[float] = []
        for metric in metric_names:
            population_values = [
                p.numeric_metrics[metric] for p in self._players if metric in p.numeric_metrics
            ]
            if not population_values:
                continue
            min_value = min(population_values)
            max_value = max(population_values)
            current_value = values[metric]
            if max_value == min_value:
                metric_score = 1.0
            else:
                raw = (current_value - min_value) / (max_value - min_value)
                metric_score = 1.0 - raw if prefer_low else raw
            normalized_scores.append(metric_score)

        if not normalized_scores:
            return None

        return sum(normalized_scores) / len(normalized_scores), values

    def search_players(
        self,
        query: str = "",
        position: str | None = None,
        country: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, object]]:
        normalized_query = query.strip().lower()
        inferred_position = self._infer_position(query)
        normalized_position = position.strip().lower() if position else inferred_position
        normalized_country = country.strip().lower() if country else None
        results: list[dict[str, object]] = []

        for player in self._players:
            if (
                normalized_query
                and normalized_query
                not in " ".join(
                    [player.name, player.club_name, player.nationality, player.position]
                ).lower()
            ):
                continue
            if normalized_position and not self._match_position(player, normalized_position):
                continue
            if normalized_country and player.nationality.lower() != normalized_country:
                continue
            results.append(asdict(player))
            if len(results) >= limit:
                break

        return results

    def rank_players_by_preferences(
        self,
        prompt: str,
        position: str | None = None,
        country: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, object]]:
        metrics = self._resolve_requested_metrics(prompt)
        prefer_low = self._prefer_low(prompt)
        resolved_position = position.strip().lower() if position else self._infer_position(prompt)
        normalized_country = country.strip().lower() if country else None

        ranked: list[dict[str, object]] = []
        for player in self._players:
            if resolved_position and not self._match_position(player, resolved_position):
                continue
            if normalized_country and player.nationality.lower() != normalized_country:
                continue

            scored = self._rank_player(player, metrics, prefer_low)
            if scored is None:
                continue
            score, metric_values = scored
            ranked.append(
                {
                    "score": round(score, 4),
                    "matched_metrics": metric_values,
                    "requested_metrics": metrics,
                    "player": asdict(player),
                }
            )

        ranked.sort(key=lambda item: float(item["score"]), reverse=True)
        if metrics:
            return ranked[:limit]

        # Fallback for generic prompts with no explicit metric mention.
        text_prompt = _normalize_text(prompt)
        generic = []
        for item in ranked:
            player = item["player"]
            search_blob = _normalize_text(
                " ".join(
                    [
                        str(player.get("name", "")),
                        str(player.get("club_name", "")),
                        str(player.get("nationality", "")),
                        str(player.get("position", "")),
                    ]
                )
            )
            if text_prompt and text_prompt not in search_blob:
                continue
            generic.append(item)
        return generic[:limit]

    def get_player_profile(self, player_id: str) -> dict[str, object] | None:
        for player in self._players:
            if player.player_id == player_id:
                return asdict(player)
        return None

    def list_clubs(self, country: str | None = None, limit: int = 20) -> list[dict[str, object]]:
        normalized_country = country.strip().lower() if country else None
        results: list[dict[str, object]] = []

        for club in self._clubs:
            if normalized_country and club.country.lower() != normalized_country:
                continue
            results.append(asdict(club))
            if len(results) >= limit:
                break

        return results

    def get_club_squad(self, club_id: str) -> list[dict[str, object]]:
        club = next((c for c in self._clubs if c.club_id == club_id), None)
        if club is None:
            return []
        return [asdict(player) for player in self._players if player.club_name == club.name]

    def list_available_columns(self) -> list[dict[str, object]]:
        columns: dict[str, dict[str, object]] = {}
        for player in self._players:
            for column_name, raw_value in player.metrics.items():
                entry = columns.setdefault(
                    column_name,
                    {"column": column_name, "numeric": False, "example": raw_value},
                )
                if column_name in player.numeric_metrics:
                    entry["numeric"] = True

        return sorted(columns.values(), key=lambda item: str(item["column"]))
