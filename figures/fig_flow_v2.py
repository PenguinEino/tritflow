"""Fig. 1 (v2) — one ternary HDL source to a checked TR-1um layout, drawn from the real GDS."""

import io
import json

import klayout.db as db
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import PolyCollection
from matplotlib.patches import ConnectionPatch, FancyArrowPatch

from tritflow import CELLS_DIR, ROOT, flow
from tritflow.viz.layers import LAYER_STYLE, MATPLOTLIB_HATCH

import paperstyle as style

B = ROOT / "build/full_add"
# examples/full_add.tv, with its long instance lines wrapped to fit the panel.
HDL = """module full_add(
  input  trit a, b, cin,
  output trit sum, cout);
  wire trit s1, c1, c2, nc;
  half_add ha1(.a(a), .b(b),
               .sum(s1), .carry(c1));
  half_add ha2(.a(s1), .b(cin),
               .sum(sum), .carry(c2));
  nany g_nc  (nc, c1, c2);
  inv  g_cout(cout, nc);
endmodule"""


TEXT = {
    "en": {"hdl": "TritVerilog", "hdl_note": ["a full adder: a + b + cin = sum + 3·cout", "built from two half adders"],
           "synth": "Synthesis", "synth_note": "{n} cells ({counts}); at a = b = cin = +1:",
           "synth_note2": "1 + 1 + 1 = 0 + 3·(+1)  (red +1, blue −1, gray 0)",
           "cell": "Standard cell", "cell_note": ["NANY, from the taped-out", "circuit; 3 rails"],
           "pnr": "Place & route", "pnr_note": "DRC {drc}, LVS {lvs}", "match": "match", "mismatch": "mismatch",
           "zoom_note": ["magnified: transistors,", "M1, M2 and vias"],
           "spice": "Post-layout SPICE", "spice_note": ["extracted devices + wire C", "three levels, ±0.5 V bands"]},
    "ja": {"hdl": "三値のHDL（TritVerilog）", "hdl_note": ["全加算器：a + b + cin = sum + 3·cout", "半加算器2個で組む"],
           "synth": "合成", "synth_note": "{n}セル（{counts}）。a = b = cin = +1 のとき",
           "synth_note2": "1 + 1 + 1 = 0 + 3·(+1)（赤 +1、青 −1、灰 0）",
           "cell": "スタンダードセル", "cell_note": ["NANY。テープアウトした", "回路から。電源レール3本"],
           "pnr": "配置配線", "pnr_note": "DRC {drc}件、LVS {lvs}", "match": "一致", "mismatch": "不一致",
           "zoom_note": ["拡大：トランジスタ、", "M1・M2とビア"],
           "spice": "ポストレイアウトシミュレーション", "spice_note": ["抽出した素子＋配線容量", "3つのレベル、±0.5 Vの帯"]},
}


def draw_gds(ax, path, *, line=0.3):
    """Every drawn layer of a GDS, flattened, in the notebook's TR-1um colors and hatches."""
    layout = db.Layout()
    layout.read(str(path))
    top = layout.top_cells()[0]
    for key, _, color, hatch, opacity in LAYER_STYLE:
        index = layout.find_layer(*key)
        if index is None:
            continue
        region = db.Region(top.begin_shapes_rec(index)).merged()
        polygons = [[(p.x*layout.dbu, p.y*layout.dbu) for p in
                     (poly.to_simple_polygon().each_point() if poly.holes() else poly.each_point_hull())]
                    for poly in region.each()]
        if not polygons:
            continue
        if opacity:
            ax.add_collection(PolyCollection(polygons, facecolors=color, alpha=opacity, linewidths=0))
        ax.add_collection(PolyCollection(polygons, facecolors="none", edgecolors=color, linewidths=line,
                                         hatch=MATPLOTLIB_HATCH[hatch]))
    box = top.dbbox()
    ax.set_xlim(box.left, box.right)
    ax.set_ylim(box.bottom, box.top)
    ax.set_aspect("equal")
    ax.axis("off")
    return box


def panel(fig, rect, title, note):
    """An axes with its title above and a two-line note below, in figure coordinates."""
    ax = fig.add_axes(rect)
    x, y, w, h = rect
    fig.text(x, y+h+0.045, title, fontsize=9, fontweight="bold", color=style.INK, va="bottom")
    fig.text(x, y-0.025, "\n".join(note), fontsize=7.4, color=style.INK2, va="top", linespacing=1.35)
    return ax


def arrow(fig, start, end, **options):
    fig.patches.append(FancyArrowPatch(start, end, transform=fig.transFigure, arrowstyle="-|>",
                                       mutation_scale=13, lw=1.6, color=style.INK2, **options))


def make(lang="en"):
    style.use()
    T = TEXT[lang]
    if lang == "ja":
        plt.rcParams["font.family"] = ["Nimbus Roman", "Noto Serif CJK JP"]
    plt.rcParams["hatch.linewidth"] = 0.25
    report = json.loads((B/"full_add.report.json").read_text())
    pnr = json.loads((B/"full_add.pnr.json").read_text())
    lvs = json.loads((B/"full_add.lvs.summary.json").read_text())
    drc_items = pnr.get("checks", {}).get("pdk_drc", {}).get("violations") or 0
    fig = plt.figure(figsize=(style.DOUBLE, 5.1))

    # Top row: the source and what synthesis makes of it.
    top, height = 0.635, 0.29
    ax = panel(fig, [0.01, top, 0.3, height], T["hdl"], T["hdl_note"])
    ax.axis("off")
    ax.add_patch(plt.Rectangle((0, 0), 1, 1, transform=ax.transAxes, fc="#f6f5f1", ec=style.AXIS, lw=0.6))
    ax.text(0.05, 0.94, HDL, transform=ax.transAxes, family="monospace", fontsize=6.2, va="top",
            color=style.INK, linespacing=1.3)
    counts = " + ".join(f"{n} {cell}" for cell, n in sorted(report["cells"].items(), key=lambda kv: -kv[1]))
    ax = panel(fig, [0.36, top, 0.63, height], T["synth"],
               [T["synth_note"].format(n=report['total_cells'], counts=counts), T["synth_note2"]])
    ax.axis("off")
    adder = flow.load(ROOT/"examples/full_add.tv", "full_add").synthesize()
    schematic = adder.schematic(inputs={"a": 1, "b": 1, "cin": 1}, net_names=False, title="", expand="*")
    picture = plt.imread(io.BytesIO(schematic.png(scale=3)))
    picture = picture[int(picture.shape[0]*0.05):int(picture.shape[0]*0.79)]   # drop the cell count and legend
    ink = np.where((picture[..., :3] < 0.92).any(axis=2))
    picture = picture[ink[0].min():ink[0].max()+1, ink[1].min():ink[1].max()+1]
    ax.imshow(picture, interpolation="lanczos")
    ax.set_anchor("W")
    arrow(fig, (0.315, top+height/2), (0.352, top+height/2))

    # Bottom row: the cell it is built from, the routed layout, and the extracted circuit running.
    low, height = 0.11, 0.29
    ax = panel(fig, [0.01, low, 0.16, height], T["cell"], T["cell_note"])
    draw_gds(ax, CELLS_DIR/"out/NANY/NANY.gds", line=0.35)
    ax = panel(fig, [0.21, low, 0.2, height], T["pnr"],
               [f"{pnr['die'][0]:.0f} × {pnr['die'][1]:.0f} µm, M1 + M2",
                T["pnr_note"].format(drc=drc_items, lvs=T["match"] if lvs["matched"] else T["mismatch"])])
    box = draw_gds(ax, B/"full_add.gds", line=0.08)
    # A corner next to the magnified view keeps the guide lines short.
    size = 0.28*box.width()
    x0, y0 = box.right-0.03*box.width()-size, box.bottom+0.35*box.height()
    ax.add_patch(plt.Rectangle((x0, y0), size, size, fill=False, ec="#eb6834", lw=0.9, zorder=10))
    zoom = panel(fig, [0.43, low, 0.2, height], "", T["zoom_note"])
    draw_gds(zoom, B/"full_add.gds", line=0.25)
    zoom.set_xlim(x0, x0+size)
    zoom.set_ylim(y0, y0+size)
    zoom.axis("on")
    zoom.set_xticks([])
    zoom.set_yticks([])
    for spine in zoom.spines.values():
        spine.set_edgecolor("#eb6834")
        spine.set_linewidth(0.9)
    fig.add_artist(ConnectionPatch((x0+size, y0+size), (0, 1), "data", "axes fraction", axesA=ax, axesB=zoom,
                                   color="#eb6834", lw=0.6, ls=":"))
    fig.add_artist(ConnectionPatch((x0+size, y0), (0, 0), "data", "axes fraction", axesA=ax, axesB=zoom,
                                   color="#eb6834", lw=0.6, ls=":"))

    ax = panel(fig, [0.7, low, 0.25, height], T["spice"], T["spice_note"])
    z = np.load(B/"postlayout/post/waveforms.npz")
    t = z["time"]*1e6
    window = t <= 4.2
    style.bands(ax)
    ax.plot(t[window], z["v(sum)"][window], color=style.BLUE, lw=0.9)
    ax.plot(t[window], z["v(cout)"][window], color=style.ORANGE, lw=0.9)
    ax.set_yticks([-5, 0, 5], ["−1", "0", "+1"])
    ax.yaxis.tick_right()
    ax.set_ylim(-6.5, 6.5)
    ax.tick_params(labelsize=7, length=0)
    ax.set_xticks([])
    ax.set_xlim(0, 4.2)
    ax.text(4.15, -6.2, "4 µs", fontsize=6, color=style.INK2, ha="right")
    ax.text(0.05, 6.0, "sum", fontsize=6, color=style.BLUE)
    ax.text(0.8, 6.0, "cout", fontsize=6, color=style.ORANGE)

    middle = low+height/2
    # From the end of the top row, around the right margin and back to the start of the bottom row.
    turn = 0.537
    # Leave the top row sideways, like the other arrows, then turn down at the margin.
    fig.add_artist(plt.Line2D([0.962, 0.993, 0.993, 0.03], [top+height/2, top+height/2, turn, turn],
                              transform=fig.transFigure, color=style.INK2, lw=1.6, solid_joinstyle="round",
                              solid_capstyle="round"))
    # shrinkA=0: the arrow continues the line without a gap at the corner.
    arrow(fig, (0.03, turn), (0.03, low+height+0.085), shrinkA=0)
    arrow(fig, (0.175, middle), (0.205, middle))
    arrow(fig, (0.645, middle), (0.69, middle))
    return style.save(fig, "fig_flow_v2" + ("" if lang == "en" else f"_{lang}"))


if __name__ == "__main__":
    print(make("en"), make("ja"))
