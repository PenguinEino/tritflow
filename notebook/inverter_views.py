"""Chapter 2 view: the ternary INV redrawn small, its DC transfer, and the sizing grid.

The INV is PMOS–RR–Y–RR–NMOS in series between VDD and VSS (VMID unused). The view draws the
taped-out size from the SPICE run the reader's cell just made, and every other size from the
recorded grid that ``tritflow.sim.sizing.load_grid`` checks against the schematic, models and
analysis code. Buttons and sliders work in the browser alone; no kernel callback is needed.
"""

from html import escape
import json

from IPython.display import HTML, display

from live import FONT, DIM, control_style

ON, OFF, INK = "#e8782a", "#b4b9c1", "#30353b"
TRIT_TEXT = {-1: "−1", 0: "0", 1: "+1"}
_VIEWS = 0


def _key(prefix):
    global _VIEWS
    _VIEWS += 1
    return f"{prefix}{_VIEWS}"


def _wire(points, color, width):
    return f'<polyline points="{" ".join(f"{x},{y}" for x, y in points)}" fill="none" stroke="{color}" stroke-width="{width}"/>'


def _mos(x, top, kind, on, field):
    """A MOS on the vertical stack at ``x``: terminals at ``top`` and ``top+40``, the channel to
    the left, the gate plate left of it (with a bubble for PMOS), and the gate lead to x−70."""
    color, width = (ON, 2.6) if on else (OFF, 1.6)
    channel, plate = x-14, x-20
    parts = [
        _wire([(x, top), (x, top+8), (channel, top+8)], color, width),
        _wire([(channel, top+32), (x, top+32), (x, top+40)], color, width),
        f'<path d="M{channel},{top+4} V{top+36}" stroke="{color}" stroke-width="{width+1.2}"/>',
        f'<path d="M{plate},{top+8} V{top+32}" stroke="{INK}" stroke-width="1.8"/>',
    ]
    lead = plate
    if kind == "P":
        parts.append(f'<circle cx="{plate-4}" cy="{top+20}" r="3.5" fill="white" stroke="{INK}" stroke-width="1.5"/>')
        lead = plate-7.5
    parts.append(_wire([(lead, top+20), (x-70, top+20)], INK, 1.5))
    parts.append(f'<text x="{x+12}" y="{top+25}" font-size="12" fill="{INK}" data-f="{field}"></text>')
    return "".join(parts)


def _resistor(x, top, on, field):
    """A zigzag resistor from ``top`` to ``top+44``."""
    color, width = (ON, 2.4) if on else (OFF, 1.6)
    points = [(x, top), (x, top+6)] + [(x+(7 if k % 2 else -7), top+10+k*4.6) for k in range(7)] + [(x, top+38), (x, top+44)]
    return _wire(points, color, width) + f'<text x="{x+14}" y="{top+27}" font-size="12" fill="{INK}" data-f="{field}"></text>'


def _inverter_svg(trit):
    """INV at input ``trit``. Conducting devices and the wires between them are orange; the
    sizes, Y and I are text fields the script fills for the selected size."""
    up, down = trit in (-1, 0), trit in (0, 1)
    x, gate = 150, 80
    rail = lambda on: (ON, 2.4) if on else (OFF, 1.6)
    body = [
        f'<path d="M{x-34},16 H{x+34}" stroke="{INK}" stroke-width="2.2"/>'
        f'<text x="{x+40}" y="20" font-size="12" fill="{INK}">VDD</text>',
        _wire([(x, 16), (x, 40)], *rail(up)),
        _mos(x, 40, "P", up, "mp"),
        _wire([(x, 80), (x, 92)], *rail(up)),
        _resistor(x, 92, up, "rp"),
        _wire([(x, 136), (x, 172)], *rail(up)),
        _wire([(x, 172), (x, 208)], *rail(down)),
        _resistor(x, 208, down, "rn"),
        _wire([(x, 252), (x, 264)], *rail(down)),
        _mos(x, 264, "N", down, "mn"),
        _wire([(x, 304), (x, 328)], *rail(down)),
        f'<path d="M{x-34},328 H{x+34}" stroke="{INK}" stroke-width="2.2"/>'
        f'<text x="{x+40}" y="332" font-size="12" fill="{INK}">VSS</text>',
        f'<circle cx="{x}" cy="172" r="3.2" fill="{INK}"/>',
        _wire([(x, 172), (x+56, 172)], INK, 1.6),
        f'<text x="{x+62}" y="168" font-size="12" fill="{INK}">Y</text>',
        f'<text x="{x+62}" y="184" font-size="12" font-weight="700" fill="{INK}" data-f="y"></text>',
        _wire([(gate, 60), (gate, 284)], INK, 1.5),
        f'<circle cx="{gate}" cy="172" r="3.2" fill="{INK}"/>',
        _wire([(28, 172), (gate, 172)], INK, 1.6),
        f'<text x="20" y="160" font-size="12" fill="{INK}">A</text>',
        f'<text x="20" y="190" font-size="12" font-weight="700" fill="{INK}">{ {-1: "−5 V", 0: "0 V", 1: "+5 V"}[trit] }</text>',
        f'<text x="{x+40}" y="38" font-size="12" fill="{ON if trit == 0 else DIM}" data-f="i"></text>',
    ]
    return f'<svg viewBox="0 0 290 344" width="290" height="344">{"".join(body)}</svg>'


def _candidate(row, transfer=None):
    """What the view needs from one simulated size: dimensions, curve, per-input Y and I."""
    d, data = row["dimensions"], (transfer or row["transfer"]["data"])
    dc = {r["input_trits"][0]: r for r in row["dc"]}
    return {"wp": d["MP"]["w_um"], "wn": d["MN"]["w_um"], "l": d["MP"]["l_um"], "r": d["RP"]["l_um"],
            "y": [round(v, 4) for v in data["v(Y)"]],
            "dc": {str(t): [dc[t]["output_v"]["Y"], abs(dc[t]["rail_current_a"]["VDD"])*1e6] for t in (-1, 0, 1)},
            "err": row["max_error_v"]*1e3, "cur": row["max_static_current_a"]*1e6, "ok": row["passed"]}


_SCRIPT = r"""
const root = document.querySelector('.KEY'), data = DATA;
const curve = () => document.getElementById('KEY-curve'), cloud = () => document.getElementById('KEY-cloud');
const main = root.querySelector('input[data-name=main]'), params = [...root.querySelectorAll('input[data-param]')];
let index = data.adopted, trit = 0;
const sign = v => (v >= 0 ? '+' : '') + v.toFixed(2);
function draw() {
  const c = data.rows[index], [y, current] = c.dc[String(trit)];
  main.value = index;
  root.querySelector('[data-out=main]').textContent = index === data.adopted ? 'テープアウトした寸法' : (index + 1) + ' / ' + data.rows.length;
  params.forEach(s => { s.value = JSON.parse(s.dataset.values).indexOf(c[s.dataset.param]);
    root.querySelector('[data-out=' + s.dataset.param + ']').textContent = c[s.dataset.param]; });
  const text = {mp: 'MP ' + c.wp + '/' + c.l, mn: 'MN ' + c.wn + '/' + c.l, rp: 'RP ' + c.r, rn: 'RN ' + c.r,
                y: sign(y) + ' V', i: current.toFixed(0) + ' µA'};
  for (const [f, t] of Object.entries(text)) root.querySelectorAll('[data-f=' + f + ']').forEach(e => e.textContent = t);
  root.querySelector('.read').textContent = '誤差 ' + c.err.toFixed(1) + ' mV · 静的電流 ' + c.cur.toFixed(0) + ' µA'
    + (c.ok ? '' : ' · ±0.5 V の帯から外れる入力がある');
  if (window.Plotly && curve()) {
    Plotly.restyle(curve(), {y: [c.y]}, [1]);
    Plotly.restyle(curve(), {x: [[trit * 5]], y: [[y]]}, [2]);
  }
  if (window.Plotly && cloud()) Plotly.restyle(cloud(), {x: [[c.cur]], y: [[c.err]]}, [2]);
}
main.addEventListener('input', () => { index = +main.value; draw(); });
params.forEach(s => s.addEventListener('input', () => {
  const values = params.map(p => JSON.parse(p.dataset.values)[+p.value]);
  const found = data.rows.findIndex(r => params.every((p, k) => r[p.dataset.param] === values[k]));
  if (found >= 0) { index = found; draw(); }
  else root.querySelector('.read').textContent = 'この組合せはSPICEが収束しなかった';
}));
root.querySelectorAll('input[name=KEY]').forEach(r => r.addEventListener('change', () => { trit = +r.dataset.t; draw(); }));
draw();
"""


def inverter(spice, grid):
    """Top: input buttons, the redrawn INV and its DC transfer. Bottom: the sizes — one slider over
    every simulated size (as in v1), four linked sliders for the dimensions, and where the size
    sits among all candidates in level error and static current."""
    import plotly.graph_objects as go
    from tritflow import PASS_BAND

    key = _key("tfinv")
    live = spice["rows"][0]
    rows = [r for r in grid["rows"] if not r.get("error")]
    adopted = next(i for i, r in enumerate(rows) if r["is_adopted"])
    candidates = [_candidate(r, live["transfer"]["data"] if r["is_adopted"] else None) for r in rows]
    sweep = [round(v, 3) for v in live["transfer"]["data"]["v-sweep"]]
    taped = candidates[adopted]
    config = {"displaylogo": False}

    curve = go.Figure()
    for volts in (-5, 0, 5):
        curve.add_hrect(y0=volts-PASS_BAND, y1=volts+PASS_BAND, fillcolor="#6eae89", opacity=.15, line_width=0)
    curve.add_trace(go.Scatter(x=sweep, y=taped["y"], name="テープアウトした寸法", mode="lines",
                               line={"color": "#9aa1ab", "dash": "dash", "width": 1.6}))
    curve.add_trace(go.Scatter(x=sweep, y=taped["y"], name="選んだ寸法", mode="lines", line={"color": ON, "width": 2.4}))
    curve.add_trace(go.Scatter(x=[0], y=[taped["dc"]["0"][0]], mode="markers", showlegend=False,
                               marker={"size": 10, "color": ON, "line": {"color": "white", "width": 1.5}}))
    curve.update_layout(template="plotly_white", height=344, margin={"t": 30, "l": 50, "r": 10, "b": 40},
                        xaxis={"title": "A (V)", "tickvals": [-5, 0, 5]}, yaxis={"title": "Y (V)", "tickvals": [-5, 0, 5]},
                        legend={"orientation": "h", "y": 1.02, "x": 0, "yanchor": "bottom"})
    cloud = go.Figure()
    cloud.add_trace(go.Scatter(x=[c["cur"] for c in candidates], y=[c["err"] for c in candidates], mode="markers",
                               showlegend=False, marker={"color": "#c4c8ce", "size": 6}))
    cloud.add_trace(go.Scatter(x=[taped["cur"]], y=[taped["err"]], mode="markers", showlegend=False,
                               marker={"symbol": "star", "size": 12, "color": INK}))
    cloud.add_trace(go.Scatter(x=[taped["cur"]], y=[taped["err"]], mode="markers", showlegend=False,
                               marker={"symbol": "circle-open", "size": 15, "color": ON, "line": {"width": 3}}))
    cloud.update_layout(template="plotly_white", height=260, margin={"t": 10, "l": 55, "r": 10, "b": 40},
                        xaxis={"title": "静的電流 (µA)"}, yaxis={"title": "誤差 (mV)", "type": "log"})
    html = lambda figure, name: figure.to_html(include_plotlyjs="cdn", full_html=False, div_id=f"{key}-{name}", config=config)

    axes = grid["grid_axes"]
    params = [("wp", "MPの幅 W", axes["mp_w_um"]), ("wn", "MNの幅 W", axes["mn_w_um"]),
              ("l", "MOSの長さ L", axes["mos_l_um"]), ("r", "抵抗の長さ", axes["rr_l_um"])]
    sliders = (f'<label class="s">寸法の候補　<b data-out="main"></b>'
               f'<input type="range" data-name="main" min="0" max="{len(candidates)-1}" step="1"></label>' + "".join(
                   f'<label class="s">{escape(text)}　<b data-out="{name}"></b> µm<input type="range" data-param="{name}" '
                   f'min="0" max="{len(values)-1}" step="1" data-values="{escape(json.dumps(values))}"></label>'
                   for name, text, values in params) + '<div class="read"></div>')
    radios, panels, rules = [], [], []
    for index, trit in enumerate((-1, 0, 1)):
        radios.append(f'<input type="radio" name="{key}" id="{key}-{index}" data-t="{trit}"{" checked" if trit == 0 else ""}>'
                      f'<label for="{key}-{index}">A = {TRIT_TEXT[trit]}</label>')
        panels.append(f'<div class="p{index}">{_inverter_svg(trit)}</div>')
        rules.append(f"#{key}-{index}:checked ~ .top .p{index}{{display:block}}")
    style = (control_style(f".{key}") + f".{key}{{max-width:960px}}"
             f".{key} .top,.{key} .bottom{{display:grid;grid-template-columns:300px 1fr;gap:1.2em;align-items:center}}"
             f".{key} .bottom{{margin-top:1em;padding-top:.8em;border-top:1px solid #e3e5e8}}"
             f".{key} .sch > div{{display:none}}"
             f".{key} .s{{display:block;font-size:13px;margin:.15em 0 .45em;color:#2b2f36}}"
             f".{key} .read{{font-size:13px;color:{INK};margin-top:.3em}}"
             f"@media (max-width:720px){{.{key} .top,.{key} .bottom{{grid-template-columns:1fr}}}}" + "".join(rules))
    data = {"rows": candidates, "adopted": adopted}
    script = "<script>(function(){" + _SCRIPT.replace("KEY", key).replace("DATA", json.dumps(data)) + "})();</script>"
    display(HTML(f'<style>{style}</style><div class="{key}" style="{FONT}">{"".join(radios)}'
                 f'<div class="top"><div class="sch">{"".join(panels)}</div><div>{html(curve, "curve")}</div></div>'
                 f'<div class="bottom"><div>{sliders}</div><div>{html(cloud, "cloud")}</div></div></div>{script}'))
