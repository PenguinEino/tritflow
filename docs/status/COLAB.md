# COLAB — round 6, 2026-10-19 JST

**PASS on the FIRST Run all: all 34 code cells completed in 332.5 s including setup (5 min 32.5 s).** No retry, restart, individual-cell rerun or uncaught traceback. The restructured notebook has **54 cells: 34 code and 20 text**.

Printed source: **`91f642d40000f7b470578deee86fb32e62687a4e`**, ref `colab-v0`. The method/check split renders correctly in Colab. New live STA output and recorded chip output appear. Appendix A now wraps without truncation; Appendix C renders. Runtime deleted after capture.

## Environment and procedure

- Reloaded https://colab.research.google.com/github/PenguinEino/tritflow/blob/colab-v0/notebook/tritflow_tr1um.ipynb through the extension-backed Chrome surface using `cua_repl`.
- Initially no old runtime: Connect offered, Disconnect/delete disabled. Inspected Python 3 / **CPU selected** / latest recommended runtime, then connected a fresh standard free Google Compute Engine backend (12.67 GB RAM).
- Exactly one **Runtime → Run all at 00:56:49 JST**; accepted the authorized GitHub warning at **00:56:54**. No source edits, execution recovery or later execution actions.
- Setup time shown: **1 min** (rounded gutter); imports **3 s**. Final printed total **332.5 s including setup**. Completion observed by **01:02:57 JST**; observation includes polling delay and is not the execution timer.
- Printed **KLayout 0.30.6**, `/usr/bin/klayout`; **ngspice-42**, `/usr/bin/ngspice`, KLU Direct Linear Solver.
- Preserved host packages: **NumPy 2.1.3, SciPy 1.16.3, Matplotlib 3.10.0, Plotly 5.24.1**.
- Runtime → Disconnect and delete runtime → Yes at **01:04:41 JST**; verified **Reconnect** afterward.
- No credentials, sign-in, OAuth, notebook saving/sharing, paid upgrade or account settings. No local package installation, code modification or git write commands. Only COLAB-owned report/log paths written.

## Every cell

Zero-based Colab cell indices; execution counts **1–34** belong to the single completed run. All times are the displayed rounded gutter values. `0 s` is rounded, not zero work; text cells do not execute.

| Cell | Execution | Purpose | Result | Wall time |
|---|---|---|---|---|
| 0 | — | TritFlow: balanced-ternary HDL to GDS on OpenSUSI TR-1um | Rendered | — |
| 1 | 1 | Setup (collapsed form) | PASS | 1 min |
| 2 | 2 | Imports and run bookkeeping | PASS | 3 s |
| 3 | — | From HDL to a checked adder layout | Rendered | — |
| 4 | 3 | Chapter 0 inputs: test conditions and an independent integer oracle | PASS | 0 s |
| 5 | 4 | Chapter 0 public API: HDL → GDS → extracted SPICE | PASS | 1 min |
| 6 | 5 | Chapter 0 checks | PASS | 0 s |
| 7 | — | Three levels from ordinary CMOS | Rendered | — |
| 8 | 6 | Chapter 1 public API: gates and DC | PASS | 0 s |
| 9 | 7 | Chapter 1 checks and the taped-out INV schematic | PASS | 0 s |
| 10 | — | Sizing sets the middle level | Rendered | — |
| 11 | 8 | Chapter 2 public API: sizing slider | PASS | 3 s |
| 12 | 9 | Chapter 2 details: resistor-length candidates at the taped-out MOS sizes | PASS | 0 s |
| 13 | — | Taped-out circuits become placeable cells | Rendered | — |
| 14 | 10 | Chapter 3 public API: cell view | PASS | 0 s |
| 15 | 11 | Chapter 3 checks: template, clamp devices and cell qualification | PASS | 0 s |
| 16 | — | Describe signed arithmetic in TritVerilog | Rendered | — |
| 17 | 12 | Chapter 4 public API: arithmetic | PASS | 0 s |
| 18 | 13 | Chapter 4 checks: cell counts against the taped-out schematics | PASS | 0 s |
| 19 | — | Follow an expression into cells | Rendered | — |
| 20 | 14 | Chapter 5 public API: synthesis graph | PASS | 0 s |
| 21 | 15 | Chapter 5 checks: mapping rules and gate-level TritVerilog | PASS | 0 s |
| 22 | 16 | Chapter 5 public API: mapped schematics | PASS | 0 s |
| 23 | — | Route signals and feed the standing current | Rendered | — |
| 24 | 17 | Chapter 6 public API: P&R view | PASS | 0 s |
| 25 | 18 | Chapter 6 details and an optional floorplan experiment | PASS | 0 s |
| 26 | — | Does the layout still work? | Rendered | — |
| 27 | 19 | Chapter 7 public API: device-only SPICE and wire overlay | PASS | 1 min |
| 28 | 20 | Chapter 7 checks: identical devices with and without wire C | PASS | 0 s |
| 29 | — | Chapter 7 scaling and power evidence | Rendered | — |
| 30 | 21 | Chapter 7 recorded width and load campaigns | PASS | 0 s |
| 31 | — | Predict with static timing, confirm with SPICE | Rendered | — |
| 32 | 22 | Chapter 7 public API: STA vs SPICE | PASS | 0 s |
| 33 | 23 | Chapter 7 STA comparison table and critical path | PASS | 0 s |
| 34 | — | STA validation figure and scope | Rendered | — |
| 35 | — | Change the circuit and close the loop | Rendered | — |
| 36 | 24 | Chapter 8 editable HDL | PASS | 0 s |
| 37 | 25 | Chapter 8 synthesis / truth table | PASS | 0 s |
| 38 | 26 | Chapter 8 check: every input state against the independent arithmetic reference | PASS | 0 s |
| 39 | 27 | Chapter 8 public API: layout | PASS | 8 s |
| 40 | 28 | Chapter 8: extracted SPICE of your layout and its waveform | PASS | 20 s |
| 41 | — | Expected diagnostic introduction | Rendered | — |
| 42 | 29 | Chapter 8 expected caught HDL error | PASS; expected diagnostic caught | 0 s |
| 43 | — | Next: compare the model with silicon | Rendered | — |
| 44 | — | From your HDL to a shuttle-ready top | Rendered | — |
| 45 | 30 | Chapter 9 recorded chip image and signoff table | PASS | 0 s |
| 46 | 31 | Chapter 9 checks: recorded signoff snapshot and pad map | PASS | 0 s |
| 47 | — | Chip results and remaining submission requirements | Rendered | — |
| 48 | — | Appendix A. What the results establish | Rendered | — |
| 49 | — | Appendix B. Verification evidence and how to rerun | Rendered | — |
| 50 | 32 | Appendix B: cell characterization and fanout evidence | PASS | 0 s |
| 51 | 33 | Appendix B: four-design physical and timing campaign | PASS | 0 s |
| 52 | 34 | Appendix B: evidence tables, provenance and run time | PASS | 0 s |
| 53 | — | Appendix C. Use and extend TritFlow | Rendered | — |

The final cache-stage table lists `your-minmax: run` (**20.52 s**) and four retained lookups: mac1 **0.089 s**, adder4 **0.059 s**, full_add **0.022 s**, mul1 **0.006 s**. The visible public-API adder and device-only simulation run outside that cache-stage list; their gutter times are recorded in cells 5 and 27 above. The cache table is therefore not a complete phase-time breakdown of this run.

## Rendering and new results

**Visible methods followed by collapsed forms:** screenshot 02 shows the completed chapter-0 method cell with the public API and its `DRC clean: True · LVS match: True · analog PASS: True` output. Immediately below, “Chapter 0 checks” retains hidden code with Colab's **Show code** link and visible result table. No manual code collapse was needed. The checks report a **32-cell, 1284 × 1038 µm** live adder, **0 DRC markers, strict LVS True, analog True**, **243 exhaustive logical states** and **9 selected unique analog states**. The titled forms are real executable cells, not literal `#@title` text or raw HTML. They executed despite hidden code.

**Live chapter-7 STA vs SPICE:** the short `tritflow.sta.analyze` method uses the live adder, matched input-vector pairs, routed wire capacitances, output load and input transition. Its output and the following collapsed check cell show:

| Output | STA (ns) | Post-layout SPICE (ns) | Difference (%) |
|---|---:|---:|---:|
| sum[1] | 141.0 | 149.3 | −5.558 |
| sum[0] | 132.4 | 138.4 | −4.348 |
| cout | 114.3 | 107.0 | +6.846 |

The separate **recorded validation figure** states 38/39 output maxima within ±20%, 6.782% mean absolute percentage error; scaling/adder2/cout is the 36.48% overprediction exception. Its separate conservative envelope averages 2.182× the saved maxima and is not a certified analog/PVT bound. That campaign was displayed, not freshly recomputed by this Colab.

**Chapter-9 framed chip:** the image and table are visible and readable. The executable cell explicitly reads the committed `notebook/assets/chip/adder4/signoff.json` and PNG: this is a **recorded adder4 seed-7 signoff snapshot**, not a fresh full-top build in this runtime. The narrative public calls `layout.result.to_chip()` / `chip.signoff()` explain reproduction, but the live cell does not execute them. The recorded **2500 × 2500 µm, 23-pad** top reports:

| Check | Displayed result |
|---|---|
| Drawing DRC | clean True, 0 violations |
| Drawing LVS | matched True, strict_ports True |
| Mask DRC | clean True, 0 violations |
| MPW precheck | clean True, exit_code 0 |
| submission_ready | **False** |

Reason: custom TEG pad/bond allocation and ESD/power/package approval still required. The text distinguishes physical checks from organizer approval, notes passive pads have no ESD network, and states no post-mask LVS stage is defined. No allocation or submission action was taken.

**Appendix A:** bold topic labels and wrapped paragraphs replace the prior truncated table. Top and bottom captures cover the scope statements, including static timing and manufacturing. No ellipsis truncation or horizontal overflow observed in these paragraphs.

**Appendix C:** installation from a source checkout, seven-line API, CLI entry points, adding a cell and adding an operator render as readable prose/code blocks. No raw Markdown or clipped paragraph text observed. These are static instructions; their shell commands were not separately executed during this verification.

## Errors and readability

**No uncaught exception, failing cell or Python traceback.** Cell 42 intentionally catches and prints the unsupported-HDL teaching diagnostic and passes:

```text
your_circuit.tv:2:17: arithmetic/comparison on trits is unsupported; use ~, &, |, nany and sized trit literals
Repair: use gates for signal arithmetic; e.g. nany(a,b) gives the negative saturated sum.
```

Readability findings:

- First screen remains clear, with visible Run all guidance and complete overview; miniature HDL/GDS detail and figure footnotes are small. The verification note still cites the older `2c81d2c` second-run result, so it is stale as a latest-status note, although explicitly attributed to that revision.
- The visible method/check split substantially reduces long code blocks. Some method lines are long and their comments/print expressions are dense; at this 1348 × 913 viewport the chapter-0 method remains readable. Hidden code can be revealed through Show code; results remain visible.
- **STA validation figure is oversized vertically:** its large labels and plot span more than one viewport. Screenshots 04a/04b give complementary graph/scope views. This is a sizing/readability issue, not blank output or missing data. The compact live STA table is fully readable on one screen.
- The chapter-9 chip image and status table fit together on one screen. The tiny layer legend is harder to read than the status table, but the full frame/core/pads are visible. Its remaining-approval reason is displayed in full.
- Appendix A's round-5 truncation issue is fixed. Appendix C is text-dense in the extension section but wraps normally; code examples are legible.
- The final table's routing identifiers wrap across several lines but remain readable. The cache-event list and total timer are visible without horizontal scrolling.

Default execution still uses a mix of fresh public-API calculations and recorded paper/sweep/qualification/four-design/chip evidence. A first-run pass verifies compatibility and notebook execution; it does not freshly qualify every published campaign or make the chip submission-ready.

## Screenshots and records

15 numbered actual PNG screenshots, **1348 × 913**; 04a/04b cover the large STA figure in complementary views:

- [round6-00-first-screen.png](../../logs/colab/round6-00-first-screen.png)
- [round6-01-setup.png](../../logs/colab/round6-01-setup.png)
- [round6-02-ch0-method-form.png](../../logs/colab/round6-02-ch0-method-form.png)
- [round6-03-ch7-sta-spice.png](../../logs/colab/round6-03-ch7-sta-spice.png)
- [round6-04a-ch7-sta-validation.png](../../logs/colab/round6-04a-ch7-sta-validation.png)
- [round6-04b-ch7-sta-scope.png](../../logs/colab/round6-04b-ch7-sta-scope.png)
- [round6-05-ch9-chip.png](../../logs/colab/round6-05-ch9-chip.png)
- [round6-06-ch9-method.png](../../logs/colab/round6-06-ch9-method.png)
- [round6-07-appendix-a-top.png](../../logs/colab/round6-07-appendix-a-top.png)
- [round6-08-appendix-a-bottom.png](../../logs/colab/round6-08-appendix-a-bottom.png)
- [round6-09-appendix-c-top.png](../../logs/colab/round6-09-appendix-c-top.png)
- [round6-10-appendix-c-extension.png](../../logs/colab/round6-10-appendix-c-extension.png)
- [round6-11-final-summary.png](../../logs/colab/round6-11-final-summary.png)
- [round6-12-final-runtime.png](../../logs/colab/round6-12-final-runtime.png)
- [round6-13-runtime-deleted.png](../../logs/colab/round6-13-runtime-deleted.png)

Records: [all 54 cells](../../logs/colab/round6-cells.json), [one-run timing](../../logs/colab/round6-timing.json), [completed output](../../logs/colab/round6-results-ax.txt), [expanded final evidence](../../logs/colab/round6-results-expanded-ax.txt), [early setup progress](../../logs/colab/round6-progress-01-ax.txt), [cleanup confirmation](../../logs/colab/round6-cleanup-ax.txt). Saved accessibility text redacts the Google-account identifier.

## Short history

- **Round 1 — FAIL**, `89b484b`: setup passed; SciPy/NumPy `_blas_supports_fpe` AttributeError. Manual diagnostics: 8 pass / 4 fail; runtime deleted. [Report](../../logs/colab/round1-report.md).
- **Round 2 — PASS**, `842afe2`: uninterrupted first Run all, 17 code cells, **384.1 s** including setup; runtime deleted. [Report](../../logs/colab/round2-report.md).
- **Round 3 — FAIL**, `c84145b`: imports rejected paper artifact `figures/out/fig_cell.svg`; remaining 16 code cells unexecuted; runtime deleted. [Report](../../logs/colab/round3-report.md).
- **Round 4 — PASS after retry**, `2c81d2c`: unexplained initial stop after setup; second Run all passed all 18 code cells in **405.0 s** excluding initial attempt; runtime deleted. [Report](../../logs/colab/round4-report.md).
- **Round 5 — FIRST-RUN PASS**, `6d8df9e`: 18 code cells, **404.9 s** including setup, no retry/restart/uncaught traceback. Sizing caption fixed; Appendix A text truncated. Runtime deleted. [Report](../../logs/colab/round5-report.md).

## Status and requests

Round-6 first-run verification, required captures and runtime cleanup complete. No execution blocker. Presentation requests: reduce the STA validation figure's displayed height and update the latest Colab-verification note. No implementation edits made outside COLAB ownership.

Validation: actual Colab UI execution, counts 1–34, all 54 cell records, closing prerequisite/source checks, output inspection, PNG decoding and report-link checks. No local unit tests required because no code changed.
