"""Your private prediction pass + a day-to-day change report.

Runs the pipeline with YOUR weights (weights.local.yaml included), writes a
gitignored PREDICTIONS.local.md, and diffs against yesterday's private run.
The diff (output/changes.md) is what gets mailed, so you only hear about it
when something you must re-enter in your pool actually moved.

Nothing here touches the committed/public artifacts or the public
history.jsonl — your edge stays local.
"""
from __future__ import annotations

import datetime as dt
import json

from . import data_io, scoring, schedule
from .config import NEWS_DIR, OUTPUT_DIR, ROOT
from .plugins.injuries import InjuryPlugin
from .predict import _advantage, predict_remaining
from .sim import TournamentSim

PRIVATE_MD = ROOT / "PREDICTIONS.local.md"
PREV_JSON = OUTPUT_DIR / "private_prev.json"
CHANGES_MD = OUTPUT_DIR / "changes.md"

PROB_THRESHOLD = 0.05   # report a match if its top probability moved this much
CHAMP_THRESHOLD = 0.02  # report a team if its title chance moved this much


def _tip(row: dict) -> str:
    probs = {"1": row["p_home"], "X": row["p_draw"], "2": row["p_away"]}
    return max(probs, key=probs.get)


def _enrich(preds, goal_model, ratings, weights) -> list[dict]:
    """Add the expected-points-optimal scoreline (what to enter) per match."""
    rubric = weights.get("pool_scoring", scoring.DEFAULT_RUBRIC)
    home_adv = float(weights["ratings"]["home_advantage"])
    rows = []
    for r in preds.itertuples(index=False):
        adv = _advantage(r.home, r.away, home_adv)
        lam_h, lam_a = goal_model.lambdas(ratings[r.home], ratings[r.away], home_adv=adv)
        eh, ea, ev = scoring.optimal_prediction(lam_h, lam_a, rubric)
        rows.append({"date": r.date, "home": r.home, "away": r.away,
                     "p_home": r.p_home, "p_draw": r.p_draw, "p_away": r.p_away,
                     "likely": r.likely_score, "enter": f"{eh}-{ea}",
                     "ev": round(ev, 1)})
    return rows


def _snapshot(rows: list[dict], sim_df, news_adj: dict) -> dict:
    matches = {f"{r['home']}|{r['away']}": r for r in rows}
    champ = {r.team: round(float(r.p_champion), 4)
             for r in sim_df.itertuples(index=False)}
    return {"matches": matches, "champions": champ, "news_adj": news_adj}


def _news_adjustments(weights: dict) -> dict[str, float]:
    """Per-team Elo nudge from injuries/suspensions only — the news signal.

    Climate and odds are not news, so the action alert keys on the injuries
    plugin alone (weighted as the engine uses it).
    """
    w = float(weights.get("plugin_weights", {}).get("injuries", 0.0))
    if w == 0.0:
        return {}
    raw = InjuryPlugin().adjustments(schedule.all_teams(), weights)
    return {t: round(w * pts, 1) for t, pts in raw.items()}


def _news_reason(team: str) -> str:
    """Short readable summary of a team's current injury/suspension news."""
    path = NEWS_DIR / f"{team.lower().replace(' ', '_')}.json"
    if not path.exists():
        return ""
    try:
        report = json.loads(path.read_text())
    except (json.JSONDecodeError, ValueError):
        return ""
    out = [i.get("player", "?") for i in report.get("injuries", [])
           if i.get("status") == "out"]
    doubt = [i.get("player", "?") for i in report.get("injuries", [])
             if i.get("status") == "doubtful"]
    susp = [s.get("player", "?") if isinstance(s, dict) else str(s)
            for s in report.get("suspensions", [])]
    bits = []
    if out:
        bits.append("out: " + ", ".join(out[:3]) + ("…" if len(out) > 3 else ""))
    if susp:
        bits.append("geschorst: " + ", ".join(susp[:3]))
    if doubt and not out:
        bits.append("twijfel: " + ", ".join(doubt[:3]))
    return "; ".join(bits)


def _action_items(prev: dict, cur: dict) -> list[str]:
    """Upcoming matches whose ENTER score moved *and* a participating team's
    news adjustment moved since the last run — the pool entries to re-fill now.

    `cur['matches']` only holds not-yet-played matches (predict_remaining), so
    decided matches are out of scope by construction.
    """
    if not prev:
        return []
    pm, cm = prev.get("matches", {}), cur["matches"]
    pa, ca = prev.get("news_adj", {}), cur.get("news_adj", {})
    items = []
    for key, c in cm.items():
        p = pm.get(key)
        if p is None or p.get("enter") == c["enter"]:
            continue  # brand-new match, or the entry did not move
        home, away = c["home"], c["away"]
        moved = next((t for t in (home, away)
                      if round(ca.get(t, 0.0) - pa.get(t, 0.0), 1) != 0.0), None)
        if moved is None:
            continue  # entry moved, but not because of news
        old, new = pa.get(moved, 0.0), ca.get(moved, 0.0)
        detail = f"{moved} nieuws ({old:+.0f}→{new:+.0f} Elo)"
        reason = _news_reason(moved)
        if reason:
            detail += f": {reason}"
        items.append(f"{home} – {away} ({c['date']}): vul **{c['enter']}** in "
                     f"(was {p.get('enter')}) — {detail}")
    return items


def _diff(prev: dict, cur: dict) -> list[str]:
    if not prev:
        return ["First private run — baseline stored, no diff yet."]
    out = []
    pm, cm = prev.get("matches", {}), cur["matches"]
    for key, c in cm.items():
        p = pm.get(key)
        label = f"{c['home']} – {c['away']} ({c['date']})"
        if p is None:
            out.append(f"NEW {label}: enter {c['enter']} "
                       f"(EV {c['ev']}, {_tip(c)} {c['p_home']:.0%}/{c['p_draw']:.0%}/{c['p_away']:.0%})")
            continue
        enter_changed = p.get("enter") != c["enter"]
        moved = max(abs(c[k] - p[k]) for k in ("p_home", "p_draw", "p_away"))
        if enter_changed:
            out.append(f"ENTER {label}: {p.get('enter')} -> {c['enter']} "
                       f"(EV {c['ev']}; {_tip(c)} {c['p_home']:.0%}/{c['p_draw']:.0%}/{c['p_away']:.0%})")
        elif moved >= PROB_THRESHOLD:
            out.append(f"{label}: enter stays {c['enter']}, "
                       f"odds {p['p_home']:.0%}/{p['p_draw']:.0%}/{p['p_away']:.0%}"
                       f" -> {c['p_home']:.0%}/{c['p_draw']:.0%}/{c['p_away']:.0%}")
    pc, cc = prev.get("champions", {}), cur["champions"]
    champ_lines = []
    for team, c in sorted(cc.items(), key=lambda kv: -kv[1])[:12]:
        p = pc.get(team, 0.0)
        if abs(c - p) >= CHAMP_THRESHOLD:
            champ_lines.append(f"  {team}: {p:.1%} -> {c:.1%}")
    if champ_lines:
        out.append("Title-chance shifts:\n" + "\n".join(champ_lines))
    return out


def run(weights: dict, n_sims: int | None = None) -> bool:
    """Run the private pass; return True if predictions changed since last run."""
    from .cli import _prepare
    df, outcome, goal_model, ratings, forms, played, metrics = _prepare(weights)
    preds = predict_remaining(outcome, goal_model, ratings, forms, weights, played)
    sim = TournamentSim(goal_model, ratings, weights, played)
    sim_df = sim.run(n_sims or int(weights["simulation"]["n_sims"]))

    rows = _enrich(preds, goal_model, ratings, weights)
    cur = _snapshot(rows, sim_df, _news_adjustments(weights))
    prev = json.loads(PREV_JSON.read_text()) if PREV_JSON.exists() else {}
    changes = _diff(prev, cur)
    actions = _action_items(prev, cur)

    # full private report — "enter" is the expected-points-optimal score to fill in
    today = dt.date.today().isoformat()
    lines = [f"# My private predictions — {today}", "",
             "_Run with your weights. Not committed. **Enter** = the score that "
             "maximises expected points under your pool's rubric._", ""]
    lines += ["## Tournament outlook (top 8)", ""]
    for r in sim_df.head(8).itertuples(index=False):
        lines.append(f"- {r.team}: champion {r.p_champion:.1%}, final {r.p_F:.1%}")
    lines += ["", "## Upcoming matches", "",
              "| Date | Match | ENTER | exp. pts | 1/X/2 | modal |",
              "|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['date']} | {r['home']} – {r['away']} | **{r['enter']}** "
                     f"| {r['ev']} | {r['p_home']:.0%}/{r['p_draw']:.0%}/{r['p_away']:.0%} "
                     f"| {r['likely']} |")
    PRIVATE_MD.write_text("\n".join(lines))

    has_changes = bool(changes) and changes != ["First private run — baseline stored, no diff yet."]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if has_changes:
        cl = [f"# What changed in your predictions — {today}", ""]
        if actions:
            cl += ["## ⚠️ ACTIE — poule bijstellen (nieuws verschoof je invoer)", ""]
            cl += [f"- {a}" for a in actions]
            cl += ["", "## Overige wijzigingen", ""]
        cl += [f"- {c}" for c in changes]
        cl += ["", "Full list: PREDICTIONS.local.md"]
        CHANGES_MD.write_text("\n".join(cl))
    elif CHANGES_MD.exists():
        CHANGES_MD.unlink()  # no real changes -> no mail trigger

    PREV_JSON.write_text(json.dumps(cur, ensure_ascii=False))
    print(f"private run: {len(changes)} change line(s), "
          f"{len(actions)} news-driven action(s); wrote {PRIVATE_MD.name}")
    return has_changes
