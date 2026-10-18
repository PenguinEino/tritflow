# COLAB — round 5, 2026-10-19 JST

**PASS on the FIRST Run all: all 18 code cells completed in 404.9 s including setup (6 min 44.9 s). No retry was needed or performed.** No restart, individual-cell rerun, interruption, notebook edit or uncaught traceback occurred. The round-4 initial queue-loss symptom did not recur in this run.

Printed source: **`6d8df9ef98135824198d1913fbfeada5a3f1c3a7`**, ref `colab-v0`.

## Procedure and environment

- Reloaded https://colab.research.google.com/github/PenguinEino/tritflow/blob/colab-v0/notebook/tritflow_tr1um.ipynb through the Chrome extension surface via `cua_repl`.
- No old runtime existed: Connect was offered, and Runtime → Disconnect/delete was disabled. Inspected Python 3 / **CPU selected** / latest recommended runtime; connected a new standard free Google Compute Engine backend (12.67 GB RAM).
- Issued **Runtime → Run all exactly once at 00:08:58 JST**, accepted the authorized GitHub warning at **00:09:04**. Setup and imports completed, then execution proceeded through every chapter and the closing prerequisite/source checks without further execution actions.
- Setup gutter time: **1 min** (Colab rounded). Imports: **4 s**. Final printed installation-inclusive runtime: **404.9 s**. Completion was observed by **00:16:06 JST**; observation includes polling delay and is not the execution timer.
- Printed tools: **KLayout 0.30.6** at `/usr/bin/klayout`; **ngspice-42** at `/usr/bin/ngspice`, compiled with KLU Direct Linear Solver.
- Host stack preserved: **NumPy 2.1.3, SciPy 1.16.3, Matplotlib 3.10.0, Plotly 5.24.1**.
- **Runtime deleted at 00:16:57 JST**, using Runtime → Disconnect and delete runtime → Yes. Confirmed toolbar **Reconnect** afterward.
- No credentials, sign-in, OAuth, notebook saving/sharing, paid tier or account-setting changes. No local package installation or code changes; only COLAB-owned report/log paths written, with no git write commands.

## Every cell

Colab's zero-based indices: **33 cells = 18 code + 15 text**. Code execution counts are uninterrupted **1–18** from the single Run all. Times are the displayed rounded gutter values; `0 s` means rounded, not zero work. Text cells have no execution time.

| Cell | Execution | Purpose | Result | Colab wall time |
|---|---|---|---|---|
| 0 | — | Opening narrative / overview hero | Rendered | — |
| 1 | 1 | Setup | PASS | 1 min |
| 2 | 2 | Imports / paper evidence | PASS | 4 s |
| 3 | — | Chapter 0 narrative | Rendered | — |
| 4 | 3 | Live two-trit adder | PASS | 2 min |
| 5 | — | Chapter 1 narrative / DC hero / math | Rendered | — |
| 6 | 4 | Gate checks / inverter DC | PASS | 0 s |
| 7 | — | Chapter 2 narrative / sizing hero / math | Rendered | — |
| 8 | 5 | Sizing tables and interactive slider | PASS | 4 s |
| 9 | — | Chapter 3 narrative / cell-layout hero | Rendered | — |
| 10 | 6 | Cell dimensions / mapping / qualification | PASS | 0 s |
| 11 | — | Chapter 4 narrative / arithmetic hero | Rendered | — |
| 12 | 7 | Half/full-adder arithmetic checks | PASS | 0 s |
| 13 | — | Chapter 5 synthesis narrative | Rendered | — |
| 14 | 8 | Mapped half-adder graph / reports | PASS | 0 s |
| 15 | 9 | Mapped adder and half-adder schematics | PASS | 0 s |
| 16 | — | Chapter 6 narrative / P&R hero | Rendered | — |
| 17 | 10 | P&R measurements | PASS | 0 s |
| 18 | — | Chapter 7 narrative / post-layout hero / math | Rendered | — |
| 19 | 11 | Identical extracted devices, without wire C | PASS | 2 min |
| 20 | — | Chapter 7 scaling/power hero and estimates | Rendered | — |
| 21 | 12 | Published width/load evidence | PASS | 0 s |
| 22 | — | Chapter 8 narrative | Rendered | — |
| 23 | 13 | Edited minmax HDL | PASS | 0 s |
| 24 | 14 | Custom flow / schematic / GDS / waveform | PASS | 28 s |
| 25 | — | Expected diagnostic introduction | Rendered | — |
| 26 | 15 | Caught unsupported-HDL diagnostic | PASS; expected diagnostic caught | 0 s |
| 27 | — | Chapter 9 outlook / measurement table | Rendered | — |
| 28 | — | Appendix A scope | Rendered | — |
| 29 | — | Appendix B evidence introduction | Rendered | — |
| 30 | 16 | Characterization evidence | PASS | 0 s |
| 31 | 17 | Four-design recorded campaign | PASS | 1 s |
| 32 | 18 | Final assertions / summary / timings | PASS | 1 s |

Fresh stages and recorded lookups from the final table:

| Stage | State | Seconds |
|---|---|---:|
| adder2-complete | run | 151.3 |
| adder2-pre | run | 134.8 |
| your-minmax | run | 27.49 |
| your-minmax-raster | run | 0.461 |
| inv-dc | run | 0.252 |
| four-mac1 | recorded lookup | 0.342 |
| four-adder4 | recorded lookup | 0.282 |
| four-full_add | recorded lookup | 0.075 |
| four-mul1 | recorded lookup | 0.026 |

The 404.9 s includes setup and the notebook's default mix of fresh calculations and labeled recorded evidence. It is not fresh recomputation of every sizing, width/load sweep, cell qualification or four-design campaign. The final prerequisite guard and artifact/source checks completed successfully.

## Results and tracebacks

- Live two-trit adder: **32 cells, 1284 × 1038 µm, DRC 0, strict LVS True, analog True**. Independent integer reference: **243 exhaustive states**; extracted sequence: **9 selected unique states**.
- Chapter 8 minmax: **4 cells, 384 × 366 µm, DRC 0, LVS Match, analog PASS for 9 input states**. The generated outputs and final takeaway were emitted by the first run.
- Four-design table explicitly identifies the retained routing realizations and reports DRC/LVS True for adder4, full_add, mac1 and mul1. These are recorded results, not new physical runs.
- **No uncaught Python traceback or failing cell.** No retry required. This is one successful first-run trial; it does not establish the cause of the prior round's transient interruption.

Cell 26 intentionally catches and prints the following teaching diagnostic; the cell passes:

```text
your_circuit.tv:2:17: arithmetic/comparison on trits is unsupported; use ~, &, |, nany and sized trit literals
Repair: use gates for signal arithmetic; e.g. nany(a,b) gives the negative saturated sum.
```

Published load-failure boundaries and unavailable sizing points remain recorded experimental evidence, not newly failing cells.

## Visual findings

- **First screen:** clear title, visible bold Run all instruction and complete overview. It accurately labels the older round-4 verification as a successful second run rather than claiming a first-run pass. Miniature HDL/GDS detail and overview footnotes remain small at normal zoom, but the body text is readable.
- **Sizing figure right edge fixed:** both scatter-plot x-axis labels now read **“Max static current (mA)”** in full, with no cut-off right caption. The pale 20 µm series label remains low contrast. Screenshot 02 captures the full figure width.
- **Appendix A table fits the page**, removing the previous horizontal overflow, but its long Scope entries are now displayed on single lines with **ellipsis truncation**. The complete statements cannot be read in the captured rendered table; wrapping or another visible expansion would be preferable. Screenshot 03 preserves this issue. The full underlying statements remain accessible in the saved accessibility record, but that does not make the visible table easy to read.
- **Final summary:** all four recorded rows and routing identities are visible. The narrow routing-identity column wraps onto several lines but is readable. The cache-stage list now prints one event per line, avoiding round 4's long horizontal line. The final 404.9 s timer is fully visible.
- No blank requested figure or unreadable light-theme color combination observed. This round's visual scope is the requested first screen, setup, sizing edge, appendix table and final summary; the round-4 interactive-slider test was not repeated.

## Screenshots and records

Seven numbered screenshots, validated as actual PNG files at **1348 × 913**:

- [round5-00-first-screen.png](../../logs/colab/round5-00-first-screen.png)
- [round5-01-setup.png](../../logs/colab/round5-01-setup.png)
- [round5-02-sizing-right-edge.png](../../logs/colab/round5-02-sizing-right-edge.png)
- [round5-03-appendix-table.png](../../logs/colab/round5-03-appendix-table.png)
- [round5-04-final-summary.png](../../logs/colab/round5-04-final-summary.png)
- [round5-05-final-runtime.png](../../logs/colab/round5-05-final-runtime.png)
- [round5-06-runtime-deleted.png](../../logs/colab/round5-06-runtime-deleted.png)

Records: [all 33 cells](../../logs/colab/round5-cells.json), [one-run timing record](../../logs/colab/round5-timing.json), [complete output](../../logs/colab/round5-results-ax.txt), [expanded final table](../../logs/colab/round5-results-expanded-ax.txt), [cleanup confirmation](../../logs/colab/round5-cleanup-ax.txt). Progress records [01](../../logs/colab/round5-progress-01-ax.txt), [02](../../logs/colab/round5-progress-02-ax.txt), [03](../../logs/colab/round5-progress-03-ax.txt) show setup progressing directly into chapters on the first run. Saved accessibility text redacts the Google-account identifier.

## Earlier rounds

- **Round 1 — FAIL**, `89b484bb484ca26f8bb8e1d8cb7ec26cccbea269`: setup succeeded; SciPy/NumPy import raised `_blas_supports_fpe` AttributeError. Diagnostic manual attempts: 8 pass / 4 fail. Runtime deleted. [Report](../../logs/colab/round1-report.md).
- **Round 2 — PASS**, `842afe27bead953c9ffd48a7ddceadb57fe0d39d`: uninterrupted first Run all, 17 code cells, **384.1 s including setup**, no retry/restart/uncaught traceback. Runtime deleted. [Report](../../logs/colab/round2-report.md).
- **Round 3 — FAIL**, `c84145b1ed66a37a87fe0c4ffb091a405e2d4034`: setup passed; imports rejected `figures/out/fig_cell.svg` in paper-evidence verification. Remaining 16 code cells did not execute. Runtime deleted. [Report](../../logs/colab/round3-report.md).
- **Round 4 — PASS after retry**, `2c81d2c1aa81ecebefaa93851f004eb17c9040ba`: initial run ceased after setup without traceback; second Run all completed all 18 code cells in **405.0 s** (initial attempt excluded). Math, slider at two positions and chapter-8 outputs verified. Runtime deleted. [Report](../../logs/colab/round4-report.md).

## Status and interface request

Round-5 first-run verification, required captures and cleanup are complete. **No execution blocker.** Remaining presentation request: wrap or visibly expand Appendix A's truncated scope text. No implementation changes were made outside COLAB ownership.

Validation: real Colab first Run all, execution counts 1–18, final prerequisite/source assertions, full output inspection, all-cell inventory, screenshot PNG decode and report-link checks. No local unit tests needed because no code changed.
