"""News-driven action alert: the ENTER score of an upcoming match must only
flag as 'pool action' when a participating team's injury news actually moved."""
from wkpool import mine


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
