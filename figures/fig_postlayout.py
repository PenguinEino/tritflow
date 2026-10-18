"""Fig. 8 — full adder, all 27 inputs: extracted devices without vs with wire C, and the load at which it fails."""

import json

import matplotlib.pyplot as plt
import numpy as np

from tritflow import ROOT

import data
import style

DIR = ROOT / "build/full_add/postlayout"


def wave(kind):
    z = np.load(DIR / kind / "waveforms.npz")
    return {k: z[k] for k in z.files}


def make():
    style.use()
    pre, post = wave("pre"), wave("post")
    meas_pre = json.loads((DIR / "pre/measurements.json").read_text())
    meas_post = json.loads((DIR / "post/measurements.json").read_text())
    summary = json.loads((DIR / "summary.json").read_text())
    hold = summary["hold_s"]
    load = data.load("results/full_add_load_sweep.json")

    fig = plt.figure(figsize=(style.DOUBLE, 3.6))
    gs = fig.add_gridspec(3, 2, width_ratios=[2.15, 1], height_ratios=[0.8, 1, 1],
                          hspace=0.18, wspace=0.28)
    ain = fig.add_subplot(gs[0, 0])
    asum = fig.add_subplot(gs[1, 0], sharex=ain)
    acout = fig.add_subplot(gs[2, 0], sharex=ain)
    right = gs[:, 1].subgridspec(2, 1, height_ratios=[1.75, 1], hspace=0.42)
    azoom = fig.add_subplot(right[0])
    aload = fig.add_subplot(right[1])

    t = pre["time"] * 1e6
    for name, off in (("a", 2), ("b", 1), ("cin", 0)):
        v = pre[f"v({name})"] / 5.0
        ain.plot(t, v * 0.36 + off, color=style.INK2, lw=0.8)
        ain.text(-0.15, off, name, ha="right", va="center", fontsize=7)
    ain.set_yticks([])
    ain.set_ylim(-0.6, 2.6)
    ain.grid(False)
    ain.spines["left"].set_visible(False)
    ain.set_title("inputs: all 27 (a, b, cin) combinations, 500 ns each", loc="left", fontsize=7.5)
    plt.setp(ain.get_xticklabels(), visible=False)

    for ax, out in ((asum, "sum"), (acout, "cout")):
        style.bands(ax)
        ax.plot(t, pre[f"v({out})"], color=style.BLUE, lw=0.9, label="extracted devices")
        ax.plot(post["time"] * 1e6, post[f"v({out})"], color=style.ORANGE, lw=0.9,
                ls=(0, (3, 1.5)), label="+ wire C")
        ax.set_ylabel(f"$V_{{\\mathrm{{{out}}}}}$ (V)")
        ax.set_yticks([-5, 0, 5])
        ax.set_ylim(-6, 6)
    plt.setp(asum.get_xticklabels(), visible=False)
    acout.set_xlabel("Time (µs)")
    acout.set_xlim(0, t[-1])

    # zoom on the slowest sum transition (post-layout)
    rows = meas_post["rows"]
    k = max(range(1, len(rows)), key=lambda i: rows[i]["outputs"]["sum"]["settling_s"] or 0)
    t0 = k * hold
    for w, color, ls, meas, lab in ((pre, style.BLUE, "-", meas_pre, "devices only"),
                                    (post, style.ORANGE, (0, (3, 1.5)), meas_post, "+ wire C")):
        tt = (w["time"] - t0) * 1e9
        sel = (tt > -20) & (tt < 200)
        azoom.plot(tt[sel], w["v(sum)"][sel], color=color, lw=1.1, ls=ls)
        ts = meas["rows"][k]["outputs"]["sum"]["settling_s"] * 1e9
        azoom.axvline(ts, color=color, lw=0.7, ls=":")
        azoom.text(114, -3.4 if color == style.BLUE else -4.7, f"{lab}: {ts:.0f} ns", color=color,
                   fontsize=6.5, va="center", ha="left")
    ideal = rows[k]["outputs"]["sum"]["ideal_voltage_v"]
    azoom.axhspan(ideal - 0.5, ideal + 0.5, color=style.BAND, lw=0)
    prev, cur = rows[k]["previous_trits"], rows[k]["input_trits"]
    azoom.set_title(f"slowest sum step, (a,b,cin) {tuple(prev)} → {tuple(cur)}".replace("-1", "−1"),
                    loc="left", fontsize=7)
    from matplotlib.lines import Line2D
    azoom.legend(handles=[Line2D([], [], color=style.BLUE, lw=1.1, label="extracted devices"),
                          Line2D([], [], color=style.ORANGE, lw=1.1, ls=(0, (3, 1.5)),
                                 label="devices + wire C")],
                 loc="center right", fontsize=6.5, handlelength=1.8)
    azoom.set_xlabel("Time from input step (ns)")
    azoom.set_ylabel("$V_{\\mathrm{sum}}$ (V)")
    azoom.set_xlim(-20, 200)
    azoom.set_ylim(-5.8, 5.8)
    azoom.set_yticks([-5, 0, 5])

    xs, ys_s, ys_c, ok = [], [], [], []
    for r in load["rows"]:
        xs.append(r["load_f"] * 1e12)
        ys_s.append((r["max_settling_s"] or {}).get("sum"))
        ys_c.append((r["max_settling_s"] or {}).get("cout"))
        ok.append(r["passed"])
    order = np.argsort(xs)
    xs = np.array(xs)[order]
    ok = np.array(ok)[order]
    for ys, color, lab in ((ys_s, style.BLUE, "sum"), (ys_c, style.AQUA, "cout")):
        ys = [ys[i] for i in order]
        px = [x for x, y, g in zip(xs, ys, ok) if y is not None and g]
        py = [y * 1e9 for y, g in zip(ys, ok) if y is not None and g]
        aload.plot(px, py, "o-", color=color, ms=3, lw=0.9, label=lab)
    aload.axhline(hold * 1e9, color=style.INK2, lw=0.7, ls=(0, (3, 2)))
    aload.text(xs[0], hold * 1e9 * 1.06, "500 ns hold window", fontsize=6.5, color=style.INK2,
               va="bottom")
    b = load.get("boundary") or {}
    fail = b.get("first_fail_f") or b.get("fail_f")
    if fail:
        aload.axvspan(fail * 1e12, xs[-1] * 1.5, color="#f7d3d2", lw=0, zorder=0)
        aload.text(fail * 1e12 * 1.08, hold * 1e9 * 0.55, "not settled\nin 500 ns", fontsize=6.5,
                   color=style.TRIT_COLOR[1], ha="left")
        aload.text(fail * 1e12 * 0.9, 40, f"limit ≈ {b['last_pass_f'] * 1e12:.1f} pF", ha="right",
                   fontsize=6.5, color=style.INK)
        aload.set_xlim(xs[0] * 0.7, xs[-1] * 1.5)
    aload.set_xscale("log")
    aload.set_xlabel("Output load (pF)")
    aload.set_ylabel("Worst settling (ns)")
    aload.set_ylim(0, hold * 1e9 * 1.25)
    aload.legend(loc="center left", fontsize=6.5, handlelength=1.2)

    style.panel(ain, "a", x=-0.07, y=1.0)
    style.panel(azoom, "b", x=-0.24, y=1.0)
    style.panel(aload, "c", x=-0.24, y=1.0)
    return style.save(fig, "fig_postlayout")


if __name__ == "__main__":
    print(make())
