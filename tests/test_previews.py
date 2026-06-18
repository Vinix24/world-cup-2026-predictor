"""Press-consensus plugin: favored team nudged up, underdog down, off by default."""
import datetime as dt
import json

import wkpool.plugins.previews as pv
from wkpool.config import DEFAULTS
from wkpool.plugins.previews import PreviewsPlugin

WEIGHTS = {"previews": {"blend": 40, "max_age_days": 5, "max_team_points": 40}}


def _write(tmp_path, **over):
    rep = {"home": "Brazil", "away": "Haiti",
           "as_of": dt.date.today().isoformat(),
           "consensus": {"p_home": 0.8, "p_draw": 0.15, "p_away": 0.05},
           "favored": "home", "confidence": "high"}
    rep.update(over)
    (tmp_path / "m.json").write_text(json.dumps(rep))


def test_favored_team_nudged_up_underdog_down(tmp_path, monkeypatch):
    monkeypatch.setattr(pv, "PREVIEWS_DIR", tmp_path)
    _write(tmp_path)
    adj = PreviewsPlugin().adjustments(["Brazil", "Haiti"], WEIGHTS)
    assert adj["Brazil"] > 0 and adj["Haiti"] < 0
    assert adj["Brazil"] == -adj["Haiti"]          # symmetric within a match


def test_stale_preview_ignored(tmp_path, monkeypatch):
    monkeypatch.setattr(pv, "PREVIEWS_DIR", tmp_path)
    _write(tmp_path, as_of="2020-01-01")
    assert PreviewsPlugin().adjustments(["Brazil", "Haiti"], WEIGHTS) == {}


def test_silent_when_blend_zero(tmp_path, monkeypatch):
    monkeypatch.setattr(pv, "PREVIEWS_DIR", tmp_path)
    _write(tmp_path)
    assert PreviewsPlugin().adjustments(["Brazil", "Haiti"],
                                        {"previews": {"blend": 0}}) == {}


def test_off_by_default_in_config():
    assert DEFAULTS["plugin_weights"]["previews"] == 0.0
