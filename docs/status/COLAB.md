# COLAB — round 7, 2026-10-19 JST

**PASS on the FIRST Run all: all 34 code cells completed in 472.9 s including setup (7 min 52.9 s).** Exactly one Run all; no retry, restart, individual-cell rerun or uncaught traceback. All **54 cells (34 code, 20 text)** were inspected and recorded.

Printed source: **`953cb0c36d256c4d6ceeda21fe85da8940725b37`**, ref `colab-v0`. Both requested presentation changes are confirmed: the intro cites round 6, and the complete STA validation plot fits one viewport. Runtime deleted after capture.

## Environment and procedure

- Reloaded the [target Colab URL](https://colab.research.google.com/github/PenguinEino/tritflow/blob/colab-v0/notebook/tritflow_tr1um.ipynb) through extension-backed Chrome using `cua_repl`.
- No old runtime attached: Connect offered and Disconnect/delete disabled. Inspected Python 3, **CPU selected**, latest recommended version; canceled settings without saving. Connected a fresh standard free Google Compute Engine runtime with 12.67 GB RAM.
- Exactly one **Runtime → Run all at 01:18:36 JST**. Accepted the authorized GitHub warning at **01:18:42**. The queue continued after setup automatically.
- Setup gutter: **1 min**; imports **6 s**. Final printed total: **472.9 s including setup**. Completion observed by **01:27:08 JST**; this observation includes polling delay and is not the execution timer.
- **KLayout 0.30.6**, `/usr/bin/klayout`; **ngspice-42**, `/usr/bin/ngspice`, KLU Direct Linear Solver.
- Preserved host packages: **NumPy 2.1.3, SciPy 1.16.3, Matplotlib 3.10.0, Plotly 5.24.1**.
- Runtime → Disconnect and delete runtime → Yes at **01:29:09 JST**. Verified **Reconnect** afterward; cleanup evidence retained.
- No credentials, sign-in, OAuth, account changes, notebook saving/sharing or paid upgrade. No local package installation, code changes or git write commands. Only COLAB-owned report/log paths written.

## Every cell

Zero-based cell indices. Execution counts **1–34** are from the single completed run. Times are Colab's displayed rounded gutter values: `0 s` is rounded, not zero work. Text cells render and have no execution time.

| Cell | Execution | Purpose | Result | Wall time |
|---|---|---|---|---|
| 0 | — | TritFlow: balanced-ternary HDL to GDS on OpenSUSI TR-1um | Rendered | — |
| 1 | 1 | Setup (collapsed form) | PASS | 1 min |
| 2 | 2 | Imports and run bookkeeping | PASS | 6 s |
| 3 | — | From HDL to a checked adder layout | Rendered | — |
| 4 | 3 | Chapter 0 inputs: test conditions and an independent integer oracle | PASS | 0 s |
| 5 | 4 | Chapter 0 public API: HDL → GDS → extracted SPICE | PASS | 2 min |
| 6 | 5 | Chapter 0 checks | PASS | 0 s |
| 7 | — | Three levels from ordinary CMOS | Rendered | — |
| 8 | 6 | Chapter 1 public API: gates and DC | PASS | 0 s |
| 9 | 7 | Chapter 1 checks and the taped-out INV schematic | PASS | 0 s |
| 10 | — | Sizing sets the middle level | Rendered | — |
| 11 | 8 | Chapter 2 public API: sizing slider | PASS | 4 s |
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
| 27 | 19 | Chapter 7 public API: device-only SPICE and wire overlay | PASS | 2 min |
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
| 39 | 27 | Chapter 8 public API: layout | PASS | 13 s |
| 40 | 28 | Chapter 8: extracted SPICE of your layout and its waveform | PASS | 32 s |
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

The run was slower than round 6 (472.9 vs 332.5 s), but finished without intervention. The expensive public-API cells show 2 min each for the live adder flow and device-only SPICE, 13 s for the edited layout and 32 s for its extracted SPICE. No cause for the runtime variation was established.

The final cache table reports `your-minmax: run` at **31.91 s**, plus retained lookups: mac1 **0.140 s**, adder4 **0.093 s**, full_add **0.033 s**, mul1 **0.008 s**. Public-API adder and device-only calculations run outside that table, so it is not a complete phase-time breakdown.

## Round-7 rendering and results

- **First screen:** the verification note now links `91f642d` and states all 34 code cells completed in 332.5 s including setup. Run all guidance, overview, power cost and the prior verification note fit together on the first screen. No clipping or raw markup observed. The miniature HDL/GDS details and serif footnotes in the overview remain small at the native **1348 × 913** viewport.
- **STA figure:** fixed. The complete plot occupies approximately 520 × 520 pixels and fits one viewport, including both axes, legend, all points, equality line and shaded ±20% band. Screenshot 09 also includes the start of its caption. The full explanatory paragraph extends below the viewport; the figure itself does not. Labels remain readable. The plot is left aligned with considerable whitespace to the right, which is acceptable but visually unbalanced.
- Chapters 1–4 and 6–7 paper figures render with visible content and readable axes/captions. Chapter-2 right panel and its labels are fully visible. Chapter-5 interactive synthesis graph renders; chapter-8 edited GDS and waveform render. Chapter-9 framed chip image renders; its layer legend is small. No blank figure or theme-related disappearance observed in the captured figures.
- The short chapter-0 public method and following collapsed check form still render correctly: code hidden behind **Show code**, results visible. Live adder: **32 cells, 1284 × 1038 µm, 0 DRC markers, strict LVS True, analog True**; independent oracle **243 exhaustive logical states**, extracted sequence **9 selected states**.
- Live STA comparison remains **sum[1] 141.0 / 149.3 ns (−5.558%)**, **sum[0] 132.4 / 138.4 ns (−4.348%)**, **cout 114.3 / 107.0 ns (+6.846%)** for STA / post-layout SPICE. The static validation plot is recorded campaign evidence, not a fresh 39-output campaign: 38/39 within ±20%, 6.782% MAPE; scaling/adder2/cout is the 36.48% overprediction exception. The separate 2.182× envelope is not a certified analog/PVT bound.
- Chapter 9 displays the **recorded** adder4 seed-7, **2500 × 2500 µm, 23-pad** chip snapshot. Drawing DRC clean/0, drawing LVS matched/strict ports, mask DRC clean/0, MPW precheck clean/exit 0. **submission_ready False** because custom TEG pad/bond allocation and ESD/power/package approval remain required. The live cell reads committed signoff JSON/PNG; it does not freshly execute `to_chip()`/`signoff()`.
- The expanded final four-design table displays DRC/LVS `[True, True]` for all four retained designs, with source identities and visited/possible input-state counts visible. Routing identities wrap over multiple lines but remain readable.

This pass verifies real-Colab installation and uninterrupted default execution. Recorded paper, sizing, qualification, four-design and chip results are displayed/checked, not all freshly recomputed; this run does not establish manufacturing approval or exhaustive analog qualification of the larger designs.

## Errors

**No failing cell or uncaught Python traceback.** No error screenshot was required for an execution failure. Cell 42 deliberately catches an `HDLError`; screenshot 10c records the expected diagnostic and its successful execution:

```text
your_circuit.tv:2:13: arithmetic/comparison on trits is unsupported; use ~, &, |, nany and sized trit literals
Repair: use gates for signal arithmetic; e.g. nany(a,b) gives the negative saturated sum.
```

The round-6 report quoted this diagnostic's column as `2:17`; its saved UI output actually says `2:13`. This round records the observed location correctly; the archived round-6 report is preserved unchanged.

## Screenshots and records

Numbered actual PNG captures (1348 × 913), including the requested first screen, narrower STA plot and final summary, plus setup and each chapter's main evidence:

- [round7-00-first-screen.png](../../logs/colab/round7-00-first-screen.png)
- [round7-01-setup.png](../../logs/colab/round7-01-setup.png)
- [round7-02-ch0.png](../../logs/colab/round7-02-ch0.png)
- [round7-03-ch1.png](../../logs/colab/round7-03-ch1.png)
- [round7-04-ch2.png](../../logs/colab/round7-04-ch2.png)
- [round7-05-ch3.png](../../logs/colab/round7-05-ch3.png)
- [round7-06-ch4.png](../../logs/colab/round7-06-ch4.png)
- [round7-07-ch5.png](../../logs/colab/round7-07-ch5.png)
- [round7-08-ch6.png](../../logs/colab/round7-08-ch6.png)
- [round7-09-sta-figure.png](../../logs/colab/round7-09-sta-figure.png)
- [round7-09a-ch7-spice.png](../../logs/colab/round7-09a-ch7-spice.png)
- [round7-10-ch8.png](../../logs/colab/round7-10-ch8.png)
- [round7-10a-ch8-layout.png](../../logs/colab/round7-10a-ch8-layout.png)
- [round7-10b-ch9.png](../../logs/colab/round7-10b-ch9.png)
- [round7-10c-expected-diagnostic.png](../../logs/colab/round7-10c-expected-diagnostic.png)
- [round7-11-final-summary.png](../../logs/colab/round7-11-final-summary.png)
- [round7-12-final-runtime.png](../../logs/colab/round7-12-final-runtime.png)
- [round7-13-runtime-deleted.png](../../logs/colab/round7-13-runtime-deleted.png)

Records: [all 54 cells](../../logs/colab/round7-cells.json), [one-run timing](../../logs/colab/round7-timing.json), [completed output](../../logs/colab/round7-results-ax.txt), [expanded final evidence](../../logs/colab/round7-results-expanded-ax.txt), [setup progress](../../logs/colab/round7-progress-01-ax.txt), [runtime cleanup](../../logs/colab/round7-cleanup-ax.txt). Saved accessibility text redacts the Google account identifier.

## Short history

- **Round 1 — FAIL**, `89b484b`: setup passed; SciPy/NumPy `_blas_supports_fpe` AttributeError. Manual diagnostics 8 pass / 4 fail; runtime deleted. [Report](../../logs/colab/round1-report.md).
- **Round 2 — FIRST-RUN PASS**, `842afe2`: 17 code cells, **384.1 s** including setup; runtime deleted. [Report](../../logs/colab/round2-report.md).
- **Round 3 — FAIL**, `c84145b`: imports rejected paper artifact `figures/out/fig_cell.svg`; remaining 16 code cells unexecuted; runtime deleted. [Report](../../logs/colab/round3-report.md).
- **Round 4 — PASS after retry**, `2c81d2c`: initial queue stopped after setup without traceback; second Run all passed 18 code cells in **405.0 s**, excluding first attempt; runtime deleted. [Report](../../logs/colab/round4-report.md).
- **Round 5 — FIRST-RUN PASS**, `6d8df9e`: 18 code cells, **404.9 s** including setup, no retry/restart/uncaught traceback. Sizing caption fixed; Appendix A truncated. Runtime deleted. [Report](../../logs/colab/round5-report.md).
- **Round 6 — FIRST-RUN PASS**, `91f642d`: 34 code/20 text cells, **332.5 s** including setup; no retry/restart/uncaught traceback. Method/form split, STA, recorded chip and Appendix C rendered; Appendix A wrapping fixed. STA figure too tall and intro verification note stale. Runtime deleted. [Report](../../logs/colab/round6-report.md).

## Status and interface requests

Round-7 verification, per-cell records, captures and runtime deletion complete. No execution blocker. Both round-6 presentation requests addressed. Remaining minor readability observations: tiny overview/chip layer detail, dense method lines, and long wrapped routing identifiers. No implementation change requested or made outside COLAB ownership.

Validation: real Colab execution counts 1–34, all 54 cell records, first-run timer, source/tools output, figure inspection, cleanup confirmation, PNG decoding and report-link checks. No local unit tests needed because no code changed.
