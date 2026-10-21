"""Chapter 1 recap — the flow the reader just ran on ``y = a & ~a``, as a block diagram.

Each block shows what that stage produced for this circuit, drawn from a real run. White blocks
are TritFlow's own; grey blocks are open-source tools (KLayout, ngspice) with the PDK's decks
and models.
"""

import io

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, Rectangle

from tritflow import CELLS_DIR, ROOT, flow

import paperstyle as style
from fig_flow_v2 import draw_gds

B = ROOT/"build/fig_flow_map"
SOURCE = "module first(\n  input  trit a,\n  output trit y);\n  assign y = a & ~a;\nendmodule"
OSS_FILL, OSS_EDGE = "#ecebe6", "#a9a79f"


def run():
    """The chapter 1 flow on ``a & ~a``: synthesis, P&R, LVS, extraction and post-layout SPICE."""
    net = flow.loads(SOURCE+"\n", "first").synthesize()
    lay = net.place_and_route(output_dir=B, seed=0)
    drc, lvs = lay.drc(), lay.lvs()
    extracted = lay.extract()
    post = extracted.simulate([(-1,), (0,), (1,), (0,), (-1,)], load=100e-15, hold_s=1e-6, step_s=2e-9,
                              edge_s=1e-9, temperature_c=27)
    return net, lay, drc, lvs, extracted, post


def block(fig, rect, title, tool, oss=False):
    """A block with its title above the picture and the tool that does it below."""
    x, y, w, h = rect
    fig.patches.append(Rectangle((x, y), w, h, transform=fig.transFigure, fc=OSS_FILL if oss else "white",
                                 ec=OSS_EDGE if oss else style.INK, lw=0.8, zorder=-1))   # under the picture
    fig.text(x+w/2, y+h-0.035, title, ha="center", va="top", fontsize=8.5, fontweight="bold", color=style.INK)
    fig.text(x+w/2, y+0.022, tool, ha="center", va="bottom", fontsize=7, color=style.INK2,
             style="italic" if oss else "normal")
    ax = fig.add_axes([x+0.012, y+0.075, w-0.024, h-0.165])
    ax.axis("off")
    return ax


def arrow(fig, start, end):
    fig.patches.append(FancyArrowPatch(start, end, transform=fig.transFigure, arrowstyle="-|>",
                                       mutation_scale=10, lw=1.0, color=style.INK2, shrinkA=0, shrinkB=0))


def make():
    style.use()
    plt.rcParams["font.family"] = ["Nimbus Roman", "Noto Serif CJK JP"]
    plt.rcParams["hatch.linewidth"] = 0.25
    net, lay, drc, lvs, extracted, post = run()
    fig = plt.figure(figsize=(style.DOUBLE, 3.9))

    top, low, h = 0.53, 0.06, 0.40
    w4, gap4 = 0.225, 0.033
    xs = [0.005+k*(w4+gap4) for k in range(4)]
    ax = block(fig, [xs[0], top, w4, h], "三値のHDL", "TritFlow（TritVerilog）")
    ax.text(0.0, 0.92, SOURCE, family="monospace", fontsize=6.4, va="top", color=style.INK, linespacing=1.35)
    ax = block(fig, [xs[1], top, w4, h], "論理合成", "TritFlow")
    picture = plt.imread(io.BytesIO(net.schematic(inputs={"a": 0}, title="", expand="*").png(scale=3)))
    picture = picture[int(picture.shape[0]*0.12):int(picture.shape[0]*0.62)]   # drop the cell count and legend
    ink = np.where((picture[..., :3] < 0.92).any(axis=2))
    picture = picture[ink[0].min():ink[0].max()+1, ink[1].min():ink[1].max()+1]
    ax.imshow(picture, interpolation="lanczos")
    ax = block(fig, [xs[2], top, w4, h], "スタンダードセル", "TritFlow（テープアウトした回路）")
    draw_gds(ax, CELLS_DIR/"out/INV/INV.gds", line=0.3)
    ax = block(fig, [xs[3], top, w4, h], "配置配線", "TritFlow")
    draw_gds(ax, lay.gds_path, line=0.15)
    for k in range(3):
        arrow(fig, (xs[k]+w4, top+h/2), (xs[k+1], top+h/2))

    w5, gap5 = 0.176, 0.03
    xs5 = [0.005+k*(w5+gap5) for k in range(5)]
    ax = block(fig, [xs5[0], low, w5, h], "DRC・LVS", "KLayout＋PDKのデッキ", oss=True)
    draw_gds(ax, lay.gds_path, line=0.15)
    ax.text(0.5, 1.0, f"DRC {drc['violations']}件 · LVS {'一致' if lvs['matched'] else '不一致'}", transform=ax.transAxes,
            ha="center", va="bottom", fontsize=6.8, color=style.INK)
    ax = block(fig, [xs5[1], low, w5, h], "抽出", "KLayout", oss=True)
    lines = [l for l in extracted.spice.splitlines() if l[:1] in ("M", "R", "X") and "first" not in l.lower()][:7]
    ax.text(0.0, 0.95, "\n".join(l[:27] for l in lines), family="monospace", fontsize=4.6, va="top",
            color=style.INK, linespacing=1.4)
    ax = block(fig, [xs5[2], low, w5, h], "配線容量の見積もり", "TritFlow")
    caps = {n: v["capacitance_f"] for n, v in extracted.capacitance["nets"].items() if n not in ("VDD", "VMID", "VSS")}
    ax.text(0.0, 0.95, "\n".join(f"C({n}) = {c*1e15:4.0f} fF" for n, c in caps.items()), family="monospace",
            fontsize=6.4, va="top", color=style.INK, linespacing=1.6)
    ax.text(0.0, 0.18, "M1/M2の面積と周長から", fontsize=6.2, color=style.INK2)
    data = post["waveforms"]
    t = data["time"]*1e6
    ax = block(fig, [xs5[3], low, w5, h], "回路シミュレーション", "ngspice＋PDKのモデル", oss=True)
    ax.plot(t, data["v(a)"], color=style.INK2, lw=0.7)
    ax.plot(t, data["v(y)"], color=style.BLUE, lw=0.9)
    ax.text(0.02, 0.98, "a", transform=ax.transAxes, fontsize=6.5, color=style.INK2, va="top")
    ax.text(0.12, 0.98, "y", transform=ax.transAxes, fontsize=6.5, color=style.BLUE, va="top")
    ax = block(fig, [xs5[4], low, w5, h], "三値の判定", "TritFlow")
    style.bands(ax)
    ax.plot(t, data["v(y)"], color=style.BLUE, lw=0.9)
    for row in post["measurements"]["rows"]:
        out = row["outputs"]["y"]
        ax.plot(row["check_s"]*1e6, out["voltage_v"], marker="o", ms=3.2, mfc="white",
                mec=style.AQUA if out["passed"] else style.ORANGE, mew=1.0)
    ax.set_ylim(-6.5, 6.5)
    ax.text(0.98, 0.02, "±0.5 V", transform=ax.transAxes, fontsize=6, color=style.INK2, ha="right")
    for k in range(4):
        arrow(fig, (xs5[k]+w5, low+h/2), (xs5[k+1], low+h/2))
    # From the end of the top row down to the start of the bottom row.
    fig.add_artist(plt.Line2D([xs[3]+w4/2, xs[3]+w4/2, xs5[0]+w5/2], [top, top-0.03, top-0.03],
                              transform=fig.transFigure, color=style.INK2, lw=1.0))
    arrow(fig, (xs5[0]+w5/2, top-0.03), (xs5[0]+w5/2, low+h))

    fig.patches.append(Rectangle((0.73, 0.005), 0.018, 0.03, transform=fig.transFigure, fc="white", ec=style.INK, lw=0.8))
    fig.text(0.752, 0.02, "TritFlow", fontsize=7, va="center")
    fig.patches.append(Rectangle((0.84, 0.005), 0.018, 0.03, transform=fig.transFigure, fc=OSS_FILL, ec=OSS_EDGE, lw=0.8))
    fig.text(0.862, 0.02, "OSS", fontsize=7, va="center")
    return style.save(fig, "fig_flow_map_ja")


if __name__ == "__main__":
    print(make())
