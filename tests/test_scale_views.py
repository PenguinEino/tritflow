"""Chapter-6 rendering preserves failed/missing data and never computes a stage."""

from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "notebook"))

from scale_views import (layout_penalty_table, load_scaling, power_figure, power_table, scaling_figure,
                         scaling_table, synthesis_table, timing_table)


@pytest.fixture
def data():
    return json.loads((ROOT / "results/dot_scaling.json").read_text())


def test_reader_is_recorded_by_default(monkeypatch, data):
    import examples.dot_scaling as producer

    def forbidden(*args, **kwargs):
        raise AssertionError("Recorded views must never launch the producer")

    monkeypatch.setattr(producer, "run_scaling", forbidden)
    monkeypatch.setenv("NGSPICE_BINARY", "/no-simulator-needed-for-recorded-views")
    loaded = load_scaling()
    assert loaded["rows"] == data["rows"]


def test_explicit_recompute_switch_is_forwarded(monkeypatch, data):
    import examples.dot_scaling as producer
    calls = []

    def recompute(sizes, **kwargs):
        calls.append((sizes, kwargs))
        return data

    monkeypatch.setattr(producer, "run_scaling", recompute)
    assert load_scaling(recompute=True, sizes=(2, 4))["complete"]
    assert calls[0][0] == (2, 4)


@pytest.mark.parametrize("view,label", [(scaling_table, "配置配線"), (synthesis_table, "等価性"),
                                      (power_table, "静的電力"), (timing_table, "STAの誤差"),
                                      (layout_penalty_table, "配線容量")])
def test_tables_use_booktabs_japanese_and_all_recorded_sizes(data, view, label):
    html = view(data).data
    assert label in html and "border-collapse:collapse" in html
    assert "border-top:1.4px" in html and "border-bottom:1.4px" in html
    assert "<thead>" in html and "<tbody>" in html
    for row in data["rows"]:
        assert f"<td>{row['n']}</td>" in html
    assert "overflow-x:auto" in html


def test_failed_timing_is_visible_and_missing_spice_is_not_plotted_as_zero(data):
    missing = deepcopy(data)
    missing["rows"] = [r for r in missing["rows"] if r.get("timing_comparison")]
    row = missing["rows"][-1]
    row["spice"] = {"state": "not_simulated"}
    for item in row["timing_comparison"]:
        item.update(spice_s=None, passed=None, signed_error_percent=None)
    assert "未実施" in timing_table(missing).data
    figure = scaling_figure(missing)
    assert figure.data[2].y[-1] is None
    assert not figure.data[2].connectgaps
    comparison = missing["rows"][0]["timing_comparison"][0]
    comparison["passed"] = False
    assert "不合格" in timing_table(missing).data


def test_scientific_figures_show_actual_data_in_correct_units(data):
    figure = scaling_figure(data)
    assert list(figure.data[0].x) == [r["n"] for r in data["rows"]]
    assert figure.data[0].y[0] == pytest.approx(data["rows"][0]["pnr"]["stats"]["die_area_um2"]*1e-6)
    assert "ns" in figure.layout.yaxis2.title.text
    assert figure.layout.paper_bgcolor == "white" and figure.layout.template.layout.plot_bgcolor is None
    assert figure.layout.xaxis2.type == "log"
    power = power_figure(data)
    assert power.data[1].fill == "tonexty"
    assert power.data[2].y[0] == pytest.approx(data["rows"][0]["power"]["zero"]["static_power_w"]*1e3)
