"""Chapter 4 view: replay one placement-and-routing run from its own record.

The run keeps snapshots of the annealing (``history``, every 25 steps) and the order in which
nets were routed. The replay draws the real cell GDS once as reusable symbols, one group of
``<use>`` per placement snapshot, and one group per routed net; a slider shows snapshots, then
nets one by one with the newest in orange, beside the wire-length curve of the annealing. It works
in the browser alone; nothing is rerun. Every place-and-route step ends by swapping its live
picture for this replay.
"""

from html import escape
import json

from live import LayoutView, _layer_paths, _patterns, _style
from style import ACCENT, INK, MUTED, RULE, control_style, figure_css

_VIEWS = 0


def _wire_rects(wires, vias):
    """Drawn shapes of a net: each wire segment at its width, each via as a square."""
    from tritflow.viz.layers import VIA_SIZE, WIRE_WIDTH
    m1, v1, m2 = _style()[7], _style()[8], _style()[9]
    shapes = []
    for wire in wires:
        layer, half = wire["layer"], WIRE_WIDTH[wire["layer"]]/2
        for (a, b), (c, d) in zip(wire["points"], wire["points"][1:]):
            left, right, low, high = min(a, c)-half, max(a, c)+half, min(b, d)-half, max(b, d)+half
            shapes.append((m1 if layer == "M1" else m2, [(left, low), (right, low), (right, high), (left, high)]))
    h = VIA_SIZE/2
    for via in vias:
        x, y = via["x"], via["y"]
        shapes.append((v1, [(x-h, y-h), (x+h, y-h), (x+h, y+h), (x-h, y+h)]))
    return shapes


def _uses(placements):
    return "".join(
        f'<use href="#rp-{p["cell"]}" transform="translate({p["x"]+p["width"]:g},{p["y"]:g}) scale(-1,1)"/>'
        if p["orient"] == "MY" else f'<use href="#rp-{p["cell"]}" transform="translate({p["x"]:g},{p["y"]:g})"/>'
        for p in placements)


def replay(lay, *, width=600):
    """HTML of a slider over the run: annealing snapshots, then the nets in routing order."""
    global _VIEWS
    _VIEWS += 1
    key = f"tfpnr{_VIEWS}"
    data = lay.data
    history, order = data["history"], data["routing_order"]
    die_w, die_h = data["die"]
    unit = max(die_w, die_h)/500
    view = LayoutView()
    cells = sorted({p["cell"] for p in data["placements"]})
    symbols = "".join(f'<g id="rp-{c}">{_layer_paths(view._cell(c), unit)}</g>' for c in cells)
    snapshots = "".join(f'<g class="s" data-i="{i}">{_uses(h["placements"])}</g>' for i, h in enumerate(history))
    by_net = {}
    for wire in data["wires"]:
        by_net.setdefault(wire["net"], [[], []])[0].append(wire)
    for via in data["vias"]:
        by_net.setdefault(via["net"], [[], []])[1].append(via)
    nets = "".join(f'<g class="n" data-i="{k}">{_layer_paths(_wire_rects(*by_net.get(net, ([], []))), unit)}</g>'
                   for k, net in enumerate(order))
    power = _layer_paths(_wire_rects(data["power"]["straps"], []), unit) if data["power"].get("straps") else ""
    pad = 10*unit
    svg = (f'<svg viewBox="{-pad:g} {-die_h-pad:g} {die_w+2*pad:g} {die_h+2*pad:g}" class="lay">'
           f'<defs>{_patterns(unit)}{symbols}</defs><g transform="scale(1,-1)">'
           f'<rect x="0" y="0" width="{die_w:g}" height="{die_h:g}" fill="none" stroke="{RULE}" stroke-width="{unit:g}"/>'
           f'<g class="pw">{power}</g>{snapshots}{nets}</g></svg>')
    # The annealing curve: wire length (HPWL) against step, with a marker that follows the slider.
    steps, lengths = [h["step"] for h in history], [h["hpwl"]/1e3 for h in history]
    x0, x1, top, low = 40, 300, 12, 110
    sx = lambda s: x0+(x1-x0)*s/max(steps)
    sy = lambda v: low-(low-top)*(v-min(lengths))/max(1e-9, max(lengths)-min(lengths))
    line = " ".join(f"{sx(s):.1f},{sy(v):.1f}" for s, v in zip(steps, lengths))
    curve = (f'<svg viewBox="0 0 320 140" class="curve"><polyline points="{line}" fill="none" stroke="{INK}" stroke-width="1.6"/>'
             f'<line x1="{x0}" y1="{low}" x2="{x1}" y2="{low}" stroke="{MUTED}"/><line x1="{x0}" y1="{top}" x2="{x0}" y2="{low}" stroke="{MUTED}"/>'
             f'<text x="{x0}" y="{low+16}" font-size="11" fill="{MUTED}">0</text>'
             f'<text x="{x1}" y="{low+16}" font-size="11" fill="{MUTED}" text-anchor="end">{max(steps)-1}</text>'
             f'<text x="{(x0+x1)/2}" y="{low+28}" font-size="11" fill="{MUTED}" text-anchor="middle">焼きなましの段</text>'
             f'<text x="{x0-6}" y="{sy(lengths[0])+4:.1f}" font-size="11" fill="{MUTED}" text-anchor="end">{lengths[0]:.1f}</text>'
             f'<text x="{x0-6}" y="{sy(lengths[-1])+4:.1f}" font-size="11" fill="{MUTED}" text-anchor="end">{lengths[-1]:.1f}</text>'
             f'<text x="{x0}" y="{top-2}" font-size="11" fill="{MUTED}">配線長の見積もり (mm)</text>'
             f'<circle class="dot" r="4" fill="{ACCENT}"/></svg>')
    frames = {"steps": steps, "hpwl": lengths, "nets": order, "points": [[sx(s), sy(v)] for s, v in zip(steps, lengths)]}
    script = (f"<script>(function(){{const root=document.querySelector('.{key}'),f={json.dumps(frames)};"
              "const P=f.steps.length,N=f.nets.length,slider=root.querySelector('input'),cap=root.querySelector('.cap'),dot=root.querySelector('.dot');"
              "function show(v){root.querySelectorAll('.s').forEach(g=>g.style.display=(+g.dataset.i===Math.min(v,P-1))?'':'none');"
              "const k=v-P+1;root.querySelectorAll('.n').forEach(g=>{const i=+g.dataset.i;g.style.display=i<k?'':'none';"
              "g.style.filter=i===k-1&&k<N?'drop-shadow(0 0 3px "+ACCENT+")':'';g.style.opacity=i===k-1&&k<N?1:.9;});"
              "const i=Math.min(v,P-1);dot.setAttribute('cx',f.points[i][0]);dot.setAttribute('cy',f.points[i][1]);"
              "cap.textContent=v<P?((v===P-1?'配置：採用した配置':'配置：焼きなまし '+f.steps[v]+' 段')+' · 配線長の見積もり '+f.hpwl[v].toFixed(2)+' mm')"
              ":('配線：'+k+' / '+N+' 本 · '+f.nets[k-1]);}"
              "slider.max=P+N-1;slider.addEventListener('input',()=>show(+slider.value));slider.value=P+N-1;show(P+N-1);})();</script>")
    style = (figure_css(f".{key}") + control_style(f".{key}") +
             f".{key}{{max-width:1100px}} .{key} .row{{display:flex;flex-wrap:wrap;gap:1.2em;align-items:flex-start}}"
             f".{key} .lay{{width:100%;max-width:{width}px;height:auto;flex:1 1 420px}} .{key} .curve{{width:320px;max-width:100%}}"
             f".{key} .cap{{font-size:14px;margin:.2em 0 .4em}}")
    return (f'<style>{style}</style><div class="{key}"><input type="range" min="0" step="1">'
            f'<div class="cap"></div><div class="row">{svg}{curve}</div></div>{script}')
