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
ENTER_HISTORY = OUTPUT_DIR / "enter_history.jsonl"
ACTION_LOG = OUTPUT_DIR / "action_log.jsonl"        # append-only audit trail
ACTION_LOG_MD = OUTPUT_DIR / "action_log.md"        # readable view of the above

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
        items.append({"date": c["date"], "home": home, "away": away,
                      "from": p.get("enter"), "to": c["enter"], "team": moved,
                      "elo_from": round(old, 1), "elo_to": round(new, 1),
                      "reason": _news_reason(moved)})
    return items


def _action_line(it: dict) -> str:
    detail = f"{it['team']} nieuws ({it['elo_from']:+.0f}→{it['elo_to']:+.0f} Elo)"
    if it["reason"]:
        detail += f": {it['reason']}"
    return (f"{it['home']} – {it['away']} ({it['date']}): vul **{it['to']}** in "
            f"(was {it['from']}) — {detail}")


def _log_actions(items: list[dict]) -> None:
    """Append every news-driven entry change to a permanent local audit trail and
    re-render the readable view. So you keep a dated record of why each pick moved,
    not just the latest changes.md (overwritten each run)."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().isoformat(timespec="seconds")
    with open(ACTION_LOG, "a") as f:
        for it in items:
            f.write(json.dumps({"logged_at": stamp, **it}, ensure_ascii=False) + "\n")
    _render_action_log()


def _render_action_log() -> None:
    if not ACTION_LOG.exists():
        return
    rows = [json.loads(line) for line in ACTION_LOG.read_text().splitlines()]
    lines = ["# Pool action log — why each pick moved", "",
             "_Append-only, local. Every news-driven change to your entered score, "
             "with the reason. Newest first._", ""]
    for r in reversed(rows):
        when = r.get("logged_at", "")[:16].replace("T", " ")
        detail = f"{r['team']} {r['elo_from']:+.0f}→{r['elo_to']:+.0f} Elo"
        if r.get("reason"):
            detail += f" ({r['reason']})"
        lines.append(f"- **{when}** — {r['home']} – {r['away']} ({r['date']}): "
                     f"{r['from']} → {r['to']}. {detail}")
    ACTION_LOG_MD.write_text("\n".join(lines) + "\n")


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


def _log_enter(rows: list[dict]) -> None:
    """Append this run's entered scores, so the pool track measures what you
    actually fill in (the expected-points-optimal ENTER), not the public modal."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().isoformat(timespec="seconds")
    with open(ENTER_HISTORY, "a") as f:
        for r in rows:
            f.write(json.dumps({"at": stamp, "date": r["date"], "home": r["home"],
                                "away": r["away"], "enter": r["enter"]},
                               ensure_ascii=False) + "\n")


def score_pool(results_2026, rubric: dict) -> dict | None:
    """Exact hits + total pool points of the last pre-match ENTER per played match.

    Uses the entered (expected-points-optimal) score, oriented to the result's
    home/away. Only counts matches that had a logged ENTER before kickoff, so the
    track starts the day logging began and reflects your real pool entries.
    """
    if not ENTER_HISTORY.exists():
        return None
    latest: dict[tuple[str, str], str] = {}
    for line in ENTER_HISTORY.read_text().splitlines():
        r = json.loads(line)
        latest[(r["home"], r["away"])] = r["enter"]   # later lines overwrite
    exact = pts = n = 0
    for res in results_2026.itertuples(index=False):
        direct = latest.get((res.home_team, res.away_team))
        swap = latest.get((res.away_team, res.home_team))
        if direct is not None:
            eh, ea = (int(x) for x in direct.split("-"))
        elif swap is not None:
            ea, eh = (int(x) for x in swap.split("-"))  # logged with teams swapped
        else:
            continue
        ah, aa = int(res.home_score), int(res.away_score)
        pts += scoring.points(eh, ea, ah, aa, rubric)
        n += 1
        if (eh, ea) == (ah, aa):
            exact += 1
    return {"matches": n, "exact": exact, "points": pts} if n else None


def run(weights: dict, n_sims: int | None = None) -> bool:
    """Run the private pass; return True if predictions changed since last run."""
    from .cli import _prepare
    df, outcome, goal_model, ratings, forms, played, metrics = _prepare(weights)
    preds = predict_remaining(outcome, goal_model, ratings, forms, weights, played)
    sim = TournamentSim(goal_model, ratings, weights, played)
    sim_df = sim.run(n_sims or int(weights["simulation"]["n_sims"]))

    rows = _enrich(preds, goal_model, ratings, weights)
    _log_enter(rows)
    rubric = weights.get("pool_scoring", scoring.DEFAULT_RUBRIC)
    pool = score_pool(data_io.world_cup_2026_results(df), rubric)
    cur = _snapshot(rows, sim_df, _news_adjustments(weights))
    prev = json.loads(PREV_JSON.read_text()) if PREV_JSON.exists() else {}
    changes = _diff(prev, cur)
    actions = _action_items(prev, cur)
    if actions:
        _log_actions(actions)   # permanent audit trail of why each pick moved

    # full private report — "enter" is the expected-points-optimal score to fill in
    today = dt.date.today().isoformat()
    lines = [f"# My private predictions — {today}", "",
             "_Run with your weights. Not committed. **Enter** = the score that "
             "maximises expected points under your pool's rubric._", ""]
    if pool:
        lines += [f"_Pool track so far: {pool['exact']}/{pool['matches']} exact, "
                  f"{pool['points']} pts (your entered scores vs results)._", ""]
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
            cl += [f"- {_action_line(a)}" for a in actions]
            cl += ["", "## Overige wijzigingen", ""]
        cl += [f"- {c}" for c in changes]
        cl += ["", "Full list: PREDICTIONS.local.md"]
        CHANGES_MD.write_text("\n".join(cl))
    elif CHANGES_MD.exists():
        CHANGES_MD.unlink()  # no real changes -> no mail trigger

    PREV_JSON.write_text(json.dumps(cur, ensure_ascii=False))
    msg = (f"private run: {len(changes)} change line(s), "
           f"{len(actions)} news-driven action(s)")
    if pool:
        msg += f"; pool {pool['exact']}/{pool['matches']} exact, {pool['points']} pts"
    print(msg + f"; wrote {PRIVATE_MD.name}")
    return has_changes
