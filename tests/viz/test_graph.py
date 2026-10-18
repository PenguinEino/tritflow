"""Notebook graphs preserve logic direction, cell identity and every net value."""

from html.parser import HTMLParser

import numpy as np
import plotly.graph_objects as go
import pytest

from tritflow.hdl import load, loads
from tritflow.netlist import GateNetlist, Instance, Port
from tritflow.synth import evaluate_netlist, synthesize
from tritflow.viz.graph import CELL_COLORS, TRIT_COLORS, color_nets, gate_graph, net_values, truth_table_html


@pytest.fixture(scope="module")
def full_add():
    return synthesize(load("examples/full_add.tv", top="full_add"))


def traces(fig, kind):
    return [trace for trace in fig.data if trace.meta["kind"] == kind]


def test_logic_levels_and_cell_colors(full_add):
    fig = gate_graph(full_add)
    assert isinstance(fig, go.Figure)
    assert {trace.meta["net"] for trace in traces(fig, "net")} == full_add.nets()
    rows = {}
    for trace in traces(fig, "nodes"):
        if trace.meta["cell"] in CELL_COLORS:
            assert trace.marker.color == CELL_COLORS[trace.meta["cell"]]
        for x, row in zip(trace.x, trace.customdata):
            name, cell, _, _, level, value, _ = row
            assert x == level
            assert value == "not evaluated"
            rows[(cell, name)] = level
    assert [rows[("INPUT", name)] for name in ["a", "b", "cin"]] == [0, 0, 0]
    assert rows[("OUTPUT", "sum")] == rows[("OUTPUT", "cout")] == 13
    assert max(v for (cell, _), v in rows.items() if cell not in {"INPUT", "OUTPUT"}) == 12
    for trace in traces(fig, "net"):
        # Each fanout branch starts at the driver and ends at its load.
        branches = []
        current = []
        for x in trace.x:
            if x is None:
                branches.append(current)
                current = []
            else:
                current.append(x)
        if current:
            branches.append(current)
        assert all(branch == sorted(branch) for branch in branches)


def test_every_net_color_and_hover_contains_source_hierarchy(full_add):
    before = full_add.to_json()
    values = net_values(full_add, {"a": 1, "b": 1, "cin": -1})
    assert set(values) == full_add.nets()
    assert values["sum"] == 1 and values["cout"] == 0
    by_name = {inst.name: inst for inst in full_add.instances}
    assert values[by_name["ha1.g_c"].pins["Y"]] == 1
    assert values[by_name["ha1.g_s"].pins["Y"]] == -1
    fig = color_nets(full_add, {"a": 1, "b": 1, "cin": -1})
    assert dict(fig.layout.meta["net_values"]) == values
    for trace in traces(fig, "net"):
        value = values[trace.meta["net"]]
        assert trace.meta["value"] == value
        assert trace.line.color == TRIT_COLORS[value]
        assert all("Hierarchy:" in text and "Value:" in text and "Cell:" in text for text in trace.text)
    for trace in traces(fig, "nodes"):
        assert "Hierarchy:" in trace.hovertemplate and "Value:" in trace.hovertemplate
        for row in trace.customdata:
            assert row[5] in {"-1", "0", "+1"}
    gate_rows = {row[0]: row for trace in traces(fig, "nodes") for row in trace.customdata}
    assert gate_rows["ha1.g_c"][2] == "ha1"
    assert full_add.to_json() == before


def test_signal_legend_always_contains_all_three_values():
    n = synthesize(loads("module m(input trit a,output trit y); assign y=a; endmodule"))
    fig = color_nets(n, {"a": 0})
    legend = traces(fig, "signal_legend")
    assert [trace.meta["value"] for trace in legend] == [-1, 0, 1]
    assert [trace.name for trace in legend] == ["-1 (−5 V)", "0 (0 V)", "+1 (+5 V)"]
    assert len({trace.line.color for trace in legend}) == 3


def test_arbitrary_json_order_and_loaded_dataclass(full_add, tmp_path):
    path = tmp_path / "fa.json"
    full_add.save(path)
    net = GateNetlist.load(path)
    net.instances.reverse()
    first = gate_graph(full_add, {"a": -1, "b": 0, "cin": 1})
    second = gate_graph(net, {"a": -1, "b": 0, "cin": 1})
    first_levels = {row[0]: row[4] for trace in traces(first, "nodes") for row in trace.customdata}
    second_levels = {row[0]: row[4] for trace in traces(second, "nodes") for row in trace.customdata}
    assert first_levels == second_levels
    assert first.layout.meta["net_values"] == second.layout.meta["net_values"]


def test_ties_unloaded_nets_and_port_instance_name_collision():
    const = synthesize(loads("module m(output trit [2:0] y); assign y=3'tT01; endmodule"))
    fig = color_nets(const, {})
    assert set(fig.layout.meta["net_values"].values()) == {-1, 0, 1}
    n = GateNetlist("m", [Port("a", "input"), Port("unused", "input"), Port("g", "output")],
                    [Instance("g", "INV", {"A": "a", "Y": "g"})])
    fig = color_nets(n, {"a": -1, "unused": 1})
    assert sum(len(trace.x) for trace in traces(fig, "nodes")) == 4
    unused = next(trace for trace in traces(fig, "net") if trace.meta["net"] == "unused")
    assert unused.line.color == TRIT_COLORS[1] and len(unused.x) == 2


def test_empty_design_graph_serializes_without_special_renderer():
    fig = gate_graph(synthesize(loads("module empty(); endmodule")))
    assert fig.layout.meta["top"] == "empty"
    assert "plotly" in fig.to_html(include_plotlyjs=False).lower()


@pytest.mark.parametrize("inputs, message", [
    ({"a": 1, "b": 0}, "expected inputs"),
    ({"a": 5, "b": 0, "cin": 1}, "outside trits"),
    ({"a": 0.25, "b": 0, "cin": 1}, "outside trits"),
    ({"a": [-1], "b": 0, "cin": 1}, "scalar trit"),
])
def test_invalid_coloring_inputs(full_add, inputs, message):
    with pytest.raises(ValueError, match=message):
        color_nets(full_add, inputs)


def test_cyclic_or_undriven_netlist_is_rejected():
    n = GateNetlist("bad", [Port("y", "output")], [Instance("g", "INV", {"A": "y", "Y": "y"})])
    with pytest.raises(ValueError, match="cycle"):
        gate_graph(n)


class TableRows(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []
        self.cell = None

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.rows.append([])
        if tag in {"th", "td"}:
            self.cell = []

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if tag in {"th", "td"}:
            self.rows[-1].append("".join(self.cell))
            self.cell = None


def test_truth_table_source_and_mapped_all_rows_match_integer_reference():
    d = load("examples/half_add.tv", top="half_add")
    source = truth_table_html(d)
    mapped = truth_table_html(synthesize(d))
    assert isinstance(source, str) and source._repr_html_() == str(source)
    assert source == mapped
    parser = TableRows()
    parser.feed(source)
    assert parser.rows[0] == ["Vector", "ainput", "binput", "sumoutput", "carryoutput"]
    assert len(parser.rows) == 10
    for index, row in enumerate(parser.rows[1:]):
        number, a, b, s, c = map(int, row)
        assert number == index + 1
        assert a == index // 3 - 1 and b == index % 3 - 1
        assert a + b == s + 3*c


def test_table_size_guard_before_evaluation(monkeypatch):
    d = load("examples/adder.tv", top="adder")

    def forbidden(*args):
        raise AssertionError("large truth table must not be evaluated")

    monkeypatch.setattr(d, "evaluate", forbidden)
    with pytest.raises(ValueError, match="19683 rows"):
        truth_table_html(d)
    d = loads("module m(input trit [4:0] a,output trit y); assign y=a[0]; endmodule")
    assert "all 243 input vectors" in truth_table_html(d, max_rows=243)


@pytest.mark.parametrize("limit", [0, -1, True, 1.5])
def test_truth_table_invalid_row_limits(limit):
    with pytest.raises(ValueError, match="positive integer"):
        truth_table_html(loads("module m(); endmodule"), max_rows=limit)


def test_html_escape_and_constant_table():
    net = GateNetlist('<script>alert("top")</script>',
                      [Port("<img>", "input"), Port("out&", "output")],
                      [Instance("g<script>", "INV", {"A": "<img>", "Y": "out&"}, "<b>scope</b>")])
    html = truth_table_html(net)
    assert "<script>" not in html and "<img>" not in html
    assert "&lt;script&gt;" in html and "&lt;img&gt;" in html and "out&amp;" in html
    fig = color_nets(net, {"<img>": 0})
    assert "<script>" not in fig.layout.title.text
    for trace in traces(fig, "nodes"):
        assert all("<script>" not in row[0] for row in trace.customdata)
    constant = synthesize(loads("module c(output trit y); assign y=1'tT; endmodule"))
    assert "all 1 input vectors" in truth_table_html(constant)


def test_return_all_cell_evaluation_preserves_default_api(full_add):
    inputs = {"a": np.array([-1, 0, 1]), "b": 0, "cin": 1}
    all_nets = evaluate_netlist(full_add, inputs, return_all=True)
    outputs = evaluate_netlist(full_add, inputs)
    assert set(all_nets) == full_add.nets()
    assert set(outputs) == {"sum", "cout"}
    for name, value in outputs.items():
        np.testing.assert_array_equal(value, all_nets[name])
