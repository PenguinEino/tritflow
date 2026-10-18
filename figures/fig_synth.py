"""Fig. 6 — TritVerilog source and the synthesized cells, nets coloured by their trit value."""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch, Path, PathPatch

from tritflow import ROOT, flow
from tritflow.synth.simulate import evaluate_netlist
from tritflow.viz.graph import _structure

import style

SOURCE = """module half_add(input trit a, b,
                output trit sum, carry);
  wire trit t, u, na, d, nd;
  nany g_t (t, a, b);
  nany g_u (u, b, t);
  inv  g_na (na, a);
  nany g_c (carry, na, u);
  nany g_d (d, t, carry);
  inv  g_nd (nd, d);
  nany g_s (sum, nd, carry);
endmodule

module full_add(input trit a, b, cin,
                output trit sum, cout);
  wire trit s1, c1, c2, nc;
  half_add ha1 (.a(a),  .b(b),   .sum(s1),  .carry(c1));
  half_add ha2 (.a(s1), .b(cin), .sum(sum), .carry(c2));
  nany g_nc (nc, c1, c2);
  inv  g_cout (cout, nc);
endmodule"""


def tstr(v):
    return {-1: "−1", 0: "0", 1: "+1"}[int(v)]


def wire(ax, p0, p1, value, lw=1.1):
    (x0, y0), (x1, y1) = p0, p1
    xm = (x0 + x1) / 2
    path = Path([(x0, y0), (xm, y0), (xm, y1), (x1, y1)],
                [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4])
    ax.add_patch(PathPatch(path, fc="none", ec=style.TRIT_COLOR[int(value)], lw=lw, zorder=1,
                           capstyle="round"))


def box(ax, x, y, w, h, label, fs=6.2, fc="white"):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0,rounding_size=0.05",
                                fc=fc, ec=style.INK, lw=0.7, zorder=3))
    ax.text(x, y, label, ha="center", va="center", fontsize=fs, color=style.INK, zorder=4)


def half_adder(ax, vector):
    net = flow.load(ROOT / "examples/half_add.tv", "half_add").synthesize()
    net = getattr(net, "netlist", net)
    values = {k: int(np.asarray(v)) for k, v in evaluate_netlist(net, vector, return_all=True).items()}
    nodes, drivers, loads, pos = _structure(net)
    W, H = 0.62, 0.36
    for name, sinks in loads.items():
        x0, y0 = pos[drivers[name]]
        start = (x0 + (0.12 if nodes[drivers[name]].cell == "INPUT" else W / 2), y0)
        for key, pin in sinks:
            x1, y1 = pos[key]
            dy = {"A": 0.08, "B": -0.08}.get(pin, 0.0)
            end = (x1 - (0.12 if nodes[key].cell == "OUTPUT" else W / 2), y1 + dy)
            wire(ax, start, end, values[name])
    for key, n in nodes.items():
        x, y = pos[key]
        if n.cell == "INPUT":
            ax.text(x + 0.08, y, f"{n.net} = {tstr(values[n.net])}", ha="right", va="center", fontsize=7)
        elif n.cell == "OUTPUT":
            ax.text(x - 0.08, y, f"{n.net} = {tstr(values[n.net])}", ha="left", va="center", fontsize=7)
        else:
            box(ax, x, y, W, H, n.cell)
    xs = [p[0] for p in pos.values()]
    ys = [p[1] for p in pos.values()]
    ax.set_xlim(min(xs) - 0.9, max(xs) + 1.0)
    ax.set_ylim(min(ys) - 0.45, max(ys) + 0.45)


def bt(total):
    """Balanced-ternary digit and carry of a small integer sum."""
    s = ((total + 1) % 3) - 1
    return s, (total - s) // 3


def full_adder(ax, a, b, cin):
    s1, c1 = bt(a + b)
    s, c2 = bt(s1 + cin)
    nc = -max(-1, min(1, c1 + c2))
    cout = -nc
    P = {"a": (0, 1.0), "b": (0, 0.5), "cin": (0, -0.4)}
    for name, (x, y) in P.items():
        ax.text(x, y, f"{name} = {tstr({'a': a, 'b': b, 'cin': cin}[name])}", ha="right",
                va="center", fontsize=7)
    hw, hh = 1.1, 0.95
    box(ax, 1.2, 0.75, hw, hh, "ha1\n5 NANY + 2 INV", fs=5.8, fc="#f6f5f1")
    box(ax, 2.7, 0.15, hw, hh, "ha2\n5 NANY + 2 INV", fs=5.8, fc="#f6f5f1")
    box(ax, 4.05, 0.95, 0.62, 0.36, "NANY")
    box(ax, 4.95, 0.95, 0.62, 0.36, "INV")
    wire(ax, (0.08, 1.0), (1.2 - hw / 2, 0.95), a)
    wire(ax, (0.08, 0.5), (1.2 - hw / 2, 0.55), b)
    wire(ax, (1.2 + hw / 2, 0.55), (2.7 - hw / 2, 0.35), s1)
    wire(ax, (0.12, -0.4), (2.7 - hw / 2, -0.05), cin)
    wire(ax, (1.2 + hw / 2, 0.95), (4.05 - 0.31, 1.05), c1)
    wire(ax, (2.7 + hw / 2, 0.35), (4.05 - 0.31, 0.85), c2)
    wire(ax, (4.05 + 0.31, 0.95), (4.95 - 0.31, 0.95), nc)
    wire(ax, (4.95 + 0.31, 0.95), (5.75, 0.95), cout)
    wire(ax, (2.7 + hw / 2, -0.05), (5.75, -0.05), s)
    for label, y, v in (("cout", 0.95, cout), ("sum", -0.05, s)):
        ax.text(5.8, y, f"{label} = {tstr(v)}", ha="left", va="center", fontsize=7)
    for label, (x, y), v in (("s1", (1.95, 0.52), s1), ("c1", (2.25, 1.08), c1),
                             ("c2", (3.62, 0.5), c2), ("nc", (4.5, 1.03), nc)):
        ax.text(x, y, label, fontsize=6.2, color=style.INK2, ha="center", va="bottom")
    ax.set_xlim(-0.95, 6.75)
    ax.set_ylim(-0.75, 1.45)
    return a + b + cin, s, cout


def make():
    style.use()
    fig = plt.figure(figsize=(style.DOUBLE, 3.0))
    src = fig.add_axes([0.0, 0.0, 0.37, 0.93])
    src.axis("off")
    src.text(0.0, 1.0, SOURCE, family="monospace", fontsize=5.9, va="top", ha="left",
             color=style.INK, linespacing=1.32)
    style.panel(src, "a", x=0.0, y=1.02)

    ax1 = fig.add_axes([0.42, 0.52, 0.58, 0.41])
    ax1.axis("off")
    half_adder(ax1, {"a": 1, "b": 1})
    ax1.set_title("      half_add cells, a = b = +1:  2 = (−1) + 3·(+1)", loc="left", fontsize=7.5)
    style.panel(ax1, "b", x=-0.03, y=1.0)

    ax2 = fig.add_axes([0.42, 0.06, 0.58, 0.36])
    ax2.axis("off")
    total, s, c = full_adder(ax2, 1, 1, 0)
    ax2.set_title(f"      full_add = 11 NANY + 5 INV, a = b = +1, cin = 0:  {total} = ({tstr(s)}) + 3·({tstr(c)})",
                  loc="left", fontsize=7.5)
    style.panel(ax2, "c", x=-0.03, y=1.0)

    keys = [Line2D([], [], color=style.TRIT_COLOR[t], lw=1.6, label=f"net at {tstr(t)}") for t in (-1, 0, 1)]
    fig.legend(handles=keys, loc="lower left", bbox_to_anchor=(0.0, 0.0), ncol=3, handlelength=1.5,
               columnspacing=0.9)
    return style.save(fig, "fig_synth")


if __name__ == "__main__":
    print(make())
