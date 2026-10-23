# VISUAL — saved notebook output audit

2026-10-24 JST. **Done: complete visual review; 10 visible defect groups below.**
In progress: none. Blockers: none. Fixes are handed to the owning streams; this brief is report-only.

## Scope and decisions

- Used the existing `notebook/v3/tritflow_ja_output.ipynb` and `tritflow_en_output.ipynb` unchanged. Neither notebook needed a build.
- Rendered all 25 output-bearing code cells in each language at both 1140 and 800 CSS px: **100 base screenshots**, covering 80 Japanese and 81 English output records at each width. Cells with no saved output (`c3`, `c22`, `c25`, `c28`, `c32`, `c58`) have nothing to render.
- Used local headless Chrome 152.0.7977.64, device scale factor 1, a white output surface with 8 px padding, and the saved outputs' own CSS. Replayed HTML with its JavaScript active; decoded image MIME outputs as images; retained text streams. Waited for fonts, images, and Plotly before capture. Each page contains all outputs of one code cell in their saved order. This reproduces the output area, without Colab's surrounding editor chrome.
- Opened and visually inspected every base screenshot and all 72 supplemental screenshots of changed controls or expanded panels. Tall outputs were also inspected in sections and at their footers. DOM measurements helped locate problems; only problems visible in screenshots are listed.
- The GDS browser controls operated on their embedded overview images. Kernel-backed rerasterization requires a live Colab session and was outside this local replay. No Colab VM was opened. All local audit browsers were closed.
- No production code, notebook, data, dependency, or git-state changes. No packages installed, commits, or pushes. Temporary browser/rendering files were removed; screenshots remain under `notebook/v3/.work/visual/`.

Input SHA-256:

| Notebook | SHA-256 |
| --- | --- |
| Japanese | `6cca7f25478bf5345bbe16dfd9f8cef3e5c65912cd2e1194c827d52f54132e3e` |
| English | `7bcdaa37b402ea09f3448ef0c636c85b80793152f65a0d32d5c6a788aa8925d9` |

## Visible defects

**V01 — Scaling chart extends beyond the output.** Cell `c56`, §6-3, ja/en, **800 px**.
The right-hand settling-time plot is cut off after N=8; N=16 and the right side of the toolbar are outside the viewport. The chart remains 940 px wide; document width is 948 px.
Evidence: [ja-c56-800.png](../../notebook/v3/.work/visual/ja-c56-800.png), [en-c56-800.png](../../notebook/v3/.work/visual/en-c56-800.png).
Smallest fix: `notebook/scale_views.py::scaling_figure` — remove the explicit `width=940` and let the figure size to the output container. Verify both subplot labels still fit at 800 px.

**V02 — Table columns require horizontal scrolling and are clipped initially.** Cell `c54`, §6-2, **en/800 px**; cell `c56`, §6-3, **ja/en/800 px**.
The power table cuts the “Hold time” heading and values. The timing table cuts the trailing percentage/STA-error columns (more columns are hidden in Japanese). The visible table boundaries cut through text.
Evidence: [en-c54-800.png](../../notebook/v3/.work/visual/en-c54-800.png), [ja-c56-800.png](../../notebook/v3/.work/visual/ja-c56-800.png), [en-c56-800.png](../../notebook/v3/.work/visual/en-c56-800.png).
Smallest fix: `notebook/scale_views.py::_table` — allow heading wrapping and reduce horizontal cell padding at narrow widths, instead of applying `white-space:nowrap` to every heading and data cell.

**V03 — Gate schematics lose their output side at 800 px.** Cells `c5` (§1-2), `c23` (§3-2), `c26` (§3-4), `c30` (§3-6), **ja/en/800 px**.
The first circuit's final INV/output `y`, the full adder's `sum`/`cout`, the multiplier's final gate/output `p`, and the selection circuits' output side are outside the initial drawing viewport. They require horizontal scrolling. The drawing viewport is approximately 784 px but the SVG minimum is 992–1000 px.
Evidence: [en-c5-800.png](../../notebook/v3/.work/visual/en-c5-800.png), [en-c23-800.png](../../notebook/v3/.work/visual/en-c23-800.png), [en-c26-800.png](../../notebook/v3/.work/visual/en-c26-800.png), [en-c30-800.png](../../notebook/v3/.work/visual/en-c30-800.png). Japanese counterparts are linked in the coverage table.
Smallest fix: `notebook/views.py::bus_picker` — remove the forced 992–1000 px minimum for compact drawings so they can fit the output. Handle the dense lower `c30` drawing separately as in V04; uniformly shrinking that drawing would worsen its unreadable labels.

**V04 — Labels in the 32-cell selection diagram are unreadable.** Cell `c30`, §3-6, lower `op ? a : b` diagram, **ja/en, both widths**.
Gate identifiers and port labels shrink to only about 4–6 px high. The upper 11-cell diagram remains legible, making the lower drawing's loss of text especially clear.
Evidence: [ja-c30-1140.png](../../notebook/v3/.work/visual/ja-c30-1140.png), [en-c30-800.png](../../notebook/v3/.work/visual/en-c30-800.png).
Smallest fix: `notebook/views.py::bus_picker` — preserve the detailed SVG's intended display width/text scale instead of overriding it with `width:100%` and a capped minimum. `tritflow/schematic/render.py::render` already supplies a larger display width for detailed scenes. The existing local scroll viewport can retain that readable scale; the resulting horizontal-scroll tradeoff should remain explicit.

**V05 — GDS power labels overlap.** Cell `c9`, §1-4, **ja/en, both widths**.
At the top of the first GDS, the white VDD/VMID/VSS labels run into one another. Blue VMID/VSS labels also overlap near the lower cell row.
Evidence: [en-c9-1140.png](../../notebook/v3/.work/visual/en-c9-1140.png), [ja-c9-800.png](../../notebook/v3/.work/visual/ja-c9-800.png).
Smallest fix: `tritflow/viz/layout.py::_gds_text_visibility` — suppress the dense label set at this overview scale, enabling it at a closer scale where labels separate. The present 1 mm threshold enables all labels for this roughly 554 µm-wide overview. This is a rendering change, not a change to GDS labels or connectivity.

**V06 — Settling arrowhead covers its own time label.** Cells `c45` (§5-3) and `c60` (§6-5), **ja/en/1140 px**.
The orange arrowhead overwrites the end of “227 ns” in `c45` and “218 ns” in `c60`, making the unit look truncated. This is visible in the original full screenshots, not just the enlarged crop.
Evidence: [en-c45-1140.png](../../notebook/v3/.work/visual/en-c45-1140.png), [ja-c60-1140.png](../../notebook/v3/.work/visual/ja-c60-1140.png), [enlarged c45 detail](../../notebook/v3/.work/visual/detail-settling-label.png).
Smallest fix: `notebook/views.py::scope_figure` — place the annotation text clear of the short delay arrow (using an offset/anchor, or a separate text annotation), while preserving the input-edge and settled-time endpoints.

**V07 — Completed P&R summary hides the via count.** Cell `c36`, §4-1, **en/800 px**.
The status line ends with “24.3 mm…”; the trailing “Vias: 329” is hidden. It is visible at 1140 px.
Evidence: [en-c36-800.png](../../notebook/v3/.work/visual/en-c36-800.png), [en-c36-1140.png](../../notebook/v3/.work/visual/en-c36-1140.png).
Smallest fix: `notebook/live.py::_line` — allow the completed detail text to wrap instead of clipping it with `white-space:pre`, `overflow:hidden`, and `text-overflow:ellipsis`.

**V08 — Japanese GDS viewers retain English instructions.** Cells `c9` (§1-4), `c38` (§4-2), `c60` (§6-5), `c62` (§6-6), **ja, both widths**.
Visible strings include “Static overview · rerun in Colab for live detail”, “Coordinates in µm”, “TR-1um layer legend”, and “Fit”. The surrounding notebook output is Japanese.
Evidence: [ja-c9-800.png](../../notebook/v3/.work/visual/ja-c9-800.png), [ja-c38-1140-open.png](../../notebook/v3/.work/visual/ja-c38-1140-open.png), [ja-c60-800.png](../../notebook/v3/.work/visual/ja-c60-800.png), [ja-c62-1140.png](../../notebook/v3/.work/visual/ja-c62-1140.png).
Smallest fix: `tritflow/viz/_gds_viewer.py::viewer_html` and `_SCRIPT`'s `state()` — accept the notebook language or translated labels and use them for the fixed markup and dynamic status. Layer codes/net names can retain their technical identifiers.

**V09 — Japanese reuse output contains an untranslated coverage note.** Cell `c60`, §6-5, **ja, both widths**.
The summary shows “sampled states”, followed by the English explanation beginning “Zero, rail corners, alternating signs…” and ending “Not exhaustive state/transition coverage.”
Evidence: [ja-c60-1140.png](../../notebook/v3/.work/visual/ja-c60-1140.png), [ja-c60-800.png](../../notebook/v3/.work/visual/ja-c60-800.png).
Smallest fix: `notebook/reuse.py::summary_view` and `run` — translate the display of `plan['mode']` and `note(plan['method'])`. Keep the underlying recorded stimulus-plan fields unchanged.

**V10 — Japanese shuttle output contains untranslated labels and explanation.** Cell `c62`, §6-6, **ja, both widths**.
“Submission ready”, the direction values “power/input/output”, and the final “Custom TEG pad/bond allocation and ESD/power/package approval still required” sentence remain English.
Evidence: [ja-c62-1140.png](../../notebook/v3/.work/visual/ja-c62-1140.png), [ja-c62-800.png](../../notebook/v3/.work/visual/ja-c62-800.png).
Smallest fix: `notebook/reuse.py::shuttle_view` — localize those labels and display values, including the displayed `report['reason']`. Preserve the underlying signoff result and reason.

## Validation and reproduction

All **28 Plotly figure instances** initialized across the base captures. There were **zero broken images and zero JavaScript errors**. The control audit made **384 changes across 52 cell/width/language combinations**: input radios, sizing/replay sliders, GDS zoom/pan/fit, and disclosure panels. Each produced a corresponding text, drawing, canvas, or view-box change. An additional **60 native pointer checks** passed: drag-to-zoom and double-click reset on 24 Plotly views, plus the time-range slider on all 12 waveform views (`c11`, `c45`, `c60`, both languages and widths). No unresponsive control was found in those checks. No blank/broken figure, legend obscuring data, or mojibake was seen.

Reproduce by replaying each saved cell's MIME outputs in their original order in headless Chrome at 1140 and 800 CSS px, with scripting enabled and images decoded; wait for fonts/images/Plotly, then capture the full output height. Review the base screenshots below and exercise the controls. Supplemental files use `-changed.png`, `-zoom.png`, and `-open.png`; `-partN.png`/`-footer.png` and the settling-label detail are inspection crops. A few early supplemental tall captures end at the footer boundary; the complete recaptured base images and footer crops were used to assess those footers.

There is no VISUAL pytest area and this report changes no implementation. Validation is the browser rendering/interaction audit above. Final checks confirmed both notebook hashes unchanged and all 126 report links present.

## Coverage: every saved output cell inspected

Each link is a base screenshot under `notebook/v3/.work/visual/`. Cell IDs are the notebook's stored IDs, not execution counts.

| Cell / section | ja 1140 | ja 800 | en 1140 | en 800 |
| --- | --- | --- | --- | --- |
| `c1` — Setup | [ja 1140](../../notebook/v3/.work/visual/ja-c1-1140.png) | [ja 800](../../notebook/v3/.work/visual/ja-c1-800.png) | [en 1140](../../notebook/v3/.work/visual/en-c1-1140.png) | [en 800](../../notebook/v3/.work/visual/en-c1-800.png) |
| `c5` — 1-2 Logic synthesis | [ja 1140](../../notebook/v3/.work/visual/ja-c5-1140.png) | [ja 800](../../notebook/v3/.work/visual/ja-c5-800.png) | [en 1140](../../notebook/v3/.work/visual/en-c5-1140.png) | [en 800](../../notebook/v3/.work/visual/en-c5-800.png) |
| `c7` — 1-3 Place and route | [ja 1140](../../notebook/v3/.work/visual/ja-c7-1140.png) | [ja 800](../../notebook/v3/.work/visual/ja-c7-800.png) | [en 1140](../../notebook/v3/.work/visual/en-c7-1140.png) | [en 800](../../notebook/v3/.work/visual/en-c7-800.png) |
| `c9` — 1-4 DRC and LVS | [ja 1140](../../notebook/v3/.work/visual/ja-c9-1140.png) | [ja 800](../../notebook/v3/.work/visual/ja-c9-800.png) | [en 1140](../../notebook/v3/.work/visual/en-c9-1140.png) | [en 800](../../notebook/v3/.work/visual/en-c9-800.png) |
| `c11` — 1-5 Post-layout simulation | [ja 1140](../../notebook/v3/.work/visual/ja-c11-1140.png) | [ja 800](../../notebook/v3/.work/visual/ja-c11-800.png) | [en 1140](../../notebook/v3/.work/visual/en-c11-1140.png) | [en 800](../../notebook/v3/.work/visual/en-c11-800.png) |
| `c14` — 2-1 INV DC analysis and sizing | [ja 1140](../../notebook/v3/.work/visual/ja-c14-1140.png) | [ja 800](../../notebook/v3/.work/visual/ja-c14-800.png) | [en 1140](../../notebook/v3/.work/visual/en-c14-1140.png) | [en 800](../../notebook/v3/.work/visual/en-c14-800.png) |
| `c16` — 2-2 Unary functions from NANY and the +1 constant | [ja 1140](../../notebook/v3/.work/visual/ja-c16-1140.png) | [ja 800](../../notebook/v3/.work/visual/ja-c16-800.png) | [en 1140](../../notebook/v3/.work/visual/en-c16-1140.png) | [en 800](../../notebook/v3/.work/visual/en-c16-800.png) |
| `c18` — 2-3 Cell truth tables | [ja 1140](../../notebook/v3/.work/visual/ja-c18-1140.png) | [ja 800](../../notebook/v3/.work/visual/ja-c18-800.png) | [en 1140](../../notebook/v3/.work/visual/en-c18-1140.png) | [en 800](../../notebook/v3/.work/visual/en-c18-800.png) |
| `c20` — 2-4 Standard cells | [ja 1140](../../notebook/v3/.work/visual/ja-c20-1140.png) | [ja 800](../../notebook/v3/.work/visual/ja-c20-800.png) | [en 1140](../../notebook/v3/.work/visual/en-c20-1140.png) | [en 800](../../notebook/v3/.work/visual/en-c20-800.png) |
| `c23` — 3-2 Logic synthesis | [ja 1140](../../notebook/v3/.work/visual/ja-c23-1140.png) | [ja 800](../../notebook/v3/.work/visual/ja-c23-800.png) | [en 1140](../../notebook/v3/.work/visual/en-c23-1140.png) | [en 800](../../notebook/v3/.work/visual/en-c23-800.png) |
| `c26` — 3-4 Logic synthesis | [ja 1140](../../notebook/v3/.work/visual/ja-c26-1140.png) | [ja 800](../../notebook/v3/.work/visual/ja-c26-800.png) | [en 1140](../../notebook/v3/.work/visual/en-c26-1140.png) | [en 800](../../notebook/v3/.work/visual/en-c26-800.png) |
| `c30` — 3-6 Synthesize and compare | [ja 1140](../../notebook/v3/.work/visual/ja-c30-1140.png) | [ja 800](../../notebook/v3/.work/visual/ja-c30-800.png) | [en 1140](../../notebook/v3/.work/visual/en-c30-1140.png) | [en 800](../../notebook/v3/.work/visual/en-c30-800.png) |
| `c33` — 3-8 Logic synthesis | [ja 1140](../../notebook/v3/.work/visual/ja-c33-1140.png) | [ja 800](../../notebook/v3/.work/visual/ja-c33-800.png) | [en 1140](../../notebook/v3/.work/visual/en-c33-1140.png) | [en 800](../../notebook/v3/.work/visual/en-c33-800.png) |
| `c36` — 4-1 Place and route | [ja 1140](../../notebook/v3/.work/visual/ja-c36-1140.png) | [ja 800](../../notebook/v3/.work/visual/ja-c36-800.png) | [en 1140](../../notebook/v3/.work/visual/en-c36-1140.png) | [en 800](../../notebook/v3/.work/visual/en-c36-800.png) |
| `c38` — 4-2 GDS | [ja 1140](../../notebook/v3/.work/visual/ja-c38-1140.png) | [ja 800](../../notebook/v3/.work/visual/ja-c38-800.png) | [en 1140](../../notebook/v3/.work/visual/en-c38-1140.png) | [en 800](../../notebook/v3/.work/visual/en-c38-800.png) |
| `c41` — 5-1 DRC and LVS | [ja 1140](../../notebook/v3/.work/visual/ja-c41-1140.png) | [ja 800](../../notebook/v3/.work/visual/ja-c41-800.png) | [en 1140](../../notebook/v3/.work/visual/en-c41-1140.png) | [en 800](../../notebook/v3/.work/visual/en-c41-800.png) |
| `c43` — 5-2 Extraction and wire capacitance | [ja 1140](../../notebook/v3/.work/visual/ja-c43-1140.png) | [ja 800](../../notebook/v3/.work/visual/ja-c43-800.png) | [en 1140](../../notebook/v3/.work/visual/en-c43-1140.png) | [en 800](../../notebook/v3/.work/visual/en-c43-800.png) |
| `c45` — 5-3 Post-layout simulation | [ja 1140](../../notebook/v3/.work/visual/ja-c45-1140.png) | [ja 800](../../notebook/v3/.work/visual/ja-c45-800.png) | [en 1140](../../notebook/v3/.work/visual/en-c45-1140.png) | [en 800](../../notebook/v3/.work/visual/en-c45-800.png) |
| `c47` — 5-4 INV delay table | [ja 1140](../../notebook/v3/.work/visual/ja-c47-1140.png) | [ja 800](../../notebook/v3/.work/visual/ja-c47-800.png) | [en 1140](../../notebook/v3/.work/visual/en-c47-1140.png) | [en 800](../../notebook/v3/.work/visual/en-c47-800.png) |
| `c49` — 5-5 Ternary STA and SPICE comparison | [ja 1140](../../notebook/v3/.work/visual/ja-c49-1140.png) | [ja 800](../../notebook/v3/.work/visual/ja-c49-800.png) | [en 1140](../../notebook/v3/.work/visual/en-c49-1140.png) | [en 800](../../notebook/v3/.work/visual/en-c49-800.png) |
| `c52` — 6-1 Dot-product size and area (recorded) | [ja 1140](../../notebook/v3/.work/visual/ja-c52-1140.png) | [ja 800](../../notebook/v3/.work/visual/ja-c52-800.png) | [en 1140](../../notebook/v3/.work/visual/en-c52-1140.png) | [en 800](../../notebook/v3/.work/visual/en-c52-800.png) |
| `c54` — 6-2 Static current and power (recorded) | [ja 1140](../../notebook/v3/.work/visual/ja-c54-1140.png) | [ja 800](../../notebook/v3/.work/visual/ja-c54-800.png) | [en 1140](../../notebook/v3/.work/visual/en-c54-1140.png) | [en 800](../../notebook/v3/.work/visual/en-c54-800.png) |
| `c56` — 6-3 STA and SPICE (recorded) | [ja 1140](../../notebook/v3/.work/visual/ja-c56-1140.png) | [ja 800](../../notebook/v3/.work/visual/ja-c56-800.png) | [en 1140](../../notebook/v3/.work/visual/en-c56-1140.png) | [en 800](../../notebook/v3/.work/visual/en-c56-800.png) |
| `c60` — 6-5 Run the full flow on the edited HDL | [ja 1140](../../notebook/v3/.work/visual/ja-c60-1140.png) | [ja 800](../../notebook/v3/.work/visual/ja-c60-800.png) | [en 1140](../../notebook/v3/.work/visual/en-c60-1140.png) | [en 800](../../notebook/v3/.work/visual/en-c60-800.png) |
| `c62` — 6-6 dot4 with MPW frame and pads (recorded) | [ja 1140](../../notebook/v3/.work/visual/ja-c62-1140.png) | [ja 800](../../notebook/v3/.work/visual/ja-c62-800.png) | [en 1140](../../notebook/v3/.work/visual/en-c62-1140.png) | [en 800](../../notebook/v3/.work/visual/en-c62-800.png) |

## Interface requests

No contract changes requested. FRONTEND/notebook owners can address V01–V04 and V06–V10; the GDS visualization owner can address V05 and the viewer portion of V08. These findings describe the saved notebooks with the hashes above, so a subsequent rebuild must be reviewed again to confirm a fix.
