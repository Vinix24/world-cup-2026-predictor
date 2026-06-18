"""Weight advisor — suggest-only. Backtests the core weights on the holdout and
proposes changes. It never edits weights.yaml; the last set stays human.

Core weights (Elo K-factors, form half-life, home advantage) are tuned against
the held-out internationals (model.eval_holdout_since), the only statistically
valid surface — the live WC sample is far too small to tune on. Signal weights
(injuries, odds, previews) cannot be holdout-validated, so they are measured
live via output/signal_log.jsonl and reported here, not proposed.

The model is deterministic (fixed random_state), so the sweep is clean: an RPS
difference between candidates is real, not noise.
"""
from __future__ import annotations

import copy
import datetime as dt
import json

from . import data_io
from .config import OUTPUT_DIR
from .elo import EloEngine
from .model import OutcomeModel, build_training_frame

REPORT_MD = OUTPUT_DIR / "weight_advice.md"
MIN_RPS_GAIN = 0.0005   # only flag a proposal when holdout RPS drops at least this

# (label, weights-path, candidate values) — coordinate search around the current
CORE_GRID = [
    ("ratings.k_world_cup", ("ratings", "k_world_cup"), [50, 60, 70, 80]),
    ("form.half_life_days", ("form", "half_life_days"), [730, 1095, 1460, 1825]),
    ("ratings.home_advantage", ("ratings", "home_advantage"), [80, 100, 120]),
]


def _get(weights: dict, path: tuple):
    d = weights
    for k in path:
        d = d[k]
    return d


def _with(weights: dict, path: tuple, value) -> dict:
    w = copy.deepcopy(weights)
    d = w
    for k in path[:-1]:
        d = d[k]
    d[path[-1]] = value
    return w


def _pick_proposal(label: str, cur, rows: list[dict], base_rps: float) -> dict | None:
    best = min(rows, key=lambda r: r["rps"])
    gain = base_rps - best["rps"]
    if best["current"] or gain < MIN_RPS_GAIN:
        return None
    return {"label": label, "from": cur, "to": best["value"],
            "rps": best["rps"], "rps_gain": gain}


def _holdout_metrics(weights: dict, df) -> dict:
    engine = EloEngine(weights)
    hist = engine.process(df)
    train_df = build_training_frame(hist, weights["model"]["train_since"])
    return OutcomeModel(weights).train(train_df)


def run(weights: dict) -> dict:
    df = data_io.load_results()
    base = _holdout_metrics(weights, df)
    base_rps = base["rps"]
    sweeps, proposals = [], []
    for label, path, candidates in CORE_GRID:
        cur = _get(weights, path)
        rows = []
        for v in candidates:
            m = base if v == cur else _holdout_metrics(_with(weights, path, v), df)
            rows.append({"value": v, "rps": m["rps"],
                         "accuracy": m["accuracy"], "current": v == cur})
        sweeps.append({"label": label, "current": cur, "rows": rows})
        proposal = _pick_proposal(label, cur, rows, base_rps)
        if proposal:
            proposals.append(proposal)
    _write_report(base, sweeps, proposals)
    print(f"advisor: baseline holdout RPS {base_rps:.4f}; "
          f"{len(proposals)} proposal(s); wrote {REPORT_MD.name}")
    return {"baseline_rps": base_rps, "proposals": proposals}


def _signal_status() -> str:
    from .analyze import SIGNAL_LOG
    if not SIGNAL_LOG.exists():
        return "No signal_log yet — run `wkpool analyze` first."
    lines = SIGNAL_LOG.read_text().splitlines()
    played = json.loads(lines[-1]).get("played", 0) if lines else 0
    tail = ("Too little to propose a change yet; accumulating."
            if played < 40 else "Enough to start a live read.")
    return f"Accumulated: {len(lines)} run snapshot(s), {played} played match(es). {tail}"


def _write_report(base: dict, sweeps: list, proposals: list) -> None:
    today = dt.date.today().isoformat()
    L = [f"# wkpool — weight advisor {today}", "",
         "_Suggest-only. Core weights backtested on the holdout (RPS, lower is "
         "better). Nothing is applied automatically — edit `weights.yaml` yourself "
         "if you agree._", "",
         "## Baseline", "",
         f"holdout RPS {base['rps']:.4f}, accuracy {base['accuracy']:.1%} "
         f"({base['holdout_matches']} matches since {base['holdout_since']})", "",
         "## Proposals", ""]
    if proposals:
        for p in proposals:
            L.append(f"- **{p['label']}: {p['from']} -> {p['to']}** "
                     f"(holdout RPS {base['rps']:.4f} -> {p['rps']:.4f}, "
                     f"gain {p['rps_gain']:.4f})")
    else:
        L.append("_No core weight beats the current setting by the threshold "
                 f"({MIN_RPS_GAIN}). Current weights stand._")

    L += ["", "## Sweeps", ""]
    for s in sweeps:
        L += [f"### {s['label']} (current {s['current']})", "",
              "| value | holdout RPS | accuracy |", "|---|---|---|"]
        for r in s["rows"]:
            mark = " ← current" if r["current"] else ""
            L.append(f"| {r['value']}{mark} | {r['rps']:.4f} | {r['accuracy']:.1%} |")
        L.append("")

    L += ["## Signal weights (injuries, odds, previews)", "",
          "Not holdout-validatable — there is no historical injury/odds/preview "
          "data. Measured live on results via signal_log.jsonl instead.",
          _signal_status(), ""]
    if proposals:
        L += ["## To apply", "",
              "Edit `weights.yaml` with the proposed value(s), then run "
              "`wkpool daily` to refit. The advisor never writes weights itself."]
    REPORT_MD.write_text("\n".join(L) + "\n")
