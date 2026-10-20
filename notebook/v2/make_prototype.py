"""Build the live-progress prototype notebook (chapter 1 sketch for v2)."""
import json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/"notebook"))
import stages

revision = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
setup = re.sub(r'(?m)^SOURCE_REF = .*', f'SOURCE_REF = os.environ.get("TRITFLOW_REF", "{revision}")', stages.SETUP)

cells = [
("markdown", "# ライブ表示の試作\n\n「ランタイム → すべてのセルを実行」で、各セルの進捗表示を確かめます。"),
("code", "#@title 準備 { display-mode: \"form\" }\n" + setup + '''
BUILD = Path(os.environ.get("TRITFLOW_NOTEBOOK_BUILD", ROOT/"build/notebook")).resolve()
from live import step, need, provides, install_error_view, LayoutView
from tritflow import flow
install_error_view()
provides("design", "1-1 HDLを読み込む")
provides("net", "1-2 合成する")
provides("lay", "1-3 配置配線する")
'''),
("code", '''# 1-1 HDLを読み込む
source = """
module first(input trit a, output trit y);
  assign y = a & ~a;   // & is min
endmodule
"""
with step("HDLを読み込む") as s:
    design = flow.loads(source, "first")
    s.done("1入力 · 1出力")'''),
("code", '''# 1-2 合成する
need("design", why="合成する回路のHDLは、1-1で読み込みます。")
with step("合成") as s:
    net = design.synthesize()
    s.done(" · ".join(f"{cell}×{n}" for cell, n in net.report()["cells"].items()))'''),
("code", '''# 1-3 配置配線する
need("net", why="このセルは、合成した回路 net を配置配線します。")
with step("配置配線", view=LayoutView()) as s:
    lay = net.place_and_route(output_dir=BUILD/"first", seed=0)
    s.done(f"{lay.stats['instance_count']}セル · {lay.stats['die_size_um'][0]:.0f} × {lay.stats['die_size_um'][1]:.0f} µm")'''),
("code", '''# 1-4 DRCとLVS
need("lay", why="DRCとLVSは、1-3で作ったGDSを調べます。")
with step("DRC") as s:
    drc = lay.drc()
    s.done(f"違反 {drc['violations']}件")
with step("LVS") as s:
    lvs = lay.lvs()
    s.done("一致" if lvs["matched"] else "不一致")'''),
("code", '''# 1-5 抽出後のSPICE
need("lay", why="SPICEは、1-3で作ったGDSから取り出した回路を動かします。")
vectors = [(-1,), (0,), (1,), (0,), (-1,)]
with step("抽出後SPICE") as s:
    post = lay.extract().simulate(vectors, load=100e-15, expected=lambda v: {"y": min(v[0], -v[0])},
                                  hold_s=1e-6, step_s=2e-9, edge_s=1e-9, temperature_c=27)
    s.done("全区間で合格" if post["measurements"]["passed"] else "不合格")'''),
("code", '''# 1-6 振り返る
need("lay", why="配置配線の途中経過は、1-3の実行で記録されます。")
from tritflow.viz.layout import placement_animation, routing_progress
placement_animation(lay.data).show()
routing_progress(lay.data).show()'''),
("code", '''# 順番を間違えた例：未定義の変数を使う
del lay
with step("DRC") as s:
    lay.drc()'''),
]
nb = {"nbformat": 4, "nbformat_minor": 5,
      "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
                   "colab": {"name": "prototype_live.ipynb"}},
      "cells": [{"cell_type": k, "id": f"c{i}", "metadata": {}, "source": s,
                 **({"execution_count": None, "outputs": []} if k == "code" else {})}
                for i, (k, s) in enumerate(cells)]}
Path(__file__).with_name("prototype_live.ipynb").write_text(json.dumps(nb, ensure_ascii=False, indent=1))
