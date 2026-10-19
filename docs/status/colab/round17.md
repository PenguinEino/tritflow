<!-- Archived copy; evidence files live in the ignored logs/colab/ directory. -->
# COLAB — round 17

2026-10-19 · real Google Colab via cua_repl / extension-backed Chrome · reset reproduction and one recovery attempt.

## Result

**FAIL on both the first Run all and the one authorized recovery Run all.** Notebook **`181206b`** (`181206ba804bc800231dc31447e091ee32496d25`, `colab-v0`); setup printed the expected immutable source **`5159190774611f3bac3cb9dd36532e005caa2aed`**. The post-setup **server/kernel reset was reproduced twice**, and the recovery did not complete.

**Total observed attempt: 429.2 s** — wall clock from first GitHub warning acceptance to final stopped-state capture, including reconnects, log inspection and recovery. **Completed Run-all total: unavailable**; neither attempt produced the final timer. The first disconnect sample occurred **127.4 s** after warning acceptance; the second occurred **124.0 s** after the recovery click. These are observation intervals, not printed execution times. Both completed setup gutters displayed **`1 分`**, with rounded times preserved below.

In each attempt: setup cell 1, imports cell 2 and chapter-0 inputs cell 4 completed; **chapter-0 method cell 5 was executing when the runtime reset**; the remaining **31 code cells never ran**. Thus each attempt has **3 completed code cells, 1 interrupted, 31 not run**, plus 22 rendered text cells. Final counts were cleared by reset. No unexpected Python traceback appeared. Exactly **two Runtime → Run all** selections, no third attempt, no individual cell runs, edits or manual restart.

**All requested feature checks remain blocked.** No chapter-1 cards/figure, chapter-6 viewer, chapter-8 scope or chip-viewer output was generated. The screenshots document absence rather than qualifying the fixes. Runtime deleted and final Manage sessions explicitly empty. No credentials, sign-in, OAuth, notebook saving/sharing, paid tier, GDS download or unrelated-file deletion.

## Session cleanup and runtime

Manage sessions was the first Colab action. It explicitly reported **no active sessions**: no scratch `empty.ipynb`, earlier TritFlow or unrelated notebook needed termination. The notebook was reloaded fresh afterward. Python 3 / latest / **CPU selected** was verified in Runtime type, then Cancel used without saving settings. Fresh connection observed **19:24:45.482 JST**, RAM **0.87/12.67 GB**, disk **20.50/107.72 GB**. The Resources panel confirmed no subscription and remained selected during the sampled execution windows.

| Observation | Active session | Last execution | Start time | RAM | Action |
|---|---|---|---|---|---|
| Before fresh reload | Explicitly none | — | — | — | Nothing to terminate |
| After both resets | Current `tritflow_tr1um.ipynb` only | `0 分前` | Not exposed | **1.25 GB** | Kept for evidence, then deleted |
| After deletion | Explicitly none | — | — | — | Cleanup verified |

No unrelated session was terminated. Open browser tabs were not treated as active runtime sessions. The last-execution field is not a runtime start time.

Session JSON (`logs/colab/round17-sessions.json`, kept outside git) · initial empty list (`logs/colab/round17-sessions-before.ax.txt`, kept outside git) · post-reset current session (`logs/colab/round17-sessions-after-resets.ax.txt`, kept outside git) · final empty list (`logs/colab/round17-sessions-final.ax.txt`, kept outside git) · CPU configuration (`logs/colab/round17-cpu.ax.txt`, kept outside git).

## Both resets and logs

| JST | Event |
|---|---|
| 19:24:29 | Initial kernel `7bbb386f-2dee-4b68-ac91-10bca197649a` started |
| 19:24:51.880 | First Runtime → Run all selected |
| 19:25:10.268 | GitHub “Run anyway” accepted |
| 19:26:15.373 | Setup RAM sample peaked at **8.39/12.67 GB**, disk 21.62 GB |
| 19:26:53 | First setup printed KLayout 0.30.6 / ngspice 42 in runtime log |
| 19:27:14.625 | Cell 5 running `[4]`, timer **16 秒**, RAM **1.36 GB**, disk **22.26 GB** |
| 19:27:17.627 | Connecting state; execution counts cleared; numeric resources unavailable |
| 19:27:32 | New **Jupyter Server 2.20.0** startup |
| 19:27:42 | New kernel **`4c2288ac-4fad-4752-9a4c-d8cccf97cbe0`** started |
| 19:27:45.461 | Connected idle, RAM 0.96 GB / disk 20.50 GB; queue did not resume |
| 19:28:15.850 | One authorized recovery Runtime → Run all selected |
| 19:29:45 | Recovery setup printed KLayout/ngspice versions |
| 19:30:16.801 | Cell 5 running `[4]`, timer **27 秒**, RAM **1.22 GB**, disk **22.27 GB** |
| 19:30:19.802 | Recovery Connecting state; counts cleared again |
| 19:30:37 | Another new **Jupyter Server 2.20.0** startup |
| 19:30:46 | New kernel **`7071ebee-7b6a-4267-bd0c-723ef17308cb`** started |
| 19:30:51.204 | Connected idle, RAM 0.97 GB / disk 20.50 GB; no resumed execution |
| 19:32:19.454 | Final stopped-state capture; no closing timer/output |
| 19:32:35.147 | Runtime deletion verified by Reconnect |

This is stronger evidence than a frontend-only reconnect: **the server startup repeats, kernel IDs change, resource readings reset, and counts clear**. In both attempts setup had completed and cell 5 had begun. The failure is therefore more precisely located than “setup stopped”: it occurs shortly after setup while the opening adder method is active.

The UI displayed **Connecting / allocating runtime** (`ランタイムを割り当て中`), followed by an idle connection. A generic **runtime disconnected** toast (`ランタイムの切断`) is visible in the reset-adjacent screenshots, including monitor 038/039 and 082. No reason-specific session-crashed/restarted or OOM toast was observed. AX state and screenshot are captured sequentially, not atomically: monitor 038 still has the last running AX/resource reading while its screenshot already shows the disconnect. The sample timestamp applies to the start of that observation, not a guaranteed instant shared by both representations. Matching screenshots/AX snapshots preserve both transitions. Runtime → View runtime logs was attempted immediately after the first observed disconnect, but was disabled while disconnected. It was opened on reconnect. The same procedure captured the second reset; the unavailable controls are also preserved.

The first log capture has **188 entries** across two 100-row pages. The second has **308 entries** across four pages, including the first reset history. Searches of all captured messages for **OOM, killed, crash, preempt** found no matches. Neither log states the cause. The earlier **8.39 GB** setup peak is real evidence, but it neither proves OOM nor excludes a shorter unsampled spike. Last sampled RAM immediately before each reset was much lower. Initial and post-reset session inventories did not show a competing active scratch notebook; that does not establish a root cause.

First log page 1 (`logs/colab/round17-first-runtime-log-page1.ax.txt`, kept outside git) · page 2 (`logs/colab/round17-first-runtime-log-page2.ax.txt`, kept outside git) · 188 parsed entries (`logs/colab/round17-first-runtime-log-entries.json`, kept outside git). Second log page 1 (`logs/colab/round17-second-runtime-log-page1.ax.txt`, kept outside git) · page 2 (`logs/colab/round17-second-runtime-log-page2.ax.txt`, kept outside git) · page 3 (`logs/colab/round17-second-runtime-log-page3.ax.txt`, kept outside git) · page 4 (`logs/colab/round17-second-runtime-log-page4.ax.txt`, kept outside git) · 308 parsed entries (`logs/colab/round17-second-runtime-log-entries.json`, kept outside git).

First reconnect log control unavailable (`logs/colab/round17-log-unavailable-during-reconnect.ax.txt`, kept outside git) · second unavailable (`logs/colab/round17-second-log-disabled.ax.txt`, kept outside git) · first stopped AX (`logs/colab/round17-first-stopped.ax.txt`, kept outside git) · second stopped AX (`logs/colab/round17-second-stopped.ax.txt`, kept outside git) · timing JSON (`logs/colab/round17-timing.json`, kept outside git).

## Resource samples and execution evidence

**89 timestamped samples**, each with raw AX and screenshot, recorded approximately every **3 s** while setup/early execution ran and through reconnect. Chapter 1 was never reached in either attempt. The resource panel stayed selected for all recorded samples; selecting the log tab occurred between attempts and after the second reset.

| Attempt | Samples | Median interval | Longest interval | Peak RAM | Peak disk |
|---|---:|---:|---:|---:|---:|
| First Run all | 45 | **3.002 s** | **15.825 s** | **8.39 / 12.67 GB** | **22.29 / 107.72 GB** |
| Recovery Run all | 44 | **3.002 s** | **16.391 s** | **1.50 / 12.67 GB** | **22.27 / 107.72 GB** |

The first sample followed warning acceptance immediately, and the first recovery sample followed its Run-all click by about **0.428 s**. Sampling has small batch/UI gaps, explicitly listed in summary JSON (`logs/colab/round17-resource-summary.json`, kept outside git): first attempt 7.204, 8.215 and 15.825 s; recovery 5.619, 8.627, 7.204 and 16.391 s. The longest gaps follow disconnect detection while runtime-log availability was checked. There are no invented/interpolated readings. Null resources mean unavailable during reconnect, not zero use.

The executing-cell column is **inferred from the highest execution count while the global running timer is active**, supported by AX counts and matching screen captures. Setup is cell 1 `[1]`; imports/input cells complete quickly; opening method is cell 5 `[4]`. Once counts clear, no running cell is claimed. The displayed last-running timers (**16 秒**, **27 秒**) are not completed wall times for cell 5.

All samples JSON (`logs/colab/round17-resources.json`, kept outside git) · CSV (`logs/colab/round17-resources.csv`, kept outside git) · full readable 89-row table (`logs/colab/round17-resource-samples.md`, kept outside git). Matching artifacts are `round17-monitor-000` through `088`. Key images: 8.39 GB setup peak, 020 (`logs/colab/round17-monitor-020.png`, kept outside git), before first reset, 038 (`logs/colab/round17-monitor-038.png`, kept outside git), first Connecting state, 039 (`logs/colab/round17-monitor-039.png`, kept outside git), before second reset, 081 (`logs/colab/round17-monitor-081.png`, kept outside git), second Connecting state, 082 (`logs/colab/round17-monitor-082.png`, kept outside git).

## Printed source, tools and traceback

The retained setup output from the current notebook is:

```text
Source: https://github.com/PenguinEino/tritflow.git ref=5159190774611f3bac3cb9dd36532e005caa2aed commit=5159190774611f3bac3cb9dd36532e005caa2aed
Scientific Python (loaded host modules preserved): numpy=2.1.3, scipy=1.16.3, matplotlib=3.10.0, plotly=5.24.1
KLayout executable: /content/tritflow-runtime/bin/klayout
KLayout 0.30.6
ngspice executable: /content/tritflow-runtime/bin/ngspice
******
** ngspice-42 : Circuit level simulation program
** Compiled with KLU Direct Linear Solver
```

Setup AX (`logs/colab/round17-setup-final.ax.txt`, kept outside git) · setup source/versions screenshot (`logs/colab/round17-07-setup-source-versions.png`, kept outside git). Both attempts progressed beyond setup into imports, inputs and the opening method; the expected immutable implementation pin is verified.

**Complete unexpected traceback: none present.** There was no collapsed traceback to expand. Cell 5 resets without a Python exception output. The deliberately caught HDL diagnostic in cell 45 also did not run. This outcome and evidence are mirrored in `logs/COLAB.last.md`.

## Requested feature checks

| Check | Round-17 result |
|---|---|
| Chapter 6 live sharp rerender after busy Run all | **Blocked** — No GDS viewer was generated in either attempt; live rerender/zoom/pan/Fit not testable. |
| Chapter 9 chip Fit without overlapping labels | **Blocked** — Chip-viewer method never ran; Fit label suppression and zoom behavior not assessed. |
| Chapter 1 tab cards: INV/NAND/NOR/NANY/Support | **Blocked** — Chapter 1 never began. No card tabs could be switched. |
| Chapter 1 schematic opens full size in a new tab, close it | **Blocked** — No schematic output to click; no new schematic tab was opened or closed. |
| Chapter 8 readable scope header | **Blocked** — Waveform cell never ran; revised header readability unverified. |
| Fig. 2 three B curves | **Blocked** — No live sweeps or regenerated figure output. |
| Sizing slider | **Blocked** — Explorer cell never ran; no drag possible. |
| Chapter 5 trit selector | **Blocked** — Synthesis selector cell never ran; no button interaction possible. |
| One GDS download then delete | **Blocked** — No generated GDS download button; no download started and no file created/deleted. |

Feature JSON (`logs/colab/round17-feature-checks.json`, kept outside git). No GDS download was attempted or created; no Downloads file needed deletion. No schematic new tab was opened because no card output existed. Do not treat the round-16 successful recovery outputs or local images as verification of source `5159190`.

The first screen and existing static prose/paper assets render in the light theme, with readable body text and smaller fixed-width figure captions. The requested changes to card-tab usability, chip labels, chapter-6 sharp rerender and scope-header readability cannot be assessed from absent outputs. Later screenshots explicitly show the unexecuted method cells and empty final summary.

## Every cell in both attempts

Zero-based indices, **35 code / 22 text**. Each attempt's execution counts reached `[4]` before reset. The completed times below were preserved from the **last numeric pre-reset snapshots** (`038` and `081`), not reconstructed from the cleared final UI. Both attempts have the same three completed cells and same interrupted cell. The execution column applies to either attempt. `1 分`, `3 秒` and `0 秒` are Colab's rounded display; no falsely precise conversion is made. No cell has an unexpected traceback.

| Cell | Type | Purpose | Execution before reset | First displayed time | Recovery displayed time | Status in both attempts | Traceback |
|---:|---|---|---:|---|---|---|---|
| 0 | text | TritFlow: balanced-ternary HDL to GDS on OpenSUSI TR-1um | — | — | — | rendered | none |
| 1 | code | Setup (collapsed form) | 1 | 1 分 | 1 分 | completed_before_reset | none |
| 2 | code | Imports and run bookkeeping | 2 | 3 秒 | 3 秒 | completed_before_reset | none |
| 3 | text | From HDL to a checked adder layout; highlighted adder.tv definition | — | — | — | rendered | none |
| 4 | code | Chapter 0 inputs: test conditions and an independent integer oracle | 3 | 0 秒 | 0 秒 | completed_before_reset | none |
| 5 | code | Chapter 0 public API: HDL → GDS → extracted SPICE | 4 | interrupted; last timer 16 秒 | interrupted; last timer 27 秒 | interrupted_runtime_reset | none |
| 6 | code | Chapter 0 checks | — | — | — | not_run_queue_lost | none |
| 7 | text | Three levels from ordinary CMOS | — | — | — | rendered | none |
| 8 | code | Chapter 1 public API: gates and DC | — | — | — | not_run_queue_lost | none |
| 9 | text |  | — | — | — | rendered | none |
| 10 | code | Chapter 1 checks and the taped-out INV schematic | — | — | — | not_run_queue_lost | none |
| 11 | text | Sizing sets the middle level | — | — | — | rendered | none |
| 12 | code | Chapter 2 public API: sizing slider | — | — | — | not_run_queue_lost | none |
| 13 | code | Chapter 2 details: resistor-length candidates at the taped-out MOS sizes | — | — | — | not_run_queue_lost | none |
| 14 | text | Taped-out circuits become placeable cells | — | — | — | rendered | none |
| 15 | code | Chapter 3 public API: cell view | — | — | — | not_run_queue_lost | none |
| 16 | code | Chapter 3 checks: template, clamp devices and cell qualification | — | — | — | not_run_queue_lost | none |
| 17 | text | Describe signed arithmetic in TritVerilog | — | — | — | rendered | none |
| 18 | text | Chapter 4 highlighted half_add.tv and full_add.tv definitions | — | — | — | rendered | none |
| 19 | code | Chapter 4 public API: arithmetic | — | — | — | not_run_queue_lost | none |
| 20 | code | Chapter 4 checks: cell counts against the taped-out schematics | — | — | — | not_run_queue_lost | none |
| 21 | text | Follow an expression into cells | — | — | — | rendered | none |
| 22 | code | Chapter 5 public API: synthesis and interactive half-adder schematic | — | — | — | not_run_queue_lost | none |
| 23 | code | Chapter 5 checks: mapping rules and gate-level TritVerilog | — | — | — | not_run_queue_lost | none |
| 24 | code | Chapter 5 public API: two-trit adder hierarchy schematic | — | — | — | not_run_queue_lost | none |
| 25 | text | Route signals and feed the standing current | — | — | — | rendered | none |
| 26 | code | Chapter 6 public API: P&R view | — | — | — | not_run_queue_lost | none |
| 27 | code | Chapter 6 details and an optional floorplan experiment | — | — | — | not_run_queue_lost | none |
| 28 | text | Does the layout still work? | — | — | — | rendered | none |
| 29 | code | Chapter 7 public API: device-only SPICE and wire overlay | — | — | — | not_run_queue_lost | none |
| 30 | code | Chapter 7 checks: identical devices with and without wire C | — | — | — | not_run_queue_lost | none |
| 31 | text | Chapter 7 scaling and power evidence | — | — | — | rendered | none |
| 32 | code | Chapter 7 recorded width and load campaigns | — | — | — | not_run_queue_lost | none |
| 33 | text | Predict with static timing, confirm with SPICE | — | — | — | rendered | none |
| 34 | code | Chapter 7 public API: STA vs SPICE | — | — | — | not_run_queue_lost | none |
| 35 | code | Chapter 7 STA comparison table and critical path | — | — | — | not_run_queue_lost | none |
| 36 | text | STA validation figure and scope | — | — | — | rendered | none |
| 37 | text | Change the circuit and close the loop | — | — | — | rendered | none |
| 38 | code | Chapter 8 editable formatted TritVerilog source definition | — | — | — | not_run_queue_lost | none |
| 39 | code | Chapter 8 circuit selection and independent reference setup | — | — | — | not_run_queue_lost | none |
| 40 | code | Chapter 8 synthesis / truth table | — | — | — | not_run_queue_lost | none |
| 41 | code | Chapter 8 check: every input state against the independent arithmetic reference | — | — | — | not_run_queue_lost | none |
| 42 | code | Chapter 8 public API: layout | — | — | — | not_run_queue_lost | none |
| 43 | code | Chapter 8: extracted SPICE of your layout and its waveform | — | — | — | not_run_queue_lost | none |
| 44 | text | Expected diagnostic introduction | — | — | — | rendered | none |
| 45 | code | Chapter 8 expected caught HDL error | — | — | — | not_run_queue_lost | none |
| 46 | text | Next: compare the model with silicon | — | — | — | rendered | none |
| 47 | text | From your HDL to a shuttle-ready top | — | — | — | rendered | none |
| 48 | code | Chapter 9 recorded chip image and signoff table | — | — | — | not_run_queue_lost | none |
| 49 | code | Chapter 9 checks: recorded signoff snapshot and pad map | — | — | — | not_run_queue_lost | none |
| 50 | text | Chip results and remaining submission requirements | — | — | — | rendered | none |
| 51 | text | Appendix A. What the results establish | — | — | — | rendered | none |
| 52 | text | Appendix B. Verification evidence and how to rerun | — | — | — | rendered | none |
| 53 | code | Appendix B: cell characterization and fanout evidence | — | — | — | not_run_queue_lost | none |
| 54 | code | Appendix B: four-design physical and timing campaign | — | — | — | not_run_queue_lost | none |
| 55 | code | Appendix B: evidence tables, provenance and run time | — | — | — | not_run_queue_lost | none |
| 56 | text | Appendix C. Use and extend TritFlow | — | — | — | rendered | none |

First-attempt cells (`logs/colab/round17-first-cells.json`, kept outside git) · recovery cells (`logs/colab/round17-second-cells.json`, kept outside git) · standard round17-cells.json, recovery record (`logs/colab/round17-cells.json`, kept outside git) · final cleared-count notebook AX (`logs/colab/round17-final.ax.txt`, kept outside git).

## Screenshots and cleanup

Real browser captures, converted from the browser tool's image payload into actual PNG files without changing content. The **89 monitoring screenshots** are indexed in resource records. Event/feature-state captures:

- round17-00-sessions.png (`logs/colab/round17-00-sessions.png`, kept outside git)
- round17-01-first-screen.png (`logs/colab/round17-01-first-screen.png`, kept outside git)
- round17-02-disconnect.png (`logs/colab/round17-02-disconnect.png`, kept outside git)
- round17-03-reset-runtime-log.png (`logs/colab/round17-03-reset-runtime-log.png`, kept outside git)
- round17-04-recovery-disconnect.png (`logs/colab/round17-04-recovery-disconnect.png`, kept outside git)
- round17-05-second-reset-log.png (`logs/colab/round17-05-second-reset-log.png`, kept outside git)
- round17-06-sessions-after-resets.png (`logs/colab/round17-06-sessions-after-resets.png`, kept outside git)
- round17-07-setup-source-versions.png (`logs/colab/round17-07-setup-source-versions.png`, kept outside git)
- round17-08-opening-interrupted.png (`logs/colab/round17-08-opening-interrupted.png`, kept outside git)
- round17-09-ch1-unexecuted.png (`logs/colab/round17-09-ch1-unexecuted.png`, kept outside git)
- round17-10-ch6-unexecuted.png (`logs/colab/round17-10-ch6-unexecuted.png`, kept outside git)
- round17-11-ch8-unexecuted.png (`logs/colab/round17-11-ch8-unexecuted.png`, kept outside git)
- round17-12-ch9-unexecuted.png (`logs/colab/round17-12-ch9-unexecuted.png`, kept outside git)
- round17-13-final-unexecuted.png (`logs/colab/round17-13-final-unexecuted.png`, kept outside git)
- round17-14-runtime-deleted.png (`logs/colab/round17-14-runtime-deleted.png`, kept outside git)
- round17-15-sessions-final.png (`logs/colab/round17-15-sessions-final.png`, kept outside git)

Runtime → Disconnect and delete runtime confirmed. Reconnect verified at **19:32:35.147 JST** and final Manage sessions explicitly empty. Cleanup AX (`logs/colab/round17-cleanup.ax.txt`, kept outside git). No notebook save/share, authentication action, OAuth, implementation edit or git write command.

## Short history

- **Round 1 — FAIL**, `89b484b`: setup passed; SciPy/NumPy `_blas_supports_fpe` AttributeError. Manual diagnostics 8 pass / 4 fail; runtime deleted. Report (`logs/colab/round1-report.md`, kept outside git).
- **Round 2 — FIRST-RUN PASS**, `842afe2`: 17 code cells, **384.1 s** including setup; runtime deleted. [Report](round2-report.md).
- **Round 3 — FAIL**, `c84145b`: imports rejected `figures/out/fig_cell.svg`; remaining 16 code cells unexecuted; runtime deleted. [Report](round3-report.md).
- **Round 4 — PASS after retry**, `2c81d2c`: initial queue stopped after setup without traceback; second Run all passed 18 code cells in **405.0 s**, excluding initial attempt; runtime deleted. [Report](round4-report.md).
- **Round 5 — FIRST-RUN PASS**, `6d8df9e`: 18 code cells, **404.9 s** including setup. Sizing caption fixed; Appendix A truncated. Runtime deleted. [Report](round5-report.md).
- **Round 6 — FIRST-RUN PASS**, `91f642d`: 34 code/20 text cells, **332.5 s** including setup. Method/form split, STA, recorded chip and Appendix C rendered; Appendix A wrapping fixed. STA too tall, intro note stale. Runtime deleted. [Report](round6-report.md).
- **Round 7 — FIRST-RUN PASS**, `953cb0c`: 34 code/20 text cells, **472.9 s** including setup. Intro cites round 6; narrower STA plot fits viewport. Runtime deleted. [Report](round7-report.md).
- **Round 8 — FIRST-RUN PASS**, `cf010a0`: 35 code/22 text cells, **499.2 s** including setup. Chapters 0/1/4 Verilog highlighted and readable; chapter-8 formatted source separated from setup, outputs pass. Runtime deleted. [Report](round8-report.md).
- **Round 9 — FIRST-RUN PASS**, `7b62e63`: 35 code/22 text cells, **384.4 s** including setup. Recoloured Fig. 2 and cleaner schematic routes; flat half-adder oversized, compact legends small. Runtime deleted. [Report](round9-report.md).
- **Round 10 — FIRST-RUN PASS**, `0ffe7a1`: 35 code/22 text cells, **300.7 s** including setup. Two selector input pairs changed outputs and wire colours correctly; flat half-adder fit, side legends readable. fig_synth auxiliary pin/net annotations remained small. Runtime deleted. Report (`logs/colab/round10-report.md`, kept outside git).
- **Round 11 — FAIL/incomplete**, `134dfe7`: setup printed versions, execution state reset and new server/kernel started; no traceback or regenerated Fig. 2. One Run all, no retry; runtime deleted. Report (`logs/colab/round11-report.md`, kept outside git).
- **Round 12 — FAIL/incomplete**, `839adbf`: setup end followed by new server/kernel at 12:23:44/50 and loss of queue; no traceback. One Run all, no retry; runtime deleted. Report (`logs/colab/round12-report.md`, kept outside git).
- **Round 13 — FIRST-RUN EXECUTION PASS**, `839adbf`: other test sessions cleared; all 35 code cells completed in **299.3 s**. No post-setup kernel restart, sole current session before/after. Fig. 2 DC-family discrepancy reported. Runtime deleted. Report (`logs/colab/round13-report.md`, kept outside git).

- **Round 14 — a90844e:** first/only Run all failed in setup after approximately **8.0 s** (rounded gutter), because it cloned stale `839adbf` and could not import `setup_identity`. One code error, 34 not run; new features blocked. Test sessions cleared first; runtime deleted. Report (`logs/colab/round14-report.md`, kept outside git).

- **Round 15 — b49e5c1 / source 7d981896…:** correct pin and tool versions, then new server/kernel after setup; first/only Run all lost its queue, 34 later cells not run, no traceback. Completed time unavailable (251.7 s observed attempt only). Features blocked; runtime deleted. Report (`logs/colab/round15-report.md`, kept outside git).

- **Round 16 — b49e5c1 / source 7d981896…:** first Run all disconnected before setup output, same kernel ID; authorized recovery completed **35/35 cells, 474.4 s**. No server reset/OOM evidence that round. Feature checks passed except chapter-6 static GDS fallback; chip labels and enlarged schematic/header readability issues. 90 resource samples, runtime and test download deleted. Report (`logs/colab/round16-report.md`, kept outside git).

## Status and interface requests

The allowed two-attempt experiment and cleanup are complete. **Reset reproduced twice; recovery failed; release feature qualification blocked.** Use the changed server/kernel IDs, setup RAM peak and precise pre-reset cell-5 observations to investigate the runtime replacement. No cause is asserted beyond the recorded evidence. COLAB changed only status/evidence files. No further Run all or notebook fix was attempted.
