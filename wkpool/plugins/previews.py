"""Press-consensus plugin — a qualitative preview signal on top of the market.

Reads data/previews/<home>__<away>.json (see previews.py): the aggregate press
view per upcoming match. Nudges the favored team's Elo up and the underdog's
down, scaled by how strongly the press leans (p_home - p_away) and how confident
the coverage is. OFF by default (weight 0.0); turn it up only once `wkpool
analyze` shows the signal earns its keep on results.

Odds capture the market consensus quantitatively; this captures what the press
reasons qualitatively (tactics, motivation) on top. The file format is the
contract, so you can populate it by hand or with your own scraper too.
"""
from __future__ import annotations

import datetime as dt
import json

from ..config import PREVIEWS_DIR

_CONFIDENCE = {"high": 1.0, "medium": 0.6, "low": 0.3}


class PreviewsPlugin:
    name = "previews"

    def adjustments(self, teams: list[str], weights: dict) -> dict[str, float]:
        if not PREVIEWS_DIR.is_dir():
            return {}
        cfg = weights.get("previews", {})
        blend = float(cfg.get("blend", 0))
        max_age = int(cfg.get("max_age_days", 5))
        cap = float(cfg.get("max_team_points", 0) or 0)
        if blend == 0:
            return {}
        today = dt.date.today()
        known = set(teams)
        out: dict[str, float] = {}
        for path in PREVIEWS_DIR.glob("*.json"):
            try:
                rep = json.loads(path.read_text())
            except json.JSONDecodeError:
                continue
            home, away = rep.get("home"), rep.get("away")
            if home not in known or away not in known:
                continue
            try:
                age = (today - dt.date.fromisoformat(rep.get("as_of", "1970-01-01"))).days
            except ValueError:
                continue
            if age > max_age:
                continue
            c = rep.get("consensus", {})
            try:
                ph, pa = float(c.get("p_home", 0)), float(c.get("p_away", 0))
            except (TypeError, ValueError):
                continue
            conf = _CONFIDENCE.get(str(rep.get("confidence", "low")).lower(), 0.3)
            lean = (ph - pa) * conf            # press strength, in [-1, 1]
            out[home] = out.get(home, 0.0) + blend * lean
            out[away] = out.get(away, 0.0) - blend * lean
        if cap > 0:
            out = {t: max(-cap, min(cap, v)) for t, v in out.items()}
        return {t: v for t, v in out.items() if v}
