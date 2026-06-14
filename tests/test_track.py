"""Track-record scoring logic."""
import pandas as pd

from wkpool import track


def _results(rows):
    return pd.DataFrame(rows, columns=["home_team", "away_team",
                                       "home_score", "away_score"])


def test_cumulative_score_counts_hits_and_misses():
    results = _results([
        ("Mexico", "South Africa", 2, 0),   # predicted home win -> hit
        ("Canada", "Bosnia and Herzegovina", 1, 1),  # predicted home win -> miss (draw)
    ])
    latest = {
        ("Mexico", "South Africa"): {"home": "Mexico", "p_home": 0.8,
                                     "p_draw": 0.12, "p_away": 0.08,
                                     "likely_score": "2-0"},
        ("Canada", "Bosnia and Herzegovina"): {"home": "Canada", "p_home": 0.75,
                                               "p_draw": 0.17, "p_away": 0.08,
                                               "likely_score": "2-0"},
    }
    score = track.cumulative_score(results, latest)
    assert score["matches"] == 2
    assert score["correct"] == 1
    assert score["accuracy"] == 0.5
    assert 0 < score["rps"] < 1


def test_cumulative_score_handles_reversed_team_order():
    # prediction stored as (A,B) but result recorded as (B,A)
    results = _results([("South Africa", "Mexico", 0, 2)])
    latest = {("Mexico", "South Africa"): {"home": "Mexico", "p_home": 0.8,
                                           "p_draw": 0.12, "p_away": 0.08,
                                           "likely_score": "2-0"}}
    score = track.cumulative_score(results, latest)
    assert score["matches"] == 1
    assert score["correct"] == 1  # Mexico (away here) won, model favoured Mexico


def test_empty_results_give_no_score():
    score = track.cumulative_score(_results([]), {})
    assert score == {"matches": 0, "correct": 0, "accuracy": None, "rps": None}
