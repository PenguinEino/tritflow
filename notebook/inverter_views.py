"""Chapter 2 view: the INV's operating point, its DC transfer, and the sizing grid.

The INV is PMOS–RR–Y–RR–NMOS in series between VDD and VSS (VMID unused). The view draws the
taped-out size from the SPICE run the reader's cell just made, and every other size from the
recorded grid that ``tritflow.sim.sizing.load_grid`` checks against the schematic, models and
analysis code. Buttons and sliders work in the browser alone; no kernel callback is needed.
"""

from html import escape
import json

from IPython.display import HTML, display

from style import (ACCENT, BAND, INK, MUTED, TRIT_TEXT, control_style, figure_css, paper_layout,
                   table_css)

_VIEWS = 0


def _key(prefix):
    global _VIEWS
    _VIEWS += 1
    return f"{prefix}{_VIEWS}"


def _operating_point(trit):
    """Which devices conduct at input ``trit``, and fields the script fills for the chosen size."""
    on = lambda state: "オン" if state else "オフ"
    rows = [("MP", on(trit in (-1, 0)), "mp"), ("MN", on(trit in (0, 1)), "mn"),
            ("RP, RN", "", "r"), ("Y", "", "y"), ("I<sub>VDD</sub>", "", "i")]
    body = "".join(f'<tr><th>{name}</th><td>{state}</td><td data-f="{field}"></td></tr>' for name, state, field in rows)
    return f'<table><tr><th></th><th>状態</th><th>値</th></tr>{body}</table>'


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
  const text = {mp: 'W/L = ' + c.wp + '/' + c.l + ' µm', mn: 'W/L = ' + c.wn + '/' + c.l + ' µm', r: 'L = ' + c.r + ' µm',
                y: sign(y) + ' V', i: current.toFixed(0) + ' µA'};
  for (const [f, t] of Object.entries(text)) root.querySelectorAll('[data-f=' + f + ']').forEach(e => e.textContent = t);
  root.querySelector('.read').textContent = '最大誤差 ' + c.err.toFixed(1) + ' mV, 最大静的電流 ' + c.cur.toFixed(0) + ' µA'
    + (c.ok ? '' : '（±0.5 V の帯から外れる入力がある）');
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
    """Top: input buttons, the operating point (which devices conduct, Y and I) and the DC transfer.
    Bottom: the sizes — one slider over every simulated size (as in v1), four linked sliders for the
    dimensions, and where the size sits among all candidates in level error and static current."""
    import plotly.graph_objects as go
    from tritflow import PASS_BAND

    key = _key("tfinv")
    live = spice["rows"][0]
    rows = [r for r in grid["rows"] if not r.get("error")]
    adopted = next(i for i, r in enumerate(rows) if r["is_adopted"])
    candidates = [_candidate(r, live["transfer"]["data"] if r["is_adopted"] else None) for r in rows]
    sweep = [round(v, 3) for v in live["transfer"]["data"]["v-sweep"]]
    taped = candidates[adopted]
    config = {"displaylogo": False, "displayModeBar": False}

    curve = go.Figure()
    for volts in (-5, 0, 5):
        curve.add_hrect(y0=volts-PASS_BAND, y1=volts+PASS_BAND, fillcolor=BAND, opacity=1, line_width=0, layer="below")
    curve.add_trace(go.Scatter(x=sweep, y=taped["y"], name="テープアウトした寸法", mode="lines",
                               line={"color": MUTED, "dash": "dash", "width": 2}))
    curve.add_trace(go.Scatter(x=sweep, y=taped["y"], name="選んだ寸法", mode="lines", line={"color": "#2a78d6", "width": 2.6}))
    curve.add_trace(go.Scatter(x=[0], y=[taped["dc"]["0"][0]], mode="markers", showlegend=False,
                               marker={"size": 9, "color": ACCENT, "line": {"color": "white", "width": 1}}))
    curve.update_layout(**paper_layout(height=320, legend={"orientation": "h", "y": 1.02, "x": 0, "yanchor": "bottom"},
                                       margin={"t": 30, "l": 55, "r": 10, "b": 45}))
    curve.update_xaxes(title_text="V<sub>A</sub> (V)", tickvals=[-5, 0, 5])
    curve.update_yaxes(title_text="V<sub>Y</sub> (V)", tickvals=[-5, 0, 5])
    cloud = go.Figure()
    cloud.add_trace(go.Scatter(x=[c["cur"] for c in candidates], y=[c["err"] for c in candidates], mode="markers",
                               showlegend=False, marker={"color": MUTED, "size": 5, "opacity": .6}))
    cloud.add_trace(go.Scatter(x=[taped["cur"]], y=[taped["err"]], mode="markers", showlegend=False,
                               marker={"symbol": "star", "size": 11, "color": INK}))
    cloud.add_trace(go.Scatter(x=[taped["cur"]], y=[taped["err"]], mode="markers", showlegend=False,
                               marker={"symbol": "circle-open", "size": 14, "color": ACCENT, "line": {"width": 2}}))
    cloud.update_layout(**paper_layout(height=250, margin={"t": 10, "l": 60, "r": 10, "b": 45}))
    cloud.update_xaxes(title_text="最大静的電流 (µA)")
    cloud.update_yaxes(title_text="最大誤差 (mV)", type="log")
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
        panels.append(f'<div class="p{index}">{_operating_point(trit)}</div>')
        rules.append(f"#{key}-{index}:checked ~ .top .p{index}{{display:block}}")
    style = (figure_css(f".{key}") + control_style(f".{key}") + table_css(f".{key}") + f".{key}{{max-width:960px}}"
             f".{key} .top,.{key} .bottom{{display:grid;grid-template-columns:280px minmax(0,1fr);gap:1.4em;align-items:center}}"
             f".{key} .top > div,.{key} .bottom > div{{min-width:0}}"
             f".{key} .bottom{{margin-top:.8em}}"
             f".{key} .op > div{{display:none}} .{key} .op td{{text-align:left}}"
             f".{key} .s{{display:block;font-size:13px;margin:.1em 0 .45em}}"
             f".{key} .read{{font-size:13px;margin-top:.3em}}"
             f"@media (max-width:720px){{.{key} .top,.{key} .bottom{{grid-template-columns:1fr}}"
             f".{key} .op{{justify-self:center}}}}" + "".join(rules))
    data = {"rows": candidates, "adopted": adopted}
    script = "<script>(function(){" + _SCRIPT.replace("KEY", key).replace("DATA", json.dumps(data)) + "})();</script>"
    display(HTML(f'<style>{style}</style><div class="{key}">{"".join(radios)}'
                 f'<div class="top"><div class="op">{"".join(panels)}</div><div>{html(curve, "curve")}</div></div>'
                 f'<div class="bottom"><div>{sliders}</div><div>{html(cloud, "cloud")}</div></div></div>{script}'))
