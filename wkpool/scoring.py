"""Pool scoring rubric + expected-points-optimal scoreline.

Most pools reward the exact scoreline far more than the bare winner, so the
score you should *enter* is the one that maximises expected points under the
rubric — not the single most likely score. For evenly matched teams that is
often a draw like 1-1, because any draw scores the "correct draw" tier.

The default rubric matches Vincent's pool (graded exact-score). Override it in
weights.yaml under `pool_scoring` for a different pool.
"""
from __future__ import annotations

import math

DEFAULT_RUBRIC = {
    "exact": 200,                  # exact full-time score
    "draw": 100,                   # correct draw, wrong score
    "winner_plus_one_goals": 95,   # correct winner + one team's goal count
    "winner": 75,                  # correct winner only
    "one_team_goals": 20,          # wrong winner, but one team's goals right
    "max_pred_goals": 6,           # search predicted scores 0..this
    "max_calc_goals": 10,          # integrate the Poisson grid 0..this
}


def points(ph: int, pa: int, ah: int, aa: int, rubric: dict = DEFAULT_RUBRIC) -> int:
    """Points for predicting (ph, pa) when the actual score is (ah, aa)."""
    if ph == ah and pa == aa:
        return rubric["exact"]
    pred_draw, act_draw = ph == pa, ah == aa
    if pred_draw and act_draw:
        return rubric["draw"]
    pred_w = (ph > pa) - (ph < pa)
    act_w = (ah > aa) - (ah < aa)
    one_goal = (ph == ah) or (pa == aa)
    if pred_w == act_w and pred_w != 0:        # correct (non-draw) winner
        return rubric["winner_plus_one_goals"] if one_goal else rubric["winner"]
    return rubric["one_team_goals"] if one_goal else 0


def _poisson_pmf(lam: float, k: int) -> float:
    return math.exp(-lam) * lam ** k / math.factorial(k)


def score_grid(lam_h: float, lam_a: float, max_goals: int) -> list[list[float]]:
    ph = [_poisson_pmf(lam_h, k) for k in range(max_goals + 1)]
    pa = [_poisson_pmf(lam_a, k) for k in range(max_goals + 1)]
    return [[ph[h] * pa[a] for a in range(max_goals + 1)] for h in range(max_goals + 1)]


def expected_points(pred_h: int, pred_a: int, grid: list[list[float]],
                    rubric: dict = DEFAULT_RUBRIC) -> float:
    total = 0.0
    for ah, row in enumerate(grid):
        for aa, p in enumerate(row):
            if p:
                total += p * points(pred_h, pred_a, ah, aa, rubric)
    return total


def optimal_prediction(lam_h: float, lam_a: float,
                       rubric: dict = DEFAULT_RUBRIC) -> tuple[int, int, float]:
    """Return (pred_home, pred_away, expected_points) maximising expected points."""
    grid = score_grid(lam_h, lam_a, int(rubric["max_calc_goals"]))
    best, best_ev = (0, 0), -1.0
    for ph in range(int(rubric["max_pred_goals"]) + 1):
        for pa in range(int(rubric["max_pred_goals"]) + 1):
            ev = expected_points(ph, pa, grid, rubric)
            if ev > best_ev:
                best, best_ev = (ph, pa), ev
    return best[0], best[1], best_ev
