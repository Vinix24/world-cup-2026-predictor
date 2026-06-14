"""Track record: an honest, append-only audit trail committed to the repo.

Each daily run upserts one dated snapshot into track_record.jsonl (the data)
and re-renders TRACK_RECORD.md (the readable proof). Every prediction was
logged before kickoff (output/history.jsonl + git history), so the
cumulative accuracy curve cannot be cherry-picked after the fact — hits and
misses both land in the record.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import numpy as np

from . import data_io
from .config import NEWS_DIR, OUTPUT_DIR, ROOT
from .predict import HISTORY

TRACK_JSONL = ROOT / "track_record.jsonl"
TRACK_MD = ROOT / "TRACK_RECORD.md"


def _latest_predictions() -> dict[tuple[str, str], dict]:
    if not HISTORY.exists():
        return {}
    latest: dict[tuple[str, str], dict] = {}
    for line in HISTORY.read_text().splitlines():
        rec = json.loads(line)
        latest[(rec["home"], rec["away"])] = rec  # later overwrites earlier
    return latest


def _score_match(rec: dict, home: str, hs: int, as_) -> tuple[int, float] | None:
    """Return (correct, rps) for one played match given its pre-match prediction."""
    if rec is None:
        return None
    # probs in result orientation: [home win, draw, away win]
    if rec["home"] == home:
        probs = [rec["p_home"], rec["p_draw"], rec["p_away"]]
    else:  # prediction stored with teams swapped vs. the result
        probs = [rec["p_away"], rec["p_draw"], rec["p_home"]]
    diff = hs - as_
    outcome = 0 if diff > 0 else (1 if diff == 0 else 2)
    cum_p = np.cumsum(probs)
    cum_o = np.cumsum([1 if i == outcome else 0 for i in range(3)])
    rps = float(np.sum((cum_p - cum_o)[:2] ** 2) / 2)
    return int(int(np.argmax(probs)) == outcome), rps


def cumulative_score(results_2026, latest) -> dict:
    correct, rps_terms = 0, []
    for r in results_2026.itertuples(index=False):
        rec = latest.get((r.home_team, r.away_team)) or latest.get((r.away_team, r.home_team))
        scored = _score_match(rec, r.home_team, int(r.home_score), int(r.away_score))
        if scored is None:
            continue
        correct += scored[0]
        rps_terms.append(scored[1])
    n = len(rps_terms)
    return {"matches": n,
            "correct": correct,
            "accuracy": (correct / n) if n else None,
            "rps": (sum(rps_terms) / n) if n else None}


def _news_summary() -> dict:
    """Summarise the news currently feeding the model (today's ingestion)."""
    out, doubtful, suspensions, teams = 0, 0, [], 0
    if NEWS_DIR.is_dir():
        for path in NEWS_DIR.glob("*.json"):
            try:
                d = json.loads(path.read_text())
            except json.JSONDecodeError:
                continue
            teams += 1
            for i in d.get("injuries", []):
                if i.get("status") == "out":
                    out += 1
                elif i.get("status") == "doubtful":
                    doubtful += 1
            for s in d.get("suspensions", []):
                suspensions.append(f"{s.get('player', '?')} ({d.get('team', '?')})")
    return {"teams": teams, "out": out, "doubtful": doubtful,
            "suspensions": suspensions}


def _weights_summary(weights: dict) -> str:
    r, f, inj = weights["ratings"], weights["form"], weights["injuries"]
    pw = weights["plugin_weights"]
    return (f"injuries ×{pw.get('injuries', 0)} ({inj['points_per_out']}/out, "
            f"{inj['points_per_doubtful']}/doubtful), climate ×{pw.get('climate', 0)}, "
            f"form half-life {f['half_life_days']}d, "
            f"K_wc={r['k_world_cup']}, sims={weights['simulation']['n_sims']}")


def update(weights: dict, today: dt.date | None = None) -> None:
    """Upsert today's snapshot and re-render the track record."""
    today = today or dt.date.today()
    df = data_io.load_results()
    results = data_io.world_cup_2026_results(df)
    latest = _latest_predictions()

    snapshots: dict[str, dict] = {}
    if TRACK_JSONL.exists():
        for line in TRACK_JSONL.read_text().splitlines():
            if line.strip():
                s = json.loads(line)
                snapshots[s["date"]] = s

    prev_keys = set()
    for d in sorted(k for k in snapshots if k < today.isoformat()):
        prev_keys = set(tuple(k) for k in snapshots[d].get("played_keys", []))

    played_now = [(r.home_team, r.away_team, int(r.home_score), int(r.away_score))
                  for r in results.itertuples(index=False)]
    newly = []
    for h, a, hs, as_ in played_now:
        if (h, a) not in prev_keys:
            rec = latest.get((h, a)) or latest.get((a, h))
            verdict = _score_match(rec, h, hs, as_)
            mark = "?" if verdict is None else ("OK" if verdict[0] else "X")
            tip = ""
            if rec is not None:
                tip = f", predicted {rec['likely_score']}"
            newly.append(f"{h} {hs}-{as_} {a} [{mark}{tip}]")

    score = cumulative_score(results, latest)
    news = _news_summary()
    snapshots[today.isoformat()] = {
        "date": today.isoformat(),
        "score": score,
        "news": news,
        "weights": _weights_summary(weights),
        "newly_decided": newly,
        "played_keys": [[h, a] for h, a, _, _ in played_now],
    }

    ordered = [snapshots[k] for k in sorted(snapshots)]
    TRACK_JSONL.write_text("\n".join(json.dumps(s, ensure_ascii=False) for s in ordered) + "\n")
    _render(ordered)


def _render(snapshots: list[dict]) -> None:
    lines = [
        "# wkpool — track record",
        "",
        "Honest, automated audit trail. Every prediction is logged **before** the",
        "match is played (`output/history.jsonl` + git history), so this accuracy",
        "curve cannot be cherry-picked afterwards. Hits and misses both.",
        "",
        "## Cumulative accuracy",
        "",
        "| As of | Matches scored | Correct (toto) | Accuracy | RPS |",
        "|---|---|---|---|---|",
    ]
    for s in snapshots:
        sc = s["score"]
        if sc["matches"]:
            lines.append(f"| {s['date']} | {sc['matches']} | {sc['correct']} "
                         f"| {sc['accuracy']:.0%} | {sc['rps']:.4f} |")
        else:
            lines.append(f"| {s['date']} | 0 | – | – | – |")
    lines += ["", "## Daily recalibration log", ""]
    for s in reversed(snapshots):
        lines.append(f"### {s['date']}")
        sc = s["score"]
        if sc["matches"]:
            lines.append(f"- Score so far: {sc['matches']} matches, "
                         f"{sc['accuracy']:.0%} correct, RPS {sc['rps']:.4f}")
        else:
            lines.append("- Score so far: no matches scored yet")
        if s["newly_decided"]:
            lines.append(f"- Newly decided: {'; '.join(s['newly_decided'])}")
        n = s["news"]
        susp = f", {len(n['suspensions'])} suspensions" if n["suspensions"] else ""
        lines.append(f"- News ingested: {n['teams']} teams scanned, "
                     f"{n['out']} out / {n['doubtful']} doubtful{susp}")
        if n["suspensions"]:
            lines.append(f"  - Suspensions: {'; '.join(n['suspensions'][:8])}")
        lines.append(f"- Active weights: {s['weights']}")
        lines.append("")
    TRACK_MD.write_text("\n".join(lines))
    print(f"wrote {TRACK_MD}")
