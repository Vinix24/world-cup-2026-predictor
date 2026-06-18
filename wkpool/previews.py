"""Forward-looking match-preview scraper via Perplexity (optional feature).

Where the injury feed (news.py) looks backward at what already happened, this
looks forward: for each upcoming fixture it gathers the aggregate press/pundit
preview consensus — who is favored, by how much, and the reasons. Structured
JSON per match feeds the previews plugin, which stays OFF until `wkpool analyze`
shows the signal earns its keep on results.

Needs PERPLEXITY_API_KEY. Without it this is a graceful no-op.
"""
from __future__ import annotations

import datetime as dt
import json
import os

import requests

from . import schedule
from .config import PREVIEWS_DIR, ensure_dirs

API_URL = "https://api.perplexity.ai/chat/completions"
MODEL = "sonar-pro"

SYSTEM_PROMPT = """\
You are a data-extraction agent for a World Cup 2026 prediction model. For ONE
upcoming match you search recent preview and punditry coverage (last 5 days)
across multiple outlets and return ONLY valid JSON matching exactly this schema
— no prose, no markdown:
{
  "home": string,
  "away": string,
  "as_of": string (ISO date),
  "consensus": {"p_home": number, "p_draw": number, "p_away": number},
  "favored": "home"|"draw"|"away",
  "confidence": "high"|"medium"|"low",
  "reasons": [{"team": "home"|"away",
               "factor": "form"|"tactics"|"motivation"|"injuries"|"homefield"|"other",
               "detail": string}],
  "n_sources": number,
  "caveats": string
}
Rules: p_home + p_draw + p_away must sum to ~1.0 and reflect the AGGREGATE view
across the previews you actually found, not your own opinion. Base it on what
pundits and preview articles predict. If coverage is thin, set confidence "low"
and n_sources low. Never invent sources. An empty reasons array is allowed."""


def _slug(home: str, away: str) -> str:
    return f"{home}__{away}".lower().replace(" ", "_")


def _extract_json(text: str) -> dict:
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("no JSON object in response")
    return json.loads(text[start:end + 1])


def upcoming_fixtures(played: dict, today: dt.date,
                      days_ahead: int = 2) -> list[tuple[str, str, str]]:
    """Group fixtures not yet played whose kickoff is within the window."""
    out = []
    for date_str, home, away in schedule.GROUP_FIXTURES:
        if (home, away) in played or (away, home) in played:
            continue
        d = dt.date.fromisoformat(date_str)
        if 0 <= (d - today).days <= days_ahead:
            out.append((date_str, home, away))
    return out


def fetch_match(home: str, away: str, date_str: str, api_key: str,
                today: dt.date) -> dict:
    user = (f"Upcoming FIFA World Cup 2026 match: {home} vs {away} on {date_str}. "
            f"Today is {today.isoformat()}. Gather the aggregate press and pundit "
            f"preview consensus: predicted result, who is favored and the reasons.")
    payload = {
        "model": MODEL, "temperature": 0.1, "max_tokens": 1500,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user},
        ],
    }
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = requests.post(API_URL, json=payload, headers=headers, timeout=120)
    resp.raise_for_status()
    text = resp.json()["choices"][0]["message"]["content"]
    try:
        return _extract_json(text)
    except (ValueError, json.JSONDecodeError):
        payload["messages"].append({"role": "assistant", "content": text})
        payload["messages"].append({"role": "user", "content":
                                    "That was not valid JSON. Return ONLY the JSON object."})
        resp = requests.post(API_URL, json=payload, headers=headers, timeout=120)
        resp.raise_for_status()
        return _extract_json(resp.json()["choices"][0]["message"]["content"])


def fetch_all(played: dict, days_ahead: int = 2) -> int:
    """Fetch previews for upcoming fixtures in the window; returns matches done."""
    api_key = os.environ.get("PERPLEXITY_API_KEY", "").strip()
    if not api_key:
        print("PERPLEXITY_API_KEY not set — skipping previews fetch")
        return 0
    ensure_dirs()
    today = dt.date.today()
    fixtures = upcoming_fixtures(played, today, days_ahead)
    if not fixtures:
        print("no upcoming fixtures in window — skipping previews fetch")
        return 0
    done = 0
    for date_str, home, away in fixtures:
        path = PREVIEWS_DIR / f"{_slug(home, away)}.json"
        try:
            rep = fetch_match(home, away, date_str, api_key, today)
            rep.setdefault("home", home)
            rep.setdefault("away", away)
            rep.setdefault("as_of", today.isoformat())
            path.write_text(json.dumps(rep, indent=2, ensure_ascii=False))
            c = rep.get("consensus", {})
            print(f"  {home} vs {away}: favored={rep.get('favored', '?')} "
                  f"({c.get('p_home', '?')}/{c.get('p_draw', '?')}/{c.get('p_away', '?')}), "
                  f"{rep.get('n_sources', '?')} sources")
            done += 1
        except Exception as exc:  # one match failing must not kill the run
            print(f"  {home} vs {away}: preview fetch failed ({exc})")
    return done
