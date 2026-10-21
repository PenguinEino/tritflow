# VIEWER_SPEED status

2026-10-21. Implementation and measurements complete in `~/code-a-chip-viewer`.
No commits, pushes, sign-ins, publishing, or changes to other worktrees.

## Scope and decisions

Read AGENTS.md, docs/concept.md, docs/interfaces.md and briefs/VIEWER_SPEED.md.
Reviewed and continued the interrupted implementation rather than replacing it.
Only `tritflow/viz/_gds_viewer.py`, tests under `tests/viz/`, and this status
file were edited. Generated layouts/results live under ignored `build/`.
Pinned PDK: `TR1UM_PDK=~/pdk/TR-1um-pinned`; no recorded simulation,
extraction, routing, cell-library, or PDK inputs were edited.

The main scheduling defect was a 50 ms debounce reset on every pointer event:
continuous motion could postpone the first real render until motion stopped.
A single slow callback could then be followed by an unnecessary sharp request,
even on a 1x display. The old quick pass rendered 25% extra on every edge,
or 2.25 times the viewport area, on every interaction.

Changes:

- Quick requests use a leading throttle (at most one start per 32 ms), without
  postponing an existing earlier timer. Events during a callback coalesce into
  the latest box. Dragging and wheel input keep requesting actual KLayout pixels.
- Quick pass uses the visible viewport at one pixel per CSS pixel. The sharp
  pass runs only for higher-resolution displays, after 120 ms idle; renewed
  input downgrades a scheduled sharp pass to quick. A 1x display needs one
  callback per uncached view instead of two.
- Live images use Pillow's lossless WebP, method 0, preserving every metal/poly
  edge, layer colour and stipple. The initial embedded overview remains PNG.
  Server keeps PNG if WebP is unavailable, fails, or is larger; browser decode
  failure switches subsequent requests to PNG through the normal retry path.
  Existing three-argument callback calls still return PNG.
- Reuse the warm LayoutView with an explicit physical target box. Removed
  redundant `resize` and `zoom_box` calls. Static rendering and styling remain
  KLayout with the pinned PDK's TR-1um.lyp.
- Browser keeps up to eight crops / 16 MiB of decoded RGBA pixels, plus the
  current image and overview. Cached views need sufficient sampling and must
  agree on the 1 mm label threshold. Labelled crops require the same pixel
  scale, so cache reuse does not resize KLayout's fixed-size text. Fit and
  revisiting a cached box can finish without a kernel request. Canvas backing
  store is reallocated only when dimensions change, and obeys kernel limits.
- Kernel cache includes encoding in its key; still capped at six crops / 16 MiB
  encoded data per session and eight LayoutViews. Evicted sessions close their
  views, release image caches and unregister callbacks when supported. Callback
  closures look up sessions by name rather than retaining expired renderers.
- A slow queued request is never timed out or duplicated. Rejected requests use
  0.5/1/2/4/8/10 s capped backoff that pointer input cannot reset. Replies retain
  their physical boxes; an old reply cannot replace a cached current Fit view.
  Cached views report no unserved work even after a prior transport failure.

Controls, keyboard access, GDS download, layer legend, micrometre coordinates,
scale bar and the standalone static overview are preserved. No runtime
packages added. Installed **quickjs 1.19.4** locally as an optional development
test dependency using the authorized pip flags; no repository dependency or
notebook setup changes.

## Before/after measurements

Baseline: `_gds_viewer.py` at `fd1069bb5383fc10bee4a7e17eabbe2f0fed5e7e`.
Reused the interrupted run's generated `build/full_add/full_add.gds` (16 cells,
876 × 702 µm die) and `build/alu/alu.gds` (64 cells, 1692 × 1590 µm die).
Nine repetitions after warming imports/renderer/encoder, clearing only the
crop cache before each request; median includes rendering, encoding, base64
and the IPython JSON response wrapper. Views use a centred 70% crop of the
isotropic die box. No simulated transport delay is included. JSON byte counts
use `len(json.dumps(response).encode())`, excluding transport framing.

Local: Python 3.12.3, aarch64, KLayout 0.30.6, Pillow 10.2.0.
Colab: CPU Standard VM, Python 3.13.16, x86_64, KLayout 0.30.6; callback
registered with `output.register_callback` and called through Colab's Python
`_invoke_function` dispatcher, not through a browser. Its PDK layer-properties
file and the two GDS files were copied from this pinned local environment.

| Layout | Pass | Before px | After px | Local ms before → after | Colab ms before → after | JSON bytes before → after |
|---|---|---|---|---|---|---|
| full_add | quick | 1050×735 | 700×490 | 22.439 → 21.447 | 103.815 → 64.291 | 120,262 → 33,759 |
| alu | quick | 1050×735 | 700×490 | 27.473 → 25.095 | 79.452 → 72.132 | 130,241 → 37,357 |
| full_add | sharp | 1400×980 | 1400×980 | 36.087 → 62.169 | 114.874 → 186.632 | 197,431 → 78,388 |
| alu | sharp | 1400×980 | 1400×980 | 47.677 → 78.535 | 142.958 → 229.956 | 252,785 → 99,654 |

Quick payloads are 71.9% / 71.3% smaller. Sharp payloads are 60.3% / 60.6%
smaller, at a CPU cost: WebP needs an additional PNG decode and encode. For a
CPU-only comparison, new 700×490 PNG takes 13.137 / 15.546 ms locally and
40.858 / 68.058 ms in Colab, returning 71,326 / 83,720 JSON bytes. WebP is a
payload tradeoff, not an across-the-board CPU speedup. Browser-to-kernel
transfer would need to save roughly 24 / 4 ms on these quick responses to
beat viewport PNG on this VM; frontend timing is needed to establish that.
Exact kernel cache hits take 0.002–0.003 ms locally and 0.021–0.042 ms in Colab,
but still incur a round trip. Browser cache hits avoid that round trip.

These figures measure callback work, **not end-to-end interactive latency**.
The headless CLI cannot measure a human drag, notebook iframe decoding, network
latency or Colab queue/transport overhead. No claim of an observed browser
speedup or a particular frames-per-second rate is made.

The dedicated `vsSpeed1021` session left by the interrupted run was reused,
then stopped with `colab stop -s vsSpeed1021` (reported `Session terminated`).
Other Colab sessions were left alone. Raw measurements are in ignored
`build/viewer-speed/{local,colab,tiles}.json`; the tables here are the durable
review record.

## Alternatives evaluated

Encoding trials from the interrupted run were reviewed. At 700×490 for the
full adder (9 exact colours), KLayout PNG was 51,561 bytes; lossless palette PNG
27,688 bytes (+6.74 ms encode); lossless WebP 20,806 bytes (+5.49 ms encode).
Lossy WebP quality 85 was 184,592 bytes (+13.57 ms, maximum channel error 217),
and JPEG quality 90 / no chroma subsampling was 367,287 bytes (+1.41 ms,
maximum channel error 48). The stipples punish lossy compression. ALU and
larger images showed the same ordering. Palette PNG is lossless but slower
and larger than lossless WebP here. PixelBuffer has individual pixel access
and PNG export, but no bulk raw-pixel export in KLayout 0.30.6; a Python
per-pixel copy would add substantial work, so the intermediate PNG remains.

Fixed-grid tiling was measured separately at 256×256, one CSS pixel per pixel,
on a 35% zoom view. Labels were controlled by the complete view's threshold,
not each tile's span. Six aligned tiles cover a 700×490 viewport; this is an
optimistic case, because an arbitrary alignment may need more tiles.

| Layout | Viewport ms / JSON bytes | Six new tiles ms / JSON bytes | Two new tiles for a one-column pan ms / JSON bytes |
|---|---|---|---|
| full_add | 16.507 / 21,313 | 19.842 / 28,938 | 4.896 / 5,145 |
| alu | 21.413 / 30,361 | 26.506 / 38,810 | 8.347 / 13,436 |

Tiles help a sustained pan at one fixed scale, but add 20–24% CPU and 28–36%
payload on the first frame and every new zoom level. They also need explicit
viewport-wide text visibility and font/stipple seam qualification. Kept crops
for the first-image goal, with bounded browser reuse. Neighbour/zoom prefetch
and multiple simultaneous callbacks were not enabled: they add speculative
work behind notebook cells and cannot overtake the kernel's serialized work.
There is at most one outstanding callback to coalesce obsolete views safely.

Transport remains base64 in the JSON MIME response. Checked Colab's
[callback implementation](https://github.com/googlecolab/colabtools/blob/main/google/colab/output/_js.py)
and [output-area implementation](https://github.com/googlecolab/colabtools/blob/main/google/colab/output/_area.py).
`invokeFunction` dispatches JSON arguments to a callback; output areas redirect
MIME output and do not provide an independent byte transport. On the actual
VM, formatting raw `bytes` produced `text/plain` with a Python bytes repr.
An image MIME result would still be base64, saving only the small JSON metadata.
No measured lower-latency comm path was available without additional frontend
integration; retained the supported self-contained callback path.

## Verification

`python3 -m pytest tests/viz -q`: **79 passed** (including ten executed
JavaScript behavior tests). The JS tests use QuickJS with a deterministic DOM,
fake clock, image decode and a held Colab queue. They exercise continuous
wheel/drag input, latest-box coalescing, a 180-second busy kernel, backoff under
continued input, 1x/2x refinement, cache eviction, fixed-size labels, cached Fit
while pending/after failure, decode fallback, static output and detached output.
Python tests check physical crop coordinates and PDK colours, pixel-exact
WebP, cache keys/byte limits/LRU, expired-session cleanup, PNG fallback and
unchanged notebook usage/download.

`python3 -m pytest submission/tests/test_gds_viewer.py -q`: **2 passed**.

Additionally compared three different real hierarchical crops of each measured
GDS against baseline PNG: new WebP decoded pixels were identical in all six
comparisons. `git diff --check` passes.

The whole `python3 -m pytest tests/ -q` run finished: **771 passed, 2 skipped
in 545.78 s**. It collected before the final five viewer regressions and the
last JavaScript fixes were added; those final changes are covered by the
subsequent **79-passing-test** visualization run above. No unrelated failures
were found, and no out-of-scope fixes were needed.

Reproduce tests and measurements (save the baseline before integration):

```sh
python3 -m pip install --user --break-system-packages quickjs==1.19.4
python3 -m pytest tests/viz -q
git show fd1069bb5383fc10bee4a7e17eabbe2f0fed5e7e:tritflow/viz/_gds_viewer.py > /tmp/viewer_before.py
PYTHONPATH=. TR1UM_PDK=~/pdk/TR-1um-pinned python3 tests/viz/benchmark_gds_viewer.py --baseline /tmp/viewer_before.py
PYTHONPATH=. TR1UM_PDK=~/pdk/TR-1um-pinned python3 tests/viz/benchmark_gds_viewer.py --tiles
```

## Remaining limitations / blockers

No implementation blocker. Colab's serialized busy-kernel queue and network
round trip remain outside renderer control. New, uncached views necessarily
show aligned existing pixels until their reply arrives; the scheduler now
keeps real renders flowing during interaction instead of waiting for it to end.
Lossless WebP reduces transfer volume but adds encoding CPU, especially for
the high-DPI refinement. Actual frontend latency should be observed in the
integrator's next interactive Colab session.

## Interface requests

None. `gds_viewer` and its public arguments are unchanged.
