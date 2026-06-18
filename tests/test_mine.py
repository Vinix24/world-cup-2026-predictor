"""News-driven action alert: the ENTER score of an upcoming match must only
flag as 'pool action' when a participating team's injury news actually moved."""
import json

import pandas as pd

from wkpool import mine
from wkpool.scoring import DEFAULT_RUBRIC


def _snap(enter="1-0", bel_adj=-12.0, egy_adj=0.0):
    return {
        "matches": {"Belgium|Egypt": {"home": "Belgium", "away": "Egypt",
                                       "date": "2026-06-15", "enter": enter}},
        "champions": {},
        "news_adj": {"Belgium": bel_adj, "Egypt": egy_adj},
    }


def test_action_when_news_moves_entry():
    prev = _snap(enter="1-0", bel_adj=-12.0)
    cur = _snap(enter="1-1", bel_adj=-30.0)   # entry moved, Belgium news worsened
    items = mine._action_items(prev, cur)
    assert len(items) == 1
    assert "Belgium – Egypt" in items[0]
    assert "1-1" in items[0] and "was 1-0" in items[0]


def test_no_action_when_entry_moves_without_news():
    prev = _snap(enter="1-0", bel_adj=-12.0)
    cur = _snap(enter="1-1", bel_adj=-12.0)   # entry moved, news unchanged
    assert mine._action_items(prev, cur) == []


def test_no_action_when_news_moves_but_entry_stable():
    prev = _snap(enter="1-0", bel_adj=-12.0)
    cur = _snap(enter="1-0", bel_adj=-30.0)   # news moved, entry held
    assert mine._action_items(prev, cur) == []


def test_no_action_on_first_run():
    assert mine._action_items({}, _snap()) == []


def test_score_pool_exact_and_points(tmp_path, monkeypatch):
    monkeypatch.setattr(mine, "ENTER_HISTORY", tmp_path / "enter.jsonl")
    (tmp_path / "enter.jsonl").write_text("\n".join(
        json.dumps(r) for r in [
            {"home": "Mexico", "away": "South Africa", "enter": "1-0"},   # superseded
            {"home": "Mexico", "away": "South Africa", "enter": "2-0"},   # latest wins
            {"home": "Brazil", "away": "Morocco", "enter": "1-1"},
        ]) + "\n")
    results = pd.DataFrame([
        {"home_team": "Mexico", "away_team": "South Africa", "home_score": 2, "away_score": 0},
        {"home_team": "Brazil", "away_team": "Morocco", "home_score": 1, "away_score": 1},
    ])
    pool = mine.score_pool(results, DEFAULT_RUBRIC)
    assert pool["matches"] == 2
    assert pool["exact"] == 2                                  # 2-0 and 1-1 both exact
    assert pool["points"] == 2 * DEFAULT_RUBRIC["exact"]


def test_score_pool_orients_to_result(tmp_path, monkeypatch):
    monkeypatch.setattr(mine, "ENTER_HISTORY", tmp_path / "enter.jsonl")
    # entered as Haiti–Scotland 0-1; result logged swapped (Scotland home)
    (tmp_path / "enter.jsonl").write_text(
        json.dumps({"home": "Haiti", "away": "Scotland", "enter": "0-1"}) + "\n")
    results = pd.DataFrame([
        {"home_team": "Scotland", "away_team": "Haiti", "home_score": 1, "away_score": 0},
    ])
    pool = mine.score_pool(results, DEFAULT_RUBRIC)
    assert pool["exact"] == 1 and pool["matches"] == 1


def test_score_pool_none_without_log(tmp_path, monkeypatch):
    monkeypatch.setattr(mine, "ENTER_HISTORY", tmp_path / "absent.jsonl")
    assert mine.score_pool(pd.DataFrame(), DEFAULT_RUBRIC) is None
