"""Pool scoring rubric and expected-points optimiser."""
from wkpool.scoring import (DEFAULT_RUBRIC, points, optimal_prediction,
                            expected_points, score_grid)

R = DEFAULT_RUBRIC


def test_points_tiers_match_pool_rules():
    assert points(2, 1, 2, 1) == 200          # exact
    assert points(1, 1, 2, 2) == 100          # correct draw, wrong score
    assert points(3, 0, 3, 1) == 95           # winner + home goals
    assert points(3, 1, 1, 0) == 75           # winner only
    assert points(1, 2, 1, 0) == 20           # wrong winner, home goals right
    assert points(0, 3, 2, 0) == 0            # nothing right


def test_predicted_draw_vs_actual_win_can_still_score_goals():
    # predict 1-1, actual 1-0: winner wrong, but home goals (1) right -> 20
    assert points(1, 1, 1, 0) == 20
    # predict 1-1, actual 3-0: nothing right -> 0
    assert points(1, 1, 3, 0) == 0


def test_optimiser_picks_draw_for_even_match():
    # equal strengths -> a draw should maximise expected points (any draw = 100)
    h, a, ev = optimal_prediction(1.2, 1.2)
    assert h == a            # a draw
    assert ev > 0


def test_optimiser_picks_home_win_for_strong_favourite():
    h, a, ev = optimal_prediction(2.6, 0.5)
    assert h > a             # predict a home win
    assert ev > 75           # better than a bare winner tier in expectation... at least positive & favouring exact-ish


def test_expected_points_consistent_with_grid():
    grid = score_grid(1.5, 1.0, 10)
    # expected points of some prediction is a probability-weighted average, bounded by 200
    ev = expected_points(2, 1, grid)
    assert 0 <= ev <= 200
