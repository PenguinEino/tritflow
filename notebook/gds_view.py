"""A GDS viewer that zooms and pans in the browser.

The layout is turned into SVG once, keeping the GDS hierarchy: each cell becomes a symbol
(one path per drawn layer) and every instance a ``<use>`` with its transform. Zoom and pan only
change the SVG view box, so they need no kernel round trip and stay instant. Layers are drawn in
the notebook's TR-1um colours and hatches. A layout too large to draw this way falls back to
the KLayout tile viewer, which renders on the kernel.
"""

from base64 import b64encode
from html import escape
from pathlib import Path

from IPython.display import HTML

from live import FONT, DIM, _layer_paths, _patterns, _style

POLYGON_LIMIT = 150_000
DOWNLOAD_LIMIT = 20_000_000


def _symbols(layout, unit):
    """One ``<g>`` per cell: its own shapes by layer, then its child instances."""
    import klayout.db as db
    styles = [(style, layout.find_layer(*style[0])) for style in _style()]
    styles = [(style, index) for style, index in styles if index is not None]
    groups, polygons = [], 0
    for cell in layout.each_cell():
        shapes = []
        for style, index in styles:
            for polygon in db.Region(cell.shapes(index)).merged().each():
                points = polygon.to_dtype(layout.dbu)
                shapes.append((style, [(p.x, p.y) for p in points.each_point_hull()]))
        polygons += len(shapes)
        uses = []
        for instance in cell.each_inst():
            for trans in instance.cell_inst.each_cplx_trans():
                # The instance transform is in database units; the symbols are in µm.
                t = db.DCplxTrans(trans.mag, trans.angle, trans.is_mirror(),
                                  db.DVector(trans.disp.x*layout.dbu, trans.disp.y*layout.dbu))
                origin, ex, ey = t*db.DPoint(0, 0), t*db.DPoint(1, 0), t*db.DPoint(0, 1)
                uses.append(f'<use href="#c{instance.cell_index}" transform="matrix({ex.x-origin.x:.6g},{ex.y-origin.y:.6g},'
                            f'{ey.x-origin.x:.6g},{ey.y-origin.y:.6g},{origin.x:.6g},{origin.y:.6g})"/>')
        groups.append(f'<g id="c{cell.cell_index()}">{_layer_paths(shapes, unit)}{"".join(uses)}</g>')
    return "".join(groups), polygons


_SCRIPT = r"""
const root = document.getElementById('KEY'), svg = root.querySelector('svg'), status = root.querySelector('.status');
const full = FULL; let box = full.slice(), drag = null;
function show() { svg.setAttribute('viewBox', box.join(' '));
  status.textContent = (box[2]).toFixed(box[2] < 10 ? 2 : 0) + ' × ' + (box[3]).toFixed(box[3] < 10 ? 2 : 0) + ' µm'; }
function point(event) { const r = svg.getBoundingClientRect();
  return [box[0] + (event.clientX - r.left) / r.width * box[2], box[1] + (event.clientY - r.top) / r.height * box[3]]; }
function zoom(factor, at) { const [x, y] = at || [box[0] + box[2] / 2, box[1] + box[3] / 2];
  box = [x - (x - box[0]) * factor, y - (y - box[1]) * factor, box[2] * factor, box[3] * factor]; show(); }
svg.addEventListener('wheel', e => { e.preventDefault(); zoom(Math.exp(e.deltaY * 0.0015), point(e)); }, {passive: false});
svg.addEventListener('pointerdown', e => { drag = [e.clientX, e.clientY, box[0], box[1]]; svg.setPointerCapture(e.pointerId); });
svg.addEventListener('pointermove', e => {
  const [x, y] = point(e); root.querySelector('.xy').textContent = 'x ' + x.toFixed(1) + ', y ' + (-y).toFixed(1) + ' µm';
  if (!drag) return; const r = svg.getBoundingClientRect();
  box[0] = drag[2] - (e.clientX - drag[0]) / r.width * box[2]; box[1] = drag[3] - (e.clientY - drag[1]) / r.height * box[3]; show(); });
svg.addEventListener('pointerup', () => drag = null);
svg.addEventListener('dblclick', () => { box = full.slice(); show(); });
root.querySelector('[data-a=fit]').onclick = () => { box = full.slice(); show(); };
root.querySelector('[data-a=in]').onclick = () => zoom(0.6);
root.querySelector('[data-a=out]').onclick = () => zoom(1 / 0.6);
show();
"""

_VIEWS = 0


def gds_view(gds_path, *, top=None, height=560):
    """Interactive layout of ``gds_path``: wheel zooms about the cursor, drag pans, double-click
    fits, and the GDS itself can be downloaded."""
    import klayout.db as db
    global _VIEWS
    path = Path(gds_path)
    layout = db.Layout()
    layout.read(str(path))
    cell = layout.cell(top) if top else layout.top_cell()
    box = cell.dbbox()
    unit = max(box.width(), box.height())/900
    symbols, polygons = _symbols(layout, unit)
    if polygons > POLYGON_LIMIT:
        from tritflow.viz.layout import gds_viewer
        return gds_viewer(path, top=top)
    _VIEWS += 1
    key = f"tfgds{_VIEWS}"
    pad = max(box.width(), box.height())*0.03
    full = [box.left-pad, -box.top-pad, box.width()+2*pad, box.height()+2*pad]
    download = ""
    if path.stat().st_size <= DOWNLOAD_LIMIT:
        download = (f'<a download="{escape(path.name, quote=True)}" href="data:application/octet-stream;base64,'
                    f'{b64encode(path.read_bytes()).decode()}" class="b" style="margin-left:auto">⬇ GDS</a>')
    legend = "".join(f'<span><i style="background:{color}"></i>{escape(name)}</span>'
                     for (_, name, color, *_rest) in _legend())
    style = (f"#{key}{{max-width:1100px;border:1px solid #d5d7db;border-radius:8px;background:#fff;padding:6px}}"
             f"#{key} .bar{{display:flex;gap:8px;align-items:center;margin-bottom:4px;font-size:13px}}"
             f"#{key} .b{{border:1px solid #c9ccd1;border-radius:4px;padding:1px 10px;background:#fff;cursor:pointer;"
             f"color:#30353b;text-decoration:none;font:inherit}}"
             f"#{key} svg{{width:100%;height:{height}px;display:block;cursor:grab;touch-action:none;background:#fff}}"
             f"#{key} .lg{{display:flex;flex-wrap:wrap;gap:4px 14px;font-size:12px;color:{DIM};margin-top:4px}}"
             f"#{key} .lg i{{display:inline-block;width:10px;height:10px;margin-right:4px;vertical-align:middle}}")
    script = _SCRIPT.replace("KEY", key).replace("FULL", str(full))
    return HTML(
        f'<style>{style}</style><div id="{key}" style="{FONT}"><div class="bar">'
        f'<b>{escape(cell.name)}</b><button class="b" data-a="fit">全体</button>'
        f'<button class="b" data-a="in">＋</button><button class="b" data-a="out">−</button>'
        f'<span class="status"></span><span class="xy" style="color:{DIM}"></span>{download}</div>'
        f'<svg preserveAspectRatio="xMidYMid meet"><defs>{_patterns(unit)}{symbols}</defs>'
        f'<g transform="scale(1,-1)"><use href="#c{cell.cell_index()}"/></g></svg>'
        f'<div style="color:{DIM};font-size:12px">ホイールで拡大縮小、ドラッグで移動、ダブルクリックで全体に戻る。</div>'
        f'<div class="lg">{legend}</div></div><script>(function(){{{script}}})();</script>')


def _legend():
    from tritflow.viz.layers import LAYER_STYLE
    return LAYER_STYLE
