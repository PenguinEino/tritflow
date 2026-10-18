# COLAB — round 10, 2026-10-19 JST

**PASS on the FIRST Run all: all 35 code cells completed in 300.7 s including setup (5 min 0.7 s).** Exactly one Run all; no retry, restart, individual-cell rerun or uncaught traceback. All **57 cells (35 code, 22 text)** recorded.

Printed source: **`0ffe7a12c34738664e9e788853d87edc9da5b7ec`**, ref `colab-v0`. The new input-trit selector works: requested input pairs produce correct outputs and visibly recolour wires. **The flat half-adder now fits without output scrolling.** Side legends improve the adder and wire-C views. Remaining minor readability issue: very small auxiliary pin/net labels in the chapter-4 composite figure. Runtime deleted after capture.

## Environment and procedure

- Freshly reloaded the [target Colab URL](https://colab.research.google.com/github/PenguinEino/tritflow/blob/colab-v0/notebook/tritflow_tr1um.ipynb) using the installed Chrome browser runtime through `node_repl`, on the same extension-backed Chrome surface as round 9. UI actions used the documented accessibility API and screenshots.
- Colab automatically reattached an old runtime. Deleted it at **05:28:37 JST**, verified Reconnect, then connected a new free Google Compute Engine CPU runtime (**12.67 GB RAM**). Inspected **Python 3 / CPU selected / latest recommended** and canceled settings without saving.
- Exactly one **Runtime → Run all at 05:29:14 JST**; GitHub warning accepted at **05:29:24**. Setup advanced through the queue automatically.
- Setup gutter **1 min**, imports **2 s**. Final printed timer **300.7 s including setup**. Completion recorded at **05:34:52 JST**, including observation delay.
- Printed **KLayout 0.30.6**, `/usr/bin/klayout`; **ngspice-42**, `/usr/bin/ngspice`, KLU Direct Linear Solver.
- Host packages preserved: **NumPy 2.1.3, SciPy 1.16.3, Matplotlib 3.10.0, Plotly 5.24.1**.
- Tested the requested selector buttons after the synthesis cell completed while the original queue continued. No code edited and no cells rerun. Final selector state: **a=0, b=+1**.
- Runtime → Disconnect and delete runtime → Yes at **05:36:07 JST**, verified **Reconnect** afterward.
- No credentials, sign-in, OAuth, saving/sharing, account changes or paid upgrade. No local package installation, implementation edits or git writes. Only COLAB-owned report/log paths written.

## Every cell

Zero-based indices. Execution counts **1–35** belong to the single fresh run. Times are rounded gutter values; `0 s` does not mean zero work. Text cells render without execution time. JSON keeps the round-9 keys and Japanese gutter-time strings.

| Cell | Execution | Purpose | Result | Wall time |
|---|---|---|---|---|
| 0 | — | TritFlow: balanced-ternary HDL to GDS on OpenSUSI TR-1um | Rendered | — |
| 1 | 1 | Setup (collapsed form) | PASS | 1 min |
| 2 | 2 | Imports and run bookkeeping | PASS | 2 s |
| 3 | — | From HDL to a checked adder layout; highlighted adder.tv definition | Rendered | — |
| 4 | 3 | Chapter 0 inputs: test conditions and an independent integer oracle | PASS | 0 s |
| 5 | 4 | Chapter 0 public API: HDL → GDS → extracted SPICE | PASS | 1 min |
| 6 | 5 | Chapter 0 checks | PASS | 0 s |
| 7 | — | Three levels from ordinary CMOS | Rendered | — |
| 8 | — | Chapter 1 highlighted TritVerilog definition: examples/gates.tv | Rendered | — |
| 9 | 6 | Chapter 1 public API: gates and DC | PASS | 0 s |
| 10 | 7 | Chapter 1 checks and the taped-out INV schematic | PASS | 0 s |
| 11 | — | Sizing sets the middle level | Rendered | — |
| 12 | 8 | Chapter 2 public API: sizing slider | PASS | 2 s |
| 13 | 9 | Chapter 2 details: resistor-length candidates at the taped-out MOS sizes | PASS | 0 s |
| 14 | — | Taped-out circuits become placeable cells | Rendered | — |
| 15 | 10 | Chapter 3 public API: cell view | PASS | 0 s |
| 16 | 11 | Chapter 3 checks: template, clamp devices and cell qualification | PASS | 0 s |
| 17 | — | Describe signed arithmetic in TritVerilog | Rendered | — |
| 18 | — | Chapter 4 highlighted half_add.tv and full_add.tv definitions | Rendered | — |
| 19 | 12 | Chapter 4 public API: arithmetic | PASS | 0 s |
| 20 | 13 | Chapter 4 checks: cell counts against the taped-out schematics | PASS | 0 s |
| 21 | — | Follow an expression into cells | Rendered | — |
| 22 | 14 | Chapter 5 public API: synthesis and interactive half-adder schematic | PASS | 0 s |
| 23 | 15 | Chapter 5 checks: mapping rules and gate-level TritVerilog | PASS | 0 s |
| 24 | 16 | Chapter 5 public API: two-trit adder hierarchy schematic | PASS | 0 s |
| 25 | — | Route signals and feed the standing current | Rendered | — |
| 26 | 17 | Chapter 6 public API: P&R view | PASS | 0 s |
| 27 | 18 | Chapter 6 details and an optional floorplan experiment | PASS | 0 s |
| 28 | — | Does the layout still work? | Rendered | — |
| 29 | 19 | Chapter 7 public API: device-only SPICE and wire overlay | PASS | 1 min |
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
| 42 | 28 | Chapter 8 public API: layout | PASS | 8 s |
| 43 | 29 | Chapter 8: extracted SPICE of your layout and its waveform | PASS | 19 s |
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

Long cells: live adder **1 min**, device-only SPICE **1 min**, edited layout **8 s**, edited extracted SPICE **19 s**. Final cache table reports `your-minmax: run` **19.39 s**; retained lookups mac1 **0.090 s**, adder4 **0.060 s**, full_add **0.022 s**, mul1 **0.005 s**. Public-API adder/device-only calculations are outside this cache list; it is not a complete phase-time breakdown.

## Requested presentation and interaction checks

Assessed at the normal **1348 × 913** Colab viewport, with no viewport override or browser zoom change.

### 1. Chapter 4: fig_synth

The complete composite figure fits with its caption. Half-adder gates share an aligned row, inverter g_na sits above it, and full-adder modules use aligned blocks with Manhattan routes. Input, carry and sum paths can be followed; no major block collision or clipped output observed. Blue/grey/red wires remain distinct. Main gate names and the arithmetic/output labels are readable.

**Small auxiliary text remains difficult:** A/B pin labels and internal-net/instance annotations around the half-adder row are tiny and dense, as are some full-adder pin labels. They are harder to read than the main NANY/INV labels at normal size. The HDL embedded in the left panel is smaller than the separate highlighted definition blocks below. Recommend reducing auxiliary annotations or enlarging that detail if those labels are necessary to the lesson. Screenshot 06 records the actual default-size rendering.

### 2. Chapter 5 synthesis: input-trit selector

**PASS.** Clicked four buttons to exercise both requested pairs, with intermediate states also updating. The whole seven-cell schematic, six buttons, output line, branch/crossing key and port-value legend fit together on one screen. **No horizontal or vertical scrolling inside the output** was needed; only normal notebook navigation to reach the cell. This fixes round 9's oversized flat schematic.

| State | Displayed outputs | Observed colour change |
|---|---|---|
| Default a=+1, b=+1 | sum=−1, carry=+1 | Inputs/carry red, sum blue; baseline screenshot 07a |
| Clicked a=−1, b=0 | **sum=−1, carry=0** | a input becomes blue, b/carry grey; internal wires visibly change; screenshot 07b |
| Clicked a=0, b=+1 | **sum=+1, carry=0** | a becomes grey, b/sum red; intermediate wires change again; screenshot 07c |

Intermediate a=−1,b=+1 and a=0,b=0 both showed sum=0, carry=0. Selected buttons switch to dark fill. The port-value legend changes with the output line and schematic. No stale output, error, overlap or re-execution needed. Logical interpretation matches a+b=sum+3·carry for each tested pair.

### 3. Chapter 5 adder and chapter 7 wire-C schematic

**Improved and readable.** Both have a vertical side legend in the previously unused area instead of tiny text below a large blank margin. The adder's eight port-value entries are legible; the wire-C view's numeric capacitances and fF units can be read directly. The wire-C explanation (“Darker / thicker = more C”) is also readable. Hierarchy blocks, pin labels and coloured/thickness-coded wires do not overlap the side legend.

The diagram plus legend fits on one screen without output scrolling. The content uses the width much better than round 9. Some right margin remains, but no large empty interior area separates the diagram from its evidence. Screenshots 08 and 11 show the full views.

### 4. Chapter 8 edited schematic

Four cells and both outputs fit on one screen. Orthogonal routes, branch dots and no-connection gaps are clear, with no observed label/wire collision or clipped output. Ports a/b/lo/hi are readable. Gate IDs g0–g3 and the branch/crossing key are now readable at normal display size. Some whitespace remains on the right, but it does not force tiny text or scrolling. Screenshot 12.

Other observations: first-screen guidance remains clear and attributes round 9 (`7b62e63`, 35 cells, 384.4 s). Miniature overview/GDS and chip layer detail remain small. Other captured figures render with visible content and labels. Final-table routing identities wrap but remain readable.

## Results and scope

- Live adder: **32 cells, 1284 × 1038 µm, 0 DRC markers, strict LVS True, analog True**, **243 exhaustive logical states**, extracted sequence **9 selected states**.
- Device-only → wire-C SPICE settling: **sum[1] 132.1 → 149.3 ns; sum[0] 124.6 → 138.4 ns; cout 102.2 → 107.0 ns**.
- Edited minmax: **4 cells, 384 × 366 µm**, DRC clean / LVS Match; independent reference **9 states**, extracted sequence **9 states**, output checks **PASS**. Schematic, GDS and waveform render.
- Final four-design table displays DRC/LVS `[True, True]` for all four retained designs, with source identities and visited/possible input counts.
- Chapter 9 is a **recorded** adder4 seed-7, 2500 × 2500 µm, 23-pad snapshot: drawing DRC clean/0, drawing LVS matched/strict ports, mask DRC clean/0, MPW precheck clean/exit 0. **submission_ready False** because pad/bond allocation and ESD/power/package approval remain required. The cell reads committed JSON/PNG, not a fresh full-top build.

This pass verifies real-Colab installation and uninterrupted default execution, plus the requested live selector. Recorded paper/sweep/qualification/four-design/chip campaigns are displayed/checked rather than all recomputed; this is not manufacturing approval.

## Errors

**No failing cell or uncaught traceback.** Cell 45 intentionally catches the unsupported-HDL teaching diagnostic and passes; screenshot 15:

```text
your_circuit.tv:3:14: arithmetic/comparison on trits is unsupported; use ~, &, |, nany and sized trit literals
Repair: use gates for signal arithmetic; e.g. nany(a,b) gives the negative saturated sum.
```

## Screenshots and records

22 numbered actual PNG screenshots, **1348 × 913**, covering every requested view, selector states, setup, each chapter's main evidence, final summary and cleanup:

- [round10-00-first-screen.png](../../logs/colab/round10-00-first-screen.png)
- [round10-01-setup.png](../../logs/colab/round10-01-setup.png)
- [round10-02-ch0.png](../../logs/colab/round10-02-ch0.png)
- [round10-03-ch1.png](../../logs/colab/round10-03-ch1.png)
- [round10-04-ch2.png](../../logs/colab/round10-04-ch2.png)
- [round10-05-ch3.png](../../logs/colab/round10-05-ch3.png)
- [round10-06-ch4-fig-synth.png](../../logs/colab/round10-06-ch4-fig-synth.png)
- [round10-07a-selector-default.png](../../logs/colab/round10-07a-selector-default.png)
- [round10-07b-selector-a-neg1-b0.png](../../logs/colab/round10-07b-selector-a-neg1-b0.png)
- [round10-07c-selector-a0-b-pos1.png](../../logs/colab/round10-07c-selector-a0-b-pos1.png)
- [round10-08-ch5-adder.png](../../logs/colab/round10-08-ch5-adder.png)
- [round10-09-ch6.png](../../logs/colab/round10-09-ch6.png)
- [round10-10-ch7-figure.png](../../logs/colab/round10-10-ch7-figure.png)
- [round10-11-ch7-wire-c.png](../../logs/colab/round10-11-ch7-wire-c.png)
- [round10-12-ch8-schematic.png](../../logs/colab/round10-12-ch8-schematic.png)
- [round10-13-ch8-layout.png](../../logs/colab/round10-13-ch8-layout.png)
- [round10-14-ch8-waveform.png](../../logs/colab/round10-14-ch8-waveform.png)
- [round10-15-expected-diagnostic.png](../../logs/colab/round10-15-expected-diagnostic.png)
- [round10-16-ch9.png](../../logs/colab/round10-16-ch9.png)
- [round10-17-final-summary.png](../../logs/colab/round10-17-final-summary.png)
- [round10-18-final-runtime.png](../../logs/colab/round10-18-final-runtime.png)
- [round10-19-runtime-deleted.png](../../logs/colab/round10-19-runtime-deleted.png)

Records: [all 57 cells](../../logs/colab/round10-cells.json), [one-run timing](../../logs/colab/round10-timing.json), [selector checks](../../logs/colab/round10-selector-checks.json), [a=−1,b=0 UI state](../../logs/colab/round10-selector-a-neg1-b0-ax.txt), [a=0,b=+1 UI state](../../logs/colab/round10-selector-a0-b-pos1-ax.txt), [completed output](../../logs/colab/round10-results-ax.txt), [expanded evidence](../../logs/colab/round10-results-expanded-ax.txt), [setup progress](../../logs/colab/round10-progress-01-ax.txt), [cleanup](../../logs/colab/round10-cleanup-ax.txt). Saved accessibility text redacts the Google account identifier.

## Short history

- **Round 1 — FAIL**, `89b484b`: setup passed; SciPy/NumPy `_blas_supports_fpe` AttributeError. Manual diagnostics 8 pass / 4 fail; runtime deleted. [Report](../../logs/colab/round1-report.md).
- **Round 2 — FIRST-RUN PASS**, `842afe2`: 17 code cells, **384.1 s** including setup; runtime deleted. [Report](../../logs/colab/round2-report.md).
- **Round 3 — FAIL**, `c84145b`: imports rejected `figures/out/fig_cell.svg`; remaining 16 code cells unexecuted; runtime deleted. [Report](../../logs/colab/round3-report.md).
- **Round 4 — PASS after retry**, `2c81d2c`: initial queue stopped after setup without traceback; second Run all passed 18 code cells in **405.0 s**, excluding initial attempt; runtime deleted. [Report](../../logs/colab/round4-report.md).
- **Round 5 — FIRST-RUN PASS**, `6d8df9e`: 18 code cells, **404.9 s** including setup. Sizing caption fixed; Appendix A truncated. Runtime deleted. [Report](../../logs/colab/round5-report.md).
- **Round 6 — FIRST-RUN PASS**, `91f642d`: 34 code/20 text cells, **332.5 s** including setup. Method/form split, STA, recorded chip and Appendix C rendered; Appendix A wrapping fixed. STA too tall, intro note stale. Runtime deleted. [Report](../../logs/colab/round6-report.md).
- **Round 7 — FIRST-RUN PASS**, `953cb0c`: 34 code/20 text cells, **472.9 s** including setup. Intro cites round 6; narrower STA plot fits viewport. Runtime deleted. [Report](../../logs/colab/round7-report.md).
- **Round 8 — FIRST-RUN PASS**, `cf010a0`: 35 code/22 text cells, **499.2 s** including setup. Chapters 0/1/4 Verilog highlighted and readable; chapter-8 formatted source separated from setup, outputs pass. Runtime deleted. [Report](../../logs/colab/round8-report.md).
- **Round 9 — FIRST-RUN PASS**, `7b62e63`: 35 code/22 text cells, **384.4 s** including setup. Recoloured Fig. 2 and cleaner schematic routes; flat half-adder oversized, compact legends small. Runtime deleted. [Report](../../logs/colab/round9-report.md).

## Status and interface requests

Round-10 first-run verification, both requested selector states, all per-cell records, captures and runtime deletion complete. No execution blocker. Round-9 half-adder scrolling and compact-legend issues are fixed in the inspected views. Remaining optional presentation request: enlarge or simplify the tiny auxiliary pin/net annotations in fig_synth. No implementation changes made.

Validation: actual Colab execution counts 1–35, all 57 records, printed source/tools/timer, live selector button changes and expected outputs, normal-size figure inspection, runtime cleanup, PNG decoding and report links. No local unit tests needed because no code changed.
