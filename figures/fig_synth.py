"""Fig. 6 — Source and adder cells, with settled trits on orthogonal nets.

The half adder has a fixed, logic-level grid. Its four exterior ports require
one crossover (the exterior-vertex augmentation is nonplanar); a gap in the
vertical a branch distinguishes it from the continuous b net. All other nets
are disjoint except at explicitly dotted branches of the same signal.
"""

from collections import Counter

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch

from tritflow import flow
from tritflow.synth.simulate import evaluate_netlist

import data
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
  half_add ha1 (.a(a), .b(b),
                .sum(s1), .carry(c1));
  half_add ha2 (.a(s1), .b(cin),
                .sum(sum), .carry(c2));
  nany g_nc (nc, c1, c2);
  inv  g_cout (cout, nc);
endmodule"""

# Both diagrams share port columns. Gate columns advance one logic level.
INPUT_X, OUTPUT_X = 0.0, 12.1
GATE_W, GATE_H, PIN_DY = 1.24, 0.88, 0.22
CELL_FONT, MIN_PADDING_EM = 6.2, 0.6
HALF_GRID = {
    "g_t": (1, 0), "g_na": (1, 1), "g_u": (2, 0),
    "g_c": (3, 0), "g_d": (4, 0), "g_nd": (5, 0), "g_s": (6, 0),
}


def grid(column, row):
    """Shared column/row pitch for primitive gates and hierarchy blocks."""
    return 1.65 + 1.75 * (column - 1), 1.6 * row


def tstr(value):
    return {-1: "−1", 0: "0", 1: "+1"}[int(value)]


def circuits():
    """Read the actual HDL through data.py, including FIG_REF snapshots.

    Counts come from these mapped circuits, so the figure needs no prebuilt
    build/ report and cannot silently retain a stale hard-coded cell count.
    """
    half_source = data.text("examples/half_add.tv")
    full_source = data.text("examples/full_add.tv").replace(
        '`include "half_add.tv"', half_source)
    half = flow.loads(half_source, "half_add").synthesize()
    full = flow.loads(full_source, "full_add").synthesize()
    return half, full


def wire(ax, points, value):
    """Draw one continuous Manhattan run; branches are separate runs."""
    if any(x0 != x1 and y0 != y1 for (x0, y0), (x1, y1) in zip(points, points[1:])):
        raise ValueError("adder figure wires must be orthogonal")
    x, y = zip(*points)
    ax.plot(x, y, color=style.TRIT_COLOR[int(value)], lw=1.1,
            solid_capstyle="butt", solid_joinstyle="miter", zorder=1)


def junction(ax, xy, value):
    ax.plot(*xy, "o", color=style.TRIT_COLOR[int(value)], ms=2.8, mew=0, zorder=2)


def label(ax, xy, text, *, ha="center", va="bottom"):
    ax.text(*xy, text, ha=ha, va=va, fontsize=7, color=style.INK2, zorder=4)


def box(ax, xy, size, text, pins, *, fill="white"):
    """Cell box with distinct, named signal-pin landing points."""
    x, y = xy
    w, h = size
    instance = text.splitlines()[0].split(" / ")[0]
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                               boxstyle="round,pad=0,rounding_size=0.045",
                               fc=fill, ec=style.INK, lw=0.7, zorder=3,
                               gid=f"cell-box-{instance}"))
    ax.text(x, y, text, ha="center", va="center", fontsize=CELL_FONT,
            linespacing=1.2, color=style.INK, zorder=4, gid=f"cell-label-{instance}")
    for name, (px, py) in pins.items():
        left = px < x
        ax.plot([px - 0.07, px + 0.07], [py, py], color=style.INK, lw=0.6, zorder=4)
        if name == "Y" or (len(pins) == 2 and name == "A"):
            continue
        # Input names sit outside the box, clear of its two-line cell label.
        inside = name == "carry"
        ax.annotate(name, (px, py), xytext=(-3 if inside else -1.5 if left else 1.5,
                                          -3 if inside else 3),
                    textcoords="offset points", ha="right" if left or inside else "left",
                    va="top" if inside else "bottom", fontsize=6, color=style.INK2,
                    zorder=4, gid=f"pin-label-{instance}-{name}")


def check_label_padding(fig):
    """Require 0.6 em inside the border stroke around every central label."""
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    for ax in fig.axes:
        boxes = [p for p in ax.patches if (p.get_gid() or "").startswith("cell-box-")]
        labels = [t for t in ax.texts if (t.get_gid() or "").startswith("cell-label-")]
        for patch, text in zip(boxes, labels, strict=True):
            outer = patch.get_window_extent(renderer)
            inner = text.get_window_extent(renderer)
            stroke = patch.get_linewidth() * fig.dpi / 144
            padding = min(inner.x0 - outer.x0, outer.x1 - inner.x1,
                          inner.y0 - outer.y0, outer.y1 - inner.y1) - stroke
            required = MIN_PADDING_EM * text.get_fontsize() * fig.dpi / 72
            if padding < required:
                raise ValueError(f"Insufficient cell-label padding: {text.get_text()!r}")


def port(ax, name, y, value, *, output=False):
    x = OUTPUT_X if output else INPUT_X
    ax.annotate(f"{name} = {tstr(value)}", (x, y), xytext=(3 if output else -3, 0),
                textcoords="offset points", ha="left" if output else "right",
                va="center", fontsize=7, color=style.INK)


def half_adder(ax, net, vector):
    """Route the seven source instances; pin/net identity comes from synthesis."""
    instances = {inst.name: inst for inst in net.instances}
    if instances.keys() != HALF_GRID.keys():
        raise ValueError("half_add changed: review the figure's seven-cell grid")
    values = {name: int(value) for name, value in
              evaluate_netlist(net, vector, return_all=True).items()}
    centers = {name: grid(col, row) for name, (col, row) in HALF_GRID.items()}
    pins = {}
    for name, inst in instances.items():
        x, y = centers[name]
        # Swapping the drawn vertical pin order keeps each bypass on its side.
        order = {"A": -PIN_DY, "B": PIN_DY} if name in {"g_t", "g_d", "g_s"} else {
            "A": PIN_DY, "B": -PIN_DY}
        pins[name] = {p: (x - GATE_W / 2, y + (order[p] if inst.cell == "NANY" else 0))
                      for p in inst.pins if p != "Y"}
        pins[name]["Y"] = (x + GATE_W / 2, y)

    def run(driver, points):
        signal = vector[driver] if driver in vector else values[instances[driver].pins["Y"]]
        wire(ax, points, signal)

    # a branches to g_na and g_t. Only its vertical branch has a crossover gap.
    a_branch, b_branch, b_y = 0.35, 0.68, 0.64
    run("a", [(INPUT_X, 1.6), pins["g_na"]["A"]])
    run("a", [(a_branch, 1.6), (a_branch, b_y + 0.105)])
    run("a", [(a_branch, b_y - 0.105), (a_branch, -PIN_DY), pins["g_t"]["A"]])
    junction(ax, (a_branch, 1.6), values["a"])
    run("b", [(INPUT_X, b_y), (2.44, b_y), (2.44, PIN_DY), pins["g_u"]["A"]])
    run("b", [(b_branch, b_y), (b_branch, PIN_DY), pins["g_t"]["B"]])
    junction(ax, (b_branch, b_y), values["b"])

    run("g_t", [pins["g_t"]["Y"], (2.40, 0), (2.40, -1.0), (5.94, -1.0),
                (5.94, -PIN_DY), pins["g_d"]["A"]])
    run("g_t", [(2.40, -PIN_DY), pins["g_u"]["B"]])
    junction(ax, (2.40, -PIN_DY), values[instances["g_t"].pins["Y"]])
    run("g_na", [pins["g_na"]["Y"], (4.18, 1.6), (4.18, PIN_DY), pins["g_c"]["A"]])
    run("g_u", [pins["g_u"]["Y"], (4.14, 0), (4.14, -PIN_DY), pins["g_c"]["B"]])

    # carry leaves on a dedicated upper bus, with two dotted loads and the port.
    run("g_c", [pins["g_c"]["Y"], (5.94, 0), (5.94, PIN_DY), pins["g_d"]["B"]])
    run("g_c", [(5.94, PIN_DY), (5.94, 0.90), (OUTPUT_X, 0.90)])
    run("g_c", [(9.44, 0.90), (9.44, PIN_DY), pins["g_s"]["B"]])
    for xy in ((5.94, PIN_DY), (9.44, 0.90)):
        junction(ax, xy, values["carry"])
    run("g_d", [pins["g_d"]["Y"], pins["g_nd"]["A"]])
    run("g_nd", [pins["g_nd"]["Y"], (9.44, 0), (9.44, -PIN_DY), pins["g_s"]["A"]])
    run("g_s", [pins["g_s"]["Y"], (OUTPUT_X, 0)])

    for name, inst in instances.items():
        box(ax, centers[name], (GATE_W, GATE_H), f"{name}\n{inst.cell}", pins[name])
    for xy, text in (((3.3, 1.68), "na"), ((3.5, -0.93), "t"),
                     ((4.36, -0.68), "u"), ((7.75, 0.08), "d"),
                     ((9.52, -0.68), "nd")):
        label(ax, xy, text)
    port(ax, "a", 1.6, values["a"])
    port(ax, "b", b_y, values["b"])
    port(ax, "carry", 0.90, values["carry"], output=True)
    port(ax, "sum", 0, values["sum"], output=True)
    ax.set_ylim(-1.24, 2.16)
    return values


def cell_count(counts):
    return " + ".join(f"{counts[cell]} {cell}" for cell in ("NANY", "INV"))


def full_adder(ax, half, full, a, b, cin):
    """Two aligned half adders, a straight sum path and an upper carry merge."""
    first = {k: int(v) for k, v in evaluate_netlist(half, {"a": a, "b": b}).items()}
    second = {k: int(v) for k, v in evaluate_netlist(half, {"a": first["sum"], "b": cin}).items()}
    output = {k: int(v) for k, v in evaluate_netlist(full, {"a": a, "b": b, "cin": cin}).items()}
    s1, c1, c2 = first["sum"], first["carry"], second["carry"]
    nc = -output["cout"]
    hw, hh = 2.65, 1.70
    centers = {"ha1": grid(1, 0), "ha2": grid(3, 0),
               "g_nc": grid(5, 1), "g_cout": grid(6, 1)}
    hpins = {}
    for name in ("ha1", "ha2"):
        x, _ = centers[name]
        hpins[name] = {"a": (x - hw / 2, 0.0), "b": (x - hw / 2, -0.6),
                       "sum": (x + hw / 2, 0.0), "carry": (x + hw / 2, 0.7)}
    mx, my = centers["g_nc"]
    ix, iy = centers["g_cout"]
    merge = {"A": (mx - GATE_W / 2, my + PIN_DY),
             "B": (mx - GATE_W / 2, my - PIN_DY), "Y": (mx + GATE_W / 2, my)}
    inv = {"A": (ix - GATE_W / 2, iy), "Y": (ix + GATE_W / 2, iy)}
    wire(ax, [(INPUT_X, 0.0), hpins["ha1"]["a"]], a)
    wire(ax, [(INPUT_X, -0.6), hpins["ha1"]["b"]], b)
    wire(ax, [(INPUT_X, -1.15), (3.60, -1.15), (3.60, -0.6), hpins["ha2"]["b"]], cin)
    wire(ax, [hpins["ha1"]["sum"], hpins["ha2"]["a"]], s1)
    wire(ax, [hpins["ha2"]["sum"], (OUTPUT_X, 0.0)], output["sum"])
    wire(ax, [hpins["ha1"]["carry"], (3.20, 0.7), (3.20, my + PIN_DY), merge["A"]], c1)
    wire(ax, [hpins["ha2"]["carry"], (7.70, 0.7), (7.70, my - PIN_DY), merge["B"]], c2)
    wire(ax, [merge["Y"], inv["A"]], nc)
    wire(ax, [inv["Y"], (OUTPUT_X, iy)], output["cout"])
    counts = Counter(inst.cell for inst in half.instances)
    for name in ("ha1", "ha2"):
        box(ax, centers[name], (hw, hh), f"{name} / half_add\n{cell_count(counts)}",
            hpins[name], fill="#f6f5f1")
    box(ax, centers["g_nc"], (GATE_W, GATE_H), "g_nc\nNANY", merge)
    box(ax, centers["g_cout"], (GATE_W, GATE_H), "g_cout\nINV", inv)
    for xy, text in (((3.40, -0.35), "s1"), ((5.95, 1.90), "c1"),
                     ((7.95, 0.76), "c2"), ((9.55, 1.68), "nc")):
        label(ax, xy, text)
    for name, y, value in (("a", 0.0, a), ("b", -0.6, b), ("cin", -1.15, cin)):
        port(ax, name, y, value)
    port(ax, "sum", 0.0, output["sum"], output=True)
    port(ax, "cout", iy, output["cout"], output=True)
    ax.set_ylim(-1.24, 2.16)
    return output


def make():
    style.use()
    half, full = circuits()
    fig = plt.figure(figsize=(style.DOUBLE, 3.25))
    src = fig.add_axes([0.0, 0.08, 0.30, 0.85])
    src.axis("off")
    src.text(0, 1, SOURCE, family="monospace", fontsize=5.9, va="top", ha="left",
             color=style.INK, linespacing=1.32)
    style.panel(src, "a", x=0, y=1.035)

    ax1 = fig.add_axes([0.34, 0.55, 0.66, 0.38])
    ax2 = fig.add_axes([0.34, 0.08, 0.66, 0.38])
    for ax in (ax1, ax2):
        ax.axis("off")
        ax.set_xlim(-1.25, 14.25)
    half_values = half_adder(ax1, half, {"a": 1, "b": 1})
    ax1.set_title(f"half_add, a = b = +1:  2 = ({tstr(half_values['sum'])}) + 3·({tstr(half_values['carry'])})",
                  loc="left", fontsize=7.5, pad=6)
    style.panel(ax1, "b", x=-0.07, y=1.02)
    output = full_adder(ax2, half, full, 1, 1, 0)
    counts = Counter(inst.cell for inst in full.instances)
    ax2.set_title(f"full_add: {cell_count(counts)}\n"
                  f"a = b = +1, cin = 0:  2 = ({tstr(output['sum'])}) + 3·({tstr(output['cout'])})",
                  loc="left", fontsize=7.5, pad=6, linespacing=1.3)
    style.panel(ax2, "c", x=-0.07, y=1.085)

    keys = [Line2D([], [], color=style.TRIT_COLOR[t], lw=1.6, label=f"net at {tstr(t)}")
            for t in (-1, 0, 1)]
    fig.legend(handles=keys, loc="lower left", bbox_to_anchor=(0, 0), ncol=3,
               handlelength=1.5, columnspacing=0.9)
    check_label_padding(fig)
    return style.save(fig, "fig_synth")


if __name__ == "__main__":
    print(make())
