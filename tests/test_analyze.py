"""Schommelingen-analyse: the help/hurt verdict on a prediction's net movement."""
from wkpool import analyze


def test_toto():
    assert analyze._toto(2, 0) == "1"
    assert analyze._toto(1, 1) == "X"
    assert analyze._toto(0, 3) == "2"


def test_adjustment_helped_flips_to_correct_winner():
    # opened wrong (draw), ended on the correct home win
    seq = [("1-1", "X"), ("1-0", "1")]
    assert analyze._judge(seq, (2, 0)) == "hielp"


def test_adjustment_hurt_flips_away_from_correct_winner():
    seq = [("1-0", "1"), ("1-1", "X")]
    assert analyze._judge(seq, (2, 0)) == "schaadde"


def test_adjustment_neutral_when_winner_unchanged():
    # both predictions call the home win, neither is exact -> noise
    seq = [("2-0", "1"), ("1-0", "1")]
    assert analyze._judge(seq, (3, 0)) == "neutraal"


def test_no_verdict_without_movement_or_result():
    assert analyze._judge([("1-0", "1")], (2, 0)) == ""   # never moved
    assert analyze._judge([("1-1", "X"), ("1-0", "1")], None) == ""  # not played
