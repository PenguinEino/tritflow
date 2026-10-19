# COLAB — round 13

2026-10-19 · real Google Colab · extension-backed Chrome · `colab-v0 = 839adbf`.

## Outcome

**FIRST-RUN EXECUTION PASS, with a Fig. 2 discrepancy.** After terminating the two identified preexisting test sessions, exactly one Runtime → Run all completed all **35 code cells** (execution counts 1–35). The notebook printed **299.3 s including setup**, source `839adbf19f7590221d18d171adaaddb95c8fd27a`. No unexpected Python exception or traceback. No retry, second Run all, manual restart or individual-cell execution.

Manage sessions showed no active sessions after the two terminations, only the new current TritFlow session immediately before Run all, and only that current session again after completion. No unrelated user notebook was listed or terminated. This successful isolation experiment **supports the competing-session hypothesis**, but one run does not establish that concurrent sessions caused rounds 11/12 to fail.

The browser briefly showed Connecting / resuming execution, then recovered outputs and final completion automatically. Unlike rounds 11/12, the captured runtime log contains **no new kernel/server startup after setup**. Reconnection messages target the same kernel ID throughout. No explicit session-crashed/restarted toast was observed.

Runtime → Disconnect and delete runtime was confirmed at the end; **Reconnect** was verified. No credentials, sign-in, OAuth, saving/sharing or paid tier was used. Only reports/evidence were changed.

## Session inventory and terminations

Before starting, Runtime → Manage sessions listed exactly these two active sessions. The dialog exposed **last execution**, not session start time; start times are recorded as unavailable instead of treating last execution as start. RAM was not shown for these other sessions. The already-open scratchpad tab supplied its RAM/disk reading; the earlier Japanese notebook was disconnected, and was not reconnected just to obtain RAM.

| Notebook | Identifying URL | Start time | Last execution shown | RAM | Action |
|---|---|---|---|---|---|
| `tritflow_tr1um.ipynb` | GitHub `review-ja/notebook/tritflow_tr1um_ja.ipynb` | Not provided by UI | `21 分前` (later 22 min) | Unavailable; disconnected tab | Terminated individually as an earlier TritFlow test session |
| `scratchpad` | `colab.research.google.com/notebooks/empty.ipynb` | Not provided by UI | `0 分前` | **1.75/12.67 GB**; disk **21.47/107.72 GB** in existing tab | Terminated individually as the empty.ipynb test session |

Session inventory timestamp: **12:50:23.757 JST**. Scratch termination request recorded at **12:50:51.695**; both entries were verified gone at **12:51:01.220**, with `アクティブなセッションがありません` (“No active sessions”). The broad “terminate other sessions” control was not used.

The new runtime connected at **12:51:50.707**; initial RAM **0.89/12.67 GB**, disk **20.50/107.72 GB**. At **12:52:17.722**, Manage sessions listed only the current notebook, **0.94 GB RAM**, last execution `0 分前`. Post-run Manage sessions again listed only the current notebook, **1.41 GB RAM**, last execution `0 分前`. No other sessions were observed returning.

Evidence: [session JSON](round13-sessions.json), [before](round13-sessions-before-ax.txt), [cleared](round13-sessions-cleared-ax.txt), [only-current pre-run](round13-sessions-prerun-ax.txt), [post-run](round13-sessions-postrun-ax.txt). Browser tabs themselves were left open; session deletion was performed through Manage sessions.

## Execution, timing and runtime logs

- Fresh latest Python 3 / CPU settings verified; runtime type dialog cancelled without changes. Initially Connect was shown and delete-runtime was disabled.
- Exactly one Runtime → Run all: **12:52:21.027 JST**. GitHub “Run anyway”: **12:52:31.965**.
- Final printed total: **299.3 s including setup**. Completion observation timestamp and cleanup timestamp are in [round13-timing.json](round13-timing.json); observation time is not the exact internal finishing time.
- **Per-cell timing limitation:** after automatic reconnection Colab displayed `0 秒` for 34 code cells, including setup, and `2 秒` for cell 43. Those displayed values are preserved in JSON/table. They are inconsistent with the 299.3 s total and must not be summed or represented as accurate full cell durations. Setup's accurate completed wall time is unavailable.
- Setup versions were logged at **12:53:34**. This was about 62 seconds after warning acceptance, but that interval is not an exact setup duration.
- All **615 runtime-log entries** visible through seven paginated UI views were saved and parsed. Kernel startup was **12:51:43**, before this run; Jupyter server startup was **12:27:39**, also before this run. A fresh kernel does not require a newly booted server process. There is no captured startup after setup.
- Connections at **12:51:44, 12:55:40 and 12:57:30** all reference kernel `3cf39d7b-8b69-40e1-b9a2-af097995b6f4`. Closed-stream warnings appear at 12:57:03. They did not prevent final completion. The browser's resuming/reconnection display is not evidence of a kernel restart.
- Post-completion resource panel: **1.4/12.7 GB RAM**, **21.5/107.7 GB disk** (rounded), chart range 12:57–12:58; this is not an instantaneous setup-end measurement.

Selected messages copied verbatim from the log UI, newest first:

```text
Oct 19, 2026, 12:57:30 PM [INFO]
Connecting to kernel 3cf39d7b-8b69-40e1-b9a2-af097995b6f4.

Oct 19, 2026, 12:55:40 PM [INFO]
Connecting to kernel 3cf39d7b-8b69-40e1-b9a2-af097995b6f4.

Oct 19, 2026, 12:53:34 PM [WARNING]
KLayout 0.30.6

Oct 19, 2026, 12:51:44 PM [INFO]
Connecting to kernel 3cf39d7b-8b69-40e1-b9a2-af097995b6f4.

Oct 19, 2026, 12:51:43 PM [INFO]
Kernel started: 3cf39d7b-8b69-40e1-b9a2-af097995b6f4

Oct 19, 2026, 12:27:39 PM [INFO]
Jupyter Server 2.20.0 is running at:
```

[Full parsed runtime log](round13-runtime-log-entries.json) · [completed output](round13-results-ax.txt) · [expanded inspection](round13-results-expanded-ax.txt).

## Printed tools and checks

```text
Source: https://github.com/PenguinEino/tritflow.git ref=colab-v0 commit=839adbf19f7590221d18d171adaaddb95c8fd27a
Scientific Python (host versions preserved): numpy=2.1.3, scipy=1.16.3, matplotlib=3.10.0, plotly=5.24.1
KLayout executable: /usr/bin/klayout
KLayout 0.30.6
ngspice executable: /usr/bin/ngspice
** ngspice-42 : Circuit level simulation program
** Compiled with KLU Direct Linear Solver
```

Opening live adder: `DRC clean: True · LVS match: True · analog PASS: True`, 243 exhaustive integer-reference states and 9 selected extracted sequence states. Chapter 1 live method imported `fig_gates` and `paperstyle`, returned a figure, and printed:

```text
A = 0 V:  Y = -39.5 mV,  supply current = 0.407 mA
```

Edited minmax circuit: 4 cells, 384 × 366 µm; drawing DRC 0 markers, strict LVS match, 9 reference/input states and output checks PASS. Final stage table labels `your-minmax: run` (**19.67 s**) and four larger example campaigns `recorded`; those recorded campaigns were not rerun in this notebook. Chapter-9 full-chip signoff is explicitly recorded evidence, with `submission_ready=False` and outstanding pad/bond/ESD/power/package approval, not a notebook execution error.

No unexpected traceback was displayed. Cell 45 deliberately catches and prints the unsupported-HDL diagnostic below; execution continued through count 35:

```text
your_circuit.tv:3:14: arithmetic/comparison on trits is unsupported; use ~, &, |, nany and sized trit literals
Repair: use gates for signal arithmetic; e.g. nany(a, b) gives the negative saturated sum.
```

## Figure/readability findings

**Fig. 2 requires investigation despite execution success.** The regenerated chapter-1 figure fits the displayed notebook width. Serif headings, italic voltage/current axes, grey acceptance bands and coloured B legend are readable and broadly match the paper styling. However, NAND/NOR/NANY panels show essentially a single red transfer/current trace rather than the distinct blue/grey/red families in the repository paper asset. For example, the live NAND red transfer settles near 0 V at high A while the reference has a blue +5 V line, grey near-0 branch and red −5 V branch; live NANY lacks the visibly separated shifted blue/grey/red transitions. This is a content/curve discrepancy, not clipping or a font-only difference. No numerical DC-family validation was performed beyond the notebook's own checks; the root cause was not diagnosed or fixed in this stream.

Comparison reference: the read-only workspace `figures/out/fig_gates.png` at inspection, copied to [round13-reference-fig-gates.png](round13-reference-fig-gates.png), SHA-256 `a708a63d5734df46116473079b6075de676ceee9ec7b024b0a810a1d21624ca7`. This identifies the inspected reference; it is not a claim of a byte-for-byte comparison against an externally published PDF.

Other inspected chapter heroes rendered. Chapter-4 pin/net annotations and chapter-9 chip layer legend remain small at displayed size. Chapter-5 half-adder/two-trit schematics and chapter-8 edited schematic have readable ports and no obvious label overlaps. Chapter-7 STA plot fits in the captured viewport. Chapter-8 GDS/waveform display and final summary are present. No other blank main figure or horizontal clipping was observed in the captured views. Light-theme contrast is adequate; no zoom/viewport override was applied.

## Every cell

Zero-based indices, same record keys as earlier rounds. **35 code / 22 text**. Code status below means execution completed without an unexpected exception; it does not validate every plotted curve. Wall times are the **displayed, unreliable post-reconnection gutter values** described above.

| Cell | Type | Purpose | Execution | Displayed time | Status | Traceback |
|---:|---|---|---:|---|---|---|
| 0 | text | TritFlow: balanced-ternary HDL to GDS on OpenSUSI TR-1um | — | — | rendered | none |
| 1 | code | Setup (collapsed form) | 1 | 0 秒 | pass | none |
| 2 | code | Imports and run bookkeeping | 2 | 0 秒 | pass | none |
| 3 | text | From HDL to a checked adder layout; highlighted adder.tv definition | — | — | rendered | none |
| 4 | code | Chapter 0 inputs: test conditions and an independent integer oracle | 3 | 0 秒 | pass | none |
| 5 | code | Chapter 0 public API: HDL → GDS → extracted SPICE | 4 | 0 秒 | pass | none |
| 6 | code | Chapter 0 checks | 5 | 0 秒 | pass | none |
| 7 | text | Three levels from ordinary CMOS | — | — | rendered | none |
| 8 | code | Chapter 1 public API: gates and DC | 6 | 0 秒 | pass | none |
| 9 | text |  | — | — | rendered | none |
| 10 | code | Chapter 1 checks and the taped-out INV schematic | 7 | 0 秒 | pass | none |
| 11 | text | Sizing sets the middle level | — | — | rendered | none |
| 12 | code | Chapter 2 public API: sizing slider | 8 | 0 秒 | pass | none |
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
| 29 | code | Chapter 7 public API: device-only SPICE and wire overlay | 19 | 0 秒 | pass | none |
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
| 42 | code | Chapter 8 public API: layout | 28 | 0 秒 | pass | none |
| 43 | code | Chapter 8: extracted SPICE of your layout and its waveform | 29 | 2 秒 | pass | none |
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

[Full 57-cell JSON](round13-cells.json).

## Screenshots

- [round13-00-sessions-before.png](round13-00-sessions-before.png) — actual PNG, 2396 × 1623.
- [round13-01-sessions-cleared.png](round13-01-sessions-cleared.png) — actual PNG, 2396 × 1623.
- [round13-02-first-screen.png](round13-02-first-screen.png) — actual PNG, 2396 × 1623.
- [round13-03-only-current-session.png](round13-03-only-current-session.png) — actual PNG, 2396 × 1623.
- [round13-04-setup-transition.png](round13-04-setup-transition.png) — actual PNG, 2396 × 1623.
- [round13-05-setup-resources.png](round13-05-setup-resources.png) — actual PNG, 2396 × 1623.
- [round13-06-runtime-log.png](round13-06-runtime-log.png) — actual PNG, 2396 × 1623.
- [round13-07-sessions-postrun.png](round13-07-sessions-postrun.png) — actual PNG, 2396 × 1623.
- [round13-08-ch0.png](round13-08-ch0.png) — actual PNG, 2396 × 1623.
- [round13-09-ch1-fig2.png](round13-09-ch1-fig2.png) — actual PNG, 2396 × 1623.
- [round13-10-ch2.png](round13-10-ch2.png) — actual PNG, 2396 × 1623.
- [round13-11-ch3.png](round13-11-ch3.png) — actual PNG, 2396 × 1623.
- [round13-12-ch4.png](round13-12-ch4.png) — actual PNG, 2396 × 1623.
- [round13-13-ch5-half-adder.png](round13-13-ch5-half-adder.png) — actual PNG, 2396 × 1623.
- [round13-14-ch5-two-trit-adder.png](round13-14-ch5-two-trit-adder.png) — actual PNG, 2396 × 1623.
- [round13-15-ch6.png](round13-15-ch6.png) — actual PNG, 2396 × 1623.
- [round13-16-ch7-wire-c.png](round13-16-ch7-wire-c.png) — actual PNG, 2396 × 1623.
- [round13-17-ch7-sta.png](round13-17-ch7-sta.png) — actual PNG, 2396 × 1623.
- [round13-18-ch8-schematic.png](round13-18-ch8-schematic.png) — actual PNG, 2396 × 1623.
- [round13-19-ch8-gds.png](round13-19-ch8-gds.png) — actual PNG, 2396 × 1623.
- [round13-20-ch8-waveform.png](round13-20-ch8-waveform.png) — actual PNG, 2396 × 1623.
- [round13-21-ch9.png](round13-21-ch9.png) — actual PNG, 2396 × 1623.
- [round13-22-final-summary.png](round13-22-final-summary.png) — actual PNG, 2396 × 1623.
- [round13-23-runtime-deleted.png](round13-23-runtime-deleted.png) — actual PNG, 2396 × 1623.

All UI captures and JSON are under `logs/colab/round13-*`. Full notebook AX captures redact the account identifier; scratch URLs redact the MCP token. The reference image above is a local comparison asset, not a browser screenshot.

## Short history

- **Round 1 — FAIL**, `89b484b`: setup passed; SciPy/NumPy `_blas_supports_fpe` AttributeError. Manual diagnostics 8 pass / 4 fail; runtime deleted. [Report](round1-report.md).
- **Round 2 — FIRST-RUN PASS**, `842afe2`: 17 code cells, **384.1 s** including setup; runtime deleted. [Report](round2-report.md).
- **Round 3 — FAIL**, `c84145b`: imports rejected `figures/out/fig_cell.svg`; remaining 16 code cells unexecuted; runtime deleted. [Report](round3-report.md).
- **Round 4 — PASS after retry**, `2c81d2c`: initial queue stopped after setup without traceback; second Run all passed 18 code cells in **405.0 s**, excluding initial attempt; runtime deleted. [Report](round4-report.md).
- **Round 5 — FIRST-RUN PASS**, `6d8df9e`: 18 code cells, **404.9 s** including setup. Sizing caption fixed; Appendix A truncated. Runtime deleted. [Report](round5-report.md).
- **Round 6 — FIRST-RUN PASS**, `91f642d`: 34 code/20 text cells, **332.5 s** including setup. Method/form split, STA, recorded chip and Appendix C rendered; Appendix A wrapping fixed. STA too tall, intro note stale. Runtime deleted. [Report](round6-report.md).
- **Round 7 — FIRST-RUN PASS**, `953cb0c`: 34 code/20 text cells, **472.9 s** including setup. Intro cites round 6; narrower STA plot fits viewport. Runtime deleted. [Report](round7-report.md).
- **Round 8 — FIRST-RUN PASS**, `cf010a0`: 35 code/22 text cells, **499.2 s** including setup. Chapters 0/1/4 Verilog highlighted and readable; chapter-8 formatted source separated from setup, outputs pass. Runtime deleted. [Report](round8-report.md).
- **Round 9 — FIRST-RUN PASS**, `7b62e63`: 35 code/22 text cells, **384.4 s** including setup. Recoloured Fig. 2 and cleaner schematic routes; flat half-adder oversized, compact legends small. Runtime deleted. [Report](round9-report.md).
- **Round 10 — FIRST-RUN PASS**, `0ffe7a1`: 35 code/22 text cells, **300.7 s** including setup. Two selector input pairs changed outputs and wire colours correctly; flat half-adder fit, side legends readable. fig_synth auxiliary pin/net annotations remained small. Runtime deleted. [Report](round10-report.md).
- **Round 11 — FAIL/incomplete**, `134dfe7`: setup printed versions, execution state reset and new server/kernel started; no traceback or regenerated Fig. 2. One Run all, no retry; runtime deleted. [Report](round11-report.md).
- **Round 12 — FAIL/incomplete**, `839adbf`: setup end followed by new server/kernel at 12:23:44/50 and loss of queue; no traceback. One Run all, no retry; runtime deleted. [Report](round12-report.md).

## Status and interface requests

Round-13 session isolation, exactly-one-Run-all execution, records, figures/logs and runtime deletion complete. **Queue-loss failure did not reproduce after clearing other sessions.** Keep session isolation as a verification precondition and repeat if stronger causal evidence is needed. Separately investigate the regenerated Fig. 2 DC-family discrepancy before treating the figure as paper-equivalent. No implementation changes made.

Validation: Manage sessions before/after, individual test-session terminations, empty list, sole current runtime before/after Run all, source/tools, counts 1–35, final timer, live checks, inspected figures, all 615 log entries, JSON consistency, PNG decoding, report links and runtime deletion. No local tests were run because only reports/evidence changed.
