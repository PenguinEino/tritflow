# COLAB — round 3, 2026-10-18

**FAIL: Run all stops in imports before chapter 0.** The fresh GitHub notebook loaded the editorial rewrite, paper figures and chapter-8 code. Setup completed, but `load_paper(ROOT)` rejected `figures/out/fig_cell.svg`. No chapter computation, sizing widget or chapter-8 generated schematic/GDS was produced. This round does not verify those features.

## Environment and procedure

- Target: https://colab.research.google.com/github/PenguinEino/tritflow/blob/colab-v0/notebook/tritflow_tr1um.ipynb
- Chrome extension surface through `cua_repl`; reloaded the GitHub notebook. Initial runtime was disconnected and deletion was disabled, so there was no old runtime to delete. Inspected runtime settings: Python 3, CPU selected, latest recommended runtime; connected a fresh standard free Google Compute Engine backend (12.67 GB RAM).
- Used **Runtime → Run all**, accepted the authorized GitHub warning. No notebook edits, manual reruns, guard bypasses or source fixes.
- Printed source commit: **`c84145b1ed66a37a87fe0c4ffb091a405e2d4034`**, ref `colab-v0`.
- Printed KLayout: `/usr/bin/klayout`, **0.30.6**. Printed ngspice: `/usr/bin/ngspice`, **ngspice-42**, KLU Direct Linear Solver.
- Host scientific packages preserved: NumPy **2.1.3**, SciPy **1.16.3**, Matplotlib **3.10.0**, Plotly **5.24.1**.
- Setup wall time: **not shown in the captured Colab UI**; complete source/version output is preserved. Run all completion time: **unavailable, because the run failed**; the final timer cell never ran. Run all clicked 22:38:00 JST, warning accepted 22:38:04.743; failure was recorded by 22:40:03.205 (118.5 s after acceptance, an observation upper bound, not measured execution time). Colab did not retain execution counts or gutter durations in the captured final state.
- Deleted the runtime using Runtime → Disconnect and delete runtime → Yes at **22:42:02 JST**. Confirmed **Reconnect** afterward. No credentials entered, sign-in, OAuth, saving, sharing, paid upgrade or account-setting changes.

## Traceback — cell 2 (`imports`)

```text
RuntimeError                              Traceback (most recent call last)
/tmp/ipykernel_2146/2922323329.py in <cell line: 0>()
     38 from predictions import divider, zero_dc, rail_power
     39 from presentation import details_html, details_svg
---> 40 paper = load_paper(ROOT)
     41 narrative_values = context(ROOT)

/content/tritflow/notebook/paper_evidence.py in load_paper(root)
     25 for name, expected in record['repository_sha256'].items():
     26     if digest(root / name) != expected:
---> 27         raise RuntimeError(f'Static figure evidence changed: {name}. Rebuild the paper evidence and notebook together.')

RuntimeError: Static figure evidence changed: figures/out/fig_cell.svg. Rebuild the paper evidence and notebook together.
```

This is the only emitted traceback. The UI evidence establishes that the repository-artifact digest check failed; it does not distinguish a missing file from different file bytes. The NumPy/SciPy import incompatibility from round 1 did not recur before this failure.

## Every cell

Cell numbers are Colab's zero-based indices. There are 18 code cells and 15 text cells. Only setup and imports ran; the remaining 16 code cells have empty outputs. Text rendering and embedded paper figures are not fresh simulation results. “—” means no execution time applies or the cell did not execute.

| Cell | Purpose | Result | Wall time |
|---|---|---|---|
| 0 | Opening narrative / paper overview | Rendered (text/static) | — |
| 1 | Setup | Ran; setup output complete | Not shown |
| 2 | Imports / paper-evidence verification | ERROR: paper-evidence check | Not shown |
| 3 | Chapter 0 narrative | Rendered (text/static) | — |
| 4 | Chapter 0 live adder | Not run; stopped at cell 2 | — |
| 5 | Chapter 1 narrative / DC paper figure | Rendered (text/static) | — |
| 6 | Chapter 1 gate checks / live DC | Not run; stopped at cell 2 | — |
| 7 | Chapter 2 narrative / sizing paper figure | Rendered (text/static) | — |
| 8 | Chapter 2 sizing / slider | Not run; stopped at cell 2 | — |
| 9 | Chapter 3 narrative / cell-layout figure | Rendered (text/static) | — |
| 10 | Chapter 3 cell evidence | Not run; stopped at cell 2 | — |
| 11 | Chapter 4 narrative / arithmetic figure | Rendered (text/static) | — |
| 12 | Chapter 4 arithmetic checks | Not run; stopped at cell 2 | — |
| 13 | Chapter 5 narrative | Rendered (text/static) | — |
| 14 | Chapter 5 synthesis | Not run; stopped at cell 2 | — |
| 15 | Chapter 5 mapped schematic | Not run; stopped at cell 2 | — |
| 16 | Chapter 6 narrative / placement figure | Rendered (text/static) | — |
| 17 | Chapter 6 live P&R | Not run; stopped at cell 2 | — |
| 18 | Chapter 7 narrative / post-layout figure | Rendered (text/static) | — |
| 19 | Chapter 7 matched pre/post simulation | Not run; stopped at cell 2 | — |
| 20 | Chapter 7 scaling narrative / paper figure | Rendered (text/static) | — |
| 21 | Chapter 7 published scaling/load results | Not run; stopped at cell 2 | — |
| 22 | Chapter 8 narrative | Rendered (text/static) | — |
| 23 | Chapter 8 edited HDL | Not run; stopped at cell 2 | — |
| 24 | Chapter 8 custom flow / schematic / GDS | Not run; stopped at cell 2 | — |
| 25 | Chapter 8 diagnostic introduction | Rendered (text/static) | — |
| 26 | Chapter 8 expected HDL diagnostic | Not run; stopped at cell 2 | — |
| 27 | Chapter 9 outlook / measurement table | Rendered (text/static) | — |
| 28 | Appendix A scope | Rendered (text/static) | — |
| 29 | Appendix B evidence introduction | Rendered (text/static) | — |
| 30 | Appendix B characterization | Not run; stopped at cell 2 | — |
| 31 | Appendix B four-design campaign | Not run; stopped at cell 2 | — |
| 32 | Appendix B final assertions / timings | Not run; stopped at cell 2 | — |

## Visual and interaction findings

- **First screen:** title and body are readable in Colab's light theme; the overview image renders with all five panels. Its small serif annotations and miniature HDL are much smaller than the surrounding prose. The caption repeats the 17-line / 64-cell / DRC-zero / LVS-match result in consecutive paragraphs, making the opening dense. The first viewport ends before the Run-all guidance and setup, requiring scrolling. No blank hero panel was observed.
- **Math rendering:** chapter 1 shows literal `\operatorname`, `\frac`, `\qquad`, subscripts and bracket delimiters; chapter 2 and chapter 7 also show raw formula commands. This makes the prediction sections hard to read. Screenshot 06 records chapter 1.
- **Width/overflow:** the chapter-2 sizing figure's rightmost x-axis caption extends beyond the notebook's right edge at the captured 1348 × 913 viewport; a horizontal notebook scrollbar is present. Appendix A's long scope table also runs beyond the right edge. Other captured paper figures have readable plots, although the dense overview and cell-layout labels benefit from zooming. Vertical scrolling was used to frame figures; viewport clipping alone is not evidence of a malformed image.
- **Sizing slider:** unavailable. Cell 8 never executed; only its source call `show(sizing_slider(gi,PDK_ROOT))` and the static sizing paper figure were visible. No slider could be moved to a second position. Screenshot 08 records the empty-output boundary.
- **Chapter 8:** both the edited source and the new schematic/GDS display code are present. Cells 23/24 never ran, so no truth-table result, generated schematic, GDS or waveforms exist for this round. Screenshots 15/16 document this limitation; they are not successful output captures.
- **Chapter 5** refers to the preceding chapter-4 mapped-adder paper figure; live graph/schematic output is unavailable. **Chapter 9** contains an outlook and measurement table, with no separate hero figure.
- The opening's 384.1 s / commit `842afe2` verification statement still refers to round 2. It is labeled with that older commit and must not be read as a passing result for `c84145b`.

## Evidence

19 numbered screenshots, re-encoded and verified as actual PNG files (1348 × 913). Paper figures are explicitly named `static`; they are embedded notebook assets, not outputs generated during this failed run. Setup and the only traceback are captured in full.

- [round3-00-first-screen.png](../../logs/colab/round3-00-first-screen.png)
- [round3-01-setup-commit.png](../../logs/colab/round3-01-setup-commit.png)
- [round3-02-setup-versions.png](../../logs/colab/round3-02-setup-versions.png)
- [round3-03-imports-error.png](../../logs/colab/round3-03-imports-error.png)
- [round3-04-ch0-static-hero.png](../../logs/colab/round3-04-ch0-static-hero.png)
- [round3-05-ch1-static-hero.png](../../logs/colab/round3-05-ch1-static-hero.png)
- [round3-06-unrendered-math.png](../../logs/colab/round3-06-unrendered-math.png)
- [round3-07-ch2-static-hero.png](../../logs/colab/round3-07-ch2-static-hero.png)
- [round3-08-sizing-slider-unavailable.png](../../logs/colab/round3-08-sizing-slider-unavailable.png)
- [round3-09-ch3-static-hero.png](../../logs/colab/round3-09-ch3-static-hero.png)
- [round3-10-ch4-static-hero.png](../../logs/colab/round3-10-ch4-static-hero.png)
- [round3-11-ch5-unexecuted.png](../../logs/colab/round3-11-ch5-unexecuted.png)
- [round3-12-ch6-static-hero.png](../../logs/colab/round3-12-ch6-static-hero.png)
- [round3-13-ch7-static-hero.png](../../logs/colab/round3-13-ch7-static-hero.png)
- [round3-14-ch7-scaling.png](../../logs/colab/round3-14-ch7-scaling.png)
- [round3-15-ch8-unexecuted.png](../../logs/colab/round3-15-ch8-unexecuted.png)
- [round3-16-ch8-custom-unexecuted.png](../../logs/colab/round3-16-ch8-custom-unexecuted.png)
- [round3-17-ch9-outlook.png](../../logs/colab/round3-17-ch9-outlook.png)
- [round3-18-runtime-deleted.png](../../logs/colab/round3-18-runtime-deleted.png)

Machine-readable records: [all 33 cells](../../logs/colab/round3-cells.json), [timing observations](../../logs/colab/round3-timing.json), [failed-run accessibility output](../../logs/colab/round3-results-ax.txt), [cleanup confirmation](../../logs/colab/round3-cleanup-ax.txt). Google-account identifiers are redacted from saved accessibility text.

## Earlier rounds

- **Round 1 — FAIL**, commit `89b484bb484ca26f8bb8e1d8cb7ec26cccbea269`: setup completed; first chapter failed in SciPy/NumPy with `AttributeError: module 'numpy._core._multiarray_umath' has no attribute '_blas_supports_fpe'`. Manual diagnostic attempts totaled 8 passing / 4 failing code cells; additional missing-state and raw-HTML presentation problems. Runtime deleted. [Archived report](../../logs/colab/round1-report.md).
- **Round 2 — PASS**, commit `842afe27bead953c9ffd48a7ddceadb57fe0d39d`: uninterrupted Run all, all 17 code cells, **384.1 s including setup**; no uncaught traceback, manual reruns or restart. KLayout 0.30.6/ngspice 42; main adder DRC 0, LVS matched and analog passed. Recorded campaign evidence was distinguished from fresh runs. Runtime deleted. [Archived report](../../logs/colab/round2-report.md).

## Status and interface requests

Verification and cleanup completed; **round-3 execution is blocked by the published paper-evidence artifact check**. Rebuild/package the paper evidence and notebook together so the expected `figures/out/fig_cell.svg` digest matches the artifact in a clean tag checkout, then rerun real Colab. Also repair Colab math delimiters and constrain the sizing figure/table widths. No implementation changes were made because COLAB owns only this report and `logs/colab/`.

Validation: real Colab UI run, traceback/output inspection, all-cell inventory, screenshot PNG decoding and report-link checks. No local code tests or package installations were needed; no code was changed.
