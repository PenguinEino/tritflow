# COLAB — round 4 release candidate, 2026-10-18

**PASS after one Run-all retry: all 18 code cells completed, no uncaught traceback, printed runtime 405.0 s (6 min 45 s).** The initial attempt ceased after setup without chapter output or a traceback; the second Runtime → Run all completed on the same runtime. This is a successful complete execution with a recovery step, not evidence of an uninterrupted first-attempt clean-install pass.

Printed commit: **`2c81d2c1aa81ecebefaa93851f004eb17c9040ba`** (`colab-v0`). Math renders in chapters 1/2/7. The sizing slider updates at two positions. Chapter 8 produces the edited HDL, mapped schematic, real GDS and passing extracted waveform. Runtime was disconnected and deleted afterward.

## Procedure, tools and timing

- Used the Chrome extension surface through `cua_repl` at https://colab.research.google.com/github/PenguinEino/tritflow/blob/colab-v0/notebook/tritflow_tr1um.ipynb ; reloaded to retrieve the new notebook.
- Initially no runtime existed: Connect was offered and Disconnect/delete was disabled. Verified Python 3, **CPU selected**, latest recommended runtime, then connected a standard free Google Compute Engine backend (12.67 GB RAM). No accelerator or paid option selected.
- First Runtime → Run all: **23:36:27 JST**, authorized GitHub warning accepted **23:36:31**. Setup printed the expected commit and versions. Subsequently the UI showed an idle check mark, blank execution counts and no imports/chapter output or traceback. The captured [initial state](../../logs/colab/round4-latest-ax.txt) and [setup screenshot](../../logs/colab/round4-02-setup-versions.png) preserve that observation. The cause was not established; no intentional interrupt, restart, source edit or runtime change was made.
- Recovery: second **Runtime → Run all at 23:38:55 JST**, same runtime, no code edits or bypasses. It completed all cells. The initial attempt had already installed tools, so the successful run's setup is not a pristine first installation.
- Setup cell: **1 min**, Colab's rounded gutter display. Imports: **3 s**. The successful final cell printed **405.0 s including setup**, and completion was observed by 23:46:06. The observation time includes polling/capture delay and is not the execution timer. The 405.0 s excludes the first interrupted attempt and gap before retry.
- Printed scientific stack, preserved host versions: **NumPy 2.1.3, SciPy 1.16.3, Matplotlib 3.10.0, Plotly 5.24.1**.
- Printed tools: **KLayout 0.30.6**, `/usr/bin/klayout`; **ngspice-42**, `/usr/bin/ngspice`, compiled with KLU Direct Linear Solver.
- Cleanup: Runtime → Disconnect and delete runtime → Yes at **23:47:48 JST**. Verified **Reconnect** in the toolbar; [cleanup screenshot](../../logs/colab/round4-28-runtime-deleted.png) and [accessibility confirmation](../../logs/colab/round4-cleanup-ax.txt).
- No credentials entered, sign-in, OAuth, notebook saving/sharing, paid upgrade or account-setting changes. No notebook source was edited. No local package installation, source change or git write command was used.

## Every cell

Colab indices are zero-based: **33 cells = 18 code + 15 text**. Execution counts 1–18 and timings below are from the completed second Run all. Text cells rendered; they do not execute. `0 s` is Colab's rounded display, not a claim of zero work.

| Cell | Execution | Purpose | Result | Colab wall time |
|---|---|---|---|---|
| 0 | — | Opening narrative / overview hero | Rendered | — |
| 1 | 1 | Setup | PASS | 1 min (rounded) |
| 2 | 2 | Imports / paper evidence | PASS | 3 s (rounded) |
| 3 | — | Chapter 0 narrative | Rendered | — |
| 4 | 3 | Live two-trit adder | PASS | 2 min (rounded) |
| 5 | — | Chapter 1 narrative / DC hero / math | Rendered | — |
| 6 | 4 | Gate checks / inverter DC | PASS | 0 s (rounded) |
| 7 | — | Chapter 2 narrative / sizing hero / math | Rendered | — |
| 8 | 5 | Sizing tables and interactive slider | PASS | 8 s (rounded) |
| 9 | — | Chapter 3 narrative / cell-layout hero | Rendered | — |
| 10 | 6 | Cell dimensions / mapping / qualification | PASS | 0 s (rounded) |
| 11 | — | Chapter 4 narrative / arithmetic hero | Rendered | — |
| 12 | 7 | Half/full-adder arithmetic checks | PASS | 0 s (rounded) |
| 13 | — | Chapter 5 synthesis narrative | Rendered | — |
| 14 | 8 | Mapped half-adder graph / reports | PASS | 0 s (rounded) |
| 15 | 9 | Mapped adder and half-adder schematics | PASS | 0 s (rounded) |
| 16 | — | Chapter 6 narrative / P&R hero | Rendered | — |
| 17 | 10 | P&R measurements | PASS | 0 s (rounded) |
| 18 | — | Chapter 7 narrative / post-layout hero / math | Rendered | — |
| 19 | 11 | Identical extracted devices, without wire C | PASS | 2 min (rounded) |
| 20 | — | Chapter 7 scaling/power hero and estimates | Rendered | — |
| 21 | 12 | Published width/load evidence | PASS | 0 s (rounded) |
| 22 | — | Chapter 8 narrative | Rendered | — |
| 23 | 13 | Edited minmax HDL | PASS | 0 s (rounded) |
| 24 | 14 | Custom flow / schematic / GDS / waveform | PASS | 28 s (rounded) |
| 25 | — | Expected diagnostic introduction | Rendered | — |
| 26 | 15 | Caught unsupported-HDL diagnostic | PASS; expected diagnostic caught | 0 s (rounded) |
| 27 | — | Chapter 9 outlook / measurement table | Rendered | — |
| 28 | — | Appendix A scope | Rendered | — |
| 29 | — | Appendix B evidence introduction | Rendered | — |
| 30 | 16 | Characterization evidence | PASS | 0 s (rounded) |
| 31 | 17 | Four-design recorded campaign | PASS | 0 s (rounded) |
| 32 | 18 | Final assertions / summary / timings | PASS | 0 s (rounded) |

Fresh-stage times printed by the notebook:

| Stage | State | Seconds |
|---|---|---:|
| adder2-complete | run | 154.2 |
| adder2-pre | run | 139.3 |
| your-minmax | run | 27.75 |
| your-minmax-raster | run | 0.336 |
| inv-dc | run | 0.330 |
| four-mac1 | recorded lookup | 0.265 |
| four-adder4 | recorded lookup | 0.178 |
| four-full_add | recorded lookup | 0.068 |
| four-mul1 | recorded lookup | 0.017 |

The paper figures, cell qualification, characterization, sizing grids, width/load campaigns and four-design retained reports are published evidence. Their display and compatibility/assertion checks passed, but they were not all freshly simulated in this Colab. The final table explicitly labels the four-design records and their routing identities.

## Computation and interaction results

- **Live chapter-0 adder:** 32 cells, **1284 × 1038 µm**, **0 DRC markers**, strict LVS **True**, analog **True**. Independent integer oracle checked **243 exhaustive input states**; the extracted sequence covered **9 selected unique states**. The illustrated four-trit paper hero is a separate recorded design, not this fresh two-trit run.
- **Math:** chapter 1 gate/divider/power equations, chapter 2 sizing/voltage-shift equations and chapter 7 timing/rail-power sums all render as formatted math. The raw-LaTeX problem from round 3 is fixed in these views.
- **Sizing position 1:** candidate **0**, taped-out size, Wp=13.5, Wn=5, L=1, RR=30 µm. Prediction Y(0)=−0.02066 V, P=4.432 mW; schematic SPICE Y(0)=−0.03954 V; worst discrete error **39.54 mV**, max rail |I| **407.2 µA**, within band.
- **Sizing position 2:** dragged slider to candidate **45**, Wp=13.5, Wn=5, L=2, RR=20 µm. Prediction Y(0)=−0.0671 V, P=7.197 mW; SPICE Y(0)=−0.01213 V; worst error **12.13 mV**, max rail |I| **545.7 µA**, within band. Transfer curve, selected operating point, error/current marker and explanatory annotation visibly changed. These select precomputed measured candidates; dragging is not a fresh physical-cell regeneration.
- **Chapter 5:** mapped graph and expandable mapped-hierarchy schematic render successfully. The graph's input selector no longer covers its title in the captured view.
- **Chapter 8:** executed the notebook's prewritten successful edit `lo = ~((~a) | (~b)); hi = a | b;`. No agent source edit was needed. The sorter passes the independent integer reference for **9 input states**. Its **4 cells** occupy **384 × 366 µm**, drawing DRC **0**, LVS **Match**, extracted sequence **9 input states**, both outputs **PASS**. Generated schematic and GDS appear, and the lo/hi waveform shows the three voltage levels, target bands and passing samples. Displayed settling annotations: **11.26 ns** and **10.95 ns**.
- **Final summary:** prerequisite guard and source checks completed. Four recorded designs are explicitly identified as retained checks: adder4 (18/19683 selected states), full_add (27/27), mac1 (81/81), mul1 (9/9); all display DRC/LVS True. This does not turn those records into fresh Colab qualifications.

## Errors and traceback record

**No uncaught exception or Python traceback** appeared in either captured attempt. The initial queue interruption remains unexplained; it should be investigated before claiming a reliable one-click first run.

Cell 26 intentionally catches `HDLError`, passes and prints the following expected teaching diagnostic (screenshot 23):

```text
your_circuit.tv:2:17: arithmetic/comparison on trits is unsupported; use ~, &, |, nany and sized trit literals
Repair: use gates for signal arithmetic; e.g. nany(a,b) gives the negative saturated sum.
```

This is not a failing cell. The round-3 paper-figure digest RuntimeError did not recur. Recorded failed/unavailable sweep points and the published load-failure boundary are experiment evidence, not new execution failures.

## Readability and figure review

- **First screen improved:** concise introduction, visible bold Run all instruction, full overview hero and a single compact adder caption. The previous duplicated caption is gone. Body text and panel headings are readable in the current light theme. The overview's miniature HDL, GDS detail and serif footnotes remain small at normal zoom; the main message is clear.
- **Sizing paper figure:** rightmost x-axis caption is still cut off inside the embedded figure (“Max static current over input states (m…”). Plot data and title are visible. The pale 20 µm series label has low contrast. Screenshot 08 preserves this.
- **Interactive sizing widget:** both plots and slider are usable; candidate annotation and log-axis minor labels are small. The legend and titles remain separate, and both selected positions are readable in screenshots 09/10.
- **Chapter-8 outputs:** no blank schematic, layout or waveform. Colab wraps the long output in an inner scrollbar; one must scroll inside it to see schematic, then GDS, then waveform. Captures explicitly frame each output. The GDS says “Axes are in µm” but the raster primarily shows die dimensions and layer legend, with no visible axis ticks; wording could be clearer. The schematic's detailed net legend is small; its main connectivity is legible.
- **Chapter 7:** the paper load-boundary panel uses a useful pF range and is readable; the round-2 giant log-range problem is absent from this static hero. This does not test the optional EXTENDED interactive sweep plot.
- **Appendix A:** the long scope table still extends beyond the viewport's right edge and requires horizontal scrolling. Long final cache-event text also requires horizontal scrolling. The summary table and timed stages remain usable.
- Chapter 9 has a readable outlook and measurement table, no separate hero image. Chapter 5 refers to the prior arithmetic paper figure and also provides live graph/schematic outputs.

## Screenshots and records

**29 numbered screenshots**, all validated as actual PNG, **1348 × 913**. Static paper heroes are embedded published figures; the live chapter-0 result, slider, chapter-5 output, chapter-8 output and final tables were captured after execution. No uncaught error screenshot was needed; screenshot 23 records the expected caught diagnostic.

- [round4-00-first-screen.png](../../logs/colab/round4-00-first-screen.png)
- [round4-01-setup-commit.png](../../logs/colab/round4-01-setup-commit.png)
- [round4-02-setup-versions.png](../../logs/colab/round4-02-setup-versions.png)
- [round4-03-ch0-hero.png](../../logs/colab/round4-03-ch0-hero.png)
- [round4-04-ch0-live-result.png](../../logs/colab/round4-04-ch0-live-result.png)
- [round4-05-ch1-math.png](../../logs/colab/round4-05-ch1-math.png)
- [round4-06-ch1-hero.png](../../logs/colab/round4-06-ch1-hero.png)
- [round4-07-ch2-math.png](../../logs/colab/round4-07-ch2-math.png)
- [round4-08-ch2-hero.png](../../logs/colab/round4-08-ch2-hero.png)
- [round4-09-sizing-position1.png](../../logs/colab/round4-09-sizing-position1.png)
- [round4-10-sizing-position2.png](../../logs/colab/round4-10-sizing-position2.png)
- [round4-11-ch3-hero.png](../../logs/colab/round4-11-ch3-hero.png)
- [round4-12-ch4-hero.png](../../logs/colab/round4-12-ch4-hero.png)
- [round4-13-ch5-live-graph.png](../../logs/colab/round4-13-ch5-live-graph.png)
- [round4-14-ch5-schematic.png](../../logs/colab/round4-14-ch5-schematic.png)
- [round4-15-ch6-hero.png](../../logs/colab/round4-15-ch6-hero.png)
- [round4-16-ch7-math.png](../../logs/colab/round4-16-ch7-math.png)
- [round4-17-ch7-hero.png](../../logs/colab/round4-17-ch7-hero.png)
- [round4-18-ch7-scaling.png](../../logs/colab/round4-18-ch7-scaling.png)
- [round4-19-ch8-edited-hdl.png](../../logs/colab/round4-19-ch8-edited-hdl.png)
- [round4-20-ch8-schematic.png](../../logs/colab/round4-20-ch8-schematic.png)
- [round4-21-ch8-gds.png](../../logs/colab/round4-21-ch8-gds.png)
- [round4-22-ch8-waveform.png](../../logs/colab/round4-22-ch8-waveform.png)
- [round4-23-expected-hdl-error.png](../../logs/colab/round4-23-expected-hdl-error.png)
- [round4-24-ch9-outlook.png](../../logs/colab/round4-24-ch9-outlook.png)
- [round4-25-final-summary.png](../../logs/colab/round4-25-final-summary.png)
- [round4-26-final-runtime.png](../../logs/colab/round4-26-final-runtime.png)
- [round4-27-stage-times.png](../../logs/colab/round4-27-stage-times.png)
- [round4-28-runtime-deleted.png](../../logs/colab/round4-28-runtime-deleted.png)

Records: [all-cell inventory](../../logs/colab/round4-cells.json), [timing observations](../../logs/colab/round4-timing.json), [slider values](../../logs/colab/round4-slider.txt), [completed-run accessibility output](../../logs/colab/round4-results-ax.txt), [expanded final evidence](../../logs/colab/round4-results-expanded-ax.txt). Saved accessibility text redacts the Google-account identifier.

## Short history

- **Round 1 — FAIL**, `89b484bb484ca26f8bb8e1d8cb7ec26cccbea269`: setup succeeded; SciPy/NumPy failed with `AttributeError: module 'numpy._core._multiarray_umath' has no attribute '_blas_supports_fpe'`. Diagnostic manual attempts totaled 8 pass / 4 fail; runtime deleted. [Report](../../logs/colab/round1-report.md).
- **Round 2 — PASS**, `842afe27bead953c9ffd48a7ddceadb57fe0d39d`: uninterrupted Run all, **17 code cells, 384.1 s including setup**, no uncaught traceback or recovery. Runtime deleted. [Report](../../logs/colab/round2-report.md).
- **Round 3 — FAIL**, `c84145b1ed66a37a87fe0c4ffb091a405e2d4034`: setup succeeded, imports rejected `figures/out/fig_cell.svg` in `load_paper`; remaining 16 code cells unexecuted. Raw math/overflow noted, slider and chapter-8 outputs unavailable; runtime deleted. [Report](../../logs/colab/round3-report.md).

## Status, requests and validation

Round-4 verification, required captures and runtime cleanup are complete. **Functional pass with one recovery**, with the initial interruption limiting the first-run reliability claim. Interface requests: investigate that initial queue loss, repair the sizing figure's clipped caption and improve wide-table handling. No source fixes made: COLAB ownership is this report and `logs/colab/` only.

Validation: real Colab UI execution; all 18 execution counts, final prerequisite assertions, printed timings and visible outputs inspected; all 33 cells recorded; screenshot PNG decode and report-link checks. No code changes requiring local unit tests.
