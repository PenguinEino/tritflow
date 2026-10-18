# COLAB — round 2

Verified 2026-10-18, approximately 21:21–21:31 JST, using real Google Colab
through the extension-backed Chrome surface in `mcp__cua_repl`.

## Overall result

**PASS: uninterrupted Runtime → Run all completed all 17 code cells, with no
uncaught exceptions, in 384.1 s including setup (6 min 24.1 s).** All 16 text
cells rendered. The final prerequisite/source-consistency checks passed. No
manual cell reruns, dependency changes, notebook edits, or runtime restarts
were needed.

This is a successful default run with explicitly labelled recorded campaigns;
it is not a fresh recomputation of every published campaign. Two remaining
figure presentation problems are described below.

Target:
https://colab.research.google.com/github/PenguinEino/tritflow/blob/colab-v0/notebook/tritflow_tr1um.ipynb

Printed source identity:

```text
Source: https://github.com/PenguinEino/tritflow.git ref=colab-v0 commit=842afe27bead953c9ffd48a7ddceadb57fe0d39d
```

This matches the requested `842afe2` release.

## Environment, setup and timing

Reloaded the existing target tab (`1460509814`) to replace round 1's notebook.
Before reload it showed Reconnect; after reload it offered a new runtime, and
Disconnect/delete was disabled. No old runtime was reused. The runtime type
dialog showed Python 3, CPU, latest/recommended; premium accelerators were
disabled. Connected the standard free runtime, selected Runtime → Run all,
and accepted the GitHub-notebook warning. Left default notebook options intact.

Actual setup printout:

| Tool | Printed version |
|---|---|
| NumPy | 2.1.3 |
| SciPy | 1.16.3 |
| Matplotlib | 3.10.0 |
| Plotly | 5.24.1 |
| KLayout executable | `/usr/bin/klayout`, KLayout 0.30.6 |
| ngspice executable | `/usr/bin/ngspice`, ngspice-42, compiled with KLU |

The setup explicitly printed `Scientific Python (host versions preserved)`.
The round-1 NumPy attribute error did not recur.

- Setup cell displayed **1 min**, rounded; finer setup wall time was not shown.
- Run all selected at **21:21:08.103 JST**; warning accepted at
  **21:21:16.361 JST**.
- Final cell printed **Run time including setup: 384.1 s**. This measures the
  notebook run, without a manual continuation as in round 1.
- Completed state was recorded at **21:28:30.018 JST**, after some figure
  capture; this later observation timestamp is not the execution duration.
- Runtime deletion verified at **21:31:09.452 JST**.

Evidence: [setup screenshot](../../logs/colab/round2-01-setup.png),
[final timing table](../../logs/colab/round2-18-ch09-summary.png),
[timestamps](../../logs/colab/round2-timing.json).

The printed stage table separates fresh work from recorded lookup:

| Stage | State | Wall time printed (s) |
|---|---|---:|
| adder2-complete | run | 148.9 |
| adder2-pre | run | 128 |
| your-minmax | run | 27.44 |
| adder2-raster | run | 0.386 |
| nany-dc | run | 0.125 |
| four-adder4 | recorded | 0.138 |
| four-full_add | recorded | 0.037 |
| four-mac1 | recorded | 0.153 |
| four-mul1 | recorded | 0.009 |

The four-design outputs state that native evidence hashes were verified and
that these are not new checks. Characterization, sizing and width/load
campaigns also read published evidence. No recorded producer timing is
presented here as fresh Colab execution.

## Every cell

Cell numbers are zero-based notebook indices (`tritflow-XX`); execution counts
are shown separately. All code cells passed in the single Run all. Times below
are the rounded Colab gutter values; `0 s` does not mean zero computation.
Text cells render without an execution count or wall time.

| Cell | Content | Result | Execution | Wall time shown |
|---|---|---|---:|---|
| 0 | Title/introduction | Rendered | — | — |
| 1 | Clone/install/runtime checks/version printout | PASS | 1 | 1 min |
| 2 | Imports, pinned-PDK/source/cache setup | PASS | 2 | 2 s |
| 3 | Chapter 0 introduction | Rendered | — | — |
| 4 | Complete two-trit adder, DRC/LVS, post-layout simulation/GDS | PASS | 3 | 2 min |
| 5 | GDS explanation | Rendered | — | — |
| 6 | Chapter 1 introduction | Rendered | — | — |
| 7 | Gate truth tables, primitive schematic, NANY DC | PASS | 4 | 0 s |
| 8 | Chapter 2 introduction | Rendered | — | — |
| 9 | Characterization and measured fanout tables | PASS | 5 | 0 s |
| 10 | Sizing experiment explanation | Rendered | — | — |
| 11 | INV/NANY sizing records and adopted transfer curves | PASS | 6 | 0 s |
| 12 | Chapter 3 introduction | Rendered | — | — |
| 13 | Cell views, clamp mapping, abutment, qualification hashes | PASS | 7 | 0 s |
| 14 | Chapter 4 introduction | Rendered | — | — |
| 15 | HA/FA reference schematic, truth tables/count assertions | PASS | 8 | 0 s |
| 16 | Chapter 5 introduction | Rendered | — | — |
| 17 | Synthesis, gate diagrams and expression mapping | PASS | 9 | 0 s |
| 18 | New mapped-schematic explanation | Rendered | — | — |
| 19 | New hierarchy and flat half-adder schematics | PASS | 10 | 0 s |
| 20 | Chapter 6 introduction | Rendered | — | — |
| 21 | P&R checks and placement animation | PASS | 11 | 0 s |
| 22 | Chapter 7 introduction | Rendered | — | — |
| 23 | Matched device-only/wire-C runs and annotated schematic | PASS | 12 | 2 min |
| 24 | Four-design evidence explanation | Rendered | — | — |
| 25 | Recorded four-design campaign, checks/tables/waveform | PASS | 13 | 0 s |
| 26 | Recorded scaling/load explanation | Rendered | — | — |
| 27 | Scaling/load provenance checks and figures | PASS | 14 | 0 s |
| 28 | Chapter 8 introduction | Rendered | — | — |
| 29 | Deliberately invalid HDL, caught diagnostic | PASS | 15 | 0 s |
| 30 | Selected minmax circuit, all inputs and physical/analog chain | PASS | 16 | 27 s |
| 31 | Chapter 9 measurement plan | Rendered | — | — |
| 32 | All-prerequisite/source checks and final timing summary | PASS | 17 | 0 s |

Machine-readable results: [round2-cells.json](../../logs/colab/round2-cells.json).
UI output evidence: [round2-results-ax.txt](../../logs/colab/round2-results-ax.txt).

## Errors and diagnostic output

**No failing cell or uncaught traceback occurred.**

Cell 29 intentionally catches `HDLError` and prints this expected example,
with a successful cell indicator:

```text
your_circuit.tv:2:17: arithmetic/comparison on trits is unsupported; use ~, &, |, nany and sized trit literals
Repair: use gates for signal arithmetic; e.g. nany(a,b) gives the negative saturated sum.
```

[Diagnostic screenshot](../../logs/colab/round2-16-ch08-expected-hdl-diagnostic.png).

The NANY sizing chart labels one solver failure in its **published candidate
campaign** (17 of 18 candidates pass); the selected adopted candidate passes.
The published load sweep deliberately includes failed/unsettled high-load
points and reports PASS at 12.8 / FAIL at 13 pF. Neither is a notebook execution
error or a new Colab solver failure.

## Observed circuit results

The opening adder reports **0 DRC violations**, **LVS matched=True** and
**Analog passed=True**, max sampled level error **0.04183 V**. It checks 243
logical states exhaustively; the analog sequence has 12 entries, 9 unique
states and 11 selected transitions, not exhaustive analog coverage. The die
is 1284×1038 µm with six physical rows and utilization 0.473.

The matched comparison table reports device-only / wire-C maximum settling:
`sum[1]` 132.1 / 149.3 ns; `sum[0]` 124.6 / 138.4 ns; `cout` 102.2 / 107 ns.
The selected minmax circuit produces passing lo/hi waveforms for all nine
input states in its selected sequence. These are nominal demonstrations
under the notebook's stated conditions.

## Figures and screenshot inventory

All **25** `logs/colab/round2-*.png` files were checked as actual PNGs at
1348×913. `cua_repl` returned JPEG bytes; they were re-encoded as PNG without
altering the displayed content. Tall Colab outputs have internal scrollbars;
paired captures preserve additional portions where needed.

| Chapter/stage | Screenshot suffixes after `round2-` | Observation |
|---|---|---|
| Setup | [01-setup](../../logs/colab/round2-01-setup.png) | Commit and all native/scientific version strings readable |
| 0 | [02 waveform](../../logs/colab/round2-02-ch00-waveform.png), [03 routing](../../logs/colab/round2-03-ch00-routing.png), [03b GDS](../../logs/colab/round2-03b-ch00-gds-raster.png), [03c lower GDS](../../logs/colab/round2-03c-ch00-gds-raster-bottom.png) | Real raster, vector routing and three-level waveforms appear; routing dropdown overlaps title |
| 1 | [04 DC](../../logs/colab/round2-04-ch01-dc.png), [04a truth table](../../logs/colab/round2-04a-ch01-truth-table.png) | DC curves/axes/bands readable; raw-HTML problem fixed; selected primitive drawing appears below table |
| 2 | [05 characterization](../../logs/colab/round2-05-ch02-characterization.png), [06 sizing](../../logs/colab/round2-06-ch02-sizing.png) | Compact numerical tables and adopted-dimension marker readable |
| 3 | [07 cell layout](../../logs/colab/round2-07-ch03-cell-layout.png) | Layers, rail/pin labels and obstruction legend visible |
| 4 | [08 reference schematic](../../logs/colab/round2-08-ch04-reference-schematic.png) | Half-adder drawing renders; fine source labels are small at default scale; truth tables render correctly |
| 5 | [09 gates](../../logs/colab/round2-09-ch05-gate-graph.png), [10 new hierarchy](../../logs/colab/round2-10-ch05-new-schematic.png), [10b flat schematic](../../logs/colab/round2-10b-ch05-flat-schematic.png) | New schematic stage renders connected branches/crossing gaps and settled-trit colors; no blank output |
| 6 | [11 placement](../../logs/colab/round2-11-ch06-placement.png) | Placement/HPWL/slider visible; Play/Pause controls overlap title |
| 7 | [12 comparison](../../logs/colab/round2-12-ch07-device-wire-comparison.png), [12b lower comparison](../../logs/colab/round2-12b-ch07-comparison-bottom.png), [13 annotated schematic](../../logs/colab/round2-13-ch07-annotated-schematic.png), [14 recorded full adder](../../logs/colab/round2-14-ch07-recorded-full-adder.png), [15 scaling](../../logs/colab/round2-15-ch07-width-scaling.png), [15b load boundary](../../logs/colab/round2-15b-ch07-load-boundary.png) | Waveforms, wire-C annotations and scaling render; load-boundary axis/annotations need repair |
| 8 | [16 expected diagnostic](../../logs/colab/round2-16-ch08-expected-hdl-diagnostic.png), [17 minmax](../../logs/colab/round2-17-ch08-minmax-waveforms.png) | Expected parser error is caught; final selected-circuit waveform passes |
| 9 | [18 summary](../../logs/colab/round2-18-ch09-summary.png) | Fresh/recorded timing table and 384.1 s total readable |
| Cleanup | [19 deleted runtime](../../logs/colab/round2-19-runtime-deleted.png) | Reconnect button visible after runtime deletion |

Remaining presentation findings:

1. **Plotly controls overlap titles.** The routing net selector covers part of
   `adder2_demo · physical routing`; placement Play/Pause covers part of
   `adder2_demo · placement annealing`. Plots themselves are populated.
2. **Load-boundary plot range/annotation problem.** Although its boundary is
   labelled 12.8/13 pF, the log x-axis extends through `1T` pF, squeezing all
   plotted points into the far-left part. The measured-boundary and settling
   window annotations overlap near the upper-right. This is visible in 15b;
   no cause is asserted without code investigation.
3. Tall raster/multi-figure outputs require scrolling inside the Colab output
   area as well as the notebook. Small historical schematic labels need zoom
   for detailed reading. No blank or broken image was observed. Current theme
   was light; dark-theme readability was not tested.
4. Introductory release-TODO prose still says `colab-v0` predates the notebook,
   despite this run loading and verifying the requested matching tag. The
   statement should be updated after integrating these results.

## Cleanup, limits and validation

Selected Runtime → Disconnect and delete runtime, accepted its disposable
runtime reset confirmation, then verified Reconnect. Evidence:
[round2-cleanup-ax.txt](../../logs/colab/round2-cleanup-ax.txt).

No credentials were entered, no sign-in or OAuth flow was performed, no Google
account settings were changed, and the notebook was not saved to Drive/GitHub
or shared. No paid tier was selected. No repository or notebook source was
edited, no git write commands were run locally, and no packages were installed
locally. Writes were confined to COLAB-owned paths.

Validation: single real-Colab Run all; sequential execution counts 1–17,
final all-prerequisite guard passed, no uncaught traceback in the recorded UI
outputs; all screenshot signatures/dimensions and evidence links checked.
No COLAB-owned pytest area or source changes require local tests.

## Short round-1 summary

Round 1 tested commit `89b484bb484ca26f8bb8e1d8cb7ec26cccbea269`: setup completed,
but Run all stopped at the SciPy/NumPy `_blas_supports_fpe` import error.
After manual attempts, 8/12 code cells passed and 4 failed, including two
missing-result dependency errors. Truth tables displayed raw HTML strings.
Round 2 resolves those observed execution and truth-table problems. Earlier
screenshots/logs remain; the full prior report is archived at
[round1-report.md](../../logs/colab/round1-report.md).

## Status / interface requests

Verification is complete; no runtime or work remains in progress. No execution
blocker or code-contract interface request remains. Integrator follow-up is
limited to the presentation findings above and updating release-validation
prose. The measured default run meets the ten-minute target with its declared
recorded campaigns; force-recomputing all campaigns was not part of this run.
