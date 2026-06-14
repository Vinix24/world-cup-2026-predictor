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
from .config import OUTPUT_DIR, ROOT
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


def _snapshot(rows: list[dict], sim_df) -> dict:
    matches = {f"{r['home']}|{r['away']}": r for r in rows}
    champ = {r.team: round(float(r.p_champion), 4)
             for r in sim_df.itertuples(index=False)}
    return {"matches": matches, "champions": champ}


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
    cur = _snapshot(rows, sim_df)
    prev = json.loads(PREV_JSON.read_text()) if PREV_JSON.exists() else {}
    changes = _diff(prev, cur)

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
        cl += [f"- {c}" for c in changes]
        cl += ["", "Full list: PREDICTIONS.local.md"]
        CHANGES_MD.write_text("\n".join(cl))
    elif CHANGES_MD.exists():
        CHANGES_MD.unlink()  # no real changes -> no mail trigger

    PREV_JSON.write_text(json.dumps(cur, ensure_ascii=False))
    print(f"private run: {len(changes)} change line(s); wrote {PRIVATE_MD.name}")
    return has_changes
