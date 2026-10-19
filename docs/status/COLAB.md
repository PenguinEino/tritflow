# COLAB — round 16

2026-10-19 · real Colab via cua_repl / extension-backed Chrome · setup resource monitoring and one recovery Run all.

## Result

**First Run all: did not complete. One recovery Run all: PASS, all 35 code cells completed in 474.4 s including its setup.** Notebook ref **`b49e5c1`** (`b49e5c165446e6337513008efd933e078a8c118a`, `colab-v0`); printed implementation source **`7d981896bd8e22963664483dc8a1ab8642496357`**. No unexpected traceback in either attempt. **Exactly two Runtime → Run all selections**, the second used only after the first disconnected/lost its queue. No individual cell execution, source edits, manual restart or third Run all.

This round reproduced a **disconnect/queue-loss failure before setup output**, followed by successful recovery. It **did not reproduce the post-setup Jupyter-server/kernel replacement** seen in rounds 11/12/15: the captured log connects to the **same kernel ID** before and after the interruption, and no OOM, killed, crash or preemption message was found. Do not call the first interruption a proven kernel reset or an OOM.

**Successful recovery total: 474.4 s**, printed by the notebook; it excludes the failed first attempt and the log-inspection pause. First attempt observed for **65.3 s** from warning acceptance to confirmed stopped-state capture, with no setup output or completed-cell timer. Wall clock from first warning acceptance through observed recovery completion: **575.0 s**, including log inspection/idle time and observation latency. Neither 65.3 s nor 575.0 s is a printed notebook execution time. Setup's completed gutter shows **`1 分`**, not an exact seconds measurement.

All requested feature checks were performed on recovery outputs. Cards/enlarge, corrected three-B-curve Fig. 2, slider drag, selector, GDS download/removal, scope, and live chapter-8/9 device zoom/pan/Fit work. **Chapter 6 remains in static fallback and fails sharp live rerender.** There are readability issues below. Runtime deleted, final Manage sessions empty, test download removed. No sign-in, credentials, OAuth, notebook saving/sharing, paid runtime or implementation changes.

## Sessions and fresh runtime

Manage sessions was the first Colab action. It initially displayed **unknown notebook**; that row was protected. After refreshing the notebook and reopening Manage sessions, it resolved to the authorized **scratchpad / empty.ipynb** test session and was terminated individually at **18:36:03.593 JST**. The dialog then explicitly reported no active sessions. No unrelated notebook was terminated.

| Stage | Notebook | Last execution | Start time | RAM | Action |
|---|---|---|---|---|---|
| Initial | Unknown notebook | Not exposed | Not exposed | Not exposed | Left untouched until identified |
| Refreshed identity | `scratchpad`, `/notebooks/empty.ipynb` | `0 分前` | Not exposed | Not exposed | Terminated individually as test session |
| After scratch cleanup | None, explicit empty list | — | — | — | New runtime permitted |
| After final runtime deletion | None, explicit empty list | — | — | — | Cleanup verified |

The release was reloaded fresh. Latest Python 3 / **CPU** selection verified; Cancel used without saving settings. New runtime connected before Run all, RAM **0.88/12.67 GB**, disk **20.50/107.72 GB**. The resource panel explicitly identifies a free account with no subscription. Start time and RAM were not supplied by this round's pre-run session row; last execution is not start time.

[Session JSON](../../logs/colab/round16-sessions.json) · [initial unknown](../../logs/colab/round16-sessions-before.ax.txt) · [identified scratch](../../logs/colab/round16-sessions-identified.ax.txt) · [cleared](../../logs/colab/round16-sessions-cleared.ax.txt) · [final empty](../../logs/colab/round16-sessions-final.ax.txt).

## Interruption, log capture and recovery

| JST | Event |
|---|---|
| 18:36:40 | Initial kernel `74e73069-7354-45a8-b630-19471fd7d0ce` started |
| 18:36:41 | Connected to that kernel |
| 18:36:56.517 | First Runtime → Run all selected |
| 18:37:19.936 | GitHub “Run anyway” accepted |
| Immediately after acceptance | “ランタイムの切断” (runtime disconnected) toast; Connecting/allocation UI; setup output empty |
| 18:37:23 | Runtime log: connecting to **same** kernel `74e73069-7354-45a8-b630-19471fd7d0ce` |
| 18:37:30.734 onward | Connected, idle; blank execution counts and no setup output; resource panel stays open |
| 18:38:25.191 | First queue loss confirmed; opened View runtime logs and captured all **69** then-present entries before recovery |
| 18:38:44.453 | One authorized recovery Runtime → Run all selected; no second GitHub warning appeared |
| 18:40:36 | Recovery setup version/configuration printout in runtime log |
| 18:40:40.990 sample | Setup/imports/inputs had completed; opening adder method cell **5**, execution `[4]`, running |
| 18:43:26.513 sample | Chapter-1 method cell **8**, execution `[6]`, running; requested high-frequency monitoring ends |
| 18:46:54.960 | Completion observed, count `[35]`, printed **474.4 s** |
| 18:50:34.748 | Runtime deletion verified by Reconnect; final session dialog subsequently empty |

The first loss happened **before setup printed anything**, unlike rounds 11/12/15. Its toast was visually observed in the immediate post-warning screenshot returned by the browser tool; that immediate image was displayed in the conversation but not separately persisted. The later stopped state and the full logs are preserved. Logs were opened as soon as the loss was confirmed; this was not instantaneous at toast time, since the connected idle state was sampled first.

The initial server log says Jupyter Server 2.20.0 started at **18:34:42**, before this attempt. Both first-capture and final-capture logs show the same initial kernel and the 18:37:23 reconnection. Final logs contain **121 entries**, all saved in two 100-row pages. Searching those captured messages for **OOM / killed / crash / preempt** finds no match; no replacement kernel/server startup appears after setup. A short-lived event absent from these logs cannot be excluded, and the observations do not identify the disconnect's cause.

[First stopped notebook AX](../../logs/colab/round16-first-stopped.ax.txt) · [first 69-entry raw log](../../logs/colab/round16-first-runtime-log.ax.txt) · [69 parsed entries](../../logs/colab/round16-first-runtime-log-entries.json) · [final raw page 1](../../logs/colab/round16-final-runtime-log-page1.ax.txt) · [page 2](../../logs/colab/round16-final-runtime-log-page2.ax.txt) · [121 parsed entries](../../logs/colab/round16-final-runtime-log-entries.json) · [timing JSON](../../logs/colab/round16-timing.json).

## RAM/disk monitoring and executing cells

The **RAM/Disk resource panel remained selected/open during execution monitoring**, from before the first Run all through chapter 1 in recovery. The only exception was selecting the runtime-log tab to preserve first-loss logs before the recovery run; Resources was selected again before the second Run all.

**90 timestamped UI samples** are recorded with matching raw accessibility snapshots and numbered screenshots (`round16-monitor-000` through `089`): 13 first-attempt idle/reconnect samples and 77 recovery samples. Recovery sampling starts **0.428 s after the second Run all click** and ends at the first observed chapter-1 execution. Median recovery interval **3.002 s**. There are five longer gaps between batches/UI observations (**8.148, 25.040, 17.843, 8.024, 7.579 s**); they are retained honestly, with no interpolated readings. The first numeric sample was **10.798 s after first warning acceptance**, so the very early disconnect/allocation interval has a visual observation but no three-second numeric series.

| Phase | RAM | Disk | Cell evidence |
|---|---|---|---|
| First reconnect/idle samples | 0.92 → about 1.23 GB / 12.67 GB | 20.50 / 107.72 GB | No execution counts, no setup output |
| Recovery setup | about 1.2–1.5 / 12.67 GB | 20.50 → about 22.26 / 107.72 GB | Setup cell 1, `[1]`; spinner/global timer and matching screenshots |
| Opening adder | about 1.17–1.5 / 12.67 GB | about 22.27 / 107.72 GB | Cell 5, `[4]`; focus button verified opening method editor and visible stop/spinner |
| Chapter 1 begins | **1.39 / 12.67 GB** | **22.27 / 107.72 GB** | Cell 8, `[6]`, global timer `2 秒` |

Peak within the requested recovery monitoring window: **1.50 GB RAM**, **22.27 GB disk**. These samples show ample observed headroom but cannot rule out spikes between samples. Later during feature inspection, one displayed resource-panel reading reached **4.3/12.7 GB**, then returned to about 1.4 GB; this lies outside the three-second setup-to-chapter-1 series and did not reset the session.

The executing-cell column in the derived CSV/Markdown is **inferred from the highest execution count while Colab reports active execution**, cross-checked with spinner/focus screenshots. The raw `cells.runningLines` field includes completed execution counts as evidence and should not be read as “all these cells are simultaneously running.” Global timers sometimes displayed `0 秒` while a later cell was visibly spinning; per-cell completed gutters and the final printed timer are therefore recorded separately.

[All samples, JSON](../../logs/colab/round16-resources.json) · [CSV](../../logs/colab/round16-resources.csv) · [readable 90-row sample table](../../logs/colab/round16-resource-samples.md) · [sampling summary/gaps](../../logs/colab/round16-resource-summary.json). For example, [setup sample 041](../../logs/colab/round16-monitor-041.png), [opening-adder sample 066](../../logs/colab/round16-monitor-066.png), [chapter-1 sample 089](../../logs/colab/round16-monitor-089.png).

## Setup identity, tools and tracebacks

Recovery setup printed:

```text
Source: https://github.com/PenguinEino/tritflow.git ref=7d981896bd8e22963664483dc8a1ab8642496357 commit=7d981896bd8e22963664483dc8a1ab8642496357
Scientific Python (loaded host modules preserved): numpy=2.1.3, scipy=1.16.3, matplotlib=3.10.0, plotly=5.24.1
KLayout executable: /content/tritflow-runtime/bin/klayout
KLayout 0.30.6
ngspice executable: /content/tritflow-runtime/bin/ngspice
******
** ngspice-42 : Circuit level simulation program
** Compiled with KLU Direct Linear Solver
```

[Setup AX before deletion](../../logs/colab/round16-setup-final.ax.txt) · [source/versions screenshot](../../logs/colab/round16-43-setup-identity-versions.png). The setup count `[1]` and displayed `1 分` were captured before runtime deletion; deletion subsequently clears counts while retaining output. Completed per-cell data comes from the pre-deletion snapshot.

**Unexpected traceback: none present.** No expanded or collapsed Python traceback was available to copy. Cell 45 intentionally catches and prints this expected HDL diagnostic, then succeeds:

```text
your_circuit.tv:3:14: arithmetic/comparison on trits is unsupported; use ~, &, |, nany and sized trit literals
Repair: use gates for signal arithmetic; e.g. nany(a, b) gives the negative saturated sum.
```

This is a successful teaching demonstration, not a notebook failure. The complete evidence/outcome is mirrored in `logs/COLAB.last.md`.

## Features and readability

The user required these checks if the first run passed; because recovery generated all outputs successfully, they were also completed on the recovery session without rerunning any cell.

| Feature | Observed result |
|---|---|
| Chapter 1 cards + click enlarge | **pass_with_readability_issue** — INV/NAND/NOR/NANY truth tables, explanations and schematics render. INV click enlarges inline and a second click shrinks it. Thumbnail labels are small; enlarged resistor/body parameter labels remain crowded/overlapping; enlargement requires vertical scrolling. |
| Fig. 2 three B curves | **pass** — Regenerated DC output/current panels show distinct blue B=-1, gray B=0 and red B=+1 curves for NAND/NOR/NANY. Fonts and colors have the paper styling; A=0 INV Y=-39.5 mV, current=0.407 mA. |
| Chapter 2 slider drag | **pass** — Dragged orange handle from candidate 0 to candidate 30; Wp 11, Wn 5, L 2, RR 45 µm; SPICE Y(0)=-0.1514 V, worst error 151.4 mV, max rail current 242.4 µA. Readout and selected curve/point change. |
| Chapter 6 GDS zoom/pan/Fit | **partial_fail_live_detail** — Wheel zoom, drag pan and Fit work, but viewer fell back to Static overview · rerun in Colab for live detail while Run all was busy. It remained static after completion and further wheel zoom. Device structures become visible but enlarged raster is pixelated; sharp live rerender FAILED. No cell was rerun to repair it. |
| Chapter 8 GDS zoom/pan/Fit | **pass** — Wheel zoom reached transistor/contact detail, live status rose to 3 updates, pan and Fit to 5 updates; contacts/patterns rerender sharply. Download minmax.gds visible. |
| Chapter 9 GDS zoom/pan/Fit | **pass** — Wheel zoom from framed chip into core transistors, pan, Fit; live update count reached 8 and detail remains sharp. At full-chip fit, supply/pad/net labels overlap heavily; zoom resolves device detail. Download tr_1um_adder4.gds visible. |
| One GDS download and removal | **pass** — Clicked adder2_demo.gds once; Downloads file completed, 179548 bytes, SHA-256 2779ea628a56eb46e45922905f1ef5656922dc15981867a48735d94669c4456b. Deleted that exact new test file and verified absent; no unrelated files touched. |
| Chapter 5 selector | **pass** — a=-1,b=0 produced sum=-1,carry=0; a=0,b=+1 produced sum=+1,carry=0. Selection highlights, outputs line and blue/gray/red wires changed. Flat drawing fits in the output without horizontal scrolling. |
| Chapter 8 dark scope + ngspice 42 header | **pass_with_readability_issue** — Five dark lanes v(a), v(b), v(lo), v(hi), \|i(vdd)\|, distinct colors, output check markers and current lane render. Header explicitly says ngspice 42, .tran 2e-09 9e-06 0 2e-09, 4 cells/12 MOSFETs/8 resistors/8 wire C, 27 °C, 4699 points. Header metadata is small/dim; tall plot can require page/output scrolling. |

[Feature JSON with evidence filenames](../../logs/colab/round16-feature-checks.json). The downloaded file's SHA-256 agrees with the viewer's displayed prefix `2779ea628a56eb46…`; [download evidence and deletion](../../logs/colab/round16-download.json), [initial Downloads inventory](../../logs/colab/round16-downloads-before.json).

The fixed-width main figures leave unused space at this wide screen size. Body prose, highlighted Verilog and selector controls are readable. The chapter-1 cards are tall enough to create a nested output scrollbar before Fig. 2; enlargement makes schematic labels larger but can put part of the drawing below the viewport. The current Fig. 2 uses readable serif/math labels and the correct distinct curve colors. At chip Fit, pad/rail/net labels overlap; transistor zoom is crisp. The scope traces/colored lane names are readable, but header metadata is smaller and lower contrast. With the resource panel open, some tall figures need page/output scrolling to see all lanes or the bottom of GDS; no horizontal scrolling was required for the flat half-adder selector. Screenshot dimensions varied with the live desktop viewport; no viewport override, browser zoom or notebook style change was applied.

The intro still cites historical `839adbf` / **299.3 s**. This round's result is **recovery completion, 474.4 s**, not a new first-run reliability pass.

## Every cell

Zero-based notebook indices. **35 code cells passed in the second Run all**, final execution counts **1–35**, 22 text cells rendered. All 35 code cells had blank counts/no output after the first failed attempt; [first-attempt cell records](../../logs/colab/round16-first-cells.json) remain separate. `0 秒` is Colab's rounded display, not an exact zero-duration measurement. Minute gutters are preserved verbatim rather than converted to falsely precise seconds. No unexpected traceback in any cell.

| Cell | Type | Purpose | Recovery execution | Displayed time | Status | Traceback |
|---:|---|---|---:|---|---|---|
| 0 | text | TritFlow: balanced-ternary HDL to GDS on OpenSUSI TR-1um | — | — | rendered | none |
| 1 | code | Setup (collapsed form) | 1 | 1 分 | pass | none |
| 2 | code | Imports and run bookkeeping | 2 | 2 秒 | pass | none |
| 3 | text | From HDL to a checked adder layout; highlighted adder.tv definition | — | — | rendered | none |
| 4 | code | Chapter 0 inputs: test conditions and an independent integer oracle | 3 | 0 秒 | pass | none |
| 5 | code | Chapter 0 public API: HDL → GDS → extracted SPICE | 4 | 2 分 | pass | none |
| 6 | code | Chapter 0 checks | 5 | 0 秒 | pass | none |
| 7 | text | Three levels from ordinary CMOS | — | — | rendered | none |
| 8 | code | Chapter 1 public API: gates and DC | 6 | 6 秒 | pass | none |
| 9 | text |  | — | — | rendered | none |
| 10 | code | Chapter 1 checks and the taped-out INV schematic | 7 | 0 秒 | pass | none |
| 11 | text | Sizing sets the middle level | — | — | rendered | none |
| 12 | code | Chapter 2 public API: sizing slider | 8 | 1 秒 | pass | none |
| 13 | code | Chapter 2 details: resistor-length candidates at the taped-out MOS sizes | 9 | 0 秒 | pass | none |
| 14 | text | Taped-out circuits become placeable cells | — | — | rendered | none |
| 15 | code | Chapter 3 public API: cell view | 10 | 0 秒 | pass | none |
| 16 | code | Chapter 3 checks: template, clamp devices and cell qualification | 11 | 0 秒 | pass | none |
| 17 | text | Describe signed arithmetic in TritVerilog | — | — | rendered | none |
| 18 | text | Chapter 4 highlighted half_add.tv and full_add.tv definitions | — | — | rendered | none |
| 19 | code | Chapter 4 public API: arithmetic | 12 | 0 秒 | pass | none |
| 20 | code | Chapter 4 checks: cell counts against the taped-out schematics | 13 | 0 秒 | pass | none |
| 21 | text | Follow an expression into cells | — | — | rendered | none |
| 22 | code | Chapter 5 public API: synthesis and interactive half-adder schematic | 14 | 0 秒 | pass | none |
| 23 | code | Chapter 5 checks: mapping rules and gate-level TritVerilog | 15 | 0 秒 | pass | none |
| 24 | code | Chapter 5 public API: two-trit adder hierarchy schematic | 16 | 0 秒 | pass | none |
| 25 | text | Route signals and feed the standing current | — | — | rendered | none |
| 26 | code | Chapter 6 public API: P&R view | 17 | 0 秒 | pass | none |
| 27 | code | Chapter 6 details and an optional floorplan experiment | 18 | 0 秒 | pass | none |
| 28 | text | Does the layout still work? | — | — | rendered | none |
| 29 | code | Chapter 7 public API: device-only SPICE and wire overlay | 19 | 2 分 | pass | none |
| 30 | code | Chapter 7 checks: identical devices with and without wire C | 20 | 0 秒 | pass | none |
| 31 | text | Chapter 7 scaling and power evidence | — | — | rendered | none |
| 32 | code | Chapter 7 recorded width and load campaigns | 21 | 0 秒 | pass | none |
| 33 | text | Predict with static timing, confirm with SPICE | — | — | rendered | none |
| 34 | code | Chapter 7 public API: STA vs SPICE | 22 | 0 秒 | pass | none |
| 35 | code | Chapter 7 STA comparison table and critical path | 23 | 0 秒 | pass | none |
| 36 | text | STA validation figure and scope | — | — | rendered | none |
| 37 | text | Change the circuit and close the loop | — | — | rendered | none |
| 38 | code | Chapter 8 editable formatted TritVerilog source definition | 24 | 0 秒 | pass | none |
| 39 | code | Chapter 8 circuit selection and independent reference setup | 25 | 0 秒 | pass | none |
| 40 | code | Chapter 8 synthesis / truth table | 26 | 0 秒 | pass | none |
| 41 | code | Chapter 8 check: every input state against the independent arithmetic reference | 27 | 0 秒 | pass | none |
| 42 | code | Chapter 8 public API: layout | 28 | 16 秒 | pass | none |
| 43 | code | Chapter 8: extracted SPICE of your layout and its waveform | 29 | 30 秒 | pass | none |
| 44 | text | Expected diagnostic introduction | — | — | rendered | none |
| 45 | code | Chapter 8 expected caught HDL error | 30 | 0 秒 | pass | none |
| 46 | text | Next: compare the model with silicon | — | — | rendered | none |
| 47 | text | From your HDL to a shuttle-ready top | — | — | rendered | none |
| 48 | code | Chapter 9 recorded chip image and signoff table | 31 | 0 秒 | pass | none |
| 49 | code | Chapter 9 checks: recorded signoff snapshot and pad map | 32 | 0 秒 | pass | none |
| 50 | text | Chip results and remaining submission requirements | — | — | rendered | none |
| 51 | text | Appendix A. What the results establish | — | — | rendered | none |
| 52 | text | Appendix B. Verification evidence and how to rerun | — | — | rendered | none |
| 53 | code | Appendix B: cell characterization and fanout evidence | 33 | 0 秒 | pass | none |
| 54 | code | Appendix B: four-design physical and timing campaign | 34 | 0 秒 | pass | none |
| 55 | code | Appendix B: evidence tables, provenance and run time | 35 | 0 秒 | pass | none |
| 56 | text | Appendix C. Use and extend TritFlow | — | — | rendered | none |

[Recovery cell JSON](../../logs/colab/round16-cells.json) · [complete notebook AX before deletion](../../logs/colab/round16-completed.ax.txt).

## Screenshots and cleanup

Real browser captures, converted from the tool's image payload to actual PNG without changing content. Numbered event/feature captures are below; the additional **90 monitoring screenshots** share their sample numbers with AX snapshots and resource records. Some earlier captures show only part of a tall figure; later complete captures are named explicitly.

- [round16-00-sessions.png](../../logs/colab/round16-00-sessions.png)
- [round16-01-first-screen.png](../../logs/colab/round16-01-first-screen.png)
- [round16-02-first-runtime-log.png](../../logs/colab/round16-02-first-runtime-log.png)
- [round16-03-recovery-ch0-running.png](../../logs/colab/round16-03-recovery-ch0-running.png)
- [round16-04-cell-cards.png](../../logs/colab/round16-04-cell-cards.png)
- [round16-05-schematic-enlarged.png](../../logs/colab/round16-05-schematic-enlarged.png)
- [round16-06-fig2.png](../../logs/colab/round16-06-fig2.png)
- [round16-07-slider-before.png](../../logs/colab/round16-07-slider-before.png)
- [round16-08-slider-after.png](../../logs/colab/round16-08-slider-after.png)
- [round16-09-ch6-gds-fit.png](../../logs/colab/round16-09-ch6-gds-fit.png)
- [round16-10-ch6-gds-zoom.png](../../logs/colab/round16-10-ch6-gds-zoom.png)
- [round16-11-ch6-device-zoom.png](../../logs/colab/round16-11-ch6-device-zoom.png)
- [round16-12-ch6-pan.png](../../logs/colab/round16-12-ch6-pan.png)
- [round16-13-ch6-refit.png](../../logs/colab/round16-13-ch6-refit.png)
- [round16-14-gds-download.png](../../logs/colab/round16-14-gds-download.png)
- [round16-15-current-execution.png](../../logs/colab/round16-15-current-execution.png)
- [round16-16-selector-a-neg-b-zero.png](../../logs/colab/round16-16-selector-a-neg-b-zero.png)
- [round16-17-selector-a-zero-b-pos.png](../../logs/colab/round16-17-selector-a-zero-b-pos.png)
- [round16-18-ch8-gds-fit.png](../../logs/colab/round16-18-ch8-gds-fit.png)
- [round16-19-ch2-hero.png](../../logs/colab/round16-19-ch2-hero.png)
- [round16-20-ch3-hero.png](../../logs/colab/round16-20-ch3-hero.png)
- [round16-21-ch4-hero.png](../../logs/colab/round16-21-ch4-hero.png)
- [round16-22-ch6-hero.png](../../logs/colab/round16-22-ch6-hero.png)
- [round16-23-ch8-schematic.png](../../logs/colab/round16-23-ch8-schematic.png)
- [round16-24-final-summary.png](../../logs/colab/round16-24-final-summary.png)
- [round16-25-ch6-idle-zoom.png](../../logs/colab/round16-25-ch6-idle-zoom.png)
- [round16-26-ch6-device-detail-static.png](../../logs/colab/round16-26-ch6-device-detail-static.png)
- [round16-27-ch8-device-zoom.png](../../logs/colab/round16-27-ch8-device-zoom.png)
- [round16-28-ch8-pan.png](../../logs/colab/round16-28-ch8-pan.png)
- [round16-29-ch8-refit.png](../../logs/colab/round16-29-ch8-refit.png)
- [round16-30-ch9-fit.png](../../logs/colab/round16-30-ch9-fit.png)
- [round16-31-ch9-device-zoom.png](../../logs/colab/round16-31-ch9-device-zoom.png)
- [round16-32-ch9-pan.png](../../logs/colab/round16-32-ch9-pan.png)
- [round16-33-ch9-refit.png](../../logs/colab/round16-33-ch9-refit.png)
- [round16-34-ch8-scope.png](../../logs/colab/round16-34-ch8-scope.png)
- [round16-35-ch8-scope-all-lanes.png](../../logs/colab/round16-35-ch8-scope-all-lanes.png)
- [round16-36-scope-overview.png](../../logs/colab/round16-36-scope-overview.png)
- [round16-37-final-runtime-log.png](../../logs/colab/round16-37-final-runtime-log.png)
- [round16-38-setup-versions.png](../../logs/colab/round16-38-setup-versions.png)
- [round16-39-ch0-results.png](../../logs/colab/round16-39-ch0-results.png)
- [round16-40-runtime-deleted.png](../../logs/colab/round16-40-runtime-deleted.png)
- [round16-41-sessions-final.png](../../logs/colab/round16-41-sessions-final.png)
- [round16-42-expected-hdl-diagnostic.png](../../logs/colab/round16-42-expected-hdl-diagnostic.png)
- [round16-43-setup-identity-versions.png](../../logs/colab/round16-43-setup-identity-versions.png)
- [round16-44-fig2-complete.png](../../logs/colab/round16-44-fig2-complete.png)

Runtime → Disconnect and delete runtime confirmed; Reconnect verified **18:50:34.748 JST**. Final Manage sessions explicitly empty. The one downloaded test GDS was deleted; unrelated files untouched. [Cleanup AX](../../logs/colab/round16-cleanup.ax.txt).

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
- **Round 10 — FIRST-RUN PASS**, `0ffe7a1`: 35 code/22 text cells, **300.7 s** including setup. Two selector input pairs changed outputs and wire colours correctly; flat half-adder fit, side legends readable. fig_synth auxiliary pin/net annotations remained small. Runtime deleted. [Report](../../logs/colab/round10-report.md).
- **Round 11 — FAIL/incomplete**, `134dfe7`: setup printed versions, execution state reset and new server/kernel started; no traceback or regenerated Fig. 2. One Run all, no retry; runtime deleted. [Report](../../logs/colab/round11-report.md).
- **Round 12 — FAIL/incomplete**, `839adbf`: setup end followed by new server/kernel at 12:23:44/50 and loss of queue; no traceback. One Run all, no retry; runtime deleted. [Report](../../logs/colab/round12-report.md).
- **Round 13 — FIRST-RUN EXECUTION PASS**, `839adbf`: other test sessions cleared; all 35 code cells completed in **299.3 s**. No post-setup kernel restart, sole current session before/after. Fig. 2 DC-family discrepancy reported. Runtime deleted. [Report](../../logs/colab/round13-report.md).

- **Round 14 — a90844e:** first/only Run all failed in setup after approximately **8.0 s** (rounded gutter), because it cloned stale `839adbf` and could not import `setup_identity`. One code error, 34 not run; new features blocked. Test sessions cleared first; runtime deleted. [Report](../../logs/colab/round14-report.md).

- **Round 15 — b49e5c1 / source 7d981896…:** correct pin and tool versions, then new server/kernel after setup; first/only Run all lost its queue, 34 later cells not run, no traceback. Completed time unavailable (251.7 s observed attempt only). Features blocked; runtime deleted. [Report](../../logs/colab/round15-report.md).

## Status and interface requests

Verification, one authorized recovery, interactive checks and cleanup are complete. **First-run reliability remains a failure; recovery works on this observed disconnect.** The older post-setup server/kernel reset was not reproduced, so its recovery under this exact notebook remains unproven. Investigate chapter-6 viewer timeout/static fallback (it does not recover after the kernel becomes idle), crowded schematic labels and tall/nested outputs. COLAB changed only status/evidence files, not implementation or git state.
