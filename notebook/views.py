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


def _waveform_png(post, chosen):
    """The post-layout inputs and outputs with their ±0.5 V bands; the stretches where the inputs equal
    ``chosen`` are shaded. A plain image, so it shows wherever the notebook is opened."""
    import base64, io
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from tritflow import PASS_BAND
    from tritflow.sim.spice import signal_waveform

    data, rows = post["waveforms"], post["measurements"]["rows"]
    pins = [*post["stimulus"]["inputs"], *post["stimulus"]["outputs"]]
    hold = post["stimulus"]["hold_s"]*1e6
    levels = post["measurements"]["ideal_volts"]
    figure, axes = plt.subplots(len(pins), 1, figsize=(7.2, 1.5*len(pins)+.5), sharex=True, squeeze=False)
    for axis, pin in zip(axes[:, 0], pins):
        for volts in levels.values():
            axis.axhspan(volts-PASS_BAND, volts+PASS_BAND, color="#6eae89", alpha=.15, lw=0)
        for index, row in enumerate(rows):
            if tuple(row["input_trits"]) == chosen:
                axis.axvspan(index*hold, (index+1)*hold, color="#e8782a", alpha=.18, lw=0)
        output = pin in post["stimulus"]["outputs"]
        axis.plot(data["time"]*1e6, signal_waveform(data, pin), color="#1f5fa8" if output else "#5b6470", lw=1.4)
        axis.set_yticks(sorted(levels.values()))
        axis.set_ylabel(f"{pin} (V)")
        axis.set_xlim(0, len(rows)*hold)
        axis.spines[["top", "right"]].set_visible(False)
    axes[-1, 0].set_xlabel("time (µs)")
    figure.tight_layout()
    buffer = io.BytesIO()
    figure.savefig(buffer, format="png", dpi=110)
    plt.close(figure)
    return base64.b64encode(buffer.getvalue()).decode()


def _reading(post, chosen):
    rows = [r for r in post["measurements"]["rows"] if tuple(r["input_trits"]) == chosen]
    if not rows:
        return "この入力の組合せはSPICEで流していない。回路図の値は論理値。"
    return "、".join(f"{pin} = {value['voltage_v']:+.2f} V（理想 {value['ideal_voltage_v']:+.0f} V）"
                    for pin, value in rows[0]["outputs"].items())


_PICKS = 0


def pick_input(net, post):
    """Input buttons; the schematic's net values and the shaded stretch of the post-layout
    waveform follow the choice. Pure HTML and CSS (no widgets or scripts), so it works in Colab,
    Jupyter and a saved copy alike."""
    global _PICKS
    _PICKS += 1
    key = f"tfpick{_PICKS}"
    inputs = [p.name for p in net.ports if p.dir == "input"]
    choices = list(dict.fromkeys(tuple(row["input_trits"]) for row in post["measurements"]["rows"]))
    choices.sort()
    start = choices.index((0,)*len(inputs)) if (0,)*len(inputs) in choices else 0
    radios, panels, rules = [], [], []
    for index, chosen in enumerate(choices):
        label = ", ".join(f"{name} = {TRIT_TEXT[v]}" for name, v in zip(inputs, chosen))
        radios.append(f'<input type="radio" name="{key}" id="{key}-{index}"{" checked" if index == start else ""}>'
                      f'<label for="{key}-{index}">{escape(label)}</label>')
        circuit = net.schematic(inputs=dict(zip(inputs, chosen)), net_names=True, expand="*", title=label)
        panels.append(f'<div class="p{index}"><div class="reading">{escape(_reading(post, chosen))}</div>'
                      f'{circuit._repr_svg_()}<img src="data:image/png;base64,{_waveform_png(post, chosen)}"></div>')
        rules.append(f"#{key}-{index}:checked ~ .p{index}{{display:block}}")
    style = (f".{key} input{{display:none}}"
             f".{key} label{{display:inline-block;padding:.25em .9em;margin:0 .3em .5em 0;border:1px solid #c9ccd1;"
             f"border-radius:4px;cursor:pointer}}"
             f".{key} input:checked + label{{background:#1f5fa8;color:#fff;border-color:#1f5fa8}}"
             f".{key} > div{{display:none}} .{key} .reading{{margin:.3em 0}}"
             f".{key} svg, .{key} img{{max-width:100%;height:auto;display:block}}" + "".join(rules))
    display(HTML(f'<style>{style}</style><div class="{key}" style="{FONT}">{"".join(radios)}{"".join(panels)}</div>'))


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
