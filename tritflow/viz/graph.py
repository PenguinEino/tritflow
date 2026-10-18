"""Notebook gate graphs and small truth tables for ideal balanced-ternary logic.

``gate_graph(net)`` draws the synthesized circuit by logic level, with cell-type
fills. ``color_nets(net, {"a": -1, "b": 1})`` evaluates one input vector and
colors every signal wire blue/gray/red for -1/0/+1. Hover exposes the authored
hierarchy, cell function's output value and input-pin values. These are settled
logic levels; the horizontal axis counts cell stages, not placement or delay.

``truth_table_html(design)`` returns a pandas-free string with an HTML rich
representation, suitable for a notebook's final expression or ``display()``.
Import these helpers directly from this module; no notebook renderer is set
globally and no browser or display is opened by these functions.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from html import escape
from typing import Mapping

import numpy as np
import plotly.graph_objects as go

from tritflow.hdl.ir import Design, input_batches
from tritflow.netlist import GateNetlist
from tritflow.synth.simulate import CELL_INPUTS, evaluate_netlist, ordered_instances


TRIT_COLORS = {-1: "#2166ac", 0: "#616161", 1: "#b2182b"}
CELL_COLORS = {
    "INV": "#9467bd", "NAND": "#e69f00", "NOR": "#59a14f", "NANY": "#17a2a4",
    "BUF": "#4e79a7", "TIEN": "#8cb4d8", "TIEZ": "#bdbdbd", "TIEP": "#e69ca6",
}
_NEUTRAL = "#a0a6ad"


def _value_text(value: int | None) -> str:
    if value is None:
        return "not evaluated"
    return f"{value:+d}" if value else "0"


def net_values(net: GateNetlist, inputs: Mapping[str, int]) -> dict[str, int]:
    """Return every signal net's ideal trit for exactly one scalar input vector.

    Keys must match all bit-blasted input ports, such as ``a[0]``. Values must
    be -1, 0 or +1; voltage values and batches are rejected. Constants and unused
    primary inputs are included, so the result covers ``net.nets()`` exactly.
    """
    if any(np.asarray(value).ndim != 0 for value in inputs.values()):
        raise ValueError("gate coloring requires one scalar trit per input, not a batch")
    return {name: int(value) for name, value in evaluate_netlist(net, dict(inputs), return_all=True).items()}


@dataclass
class _Node:
    key: tuple[str, str]
    cell: str
    hier: str
    net: str
    level: int
    pins: dict[str, str]


def _structure(net):
    """Longest-path levels and stable barycenter ordering, without Graphviz."""
    ordered = ordered_instances(net)
    nodes, drivers, loads = {}, {}, defaultdict(list)
    for port in net.ports:
        if port.dir == "input":
            key = ("input", port.name)
            nodes[key] = _Node(key, "INPUT", "<top>", port.name, 0, {})
            drivers[port.name] = key
    for inst in ordered:
        key = ("cell", inst.name)
        level = 1 + max((nodes[drivers[inst.pins[p]]].level for p in CELL_INPUTS[inst.cell]), default=0)
        nodes[key] = _Node(key, inst.cell, inst.hier or "<top>", inst.pins["Y"], level, inst.pins)
        for pin in CELL_INPUTS[inst.cell]:
            loads[inst.pins[pin]].append((key, pin))
        drivers[inst.pins["Y"]] = key
    output_level = 1 + max((node.level for node in nodes.values()), default=0)
    for port in net.ports:
        if port.dir == "output":
            key = ("output", port.name)
            nodes[key] = _Node(key, "OUTPUT", "<top>", port.name, output_level, {})
            loads[port.name].append((key, "port"))
    groups, parents = defaultdict(list), defaultdict(list)
    for key, node in nodes.items():
        groups[node.level].append(key)
    for name, sinks in loads.items():
        for key, _ in sinks:
            parents[key].append(drivers[name])
    positions = {}
    for level, keys in sorted(groups.items()):
        def barycenter(key):
            ys = [positions[parent][1] for parent in parents[key]]
            return -sum(ys) / len(ys) if ys else 0

        keys.sort(key=barycenter)  # stable for equal centers and declared input order
        for index, key in enumerate(keys):
            positions[key] = (level, (len(keys) - 1) / 2 - index)
    return nodes, drivers, loads, positions


def _wire_trace(name, driver, sinks, positions, values):
    """A signal is one trace with all fanout branches, including unused stubs."""
    x0, y0 = positions[driver.key]
    xs, ys = [], []
    arrows = []
    for sink, pin in sinks:
        x1, y1 = positions[sink]
        y1 += {"A": 0.07, "B": -0.07}.get(pin, 0)
        start, stop = x0 + 0.12, x1 - 0.14
        middle = (start + stop) / 2
        xs.extend([start, middle, middle, stop, None])
        ys.extend([y0, y0, y1, y1, None])
        arrows.append((stop, y1))
    if not sinks:
        xs, ys = [x0 + 0.12, x0 + 0.35], [y0, y0]
    value = values[name] if values is not None else None
    color = TRIT_COLORS[value] if value is not None else _NEUTRAL
    hover = (f"Net: {escape(name)}<br>Cell: {driver.cell}<br>"
             f"Driver: {escape(driver.key[1])}<br>Hierarchy: {escape(driver.hier)}<br>"
             f"Value: {_value_text(value)}<br>Loads: " +
             (", ".join(escape(f"{key[1]}.{pin}") for key, pin in sinks) or "none"))
    trace = go.Scatter(x=xs, y=ys, mode="lines", line={"color": color, "width": 2},
                       text=[hover] * len(xs), hovertemplate="%{text}<extra></extra>",
                       name=name, showlegend=False,
                       meta={"kind": "net", "net": name, "value": value})
    annotations = [dict(x=x, y=y, ax=x-0.12, ay=y, xref="x", yref="y", axref="x", ayref="y",
                        showarrow=True, arrowhead=2, arrowsize=0.8, arrowwidth=1.5,
                        arrowcolor=color, text="") for x, y in arrows]
    return trace, annotations


def gate_graph(net: GateNetlist, inputs: Mapping[str, int] | None = None, *,
               title: str | None = None) -> go.Figure:
    """Draw a synthesized netlist left-to-right by longest input-to-gate path.

    Gate fills always encode cell type. Supplying ``inputs`` colors all nets by
    their ideal trit, with a three-entry signal legend; omitting it draws neutral
    wires. Ports use distinct marker shapes, and output ports occupy the final
    column. Every gate and wire exposes hierarchy/value in hover. Pan/zoom works
    with the normal Plotly notebook renderer; call ``fig.show()`` to display.
    A plain ``GateNetlist.load(...)`` is sufficient; synthesis metadata is not
    required, and instance order in the JSON does not affect logic levels.
    """
    nodes, drivers, loads, positions = _structure(net)
    values = net_values(net, inputs) if inputs is not None else None
    fig = go.Figure()
    annotations = []
    for name, driver in drivers.items():
        trace, arrows = _wire_trace(name, nodes[driver], loads[name], positions, values)
        fig.add_trace(trace)
        annotations.extend(arrows)
    by_cell = defaultdict(list)
    for node in nodes.values():
        by_cell[node.cell].append(node)
    for cell, group in by_cell.items():
        is_port = cell in {"INPUT", "OUTPUT"}
        customdata, labels = [], []
        for node in group:
            value = values[node.net] if values is not None else None
            pins = "<br>".join(
                f"{pin}: {escape(name)} = {_value_text(values[name] if values is not None else None)}"
                for pin, name in node.pins.items()
            ) or "port"
            customdata.append([escape(node.key[1]), cell, escape(node.hier), escape(node.net),
                               node.level, _value_text(value), pins])
            labels.append(escape(node.key[1] if is_port else node.key[1].split(".")[-1]))
        symbol = {"INPUT": "circle", "OUTPUT": "triangle-right"}.get(cell, "square")
        fig.add_trace(go.Scatter(
            x=[positions[n.key][0] for n in group], y=[positions[n.key][1] for n in group],
            mode="markers+text", text=labels, textposition="top center", textfont={"size": 10},
            marker={"color": CELL_COLORS.get(cell, "#ffffff"), "size": 19 if is_port else 23,
                    "symbol": symbol, "line": {"color": "#384152", "width": 1}},
            customdata=customdata,
            hovertemplate=("%{customdata[0]}<br>Cell: %{customdata[1]}<br>Hierarchy: %{customdata[2]}"
                           "<br>Output net: %{customdata[3]}<br>Logic level: %{customdata[4]}"
                           "<br>Value: %{customdata[5]}<br>%{customdata[6]}<extra></extra>"),
            name=cell if is_port else f"Cell: {cell}", legendgroup="ports" if is_port else "cells",
            meta={"kind": "nodes", "cell": cell},
        ))
    legend_entries = [(None, "Net (not evaluated)", _NEUTRAL)] if values is None else [
        (-1, "-1 (−5 V)", TRIT_COLORS[-1]), (0, "0 (0 V)", TRIT_COLORS[0]),
        (1, "+1 (+5 V)", TRIT_COLORS[1]),
    ]
    for value, label, color in legend_entries:
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="lines", line={"color": color, "width": 3},
                                name=label, legendgroup="signals", hoverinfo="skip",
                                meta={"kind": "signal_legend", "value": value}))
    levels = [node.level for node in nodes.values()]
    row_count = max((sum(node.level == level for node in nodes.values()) for level in set(levels)), default=1)
    fig.update_layout(
        title={"text": escape(title if title is not None else f"{net.top}: gate graph")},
        template="plotly_white", height=max(420, min(1200, 180 + 60 * row_count)),
        margin={"l": 65, "r": 180, "t": 70, "b": 55},
        xaxis={"title": "Logic level →", "dtick": 1, "range": [-0.5, max(levels, default=0)+0.6],
               "zeroline": False},
        yaxis={"visible": False, "range": [-row_count/2-0.6, row_count/2+0.8]},
        legend={"title": {"text": "Cells / signal levels"}, "groupclick": "toggleitem"},
        hovermode="closest", dragmode="pan", annotations=annotations,
        meta={"top": net.top, "net_values": values},
    )
    return fig


def color_nets(net: GateNetlist, inputs: Mapping[str, int], *, title: str | None = None) -> go.Figure:
    """Create a gate graph with every net colored -1/0/+1 for one input vector.

    This returns a fresh figure and leaves the netlist unchanged. Node fill
    remains cell type, while both wire color and hover text expose signal value.
    """
    return gate_graph(net, inputs, title=title)


class TruthTableHTML(str):
    """HTML string that a notebook can display directly without importing pandas."""

    def _repr_html_(self) -> str:
        return str(self)


def truth_table_html(design: Design | GateNetlist, *, max_rows: int = 81) -> TruthTableHTML:
    """Display every input combination of a small source or synthesized circuit.

    Columns follow port order and identify input/output direction. Rows enumerate
    -1, 0, +1 in the same order as ``Design.truth_table()``. The row limit is
    checked before simulation; larger designs require an explicit higher limit,
    rather than displaying a silently truncated truth table. All names are HTML
    escaped and trit cells use the graph's three signal colors plus numeric text.
    """
    if not isinstance(max_rows, int) or isinstance(max_rows, bool) or max_rows < 1:
        raise ValueError("max_rows must be a positive integer")
    names = [p.name for p in design.ports if p.dir == "input"]
    count = 3 ** len(names)
    if count > max_rows:
        raise ValueError(f"truth table has {count} rows; increase max_rows={max_rows} explicitly")
    if isinstance(design, GateNetlist):
        ordered = ordered_instances(design)

        def evaluate(inputs):
            return evaluate_netlist(design, inputs, ordered=ordered)
    else:
        evaluate = design.evaluate
    parts = ['<div class="tritflow-truth" style="overflow-x:auto">',
             '<table style="border-collapse:collapse;text-align:center">',
             f'<caption>{escape(design.top)}: all {count} input vectors (trits −1, 0, +1)</caption>',
             '<thead><tr><th scope="col">Vector</th>']
    for port in design.ports:
        parts.append(f'<th scope="col" style="padding:0.4em 0.8em">{escape(port.name)}'
                     f'<br><small>{escape(port.dir)}</small></th>')
    parts.append('</tr></thead><tbody>')
    row_index = 0
    for inputs in input_batches(names, count, exhaustive=True):
        outputs = evaluate(inputs)
        columns = {**inputs, **outputs}
        size = len(next(iter(inputs.values()))) if inputs else 1
        arrays = {name: np.broadcast_to(value, (size,)) for name, value in columns.items()}
        for row in range(size):
            row_index += 1
            parts.append(f'<tr><th scope="row">{row_index}</th>')
            for port in design.ports:
                value = int(arrays[port.name][row])
                parts.append(f'<td data-trit="{value}" style="padding:0.3em 0.8em;'
                             f'border-top:1px solid #ddd;color:{TRIT_COLORS[value]}">{_value_text(value)}</td>')
            parts.append('</tr>')
    parts.append('</tbody></table></div>')
    return TruthTableHTML("".join(parts))


__all__ = ["CELL_COLORS", "TRIT_COLORS", "gate_graph", "color_nets", "net_values", "truth_table_html"]
