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

RAW = "https://raw.githubusercontent.com/PenguinEino/tritflow"

PREAMBLE = '''
from live import need, provides, install_error_view, LayoutView
from views import pick_input, flow_map, stimulus
from tritflow import flow
from tritflow.viz.graph import gate_graph
from tritflow.viz.layout import gds_viewer
install_error_view()
for name, cell in {"net": "1-1 HDLを書いて合成する", "lay": "1-2 配置配線する",
                   "lvs": "1-3 DRCとLVS", "post": "1-4 ポストレイアウトシミュレーション"}.items():
    provides(name, cell)
'''

CODE = {
"hdl": '''# 1-1 HDLを書いて合成する
source = """
module first(input trit a, output trit y);
  assign y = a & ~a;
endmodule
"""
with step("HDLを読み込んで合成") as s:
    net = flow.loads(source).synthesize()
    s.done(" · ".join(f"{cell}×{n}" for cell, n in net.report()["cells"].items())
           + (" · 全入力で等価" if net.equivalence["passed"] else " · 等価でない"))
gate_graph(net, title=f"{net.top}：合成した回路").show()''',

"pnr": '''# 1-2 配置配線する
need("net", why="配置配線する回路 net は、1-1で合成します。")
with step("配置配線", view=LayoutView()) as s:
    lay = net.place_and_route(output_dir=BUILD/net.top, seed=0)
    width, height = lay.stats["die_size_um"]
    s.done(f"{lay.stats['instance_count']}セル · {width:.0f} × {height:.0f} µm · 配線 {lay.stats['routed_nets']}本")''',

"check": '''# 1-3 DRCとLVS
need("lay", why="DRCとLVSは、1-2で作ったGDSを調べます。")
with step("DRC") as s:
    drc = lay.drc()
    s.done(f"違反 {drc['violations']}件")
with step("LVS") as s:
    lvs = lay.lvs()
    s.done("一致" if lvs["matched"] else "不一致")
gds_viewer(lay.gds_path)''',

"spice": '''# 1-4 ポストレイアウトシミュレーション
need("lvs", why="シミュレーションは、1-3でLVSが一致したGDSから回路を取り出して動かします。")
with step("抽出と配線容量") as s:
    extracted = lay.extract()
    signals = [n for n in extracted.capacitance["nets"] if n not in ("VDD", "VMID", "VSS")]
    s.done(f"信号{len(signals)}本に配線容量を追加")
with step("ngspice") as s:
    post = extracted.simulate(stimulus(net), load=100e-15, hold_s=1e-6, step_s=2e-9,
                              edge_s=1e-9, temperature_c=27)
    s.done("全区間で ±0.5 V の帯に入った" if post["measurements"]["passed"] else "帯に入らない区間がある")
pick_input(net, post)''',

"map": '''# 1-5 いま何が起きたか
need("post", why="この図は、1-1から1-4までの実行結果をまとめます。")
flow_map(net, lay, drc, lvs, extracted, post)''',
}

CHAPTERS = ["00_opening.md", "01_first.md"]


def cells(ref):
    out = []
    setup = "#@title 準備（最初に実行） { display-mode: \"form\" }\n" + SETUP.replace('"PINNED"', f'"{ref}"') + PREAMBLE
    for index, name in enumerate(CHAPTERS):
        text = (HERE/"narrative"/name).read_text()
        text = re.sub(r"<!-- figure: (\w+) -->", lambda m: f"![図1]({RAW}/{ref}/figures/out/{m[1]}.png)", text)
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
