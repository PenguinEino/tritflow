"""One look for every figure, table and control in the notebook, matching the paper figures.

The palette and serif face are those of ``figures/paperstyle.py`` and the schematic renderer
(``tritflow.schematic.vector``): near-black ink, a warm grey for secondary text and rules, the
diverging trit colours (−1 blue, 0 grey, +1 red), and one accent for "the selected thing".
Tables are drawn booktabs-style (three horizontal rules, no vertical lines). Command-line style
progress lines (``live.step``) stay monospace on purpose: they are logs, not figures.
"""

INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
RULE, GRID, BAND = "#c3c2b7", "#e1e0d9", "#ecebe6"
TRIT_COLOR = {-1: "#2a78d6", 0: "#6f6e69", 1: "#e34948"}
TRIT_FILL = {-1: "#cde2fb", 0: "#ecebe6", 1: "#f7d3d2"}
ACCENT = "#eb6834"
# Signal lanes in waveforms: inputs, then outputs (the paper figures' categorical colours).
INPUT_COLORS = ("#1baf7a", "#7b61c9", "#b8860b")
OUTPUT_COLORS = ("#2a78d6", "#d6336c", "#0f8b8d")
CURRENT_COLOR = "#52514e"
SERIF = ('"Times New Roman", Times, "Nimbus Roman", "Liberation Serif", "Noto Serif JP", '
         '"Noto Serif CJK JP", "Hiragino Mincho ProN", "Yu Mincho", serif')
TRIT_TEXT = {-1: "−1", 0: "0", 1: "+1"}


def figure_css(scope):
    """Base text of a figure block: serif, ink, no decoration."""
    return f"{scope}{{font-family:{SERIF};color:{INK};font-size:14px;line-height:1.45}}"


def table_css(scope):
    """Booktabs tables under ``scope``: rules above and below, a thin rule under the header,
    trit values in their colours, the marked row tinted with the accent."""
    return (f"{scope} table{{border-collapse:collapse;font-family:{SERIF};font-size:14px;"
            f"border-top:1.4px solid {INK};border-bottom:1.4px solid {INK}}}"
            f"{scope} th{{font-weight:600;padding:.25em .75em;text-align:center}}"
            f"{scope} tr:first-child th{{border-bottom:.8px solid {INK}}}"
            f"{scope} td{{padding:.2em .75em;text-align:center}}"
            f"{scope} th small{{display:block;font-size:11px;font-weight:400;color:{MUTED}}}"
            f"{scope} td.t0{{color:{TRIT_COLOR[-1]}}} {scope} td.t1{{color:{TRIT_COLOR[0]}}}"
            f"{scope} td.t2{{color:{TRIT_COLOR[1]}}}"
            f"{scope} tr.on td{{background:{ACCENT}1f;font-weight:700}}")


def control_style(scope):
    """Radio-button labels and range sliders under ``scope``: thin rules, the selected choice in
    ink, like the controls of a figure rather than an app."""
    return (f"{scope} input[type=radio]{{position:absolute;opacity:0;width:1px;height:1px;clip-path:inset(50%)}}"
            f"{scope} input[type=radio] + label{{display:inline-block;padding:.1em .8em;margin:0 -1px .5em 0;"
            f"border:1px solid {RULE};cursor:pointer;font-family:{SERIF};font-size:14px;color:{INK};background:#fff}}"
            f"{scope} input[type=radio]:checked + label{{background:{INK};border-color:{INK};color:#fff}}"
            f"{scope} input[type=radio]:focus-visible + label{{outline:1px solid {INK};outline-offset:2px}}"
            # A slider reads as one only with a visible groove and a grabbable knob: a 4 px
            # rounded track and a 16 px knob with a white ring, accented while hovered or dragged.
            f"{scope} input[type=range]{{-webkit-appearance:none;appearance:none;width:100%;height:20px;"
            f"background:transparent;margin:.3em 0;cursor:pointer}}"
            f"{scope} input[type=range]::-webkit-slider-runnable-track{{height:4px;border-radius:2px;background:{RULE}}}"
            f"{scope} input[type=range]::-moz-range-track{{height:4px;border-radius:2px;background:{RULE}}}"
            f"{scope} input[type=range]::-webkit-slider-thumb{{-webkit-appearance:none;box-sizing:border-box;width:16px;height:16px;"
            f"margin-top:-6px;border-radius:50%;background:{INK};border:2px solid #fff;box-shadow:0 0 0 1px {INK2},0 1px 3px rgba(0,0,0,.35)}}"
            f"{scope} input[type=range]::-moz-range-thumb{{box-sizing:border-box;width:16px;height:16px;border-radius:50%;background:{INK};"
            f"border:2px solid #fff;box-shadow:0 0 0 1px {INK2},0 1px 3px rgba(0,0,0,.35)}}"
            f"{scope} input[type=range]:hover::-webkit-slider-thumb,{scope} input[type=range]:active::-webkit-slider-thumb"
            f"{{background:{ACCENT}}}"
            f"{scope} input[type=range]:hover::-moz-range-thumb,{scope} input[type=range]:active::-moz-range-thumb"
            f"{{background:{ACCENT}}}"
            f"{scope} input[type=range]:focus-visible{{outline:1px solid {INK};outline-offset:2px}}")


def paper_layout(**extra):
    """Plotly layout for figures in the paper's style: serif, ink axes with outward ticks, light
    grid, white background."""
    axis = {"showline": True, "linecolor": INK2, "linewidth": 1, "mirror": True, "ticks": "outside",
            "tickcolor": INK2, "ticklen": 4, "gridcolor": GRID, "zeroline": False,
            "title": {"font": {"size": 14}}}
    layout = {"template": "none", "paper_bgcolor": "white", "plot_bgcolor": "white",
              "font": {"family": SERIF, "size": 13, "color": INK}, "xaxis": axis, "yaxis": dict(axis),
              "legend": {"bgcolor": "rgba(0,0,0,0)", "font": {"size": 13}}, "hoverlabel": {"font": {"family": SERIF}},
              "margin": {"t": 20, "l": 60, "r": 15, "b": 50}}
    layout.update(extra)
    return layout


def paper_axes(figure):
    """Apply the paper axis style to every axis of a figure with subplots."""
    axis = paper_layout()["xaxis"]
    figure.update_xaxes(**axis)
    figure.update_yaxes(**axis)
    return figure
