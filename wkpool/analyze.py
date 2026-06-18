"""Schommelingen-analyse: how do the predictions move day-to-day, what drives
it, and did the movement help once results came in?

Read-only over the logged prediction history and results. It proposes nothing
and changes no weights — that stays a human decision. It also appends a per-run
signal snapshot to output/signal_log.jsonl: the durable substrate a later
weight-advisor needs to reason about volatility on clean data.
"""
from __future__ import annotations

import datetime as dt
import json
from collections import defaultdict

from . import data_io, schedule
from .config import OUTPUT_DIR
from .plugins.injuries import InjuryPlugin
from .plugins.previews import PreviewsPlugin
from .predict import HISTORY, score_history

SIGNAL_LOG = OUTPUT_DIR / "signal_log.jsonl"
REPORT_MD = OUTPUT_DIR / "analysis.md"


def _toto(hs: int, as_: int) -> str:
    return "1" if hs > as_ else ("2" if as_ > hs else "X")


def _judge(seq: list[tuple[str, str]], actual: tuple[int, int] | None) -> str:
    """Did the net adjustment (first vs last prediction) help, hurt, or neither?

    seq is the distinct-consecutive list of (likely_score, toto) a match passed
    through. Compares the opening prediction with the final one against the
    actual result, on both winner (toto) and exact score.
    """
    if actual is None or len(seq) < 2:
        return ""
    ah, aa = actual
    at = _toto(ah, aa)
    exact = f"{ah}-{aa}"
    (f_ls, f_t), (l_ls, l_t) = seq[0], seq[-1]
    if (l_t == at and f_t != at) or (l_ls == exact and f_ls != exact):
        return "hielp"
    if (f_t == at and l_t != at) or (f_ls == exact and l_ls != exact):
        return "schaadde"
    return "neutraal"


def _trajectories() -> dict:
    """(home, away) -> ordered [(ts, likely_score, toto, top_prob)] from history."""
    traj: dict = defaultdict(list)
    if not HISTORY.exists():
        return traj
    for line in HISTORY.read_text().splitlines():
        r = json.loads(line)
        toto = max((("1", r["p_home"]), ("X", r["p_draw"]), ("2", r["p_away"])),
                   key=lambda kv: kv[1])[0]
        traj[(r["home"], r["away"])].append(
            (r["generated_at"], r["likely_score"], toto,
             max(r["p_home"], r["p_draw"], r["p_away"])))
    for k in traj:
        traj[k].sort()
    return traj


def _record_signal(weights: dict, n_played: int) -> None:
    teams = schedule.all_teams()
    news = InjuryPlugin().adjustments(teams, weights)
    # raw preview lean at blend=1, so the stored signal is weight-independent
    prev = PreviewsPlugin().adjustments(teams, {**weights, "previews":
                                        {**weights.get("previews", {}), "blend": 1.0}})
    snap = {
        "at": dt.datetime.now().isoformat(timespec="seconds"),
        "plugin_weights": {k: float(v) for k, v
                           in weights.get("plugin_weights", {}).items()},
        "news_adj": {t: round(p, 1) for t, p in news.items() if p},
        "previews_adj": {t: round(p, 3) for t, p in prev.items() if p},
        "played": n_played,
    }
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(SIGNAL_LOG, "a") as f:
        f.write(json.dumps(snap, ensure_ascii=False) + "\n")


def _team_volatility(last_k: int = 8) -> list[tuple[str, float, float]]:
    """From signal_log: per team (mean penalty, swing) over the last K runs."""
    if not SIGNAL_LOG.exists():
        return []
    snaps = [json.loads(l) for l in SIGNAL_LOG.read_text().splitlines()][-last_k:]
    if len(snaps) < 2:
        return []
    teams = {t for s in snaps for t in s.get("news_adj", {})}
    out = []
    for t in teams:
        series = [abs(s.get("news_adj", {}).get(t, 0.0)) for s in snaps]
        swing = max(series) - min(series)
        if swing > 0:
            out.append((t, sum(series) / len(series), swing))
    return sorted(out, key=lambda x: -x[2])


def run(weights: dict) -> dict:
    res = data_io.world_cup_2026_results(data_io.load_results())
    actual = {(r.home_team, r.away_team): (int(r.home_score), int(r.away_score))
              for r in res.itertuples(index=False)}
    _record_signal(weights, len(actual))

    traj = _trajectories()
    score = score_history(res) or {}
    exact, drift, helped, hurt = [], [], 0, 0
    for key, snaps in traj.items():
        seq: list[tuple[str, str]] = []
        for _, ls, toto, _top in snaps:
            if not seq or seq[-1][0] != ls:
                seq.append((ls, toto))
        tops = [s[3] for s in snaps]
        swing = (max(tops) - min(tops)) if tops else 0.0
        played = key in actual
        verdict = _judge(seq, actual.get(key)) if played else ""
        if verdict == "hielp":
            helped += 1
        elif verdict == "schaadde":
            hurt += 1
        if played and seq and seq[-1][0] == f"{actual[key][0]}-{actual[key][1]}":
            exact.append(key)
        drift.append({"match": f"{key[0]} – {key[1]}", "played": played,
                      "changes": len(seq) - 1, "swing": swing, "verdict": verdict})

    vol = _team_volatility()
    _write_report(score, exact, drift, vol, helped, hurt, len(actual))
    print(f"analyse: {len(actual)} gespeeld, {len(exact)} exact, "
          f"bijstellingen {helped} hielp / {hurt} schaadde; wrote {REPORT_MD.name}")
    return {"played": len(actual), "exact": len(exact), "helped": helped, "hurt": hurt}


def _write_report(score, exact, drift, vol, helped, hurt, n_played) -> None:
    today = dt.date.today().isoformat()
    L = [f"# wkpool — schommelingen-analyse {today}", "",
         "_Read-only. Verandert geen gewichten; legt vast wat de voorspellingen "
         "deden en waarom._", "", "## Kerncijfers", ""]
    if score:
        L.append(f"- Gescoord: {score.get('matches_scored', n_played)} | "
                 f"toto {score.get('accuracy', 0):.0%} | RPS {score.get('rps', 0):.4f}")
    L.append(f"- Exact goed (modal-voorspelling): {len(exact)} van {n_played}")
    for k in exact:
        L.append(f"  - {k[0]} – {k[1]}")
    L.append(f"- Bijstellingen op gespeelde wedstrijden: {helped} hielp, "
             f"{hurt} schaadde, rest neutraal")

    moved = sorted([d for d in drift if d["changes"] > 0],
                   key=lambda d: (-d["changes"], -d["swing"]))
    L += ["", "## Meest bewogen voorspellingen", "",
          "| Wedstrijd | gespeeld | # score-wijzigingen | max kans-swing | achteraf |",
          "|---|---|---|---|---|"]
    for d in moved[:12]:
        L.append(f"| {d['match']} | {'ja' if d['played'] else 'nee'} "
                 f"| {d['changes']} | {d['swing']:.0%} | {d['verdict'] or '-'} |")
    if not moved:
        L.append("| _(nog niets bewogen)_ | | | | |")

    L += ["", "## Nieuws-volatiliteit per team (laatste runs)", ""]
    if vol:
        L += ["| Team | gem. blessure-penalty (Elo) | swing |", "|---|---|---|"]
        for t, mean, swing in vol[:12]:
            L.append(f"| {t} | {mean:.0f} | {swing:.0f} |")
    else:
        L.append("_Baseline vastgelegd in signal_log.jsonl; volatiliteit verschijnt "
                 "zodra er meerdere runs zijn._")
    REPORT_MD.write_text("\n".join(L) + "\n")
