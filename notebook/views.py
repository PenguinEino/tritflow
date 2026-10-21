"""Chapter views for the v2 notebook: pick an input and see the circuit and its waveform.

Every number shown comes from the objects the reader's own cells just made; nothing here
reruns a tool.
"""

from html import escape
from itertools import product

from IPython.display import HTML, display

from style import (ACCENT, BAND, CURRENT_COLOR, INK, INPUT_COLORS, MUTED, OUTPUT_COLORS, TRIT_TEXT, control_style,
                   figure_css, paper_axes, paper_layout, table_css)


def stimulus(net, limit=27):
    """Input vectors for a post-layout run: a there-and-back sweep for one input, every
    combination for a few, a deterministic subset beyond ``limit``."""
    inputs = [p.name for p in net.ports if p.dir == "input"]
    if len(inputs) == 1:
        return [(-1,), (0,), (1,), (0,), (-1,)]
    vectors = list(product((-1, 0, 1), repeat=len(inputs)))
    return vectors if len(vectors) <= limit else vectors[::max(1, len(vectors)//limit)][:limit]


def _reading(post, chosen):
    rows = [r for r in post["measurements"]["rows"] if tuple(r["input_trits"]) == chosen]
    if not rows:
        return "この入力の組合せはSPICEで流していない。回路図の値は論理値。"
    return "、".join(f"{pin} = {value['voltage_v']:+.2f} V（理想 {value['ideal_voltage_v']:+.0f} V）"
                    for pin, value in rows[0]["outputs"].items())


_PICKS = 0
HIGHLIGHT = {"type": "rect", "xref": "x", "yref": "paper", "y0": 0, "y1": 1, "layer": "below",
             "fillcolor": ACCENT, "opacity": .14, "line": {"width": 0}}


def scope_figure(post, *, title=None):
    """Post-layout transient in the paper style: one lane per input and output with the ±0.5 V
    bands and the checker's sample points, then the VDD current; a range slider under it."""
    import numpy as np
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    from tritflow import PASS_BAND
    from tritflow.sim.spice import signal_waveform

    stimulus, waves = post["stimulus"], post["waveforms"]
    lanes = [("v", p) for p in stimulus["inputs"]] + [("v", p) for p in stimulus["outputs"]] + [("i", "VDD")]
    t = np.asarray(waves["time"])*1e6
    rows = post["measurements"]["rows"]
    figure = make_subplots(rows=len(lanes), cols=1, shared_xaxes=True, vertical_spacing=.035)
    for row, (kind, name) in enumerate(lanes, 1):
        if kind == "v":
            for level in (-5, 0, 5):
                figure.add_hrect(y0=level-PASS_BAND, y1=level+PASS_BAND, fillcolor=BAND, opacity=1, line_width=0,
                                 layer="below", row=row, col=1, exclude_empty_subplots=False)
            output = name in stimulus["outputs"]
            group, palette = (stimulus["outputs"], OUTPUT_COLORS) if output else (stimulus["inputs"], INPUT_COLORS)
            color = palette[group.index(name) % len(palette)]
            figure.add_trace(go.Scatter(x=t, y=signal_waveform(waves, name), mode="lines", name=name, showlegend=False,
                                        line={"color": color, "width": 2.4},
                                        hovertemplate=f"{name} %{{y:.3f}} V<extra></extra>"), row=row, col=1)
            if output:
                figure.add_trace(go.Scatter(
                    x=[r["check_s"]*1e6 for r in rows], y=[r["outputs"][name]["voltage_v"] for r in rows],
                    mode="markers", showlegend=False, hoverinfo="skip",
                    marker={"symbol": ["circle-open" if r["outputs"][name]["passed"] else "x" for r in rows],
                            "size": 7, "color": [INK if r["outputs"][name]["passed"] else ACCENT for r in rows],
                            "line": {"width": 1.3}}), row=row, col=1)
            figure.update_yaxes(range=[-6.2, 6.2], tickvals=[-5, 0, 5], title_text=f"{name} (V)",
                                title_font={"color": color}, row=row, col=1)
        else:
            figure.add_trace(go.Scatter(x=t, y=np.abs(np.asarray(waves["i(vdd)"]))*1e3, mode="lines", showlegend=False,
                                        line={"color": CURRENT_COLOR, "width": 2},
                                        hovertemplate="|I(VDD)| %{y:.3f} mA<extra></extra>"), row=row, col=1)
            figure.update_yaxes(title_text="|I<sub>VDD</sub>| (mA)", row=row, col=1)
    paper_axes(figure)
    figure.update_xaxes(range=[0, len(rows)*stimulus["hold_s"]*1e6])
    figure.update_xaxes(title_text="time (µs)", rangeslider={"visible": True, "thickness": .05, "bgcolor": "#f6f5f1"},
                        row=len(lanes), col=1)
    figure.update_layout(**paper_layout(height=150*len(lanes)+110, hovermode="x unified",
                                        margin={"t": 40 if title else 15, "l": 70, "r": 15, "b": 40},
                                        title={"text": title, "font": {"size": 15}, "x": 0} if title else None))
    return figure


def _truth_table(net, inputs, outputs, rows, chosen):
    """Truth table with every internal net (named by the gate that drives it) between inputs
    and outputs; the chosen input row is marked."""
    from tritflow.synth.simulate import CELL_INPUTS, evaluate_netlist, ordered_instances
    ports = {*inputs, *outputs}
    inner = [(inst.name, inst.cell, net_name) for inst in ordered_instances(net)
             for pin, net_name in inst.pins.items()
             if pin not in CELL_INPUTS[inst.cell] and net_name not in ports]
    head = ("".join(f'<th class="io">{escape(n)}</th>' for n in inputs)
            + "".join(f'<th class="mid">{escape(name)}<small>{escape(cell)}</small></th>' for name, cell, _ in inner)
            + "".join(f'<th class="io">{escape(n)}</th>' for n in outputs))
    body = []
    for vector in rows:
        values = evaluate_netlist(net, dict(zip(inputs, vector)), return_all=True)
        cells = [*vector, *(int(values[n]) for _, _, n in inner), *(int(values[n]) for n in outputs)]
        mark = ' class="on"' if vector == chosen else ""
        body.append(f"<tr{mark}>" + "".join(f'<td class="t{v+1}">{TRIT_TEXT[v]}</td>' for v in cells) + "</tr>")
    return f'<table class="tt"><tr>{head}</tr>{"".join(body)}</table>'


def pick_input(net, post):
    """Input buttons over the schematic (net values in colour) beside the truth table with the
    chosen row marked, then the zoomable post-layout waveform with the chosen stretches shaded.
    Schematic and table switch by CSS alone; the waveform shading needs Plotly's script."""
    import json
    global _PICKS
    _PICKS += 1
    key = f"tfpick{_PICKS}"
    inputs = [p.name for p in net.ports if p.dir == "input"]
    outputs = [p.name for p in net.ports if p.dir == "output"]
    rows = post["measurements"]["rows"]
    hold = post["stimulus"]["hold_s"]*1e6
    choices = sorted(dict.fromkeys(tuple(row["input_trits"]) for row in rows))
    start = choices.index((0,)*len(inputs)) if (0,)*len(inputs) in choices else 0
    table_rows = list(product((-1, 0, 1), repeat=len(inputs))) if len(inputs) <= 3 else choices

    scope = scope_figure(post)
    base = scope.to_plotly_json()["layout"].get("shapes", [])
    marks = [[{**HIGHLIGHT, "x0": i*hold, "x1": (i+1)*hold} for i, row in enumerate(rows)
              if tuple(row["input_trits"]) == chosen] for chosen in choices]
    scope.update_layout(shapes=[*base, *marks[start]])
    plot = scope.to_html(include_plotlyjs="cdn", full_html=False, div_id=f"{key}-scope",
                         config={"displaylogo": False, "scrollZoom": True})

    radios, panels, rules = [], [], []
    for index, chosen in enumerate(choices):
        label = ", ".join(f"{name} = {TRIT_TEXT[v]}" for name, v in zip(inputs, chosen))
        radios.append(f'<input type="radio" name="{key}" id="{key}-{index}" data-i="{index}"'
                      f'{" checked" if index == start else ""}><label for="{key}-{index}">{escape(label)}</label>')
        circuit = net.schematic(inputs=dict(zip(inputs, chosen)), net_names=True, expand="*", title="", legend=False)
        panels.append(f'<div class="p{index}"><div class="reading">{escape(_reading(post, chosen))}</div><div class="row">'
                      f'<div class="sch">{circuit._repr_svg_()}</div>'
                      f'{_truth_table(net, inputs, outputs, table_rows, chosen)}</div></div>')
        rules.append(f"#{key}-{index}:checked ~ .p{index}{{display:block}}")
    style = (figure_css(f".{key}") + control_style(f".{key}") + table_css(f".{key}") + f".{key}{{max-width:1080px}}"
             f".{key} > div[class^=p]{{display:none}} .{key} .reading{{margin:.1em 0 .4em}}"
             f".{key} .row{{display:flex;flex-wrap:wrap;gap:1.5em;align-items:center}}"
             f".{key} .sch{{flex:3 1 480px;min-width:0}} .{key} .sch svg{{width:100%;height:auto;display:block}}"
             f".{key} .hint{{color:{MUTED};font-size:13px;margin:.8em 0 0}}" + "".join(rules))
    script = (f"<script>(function(){{var marks={json.dumps(marks)},base={json.dumps(base)};"
              f"document.querySelectorAll('input[name={key}]').forEach(function(r){{r.addEventListener('change',function(){{"
              f"var d=document.getElementById('{key}-scope');if(window.Plotly&&d)"
              f"Plotly.relayout(d,{{shapes:base.concat(marks[+r.dataset.i])}});}});}});}})();</script>")
    display(HTML(f'<style>{style}</style><div class="{key}">{"".join(radios)}{"".join(panels)}'
                 f'<div class="hint">ドラッグで拡大、ダブルクリックで全体に戻る。下のスライダーで時間の範囲を選べる。</div>'
                 f'{plot}</div>{script}'))
