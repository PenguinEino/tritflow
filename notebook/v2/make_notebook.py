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

PREAMBLE = '''
from live import need, provides, install_error_view, LayoutView
from views import pick_input, flow_map, stimulus
from inverter_views import inverter
from cell_views import closure_view, cell_tables, cell_row
from tritflow import CELLS_DIR
from tritflow.sim.sizing import sweep_dimensions, load_grid
from tritflow import flow
from tritflow.viz.layout import gds_viewer
from tritflow.schematic import set_language
set_language("ja")
install_error_view()
for name, cell in {"source": "1-1 HDL", "net": "1-2 合成する", "lay": "1-3 配置配線する",
                   "lvs": "1-4 DRCとLVS", "post": "1-5 ポストレイアウトシミュレーション"}.items():
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
net.schematic(net_names=True, expand="*", title=f"{net.top}：合成した回路")''',

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
pick_input(net, post)''',

"map": '''# 1-6 いま何が起きたか
need("post", why="この図は、1-1から1-5までの実行結果をまとめます。")
flow_map(net, lay, drc, lvs, extracted, post)''',

"inv": '''# 2-1 INVのDC解析と寸法
with step("ngspice（INVのDC解析）") as s:
    spice = sweep_dimensions("INV", [], workdir=BUILD/"inv")
    zero = next(r for r in spice["rows"][0]["dc"] if r["input_trits"] == [0])
    s.done(f"入力 0 V：Y = {zero['output_v']['Y']:+.3f} V · {abs(zero['rail_current_a']['VDD'])*1e3:.3f} mA")
with step("寸法の記録を照合") as s:
    grid = load_grid("INV")
    s.done(f"{len(grid['rows'])}通り · 回路・モデル・解析コードが一致")
inverter(spice, grid)''',

"closure": '''# 3-1 1入力関数の閉包
from completeness import unary_closure, surjective_and_depends_on_both, inv, nand, nor, nany
bases = [("INV・NAND・NOR＋定数3つ", dict(unary=(inv,), binary=(nand, nor), constants=(-1, 0, 1))),
         ("NANY＋TIEZ", dict(binary=(nany,), constants=(0,))),
         ("NANY＋TIEP・TIEN", dict(binary=(nany,), constants=(-1, 1)))]
closures = [unary_closure(**basis) for _, basis in bases]
closure_view(bases, closures)
print("NANYは2つの入力の両方に依存し、出力に−1・0・+1のすべてが現れる：", surjective_and_depends_on_both(nany))''',

"cells": '''# 3-2 セルの真理値表
cell_tables(CELLS_DIR/"out", ROOT/"notebook/assets/schematics")''',

"stdcells": '''# 3-3 スタンダードセル
import json
cell_row(json.loads((CELLS_DIR/"out/library.json").read_text()), CELLS_DIR/"out")''',
}

CHAPTERS = ["00_opening.md", "01_first.md", "02_inverter.md", "03_cells.md"]


def cells(ref):
    out = []
    setup = "#@title 準備（最初に実行） { display-mode: \"form\" }\n" + SETUP.replace('"PINNED"', f'"{ref}"') + PREAMBLE
    for index, name in enumerate(CHAPTERS):
        text = (HERE/"narrative"/name).read_text()
        text = re.sub(r"<!-- tables: ([\w ]+) -->", lambda m: "&emsp;&emsp;".join(
            f'<img src="{RAW}/{ref}/notebook/assets/tables/{name}.png" width="{width(TABLES[name])}" alt="{name}">'
            for name in m[1].split()), text)
        text = re.sub(r"<!-- asset: (\S+) \| (.+?) -->", lambda m: f"<details><summary>{m[2]}</summary>\n\n"
                      f"![{m[2]}]({RAW}/{ref}/{m[1]})\n\n</details>", text)
        text = re.sub(r"<!-- figure: (\w+) -->", lambda m: f"![図1]({RAW}/{ref}/figures/out/{m[1]}_ja.png)", text)
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
