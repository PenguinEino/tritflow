"""Chapter 2 view: the ternary INV redrawn small, its DC transfer, and the sizing grid.

The INV is PMOS–RR–Y–RR–NMOS in series between VDD and VSS (VMID unused). The view draws the
taped-out size from the SPICE run the reader's cell just made, and every other size from the
recorded grid that ``tritflow.sim.sizing.load_grid`` checks against the schematic, models and
analysis code. Buttons and sliders work in the browser alone; no kernel callback is needed.
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


def _mos(x, top, kind, on, field):
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
    parts.append(f'<text x="{x+10}" y="{top+16}" font-size="12" fill="{INK}" data-f="{field}"></text>')
    parts.append(f'<text x="{x+10}" y="{top+32}" font-size="11" fill="{ON if on else DIM}">{"オン" if on else "オフ"}</text>')
    return "".join(parts)


def _resistor(x, top, on, field):
    color, width = (ON, 2.4) if on else (OFF, 1.4)
    zig = " ".join(f"L{x+(8 if k % 2 else -8)},{top+8+k*6}" for k in range(7))
    return (f'<path d="M{x},{top} V{top+5} {zig} L{x},{top+50} V{top+56}" stroke="{color}" stroke-width="{width}" fill="none"/>'
            f'<text x="{x+14}" y="{top+32}" font-size="12" fill="{INK}" data-f="{field}"></text>')


def _inverter_svg(trit):
    """INV at input ``trit``: conducting devices and the current path in orange. Sizes, Y and I
    are text fields the script fills for the selected size."""
    up, down = trit in (-1, 0), trit in (0, 1)
    x = 170
    a_volts = {-1: "−5 V", 0: "0 V", 1: "+5 V"}[trit]
    body = [
        f'<path d="M{x-40},20 H{x+40}" stroke="{INK}" stroke-width="2"/><text x="{x+46}" y="22" font-size="12" fill="{INK}">VDD +5 V</text>',
        f'<path d="M{x-40},392 H{x+40}" stroke="{INK}" stroke-width="2"/><text x="{x+46}" y="396" font-size="12" fill="{INK}">VSS −5 V</text>',
        _mos(x, 40, "P", up, "mp"),
        _resistor(x, 90, up, "rp"),
        f'<path d="M{x},146 V206" stroke="{ON if up else OFF}" stroke-width="{2.4 if up else 1.4}"/>',
        f'<path d="M{x},206 V266" stroke="{ON if down else OFF}" stroke-width="{2.4 if down else 1.4}"/>',
        _resistor(x, 266, down, "rn"),
        _mos(x, 332, "N", down, "mn"),
        f'<circle cx="{x}" cy="206" r="3.5" fill="{INK}"/><path d="M{x},206 H{x+64}" stroke="{INK}" stroke-width="1.6"/>',
        f'<text x="{x+70}" y="210" font-size="13" font-weight="700" fill="{INK}" data-f="y"></text>',
        f'<path d="M{x-78},60 V352" stroke="{INK}" stroke-width="1.4"/><circle cx="{x-78}" cy="206" r="3.5" fill="{INK}"/>',
        f'<path d="M30,206 H{x-78}" stroke="{INK}" stroke-width="1.6"/>',
        f'<text x="18" y="196" font-size="13" font-weight="700" fill="{INK}">A = {a_volts}</text>',
        f'<text x="{x+46}" y="38" font-size="12" fill="{ON if trit == 0 else DIM}" data-f="i"></text>',
    ]
    return f'<svg viewBox="0 0 330 410" width="330" height="410" style="background:#fff">{"".join(body)}</svg>'


def _candidate(row, transfer=None):
    """What the view needs from one simulated size: dimensions, curve, per-input Y and I."""
    d, data = row["dimensions"], (transfer or row["transfer"]["data"])
    dc = {r["input_trits"][0]: r for r in row["dc"]}
    return {"wp": d["MP"]["w_um"], "wn": d["MN"]["w_um"], "l": d["MP"]["l_um"], "r": d["RP"]["l_um"],
            "y": [round(v, 4) for v in data["v(Y)"]],
            "dc": {str(t): [dc[t]["output_v"]["Y"], abs(dc[t]["rail_current_a"]["VDD"])*1e6] for t in (-1, 0, 1)},
            "err": row["max_error_v"]*1e3, "cur": row["max_static_current_a"]*1e6, "ok": row["passed"]}


_SCRIPT = r"""
const root = document.querySelector('.KEY'), data = DATA, plot = () => document.getElementById('KEY-plot');
const main = root.querySelector('input[data-name=main]'), params = [...root.querySelectorAll('input[data-param]')];
let index = data.adopted, trit = 0;
function find(values) {
  return data.rows.findIndex(r => params.every((s, k) => r[s.dataset.param] === values[k]));
}
function draw() {
  const c = data.rows[index], [y, current] = c.dc[String(trit)];
  main.value = index;
  root.querySelector('[data-out=main]').textContent = (index + 1) + ' / ' + data.rows.length
    + (index === data.adopted ? '（テープアウトした寸法）' : '');
  params.forEach(s => { const vals = JSON.parse(s.dataset.values); s.value = vals.indexOf(c[s.dataset.param]);
    root.querySelector('[data-out=' + s.dataset.param + ']').textContent = c[s.dataset.param]; });
  root.querySelectorAll('[data-f=mp]').forEach(e => e.textContent = 'MP ' + c.wp + '/' + c.l + ' µm');
  root.querySelectorAll('[data-f=mn]').forEach(e => e.textContent = 'MN ' + c.wn + '/' + c.l + ' µm');
  root.querySelectorAll('[data-f=rp]').forEach(e => e.textContent = 'RP ' + c.r + ' µm');
  root.querySelectorAll('[data-f=rn]').forEach(e => e.textContent = 'RN ' + c.r + ' µm');
  root.querySelectorAll('[data-f=y]').forEach(e => e.textContent = 'Y = ' + (y >= 0 ? '+' : '') + y.toFixed(2) + ' V');
  root.querySelectorAll('[data-f=i]').forEach(e => e.textContent = 'I = ' + current.toFixed(0) + ' µA');
  root.querySelector('.read').textContent = '最大レベル誤差 ' + c.err.toFixed(1) + ' mV · 最大静的電流 '
    + c.cur.toFixed(0) + ' µA · ' + (c.ok ? '全入力で ±0.5 V の帯に入る' : '帯から外れる入力がある');
  const d = plot();
  if (window.Plotly && d) {
    Plotly.restyle(d, {y: [c.y]}, [1]);
    Plotly.restyle(d, {x: [[trit * 5]], y: [[y]]}, [2]);
    Plotly.restyle(d, {x: [[c.cur]], y: [[c.err]]}, [5]);
  }
}
main.addEventListener('input', () => { index = +main.value; draw(); });
params.forEach(s => s.addEventListener('input', () => {
  const values = params.map(p => JSON.parse(p.dataset.values)[+p.value]), found = find(values);
  if (found >= 0) { index = found; draw(); }
  else root.querySelector('.read').textContent = 'この組合せはSPICEが収束しなかった';
}));
root.querySelectorAll('input[name=KEY]').forEach(r => r.addEventListener('change', () => { trit = +r.dataset.t; draw(); }));
draw();
"""


def inverter(spice, grid):
    """The INV with input buttons, one slider over every simulated size (as in v1) and four
    linked sliders for the individual dimensions. The schematic labels, Y and I, the transfer
    curve, and the size's place among all candidates follow both."""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    from tritflow import PASS_BAND

    key = _key("tfinv")
    live = spice["rows"][0]
    rows = [r for r in grid["rows"] if not r.get("error")]
    adopted = next(i for i, r in enumerate(rows) if r["is_adopted"])
    candidates = [_candidate(r, live["transfer"]["data"] if r["is_adopted"] else None) for r in rows]
    sweep = [round(v, 3) for v in live["transfer"]["data"]["v-sweep"]]

    figure = make_subplots(rows=2, cols=1, row_heights=[.58, .42], vertical_spacing=.16,
                           subplot_titles=("DC伝達特性", "全候補：最大レベル誤差と最大静的電流"))
    for volts in (-5, 0, 5):
        figure.add_hrect(y0=volts-PASS_BAND, y1=volts+PASS_BAND, fillcolor="#6eae89", opacity=.15,
                         line_width=0, row=1, col=1, exclude_empty_subplots=False)
    taped = candidates[adopted]
    figure.add_trace(go.Scatter(x=sweep, y=taped["y"], name="テープアウトした寸法", mode="lines",
                                line={"color": "#9aa1ab", "dash": "dash", "width": 1.6}), row=1, col=1)
    figure.add_trace(go.Scatter(x=sweep, y=taped["y"], name="選んだ寸法", mode="lines",
                                line={"color": ON, "width": 2.4}), row=1, col=1)
    figure.add_trace(go.Scatter(x=[0], y=[taped["dc"]["0"][0]], mode="markers", showlegend=False,
                                marker={"size": 10, "color": ON, "line": {"color": "white", "width": 1.5}}), row=1, col=1)
    figure.add_trace(go.Scatter(x=[c["cur"] for c in candidates], y=[c["err"] for c in candidates],
                                mode="markers", name="候補", marker={"color": "#b4b9c1", "size": 6}), row=2, col=1)
    figure.add_trace(go.Scatter(x=[taped["cur"]], y=[taped["err"]], mode="markers", showlegend=False,
                                marker={"symbol": "star", "size": 13, "color": INK}), row=2, col=1)
    figure.add_trace(go.Scatter(x=[taped["cur"]], y=[taped["err"]], mode="markers", showlegend=False,
                                marker={"symbol": "circle-open", "size": 15, "color": ON, "line": {"width": 3}}), row=2, col=1)
    figure.update_xaxes(title_text="A (V)", tickvals=[-5, 0, 5], row=1, col=1)
    figure.update_yaxes(title_text="Y (V)", tickvals=[-5, 0, 5], row=1, col=1)
    figure.update_xaxes(title_text="最大静的電流 (µA)", row=2, col=1)
    figure.update_yaxes(title_text="誤差 (mV)", type="log", row=2, col=1)
    figure.update_layout(template="plotly_white", height=560, width=620, margin={"t": 40, "l": 60, "r": 10, "b": 80},
                         legend={"orientation": "h", "y": -.14, "x": 0})
    plot = figure.to_html(include_plotlyjs="cdn", full_html=False, div_id=f"{key}-plot",
                          config={"displaylogo": False})

    axes = grid["grid_axes"]
    params = [("wp", "MPの幅 W", axes["mp_w_um"]), ("wn", "MNの幅 W", axes["mn_w_um"]),
              ("l", "MOSの長さ L", axes["mos_l_um"]), ("r", "抵抗の長さ", axes["rr_l_um"])]
    controls = (f'<label class="main">寸法の候補 <b data-out="main"></b><br>'
                f'<input type="range" data-name="main" min="0" max="{len(candidates)-1}" step="1"></label>'
                f'<div class="params">' + "".join(
                    f'<label>{escape(text)} <b data-out="{name}"></b> µm<br><input type="range" data-param="{name}" '
                    f'min="0" max="{len(values)-1}" step="1" data-values="{escape(json.dumps(values))}"></label>'
                    for name, text, values in params) + "</div>")
    radios, panels, rules = [], [], []
    for index, trit in enumerate((-1, 0, 1)):
        radios.append(f'<input type="radio" name="{key}" id="{key}-{index}" data-t="{trit}"{" checked" if trit == 0 else ""}>'
                      f'<label for="{key}-{index}">A = {TRIT_TEXT[trit]}</label>')
        panels.append(f'<div class="p{index}">{_inverter_svg(trit)}</div>')
        rules.append(f"#{key}-{index}:checked ~ .row .p{index}{{display:block}}")
    style = (f".{key}{{max-width:1000px}} .{key} > input{{display:none}}"
             f".{key} > label{{display:inline-block;padding:.3em 1em;margin:0 .35em .5em 0;border:1px solid #c9ccd1;"
             f"border-radius:4px;cursor:pointer;font-size:14px}}"
             f".{key} > input:checked + label{{background:{ON};color:#fff;border-color:{ON}}}"
             f".{key} .ctl{{margin:.2em 0 .5em}} .{key} .main input{{width:100%;accent-color:{ON}}}"
             f".{key} .main{{display:block;font-size:14px}}"
             f".{key} .params{{display:flex;flex-wrap:wrap;gap:.4em 2em;margin-top:.5em;font-size:13px}}"
             f".{key} .params input{{width:200px}} .{key} .read{{font-size:14px;margin:.4em 0}}"
             f".{key} .row{{display:flex;flex-wrap:wrap;gap:1.5em;align-items:flex-start}}"
             f".{key} .row .sch > div{{display:none}}" + "".join(rules))
    data = {"rows": candidates, "adopted": adopted}
    script = "<script>(function(){" + _SCRIPT.replace("KEY", key).replace("DATA", json.dumps(data)) + "})();</script>"
    display(HTML(f'<style>{style}</style><div class="{key}" style="{FONT}">'
                 f'<div class="ctl">{controls}</div>{"".join(radios)}<div class="read"></div>'
                 f'<div class="row"><div class="sch">{"".join(panels)}</div><div>{plot}</div></div></div>{script}'))
