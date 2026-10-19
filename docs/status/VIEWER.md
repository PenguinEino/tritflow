# VIEWER status

2026-10-19. Round-16 fixes implemented and qualified in a fresh real Colab runtime.
No commits, pushes, new project dependencies, or PIN/setup/evidence edits.

## Round-16 changes

- Colab mode is fixed for the lifetime of an output: a busy, disconnected or
  temporarily unavailable kernel never changes it to static mode. Local outputs
  without google.colab remain static as before.
- Keep one callback request pending while later cells execute. Removed the 15 s
  timeout/abandonment that caused round 16 to enter permanent static mode.
- Actual callback/connection errors retry indefinitely with bounded exponential
  delays: 0.5, 1, 2, 4, 8, then 10 seconds. A successful reply clears the retry
  count; interaction during a pending request queues the newest physical crop.
- While queued, disconnected or retrying, show `live: waiting for kernel…`.
  Overview pan/zoom and the last detailed tile remain usable throughout.
- KLayout text is hidden above a 1000 µm view width, restored below that threshold.
  The same policy applies to persistent live tiles, embedded fallback overviews
  and standalone `render_gds` rasters. Geometry, colours, hatches and controls stay
  unchanged. Cached tiles include their label visibility in callback metadata.

Changed this follow-up: `tritflow/viz/_gds_viewer.py`, `tritflow/viz/layout.py`,
`tests/viz/test_layout_viewer.py`, and this status file only.

## Round-16 validation

```sh
python3 -m pytest tests/viz submission/tests/test_gds_viewer.py -q
# 67 passed
python3 notebook/validate_notebook.py
# Validated 57 cells and chapters 0–9
```

Regression tests assert that generated JavaScript retains a single pending
request, has no timeout race or permanent live-to-static transition, retries with
bounded backoff, and requests the latest view after recovery. A real GDS text
fixture also verifies pixel changes when zoomed in, suppression at overview,
cache transitions, and identical static viewport pixels with/without labels.
Compilation/diff checks pass. No local packages were installed.

## Round-16 real-Colab evidence

The newly allocated runtime began with execution count 1, no imported TritFlow,
and `/content` containing only `.config` and `sample_data`. Python 3.13.16,
KLayout 0.30.6. Boot ID `b0d2c33d-0dc7-439e-8f7d-126d48514ef9`, PID 1332.
The source base was `b49e5c165446e6337513008efd933e078a8c118a` (colab-v0), with
only the final two viewer Python files overlaid. All test paths are under
`/content/tritflow-viewer-r16*`; no release or scientific evidence was rewritten.

All notebook operations used the Colab MCP bridge. Chrome was used only for its
local-MCP connection dialogs. The original bridge could not recover after an
approval timeout, so the same bridge was run through a private MCP client. A
first probe harness failed because Colab removed an inert script node; three
large HTML outputs also stalled that MCP transport. The final harness uses one
viewer per cell, records MCP results locally, and does not alter production JS.

To force the requested overlap deterministically, the harness starts the
unaltered viewer script three seconds after displaying its overview, then runs
an actual separate following cell containing `time.sleep(45)`. The routed adder
uses the real shuttle GDS's `adder4` core; chapter 9 uses the whole framed chip.
This tests the public viewer/callback path, without rerunning synthesis or SPICE.

| Observation | Measured result |
|---|---|
| Following sleep cell | 45.001364 s, observed `BUSY_START` with blank execution count before completion |
| Viewer at 37.005 s | live, waiting, zero updates; `live: waiting for kernel…` |
| Zoom requested while busy | latest crop becomes 69.613 µm wide, immediate client feedback |
| First Python render callback | 0.016133 s after following cell finished |
| Recovery at 46.134 s | live, two updates, newest zoom crop rendered without rerunning viewer cell |
| Three injected transient errors | stayed live and waiting; retries after 501 / 1001 / 2001 ms |
| Retry recovery | count reset to zero, update 3; pan preserved |
| Double-click Fit | original crop restored, update 4; labels hidden again |
| Whole-chip fit | labels false for every tile wider than 1000 µm; no overlapping pad/net labels |
| Whole-chip device zoom | labels true below 1000 µm; transistor/contact detail rendered sharply |

All final assertion checks pass. The backoff errors were injected only for the
tested viewer's callback; the 45-second busy-kernel case used unmodified real
callback transport. Other notebook work did not run during this fresh allocation.
This is a targeted reproduction of the round-16 viewer failure, not a whole-
notebook Run all reliability claim.

Actual Colab captures and machine-readable evidence:

- [Busy overview scaled during pending zoom](../../build/viewer/colab-r16/busy.png)
- [Recovered sharp adder detail](../../build/viewer/colab-r16/zoom.png)
- [Clean full-chip Fit](../../build/viewer/colab-r16/chip_fit.png)
- [Whole-chip device zoom](../../build/viewer/colab-r16/chip_zoom.png)
- [Standalone static chip overview](../../build/viewer/colab-r16/chip_static.png)
- [Probe, timing, label flags, fresh-runtime inventory and SHA-256 values](../../build/viewer/colab-r16/probe.json)

Qualified final code hashes:

- `tritflow/viz/layout.py`: `8b18d864f842286d42a96088cedaa40617ee79a55ea02f4e53662b08ac74bf65`
- `tritflow/viz/_gds_viewer.py`: `89fa6020dd7f879cad7b8bb1b1388131911d9e52a6e2f5f13d57a8da43f22606`

Local files and all five transferred screenshots match the recorded hashes.
The runtime was released with `google.colab.runtime.unassign()` after evidence
transfer. All eight cells in the final scratch test were deleted; MCP confirmed
that its original empty cell alone remains. The earlier aborted transport scratch
was not saved. No sign-in, OAuth, Save or Share operations were performed.
The prior implementation/qualification record follows for historical context;
its old code hashes and initial integration limitations do not describe this fix.

## Initial implementation record

## Done and decisions

- `tritflow.viz.layout.gds_viewer(gds_path, *, top=None, width=1000, height=700)`
  returns IPython HTML with cursor-centred wheel zoom, drag pan, double-click/Fit,
  zoom buttons, keyboard navigation, a µm scale bar/readout and PDK layer legend.
- Raster export and viewer share `_open_gds_view`: the actual GDS hierarchy,
  pinned TR-1um.lyp colours/stipples, black background and identical configuration.
- Colab retains one headless LayoutView per viewer. Debounced callbacks return
  JSON MIME data with a PNG data URL and the actual physical crop. KLayout's
  PixelBuffer supplies PNG bytes directly, without temporary tile files.
- Limits: 2048 pixels per edge, 2,000,000 pixels per tile, six tiles / 16 MiB
  cached per viewer, eight retained LayoutViews. Colab viewers keep waiting/retrying
  if a callback is unavailable; rerun an expired viewer cell to register it again.
- While rendering, the previous tile scales immediately over the embedded
  overview. Returned tiles retain their own physical box, so stale replies stay
  aligned. Busy requests remain queued; transport failures retry after
  0.5, 1, 2, 4, 8 and then 10 seconds, with no permanent static transition.
- Local Jupyter without google.colab uses client-side pan/zoom on the embedded
  high-resolution overview. With scripts disabled, the overview remains visible.
- Chapters 6, 8 and 9 use the viewer and retain GDS download buttons. Each method
  imports the public function and remains at most 14 lines.
- The submission builder recognizes `data-gds-viewer="1"`, replaces active HTML
  with its exact embedded overview as native PNG output, and rejects missing or
  malformed overview data rather than silently losing evidence.

The VIEWER brief explicitly authorizes these paths, supplementing the shared
ownership table. Pre-existing TR-1um raster styling, download-button work and PIN
builder edits were preserved; their complete diff against HEAD is not VIEWER work.
Only the three viewer method cells were updated in the generated notebook, to
avoid regenerating other streams' setup or scientific evidence during their work.

## Changed files

- `tritflow/viz/layout.py`: common LayoutView setup and public entry point.
- `tritflow/viz/_gds_viewer.py`: persistent renderer, callback/cache and inline JS.
- `tests/viz/test_layout_viewer.py`: crop, scale, PDK colours, bounds/cache,
  fallback HTML, independent callback sessions and notebook method validation.
- `notebook/methods.py`: routed/custom/shuttle methods.
- `notebook/tritflow_tr1um.ipynb`: only `method-pnr`, `method-custom_layout` and
  `method-shuttle` differ from HEAD; other cells were preserved.
- `submission/build_submission.py`: new viewer converter and dispatch branch.
- `submission/tests/test_gds_viewer.py`: exact PNG preservation and rejection tests.
- `docs/status/VIEWER.md`: this report.

## Validation

```sh
python3 -m pytest tests/viz submission/tests/test_gds_viewer.py -q
# 65 passed
python3 -m pytest tests/viz submission/tests -q \
  -k 'not actual_payload_has_readable_embedded_evidence'
# 74 passed, 1 deselected
python3 notebook/validate_notebook.py
# Validated 57 cells and chapters 0–9
```

Python compilation and `git diff --check` on the edited implementation paths pass.
No local packages were installed.

## Real Colab

Used the COLABMCP connect/approval loop. Chrome was used only to approve this
stream's local-MCP connection dialog. All notebook operations, JavaScript probes
and canvas captures used Colab MCP.

- Base checkout: `839adbf19f7590221d18d171adaaddb95c8fd27a` (`colab-v0`),
  `/content/tritflow-viewer`, with the two viewer Python files overlaid unpublished.
- Python 3.13.16, KLayout 0.30.6, public TR-1um.lyp at 5d963db. KLayout was installed
  only into `/content/tritflow-viewer-deps`; LYP is under `/content/tritflow-viewer-pdk`.
- The separate scratch tab shared an existing warm Python kernel. After discovering
  this, VIEWER used the dedicated `tritflow_viewer` package alias and LYP resolver.
  The existing kernel PDK path was restored to
  `/content/tritflow-pin-runtime/TR-1um-5d963db9d44e192d37a0489c208bfccf2e2f690c`.
  Subsequent tests used dedicated filesystem paths, imports and callbacks.
- On the actual shuttle GDS, four cursor-centred wheel events reduced width from
  3977.296 µm to 108.675 µm. The zoom capture resolves four NANY PMOS devices,
  gate poly and source/drain contacts with the real PDK colours/stipples.

| Probe | Client updates | Result |
|---|---:|---|
| Initial overview callback | 1 | live |
| Wheel zoom into PMOS group | 2 | new detailed KLayout tile |
| Right-arrow pan | 3 | shifted crop and new tile |
| Double-click Fit | 4 | original physical box restored |
| Separate callback-free viewer, `+` | 0 | static; client crop shrinks correctly |

The probe schedules JS after its executing Python cell returns: Colab callback
requests otherwise wait behind `output.eval_js` while the kernel is busy. This
resolved an initial probe deadlock without a product workaround. The first import
attempt also exposed the preloaded PIN package; the dedicated import alias resolved
it. A final digest check caught an older test overlay, which was replaced and all
interaction assertions repeated against the exact final code. Final assertions
passed without errors; local code and screenshot SHA-256 values match the record.

Screenshots are actual Colab canvas captures, not locally rendered substitutes:

- [Shuttle overview](../../build/viewer/colab/initial.png), SHA-256
  `b91f1c916c1f7c50560d259ed9c69e835d751f85ff8285ff797649255a3a739a`.
- [PMOS detail](../../build/viewer/colab/zoom.png), SHA-256
  `2a82c8af0e41837e4dd8ad80204881b196216d855cd9d0adc2eabf443d89457b`.
- [Probe boxes, versions and qualified patch hashes](../../build/viewer/colab/probe.json).

Qualified code SHA-256:

- `tritflow/viz/layout.py`:
  `c38951936bd6d9caee93de4f74e1526a6db9d49d2305728129b18e1019179a76`
- `tritflow/viz/_gds_viewer.py`:
  `ded118c1dc7ea005c86be8732e72d7ac24fa785ac750a13a67be834750d99db0`

All five cells added during VIEWER testing were deleted; the original empty
scratch cell was preserved. This is targeted interactive qualification in a warm
kernel, not a fresh-VM Run all claim or qualification of the unreleased whole tree.

## Initial implementation integration limitations

No viewer implementation blockers remain. Broader notebook/publication checks
cannot currently pass while other streams update the shared scientific inputs:

- The generator reproducibility test and two editorial context tests reject changed
  `cells/out/BUF/BUF.char.json` against the old paper evidence.
- The existing Colab publication-note test finds commit
  `0ffe7a12c34738664e9e788853d87edc9da5b7ec` absent from its named report.
- `submission/tests/test_packaging.py::test_actual_payload_has_readable_embedded_evidence`
  rejects the existing saved payload because `method-pnr` now differs from source.
  Its execution evidence was not relabelled or rewritten to hide this mismatch.

## Interface requests

After PIN publishes its scientific inputs, the integrator should refresh the
paper/Colab evidence as appropriate, regenerate the notebook from its source and
execute `submission/build_submission.py` to capture a matching static payload.
The converter and its tests are ready; the existing payload needs new execution
before it can be declared current. These release/evidence operations remain with
their owning streams.
