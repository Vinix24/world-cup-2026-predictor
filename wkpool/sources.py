"""Optional extra data sources, all key-gated and degrading gracefully:

- football-data.org: a faster World Cup results feed than the martj42 CSV,
  to close the ~1-2 day lag. Key: FOOTBALL_DATA_API_KEY.
- The Odds API: outright (winner) odds -> data/odds/outright.json for the
  bookmaker-consensus plugin. Key: ODDS_API_KEY.

Without keys these are no-ops and the model runs on its public sources.
"""
from __future__ import annotations

import datetime as dt
import json
import os

import pandas as pd
import requests

from . import schedule
from .config import ODDS_DIR, ROOT, ensure_dirs

FOOTBALL_DATA_URL = "https://api.football-data.org/v4/competitions/WC/matches"
ODDS_API_URL = ("https://api.the-odds-api.com/v4/sports/"
                "soccer_fifa_world_cup_winner/odds")

# football-data.org names -> martj42/schedule names
_FD_ALIASES = {
    "USA": "United States",
    "Republic of Ireland": "Ireland",
    "Korea Republic": "South Korea",
    "IR Iran": "Iran",
    "Côte d'Ivoire": "Ivory Coast",
    "Czechia": "Czech Republic",
    "Türkiye": "Turkey",
    "Cabo Verde": "Cape Verde",
    "Cape Verde Islands": "Cape Verde",
    "Bosnia-Herzegovina": "Bosnia and Herzegovina",
    "Congo DR": "DR Congo",
}


def _canon(name: str) -> str:
    return _FD_ALIASES.get(name, name)


def fetch_results_fallback() -> pd.DataFrame | None:
    """Recent WC2026 results from football-data.org (faster than martj42).

    Returns a DataFrame with the same columns as the martj42 results, or None
    if no key is set or the call fails. Only finished matches are returned.
    """
    key = os.environ.get("FOOTBALL_DATA_API_KEY", "").strip()
    if not key:
        return None
    try:
        resp = requests.get(FOOTBALL_DATA_URL, headers={"X-Auth-Token": key},
                            params={"status": "FINISHED"}, timeout=60)
        resp.raise_for_status()
        matches = resp.json().get("matches", [])
    except (requests.RequestException, ValueError):
        return None

    known = set(schedule.all_teams())
    rows = []
    for m in matches:
        score = m.get("score", {}).get("fullTime", {})
        if score.get("home") is None or score.get("away") is None:
            continue
        home, away = _canon(m["homeTeam"]["name"]), _canon(m["awayTeam"]["name"])
        if home not in known or away not in known:
            # unmapped name -> skip rather than create a duplicate/garbage row
            print(f"  football-data: skipping unmapped fixture {home} vs {away}")
            continue
        rows.append({
            "date": m["utcDate"][:10],
            "home_team": home, "away_team": away,
            "home_score": int(score["home"]),
            "away_score": int(score["away"]),
            "tournament": "FIFA World Cup",
            "neutral": True,
        })
    if not rows:
        return None
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    return df


def merge_results(primary: pd.DataFrame, extra: pd.DataFrame | None) -> pd.DataFrame:
    """Add WC2026 results from `extra` not yet scored in `primary`.

    Dedup is scoped to this tournament's matches. Two nations have almost always
    met before in some friendly, so a team-pair check against the full martj42
    history (matches since 1872) would treat every WC fixture as already-known
    and silently drop the fresh result. Match on the pair within WC2026 only.
    """
    if extra is None or extra.empty:
        return primary
    wc = primary[(primary["tournament"] == "FIFA World Cup")
                 & (primary["date"] >= "2026-06-11")]
    have = {(r.home_team, r.away_team) for r in wc.itertuples(index=False)}
    new = extra[[(h, a) not in have and (a, h) not in have
                 for h, a in zip(extra["home_team"], extra["away_team"])]]
    if new.empty:
        return primary
    print(f"  +{len(new)} WC result(s) from football-data.org not yet in martj42")
    return pd.concat([primary, new], ignore_index=True).sort_values("date").reset_index(drop=True)


def fetch_outright_odds() -> int:
    """Fetch winner odds -> data/odds/outright.json. Returns teams written."""
    key = os.environ.get("ODDS_API_KEY", "").strip()
    if not key:
        print("ODDS_API_KEY not set — skipping odds fetch (odds plugin stays off)")
        return 0
    try:
        resp = requests.get(ODDS_API_URL, params={
            "apiKey": key, "regions": "eu,uk", "oddsFormat": "decimal"}, timeout=60)
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError) as exc:
        print(f"odds fetch failed ({exc})")
        return 0

    # consensus = median decimal odds across books per team
    per_team: dict[str, list[float]] = {}
    for event in data if isinstance(data, list) else []:
        for book in event.get("bookmakers", []):
            for market in book.get("markets", []):
                if market.get("key") != "outrights":
                    continue
                for oc in market.get("outcomes", []):
                    name = _canon(oc.get("name", ""))
                    price = oc.get("price")
                    if name in set(schedule.all_teams()) and isinstance(price, (int, float)):
                        per_team.setdefault(name, []).append(float(price))
    if not per_team:
        print("odds fetch returned no usable outrights")
        return 0
    consensus = {t: sorted(v)[len(v) // 2] for t, v in per_team.items()}
    ensure_dirs()
    (ODDS_DIR / "outright.json").write_text(
        json.dumps(consensus, indent=2, ensure_ascii=False))
    print(f"wrote outright odds for {len(consensus)} teams")
    return len(consensus)


def render_odds_digest() -> None:
    """Render a public ODDS.md from data/odds/outright.json, sources cited.

    The shareable market view: bookmaker-consensus title odds and the
    margin-stripped implied probability per team. How the model *weights* this
    stays private (weights.local.yaml) — only the data is published.
    """
    path = ODDS_DIR / "outright.json"
    if not path.exists():
        return
    try:
        odds = {t: float(o) for t, o in json.loads(path.read_text()).items()
                if float(o) > 1.0}
    except (json.JSONDecodeError, ValueError):
        return
    if not odds:
        return
    implied = {t: 1.0 / o for t, o in odds.items()}
    total = sum(implied.values())  # strip the overround so the field sums to 100%
    implied = {t: p / total for t, p in implied.items()}

    today = dt.date.today().isoformat()
    lines = [
        "# WK 2026 — market odds",
        "",
        f"_Auto-generated {today}. Bookmaker consensus (median across EU/UK books) "
        "to win the tournament. Decimal odds and the implied champion probability, "
        "normalised to strip the bookmaker margin._",
        "",
        "| # | Team | Decimal odds | Implied champion % |",
        "|---|---|---|---|",
    ]
    for i, (t, o) in enumerate(sorted(odds.items(), key=lambda kv: kv[1]), 1):
        lines.append(f"| {i} | {t} | {o:g} | {implied[t]:.1%} |")
    lines += [
        "",
        "_Source: The Odds API (the-odds-api.com), `soccer_fifa_world_cup_winner` "
        "market, regions eu,uk. Odds are the median bookmaker consensus; implied % "
        "is normalised to remove the overround._",
    ]
    (ROOT / "ODDS.md").write_text("\n".join(lines) + "\n")
    print(f"wrote {ROOT / 'ODDS.md'}")
