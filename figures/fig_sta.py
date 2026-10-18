"""Fig. 10 — ternary static timing estimate vs. post-layout SPICE (same input transitions)."""

import matplotlib.pyplot as plt
import numpy as np

import data
import style

GROUP_COLOR = {"scaling": style.BLUE, "example": style.ORANGE}


def make():
    style.use()
    d = data.load("results/sta/validation.json")
    fig, ax = plt.subplots(figsize=(style.SINGLE, 2.9))
    lim = 0
    for group in d["designs"]:
        for o in group["outputs"]:
            sim = o["simulated_s"] * 1e9
            pred = o["tested_predicted_s"] * 1e9
            lim = max(lim, sim, pred)
            ax.plot(sim, pred, "o", ms=3.6, color=GROUP_COLOR.get(group["group"], style.INK2),
                    mec="white", mew=0.4, zorder=3)
    lim *= 1.08
    x = np.array([0, lim])
    ax.fill_between(x, 0.8 * x, 1.2 * x, color=style.BAND, lw=0, zorder=0)
    ax.plot(x, x, color=style.INK2, lw=0.7)
    ax.text(lim * 0.97, lim * 0.97 * 0.8 - lim * 0.02, "±20 %", ha="right", va="top", fontsize=6.5,
            color=style.INK2)
    s = d["statistics"]["sim_endpoint_pairs"]
    ax.text(0.04, 0.96, f"{d['outputs_within_target']} of {s['count']} outputs within ±20 %\n"
            f"mean |error| {s['mean_absolute_percent_error']:.1f} %", transform=ax.transAxes,
            va="top", fontsize=7)
    for g, c in GROUP_COLOR.items():
        ax.plot([], [], "o", ms=3.6, color=c, label={"scaling": "adders N = 1…6",
                                                       "example": "examples"}[g])
    ax.legend(loc="lower right", handletextpad=0.2)
    ax.set_xlim(0, lim)
    ax.set_ylim(0, lim)
    ax.set_aspect("equal")
    ax.set_xlabel("Post-layout SPICE settling (ns)")
    ax.set_ylabel("Static timing estimate (ns)")
    return style.save(fig, "fig_sta")


if __name__ == "__main__":
    print(make())
