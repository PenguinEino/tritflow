"""Build the v3 Japanese notebook from the narrative files and the code cells below.

Each narrative file is Markdown; a line ``<!-- code: NAME -->`` places code cell NAME there, and
``<!-- figure: NAME -->`` places figures/out/NAME.png from the pinned commit.

    python3 notebook/v3/make_notebook.py [--ref COMMIT]   # default: HEAD
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
# The setup cell and the table pictures are shared with v2.
sys.path.insert(0, str(HERE.parent/"v2"))
from setup_cell import SETUP
from make_tables import TABLES, width

RAW = "https://raw.githubusercontent.com/PenguinEino/tritflow"
# jsDelivr serves SVG as an image; raw.githubusercontent.com does not.
CDN = "https://cdn.jsdelivr.net/gh/PenguinEino/tritflow"

PREAMBLE = '''
from live import need, provides, install_error_view, LayoutView
from views import pick_input, stimulus, bus_picker, cell_counts, schematic_view, scope_figure, timing_table, wire_table, delay_table, transient_conditions, dc_conditions, note
from IPython.display import HTML, display
from inverter_views import inverter
from pnr_views import replay
from cell_views import closure_view, cell_tables, cell_row
from tritflow import CELLS_DIR
from tritflow.sim.sizing import sweep_dimensions, load_grid
from tritflow import flow
from tritflow.viz.layout import gds_viewer
from tritflow.schematic import set_language
set_language("ja")
install_error_view()
for name, cell in {"source": "1-1 HDL", "net": "1-2 合成する", "lay": "1-3 配置配線する",
                   "lvs": "1-4 DRCとLVS", "post": "1-5 ポストレイアウトシミュレーション",
                   "dot4": "3-8 論理合成する", "dot4_layout": "4-1 配置配線する",
                   "dot4_lvs": "5-1 DRCとLVS", "dot4_extracted": "5-2 抽出と配線容量", "dot4_post": "5-3 ポストレイアウトシミュレーション"}.items():
    provides(name, cell)
'''

CODE = {
"source": '''# 1-1 HDL
source = """
module first(input trit a, output trit y);
  assign y = a & ~a;
endmodule
"""''',

"hdl": '''# 1-2 合成する
need("source", why="合成するHDLは、1-1に書いてあります。")
with step("HDLを読み込んで合成") as s:
    net = flow.loads(source).synthesize()
    s.done(" · ".join(f"{cell}×{n}" for cell, n in net.report()["cells"].items())
           + (" · 全入力で等価" if net.equivalence["passed"] else " · 等価でない"))
bus_picker(net)''',

"pnr": '''# 1-3 配置配線する
need("net", why="配置配線する回路 net は、1-2で合成します。")
with step("配置配線", view=LayoutView()) as s:
    lay = net.place_and_route(output_dir=BUILD/net.top, seed=0)
    width, height = lay.stats["die_size_um"]
    s.done(f"{lay.stats['instance_count']}セル · {width:.0f} × {height:.0f} µm · 配線 {lay.stats['routed_nets']}本",
           picture=replay(lay))''',

"check": '''# 1-4 DRCとLVS
need("lay", why="DRCとLVSは、1-3で作ったGDSを調べます。")
with step("DRC") as s:
    drc = lay.drc()
    s.done(f"違反 {drc['violations']}件")
with step("LVS") as s:
    lvs = lay.lvs()
    s.done("一致" if lvs["matched"] else "不一致")
gds_viewer(lay.gds_path)''',

"spice": '''# 1-5 ポストレイアウトシミュレーション
need("lvs", why="シミュレーションは、1-4でLVSが一致したGDSから回路を取り出して動かします。")
with step("抽出と配線容量") as s:
    extracted = lay.extract()
    signals = [n for n in extracted.capacitance["nets"] if n not in ("VDD", "VMID", "VSS")]
    s.done(f"信号{len(signals)}本に配線容量を追加")
with step("ngspice") as s:
    post = extracted.simulate(stimulus(net), load=100e-15, hold_s=1e-6, step_s=2e-9,
                              edge_s=1e-9, temperature_c=27)
    s.done("全区間で ±0.5 V の帯に入った" if post["measurements"]["passed"] else "帯に入らない区間がある")
pick_input(net, post)
transient_conditions(post, load_f=100e-15)''',

"inv": '''# 2-1 INVのDC解析と寸法
with step("ngspice（INVのDC解析）") as s:
    spice = sweep_dimensions("INV", [], workdir=BUILD/"inv")
    zero = next(r for r in spice["rows"][0]["dc"] if r["input_trits"] == [0])
    s.done(f"入力 0 V：Y = {zero['output_v']['Y']:+.3f} V · {abs(zero['rail_current_a']['VDD'])*1e3:.3f} mA")
with step("寸法の記録を照合") as s:
    grid = load_grid("INV")
    s.done(f"{len(grid['rows'])}通り · 回路・モデル・解析コードが一致")
inverter(spice, grid)
dc_conditions()''',

"closure": '''# 2-2 NANYと +1 の定数から作れる1入力関数
from completeness import generations, surjective_and_depends_on_both, nany
found = generations(binary=(nany,), constants=(1,))
print(f"作れた1入力関数：{len(found)} / 27、最も深いもので {max(found.values())} 段")
print("NANYは2つの入力の両方に依存し、出力に−1・0・+1のすべてが現れる：", surjective_and_depends_on_both(nany))
closure_view(found)''',

"cells": '''# 2-3 セルの真理値表
cell_tables(CELLS_DIR/"out", ROOT/"notebook/assets/schematics")''',

"stdcells": '''# 2-4 スタンダードセル
import json
cell_row(json.loads((CELLS_DIR/"out/library.json").read_text()), CELLS_DIR/"out")''',

"fa_source": '''# 3-1 HDL：+ で書いた全加算器
full_add_source = """
module full_add_rtl(input trit a, b, cin, output trit sum, cout);
  assign {cout, sum} = a + b + cin;
endmodule
"""''',

"fa_synth": '''# 3-2 論理合成する
need("full_add_source", why="合成するHDLは、3-1に書いてあります。")
with step("論理合成") as s:
    full_add_rtl = flow.loads(full_add_source).synthesize()
    s.done(" · ".join(f"{cell}×{n}" for cell, n in full_add_rtl.report()["cells"].items())
           + f" · 全{full_add_rtl.equivalence['vectors']}入力で等価")
bus_picker(full_add_rtl)''',

"mul_source": '''# 3-3 HDL：* で書いた1トリットの積
mul_source = """
module mul(input trit w, x, output trit p);
  assign p = w * x;
endmodule
"""''',

"mul_synth": '''# 3-4 論理合成する
need("mul_source", why="合成するHDLは、3-3に書いてあります。")
with step("論理合成") as s:
    mul = flow.loads(mul_source).synthesize()
    s.done(" · ".join(f"{cell}×{n}" for cell, n in mul.report()["cells"].items())
           + f" · 全{mul.equivalence['vectors']}入力で等価")
bus_picker(mul)''',

"sel_source": '''# 3-5 HDL：同じ選択を2通りに書く
select_sources = {
"(op == 1't1) ? a : b": """
module sel_cmp(input trit a, b, op, output trit r);
  assign r = (op == 1't1) ? a : b;
endmodule
""",
"op ? a : b": """
module sel_raw(input trit a, b, op, output trit r);
  assign r = op ? a : b;
endmodule
""",
}''',

"sel_synth": '''# 3-6 論理合成して比べる
need("select_sources", why="合成するHDLは、3-5に書いてあります。")
with step("論理合成（2通り）") as s:
    selects = {name: flow.loads(source).synthesize() for name, source in select_sources.items()}
    s.done(" · ".join(f"{name} {net.report()['total_cells']}セル" for name, net in selects.items()))
cell_counts(selects)
for net in selects.values():
    bus_picker(net)''',

"dot4_source": '''# 3-7 HDL：三値重みの4項の積和
dot4_source = """
module dot4(input trit w0, w1, w2, w3, x0, x1, x2, x3, output trit [1:0] y);
  assign y = w0*x0 + w1*x1 + w2*x2 + w3*x3;
endmodule
"""''',

"dot4_synth": '''# 3-8 論理合成する
need("dot4_source", why="合成するHDLは、3-7に書いてあります。")
with step("論理合成") as s:
    dot4 = flow.loads(dot4_source).synthesize()
    s.done(" · ".join(f"{cell}×{n}" for cell, n in dot4.report()["cells"].items())
           + f" · 全{dot4.equivalence['vectors']}入力で等価")''',

"pnr2": '''# 4-1 配置配線する
need("dot4", why="配置配線する回路は、3-8で合成した積和です。")
with step("配置配線", view=LayoutView()) as s:
    dot4_layout = dot4.place_and_route(output_dir=BUILD/"dot4", seed=0)
    stats = dot4_layout.stats
    s.done(f"{stats['instance_count']}セル · {stats['row_count']}行 · {stats['die_size_um'][0]:.0f} × {stats['die_size_um'][1]:.0f} µm · "
           f"配線長の見積もり {stats['hpwl_before_um']/1e3:.1f} → {stats['hpwl_after_um']/1e3:.1f} mm · ビア {stats['via_count']}個",
           picture=replay(dot4_layout))''',

"gds2": '''# 4-2 GDS
need("dot4_layout", why="表示するGDSは、4-1で作ります。")
gds_viewer(dot4_layout.gds_path)''',

"verify5": '''# 5-1 DRCとLVS
need("dot4_layout", why="検証するGDSは、4-1で作ります。")
with step("DRC（PDKのデッキ）") as s:
    dot4_drc = dot4_layout.drc()
    s.done(f"違反 {dot4_drc['violations']}件")
with step("LVS（PDKのデッキ）") as s:
    dot4_lvs = dot4_layout.lvs()
    s.done("一致" if dot4_lvs["matched"] else "不一致")''',

"extract5": '''# 5-2 抽出と配線容量
need("dot4_lvs", why="抽出は、5-1でLVSが一致したGDSから行います。")
with step("抽出と配線容量") as s:
    dot4_extracted = dot4_layout.extract()
    dot4_wires = dot4_layout.result.net_parasitics()
    s.done(f"素子のネットリスト · 信号{len(dot4_wires['nets'])}本に配線容量を追加")
wire_table(dot4_wires)''',

"spice5": '''# 5-3 ポストレイアウトシミュレーション
need("dot4_extracted", why="シミュレーションする回路は、5-2で抽出します。")
from tritflow.sim.postlayout import logical_nodeset
dot4_inputs = [p.name for p in dot4.ports if p.dir == "input"]
weights = (+1, -1, +1, +1)
activations = [(0, 0, 0, 0), (1, 0, 0, 0), (1, -1, 0, 0), (1, -1, 1, 1), (-1, 1, -1, -1), (0, 0, 0, 0),
               (0, 1, 0, 0), (-1, 1, 0, 0), (1, -1, 1, 0), (-1, 1, -1, 0), (0, 0, 0, 0)]
def operands(x):
    """The circuit's input trits for the fixed weights and the activations x, in port order."""
    values = {f"w{i}": w for i, w in enumerate(weights)} | {f"x{i}": v for i, v in enumerate(x)}
    return tuple(values[p] for p in dot4_inputs)
dot4_vectors = [operands(x) for x in activations]
with step("ngspice") as s:
    dot4_post = dot4_extracted.simulate(dot4_vectors, load=100e-15, hold_s=1e-6, step_s=5e-9, edge_s=1e-9,
                                        temperature_c=27, timeout=600, workdir=BUILD/"dot4"/"postlayout",
                                        nodeset=logical_nodeset(dot4, dot4_lvs["report"], dot4_inputs, dot4_vectors[0]))
    s.done("全区間で ±0.5 V の帯に入った" if dot4_post["measurements"]["passed"] else "帯に入らない区間がある")
display(HTML(scope_figure(dot4_post, settle=True).to_html(include_plotlyjs="cdn", full_html=False,
                                                         config={"displaylogo": False, "scrollZoom": True})))
transient_conditions(dot4_post, load_f=100e-15)''',

"table5": '''# 5-4 INVの遅延の表
delay_table("INV")''',
"sta5": '''# 5-5 三値のSTAとSPICEの比較
need("dot4_post", why="比べるSPICEの結果は、5-3で求めます。")
from tritflow.sta import analyze
states = [dict(zip(dot4_inputs, v)) for v in dot4_vectors]
with step("三値のSTA") as s:
    dot4_timing = analyze(dot4, vector_pairs=list(zip(states, states[1:])),
                          wire_caps={n: e["wire_capacitance_f"] for n, e in dot4_wires["nets"].items()},
                          output_load_f=100e-15, input_transition_s=1e-9)
    s.done(f"{len(dot4_timing.arrival)}出力")
timing_table(dot4_post, dot4_timing)
note("STAの条件：5-3と同じ入力の列、出力の負荷 100 fF、入力の変化時間 1 ns、配線容量は5-2の抽出値。")''',
}

CHAPTERS = ["00_opening.md", "01_first.md", "02_cells.md", "03_hdl.md", "04_pnr.md", "05_verify.md"]


def cells(ref):
    out = []
    setup = "#@title 準備（最初に実行） { display-mode: \"form\" }\n" + SETUP.replace('"PINNED"', f'"{ref}"') + PREAMBLE
    for index, name in enumerate(CHAPTERS):
        text = (HERE/"narrative"/name).read_text()
        text = re.sub(r"<!-- tables: ([\w ]+) -->", lambda m: "&emsp;&emsp;".join(
            f'<img src="{CDN}@{ref}/notebook/assets/tables/{name}.svg" width="{width(TABLES[name])}" alt="{name}">'
            for name in m[1].split()), text)
        text = re.sub(r"<!-- asset: (\S+) \| (.+?) -->", lambda m: f"<details><summary>{m[2]}</summary>\n\n"
                      f"![{m[2]}]({RAW}/{ref}/{m[1]})\n\n</details>", text)
        text = re.sub(r"<!-- figure: (\w+) -->", lambda m: f"![{m[1]}]({RAW}/{ref}/figures/out/{m[1]}_ja.png)", text)
        for chunk in re.split(r"\n*<!-- code: (\w+) -->\n*", text):
            if chunk in CODE:
                out.append(("code", CODE[chunk]))
            elif chunk.strip():
                out.append(("markdown", chunk.strip()))
        if index == 0:
            out.append(("code", setup))
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ref", default="HEAD")
    parser.add_argument("--out", default=str(HERE/"tritflow_ja.ipynb"))
    args = parser.parse_args()
    ref = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", args.ref], text=True).strip()
    nb = {"nbformat": 4, "nbformat_minor": 5,
          "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
                       "language_info": {"name": "python"}, "colab": {"name": "tritflow_ja.ipynb"}},
          "cells": [{"cell_type": kind, "id": f"c{i}", "metadata": {}, "source": source,
                     **({"execution_count": None, "outputs": []} if kind == "code" else {})}
                    for i, (kind, source) in enumerate(cells(ref))]}
    Path(args.out).write_text(json.dumps(nb, ensure_ascii=False, indent=1) + "\n")
    print(args.out, ref)


if __name__ == "__main__":
    main()
