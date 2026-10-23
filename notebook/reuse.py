"""Chapter 6: editable TritVerilog to verified GDS and post-layout transients.

Put ``reuse_source`` in its own editable cell, then call
``result = run(reuse_source, output_dir=BUILD/"reuse")``. ``run()`` without a
source uses ``live.need`` to locate that cell. No preceding dot4 result is
required. Syntax/elaboration errors use the existing notebook error box.

SPICE covers every state for <=4 input trits, otherwise a repeatable sample;
neither policy claims all directed transitions. The oracle evaluates the HDL,
not the mapped gates. Wire C is the flow's geometric estimate, not signoff PEX.
"""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from itertools import product
import json
from pathlib import Path
import random

from IPython.display import HTML, display

from live import LayoutView, _box, _text, need, provides, step
from style import figure_css, table_css

LABELS_EN = {
    "項目": "Item", "結果": "Result", "回路": "Circuit", "セル数": "Cells",
    "マクロ寸法 (µm)": "Macro size (µm)", "DRC 違反": "DRC violations", "一致": "Matched", "不一致": "Mismatch",
    "SPICE 入力状態": "SPICE input states", "出力レベル・整定": "Output level and settling",
    "最大出力誤差 (V)": "Max. output error (V)", "定数重みの合成によるセル削減": "Cell reduction from constant weights",
    "検査（記録済み）": "Check (recorded)", "Drawing DRC 違反": "Drawing DRC violations", "Mask DRC 違反": "Mask DRC violations",
    "信号 / 電源": "Signal / supply", "方向": "Direction", "6章のHDLセル": "Chapter 6 HDL cell",
    "6章のHDLセル（修正後に再実行）": "Chapter 6 HDL cell (edit and rerun)",
    "編集したTritVerilogのソースを使います。": "This run uses the edited TritVerilog source.",
    "HDLを読み込んで合成": "Parse HDL and synthesize", "配置配線": "Place and route",
    "DRC（PDKのデッキ）": "DRC (PDK deck)", "LVS（PDKのデッキ）": "LVS (PDK deck)",
    "抽出と配線容量": "Extraction and wire capacitance", "ngspice（ポストレイアウト）": "ngspice (post-layout)",
    "全入力状態": "exhaustive states", "一部の入力状態": "sampled states",
    "全入力が0の状態から始め、反射型三値グレイコード順（桁の値は0、−1、+1）で全入力状態を調べる。全入力遷移を網羅する検証ではない。":
        "All states in reflected ternary Gray order (digits 0, -1, +1), starting at zero; not exhaustive transition coverage.",
    "全入力が0の状態、全入力が−1の状態と+1の状態、符号が交互の状態、1入力だけを変えた状態を状態数の上限まで選び、残りは重複のない疑似乱数で補う。全入力状態・全入力遷移を網羅する検証ではない。":
        "Zero, rail corners, alternating signs, single-input excursions until the budget, then unique pseudorandom states. Not exhaustive state/transition coverage.",
    "提出準備": "Submission ready", "未完了": "False", "完了": "True",
    "電源": "power", "入力": "input", "出力": "output",
    "提出には、シャトル運営者による2500 µm角の領域の割り当て、最終ボンディング図の合意、最終CIによる確認が必要である。":
        "Organizer allocation of a full 2500 um slot, final bond diagram and final CI remain",
    "カスタムTEGのパッドとボンディングの割り当て、およびESD・電源・パッケージの承認がまだ必要である。":
        "Custom TEG pad/bond allocation and ESD/power/package approval still required",
}


def _label(text):
    """Localize presentation labels without changing HDL, stimuli or recorded evidence."""
    text = str(text)
    japanese = next((ja for ja, en in LABELS_EN.items() if en == text), text)
    return _text(japanese, LABELS_EN.get(text, text))


DOT4_SOURCE = """module dot4(input trit w0, w1, w2, w3, x0, x1, x2, x3,
            output trit [1:0] y);
  assign y = w0*x0 + w1*x1 + w2*x2 + w3*x3;
endmodule
"""

DEFAULT_SOURCE = """// Fixed weights: w = (+1, -1, +1, +1).
module dot4_fixed(input trit x0, x1, x2, x3, output trit [1:0] y);
  assign y = x0 - x1 + x2 + x3;
endmodule
"""


def stimulus_plan(inputs, *, exhaustive_limit=81, sample_size=27, seed=0):
    """Bounded state coverage without allocating the exponential state space.

    Small circuits use reflected ternary Gray order with digits 0, -1, +1.
    Larger ones start with zero, both rail corners, alternating polarities and
    single-input excursions (until the budget), then seeded random unique rows.
    One state of a constant circuit is represented by the empty input tuple.
    """
    if exhaustive_limit < 1 or sample_size < 3:
        raise ValueError("exhaustive_limit >= 1 and sample_size >= 3 are required")
    names = list(inputs)
    count = 3 ** len(names)
    if count <= exhaustive_limit:
        rows = [()]
        for _ in names:
            rows = [(value, *row) for k, value in enumerate((0, -1, 1))
                    for row in (rows if k % 2 == 0 else reversed(rows))]
        vectors = rows
        mode = "exhaustive states"
        method = ("All states in reflected ternary Gray order (digits 0, -1, +1), "
                  "starting at zero; not exhaustive transition coverage.")
    else:
        vectors, seen = [], set()
        budget = min(sample_size, count)

        def add(row):
            row = tuple(row)
            if row not in seen and len(vectors) < budget:
                seen.add(row)
                vectors.append(row)

        for value in (0, -1, 1):
            add([value] * len(names))
        for sign in (-1, 1):
            add([sign * (-1 if i % 2 else 1) for i in range(len(names))])
        for i in range(len(names)):
            if len(vectors) == budget:
                break
            for value in (-1, 1):
                add([value if j == i else 0 for j in range(len(names))])
        rng = random.Random(seed)
        while len(vectors) < budget:
            add(rng.choices((-1, 0, 1), k=len(names)))
        mode = "sampled states"
        method = ("Zero, rail corners, alternating signs, single-input excursions until "
                  "the budget, then unique pseudorandom states. Not exhaustive state/transition coverage.")
    return {"inputs": names, "vectors": vectors, "mode": mode, "total_states": count,
            "unique_states": len(vectors), "seed": seed if count > exhaustive_limit else None,
            "method": method, "all_directed_transitions": False}


def _oracle(circuit, inputs):
    """Use the elaborated HDL as the electrical output reference."""
    def expected(vector):
        values = circuit.design.evaluate(dict(zip(inputs, vector, strict=True)))
        return {name: int(value) for name, value in values.items()}
    return expected


def _folding(circuit, net):
    """Recognize the fixed-weight function before attributing a cell reduction."""
    from tritflow import flow

    inputs = list(circuit.design.inputs)
    if set(inputs) != {"x0", "x1", "x2", "x3"} or set(circuit.design.outputs) != {"y[0]", "y[1]"}:
        return None
    expected = _oracle(circuit, inputs)
    for vector in product((-1, 0, 1), repeat=4):
        values = dict(zip(inputs, vector, strict=True))
        total = values["x0"] - values["x1"] + values["x2"] + values["x3"]
        out = expected(vector)
        if out["y[0]"] + 3 * out["y[1]"] != total:
            return None
    reference = flow.loads(DOT4_SOURCE).synthesize().report()["total_cells"]
    actual = net.report()["total_cells"]
    return {"weights": [1, -1, 1, 1], "programmable_cells": reference,
            "fixed_cells": actual, "cells_removed": reference - actual,
            "reduction_pct": 100 * (reference - actual) / reference}


def _table(rows, *, key="tfreuse"):
    head, *body = rows
    header = "<tr>" + "".join(f"<th>{escape(_label(str(c)))}</th>" for c in head) + "</tr>"
    content = "".join("<tr>" + "".join(f"<td>{escape(str(c))}</td>" for c in row) + "</tr>" for row in body)
    return HTML(f'<style>{figure_css("." + key)}{table_css("." + key)}'
                f'.{key}{{max-width:100%;overflow-x:auto}}</style>'
                f'<div class="{key}"><table>{header}{content}</table></div>')


def summary_view(summary):
    """Results from this run only, including the actual analog coverage."""
    plan = summary["stimulus"]
    w, h = summary["die_size_um"]
    rows = [["項目", "結果"], [_label("回路"), summary["top"]], [_label("セル数"), summary["cells"]],
            [_label("マクロ寸法 (µm)"), f"{w:g} × {h:g}"],
            [_label("DRC 違反"), summary["drc_violations"]],
            ["LVS", _label("一致") if summary["lvs_matched"] else _label("不一致")],
            [_label("SPICE 入力状態"), f"{plan['unique_states']} / {plan['total_states']} ({_label(plan['mode'])})"],
            [_label("出力レベル・整定"), "PASS" if summary["post_passed"] else "FAIL"],
            [_label("最大出力誤差 (V)"), f"{summary['max_error_v']:.4f}"]]
    for pin, value in summary["max_settling_s"].items():
        rows.append([_text(f"{pin} 最大整定時間 (ns)", f"{pin} max. settling time (ns)"), "—" if value is None else f"{value * 1e9:.1f}"])
    folding = summary["constant_folding"]
    if folding:
        rows.append([_label("定数重みの合成によるセル削減"),
                     f"{folding['programmable_cells']} → {folding['fixed_cells']} "
                     f"(−{folding['cells_removed']}, {folding['reduction_pct']:.1f}%)"])
    return _table(rows)


@dataclass(repr=False)
class ReuseResult:
    """Native objects remain available for further circuit/layout experiments."""

    circuit: object
    net: object
    layout: object
    drc: dict
    lvs: dict
    extracted: object
    post: dict
    summary: dict

    def __repr__(self):
        return f"ReuseResult(top={self.net.top!r}, passed={self.summary['passed']})"


def run(source=None, *, output_dir=None, top=None, params=None, cells=None, pdk=None,
        klayout_binary=None, seed=0, rows=None, anneal_steps=600, load_f=100e-15,
        hold_s=1e-6, step_s=2e-9, edge_s=1e-9, temperature_c=27, timeout=600,
        exhaustive_limit=81, sample_size=27, source_name="reuse_source", show=True):
    """Synthesize → P&R/replay → DRC → LVS → wire C → post-layout ngspice.

    Each call executes the tools afresh. Bad HDL shows ``live._box`` and returns
    None; physical-tool failures raise, and analog failures remain FAIL in the
    returned summary. A failed check never produces a green passed result.
    Every electrical run writes its deck, raw waveform, and measurements under
    ``output_dir``. The default output is ``ROOT/build/reuse/<top>``.
    """
    from tritflow import ROOT, flow
    from tritflow.hdl import HDLError
    from tritflow.sim.postlayout import logical_nodeset
    from tritflow.sim.tools import simulator_identity

    if output_dir is not None:
        (Path(output_dir).expanduser() / "summary.json").unlink(missing_ok=True)
    if source is None:
        from IPython import get_ipython
        provides(source_name, _label("6章のHDLセル"))
        need(source_name, why=_label("編集したTritVerilogのソースを使います。"))
        source = get_ipython().user_ns[source_name]
    settings = {k: v for k, v in {"cells": cells, "pdk": pdk,
                                "klayout_binary": klayout_binary}.items() if v is not None}
    try:
        with step(_label("HDLを読み込んで合成")) as s:
            circuit = flow.loads(source, top=top, params=params, filename="reuse_source.tv", **settings)
            net = circuit.synthesize()
            if not net.equivalence["passed"]:
                raise RuntimeError("HDL and mapped cells are not equivalent")
            folding = _folding(circuit, net)
            s.done(_text(f"{net.report()['total_cells']}セル · 等価性 {net.equivalence['vectors']}入力で一致",
                         f"{net.report()['total_cells']} cells · equivalent over {net.equivalence['vectors']} input vectors"))
    except HDLError as error:
        display(_box(_label("6章のHDLセル（修正後に再実行）"), str(error)))
        return None

    out = Path(output_dir or ROOT / "build/reuse" / net.top).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    # Remove a prior success before attempting a different layout or SPICE run.
    (out / "summary.json").unlink(missing_ok=True)
    (out / "source.tv").write_text(source)
    inputs = [p.name for p in net.ports if p.dir == "input"]
    plan = stimulus_plan(inputs, exhaustive_limit=exhaustive_limit, sample_size=sample_size, seed=seed)
    with step(_label("配置配線"), view=LayoutView(circuit.settings.cells)) as s:
        layout = net.place_and_route(output_dir=out, seed=seed, rows=rows, anneal_steps=anneal_steps)
        from pnr_views import replay
        s.done(_text(f"{layout.stats['row_count']}行 · 配線 {layout.stats['routed_nets']}本",
                     f"{layout.stats['row_count']} rows · {layout.stats['routed_nets']} routed nets"), picture=replay(layout))
    with step(_label("DRC（PDKのデッキ）")) as s:
        drc = layout.drc()
        if not drc["clean"]:
            raise RuntimeError(f"DRC violations: {drc['violations']}")
        s.done(_text(f"違反 {drc['violations']}件", f"Violations: {drc['violations']}"))
    with step(_label("LVS（PDKのデッキ）")) as s:
        lvs = layout.lvs()
        if not lvs["matched"]:
            raise RuntimeError(f"LVS mismatch: {lvs.get('errors', [])}")
        s.done(_label("一致"))
    with step(_label("抽出と配線容量")) as s:
        extracted = layout.extract()
        (out / "postlayout.spice").write_text(extracted.spice)
        s.done(_text(f"{len(extracted.capacitance['nets'])}ネットの集中配線容量",
                     f"Lumped wire capacitance on {len(extracted.capacitance['nets'])} nets"))
    expected = _oracle(circuit, inputs)
    guesses = logical_nodeset(net, lvs["report"], inputs, plan["vectors"][0])
    with step(_label("ngspice（ポストレイアウト）")) as s:
        s.detail = _text(f"{plan['unique_states']}入力状態 · {_label(plan['mode'])}", f"{plan['unique_states']} input states · {plan['mode']}")
        post = extracted.simulate(plan["vectors"], expected=expected, load=load_f, hold_s=hold_s,
                                  step_s=step_s, edge_s=edge_s, temperature_c=temperature_c,
                                  timeout=timeout, workdir=out / "spice", nodeset=guesses)
        measured = post["measurements"]
        s.done(("PASS" if measured["passed"] else "FAIL") + _text(f" · 最大誤差 {measured['max_error_v']:.3f} V",
                                                               f" · Max. error {measured['max_error_v']:.3f} V"))
    summary = {"schema": "tritflow.reuse.v1", "top": net.top,
               "passed": bool(drc["clean"] and lvs["matched"] and measured["passed"]),
               "cells": net.report()["total_cells"], "cell_counts": net.report()["cells"],
               "constant_folding": folding, "equivalence": net.equivalence,
               "die_size_um": layout.stats["die_size_um"], "drc_violations": drc["violations"],
               "lvs_matched": lvs["matched"], "post_passed": measured["passed"],
               "max_error_v": measured["max_error_v"], "max_settling_s": measured["max_settling_s"],
               "stimulus": plan, "conditions": {"load_f": load_f, "hold_s": hold_s, "step_s": step_s,
                   "edge_s": edge_s, "temperature_c": temperature_c, "band_v": 0.5},
               "initial_nodeset_v": guesses, "simulator": simulator_identity()}
    (out / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
    (out / "measurements.json").write_text(json.dumps(measured, indent=2, allow_nan=False) + "\n")
    if show:
        from tritflow.viz.layout import gds_viewer
        from views import note, scope_figure, transient_conditions
        display(summary_view(summary))
        note(_label(plan["method"]))
        display(gds_viewer(layout.gds_path, top=net.top))
        display(scope_figure(post, title=net.top, settle=True))
        transient_conditions(post, load_f=load_f)
    return ReuseResult(circuit, net, layout, drc, lvs, extracted, post, summary)


def shuttle_view(directory=None):
    """Open the recorded dot4 GDS and its actual pad/pin map; never rerun P&R."""
    from hashlib import sha256
    from tritflow.viz.layout import gds_viewer

    folder = Path(directory or Path(__file__).parent / "assets/chip/dot4")
    report = json.loads((folder / "signoff.json").read_text())
    gds = folder / "tr_1um_dot4.gds"
    if sha256(gds.read_bytes()).hexdigest() != report["gds_sha256"]:
        raise ValueError("Recorded dot4 GDS hash does not match its signoff record")
    display(gds_viewer(gds, top=report["top"]))
    display(_table([["検査（記録済み）", "結果"],
                    [_label("Drawing DRC 違反"), report["drawing_drc"]["violations"]],
                    ["Drawing LVS", _label("一致") if report["drawing_lvs"]["matched"] else _label("不一致")],
                    [_label("Mask DRC 違反"), report["mask_drc"]["violations"]],
                    ["MPW precheck", "PASS" if report["mpw_precheck"]["clean"] else "FAIL"],
                    [_label("Submission ready"), _label(report["submission_ready"])]], key="tfshuttlechecks"))
    directions = report["port_directions"]
    rows = [["Pad", "信号 / 電源", "方向", "X (µm)", "Y (µm)"]]
    rows += [[p["pad"], p["net"], _label(directions.get(p["net"], "power")), *p["center_um"]]
             for p in report["pad_map"]]
    display(_table(rows, key="tfshuttlepads"))
    from views import note
    note(_label(report["reason"]))
    return report


__all__ = ["DEFAULT_SOURCE", "DOT4_SOURCE", "ReuseResult", "run", "shuttle_view",
           "stimulus_plan", "summary_view"]
