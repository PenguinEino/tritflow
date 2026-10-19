# VIEWER status

2026-10-19. Implementation and targeted real-Colab qualification complete.
No commits, pushes, new project dependencies or edits to PIN setup/runtime/evidence files.

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
  cached per viewer, eight retained LayoutViews. Expired viewers switch to static.
- While rendering, the previous tile scales immediately over the embedded
  overview. Returned tiles retain their own physical box, so stale replies stay
  aligned. Two failed callbacks switch to static mode.
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

## Integration limitations / blockers

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
