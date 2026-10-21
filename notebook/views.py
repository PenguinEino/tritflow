"""Chapter views for the v2 notebook: pick an input and see the circuit and its waveform.

Every number shown comes from the objects the reader's own cells just made; nothing here
reruns a tool.
"""

from html import escape
from itertools import product

from IPython.display import HTML, display

from live import FONT, DIM

TRIT_TEXT = {-1: "−1", 0: "0", 1: "+1"}


def stimulus(net, limit=27):
    """Input vectors for a post-layout run: a there-and-back sweep for one input, every
    combination for a few, a deterministic subset beyond ``limit``."""
    inputs = [p.name for p in net.ports if p.dir == "input"]
    if len(inputs) == 1:
        return [(-1,), (0,), (1,), (0,), (-1,)]
    vectors = list(product((-1, 0, 1), repeat=len(inputs)))
    return vectors if len(vectors) <= limit else vectors[::max(1, len(vectors)//limit)][:limit]


def _intervals(post, chosen):
    """The stretches of the post-layout run where the inputs equal ``chosen``, in µs."""
    hold = post["stimulus"]["hold_s"]*1e6
    spans = [f"{i*hold:g}–{(i+1)*hold:g} µs" for i, row in enumerate(post["measurements"]["rows"])
             if tuple(row["input_trits"]) == chosen]
    return ("波形の " + "、".join(spans)) if spans else ""


def _reading(post, chosen):
    rows = [r for r in post["measurements"]["rows"] if tuple(r["input_trits"]) == chosen]
    if not rows:
        return "この入力の組合せはSPICEで流していない。回路図の値は論理値。"
    return "、".join(f"{pin} = {value['voltage_v']:+.2f} V（理想 {value['ideal_voltage_v']:+.0f} V）"
                    for pin, value in rows[0]["outputs"].items())


_PICKS = 0
HIGHLIGHT = {"type": "rect", "xref": "x", "yref": "paper", "y0": 0, "y1": 1, "layer": "below",
             "fillcolor": "#e8782a", "opacity": .28, "line": {"width": 0}}


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


def pick_input(net, post, *, title="ポストレイアウトシミュレーション"):
    """The post-layout waveform (zoomable, simulator style) with input buttons. A button marks
    its stretches on the waveform and shows the schematic with net values and the truth table
    with that row marked. Schematic and table switch by CSS alone; the waveform marks need the
    Plotly script, which Colab and Jupyter run."""
    import json
    from tritflow.viz.waves import waveform_scope
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

    scope = waveform_scope(post, title=title)
    base = scope.to_plotly_json()["layout"].get("shapes", [])
    marks = [[{**HIGHLIGHT, "x0": i*hold, "x1": (i+1)*hold} for i, row in enumerate(rows)
              if tuple(row["input_trits"]) == chosen] for chosen in choices]
    scope.update_layout(shapes=[*base, *marks[start]], paper_bgcolor="#0d1117", height=min(scope.layout.height, 560))
    scope.update_xaxes(range=[0, len(rows)*hold])
    plot = scope.to_html(include_plotlyjs="cdn", full_html=False, div_id=f"{key}-scope",
                         config={"displaylogo": False, "scrollZoom": True})

    radios, panels, rules = [], [], []
    for index, chosen in enumerate(choices):
        label = ", ".join(f"{name} = {TRIT_TEXT[v]}" for name, v in zip(inputs, chosen))
        radios.append(f'<input type="radio" name="{key}" id="{key}-{index}" data-i="{index}"'
                      f'{" checked" if index == start else ""}><label for="{key}-{index}">{escape(label)}</label>')
        circuit = net.schematic(inputs=dict(zip(inputs, chosen)), net_names=True, expand="*", title=label)
        reading = " · ".join(part for part in (_reading(post, chosen), _intervals(post, chosen)) if part)
        panels.append(f'<div class="p{index}"><div class="reading">{escape(reading)}</div><div class="row">'
                      f'<div class="sch">{circuit._repr_svg_()}</div>'
                      f'{_truth_table(net, inputs, outputs, table_rows, chosen)}</div></div>')
        rules.append(f"#{key}-{index}:checked ~ .p{index}{{display:block}}")
    style = (f".{key}{{max-width:1180px}} .{key} input{{display:none}}"
             f".{key} label{{display:inline-block;padding:.3em 1em;margin:0 .35em .5em 0;border:1px solid #c9ccd1;"
             f"border-radius:4px;cursor:pointer;font-size:14px}}"
             f".{key} input:checked + label{{background:#e8782a;color:#fff;border-color:#e8782a}}"
             f".{key} > div[class^=p]{{display:none}} .{key} .reading{{margin:.2em 0 .6em;font-size:14px}}"
             f".{key} .row{{display:flex;flex-wrap:wrap;gap:1.5em;align-items:center}}"
             f".{key} .sch{{flex:3 1 520px;min-width:0}} .{key} .sch svg{{width:100%;height:auto;display:block}}"
             f".{key} .tt{{flex:0 0 auto;border-collapse:collapse;font-size:15px}}"
             f".{key} .tt td, .{key} .tt th{{border:1px solid #d5d7db;padding:.3em .8em;text-align:center}}"
             f".{key} .tt th{{background:#f3f4f6;font-weight:700}} .{key} .tt th.mid{{background:#fafafa;color:#59606b;font-weight:600}}"
             f".{key} .tt th small{{display:block;font-size:10px;font-weight:400;color:{DIM}}}"
             f".{key} .tt td.t0{{color:#2f6fbf}} .{key} .tt td.t2{{color:#c8423b}} .{key} .tt td.t1{{color:#6b7280}}"
             f".{key} .tt tr.on td{{background:#e8782a26;font-weight:700}}"
             f".{key} .scope{{background:#0d1117;border-radius:12px;padding:8px 6px 2px;margin:.3em 0 1em;"
             f"box-shadow:0 0 0 1px #d5d7db, 0 6px 18px -8px rgba(13,17,23,.55)}}"
             f".{key} .hint{{color:{DIM};margin:1em 0 .2em}}" + "".join(rules))
    script = (f"<script>(function(){{var marks={json.dumps(marks)},base={json.dumps(base)};"
              f"document.querySelectorAll('input[name={key}]').forEach(function(r){{r.addEventListener('change',function(){{"
              f"var d=document.getElementById('{key}-scope');if(window.Plotly&&d)"
              f"Plotly.relayout(d,{{shapes:base.concat(marks[+r.dataset.i])}});}});}});}})();</script>")
    display(HTML(f'<style>{style}</style><div class="{key}" style="{FONT}">{"".join(radios)}{"".join(panels)}'
                 f'<div class="hint">ドラッグで拡大、ダブルクリックで全体に戻る。下のスライダーで時間の範囲を選べる。</div>'
                 f'<div class="scope">{plot}</div></div>{script}'))
