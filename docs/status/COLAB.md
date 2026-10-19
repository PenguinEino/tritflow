# COLAB — round 14

2026-10-19 · real Colab via cua_repl / extension-backed Chrome · pinned-dependencies release.

## Result

**FAIL on the first and only Run all.** Requested notebook release: **`a90844e91d1115edfd96bfb1d5b37f758135501d`** (`colab-v0`). The freshly loaded setup cell defaults to and actually clones **`839adbf19f7590221d18d171adaaddb95c8fd27a`**, then fails importing the newer `setup_identity` symbol from that older source.

**Total until failure: approximately 8.0 s** — only setup ran, and this is Colab's rounded `8 秒` setup gutter. **Completed Run-all total: unavailable**, because there is no final printed timer. It must not be treated as a successful `8.0 s` notebook run. Machine timing keeps `printedRunTimeSeconds` and `completionObserved` null. Setup execution count `[1]`; **1 code cell error, 34 not run**, 22 text cells rendered. No retry, second Run all, edited source pin, manual restart or individual-cell execution.

The safety-constrained verification attempt and cleanup are complete. **The requested feature checks remain blocked by setup**, not passed. Runtime → Disconnect and delete runtime was confirmed, and Reconnect was verified at the end. No sign-in, credentials, OAuth, notebook saving/sharing, paid runtime or implementation edits.

## Session inventory and cleanup before execution

Runtime → Manage sessions was the first Colab action. It listed exactly two test sessions and no unrelated notebooks:

| Notebook | Identity | Last execution | Start time | RAM shown | Action |
|---|---|---|---|---|---|
| `tritflow_tr1um.ipynb` | Current earlier TritFlow tab, GitHub colab-v0 | `0 分前` | Not exposed | **1.49 GB** | Terminated individually; accepted current-session termination confirmation |
| `scratchpad` | `colab.research.google.com/notebooks/empty.ipynb` | `0 分前` | Not exposed | **1.49 GB** | Terminated individually |

Inventory recorded **17:45:02.815 JST**. Scratch termination request recorded **17:45:11.910**. The remaining row temporarily became “unknown notebook”; it was left alone in that state. Reopening Manage sessions identified it as current `tritflow_tr1um.ipynb` again (**1.48 GB**), after which its individual termination was requested at **17:46:07.704** and the confirmation accepted. At **17:46:39.237** the dialog explicitly reported **no active sessions**. No unidentified or unrelated notebook was terminated. Browser tabs were left open.

The release notebook was reloaded fresh after clearing sessions. Latest Python 3 / CPU was verified without changing settings. New runtime connected at **17:47:31.865**, RAM **0.91/12.67 GB**, disk **20.50/107.72 GB**. Immediately before Run all, Manage sessions listed only the current TritFlow notebook, **0.95 GB RAM**, no other active sessions.

[Session JSON](../../logs/colab/round14-sessions.json) · [initial table](../../logs/colab/round14-sessions-before-ax.txt) · [refreshed identity](../../logs/colab/round14-sessions-refreshed-ax.txt) · [empty list](../../logs/colab/round14-sessions-cleared-ax.txt) · [sole current runtime](../../logs/colab/round14-sessions-prerun-ax.txt).

## Setup failure and complete traceback

Exactly one Runtime → Run all: **17:47:50.158 JST**. GitHub “Run anyway”: **17:47:59.462**. The setup printed:

```text
Source: https://github.com/PenguinEino/tritflow.git ref=839adbf19f7590221d18d171adaaddb95c8fd27a commit=839adbf19f7590221d18d171adaaddb95c8fd27a
```

The setup editor directly exposed this default:

```python
SOURCE_REF = os.environ.get("TRITFLOW_REF", "839adbf19f7590221d18d171adaaddb95c8fd27a")
```

It then executed line 37, `from runtime_support import SETUP_SCHEMA, setup_identity`. The old selected source does not supply `setup_identity`. This default-pin mismatch explains this observed ImportError; it is a different failure from the setup queue loss of rounds 11/12. No environment override was entered in this test.

The **entire traceback was visible**, with one displayed cell frame and no collapsed frames to expand. Below is its complete accessibility reading order; Colab folds the source-frame lines into one text node. The original AX text, paths and full traceback are also saved in [round14-traceback-ax.txt](../../logs/colab/round14-traceback-ax.txt) and [round14-traceback.txt](../../logs/colab/round14-traceback.txt).

```text
--------------------------------------------------------------------------- ImportError                                Traceback (most recent call last)
/tmp/ipykernel_672/1372262948.py
in  <cell line: 0> ()      35 raise RuntimeError ( "TRITFLOW_REF predates this notebook's setup. Select its matching immutable release with TRITFLOW_REF in a fresh runtime." )      36 sys . path . insert ( 0 , str ( ROOT / "notebook" ) ) ---> 37 from runtime_support import SETUP_SCHEMA , setup_identity      38 if SETUP_SCHEMA != "3" :      39 raise RuntimeError ( "The selected source commit predates the pinned runtime. Use the final submission commit with TRITFLOW_REF." ) ImportError : cannot import name 'setup_identity' from 'runtime_support' (/content/tritflow/notebook/runtime_support.py) --------------------------------------------------------------------------- 
NOTE: If your import is failing due to a missing package, you can
manually install dependencies using either !pip or !apt.

To view examples of installing some common dependencies, click the
"Open Examples" button below.
 ---------------------------------------------------------------------------

```

The same traceback evidence is recorded in `logs/COLAB.last.md`. [Full failed-cell AX output](../../logs/colab/round14-setup-expanded-ax.txt) and [observed pin](../../logs/colab/round14-setup-pin-ax.txt) are preserved. [Complete setup source at local release commit a90844e](../../logs/colab/round14-setup-release-source.py) was extracted read-only with `git show`; its default pin/import match the observed Colab editor and traceback. It is labelled as a local release source copy, not a complete clipboard export from the browser.

**Tool/dependency versions for this run: unavailable.** Setup stopped before dependency installation/version printout. Neither the new pinned dependency installation nor KLayout/ngspice versions were qualified. Historical version text from earlier runs is not substituted.

## Runtime log and cleanup

All **72 runtime-log entries** were captured from Runtime → View runtime logs, with the page set to 100 rows. Relevant entries show cloning at **17:48:00**, fetching old immutable commit at **17:48:01**, and `HEAD is now at 839adbf Rename figures/style.py to paperstyle.py` at **17:48:08**. Initial kernel start predates execution; there is no captured post-setup restart. The notebook displayed an ImportError rather than losing/resetting the queue. No explicit session-crashed/restarted toast was observed.

[Raw runtime log](../../logs/colab/round14-runtime-log-ax.txt) · [72 parsed entries](../../logs/colab/round14-runtime-log-entries.json) · [timing JSON](../../logs/colab/round14-timing.json).

Runtime deletion verified **17:50:03.362 JST**, Reconnect displayed. [Cleanup AX](../../logs/colab/round14-cleanup-ax.txt).

## Requested features and readability

| Requested check | Round-14 result |
|---|---|
| Chapter-1 truth-table/schematic cards; click schematic to enlarge | **Blocked**: method output absent; no schematic to click. |
| Live Fig. 2 with three distinct B curves for NAND/NOR/NANY | **Blocked**: no DC sweeps/figure output; round-13 issue not reverified. |
| Prominent chapter-2 slider; drag once | **Blocked**: new “Try it” prose loaded, but no slider output. No drag performed. |
| Chapter-6/8/9 GDS viewer: wheel to devices, sharp rerender, pan, Fit | **Blocked for all three**: viewer outputs were never created. |
| GDS download buttons, download start, delete downloaded file | **Blocked**: no generated download buttons. No download initiated or file created in `~/Downloads`; no unrelated Downloads files touched. |
| Chapter-5 trit selector | **Blocked**: no selector output/buttons to test. |
| Chapter-8 scope: dark lanes v(a), v(b), v(lo), v(hi), \|i(vdd)\|, ngspice 42 header | **Blocked**: no waveform/header output. |

[Feature-check JSON](../../logs/colab/round14-feature-checks.json). The setup traceback and source pin were readable in the captured light theme. The first-screen static overview rendered, with its historical `839adbf` / `299.3 s` verification note. That note is not a round-14 completion result. No new-feature readability, zoom sharpness, transistor visibility, pan/Fit behavior, curve distinction or waveform-lane assessment can be claimed from absent outputs.

## Every cell

Zero-based indices, same JSON record keys as prior rounds. **35 code / 22 text**. Setup has execution 1 and `8 秒`; remaining code has blank counts and displayed `0 秒` queue-cancellation gutters. Those zero readings are not completed execution times; statuses explicitly say not run. Only setup contains a traceback.

| Cell | Type | Purpose | Execution | Displayed time | Status | Traceback |
|---:|---|---|---:|---|---|---|
| 0 | text | TritFlow: balanced-ternary HDL to GDS on OpenSUSI TR-1um | — | — | rendered | none |
| 1 | code | Setup (collapsed form) | 1 | 8 秒 | error | ImportError (complete above) |
| 2 | code | Imports and run bookkeeping | — | 0 秒 | not_run_setup_failed | none |
| 3 | text | From HDL to a checked adder layout; highlighted adder.tv definition | — | — | rendered | none |
| 4 | code | Chapter 0 inputs: test conditions and an independent integer oracle | — | 0 秒 | not_run_setup_failed | none |
| 5 | code | Chapter 0 public API: HDL → GDS → extracted SPICE | — | 0 秒 | not_run_setup_failed | none |
| 6 | code | Chapter 0 checks | — | 0 秒 | not_run_setup_failed | none |
| 7 | text | Three levels from ordinary CMOS | — | — | rendered | none |
| 8 | code | Chapter 1 public API: gates and DC | — | 0 秒 | not_run_setup_failed | none |
| 9 | text |  | — | — | rendered | none |
| 10 | code | Chapter 1 checks and the taped-out INV schematic | — | 0 秒 | not_run_setup_failed | none |
| 11 | text | Sizing sets the middle level | — | — | rendered | none |
| 12 | code | Chapter 2 public API: sizing slider | — | 0 秒 | not_run_setup_failed | none |
| 13 | code | Chapter 2 details: resistor-length candidates at the taped-out MOS sizes | — | 0 秒 | not_run_setup_failed | none |
| 14 | text | Taped-out circuits become placeable cells | — | — | rendered | none |
| 15 | code | Chapter 3 public API: cell view | — | 0 秒 | not_run_setup_failed | none |
| 16 | code | Chapter 3 checks: template, clamp devices and cell qualification | — | 8 秒 | not_run_setup_failed | none |
| 17 | text | Describe signed arithmetic in TritVerilog | — | — | rendered | none |
| 18 | text | Chapter 4 highlighted half_add.tv and full_add.tv definitions | — | — | rendered | none |
| 19 | code | Chapter 4 public API: arithmetic | — | 8 秒 | not_run_setup_failed | none |
| 20 | code | Chapter 4 checks: cell counts against the taped-out schematics | — | 8 秒 | not_run_setup_failed | none |
| 21 | text | Follow an expression into cells | — | — | rendered | none |
| 22 | code | Chapter 5 public API: synthesis and interactive half-adder schematic | — | 8 秒 | not_run_setup_failed | none |
| 23 | code | Chapter 5 checks: mapping rules and gate-level TritVerilog | — | 8 秒 | not_run_setup_failed | none |
| 24 | code | Chapter 5 public API: two-trit adder hierarchy schematic | — | 8 秒 | not_run_setup_failed | none |
| 25 | text | Route signals and feed the standing current | — | — | rendered | none |
| 26 | code | Chapter 6 public API: P&R view | — | 8 秒 | not_run_setup_failed | none |
| 27 | code | Chapter 6 details and an optional floorplan experiment | — | 8 秒 | not_run_setup_failed | none |
| 28 | text | Does the layout still work? | — | — | rendered | none |
| 29 | code | Chapter 7 public API: device-only SPICE and wire overlay | — | 8 秒 | not_run_setup_failed | none |
| 30 | code | Chapter 7 checks: identical devices with and without wire C | — | 8 秒 | not_run_setup_failed | none |
| 31 | text | Chapter 7 scaling and power evidence | — | — | rendered | none |
| 32 | code | Chapter 7 recorded width and load campaigns | — | 8 秒 | not_run_setup_failed | none |
| 33 | text | Predict with static timing, confirm with SPICE | — | — | rendered | none |
| 34 | code | Chapter 7 public API: STA vs SPICE | — | 8 秒 | not_run_setup_failed | none |
| 35 | code | Chapter 7 STA comparison table and critical path | — | 8 秒 | not_run_setup_failed | none |
| 36 | text | STA validation figure and scope | — | — | rendered | none |
| 37 | text | Change the circuit and close the loop | — | — | rendered | none |
| 38 | code | Chapter 8 editable formatted TritVerilog source definition | — | 8 秒 | not_run_setup_failed | none |
| 39 | code | Chapter 8 circuit selection and independent reference setup | — | 8 秒 | not_run_setup_failed | none |
| 40 | code | Chapter 8 synthesis / truth table | — | 8 秒 | not_run_setup_failed | none |
| 41 | code | Chapter 8 check: every input state against the independent arithmetic reference | — | 8 秒 | not_run_setup_failed | none |
| 42 | code | Chapter 8 public API: layout | — | 8 秒 | not_run_setup_failed | none |
| 43 | code | Chapter 8: extracted SPICE of your layout and its waveform | — | 8 秒 | not_run_setup_failed | none |
| 44 | text | Expected diagnostic introduction | — | — | rendered | none |
| 45 | code | Chapter 8 expected caught HDL error | — | 8 秒 | not_run_setup_failed | none |
| 46 | text | Next: compare the model with silicon | — | — | rendered | none |
| 47 | text | From your HDL to a shuttle-ready top | — | — | rendered | none |
| 48 | code | Chapter 9 recorded chip image and signoff table | — | 8 秒 | not_run_setup_failed | none |
| 49 | code | Chapter 9 checks: recorded signoff snapshot and pad map | — | 8 秒 | not_run_setup_failed | none |
| 50 | text | Chip results and remaining submission requirements | — | — | rendered | none |
| 51 | text | Appendix A. What the results establish | — | — | rendered | none |
| 52 | text | Appendix B. Verification evidence and how to rerun | — | — | rendered | none |
| 53 | code | Appendix B: cell characterization and fanout evidence | — | 8 秒 | not_run_setup_failed | none |
| 54 | code | Appendix B: four-design physical and timing campaign | — | 8 秒 | not_run_setup_failed | none |
| 55 | code | Appendix B: evidence tables, provenance and run time | — | 8 秒 | not_run_setup_failed | none |
| 56 | text | Appendix C. Use and extend TritFlow | — | — | rendered | none |

[Complete cell records](../../logs/colab/round14-cells.json) · [full notebook AX](../../logs/colab/round14-results-ax.txt).

## Screenshots

- [round14-00-sessions-before.png](../../logs/colab/round14-00-sessions-before.png) — actual PNG, 3083 × 1637.
- [round14-01-sessions-cleared.png](../../logs/colab/round14-01-sessions-cleared.png) — actual PNG, 3083 × 1637.
- [round14-02-first-screen.png](../../logs/colab/round14-02-first-screen.png) — actual PNG, 3083 × 1637.
- [round14-03-setup-running.png](../../logs/colab/round14-03-setup-running.png) — actual PNG, 3083 × 1637.
- [round14-04-setup-error.png](../../logs/colab/round14-04-setup-error.png) — actual PNG, 3083 × 1637.
- [round14-05-setup-source.png](../../logs/colab/round14-05-setup-source.png) — actual PNG, 3083 × 1637.
- [round14-06-setup-source-pin.png](../../logs/colab/round14-06-setup-source-pin.png) — actual PNG, 3083 × 1637.
- [round14-07-runtime-log.png](../../logs/colab/round14-07-runtime-log.png) — actual PNG, 3083 × 1637.
- [round14-08-runtime-deleted.png](../../logs/colab/round14-08-runtime-deleted.png) — actual PNG, 3083 × 1637.

Full AX captures redact the Google account identifier. Browser dimensions changed during the session; no viewport/zoom override was set. Initial browser-client tab discovery failed twice with a request-header policy error; cua_repl successfully accessed the same extension-backed Chrome. No alternate runtime execution method was used.

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

## Status and interface requests

Round-14 attempt, failure evidence, session inventory, cell/timing/feature records and runtime deletion complete. **Release verification blocked**: correct the setup's default immutable source pin so it selects a commit compatible with `setup_identity` and schema 3, then request a new fresh-runtime run. All requested interactive/new-feature checks still require real-Colab verification. No code fix or retry was attempted.

Validation: cleared test sessions, new CPU runtime, exactly one Run all, full ImportError/source-pin evidence, 57 cell records, all 72 log entries, JSON/PNG/report-link checks and runtime deletion. No local tests were run because this stream changed only reports/evidence.
