"""Chapter views for the v2 notebook: pick an input and see the circuit and its waveform, and
the map of what one run did.

Every number shown comes from the objects the reader's own cells just made; nothing here
reruns a tool.
"""

from html import escape
from itertools import product

from IPython.display import HTML, display

from live import FONT, DIM

TRITFLOW, EXISTING = "#e8782a", "#7d8794"
TRIT_TEXT = {-1: "−1", 0: "0", 1: "+1"}


def stimulus(net, limit=27):
    """Input vectors for a post-layout run: a there-and-back sweep for one input, every
    combination for a few, a deterministic subset beyond ``limit``."""
    inputs = [p.name for p in net.ports if p.dir == "input"]
    if len(inputs) == 1:
        return [(-1,), (0,), (1,), (0,), (-1,)]
    vectors = list(product((-1, 0, 1), repeat=len(inputs)))
    return vectors if len(vectors) <= limit else vectors[::max(1, len(vectors)//limit)][:limit]


def _waveform(post, chosen, title):
    from tritflow.viz.waves import waveform_figure
    figure = waveform_figure(post, title=title, annotate_settling=None)
    hold = post["stimulus"]["hold_s"]*1e9
    for index, row in enumerate(post["measurements"]["rows"]):
        if tuple(row["input_trits"]) == chosen:
            figure.add_vrect(x0=index*hold, x1=(index+1)*hold, fillcolor="#e8782a", opacity=.13,
                             line_width=0, exclude_empty_subplots=False)
    figure.update_layout(height=260+120*len(post["stimulus"]["outputs"]), margin={"t": 60})
    return figure


def _reading(post, chosen):
    rows = [r for r in post["measurements"]["rows"] if tuple(r["input_trits"]) == chosen]
    if not rows:
        return "この入力の組合せは、SPICEでは流していません。回路図の値は論理の計算です。"
    parts = []
    for pin, value in rows[0]["outputs"].items():
        band = "帯の中" if value["passed"] else "帯の外"
        parts.append(f"{pin} = {value['voltage_v']:+.2f} V（理想 {TRIT_TEXT[value['ideal_trit']]}、"
                     f"{value['ideal_voltage_v']:+.0f} V ±0.5 V の{band}）")
    return "SPICE：" + "、".join(parts)


def pick_input(net, post):
    """Buttons for each input trit; the circuit's net values and the matching stretch of the
    post-layout waveform follow the choice."""
    import ipywidgets as widgets
    from tritflow.viz.graph import color_nets

    inputs = [p.name for p in net.ports if p.dir == "input"]
    buttons = {name: widgets.ToggleButtons(options=[("−1", -1), ("0", 0), ("+1", 1)], value=0,
                                           description=f"{name} =", style={"button_width": "56px"})
               for name in inputs}
    out = widgets.Output()

    def draw(_=None):
        chosen = tuple(buttons[name].value for name in inputs)
        label = ", ".join(f"{name} = {TRIT_TEXT[v]}" for name, v in zip(inputs, chosen))
        circuit = color_nets(net, dict(zip(inputs, chosen)), title=f"{net.top}（{label}）")
        circuit.update_layout(height=320, margin={"t": 50, "b": 30})
        with out:
            out.clear_output(wait=True)
            display(HTML(f'<div style="{FONT}">{escape(_reading(post, chosen))}</div>'))
            display(HTML(circuit.to_html(include_plotlyjs="cdn", full_html=False)))
            display(HTML(_waveform(post, chosen, "ポストレイアウトシミュレーション（橙が選んだ入力の区間）")
                         .to_html(include_plotlyjs="cdn", full_html=False)))

    for button in buttons.values():
        button.observe(draw, names="value")
    display(widgets.VBox([*buttons.values(), out]))
    draw()


def _box(title, owner, detail):
    color = TRITFLOW if owner == "TritFlow" else EXISTING
    return (f'<div style="border:1.5px solid {color};border-radius:6px;padding:.45em .7em;'
            f'min-width:9.5em;flex:1;background:{color}14">'
            f'<div style="font-weight:700">{escape(title)}</div>'
            f'<div style="color:{color};font-size:11px">{escape(owner)}</div>'
            f'<div style="color:#30353b;font-size:12px;margin-top:.2em">{escape(detail)}</div></div>')


def flow_map(net, lay, drc, lvs, extracted, post):
    """One picture of the run: each stage, who made it, and what it produced this time."""
    report, stats = net.report(), lay.stats
    cells = " · ".join(f"{cell}×{n}" for cell, n in report["cells"].items())
    width, height = stats["die_size_um"]
    signal_c = {name: v["capacitance_f"] for name, v in extracted.capacitance["nets"].items()
                if name not in ("VDD", "VMID", "VSS")}
    worst = max(post["measurements"]["rows"], key=lambda r: max(abs(o["error_v"]) for o in r["outputs"].values()))
    error = max(abs(o["error_v"]) for o in worst["outputs"].values())
    stages = [
        ("三値HDLの読込み", "TritFlow", "TritVerilog → 三値の式"),
        ("合成", "TritFlow", f"{cells} · 全{report['equivalence']['vectors']}入力で等価"),
        ("スタンダードセル", "TritFlow", "テープアウトした回路から生成"),
        ("配置配線", "TritFlow", f"{width:.0f} × {height:.0f} µm · {stats['routed_nets']}本 · M1/M2"),
        ("DRC", "既存：PDKのKLayoutデッキ", f"違反 {drc['violations']}件"),
        ("LVS", "既存：KLayoutの素子抽出とPDKデッキ", "一致" if lvs["matched"] else "不一致"),
        ("配線容量の見積もり", "TritFlow", f"信号{len(signal_c)}本 · 最大 {max(signal_c.values())*1e15:.0f} fF"),
        ("過渡解析", "既存：ngspiceとPDKのモデル", f"{len(post['measurements']['rows'])}区間"),
        ("三値の判定", "TritFlow", f"±0.5 Vの帯 · 最大誤差 {error:.2f} V · "
                                   + ("全区間で合格" if post["measurements"]["passed"] else "不合格あり")),
    ]
    arrow = f'<div style="align-self:center;color:{DIM}">→</div>'
    boxes = arrow.join(_box(*stage) for stage in stages)
    legend = (f'<span style="color:{TRITFLOW};font-weight:700">■</span> TritFlowが作った部分　'
              f'<span style="color:{EXISTING};font-weight:700">■</span> 既存の道具')
    display(HTML(f'<div style="{FONT};font-size:12px">'
                 f'<div style="display:flex;flex-wrap:wrap;gap:.4em">{boxes}</div>'
                 f'<div style="margin-top:.5em;color:{DIM}">{legend}</div></div>'))
