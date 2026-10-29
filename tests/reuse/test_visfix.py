"""Display translations must leave stimulus coverage and signoff evidence intact."""
from copy import deepcopy
import json
from pathlib import Path

from IPython.display import HTML
import pytest

import live
import reuse
import views


@pytest.fixture(autouse=True)
def japanese():
    original = live._text("ja", "en")
    live.set_language("ja")
    yield
    live.set_language(original)


@pytest.mark.parametrize("width,mode", [(1, "全入力状態"), (8, "一部の入力状態")])
def test_coverage_translation_does_not_change_recorded_plan(width, mode):
    plan = reuse.stimulus_plan([f"a{i}" for i in range(width)])
    original = deepcopy(plan)
    summary = {"stimulus": plan, "die_size_um": [100, 200], "top": "example", "cells": 1,
               "drc_violations": 0, "lvs_matched": True, "post_passed": True,
               "max_error_v": .01, "max_settling_s": {"y": 10e-9}, "constant_folding": None}
    assert mode in reuse.summary_view(summary).data
    assert "網羅する検証ではない" in reuse._label(plan["method"])
    live.set_language("en")
    assert plan["mode"] in reuse.summary_view(summary).data
    assert reuse._label(plan["method"]) == plan["method"]
    assert plan == original


def test_shuttle_localizes_display_and_returns_unchanged_signoff(monkeypatch):
    from tritflow.viz import layout
    captured = []
    monkeypatch.setattr(reuse, "display", lambda item: captured.append(item.data))
    monkeypatch.setattr(views, "display", lambda item: captured.append(item.data))
    monkeypatch.setattr(layout, "gds_viewer", lambda *a, **kw: HTML(""))
    folder = Path(reuse.__file__).parent / "assets/chip/dot4"
    original = json.loads((folder / "signoff.json").read_text())
    assert reuse.shuttle_view() == original
    html = "".join(captured)
    for label in ("検査（記録済み）", "電源", "入力", "出力"):
        assert label in html
    for label in (">power<", ">input<", ">output<", "提出準備", "ボンディング図", original["reason"]):
        assert label not in html
    # Checks and pad map share one flex row.
    assert html.count("display:flex") == 1 and "tfshuttlechecks" in html and "tfshuttlepads" in html
    assert reuse._label("unrecognized future signoff reason") == "unrecognized future signoff reason"


def test_settling_arrow_keeps_measured_endpoints_with_separate_text():
    post = {"stimulus": {"inputs": ["a"], "outputs": ["y"], "hold_s": 1e-6,
                         "vectors": [(0,), (1,)]},
            "waveforms": {"time": [0, 1e-6, 2e-6], "v(a)": [0, 5, 5],
                          "v(y)": [0, 0, 5], "i(vdd)": [1e-6] * 3},
            "measurements": {"rows": [
                {"check_s": 1e-6, "outputs": {"y": {"voltage_v": 0, "ideal_voltage_v": 0,
                                                     "passed": True, "settling_s": 0}}},
                {"check_s": 2e-6, "outputs": {"y": {"voltage_v": 5, "ideal_voltage_v": 5,
                                                     "passed": True, "settling_s": 227e-9}}}]}}
    original = deepcopy(post)
    figure = views.scope_figure(post, settle=True)
    arrow, label = figure.layout.annotations
    assert arrow.showarrow and arrow.text == ""
    assert (arrow.ax, arrow.ay) == (1, 5)
    assert arrow.x == pytest.approx(1.227) and arrow.y == 5
    assert not label.showarrow and label.text == "227 ns"
    assert label.yshift >= 10 and label.yanchor == "bottom"
    assert post == original
