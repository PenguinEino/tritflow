"""Persistent KLayout viewport and a self-contained notebook pan/zoom surface."""
from __future__ import annotations

from base64 import b64encode
from collections import OrderedDict
from html import escape
from io import BytesIO
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

_LABELS = {
    "en": {
        "fit": "Fit", "zoom_in": "Zoom in", "zoom_out": "Zoom out",
        "overview": "Overview · wheel to zoom, drag to pan",
        "image": "KLayout overview", "coords": "Coordinates in µm", "legend": "TR-1um layer legend",
        "canvas": "GDS layout: wheel or plus/minus to zoom, arrows to pan, 0 to fit",
        "waiting": "live: waiting for kernel…", "live": "Live KLayout · {count} updates",
        "static": "Static overview · rerun in Colab for live detail",
    },
    "ja": {
        "fit": "全体表示", "zoom_in": "拡大", "zoom_out": "縮小",
        "overview": "全体表示 · ホイールで拡大・縮小、ドラッグで移動",
        "image": "KLayoutによる全体図", "coords": "座標の単位：µm", "legend": "TR-1umの層の凡例",
        "canvas": "GDS：ホイールまたは＋・−で拡大・縮小、矢印キーで移動、0で全体表示",
        "waiting": "詳細表示：カーネルの応答待ち…", "live": "KLayout詳細表示 · 更新{count}回",
        "static": "静止画像 · Colabで再実行すると拡大時に詳細を描画する",
    },
}


def _encode_image(png, encoding):
    """Compress KLayout's stippled pixels without changing any layer colours.

    Lossy codecs blur one-pixel metal/poly edges and inflate these few-colour
    drawings. Low-effort lossless WebP is smaller; retain PNG when unavailable
    or when its original stream is already shorter (for example an empty crop).
    """
    if encoding == "webp":
        from PIL import Image, features
        if features.check("webp"):
            try:
                with Image.open(BytesIO(png)) as image:
                    stream = BytesIO()
                    image.save(stream, format="WEBP", lossless=True, method=0)
                webp = stream.getvalue()
                if len(webp) < len(png):
                    return "image/webp", webp
            except (OSError, ValueError):
                pass  # Minimal Pillow builds can lack a working WebP encoder.
    return "image/png", png


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
    """One warm LayoutView and bounded LRU crops for a single GDS hierarchy."""

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

    def render(self, box, width, height, encoding="png"):
        """Return a lossless physical crop, preserving isotropic µm scale.

        PNG remains the default for standalone exports. Live clients opt into
        lossless WebP, with automatic PNG fallback on minimal Pillow builds.
        """
        import klayout.db as db
        from .layout import _gds_text_visibility
        if encoding not in ("png", "webp"):
            raise ValueError("Image encoding must be png or webp")
        width, height = _pixel_size(width, height)
        box = _aspect_box(box, width, height)
        key = (*box, width, height, encoding)
        with self.lock:
            if self.view is None:
                raise RuntimeError("Viewer expired; rerun its notebook cell to reconnect")
            if key in self.cache:
                self.cache.move_to_end(key)
                return {**self.cache[key], "cached": True}
            target = db.DBox(*box)
            labels = _gds_text_visibility(self.view, target)
            # Explicit target_box sets both crop and scale; resize/zoom_box only
            # invalidate the warm view and are unnecessary for offscreen pixels.
            png = bytes(self.view.get_pixels_with_options(width, height, 0, 0, 0, target).to_png_data())
            mime, data = _encode_image(png, encoding)
            self.render_count += 1
            result = {"image": f"data:{mime};base64," + b64encode(data).decode(),
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
    def callback(box, width, height, encoding="png"):
        active = _SESSIONS.get(name)
        if active is None:
            raise RuntimeError("Viewer expired; rerun its notebook cell to reconnect")
        return JSON(active.render(box, width, height, encoding))

    output.register_callback(name, callback)
    _SESSIONS[name] = renderer
    while len(_SESSIONS) > 8:
        expired, old = _SESSIONS.popitem(last=False)
        old.close()
        if hasattr(output, "unregister_callback"):
            output.unregister_callback(expired)
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


def viewer_html(gds_path, *, top, width, height, language=None):
    from IPython.display import HTML
    from tritflow.schematic import get_language
    from .layout import _TEXT_LABEL_SPAN_UM

    language = get_language() if language is None else language
    if language not in _LABELS:
        raise ValueError(f"unknown language: {language}")
    labels = _LABELS[language]
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
                             "maxEdge": _MAX_EDGE, "maxPixels": _MAX_PIXELS,
                             "labelSpanUm": _TEXT_LABEL_SPAN_UM, "labels": labels,
                             "background": renderer.palette[0]}, ensure_ascii=False).replace("<", "\\u003c")
        markup = f'''<div data-gds-viewer="1" style="max-width:{width}px;color:#f2f4f7;background:#000;
            border:1px solid #344054;font:13px sans-serif;padding:8px;box-sizing:border-box">
          <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:6px">
            <strong>{escape(renderer.name)} · KLayout / TR-1um</strong>
            <button type="button" data-action="fit">{labels['fit']}</button>
            <button type="button" data-action="in" aria-label="{labels['zoom_in']}">+</button>
            <button type="button" data-action="out" aria-label="{labels['zoom_out']}">−</button>
            <span data-role="status">{labels['overview']}</span>
            {_download_link(gds_path)}
          </div>
          <div data-role="viewport" style="position:relative;background:{renderer.palette[0]};
              width:100%;aspect-ratio:{width}/{height};overflow:hidden;touch-action:none">
            <img data-gds-overview="1" alt="{escape(renderer.name, quote=True)} — {labels['image']}"
                 src="{overview['image']}" style="display:block;width:100%;height:100%">
            <span data-role="scale" style="position:absolute;bottom:12px;left:14px;border-bottom:3px solid white;
                color:white;text-shadow:0 1px 3px black;text-align:center;pointer-events:none"></span>
          </div>
          <div style="display:flex;gap:12px;flex-wrap:wrap;margin-top:6px">
            <span data-role="coords">{labels['coords']}</span><span data-role="extent"></span>
          </div>
          <details style="margin-top:6px"><summary>{labels['legend']}</summary>
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
const labels = config.labels;
const canvas = document.createElement('canvas');
canvas.tabIndex = 0;
canvas.setAttribute('aria-label', labels.canvas);
canvas.style.cssText = 'display:block;width:100%;height:100%;cursor:grab;touch-action:none';
const ctx = canvas.getContext('2d');
let box = config.box.slice(), imageBox = box.slice(), tile = overview;
let timer = null, timerAt = Infinity, pending = false, revision = 0, served = 0;
let drag = null, failures = 0, liveRenders = 0, retryAt = 0, lastRequest = -Infinity;
let changedAt = performance.now(), cacheBytes = 0, waitingSince = null;
// Saved outputs reopened in Colab have no kernel holding this viewer's callback:
// a request then never returns, so a long wait falls back to the static label.
const stallMs = 4000;
let encoding = 'webp';
const crops = new Map(), cacheLimit = 16 * 1024 * 1024;
// Kernel availability can change during Run all. Only a non-Colab output is static.
const live = !!(config.callback && window.google?.colab);
function retryDelay(failed) {
  return failed ? Math.min(10000, 500 * 2 ** Math.min(failed - 1, 5)) : 0;
}
function pixelSize(width, height) {
  const scale = Math.min(1, config.maxEdge / Math.max(width, height),
    Math.sqrt(config.maxPixels / (width * height)));
  return [Math.max(1, Math.floor(width * scale)), Math.max(1, Math.floor(height * scale))];
}
// Throttle, never debounce: another pointer event must not postpone an earlier
// quick request. One in flight coalesces all further events into the latest box.
function schedule(delay = 0, sharp = false) {
  if (!root.isConnected || !live || pending) return;
  const now = performance.now();
  const due = Math.max(now + delay, retryAt, lastRequest + 32);
  if (timer !== null && timerAt <= due) return;
  clearTimeout(timer); timerAt = due;
  timer = setTimeout(() => { timer = null; timerAt = Infinity; render(sharp); }, Math.max(0, due - now));
}
function dims() { return [box[2] - box[0], box[3] - box[1]]; }
function request(sharp) {
  const ratio = sharp ? Math.min(window.devicePixelRatio || 1, 2) : 1;
  const [width, height] = pixelSize(Math.max(1, Math.round(viewport.clientWidth * ratio)),
    Math.max(1, Math.round(viewport.clientHeight * ratio)));
  const [dx, dy] = dims(), cx = (box[0] + box[2]) / 2, cy = (box[1] + box[3]) / 2;
  const w = Math.max(dx, dy * width / height), h = Math.max(dy, dx * height / width);
  const crop = [cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2];
  return {crop, width, height};
}
function cropKey(data) { return JSON.stringify([data.box, data.width, data.height]); }
function remember(image, data) {
  const key = cropKey(data), bytes = data.width * data.height * 4;
  if (crops.has(key)) { cacheBytes -= crops.get(key).bytes; crops.delete(key); }
  if (bytes > cacheLimit) return;
  crops.set(key, {image, box:data.box, width:data.width, height:data.height, bytes});
  cacheBytes += bytes;
  while (crops.size > 8 || cacheBytes > cacheLimit) {
    const oldest = crops.keys().next().value;
    cacheBytes -= crops.get(oldest).bytes; crops.delete(oldest);
  }
  root.dataset.cacheBytes = cacheBytes;
  root.dataset.cacheEntries = crops.size;
}
function cachedCrop(req) {
  // A larger crop can supply a smaller view at the same or better sampling.
  // Use the same physical text threshold as the KLayout renderer.
  for (const [key, entry] of Array.from(crops).reverse()) {
    const b = entry.box, c = req.crop, epsilon = (c[2] - c[0]) * 1e-9;
    if ((b[2] - b[0] <= config.labelSpanUm) !== (c[2] - c[0] <= config.labelSpanUm)) continue;
    if (b[0] > c[0] + epsilon || b[1] > c[1] + epsilon ||
        b[2] < c[2] - epsilon || b[3] < c[3] - epsilon) continue;
    if (entry.width / (b[2] - b[0]) + 1e-9 < req.width / (c[2] - c[0]) ||
        entry.height / (b[3] - b[1]) + 1e-9 < req.height / (c[3] - c[1])) continue;
    // KLayout text has a fixed pixel size: reuse labelled views only at the
    // same sampling, otherwise a cached label would shrink/grow with zoom.
    if (c[2] - c[0] <= config.labelSpanUm && Math.abs((b[2] - b[0]) / entry.width -
        (c[2] - c[0]) / req.width) > (c[2] - c[0]) / req.width * 1e-6) continue;
    crops.delete(key); crops.set(key, entry);
    return entry;
  }
  return null;
}
function paint() {
  const [dx, dy] = dims();
  const [width, height] = pixelSize(Math.max(1, Math.round(viewport.clientWidth * Math.min(window.devicePixelRatio || 1, 2))),
    Math.max(1, Math.round(viewport.clientHeight * Math.min(window.devicePixelRatio || 1, 2))));
  // Resetting a canvas on every mouse event reallocates its backing store.
  if (canvas.width !== width) canvas.width = width;
  if (canvas.height !== height) canvas.height = height;
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
  root.dataset.imageBox = JSON.stringify(imageBox);
}
function state() {
  const now = performance.now(), waiting = live && (pending || served !== revision);
  if (!waiting) waitingSince = null;
  else if (waitingSince === null) { waitingSince = now; setTimeout(state, stallMs); }
  const stalled = waiting && now - waitingSince >= stallMs;
  status.textContent = !live || stalled ? labels.static
    : waiting ? labels.waiting : labels.live.replace('{count}', liveRenders);
  root.dataset.mode = live ? 'live' : 'static';
  root.dataset.waiting = waiting ? '1' : '0';
  root.dataset.stalled = stalled ? '1' : '0';
  root.dataset.retryCount = failures;
  root.dataset.retryDelay = failures ? retryDelay(failures) : 0;
}
function refine() {
  if (drag) return;
  const quick = request(false), sharp = request(true);
  // A 1x display already has the final resolution; avoid its second round trip.
  if (sharp.width > quick.width || sharp.height > quick.height)
    schedule(Math.max(0, 120 - (performance.now() - changedAt)), true);
}
async function render(sharp = false) {
  if (!root.isConnected || !live || pending) return;
  // An idle timer may coincide with fresh input; always prioritise its quick view.
  sharp = sharp && !drag && performance.now() - changedAt >= 120;
  const requested = revision, req = request(sharp), cached = cachedCrop(req);
  if (cached) {
    tile = cached.image; imageBox = cached.box; served = requested; paint(); state();
    if (!sharp) refine();
    return;
  }
  pending = true; lastRequest = performance.now(); state();
  try {
    // Leave one request queued behind later notebook cells, even for minutes.
    // Timing it out would abandon a valid reply and accumulate duplicate work.
    const kernel = window.google?.colab?.kernel;
    if (!kernel?.invokeFunction) throw new Error('Kernel not connected yet');
    const result = await kernel.invokeFunction(config.callback, [req.crop, req.width, req.height, encoding], {});
    const data = result.data['application/json'];
    if (!/^data:image\/(png|webp);base64,/.test(data?.image || '')) throw new Error('No KLayout image');
    const next = new Image(); next.src = data.image;
    try { await next.decode(); }
    catch (error) {
      if (data.image.startsWith('data:image/webp;')) encoding = 'png';
      throw error;
    }
    if (!root.isConnected) return;
    // Every crop carries its own physical box, so even a stale reply stays aligned.
    remember(next, data);
    const latest = requested !== revision ? cachedCrop(request(false)) : null;
    tile = latest ? latest.image : next; imageBox = latest ? latest.box : data.box;
    liveRenders++; served = latest ? revision : requested;
    failures = 0; retryAt = 0; paint();
  } catch (error) {
    failures++;
    retryAt = performance.now() + retryDelay(failures);
  } finally {
    pending = false; state();
    if (root.isConnected && live) {
      if (requested !== revision || failures) schedule();
      else if (!sharp) refine();
    }
  }
}
function changed() {
  revision++; changedAt = performance.now();
  const cached = cachedCrop(request(false));
  if (cached) { tile = cached.image; imageBox = cached.box; served = revision; }
  paint(); state(); schedule();
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
  remember(overview, {box:config.box, width:overview.naturalWidth, height:overview.naturalHeight});
  paint(); state(); if (live) schedule();
  new ResizeObserver(() => { if (root.isConnected) changed(); }).observe(viewport);
}
if (overview.complete) start(); else overview.onload = start;
'''
