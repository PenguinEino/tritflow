# COLAB — round 9, 2026-10-19 JST

**PASS on the FIRST Run all: all 35 code cells completed in 384.4 s including setup (6 min 24.4 s).** Exactly one Run all; no retry, restart, individual-cell rerun or uncaught traceback. All **57 cells (35 code, 22 text)** recorded.

Printed source: **`7b62e63f9f75acfa5f935c8da58a77a9db42e0cc`**, ref `colab-v0`. Recoloured Fig. 2 and redrawn schematics render. Routing and branch/crossing markers are clear. **The flat chapter-5 half-adder is oversized and requires horizontal and vertical output scrolling; compact schematic legends are still small.** Runtime deleted after capture.

## Environment and procedure

- Freshly reloaded the [target Colab URL](https://colab.research.google.com/github/PenguinEino/tritflow/blob/colab-v0/notebook/tritflow_tr1um.ipynb) through the installed Chrome browser runtime using `node_repl`, the same extension-backed Chrome surface as round 8. UI actions used its documented accessibility API and screenshots.
- Colab reattached an existing runtime during reload. Deleted it at **04:28:42 JST**, verified Reconnect, then inspected **Python 3 / CPU selected / latest recommended**. Canceled settings without saving and connected a new free Google Compute Engine runtime (**12.67 GB RAM**).
- Exactly one **Runtime → Run all at 04:29:30 JST**. Accepted the authorized GitHub warning at **04:29:39**. The queue continued after setup automatically.
- Setup gutter **1 min**, imports **2 s**. Final printed total **384.4 s including setup**. Completion observed at **04:36:30 JST**; this observation includes polling delay.
- Printed **KLayout 0.30.6**, `/usr/bin/klayout`; **ngspice-42**, `/usr/bin/ngspice`, KLU Direct Linear Solver.
- Host packages preserved: **NumPy 2.1.3, SciPy 1.16.3, Matplotlib 3.10.0, Plotly 5.24.1**.
- Runtime → Disconnect and delete runtime → Yes at **04:38:50 JST**; verified **Reconnect** afterward.
- No credentials, sign-in, OAuth, account changes, notebook saving/sharing, paid upgrade or source editing. No manual circuit change, local package installation, code change or git write. Only COLAB-owned paths written.

## Every cell

Zero-based indices. Execution counts **1–35** come from this single fresh run. Times are Colab's displayed rounded gutter values; `0 s` is rounded, not zero work. Text cells render without execution time.

| Cell | Execution | Purpose | Result | Wall time |
|---|---|---|---|---|
| 0 | — | TritFlow: balanced-ternary HDL to GDS on OpenSUSI TR-1um | Rendered | — |
| 1 | 1 | Setup (collapsed form) | PASS | 1 min |
| 2 | 2 | Imports and run bookkeeping | PASS | 2 s |
| 3 | — | From HDL to a checked adder layout; highlighted adder.tv definition | Rendered | — |
| 4 | 3 | Chapter 0 inputs: test conditions and an independent integer oracle | PASS | 0 s |
| 5 | 4 | Chapter 0 public API: HDL → GDS → extracted SPICE | PASS | 2 min |
| 6 | 5 | Chapter 0 checks | PASS | 0 s |
| 7 | — | Three levels from ordinary CMOS | Rendered | — |
| 8 | — | Chapter 1 highlighted TritVerilog definition: examples/gates.tv | Rendered | — |
| 9 | 6 | Chapter 1 public API: gates and DC | PASS | 0 s |
| 10 | 7 | Chapter 1 checks and the taped-out INV schematic | PASS | 0 s |
| 11 | — | Sizing sets the middle level | Rendered | — |
| 12 | 8 | Chapter 2 public API: sizing slider | PASS | 4 s |
| 13 | 9 | Chapter 2 details: resistor-length candidates at the taped-out MOS sizes | PASS | 0 s |
| 14 | — | Taped-out circuits become placeable cells | Rendered | — |
| 15 | 10 | Chapter 3 public API: cell view | PASS | 0 s |
| 16 | 11 | Chapter 3 checks: template, clamp devices and cell qualification | PASS | 0 s |
| 17 | — | Describe signed arithmetic in TritVerilog | Rendered | — |
| 18 | — | Chapter 4 highlighted half_add.tv and full_add.tv definitions | Rendered | — |
| 19 | 12 | Chapter 4 public API: arithmetic | PASS | 0 s |
| 20 | 13 | Chapter 4 checks: cell counts against the taped-out schematics | PASS | 0 s |
| 21 | — | Follow an expression into cells | Rendered | — |
| 22 | 14 | Chapter 5 public API: synthesis graph | PASS | 1 s |
| 23 | 15 | Chapter 5 checks: mapping rules and gate-level TritVerilog | PASS | 0 s |
| 24 | 16 | Chapter 5 public API: mapped schematics | PASS | 0 s |
| 25 | — | Route signals and feed the standing current | Rendered | — |
| 26 | 17 | Chapter 6 public API: P&R view | PASS | 1 s |
| 27 | 18 | Chapter 6 details and an optional floorplan experiment | PASS | 0 s |
| 28 | — | Does the layout still work? | Rendered | — |
| 29 | 19 | Chapter 7 public API: device-only SPICE and wire overlay | PASS | 2 min |
| 30 | 20 | Chapter 7 checks: identical devices with and without wire C | PASS | 0 s |
| 31 | — | Chapter 7 scaling and power evidence | Rendered | — |
| 32 | 21 | Chapter 7 recorded width and load campaigns | PASS | 0 s |
| 33 | — | Predict with static timing, confirm with SPICE | Rendered | — |
| 34 | 22 | Chapter 7 public API: STA vs SPICE | PASS | 0 s |
| 35 | 23 | Chapter 7 STA comparison table and critical path | PASS | 0 s |
| 36 | — | STA validation figure and scope | Rendered | — |
| 37 | — | Change the circuit and close the loop | Rendered | — |
| 38 | 24 | Chapter 8 editable formatted TritVerilog source definition | PASS | 0 s |
| 39 | 25 | Chapter 8 circuit selection and independent reference setup | PASS | 0 s |
| 40 | 26 | Chapter 8 synthesis / truth table | PASS | 0 s |
| 41 | 27 | Chapter 8 check: every input state against the independent arithmetic reference | PASS | 0 s |
| 42 | 28 | Chapter 8 public API: layout | PASS | 12 s |
| 43 | 29 | Chapter 8: extracted SPICE of your layout and its waveform | PASS | 29 s |
| 44 | — | Expected diagnostic introduction | Rendered | — |
| 45 | 30 | Chapter 8 expected caught HDL error | PASS; expected diagnostic caught | 0 s |
| 46 | — | Next: compare the model with silicon | Rendered | — |
| 47 | — | From your HDL to a shuttle-ready top | Rendered | — |
| 48 | 31 | Chapter 9 recorded chip image and signoff table | PASS | 0 s |
| 49 | 32 | Chapter 9 checks: recorded signoff snapshot and pad map | PASS | 0 s |
| 50 | — | Chip results and remaining submission requirements | Rendered | — |
| 51 | — | Appendix A. What the results establish | Rendered | — |
| 52 | — | Appendix B. Verification evidence and how to rerun | Rendered | — |
| 53 | 33 | Appendix B: cell characterization and fanout evidence | PASS | 0 s |
| 54 | 34 | Appendix B: four-design physical and timing campaign | PASS | 0 s |
| 55 | 35 | Appendix B: evidence tables, provenance and run time | PASS | 0 s |
| 56 | — | Appendix C. Use and extend TritFlow | Rendered | — |

Long cells: live adder **2 min**, device-only SPICE **2 min**, edited layout **12 s**, edited extracted SPICE **29 s**. Final cache table: `your-minmax: run` **29.74 s**; retained lookups mac1 **0.158 s**, adder4 **0.103 s**, full_add **0.038 s**, mul1 **0.009 s**. Public-API adder and device-only calculations run outside the cache list, so it is not a complete phase-time breakdown.

## Schematic and figure readability

Assessed at Colab's normal **1348 × 913** viewport without a viewport override or browser zoom change.

| Requested view | Observed in Colab |
|---|---|
| Fig. 2, chapter-1 hero | Entire 2 × 4 panel figure and caption fit. Purple input-axis labels and green output labels are visible; blue/grey/red input-level curves and labels remain distinct. The B-level key above each multi-input panel avoids covering the traces. No clipped axis, label collision or blank panel observed. Grey acceptance bands remain visible. |
| Chapter-5 two-trit adder | Two full-adder blocks, top a/b inputs, horizontal carry chain and lower sum ports are cleanly separated. Pin/module labels do not overlap wires or each other. The complete hierarchy fits one screen after positioning; labels are legible but smaller than notebook prose, with generous unused space to the right. The port-value legend is quite small. Screenshot 07. |
| Chapter-5 flat half-adder | Gate names and Σ/inverter symbols are large and readable; orthogonal routes, junction dots and crossing gaps are clear in the inspected regions. No overlapping label/wire collision observed. **The drawing is wider than the output pane and taller than its scrolling window.** The sum output is off the right edge in the left view; lower inverter/legend need vertical scrolling. Horizontal and vertical scrollbars appear. Screenshots 08a/08b/08c cover left/central routes, right/lower routes and legend separately. It cannot be understood at a glance in a single normal viewport. |
| Chapter-7 wire-C schematic | Complete two-block hierarchy, three device-only/post-wire times and the port/wire-C legend fit together on one screen. Wire thickness/colour shows the capacitance overlay without covering pin labels. No overlap observed. **Capacitance numbers, units and legend explanation are very small** and require close reading, despite ample whitespace on the right. Screenshot 11a. |
| Chapter-8 edited minmax schematic | Four cells, two inputs, lo/hi outputs and branch/crossing key all fit on one screen. Clear orthogonal branches, explicit junction dots and gaps at unconnected crossings. No label overlap or clipped output. Gate IDs g0–g3 and the branch/crossing key remain small, while ports and symbols are readily distinguishable. Screenshot 12. |

The half-adder is the main presentation regression/remaining issue: the new routing is clean, but its scale makes inspection cumbersome in Colab. Recommend bounding its displayed width to the notebook output width while retaining a readable minimum label size, or providing a compact overview plus a larger detail view. Increase the compact adder/wire-C legend font size independently of diagram dimensions.

The first screen remains readable and now attributes round 8 (`cf010a0`, 35 cells, 499.2 s). Miniature overview HDL/GDS text remains small. Other captured chapter figures have visible content/axes; the chip layer legend is small. Long final-table routing identifiers wrap without hiding results.

## Live results and scope

- Live adder: **32 cells, 1284 × 1038 µm, 0 DRC markers, strict LVS True, analog True**, **243 exhaustive logical states**, extracted sequence **9 selected states**.
- Device-only → wire-C SPICE settling: **sum[1] 132.1 → 149.3 ns; sum[0] 124.6 → 138.4 ns; cout 102.2 → 107.0 ns**. Printed above the wire-C schematic.
- Edited minmax: **4 cells, 384 × 366 µm**, DRC clean / LVS Match, integer reference for **9 states**, extracted sequence **9 states**, output checks **PASS**. Schematic, GDS and both waveform panels render.
- Final four-design table shows DRC/LVS `[True, True]` for all four **retained** designs, alongside source identities and visited/possible input counts.
- Chapter-9 **recorded** adder4 seed-7 snapshot: 2500 × 2500 µm, 23 pads. Drawing DRC clean/0, drawing LVS matched/strict ports, mask DRC clean/0, MPW precheck clean/exit 0. **submission_ready False**: custom TEG pad/bond allocation and ESD/power/package approval remain required. The cell reads committed JSON/PNG, not a fresh full-top build.

This pass verifies installation/runtime compatibility and uninterrupted default execution. Recorded paper, sweep, qualification, four-design and chip evidence is displayed/checked, not all freshly recomputed; it does not establish manufacturing approval.

## Errors

**No failing cell or uncaught Python traceback.** Cell 45 intentionally catches an unsupported-HDL teaching error and passes; screenshot 15 records the diagnostic:

```text
your_circuit.tv:3:14: arithmetic/comparison on trits is unsupported; use ~, &, |, nany and sized trit literals
Repair: use gates for signal arithmetic; e.g. nany(a,b) gives the negative saturated sum.
```

## Screenshots and records

Numbered actual PNG captures, **1348 × 913**, including setup, each chapter's main evidence, requested schematic views, final summary and cleanup. Partial half-adder views deliberately document its overflow rather than implying that it fits one screen:

- [round9-00-first-screen.png](../../logs/colab/round9-00-first-screen.png)
- [round9-01-setup.png](../../logs/colab/round9-01-setup.png)
- [round9-02-ch0.png](../../logs/colab/round9-02-ch0.png)
- [round9-03-fig2-ch1.png](../../logs/colab/round9-03-fig2-ch1.png)
- [round9-04-ch2.png](../../logs/colab/round9-04-ch2.png)
- [round9-05-ch3.png](../../logs/colab/round9-05-ch3.png)
- [round9-06-ch4.png](../../logs/colab/round9-06-ch4.png)
- [round9-07-ch5-adder-schematic.png](../../logs/colab/round9-07-ch5-adder-schematic.png)
- [round9-08a-ch5-half-adder-left.png](../../logs/colab/round9-08a-ch5-half-adder-left.png)
- [round9-08b-ch5-half-adder-right.png](../../logs/colab/round9-08b-ch5-half-adder-right.png)
- [round9-08c-ch5-half-adder-legend.png](../../logs/colab/round9-08c-ch5-half-adder-legend.png)
- [round9-09-ch6.png](../../logs/colab/round9-09-ch6.png)
- [round9-10-ch7-figure.png](../../logs/colab/round9-10-ch7-figure.png)
- [round9-11a-ch7-wire-c.png](../../logs/colab/round9-11a-ch7-wire-c.png)
- [round9-12-ch8-schematic.png](../../logs/colab/round9-12-ch8-schematic.png)
- [round9-13-ch8-layout.png](../../logs/colab/round9-13-ch8-layout.png)
- [round9-14-ch8-waveform.png](../../logs/colab/round9-14-ch8-waveform.png)
- [round9-15-expected-diagnostic.png](../../logs/colab/round9-15-expected-diagnostic.png)
- [round9-16-ch9.png](../../logs/colab/round9-16-ch9.png)
- [round9-17-final-summary.png](../../logs/colab/round9-17-final-summary.png)
- [round9-18-final-runtime.png](../../logs/colab/round9-18-final-runtime.png)
- [round9-19-runtime-deleted.png](../../logs/colab/round9-19-runtime-deleted.png)

Records: [all 57 cells](../../logs/colab/round9-cells.json), [one-run timing](../../logs/colab/round9-timing.json), [completed output](../../logs/colab/round9-results-ax.txt), [expanded final evidence](../../logs/colab/round9-results-expanded-ax.txt), [setup progress](../../logs/colab/round9-progress-01-ax.txt), [cleanup confirmation](../../logs/colab/round9-cleanup-ax.txt). Saved accessibility text redacts the Google account identifier.

## Short history

- **Round 1 — FAIL**, `89b484b`: setup passed; SciPy/NumPy `_blas_supports_fpe` AttributeError. Manual diagnostics 8 pass / 4 fail; runtime deleted. [Report](../../logs/colab/round1-report.md).
- **Round 2 — FIRST-RUN PASS**, `842afe2`: 17 code cells, **384.1 s** including setup; runtime deleted. [Report](../../logs/colab/round2-report.md).
- **Round 3 — FAIL**, `c84145b`: imports rejected `figures/out/fig_cell.svg`; remaining 16 code cells unexecuted; runtime deleted. [Report](../../logs/colab/round3-report.md).
- **Round 4 — PASS after retry**, `2c81d2c`: initial queue stopped after setup without traceback; second Run all passed 18 code cells in **405.0 s**, excluding initial attempt; runtime deleted. [Report](../../logs/colab/round4-report.md).
- **Round 5 — FIRST-RUN PASS**, `6d8df9e`: 18 code cells, **404.9 s** including setup. Sizing caption fixed; Appendix A truncated. Runtime deleted. [Report](../../logs/colab/round5-report.md).
- **Round 6 — FIRST-RUN PASS**, `91f642d`: 34 code/20 text cells, **332.5 s** including setup. Method/form split, STA, recorded chip and Appendix C rendered; Appendix A wrapping fixed. STA too tall, intro note stale. Runtime deleted. [Report](../../logs/colab/round6-report.md).
- **Round 7 — FIRST-RUN PASS**, `953cb0c`: 34 code/20 text cells, **472.9 s** including setup. Intro cites round 6; narrower STA plot fits viewport. Runtime deleted. [Report](../../logs/colab/round7-report.md).
- **Round 8 — FIRST-RUN PASS**, `cf010a0`: 35 code/22 text cells, **499.2 s** including setup. Chapters 0/1/4 Verilog highlighted and readable; chapter-8 formatted source separated from setup, outputs pass. Runtime deleted. [Report](../../logs/colab/round8-report.md).

## Status and interface requests

Round-9 first-run verification, cell records, captures and runtime deletion complete. No execution blocker. Presentation requests: fit the flat half-adder to the output width or add a compact overview; enlarge small legends/capacitance values in compact schematic views. No implementation changes made outside COLAB ownership.

Validation: actual Colab counts 1–35, all 57 cell records, printed commit/tool versions/timer, screenshot inspection at default size, runtime cleanup, PNG decoding and report-link checks. No local unit tests needed because no code changed.
