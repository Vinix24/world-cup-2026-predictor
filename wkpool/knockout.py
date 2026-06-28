"""Round-of-32 resolution and per-match prediction.

The group pipeline (`predict_remaining`) only covers group fixtures. Once the
group stage is fully played the knockout bracket is determined, so this module
resolves the official round-of-32 matchups from the actual results and predicts
each one with the same model machinery used everywhere else.

Two knockout-specific signals are layered on the Elo rating before prediction:
  - home advantage: the existing host-nation bonus (USA / Mexico / Canada),
  - altitude: a venue-specific nudge. Teams that train and play at altitude
    (Mexico, Ecuador, Colombia) cope better with thin air; sea-level teams
    suffer. It scales with how far the venue sits above `threshold_m`, so it
    only bites at Estadio Azteca (Mexico City, ~2240 m) in this round.
"""
from __future__ import annotations

import numpy as np

from . import schedule, scoring
from .predict import likely_score
from .sim import TournamentSim


def home_advantage(home: str, away: str, venue_country: str, home_adv: float) -> float:
    """Host bonus, but only for the team actually playing in its own country."""
    adv = 0.0
    if schedule.HOST_COUNTRY.get(home) == venue_country:
        adv += home_adv
    if schedule.HOST_COUNTRY.get(away) == venue_country:
        adv -= home_adv
    return adv

# Nations whose players are acclimatised to altitude (regular football at
# >=1500 m): Mexico (Mexico City ~2240 m), Ecuador (Quito ~2850 m),
# Colombia (Bogotá ~2640 m).
ALTITUDE_ACCLIMATISED = {"Mexico", "Ecuador", "Colombia"}

# allocate_thirds() only guarantees a *valid* third-place slot assignment; FIFA's
# exact priority between equally valid ones is not public. When the realised set
# of qualifying third-placed groups matches the actual draw, pin the published
# allocation (verified against the official round-of-32 bracket) so we predict
# the real fixtures. Keyed by the set of groups whose third-placed team advanced;
# value maps each third-place slot (its allowed-groups string) to a group letter.
R32_THIRD_ALLOCATION: dict[frozenset, dict[str, str]] = {
    frozenset("BDEFIJKL"): {
        "ABCDF": "D", "CDFGH": "F", "CEFHI": "E", "EHIJK": "K",
        "BEFIJ": "B", "AEHIJ": "I", "EFGIJ": "J", "DEIJL": "L",
    },
}


def group_stage_complete(played: dict[tuple[str, str], tuple[int, int]]) -> bool:
    """True once every one of the 72 group fixtures has a result."""
    return all((h, a) in played or (a, h) in played
               for _, h, a in schedule.GROUP_FIXTURES)


def resolve_r32(sim: TournamentSim, seed: int = 0) -> list[dict]:
    """Resolve the 16 round-of-32 matchups from the played group results.

    Reuses the simulation's group ranking so the tiebreak rules stay identical.
    With every group match decided this is deterministic bar exact-tie lots,
    which the seed pins for reproducibility.
    """
    rng = np.random.default_rng(seed)
    winners: dict[str, str] = {}
    runners: dict[str, str] = {}
    third_stats: list[tuple[str, str, tuple]] = []
    for letter in schedule.GROUP_LETTERS:
        ranked = sim._play_group(letter, rng)
        winners[letter], runners[letter] = ranked[0], ranked[1]
        third_stats.append((letter, ranked[2], sim._last_group_stats[ranked[2]]))

    third_stats.sort(key=lambda x: (-x[2][0], -x[2][1], -x[2][2], rng.random()))
    qualified_thirds = [g for g, _, _ in third_stats[:8]]
    third_team = {g: t for g, t, _ in third_stats[:8]}
    allocation = R32_THIRD_ALLOCATION.get(frozenset(qualified_thirds))
    if allocation is None:
        allocation = schedule.allocate_thirds(qualified_thirds)
    if allocation is None:  # cannot happen with FIFA's slot design
        slots = [m["away"][1] for m in schedule.ROUND_OF_32 if m["away"][0] == "3"]
        allocation = dict(zip(slots, qualified_thirds))

    def resolve(slot: tuple[str, str]) -> str:
        kind, ref = slot
        if kind == "1":
            return winners[ref]
        if kind == "2":
            return runners[ref]
        return third_team[allocation[ref]]

    return [{"match": m["match"], "date": m["date"],
             "home": resolve(m["home"]), "away": resolve(m["away"])}
            for m in schedule.ROUND_OF_32]


def altitude_nudge(team: str, elev_m: float, cfg: dict) -> float:
    """Elo-point adjustment for `team` playing at a venue `elev_m` high."""
    thr = float(cfg.get("threshold_m", 1000))
    ref = float(cfg.get("ref_m", 2240))
    if elev_m <= thr or ref <= thr:
        return 0.0
    factor = min(1.0, (elev_m - thr) / (ref - thr))
    if team in ALTITUDE_ACCLIMATISED:
        return float(cfg.get("accl_bonus", 40)) * factor
    return -float(cfg.get("sea_penalty", 40)) * factor


def predict_r32(outcome, goal_model, ratings: dict[str, float],
                forms: dict[str, float], weights: dict,
                played: dict[tuple[str, str], tuple[int, int]]) -> list[dict]:
    """Per-match round-of-32 prediction with the expected-points-optimal ENTER.

    Mirrors `mine._enrich`, but resolves the bracket first and applies the
    altitude nudge per venue. Returns the same row shape as the group rows plus
    venue/altitude detail, so the rest of the private pass can treat them alike.
    """
    home_adv = float(weights["ratings"]["home_advantage"])
    rubric = weights.get("pool_scoring", scoring.DEFAULT_RUBRIC)
    alt_cfg = weights.get("altitude", {})
    sim = TournamentSim(goal_model, ratings, weights, played)
    fixtures = resolve_r32(sim, seed=int(weights["simulation"].get("seed") or 0))

    rows = []
    for fx in fixtures:
        home, away = fx["home"], fx["away"]
        venue = schedule.R32_VENUES[fx["match"]]
        elev = venue["elev_m"]
        adv = home_advantage(home, away, venue["country"], home_adv)
        alt_h = altitude_nudge(home, elev, alt_cfg)
        alt_a = altitude_nudge(away, elev, alt_cfg)
        r_home = ratings[home] + alt_h
        r_away = ratings[away] + alt_a

        p = outcome.predict_match(r_home, r_away, forms[home], forms[away],
                                  importance=60.0, neutral=(adv == 0.0),
                                  home_adv=adv)
        lam_h, lam_a = goal_model.lambdas(r_home, r_away, home_adv=adv)
        eh, ea, ev = scoring.optimal_prediction(lam_h, lam_a, rubric)
        hg, ag = likely_score(goal_model, {home: r_home, away: r_away},
                              home, away, adv)
        note = []
        if adv != 0.0:
            note.append("home" if adv > 0 else "away-host")
        if round(alt_h - alt_a, 1) != 0.0:
            note.append(f"altitude {alt_h - alt_a:+.0f}")
        rows.append({"match": fx["match"], "date": fx["date"],
                     "home": home, "away": away,
                     "p_home": round(float(p[0]), 4),
                     "p_draw": round(float(p[1]), 4),
                     "p_away": round(float(p[2]), 4),
                     "likely": f"{hg}-{ag}", "enter": f"{eh}-{ea}",
                     "ev": round(ev, 1),
                     "venue": f"{venue['stadium']}, {venue['city']}",
                     "note": ", ".join(note)})
    return rows
