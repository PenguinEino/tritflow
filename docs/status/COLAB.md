# COLAB — round 8, 2026-10-19 JST

**PASS on the FIRST Run all: all 35 code cells completed in 499.2 s including setup (8 min 19.2 s).** Exactly one Run all, no retry, restart, individual-cell rerun or uncaught traceback. All **57 cells: 35 code, 22 text** were recorded.

Printed source: **`cf010a078a0e783875f5ccc9ad763ea3d0f6932b`**, ref `colab-v0`. Chapters 0, 1 and 4 have **syntax-highlighted, readable Verilog definition blocks**. Chapter 8 separates the formatted editable HDL definition from circuit-selection/setup code; its schematic, truth table, GDS and SPICE waveform all complete. Runtime deleted after capture.

## Environment and procedure

- Freshly reloaded the [target Colab URL](https://colab.research.google.com/github/PenguinEino/tritflow/blob/colab-v0/notebook/tritflow_tr1um.ipynb).
- `cua_repl` was not exposed in this turn. Used the installed Chrome browser runtime through `node_repl` instead, reaching the **same extension-backed Chrome profile and existing Colab tab**. UI actions used its documented accessibility API and screenshots. No separate remote browser or notebook execution API was used.
- No old runtime attached: Connect offered, Disconnect/delete disabled. Inspected **Python 3 / CPU selected / latest recommended**; canceled settings without saving. Connected a fresh free Google Compute Engine backend with **12.67 GB RAM**.
- One **Runtime → Run all at 01:46:13 JST**, GitHub warning accepted at **01:46:20**. Setup advanced into the remaining cells without intervention.
- Setup gutter: **1 min**; imports **3 s**. Final printed total **499.2 s including setup**. Completion observed at **01:54:53 JST**, including polling delay.
- **KLayout 0.30.6**, `/usr/bin/klayout`; **ngspice-42**, `/usr/bin/ngspice`, KLU Direct Linear Solver.
- Preserved host packages: **NumPy 2.1.3, SciPy 1.16.3, Matplotlib 3.10.0, Plotly 5.24.1**.
- Runtime → Disconnect and delete runtime → Yes at **01:56:46 JST**; verified **Reconnect** afterward.
- No credentials, sign-in, OAuth, account changes, saving/sharing or paid upgrade. No source editing or manual circuit changes in Colab, no local package installation, no git writes. Only COLAB-owned report/log paths written.

## Every cell

Zero-based Colab indices. Execution counts **1–35** belong to this single run. Times are rounded gutter values; `0 s` does not mean zero work. Text cells render without execution time.

| Cell | Execution | Purpose | Result | Wall time |
|---|---|---|---|---|
| 0 | — | TritFlow: balanced-ternary HDL to GDS on OpenSUSI TR-1um | Rendered | — |
| 1 | 1 | Setup (collapsed form) | PASS | 1 min |
| 2 | 2 | Imports and run bookkeeping | PASS | 3 s |
| 3 | — | From HDL to a checked adder layout; highlighted adder.tv definition | Rendered | — |
| 4 | 3 | Chapter 0 inputs: test conditions and an independent integer oracle | PASS | 0 s |
| 5 | 4 | Chapter 0 public API: HDL → GDS → extracted SPICE | PASS | 3 min |
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
| 22 | 14 | Chapter 5 public API: synthesis graph | PASS | 0 s |
| 23 | 15 | Chapter 5 checks: mapping rules and gate-level TritVerilog | PASS | 0 s |
| 24 | 16 | Chapter 5 public API: mapped schematics | PASS | 0 s |
| 25 | — | Route signals and feed the standing current | Rendered | — |
| 26 | 17 | Chapter 6 public API: P&R view | PASS | 0 s |
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
| 42 | 28 | Chapter 8 public API: layout | PASS | 15 s |
| 43 | 29 | Chapter 8: extracted SPICE of your layout and its waveform | PASS | 32 s |
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

The long public-API cells show **3 min** for the chapter-0 adder flow and **2 min** for chapter-7 device-only SPICE. Chapter-8 layout shows **15 s**, extracted SPICE **32 s**. The final cache table lists `your-minmax: run` **32.4 s**, plus retained lookups mac1 **0.154 s**, adder4 **0.108 s**, full_add **0.039 s**, mul1 **0.010 s**. The public-API adder and device-only calculations are outside that cache table; it is not a complete phase-time breakdown.

## HDL presentation and readability

**Chapter 0:** `examples/adder.tv` is a rendered definition block, not a Python string dump. The include, module/parameter, generate loop, port connections and assignments appear with preserved indentation. Keywords are blue, comments green and the include filename red. The entire block fits one viewport (screenshot 02), without horizontal clipping.

**Chapter 1:** screenshot 03 shows `examples/gates.tv` and the completed method directly below it. `module`, `input`, `output`, `assign` and `endmodule` are blue; comments green. Identifiers/operators remain dark. `trit` remains plain text rather than a recognized standard-Verilog type, which is reasonable for the custom HDL. All definitions and the method fit together at the native **1348 × 913** viewport. Method output: **A = 0 V: Y = −39.5 mV, supply current = 0.407 mA**. No raw Markdown fences, HTML or missing block observed.

**Chapter 4:** `examples/half_add.tv` and `examples/full_add.tv` render as two separate highlighted blocks. The filename labels, complete definitions and comments fit together on one screen (screenshot 07). Primitive instantiations and named-port connections are readable. This is a substantial improvement over the smaller uncolored HDL still embedded in the paper figure.

**Chapter 8:** screenshot 12 shows the edit cell containing only introductory comments and the formatted `source = """…"""` minmax definition. Imports, `CHOICE`, design selection and reference setup are in the following executable cell. The HDL body is visibly a **Python string colored red**, not token-by-token Verilog highlighting; its Python comments are green. This differs from the rendered Verilog blocks in chapters 0/1/4, but indentation, ports, assignments and inline HDL comments are readable. The displayed successful first edit computes the minimum as `~((~a) | (~b))` and maximum as `a | b`. No manual edit or cell rerun was needed for the default flow.

Chapter-8 outputs:

- Four-cell mapped schematic visible with `lo`/`hi`, two inputs, connected-branch dots and crossing explanation.
- Expanded truth table: **all 9 input states**, output values match ascending sort.
- **384 × 366 µm** GDS, **0 drawing-DRC markers**, **LVS Match**.
- Extracted sequence visits **9 input states**, output checks **PASS**; both waveform panels and ideal-level bands render. Screenshot 16 shows both panels and their PASS markers.

Other rendering observations: all captured chapter main figures have content and visible axes/labels. The overview HDL/GDS miniature and chip layer legend remain small. Long Python method lines and routing identifiers in the final table are dense but readable. The first-screen verification note now correctly cites round 7 (`953cb0c`, 34 code cells, 472.9 s); it is an attributed prior result. No new clipping or theme-related disappearance observed.

## Results and scope

Live chapter-0 adder checks: **32 cells, 1284 × 1038 µm, 0 DRC markers, strict LVS True, analog True**; independent integer oracle **243 exhaustive logical states**, extracted sequence **9 selected states**.

The final expanded four-design table reports DRC/LVS `[True, True]` for all four retained designs and displays source identities and visited/possible state counts. Chapter-9 chip output remains a **recorded** adder4 seed-7, 2500 × 2500 µm, 23-pad signoff snapshot read from committed JSON/PNG: drawing DRC clean/0, drawing LVS matched/strict ports, mask DRC clean/0, MPW precheck clean/exit 0. **submission_ready False**: custom TEG pad/bond allocation and ESD/power/package approval still required. No full-top build or submission was performed.

This first-run pass establishes installation/runtime compatibility and uninterrupted default execution. Recorded paper, sweep, qualification, four-design and chip evidence is displayed/checked; the whole published campaign is not freshly recomputed and this pass does not establish manufacturing approval.

## Errors

**No failing cell or uncaught traceback.** Cell 45 deliberately catches the unsupported arithmetic `HDLError`; this teaching example passed and has its own screenshot 17:

```text
your_circuit.tv:3:14: arithmetic/comparison on trits is unsupported; use ~, &, |, nany and sized trit literals
Repair: use gates for signal arithmetic; e.g. nany(a,b) gives the negative saturated sum.
```

## Screenshots and records

22 numbered actual PNG captures, 1348 × 913, covering the required HDL blocks/edit outputs/final summary plus setup and each chapter's main evidence:

- [round8-00-first-screen.png](../../logs/colab/round8-00-first-screen.png)
- [round8-01-setup.png](../../logs/colab/round8-01-setup.png)
- [round8-02-ch0-verilog.png](../../logs/colab/round8-02-ch0-verilog.png)
- [round8-03-ch1-verilog-method.png](../../logs/colab/round8-03-ch1-verilog-method.png)
- [round8-04-ch1-figure.png](../../logs/colab/round8-04-ch1-figure.png)
- [round8-05-ch2-figure.png](../../logs/colab/round8-05-ch2-figure.png)
- [round8-06-ch3-figure.png](../../logs/colab/round8-06-ch3-figure.png)
- [round8-07-ch4-verilog.png](../../logs/colab/round8-07-ch4-verilog.png)
- [round8-08-ch4-figure.png](../../logs/colab/round8-08-ch4-figure.png)
- [round8-09-ch5-figure.png](../../logs/colab/round8-09-ch5-figure.png)
- [round8-10-ch6-figure.png](../../logs/colab/round8-10-ch6-figure.png)
- [round8-11-ch7-figure.png](../../logs/colab/round8-11-ch7-figure.png)
- [round8-12-ch8-edit.png](../../logs/colab/round8-12-ch8-edit.png)
- [round8-13-ch8-schematic.png](../../logs/colab/round8-13-ch8-schematic.png)
- [round8-14-ch8-truth-table.png](../../logs/colab/round8-14-ch8-truth-table.png)
- [round8-15-ch8-layout.png](../../logs/colab/round8-15-ch8-layout.png)
- [round8-16-ch8-waveform.png](../../logs/colab/round8-16-ch8-waveform.png)
- [round8-17-expected-diagnostic.png](../../logs/colab/round8-17-expected-diagnostic.png)
- [round8-18-ch9-chip.png](../../logs/colab/round8-18-ch9-chip.png)
- [round8-19-final-summary.png](../../logs/colab/round8-19-final-summary.png)
- [round8-20-final-runtime.png](../../logs/colab/round8-20-final-runtime.png)
- [round8-21-runtime-deleted.png](../../logs/colab/round8-21-runtime-deleted.png)

Records: [all 57 cells](../../logs/colab/round8-cells.json), [single-run timing](../../logs/colab/round8-timing.json), [completed output](../../logs/colab/round8-results-ax.txt), [expanded evidence](../../logs/colab/round8-results-expanded-ax.txt), [setup progress](../../logs/colab/round8-progress-01-ax.txt), [cleanup confirmation](../../logs/colab/round8-cleanup-ax.txt). Saved accessibility text redacts the Google account identifier.

## Short history

- **Round 1 — FAIL**, `89b484b`: setup passed; SciPy/NumPy `_blas_supports_fpe` AttributeError. Manual diagnostics 8 pass / 4 fail; runtime deleted. [Report](../../logs/colab/round1-report.md).
- **Round 2 — FIRST-RUN PASS**, `842afe2`: 17 code cells, **384.1 s** including setup; runtime deleted. [Report](../../logs/colab/round2-report.md).
- **Round 3 — FAIL**, `c84145b`: imports rejected paper artifact `figures/out/fig_cell.svg`; remaining 16 code cells unexecuted; runtime deleted. [Report](../../logs/colab/round3-report.md).
- **Round 4 — PASS after retry**, `2c81d2c`: initial queue stopped after setup without traceback; second Run all passed 18 code cells in **405.0 s**, excluding initial attempt; runtime deleted. [Report](../../logs/colab/round4-report.md).
- **Round 5 — FIRST-RUN PASS**, `6d8df9e`: 18 code cells, **404.9 s** including setup. Sizing caption fixed; Appendix A truncated. Runtime deleted. [Report](../../logs/colab/round5-report.md).
- **Round 6 — FIRST-RUN PASS**, `91f642d`: 34 code/20 text cells, **332.5 s** including setup. Method/form split, STA, recorded chip and Appendix C rendered; Appendix A wrapping fixed. STA figure too tall and intro note stale. Runtime deleted. [Report](../../logs/colab/round6-report.md).
- **Round 7 — FIRST-RUN PASS**, `953cb0c`: 34 code/20 text cells, **472.9 s** including setup, no retry/restart/uncaught traceback. Intro cites round 6; narrower STA plot fits one viewport. Runtime deleted. [Report](../../logs/colab/round7-report.md).

## Status and requests

Round-8 first-run verification, all cell records, captures and runtime cleanup complete. No execution blocker. Verilog definition highlighting/readability confirmed; chapter-8 edit/setup separation confirmed. Optional presentation improvement: provide a Verilog preview of the editable Python string if per-token HDL coloring there is desired. No implementation changes made.

Validation: actual Colab execution counts 1–35, all 57 cell records, printed source/tools and final timer, requested visual inspection, runtime cleanup, PNG decoding and report-link checks. No local unit tests needed because no code changed.
