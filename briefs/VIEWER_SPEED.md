# Brief: VIEWER_SPEED — make the KLayout GDS viewer feel instant in Colab

Work in the git worktree `~/code-a-chip-viewer` (branch `viewer-speed`). Never touch `~/code-a-chip`,
`~/code-a-chip-rewrite` or other worktrees. No git commit or push: the integrator reviews and commits.

## The problem

`tritflow/viz/_gds_viewer.py` (used through `tritflow.viz.layout.gds_viewer`) shows a GDS in a notebook.
A real KLayout `LayoutView` lives in the kernel; the browser shows an overview PNG and, after each pan or
zoom, asks the kernel (Colab `google.colab.kernel.invokeFunction` → `output.register_callback`) for a new
PNG of the visible box. The author likes its look and feel (KLayout rendering with the PDK's TR-1um.lyp,
fixed-size labels, wheel/drag/double-click, download button) and wants to keep rendering in KLayout on
the kernel. But after moving or zooming, the sharp image still arrives far too late. A browser-side SVG
renderer was tried and rejected: keep KLayout.

Measured locally: one KLayout render of a 16-cell layout takes 0.02–0.05 s (700×490 to 2000×1400 px) and
the PNG is 66–260 KB. So the time goes mostly to the Colab round trip, payload size/encoding, and how the
JavaScript schedules requests. The current JS already does: one request at a time, renders while
dragging, a quick pass at 1 CSS px with a 25 % margin, then a sharp pass after 200 ms idle.

## Goal

After a pan or zoom, a correct image (at least the quick pass) should appear as fast as Colab allows,
and continuous drags/wheel zooms should keep showing real KLayout pixels rather than a stretched old
image. Keep: KLayout rendering in the kernel, appearance, controls, the download button, the static
fallback outside Colab, the busy-kernel retry behaviour (no abandoned requests, backoff), bounded memory.

## Ideas to evaluate (measure, then keep what helps)

- Payload: JPEG/WebP via Pillow (`PixelBuffer.to_png_data` → PIL) at a quality that keeps thin lines
  legible; fewer colours; smaller quick-pass size. Measure bytes and encode time.
- Transport: base64-in-JSON over `invokeFunction` vs alternatives Colab supports (e.g. returning bytes,
  `google.colab.output` channels, a comm). Keep it within what works in Colab without extensions.
- Tiling: a fixed tile grid per zoom level (pyramid) cached in the browser and in the kernel, so pans reuse
  tiles and only new tiles are requested; prefetch neighbours and the next zoom level when idle; several
  small requests in flight vs one.
- Server: keep the LayoutView warm, avoid redundant `resize`/`zoom_box`, cache by tile key, render the
  quick pass at lower resolution, text visibility handling (`_gds_text_visibility`).
- Scheduling: shortest delay that does not flood the kernel; cancel/skip stale requests on the kernel side.

## How to measure

- Locally: time kernel-side work per request (render + encode + base64) and payload sizes for
  `build/full_add/full_add.gds` (create it with `python3 -m tritflow ...` or `tritflow.flow` on
  `examples/full_add.tv` if missing) and for a larger layout (e.g. `examples/alu.tv` through
  `tritflow.flow` place_and_route). Report a table before/after.
- Colab: you may use the `colab` CLI (`colab new -s vsNAME`, `colab exec -s vsNAME -f notebook.ipynb`,
  `colab stop -s vsNAME`; always stop sessions you start; never sign in or change auth). A headless run
  cannot drag a mouse, but you can time the kernel callback itself in the Colab VM (register the callback
  and call the Python function directly) and the size of what it returns. Explain what you could and could
  not measure.
- Keep `tests/viz/test_layout_viewer.py` passing; update assertions that pin the old JS where behaviour
  intentionally changes, and add tests for new behaviour (tile keys, cache bounds, encoding, fallback).
  Run `python3 -m pytest tests/viz -q` and the whole `tests/` if time allows.

## Constraints

- TR1UM_PDK=~/pdk/TR-1um-pinned. Do not edit recorded-result inputs: `tritflow/sim/*`, `tritflow/pnr/*`,
  `tritflow/extract/*`, `cells/out/*`. Edit `tritflow/viz/_gds_viewer.py`, `tritflow/viz/layout.py`
  (viewer parts only), tests under `tests/viz/`, and add new modules if needed.
- No new runtime dependency unless it is already installed by `notebook/setup_colab.py` (Pillow and numpy
  are available). No network services, no publishing, no sign-in.
- Write `docs/status/VIEWER_SPEED.md`: what you measured, what you changed and why, before/after numbers,
  what remains slow and why.
