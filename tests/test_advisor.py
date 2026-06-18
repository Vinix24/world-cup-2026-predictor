"""Weight advisor: path helpers must not mutate, and proposals only fire when a
non-current candidate beats the baseline by the threshold."""
from wkpool import advisor
from wkpool.advisor import MIN_RPS_GAIN, _get, _pick_proposal, _with


def test_with_does_not_mutate_original():
    w = {"ratings": {"k_world_cup": 60}, "form": {"half_life_days": 1095}}
    w2 = _with(w, ("ratings", "k_world_cup"), 70)
    assert _get(w2, ("ratings", "k_world_cup")) == 70
    assert _get(w, ("ratings", "k_world_cup")) == 60      # original untouched


def test_proposes_better_candidate():
    rows = [
        {"value": 60, "rps": 0.1671, "accuracy": 0.60, "current": True},
        {"value": 70, "rps": 0.1660, "accuracy": 0.61, "current": False},
    ]
    p = _pick_proposal("ratings.k_world_cup", 60, rows, base_rps=0.1671)
    assert p is not None and p["to"] == 70 and p["from"] == 60


def test_no_proposal_when_current_is_best():
    rows = [
        {"value": 60, "rps": 0.1671, "accuracy": 0.60, "current": True},
        {"value": 70, "rps": 0.1680, "accuracy": 0.59, "current": False},
    ]
    assert _pick_proposal("x", 60, rows, base_rps=0.1671) is None


def test_no_proposal_below_threshold():
    tiny = MIN_RPS_GAIN / 2
    rows = [
        {"value": 60, "rps": 0.1671, "accuracy": 0.60, "current": True},
        {"value": 70, "rps": 0.1671 - tiny, "accuracy": 0.60, "current": False},
    ]
    assert _pick_proposal("x", 60, rows, base_rps=0.1671) is None
