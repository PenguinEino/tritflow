"""Chapter 2 views: the ternary INV redrawn small, its DC transfer, and the sizing explorer.

The INV is PMOS–RR–Y–RR–NMOS in series between VDD and VSS (VMID unused). Each view draws
from SPICE results the reader's cell just produced, or from the recorded sizing grid that
``tritflow.sim.sizing.load_grid`` checks against the schematic, models and analysis code.
"""

from html import escape
import json

from IPython.display import HTML, display

from live import FONT, DIM

ON, OFF, INK = "#e8782a", "#b4b9c1", "#30353b"
TRIT_TEXT = {-1: "−1", 0: "0", 1: "+1"}
_VIEWS = 0


def _key(prefix):
    global _VIEWS
    _VIEWS += 1
    return f"{prefix}{_VIEWS}"


def _mos(x, top, kind, on, label):
    """A MOS drawn vertically: drain/source stubs, channel, gate (bubble for PMOS)."""
    color, width = (ON, 2.6) if on else (OFF, 1.4)
    bottom = top+40
    gate_x = x-22 if kind == "P" else x-16
    parts = [
        f'<path d="M{x},{top-10} V{top+5} H{x-10} M{x-10},{bottom-5} H{x} V{bottom+10}" stroke="{color}" stroke-width="{width}" fill="none"/>',
        f'<path d="M{x-10},{top} V{bottom}" stroke="{color}" stroke-width="{width+1}"/>',
        f'<path d="M{x-16},{top+4} V{bottom-4}" stroke="{INK}" stroke-width="1.6"/>',
    ]
    if kind == "P":
        parts.append(f'<circle cx="{x-19}" cy="{top+20}" r="3" fill="white" stroke="{INK}" stroke-width="1.4"/>')
    parts.append(f'<path d="M{gate_x},{top+20} H{x-78}" stroke="{INK}" stroke-width="1.4"/>')
    parts.append(f'<text x="{x+10}" y="{top+16}" font-size="12" fill="{INK}">{escape(label)}</text>')
    parts.append(f'<text x="{x+10}" y="{top+32}" font-size="11" fill="{ON if on else DIM}">{"オン" if on else "オフ"}</text>')
    return "".join(parts)


def _resistor(x, top, on, label):
    color, width = (ON, 2.4) if on else (OFF, 1.4)
    zig = " ".join(f"L{x+(8 if k % 2 else -8)},{top+8+k*6}" for k in range(7))
    return (f'<path d="M{x},{top} V{top+5} {zig} L{x},{top+50} V{top+56}" stroke="{color}" stroke-width="{width}" fill="none"/>'
            f'<text x="{x+14}" y="{top+32}" font-size="12" fill="{INK}">{escape(label)}</text>')


def _inverter_svg(trit, dc, dimensions):
    """INV at input ``trit``: conducting devices and the current path in orange."""
    up, down = trit in (-1, 0), trit in (0, 1)
    x = 170
    mp, mn, rp = dimensions["MP"], dimensions["MN"], dimensions["RP"]
    y_volts = dc["output_v"]["Y"]
    current = abs(dc["rail_current_a"]["VDD"])
    a_volts = {-1: "−5 V", 0: "0 V", 1: "+5 V"}[trit]
    rails = [
        f'<path d="M{x-40},20 H{x+40}" stroke="{INK}" stroke-width="2"/><text x="{x+46}" y="22" font-size="12" fill="{INK}">VDD +5 V</text>',
        f'<path d="M{x-40},392 H{x+40}" stroke="{INK}" stroke-width="2"/><text x="{x+46}" y="396" font-size="12" fill="{INK}">VSS −5 V</text>',
    ]
    body = [
        *rails,
        _mos(x, 40, "P", up, f"MP {mp['w_um']:g}/{mp['l_um']:g} µm"),
        _resistor(x, 90, up, f"RP {rp['l_um']:g} µm"),
        f'<path d="M{x},146 V206" stroke="{ON if up else OFF}" stroke-width="{2.4 if up else 1.4}"/>',
        f'<path d="M{x},206 V266" stroke="{ON if down else OFF}" stroke-width="{2.4 if down else 1.4}"/>',
        _resistor(x, 266, down, f"RN {dimensions['RN']['l_um']:g} µm"),
        _mos(x, 332, "N", down, f"MN {mn['w_um']:g}/{mn['l_um']:g} µm"),
        f'<circle cx="{x}" cy="206" r="3.5" fill="{INK}"/><path d="M{x},206 H{x+64}" stroke="{INK}" stroke-width="1.6"/>',
        f'<text x="{x+70}" y="210" font-size="13" font-weight="700" fill="{INK}">Y = {y_volts:+.2f} V</text>',
        f'<path d="M{x-78},60 V352" stroke="{INK}" stroke-width="1.4"/><circle cx="{x-78}" cy="206" r="3.5" fill="{INK}"/>',
        f'<path d="M30,206 H{x-78}" stroke="{INK}" stroke-width="1.6"/>',
        f'<text x="18" y="196" font-size="13" font-weight="700" fill="{INK}">A = {a_volts}</text>',
        f'<text x="{x+46}" y="38" font-size="12" fill="{ON if current > 1e-6 else DIM}">I = {current*1e3:.3f} mA</text>',
    ]
    return (f'<svg viewBox="0 0 330 410" width="330" height="410" style="background:#fff;font-family:inherit">'
            + "".join(body) + "</svg>")


def inverter(spice, hand):
    """Input buttons (−1/0/+1) over the redrawn INV; the DC transfer with the hand estimate."""
    import plotly.graph_objects as go
    from tritflow import PASS_BAND

    key = _key("tfinv")
    row = spice["rows"][0]
    dimensions = row["dimensions"]
    dc = {r["input_trits"][0]: r for r in row["dc"]}
    data = row["transfer"]["data"]
    figure = go.Figure()
    for volts in (-5, 0, 5):
        figure.add_hrect(y0=volts-PASS_BAND, y1=volts+PASS_BAND, fillcolor="#6eae89", opacity=.15, line_width=0)
    figure.add_trace(go.Scatter(x=data["v-sweep"], y=data["v(Y)"], mode="lines", name="SPICE",
                                line={"color": "#1f5fa8", "width": 2}))
    figure.add_trace(go.Scatter(x=[0], y=[hand["output_v"]], mode="markers", name="手計算（入力 0 V）",
                                marker={"symbol": "x", "size": 11, "color": ON}))
    figure.update_layout(template="plotly_white", height=380, width=520, margin={"t": 40, "l": 55, "r": 10, "b": 45},
                         title="DC伝達特性", xaxis_title="A (V)", yaxis_title="Y (V)",
                         legend={"orientation": "h", "y": -.22}, yaxis={"tickvals": [-5, 0, 5]},
                         xaxis={"tickvals": [-5, 0, 5]})
    plot = figure.to_html(include_plotlyjs="cdn", full_html=False, config={"displaylogo": False})
    radios, panels, rules = [], [], []
    for index, trit in enumerate((-1, 0, 1)):
        radios.append(f'<input type="radio" name="{key}" id="{key}-{index}"{" checked" if trit == 0 else ""}>'
                      f'<label for="{key}-{index}">A = {TRIT_TEXT[trit]}</label>')
        panels.append(f'<div class="p{index}">{_inverter_svg(trit, dc[trit], dimensions)}</div>')
        rules.append(f"#{key}-{index}:checked ~ .row .p{index}{{display:block}}")
    style = (f".{key}{{max-width:1000px}} .{key} input{{display:none}}"
             f".{key} label{{display:inline-block;padding:.3em 1em;margin:0 .35em .5em 0;border:1px solid #c9ccd1;"
             f"border-radius:4px;cursor:pointer;font-size:14px}}"
             f".{key} input:checked + label{{background:{ON};color:#fff;border-color:{ON}}}"
             f".{key} .row{{display:flex;flex-wrap:wrap;gap:1.5em;align-items:center}}"
             f".{key} .row > .sch > div{{display:none}}" + "".join(rules))
    display(HTML(f'<style>{style}</style><div class="{key}" style="{FONT}">{"".join(radios)}'
                 f'<div class="row"><div class="sch">{"".join(panels)}</div><div>{plot}</div></div></div>'))


def sizing_explorer(grid):
    """Sliders over the recorded sizing grid: the selected transfer against the taped-out one,
    and where the selection sits among all candidates in level error versus static current."""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    from tritflow import PASS_BAND

    key = _key("tfsize")
    axes = grid["grid_axes"]
    rows = grid["rows"]
    adopted = rows[grid["adopted_index"]]

    def index_of(row):
        d = row["dimensions"]
        return "|".join(f"{v:g}" for v in (d["MP"]["w_um"], d["MN"]["w_um"], d["MP"]["l_um"], d["RP"]["l_um"]))

    curves = {index_of(r): {"x": [round(v, 3) for v in r["transfer"]["data"]["v-sweep"]],
                            "y": [round(v, 4) for v in r["transfer"]["data"]["v(Y)"]],
                            "err": r["max_error_v"]*1e3, "cur": r["max_static_current_a"]*1e6,
                            "ok": r["passed"]} for r in rows if not r.get("error")}
    figure = make_subplots(rows=1, cols=2, column_widths=[.55, .45], horizontal_spacing=.12,
                           subplot_titles=("DC伝達特性", "全候補：誤差と静的電流"))
    for volts in (-5, 0, 5):
        figure.add_hrect(y0=volts-PASS_BAND, y1=volts+PASS_BAND, fillcolor="#6eae89", opacity=.15,
                         line_width=0, row=1, col=1, exclude_empty_subplots=False)
    a = curves[index_of(adopted)]
    figure.add_trace(go.Scatter(x=a["x"], y=a["y"], name="テープアウトした寸法", mode="lines",
                                line={"color": "#9aa1ab", "dash": "dash", "width": 1.6}), row=1, col=1)
    figure.add_trace(go.Scatter(x=a["x"], y=a["y"], name="選んだ寸法", mode="lines",
                                line={"color": ON, "width": 2.4}), row=1, col=1)
    figure.add_trace(go.Scatter(x=[c["cur"] for c in curves.values()], y=[c["err"] for c in curves.values()],
                                mode="markers", name="候補", marker={"color": "#9aa1ab", "size": 6}), row=1, col=2)
    figure.add_trace(go.Scatter(x=[a["cur"]], y=[a["err"]], mode="markers", name="テープアウトした寸法",
                                marker={"symbol": "circle-open", "size": 14, "color": "#1f5fa8", "line": {"width": 2}},
                                showlegend=False), row=1, col=2)
    figure.add_trace(go.Scatter(x=[a["cur"]], y=[a["err"]], mode="markers", name="選んだ寸法", showlegend=False,
                                marker={"size": 11, "color": ON}), row=1, col=2)
    figure.update_xaxes(title_text="A (V)", tickvals=[-5, 0, 5], row=1, col=1)
    figure.update_yaxes(title_text="Y (V)", tickvals=[-5, 0, 5], row=1, col=1)
    figure.update_xaxes(title_text="最大静的電流 (µA)", row=1, col=2)
    figure.update_yaxes(title_text="最大レベル誤差 (mV)", row=1, col=2)
    figure.update_layout(template="plotly_white", height=420, margin={"t": 50, "l": 55, "r": 15, "b": 50},
                         legend={"orientation": "h", "y": -.2})
    plot = figure.to_html(include_plotlyjs="cdn", full_html=False, div_id=f"{key}-plot",
                          config={"displaylogo": False})
    base = adopted["dimensions"]
    sliders = [("wp", "MPの幅 W (µm)", axes["mp_w_um"], base["MP"]["w_um"]),
               ("wn", "MNの幅 W (µm)", axes["mn_w_um"], base["MN"]["w_um"]),
               ("l", "MOSの長さ L (µm)", axes["mos_l_um"], base["MP"]["l_um"]),
               ("r", "抵抗の長さ (µm)", axes["rr_l_um"], base["RP"]["l_um"])]
    controls = "".join(
        f'<label class="s">{escape(text)} <b data-out="{name}">{start:g}</b><br>'
        f'<input type="range" data-name="{name}" min="0" max="{len(values)-1}" step="1" '
        f'value="{values.index(start)}" data-values="{escape(json.dumps(values))}"></label>'
        for name, text, values, start in sliders)
    script = (f"<script>(function(){{var root=document.querySelector('.{key}'),curves={json.dumps(curves)};"
              "function update(){var v={};root.querySelectorAll('input[type=range]').forEach(function(s){"
              "var vals=JSON.parse(s.dataset.values),x=vals[+s.value];v[s.dataset.name]=x;"
              "root.querySelector('[data-out='+s.dataset.name+']').textContent=x;});"
              "var c=curves[[v.wp,v.wn,v.l,v.r].join('|')],out=root.querySelector('.read');"
              "if(!c){out.textContent='この組合せはSPICEが収束しなかった';return;}"
              f"var d=document.getElementById('{key}-plot');if(window.Plotly&&d){{"
              "Plotly.restyle(d,{x:[c.x],y:[c.y]},[1]);Plotly.restyle(d,{x:[[c.cur]],y:[[c.err]]},[4]);}"
              "out.textContent='最大レベル誤差 '+c.err.toFixed(1)+' mV · 最大静的電流 '+c.cur.toFixed(0)+' µA · '"
              "+(c.ok?'±0.5 Vの帯に入る':'帯から外れる');}"
              "root.querySelectorAll('input[type=range]').forEach(function(s){s.addEventListener('input',update);});"
              "update();})();</script>")
    style = (f".{key}{{max-width:1000px}} .{key} .ctl{{display:flex;flex-wrap:wrap;gap:.6em 2em;margin:.3em 0 .6em}}"
             f".{key} .s{{font-size:13px}} .{key} .s input{{width:210px}} .{key} .read{{font-size:14px;margin:.2em 0}}")
    display(HTML(f'<style>{style}</style><div class="{key}" style="{FONT}"><div class="ctl">{controls}</div>'
                 f'<div class="read"></div>{plot}</div>{script}'))


def hand_estimate(hand):
    """The divider estimate at input 0 V as a small table of its terms."""
    cells = [("R<sub>u</sub> = r<sub>on,P</sub> + R<sub>RP</sub>", hand["upper"]),
             ("R<sub>d</sub> = r<sub>on,N</sub> + R<sub>RN</sub>", hand["lower"])]
    body = "".join(f"<tr><td>{name}</td><td>{b['ron_ohm']/1e3:.3f} kΩ + {b['rr_ohm']/1e3:.3f} kΩ</td>"
                   f"<td><b>{b['total_ohm']/1e3:.3f} kΩ</b></td></tr>" for name, b in cells)
    body += (f'<tr><td>V<sub>Y</sub></td><td colspan="2"><b>{hand["output_v"]:+.3f} V</b></td></tr>'
             f'<tr><td>I</td><td colspan="2"><b>{hand["current_a"]*1e3:.3f} mA</b></td></tr>')
    display(HTML(f'<table style="{FONT};border-collapse:collapse" cellpadding="5" border="1" '
                 f'bordercolor="#d5d7db">{body}</table>'))
