"""Build v3 in Japanese (default) or English from one set of code cells.

Each narrative file is Markdown; a line ``<!-- code: NAME -->`` places code cell NAME there, and
``<!-- figure: NAME -->`` places figures/out/NAME.png from the pinned commit.

    python3 notebook/v3/make_notebook.py [--lang ja|en] [--ref COMMIT]
"""
import argparse
from io import StringIO
import json
import re
import subprocess
import sys
import tokenize
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
# The setup cell and table pictures live beside this builder.
sys.path.insert(0, str(HERE))
from setup_cell import SETUP
from make_tables import TABLES, TABLES_EN, width

sys.path.insert(0, str(HERE.parent))
from localization import localize_source, translate_text

RAW = "https://raw.githubusercontent.com/PenguinEino/tritflow"
# jsDelivr serves SVG as an image; raw.githubusercontent.com does not.
CDN = "https://cdn.jsdelivr.net/gh/PenguinEino/tritflow"

PREAMBLE = '''
from live import need, provides, install_error_view, LayoutView
from views import pick_input, stimulus, bus_picker, cell_counts, schematic_view, scope_figure, timing_table, wire_table, delay_table, transient_conditions, dc_conditions, note
from IPython.display import HTML, display
import plotly.io as pio
pio.renderers.default = "colab"
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
                   "dot4_lvs": "5-1 DRCとLVS", "dot4_extracted": "5-2 抽出と配線容量", "dot4_post": "5-3 ポストレイアウトシミュレーション",
                   "dot_scaling": "6-1 内積の規模と面積",
                   "reuse_source": "6-4 HDLを変更する"}.items():
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
with step("INVのDC解析") as s:
    spice = sweep_dimensions("INV", [], workdir=BUILD/"inv")
    zero = next(r for r in spice["rows"][0]["dc"] if r["input_trits"] == [0])
    s.done(f"入力 0 V：Y = {zero['output_v']['Y']:+.3f} V · {abs(zero['rail_current_a']['VDD'])*1e3:.3f} mA")
with step("寸法の記録を照合") as s:
    grid = load_grid("INV")
    s.done(f"{len(grid['rows'])}通り · 回路・モデル・解析コードが一致")
from predictions import divider, rail_power
from tritflow import PDK_ROOT
from style import figure_css, table_css
inv_hand = divider(grid["rows"][grid["adopted_index"]]["dimensions"], PDK_ROOT)
upper, lower = inv_hand["upper"], inv_hand["lower"]
resistances = [upper["rr_ohm"], upper["ron_ohm"], lower["ron_ohm"],
               upper["total_ohm"], lower["total_ohm"]]
comparison = [("V<sub>Y</sub> (V)", inv_hand["output_v"], zero["output_v"]["Y"], "+.3f"),
              ("I (mA)", inv_hand["current_a"]*1e3, abs(zero["rail_current_a"]["VDD"])*1e3, ".3f"),
              ("P (mW)", inv_hand["power_w"]*1e3,
               rail_power(zero, grid["conditions"]["supplies_v"])*1e3, ".3f")]
display(HTML('<style>'+figure_css('.inv-estimate')+table_css('.inv-estimate')+'</style>'
    + '<div class="inv-estimate"><table><tr>'
    + ''.join(f'<th>{label}<small>kΩ</small></th>' for label in
              ('R<sub>RR</sub>', 'r<sub>on,P</sub>', 'r<sub>on,N</sub>', 'R<sub>u</sub>', 'R<sub>d</sub>'))
    + '<th>R<sub>RR</sub>/r<sub>on,P</sub></th><th>R<sub>RR</sub>/r<sub>on,N</sub></th></tr><tr>'
    + ''.join(f'<td>{r/1e3:.3f}</td>' for r in resistances)
    + f'<td>{upper["rr_ohm"]/upper["ron_ohm"]:.1f}</td><td>{lower["rr_ohm"]/lower["ron_ohm"]:.1f}</td></tr></table>'
    + '<table style="margin-top:1em"><tr><th>入力0 V</th><th>抵抗による近似</th><th>SPICE</th></tr>'
    + ''.join(f'<tr><td>{label}</td><td>{estimate:{fmt}}</td><td>{measured:{fmt}}</td></tr>'
              for label, estimate, measured, fmt in comparison)
    + '</table></div>'))
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
with step("論理合成") as s:
    selects = {name: flow.loads(source).synthesize() for name, source in select_sources.items()}
    s.done(" · ".join(f"{name} {net.report()['total_cells']}セル" for name, net in selects.items()))
cell_counts(selects)
for net in selects.values():
    bus_picker(net)''',

"dot4_source": '''# 3-7 HDL：三値重みの4項の内積
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
need("dot4", why="配置配線する回路は、3-8で合成した内積です。")
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
with step("DRC") as s:
    dot4_drc = dot4_layout.drc()
    s.done(f"違反 {dot4_drc['violations']}件")
with step("LVS") as s:
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

"scale6": '''# 6-1 内積の規模と面積
from scale_views import load_scaling, scaling_table, synthesis_table
# 全掃引は長時間かかる（N=16の解析とN=32の配置配線試行を含む）。
RECOMPUTE_SCALING = False #@param {type:"boolean"}
dot_scaling = load_scaling(recompute=RECOMPUTE_SCALING)
display(synthesis_table(dot_scaling), scaling_table(dot_scaling))
for attempt in dot_scaling.get("optional_attempts", []):
    stage = "配置配線が未完了" if not attempt.get("pnr") else "検証が未完了"
    note(f"追加試行 N={attempt['n']} は{stage}のため、以下の比較には含めない。")
for row in dot_scaling["rows"]:
    options = row["conditions"].get("pnr_options", {})
    if options:
        note(f"N={row['n']}で既定値から変更した配置配線条件："
             f"行間チャネルの配線トラック {options['channel_tracks']}本、"
             f"M1の幅1 µm当たりの許容電流 {options['current_density_a_per_um']*1e3:g} mA。")
conditions = dot_scaling["conditions"]
holds = "、".join(f"N={row['n']}: {row['conditions']['hold_s']*1e6:g} µs"
                  for row in dot_scaling["rows"])
note(f"記録の条件：ngspice-{dot_scaling['provenance']['simulator']['version']}、"
     f"PDK {dot_scaling['provenance']['pdk']['qualified_commit'][:7]}、"
     f"{conditions['temperature_c']:g} °C、電源 +5 / 0 / −5 V。"
     f"出力負荷 {conditions['load_f']*1e15:g} fF、入力の変化時間 {conditions['edge_s']*1e9:g} ns、"
     f"最大時間刻み {conditions['step_s']*1e9:g} ns。各状態の保持時間は {holds}。")''',

"power6": '''# 6-2 静的電流と電力
need("dot_scaling", why="表示する記録は、6-1で読み込みます。")
from scale_views import power_table, power_figure
power_plot = power_figure(dot_scaling)
power_plot.update_yaxes(title_text="供給電力 (mW)")
display(power_table(dot_scaling), power_plot)''',

"timing6": '''# 6-3 STAとSPICE
need("dot_scaling", why="比較する記録は、6-1で読み込みます。")
from scale_views import scaling_figure, layout_penalty_table
display(scaling_figure(dot_scaling), layout_penalty_table(dot_scaling))''',

"reuse_source": '''# 6-4 HDLを変更する
reuse_source = """
module dot4_fixed(input trit x0, x1, x2, x3, output trit [1:0] y);
  assign y = x0 - x1 + x2 + x3;
endmodule
"""''',

"reuse6": '''# 6-5 変更したHDLから全工程を実行する
need("reuse_source", why="実行するHDLは、6-4に書いてあります。")
from reuse import run
reuse_result = run(reuse_source, output_dir=BUILD/"reuse", step_s=5e-9,
                   exhaustive_limit=27, sample_size=11)''',

"shuttle6": '''# 6-6 MPWフレームとパッドを付けた内積回路
need("dot4_layout", why="フレームに載せるdot4は、4-1で配置配線します。")
import subprocess
from reuse import chip_view
# The organizer's MPW precheck template, pinned to one commit.
mpw_template = BUILD/"TR-1um_MPW_Sanken"
if not (mpw_template/"scripts/pre_check.py").is_file():
    subprocess.run(["git", "clone", "-q", "https://github.com/munetomo-maruyama/TR-1um_MPW_Sanken.git",
                    str(mpw_template)], check=True)
    subprocess.run(["git", "-C", str(mpw_template), "checkout", "-q",
                    "b3dab389ddaac1056c93bf5704230c6d2f52d5b2"], check=True)
with step("MPWフレームに載せて検証") as s:
    dot4_chip = dot4_layout.result.to_chip(frame="OSS_FRAME", pdk_root=dot4_layout.settings.pdk,
                                           klayout_binary=dot4_layout.settings.klayout,
                                           output_dir=BUILD/"dot4_chip", mpw_template=mpw_template,
                                           force_signoff=True)
    s.done(f"2500 × 2500 µm · パッド{len(dot4_chip.data['pad_map'])}個 · "
           + ("全検査に合格" if dot4_chip.report["clean"] else "不合格の検査がある"))
dot4_chip_report = chip_view(dot4_chip, dot4)''',

"playground": '''# 7-1 Playground
playground_source = """
module add2(input trit [1:0] a, b, output trit [2:0] s);
  assign s = a + b;
endmodule
"""
from reuse import run
playground = run(playground_source, output_dir=BUILD/"playground", step_s=5e-9,
                 exhaustive_limit=27, sample_size=11)''',
}

CHAPTERS = ["00_opening.md", "01_first.md", "02_cells.md", "03_hdl.md", "04_pnr.md", "05_verify.md", "06_results.md", "07_playground.md"]

# Presentation literals and cell-title comments only; HDL and executable expressions are shared.
ENGLISH = {
    "全掃引は長時間かかる（N=16の解析とN=32の配置配線試行を含む）。": "The full campaign takes a long time (N=16 analysis and the N=32 routing attempt).",
    "入力0 V": "Input 0 V",
    "抵抗による近似": "Resistive estimate",
    "内積の規模と面積": "Dot-product size and area",
    "静的電流と電力": "Static current and power",
    "STAとSPICE": "STA and SPICE",
    "HDLを変更する": "Edit HDL",
    "変更したHDLから全工程を実行する": "Run the full flow on the edited HDL",
    "MPWフレームとパッドを付けた内積回路": "Dot-product circuit with MPW frame and pads",
    "フレームに載せるdot4は、4-1で配置配線します。": "The dot4 placed in the frame is routed in 4-1.",
    "MPWフレームに載せて検証": "Place in the MPW frame and verify",
    "µm · パッド": "µm · ",
    "個 · ": " pads · ",
    "全検査に合格": "all checks pass",
    "不合格の検査がある": "some checks fail",
    
    "表示する記録は、6-1で読み込みます。": "The recorded data is loaded in 6-1.",
    "比較する記録は、6-1で読み込みます。": "The recorded data for comparison is loaded in 6-1.",
    "実行するHDLは、6-4に書いてあります。": "The HDL to run is defined in 6-4.",
    "供給電力 (mW)": "Supply power (mW)",
    "配置配線が未完了": "incomplete at place and route",
    "検証が未完了": "incomplete at verification",
    "追加試行 N=": "Optional attempt N=",
    " は": " is ",
    "のため、以下の比較には含めない。": "; excluded from the comparisons below.",
    "で既定値から変更した配置配線条件：": " place and route overrides: ",
    "行間チャネルの配線トラック ": "inter-row channel tracks ",
    "本、": ", ",
    "M1の幅1 µm当たりの許容電流 ": "permitted current per 1 µm of M1 width ",
    "記録の条件：ngspice-": "Recorded conditions: ngspice-",
    " °C、電源 +5 / 0 / −5 V。": " °C, supplies +5 / 0 / −5 V. ",
    "出力負荷 ": "Output load ",
    " fF、入力の変化時間 ": " fF, input slew ",
    " ns、": " ns, ",
    "最大時間刻み ": "maximum time step ",
    " ns。各状態の保持時間は ": " ns. Hold time per state: ",
    "、": ", ",
    "。": ".",
    "準備": "Setup",
    "GitHubからソースを取得": "Fetch source from GitHub",
    "コミット ": "Commit ",
    " を取得": " · fetch",
    " に切り替え": " · switch",
    "ファイルを展開": "Check out files",
    "ツールを確認": "Check tools",
    "合成するHDLは、1-1に書いてあります。": "The HDL to synthesize is defined in 1-1.",
    "配置配線する回路 net は、1-2で合成します。": "The netlist net is synthesized in 1-2.",
    "DRCとLVSは、1-3で作ったGDSを調べます。": "DRC and LVS check the GDS generated in 1-3.",
    "シミュレーションは、1-4でLVSが一致したGDSから回路を取り出して動かします。": "Simulation uses the circuit extracted from the LVS-matched GDS in 1-4.",
    "合成するHDLは、3-1に書いてあります。": "The HDL to synthesize is defined in 3-1.",
    "合成するHDLは、3-3に書いてあります。": "The HDL to synthesize is defined in 3-3.",
    "合成するHDLは、3-5に書いてあります。": "The HDL to synthesize is defined in 3-5.",
    "合成するHDLは、3-7に書いてあります。": "The HDL to synthesize is defined in 3-7.",
    "配置配線する回路は、3-8で合成した内積です。": "The dot-product netlist is synthesized in 3-8.",
    "表示するGDSは、4-1で作ります。": "The GDS to display is generated in 4-1.",
    "検証するGDSは、4-1で作ります。": "The GDS to verify is generated in 4-1.",
    "抽出は、5-1でLVSが一致したGDSから行います。": "Extraction uses the LVS-matched GDS from 5-1.",
    "シミュレーションする回路は、5-2で抽出します。": "The circuit to simulate is extracted in 5-2.",
    "比べるSPICEの結果は、5-3で求めます。": "The SPICE results for comparison are computed in 5-3.",
    "STAの条件：5-3と同じ入力の列、出力の負荷 100 fF、入力の変化時間 1 ns、配線容量は5-2の抽出値。":
        "STA conditions: input sequence from 5-3, output load 100 fF, input slew 1 ns, wire capacitance extracted in 5-2.",
    "HDLを読み込んで合成": "Parse HDL and synthesize",
    "全入力で等価": "equivalent for all inputs",
    "等価でない": "not equivalent",
    "全区間で ±0.5 V の帯に入った": "within the ±0.5 V band in every interval",
    "帯に入らない区間がある": "outside the band in some intervals",
    "INVのDC解析": "INV DC analysis",
    "INVのDC解析と寸法": "INV DC analysis and sizing",
    "入力 0 V：Y = ": "Input 0 V: Y = ",
    "寸法の記録を照合": "Check recorded sizing data",
    "通り · 回路・モデル・解析コードが一致": " candidates · schematic, models and analysis code match",
    "NANYと +1 の定数から作れる1入力関数": "Unary functions from NANY and the +1 constant",
    "作れた1入力関数：": "Unary functions constructed: ",
    "、最も深いもので ": "; maximum depth ",
    " 段": " stages",
    "NANYは2つの入力の両方に依存し、出力に−1・0・+1のすべてが現れる：":
        "NANY depends on both inputs and takes all three output values (−1, 0, +1):",
    "セルの真理値表": "Cell truth tables",
    "スタンダードセル": "Standard cells",
    "HDL：+ で書いた全加算器": "HDL: full adder using +",
    "HDL：* で書いた1トリットの積": "HDL: one-trit product using *",
    "HDL：同じ選択を2通りに書く": "HDL: two descriptions of selection",
    "HDL：三値重みの4項の内積": "HDL: four-term dot product with ternary weights",
    "論理合成して比べる": "Synthesize and compare",
    "論理合成": "Logic synthesis",
    "論理合成する": "Logic synthesis",
    "合成する": "Logic synthesis",
    "論理合成": "Logic synthesis",
    "配置配線する": "Place and route",
    "配置配線": "Place and route",
    "DRCとLVS": "DRC and LVS",
    
    
    "ポストレイアウトシミュレーション": "Post-layout simulation",
    "抽出と配線容量": "Extraction and wire capacitance",
    "INVの遅延の表": "INV delay table",
    "三値のSTAとSPICEの比較": "Ternary STA and SPICE comparison",
    "三値のSTA": "Ternary STA",
    "不一致": "Mismatch",
    "一致": "Matched",
    "違反 ": "Violations: ",
    "件": "",
    "素子のネットリスト · ": "Device netlist · ",
    "本に配線容量を追加": " signal nets",
    "信号": "Wire capacitance added to ",
    "配線長の見積もり ": "Estimated wire length ",
    "配線 ": "Routed nets: ",
    "本": "",
    "ビア ": "Vias: ",
    "個": "",
    "セル": " cells",
    "行": " rows",
    " · 全": " · all ",
    "入力で等価": " input vectors equivalent",
    "出力": " outputs",
}


def code_source(source, lang):
    """Translate presentation literals and title comments, preserving executable tokens."""
    if lang == "ja":
        return source
    source = localize_source(source, ENGLISH)
    tokens = [token._replace(string=translate_text(token.string, ENGLISH))
              if token.type == tokenize.COMMENT else token
              for token in tokenize.generate_tokens(StringIO(source).readline)]
    source = tokenize.untokenize(tokens)
    if re.search(r"[ぁ-んァ-ヶ一-龠]", source):
        raise ValueError("Missing English code-cell translation:\n" + source)
    return source


def cells(ref, lang="ja"):
    if lang not in ("ja", "en"):
        raise ValueError(f"unknown language: {lang}")
    out = []
    setup = SETUP.replace('"PINNED"', f'"{ref}"')
    setup = setup.replace("from live import step, run_stages",
                          f'from live import step, run_stages, set_language as set_notebook_language\nset_notebook_language("{lang}")')
    setup = setup.replace('os.environ["TRITFLOW_NOTEBOOK_LANGUAGE"] = "ja"',
                          f'os.environ["TRITFLOW_NOTEBOOK_LANGUAGE"] = "{lang}"')
    setup = ('#@title 準備 { display-mode: "form" }\n' + setup
             + PREAMBLE.replace('set_language("ja")', f'set_language("{lang}")'))
    narrative = HERE/("narrative_en" if lang == "en" else "narrative")
    tables, suffix = (TABLES_EN, "_en") if lang == "en" else (TABLES, "")

    def figure(match):
        name = match[1]
        path = f"figures/out/{name}{'_ja' if lang == 'ja' else ''}.png"
        # The Japanese flow map has no published English counterpart; its translated vector
        # labels and raster live here so EN does not edit the figure stream's files.
        if lang == "en" and name == "fig_flow_map":
            path = "notebook/v3/assets/fig_flow_map.png"
        if not (ROOT/path).is_file():
            raise FileNotFoundError(path)
        return f"![{name}]({RAW}/{ref}/{path})"

    for index, name in enumerate(CHAPTERS):
        text = (narrative/name).read_text()
        unknown = set(re.findall(r"<!-- code: (\w+) -->", text)) - CODE.keys()
        if unknown:
            raise ValueError(f"{name}: undefined code cells: {', '.join(sorted(unknown))}")
        text = re.sub(r"<!-- tables: ([\w ]+) -->", lambda m: "&emsp;&emsp;".join(
            f'<img src="{CDN}@{ref}/notebook/assets/tables/{name}{suffix}.svg" width="{width(tables[name])}" alt="{name}">'
            for name in m[1].split()), text)
        text = re.sub(r"<!-- asset: (\S+) \| (.+?) -->", lambda m: f"<details><summary>{m[2]}</summary>\n\n"
                      f"![{m[2]}]({RAW}/{ref}/{m[1]})\n\n</details>", text)
        text = re.sub(r"<!-- figure: (\w+) -->", figure, text)
        for chunk in re.split(r"\n*<!-- code: (\w+) -->\n*", text):
            if chunk in CODE:
                out.append(("code", code_source(CODE[chunk], lang)))
            elif chunk.strip():
                out.append(("markdown", chunk.strip()))
        if index == 0:
            out.append(("code", code_source(setup, lang)))
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", choices=("ja", "en"), default="ja")
    parser.add_argument("--ref", default="HEAD")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    ref = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", args.ref], text=True).strip()
    output = args.out or HERE/f"tritflow_{args.lang}.ipynb"
    nb = {"nbformat": 4, "nbformat_minor": 5,
          "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
                       "language_info": {"name": "python"}, "colab": {"name": f"tritflow_{args.lang}.ipynb"}},
          "cells": [{"cell_type": kind, "id": f"c{i}", "metadata": {}, "source": source,
                     **({"execution_count": None, "outputs": []} if kind == "code" else {})}
                    for i, (kind, source) in enumerate(cells(ref, args.lang))]}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + "\n")
    print(output, ref)


if __name__ == "__main__":
    main()
