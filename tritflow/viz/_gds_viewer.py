"""Persistent KLayout viewport and a self-contained notebook pan/zoom surface."""
from __future__ import annotations

from base64 import b64encode
from collections import OrderedDict
from html import escape
import json
import math
from pathlib import Path
from threading import RLock
from uuid import uuid4

# Keep notebook reruns and high-DPI displays from retaining unbounded rasters.
_MAX_EDGE = 2048
_MAX_PIXELS = 2_000_000
_CACHE_BYTES = 16 * 1024 * 1024
_SESSIONS = OrderedDict()


def _pixel_size(width, height):
    values = [float(width), float(height)]
    if any(not math.isfinite(v) or v < 1 for v in values):
        raise ValueError("Pixel dimensions must be positive and finite")
    scale = min(1., _MAX_EDGE / max(values), math.sqrt(_MAX_PIXELS / math.prod(values)))
    return tuple(max(1, math.floor(v * scale)) for v in values)


def _aspect_box(box, width, height):
    """Expand about the centre so one µm has the same scale on both axes."""
    if len(box) != 4:
        raise ValueError("Visible box must contain x0, y0, x1, y1 in µm")
    x0, y0, x1, y1 = map(float, box)
    if (any(not math.isfinite(v) or abs(v) > 1e9 for v in (x0, y0, x1, y1))
            or x1 - x0 < 1e-6 or y1 - y0 < 1e-6):
        raise ValueError("Visible box must be finite, ordered and at least 1e-6 µm wide/high")
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    dx, dy = max(x1 - x0, (y1 - y0) * width / height), max(y1 - y0, (x1 - x0) * height / width)
    return [cx - dx / 2, cy - dy / 2, cx + dx / 2, cy + dy / 2]


class _GdsRenderer:
    """One real LayoutView and bounded LRU tiles for a single GDS hierarchy."""

    def __init__(self, gds_path, top=None):
        from .layout import _open_gds_view
        self.view, cell, self.layers, self.palette = _open_gds_view(gds_path, top)
        self.name = cell.name
        bbox = cell.dbbox()
        self.bounds = [bbox.left, bbox.bottom, bbox.right, bbox.top]
        self.cache = OrderedDict()
        self.cache_bytes = 0
        self.render_count = 0
        self.lock = RLock()

    def close(self):
        with self.lock:
            if self.view is not None:
                self.view.destroy()
                self.view = None
            self.cache.clear()
            self.cache_bytes = 0

    def render(self, box, width, height):
        """Return the actual crop and PNG data URL; preserve isotropic µm scale."""
        import klayout.db as db
        from .layout import _gds_text_visibility
        width, height = _pixel_size(width, height)
        box = _aspect_box(box, width, height)
        key = (*box, width, height)
        with self.lock:
            if self.view is None:
                raise RuntimeError("Viewer expired; rerun its notebook cell to reconnect")
            if key in self.cache:
                self.cache.move_to_end(key)
                return {**self.cache[key], "cached": True}
            self.view.resize(width, height)
            target = db.DBox(*box)
            self.view.zoom_box(target)
            labels = _gds_text_visibility(self.view, target)
            # Explicit target_box avoids viewport/aspect rounding shifting coordinates.
            png = bytes(self.view.get_pixels_with_options(width, height, 0, 0, 0, target).to_png_data())
            self.render_count += 1
            result = {"image": "data:image/png;base64," + b64encode(png).decode(),
                      "box": box, "width": width, "height": height,
                      "render_count": self.render_count, "cached": False, "labels": labels}
            size = len(result["image"])
            if size <= _CACHE_BYTES:
                self.cache[key] = result
                self.cache_bytes += size
                while len(self.cache) > 6 or self.cache_bytes > _CACHE_BYTES:
                    _, old = self.cache.popitem(last=False)
                    self.cache_bytes -= len(old["image"])
            return result


def _register(renderer):
    """Colab's JSON MIME response is consumed by kernel.invokeFunction in JS."""
    try:
        from google.colab import output
    except ImportError:
        return None
    from IPython.display import JSON
    name = "tritflow.gds." + uuid4().hex
    output.register_callback(name, lambda box, width, height: JSON(renderer.render(box, width, height)))
    _SESSIONS[name] = renderer
    while len(_SESSIONS) > 8:
        _, old = _SESSIONS.popitem(last=False)
        old.close()
    return name


DOWNLOAD_LIMIT = 20_000_000


def _download_link(gds_path):
    """The GDS itself, embedded so the viewer can hand it over without a kernel or server."""
    path = Path(gds_path)
    if path.stat().st_size > DOWNLOAD_LIMIT:
        return ""
    data = b64encode(path.read_bytes()).decode()
    return (f'<a download="{escape(path.name, quote=True)}" href="data:application/octet-stream;base64,{data}" '
            f'style="margin-left:auto;color:#f2f4f7;border:1px solid #667085;border-radius:4px;padding:1px 10px;'
            f'text-decoration:none" title="{escape(path.name, quote=True)}">⬇ GDS</a>')


def viewer_html(gds_path, *, top, width, height):
    from IPython.display import HTML
    width, height = _pixel_size(width, height)
    if width < 320 or height < 200:
        raise ValueError("Viewer must be at least 320 × 200 pixels")
    renderer = _GdsRenderer(gds_path, top)
    try:
        box = renderer.bounds
        dx, dy = box[2] - box[0], box[3] - box[1]
        overview = renderer.render([box[0] - dx * .03, box[1] - dy * .03,
                                    box[2] + dx * .03, box[3] + dy * .03],
                                   width * 2, height * 2)
        callback = _register(renderer)
        legend = "".join(
            f'<span style="white-space:nowrap"><i style="display:inline-block;width:10px;height:10px;'
            f'background:{color};margin-right:4px"></i>{escape(name)} {pair[0]}/{pair[1]}</span>'
            for name, pair, color, _ in renderer.layers)
        config = json.dumps({"box": overview["box"], "callback": callback,
                             "width": width, "height": height,
                             "background": renderer.palette[0]}).replace("<", "\\u003c")
        markup = f'''<div data-gds-viewer="1" style="max-width:{width}px;color:#f2f4f7;background:#000;
            border:1px solid #344054;font:13px sans-serif;padding:8px;box-sizing:border-box">
          <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:6px">
            <strong>{escape(renderer.name)} · KLayout / TR-1um</strong>
            <button type="button" data-action="fit">Fit</button>
            <button type="button" data-action="in" aria-label="Zoom in">+</button>
            <button type="button" data-action="out" aria-label="Zoom out">−</button>
            <span data-role="status">Overview · wheel to zoom, drag to pan</span>
            {_download_link(gds_path)}
          </div>
          <div data-role="viewport" style="position:relative;background:{renderer.palette[0]};
              width:100%;aspect-ratio:{width}/{height};overflow:hidden;touch-action:none">
            <img data-gds-overview="1" alt="{escape(renderer.name, quote=True)} — KLayout overview"
                 src="{overview['image']}" style="display:block;width:100%;height:100%">
            <span data-role="scale" style="position:absolute;bottom:12px;left:14px;border-bottom:3px solid white;
                color:white;text-shadow:0 1px 3px black;text-align:center;pointer-events:none"></span>
          </div>
          <div style="display:flex;gap:12px;flex-wrap:wrap;margin-top:6px">
            <span data-role="coords">Coordinates in µm</span><span data-role="extent"></span>
          </div>
          <details style="margin-top:6px"><summary>TR-1um layer legend</summary>
            <div style="display:flex;flex-wrap:wrap;gap:6px 14px;padding-top:6px">{legend}</div>
          </details>
          <script>(function(){{const config={config};{_SCRIPT}}})();</script>
        </div>'''
        if callback is None:
            renderer.close()
        return HTML(markup)
    except Exception:
        renderer.close()
        raise


_SCRIPT = r'''
const root = document.currentScript.parentElement;
const viewport = root.querySelector('[data-role="viewport"]');
const overview = root.querySelector('[data-gds-overview]');
const status = root.querySelector('[data-role="status"]');
const canvas = document.createElement('canvas');
canvas.tabIndex = 0;
canvas.setAttribute('aria-label', 'GDS layout: wheel or plus/minus to zoom, arrows to pan, 0 to fit');
canvas.style.cssText = 'display:block;width:100%;height:100%;cursor:grab;touch-action:none';
const ctx = canvas.getContext('2d');
let box = config.box.slice(), imageBox = box.slice(), tile = overview;
let timer, pending = false, revision = 0, drag = null, failures = 0, liveRenders = 0;
// Kernel availability can change during Run all. Only a non-Colab output is static.
const live = !!(config.callback && window.google?.colab);
function retryDelay(failed) {
  return failed ? Math.min(10000, 500 * 2 ** Math.min(failed - 1, 5)) : 140;
}
function schedule(delay) {
  clearTimeout(timer); timer = setTimeout(render, delay);
}
function dims() { return [box[2] - box[0], box[3] - box[1]]; }
function paint() {
  const [dx, dy] = dims();
  const ratio = Math.min(window.devicePixelRatio || 1, 2);
  canvas.width = Math.max(1, Math.round(viewport.clientWidth * ratio));
  canvas.height = Math.max(1, Math.round(viewport.clientHeight * ratio));
  ctx.fillStyle = config.background; ctx.fillRect(0, 0, canvas.width, canvas.height);
  function draw(image, bounds) {
    if (!image.complete || !image.naturalWidth) return;
    ctx.drawImage(image, (bounds[0] - box[0]) / dx * canvas.width,
      (box[3] - bounds[3]) / dy * canvas.height,
      (bounds[2] - bounds[0]) / dx * canvas.width,
      (bounds[3] - bounds[1]) / dy * canvas.height);
  }
  draw(overview, config.box);
  if (tile !== overview) draw(tile, imageBox);
  const raw = dx * 0.18, order = 10 ** Math.floor(Math.log10(raw));
  const scale = [1, 2, 5, 10].filter(n => n * order <= raw).pop() * order;
  const bar = root.querySelector('[data-role="scale"]');
  bar.style.width = (scale / dx * viewport.clientWidth) + 'px';
  bar.textContent = Number(scale.toPrecision(3)).toString() + ' µm';
  root.querySelector('[data-role="extent"]').textContent = dx.toFixed(2) + ' × ' + dy.toFixed(2) + ' µm';
  root.dataset.viewBox = JSON.stringify(box);
  root.dataset.liveRenders = liveRenders;
}
function state() {
  const waiting = live && (pending || failures > 0 || liveRenders === 0);
  status.textContent = live ? (waiting ? 'live: waiting for kernel…' : 'Live KLayout · ' + liveRenders + ' updates')
    : 'Static overview · rerun in Colab for live detail';
  root.dataset.mode = live ? 'live' : 'static';
  root.dataset.waiting = waiting ? '1' : '0';
  root.dataset.retryCount = failures;
  root.dataset.retryDelay = failures ? retryDelay(failures) : 0;
}
async function render() {
  if (!root.isConnected || !live || pending || drag) return;
  const requested = revision, crop = box.slice();
  pending = true; state();
  try {
    // Leave one request queued behind later notebook cells, even for minutes.
    // Timing it out would abandon a valid reply and accumulate duplicate work.
    const kernel = window.google?.colab?.kernel;
    if (!kernel?.invokeFunction) throw new Error('Kernel not connected yet');
    const result = await kernel.invokeFunction(config.callback, [crop, canvas.width, canvas.height], {});
    const data = result.data['application/json'];
    if (!data?.image?.startsWith('data:image/png;base64,')) throw new Error('No KLayout image');
    const next = new Image(); next.src = data.image; await next.decode();
    if (!root.isConnected) return;
    // Every tile carries its own physical box, so even a stale reply stays aligned.
    tile = next; imageBox = data.box; liveRenders++; failures = 0; paint();
  } catch (error) {
    failures++;
  } finally {
    pending = false; state();
    if (root.isConnected && live && (requested !== revision || failures)) schedule(retryDelay(failures));
  }
}
function changed() {
  revision++; paint(); schedule(retryDelay(failures));
}
function zoom(factor, px = 0.5, py = 0.5) {
  const [dx, dy] = dims();
  factor = Math.max(1e-4 / dx, Math.min(factor, (config.box[2] - config.box[0]) * 20 / dx));
  const x = box[0] + px * dx, y = box[3] - py * dy;
  box = [x - px * dx * factor, y - (1 - py) * dy * factor,
         x + (1 - px) * dx * factor, y + py * dy * factor]; changed();
}
function fit() { box = config.box.slice(); changed(); }
canvas.addEventListener('wheel', event => {
  event.preventDefault();
  const rect = canvas.getBoundingClientRect();
  const delta = event.deltaY * (event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? rect.height : 1);
  zoom(Math.exp(Math.max(-1, Math.min(1, delta * 0.0015))),
       (event.clientX - rect.left) / rect.width, (event.clientY - rect.top) / rect.height);
}, {passive:false});
canvas.addEventListener('pointerdown', event => {
  if (event.button !== 0) return;
  canvas.focus({preventScroll:true}); canvas.setPointerCapture(event.pointerId);
  drag = {x:event.clientX, y:event.clientY, box:box.slice()}; canvas.style.cursor = 'grabbing';
});
canvas.addEventListener('pointermove', event => {
  const rect = canvas.getBoundingClientRect();
  if (drag) {
    const dx = (event.clientX - drag.x) / rect.width * (drag.box[2] - drag.box[0]);
    const dy = (event.clientY - drag.y) / rect.height * (drag.box[3] - drag.box[1]);
    box = [drag.box[0] - dx, drag.box[1] + dy, drag.box[2] - dx, drag.box[3] + dy]; changed();
  }
  const [dx, dy] = dims();
  root.querySelector('[data-role="coords"]').textContent =
    'x ' + (box[0] + (event.clientX - rect.left) / rect.width * dx).toFixed(3) +
    ' · y ' + (box[3] - (event.clientY - rect.top) / rect.height * dy).toFixed(3) + ' µm';
});
function stopDrag() { if (drag) { drag = null; canvas.style.cursor = 'grab'; changed(); } }
canvas.addEventListener('pointerup', stopDrag);
canvas.addEventListener('pointercancel', stopDrag);
canvas.addEventListener('lostpointercapture', stopDrag);
canvas.addEventListener('dblclick', fit);
canvas.addEventListener('keydown', event => {
  if (['+', '=', '-', '0', 'ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'].includes(event.key)) event.preventDefault();
  if (event.key === '+' || event.key === '=') zoom(0.6);
  else if (event.key === '-') zoom(1 / 0.6);
  else if (event.key === '0') fit();
  else if (event.key.startsWith('Arrow')) {
    const [dx, dy] = dims();
    const x = event.key === 'ArrowLeft' ? -dx * .15 : event.key === 'ArrowRight' ? dx * .15 : 0;
    const y = event.key === 'ArrowDown' ? -dy * .15 : event.key === 'ArrowUp' ? dy * .15 : 0;
    box = [box[0] + x, box[1] + y, box[2] + x, box[3] + y]; changed();
  }
});
root.querySelector('[data-action="fit"]').onclick = fit;
root.querySelector('[data-action="in"]').onclick = () => zoom(0.6);
root.querySelector('[data-action="out"]').onclick = () => zoom(1 / 0.6);
function start() {
  if (!overview.naturalWidth) return;
  viewport.insertBefore(canvas, overview); overview.style.display = 'none';
  paint(); state(); if (live) schedule(140);
  new ResizeObserver(() => { if (root.isConnected) changed(); }).observe(viewport);
}
if (overview.complete) start(); else overview.onload = start;
'''
