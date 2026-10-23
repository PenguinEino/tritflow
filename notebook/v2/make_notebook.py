"""Build the v2 Japanese notebook from the narrative files and the code cells below.

Each narrative file is Markdown; a line ``<!-- code: NAME -->`` places code cell NAME there, and
``<!-- figure: NAME -->`` places figures/out/NAME.png from the pinned commit.

    python3 notebook/v2/make_notebook.py [--ref COMMIT]   # default: HEAD
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
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
                   "add2": "3-4 論理合成し、入力の値ごとに見る", "add2_layout": "4-1 配置配線する",
                   "add2_lvs": "5-1 DRCとLVS", "add2_extracted": "5-2 抽出と配線容量", "add2_post": "5-3 ポストレイアウトシミュレーション"}.items():
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
    s.done(f"{lay.stats['instance_count']}セル · {width:.0f} × {height:.0f} µm · 配線 {lay.stats['routed_nets']}本")''',

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

"add2_source": '''# 3-3 HDL：2トリットの加算
add2_source = """
module add2(input trit [1:0] a, b, output trit [2:0] s);
  assign s = a + b;
endmodule
"""''',

"add2_synth": '''# 3-4 論理合成し、入力の値ごとに見る
need("add2_source", why="合成するHDLは、3-3に書いてあります。")
with step("論理合成") as s:
    add2 = flow.loads(add2_source).synthesize()
    s.done(" · ".join(f"{cell}×{n}" for cell, n in add2.report()["cells"].items())
           + f" · 全{add2.equivalence['vectors']}入力で等価")
bus_picker(add2)''',

"sel_source": '''# 3-5 HDL：同じ選択を書き分ける
select_sources = {
"?:": """
module sel_cond(input trit [1:0] a, b, input trit op, output trit [2:0] r);
  assign r = (op == 1't0) ? a : (op == 1't1 ? a + b : a - b);
endmodule
""",
"case": """
module sel_case(input trit [1:0] a, b, input trit op, output reg trit [2:0] r);
  always @* begin
    case (op)
      1'tT: r = a - b;
      1't0: r = a;
      1't1: r = a + b;
    endcase
  end
endmodule
""",
"a + op*b": """
module sel_mul(input trit [1:0] a, b, input trit op, output trit [2:0] r);
  assign r = a + op*b;
endmodule
""",
# Not the same function: at op = 0 it keeps only the digits where a+b and a-b agree.
"op ? a+b : a-b": """
module sel_raw(input trit [1:0] a, b, input trit op, output trit [2:0] r);
  assign r = op ? a + b : a - b;
endmodule
""",
}''',

"sel_synth": '''# 3-6 論理合成して比べる
need("select_sources", why="合成するHDLは、3-5に書いてあります。")
with step("論理合成（4通り）") as s:
    selects = {name: flow.loads(source).synthesize() for name, source in select_sources.items()}
    s.done(" · ".join(f"{name} {net.report()['total_cells']}セル" for name, net in selects.items()))
cell_counts(selects)
bus_picker(selects["a + op*b"])''',

"pnr2": '''# 4-1 配置配線する
need("add2", why="配置配線する回路は、3-4で合成した2トリットの加算器です。")
with step("配置配線", view=LayoutView()) as s:
    add2_layout = add2.place_and_route(output_dir=BUILD/"add2", seed=0)
    stats = add2_layout.stats
    s.done(f"{stats['instance_count']}セル · {stats['row_count']}行 · {stats['die_size_um'][0]:.0f} × {stats['die_size_um'][1]:.0f} µm · "
           f"配線長の見積もり {stats['hpwl_before_um']/1e3:.1f} → {stats['hpwl_after_um']/1e3:.1f} mm · ビア {stats['via_count']}個")''',

"replay": '''# 4-2 途中経過を振り返る
need("add2_layout", why="振り返る実行は、4-1の配置配線です。")
replay(add2_layout)''',

"gds2": '''# 4-3 GDS
need("add2_layout", why="表示するGDSは、4-1で作ります。")
gds_viewer(add2_layout.gds_path)''',

"verify5": '''# 5-1 DRCとLVS
need("add2_layout", why="検証するGDSは、4-1で作ります。")
with step("DRC（PDKのデッキ）") as s:
    add2_drc = add2_layout.drc()
    s.done(f"違反 {add2_drc['violations']}件")
with step("LVS（PDKのデッキ）") as s:
    add2_lvs = add2_layout.lvs()
    s.done("一致" if add2_lvs["matched"] else "不一致")''',

"extract5": '''# 5-2 抽出と配線容量
need("add2_lvs", why="抽出は、5-1でLVSが一致したGDSから行います。")
with step("抽出と配線容量") as s:
    add2_extracted = add2_layout.extract()
    add2_wires = add2_layout.result.net_parasitics()
    s.done(f"素子のネットリスト · 信号{len(add2_wires['nets'])}本に配線容量を追加")
wire_table(add2_wires)''',

"spice5": '''# 5-3 ポストレイアウトシミュレーション
need("add2_extracted", why="シミュレーションする回路は、5-2で抽出します。")
from tritflow.sim.postlayout import logical_nodeset
add2_inputs = [p.name for p in add2.ports if p.dir == "input"]
def digits(value, width=2):
    """Balanced-ternary digits of an integer, low digit first."""
    out = []
    for _ in range(width):
        digit = (value + 1) % 3 - 1
        out.append(digit)
        value = (value - digit)//3
    return out
def operands(a, b):
    """The adder's input trits for the integers a and b, in port order."""
    values = {f"a[{i}]": d for i, d in enumerate(digits(a))} | {f"b[{i}]": d for i, d in enumerate(digits(b))}
    return tuple(values[p] for p in add2_inputs)
add2_vectors = [operands(a, b) for a, b in [(0, 0), (1, 0), (-1, 0), (3, 0), (-3, 0), (4, 4), (0, 0),
                                            (-4, -4), (4, -4), (2, 2), (0, 0)]]
with step("ngspice") as s:
    add2_post = add2_extracted.simulate(add2_vectors, load=100e-15, hold_s=1e-6, step_s=2e-9, edge_s=1e-9,
                                        temperature_c=27, timeout=600,
                                        nodeset=logical_nodeset(add2, add2_lvs["report"], add2_inputs, add2_vectors[0]))
    s.done("全区間で ±0.5 V の帯に入った" if add2_post["measurements"]["passed"] else "帯に入らない区間がある")
display(HTML(scope_figure(add2_post, settle=True).to_html(include_plotlyjs="cdn", full_html=False,
                                                         config={"displaylogo": False, "scrollZoom": True})))
transient_conditions(add2_post, load_f=100e-15)''',

"table5": '''# 5-4 INVの遅延の表
delay_table("INV")''',
"sta5": '''# 5-5 三値のSTAとSPICEの比較
need("add2_post", why="比べるSPICEの結果は、5-3で求めます。")
from tritflow.sta import analyze
states = [dict(zip(add2_inputs, v)) for v in add2_vectors]
with step("三値のSTA") as s:
    add2_timing = analyze(add2, vector_pairs=list(zip(states, states[1:])),
                          wire_caps={n: e["wire_capacitance_f"] for n, e in add2_wires["nets"].items()},
                          output_load_f=100e-15, input_transition_s=1e-9)
    s.done(f"{len(add2_timing.arrival)}出力")
timing_table(add2_post, add2_timing)
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
