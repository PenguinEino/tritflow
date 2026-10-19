# VIEWER brief: interactive, real-KLayout GDS viewer in the notebook

User request (2026-10-19): zoom and pan the GDS in real time, looking exactly like opening it in KLayout with
the TR-1um technology (tritflow/viz/layout.py render_gds already uses the PDK's TR-1um.lyp, black background).

Design (no web server, no new dependencies, no CDN):
- A new function, e.g. tritflow/viz/layout.py `gds_viewer(gds_path, *, top=None, width=1000, height=700)`, that
  returns an IPython HTML object: an inline, self-written JS viewer (mouse wheel zoom about the cursor, drag to
  pan, double-click / button to fit, a µm scale bar and a coordinate readout, a small layer legend from the lyp).
- Live mode (Colab): on view change (debounced), JS calls a Python callback registered with
  `google.colab.output.register_callback` (via `google.colab.kernel.invokeFunction`) passing the visible box in
  µm and the pixel size; Python renders exactly that box with KLayout LayoutView (same lyp/config as render_gds:
  zoom_box on a persistent LayoutView, save_image to memory/bytes) and returns a PNG data URL. Keep one
  LayoutView per viewer, cache recent tiles, and bound render size. While a render is pending, show the previous
  image scaled (instant feedback).
- Static fallback (no kernel callback, e.g. saved/exported notebook, local Jupyter): embed one high-quality
  overview render and do client-side zoom/pan on it.
- Local Jupyter without google.colab: fall back cleanly to static mode (no errors).
Use it in the notebook method cells for chapter 6 (routed adder), chapter 8 (your circuit) and chapter 9 (shuttle
chip, from notebook/assets/chip/adder4/tr_1um_adder4.gds): replace the static `display(Image(...render_gds...))`
with the viewer while keeping method cells short (notebook/methods.py; ≤14 lines each). Keep gds_download buttons.
The submission builder (submission/build_submission.py) must still produce readable static output: make it
replace the viewer's HTML with its embedded overview PNG (add a marker attribute like data-gds-viewer="1").
Tests: unit tests for the render-box callback (correct crop/scale, lyp colours present), the HTML (marker,
fallback image), and that notebook validation still passes. Verify in real Colab with the COLABMCP loop
(briefs/COLABMCP.md; session isolation): zoom into a cell until transistors are visible and confirm live re-render.
Coordinate: the PIN stream is concurrently editing setup/runtime/evidence files; do not touch those. Do not
commit; report changed files and screenshots in docs/status/VIEWER.md.
