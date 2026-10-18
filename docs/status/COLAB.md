# COLAB — real Google Colab verification

Completed: 2026-10-18, approximately 18:39–18:48 JST.

## Overall result

**FAIL: installation finishes, but the unmodified `colab-v0` notebook does not
complete Run all.** Chapter 0 fails while importing SciPy/NumPy through LVS:
`numpy._core._multiarray_umath` lacks `_blas_supports_fpe`. The same failure
recurs independently in chapter 8. Chapters 6 and 7 then fail on missing
chapter-0 results (`lay`, `demo`).

All **12 code cells were attempted: 8 passed, 4 failed**. The initial Runtime →
Run all stopped at cell 4; cells 7 onward were subsequently run individually
in notebook order, without changing their code. A queued chapter-8 execution
was cancelled when chapter 7 failed, then explicitly run. These follow-up
results are not a successful Run all.

Target: https://colab.research.google.com/github/PenguinEino/tritflow/blob/colab-v0/notebook/tritflow_tr1um.ipynb

## Environment and procedure

Used `mcp__cua_repl` with the now-authorized extension-backed Chrome surface,
reusing target tab `1460509814`. Deleted its existing disposable runtime first
and connected a fresh runtime. Runtime type dialog showed **Python 3, CPU,
latest (recommended)**; premium accelerators were disabled. Used the standard
runtime without upgrading (approximately 12.67 GB RAM / 107.72 GB disk).
Invoked Runtime → Run all and accepted the GitHub-notebook warning.

Printed source identity:

```text
Source: https://github.com/PenguinEino/tritflow.git ref=colab-v0 commit=89b484bb484ca26f8bb8e1d8cb7ec26cccbea269
```

The older tag was deliberately retained. KLayout and ngspice **version strings
were not printed in the observed notebook output**; no version is inferred
from local installations or repository pins. Setup's visible output was the
source identity and `'offscreen'`. Traceback package paths use
`/usr/local/lib/python3.13/dist-packages/`.

## Timing

- Setup cell: Colab displays **1 min**, rounded; finer timing was not shown.
- Run all selected: **18:39:07.215 JST**; GitHub warning accepted at
  **18:39:13.104 JST**. The failed/stopped state was recorded by
  **18:41:40.252 JST**, at most **147.148 s after acceptance**. This is an
  observation bound, not an exact execution duration. There is no completed
  full-notebook Run all runtime.
- The final summary cell, manually run after the remaining cells, printed
  **422.7 s including setup**. This includes human/automation inspection gaps
  and manual follow-up; it is not a successful Run all benchmark.
- Timing evidence: [run-timing.json](../../logs/colab/run-timing.json).

## Every cell

Indices are Colab's zero-based cell numbers (`tritflow-XX`), not execution
counts. Rounded times are quoted as shown. Exact tooltip times are included
only where observed. Text cells render without execution or wall time.

| Cell | Kind / purpose | Initial Run all | Final observed result | Wall time shown |
|---|---|---|---|---|
| 0 | Text: title/introduction | Rendered | Rendered | — |
| 1 | Code: clone/install/setup | Passed, `[1]` | Passed | 1 min |
| 2 | Code: imports/helpers | Passed, `[2]` | Passed | 0 s |
| 3 | Text: chapter 0 | Rendered | Rendered | — |
| 4 | Code: complete two-trit adder | Error, `[3]` | AttributeError; Run all stopped | 21 s |
| 5 | Text: GDS explanation | Rendered | Rendered | — |
| 6 | Text: chapter 1 | Rendered | Rendered | — |
| 7 | Code: gates/schematics/DC | Cancelled before execution | Passed manually, `[4]` | 2 s; tooltip 2.006 s |
| 8 | Text: chapter 2 | Rendered | Rendered | — |
| 9 | Code: characterization | Cancelled before execution | Passed manually, `[5]` | 0 s; tooltip 0.058 s |
| 10 | Text: chapter 3 | Rendered | Rendered | — |
| 11 | Code: cell layout/qualification | Cancelled before execution | Passed manually, `[6]` | 0 s; tooltip 0.189 s |
| 12 | Text: chapter 4 | Rendered | Rendered | — |
| 13 | Code: HA/FA logic/counts | Cancelled before execution | Passed manually, `[7]` | 0 s |
| 14 | Text: chapter 5 | Rendered | Rendered | — |
| 15 | Code: synthesis/graphs/mapping | Cancelled before execution | Passed manually, `[8]` | 0 s; tooltip 0.161 s |
| 16 | Text: chapter 6 | Rendered | Rendered | — |
| 17 | Code: P&R metrics/animation | Cancelled before execution | NameError manually, `[9]` | 0 s; tooltip 0.046 s |
| 18 | Text: chapter 7 | Rendered | Rendered | — |
| 19 | Code: pre/post comparison | Cancelled before execution | NameError manually, `[10]` | 1 min |
| 20 | Text: chapter 8 | Rendered | Rendered | — |
| 21 | Code: editable experiment | Cancelled before execution | AttributeError manually, `[11]` | 10 s |
| 22 | Text: chapter 9 | Rendered | Rendered | — |
| 23 | Code: cache/elapsed summary | Cancelled before execution | Passed manually, `[12]` | 0 s; tooltip 0.033 s |

Cancelled cells initially displayed queue/cancellation ages despite empty
execution counters; those were not treated as execution wall times.

## Failing cells and traceback excerpts

Excerpts below retain the observed failing statements and exception text;
whitespace is normalized from Colab's display. The UI collapses intermediate
frames. Expanded early call chains are retained in the linked AX logs.

### Cell 4 — chapter 0, installation/runtime failure

```text
Running: adder2-complete
AttributeError                            Traceback (most recent call last)
/tmp/ipykernel_1425/2182690211.py in <cell line: 0>()
---> 33 demo = cache.run("adder2-complete", ...)
/content/tritflow/notebook/cache.py:84 in run
        result = producer()
/tmp/ipykernel_1425/2182690211.py:25 in complete_adder
        lvs = lay.lvs()
/content/tritflow/tritflow/flow.py:155 in lvs
        from tritflow.extract import extract_layout
/content/tritflow/tritflow/extract/__init__.py:7
        from .ir import solve_resistive_network, estimate_ir_drop, DEFAULT_SHEET_OHM
/content/tritflow/tritflow/extract/ir.py:6
        from scipy.sparse import coo_matrix
... SciPy import frames ...
/usr/local/lib/python3.13/dist-packages/numpy/testing/_private/utils.py:93
        BLAS_SUPPORTS_FPE = np._core._multiarray_umath._blas_supports_fpe(None)
AttributeError: module 'numpy._core._multiarray_umath' has no attribute '_blas_supports_fpe'
```

Evidence: [screenshot](../../logs/colab/02-cell04-chapter00-error.png),
[expanded early frames](../../logs/colab/cell04-traceback-ax.txt).
No chapter-0 figures were produced. This does not establish top-level LVS,
post-layout analog pass, or complete DRC/LVS qualification.

### Cell 17 — chapter 6, downstream dependency failure

```text
NameError                                 Traceback (most recent call last)
/tmp/ipykernel_1425/2307293446.py in <cell line: 0>()
----> 1 table([["Metric", "Two-trit adder"]]+[[k,v] for k,v in lay.stats.items()])
NameError: name 'lay' is not defined
```

Evidence: [screenshot](../../logs/colab/08-cell17-chapter06-error.png).
Chapter 0 never reached its global `lay` assignment. No placement animation
was produced.

### Cell 19 — chapter 7, downstream dependency failure

```text
Running: adder2-pre
NameError                                 Traceback (most recent call last)
/tmp/ipykernel_1425/3894088357.py in <cell line: 0>()
      5 assert pre["measurements"]["passed"]
----> 6 assert pre["stimulus"]["vectors"] == demo["stimulus"]["vectors"]
NameError: name 'demo' is not defined
```

Evidence: [screenshot](../../logs/colab/09-cell19-chapter07-error.png).
The pre-layout simulation returned and its pass assertion succeeded before
this error. The pre/post comparison and waveform were not produced.

### Cell 21 — chapter 8, same NumPy import failure

```text
Running: editable-experiment
AttributeError                            Traceback (most recent call last)
/tmp/ipykernel_1425/1702845732.py in <cell line: 0>()
---> 14 custom_post = cache.run("editable-experiment", ..., run_custom, ...)
/content/tritflow/notebook/cache.py:84 in run
        result = producer()
/tmp/ipykernel_1425/1702845732.py:10 in run_custom
        assert routed.drc()["clean"] and routed.lvs()["matched"]
/content/tritflow/tritflow/flow.py:155 in lvs
        from tritflow.extract import extract_layout
... extract.ir → scipy.sparse → NumPy testing import ...
/usr/local/lib/python3.13/dist-packages/numpy/testing/_private/utils.py:93
        BLAS_SUPPORTS_FPE = np._core._multiarray_umath._blas_supports_fpe(None)
AttributeError: module 'numpy._core._multiarray_umath' has no attribute '_blas_supports_fpe'
```

Evidence: [screenshot](../../logs/colab/10-cell21-chapter08-error.png),
[expanded early frames](../../logs/colab/cell21-traceback-ax.txt).
The truth-output string and gate graph appear before failure; the post-layout
waveform does not.

## Figures and screenshots

Screenshots are numbered in notebook order under `logs/colab/`. All 15 files
were verified as actual PNGs, 1348×913. The tool returned JPEG bytes; these
were re-encoded to PNG without changing displayed content.

| Chapter / stage | Screenshot | Visual observation |
|---|---|---|
| Setup | [01](../../logs/colab/01-setup-complete.png) | Source hash and successful setup/import indicators; no printed tool versions |
| 0 | [02](../../logs/colab/02-cell04-chapter00-error.png) | Error; adder graph, waveform and routed GDS figures unavailable |
| 1 | [03 DC](../../logs/colab/03-cell07-chapter01-dc.png), [03a schematic](../../logs/colab/03a-cell07-chapter01-schematic.png) | DC traces, axes, bands and legend readable; schematics visible, but INV resistor property text overlaps symbols/labels and large drawings require scrolling |
| 2 | [04](../../logs/colab/04-cell09-chapter02-characterization.png) | Characterization and conditions tables render; many decimal digits and long dictionaries make the table dense |
| 3 | [05](../../logs/colab/05-cell11-chapter03-standard-cells.png) | NANY layout raster appears on black backing; fine geometry/text is dense at the displayed scale; qualification table renders |
| 4 | [06](../../logs/colab/06-cell13-chapter04-truth-output.png) | HA/FA truth tables display literal quoted HTML strings, truncated with an ellipsis, rather than tables; count table renders |
| 5 | [07](../../logs/colab/07-cell15-chapter05-gate-graph.png) | Colored gate graph, labels and legend readable; synthesis report renders |
| 6 | [08](../../logs/colab/08-cell17-chapter06-error.png) | Error; main animation unavailable |
| 7 | [09](../../logs/colab/09-cell19-chapter07-error.png) | Error; comparison waveform unavailable |
| 8 | [10 error](../../logs/colab/10-cell21-chapter08-error.png), [10a graph](../../logs/colab/10a-cell21-chapter08-gate-graph.png) | Gate graph readable; truth table again appears as literal HTML; post-layout waveform unavailable |
| 9 / summary | [11](../../logs/colab/11-cell23-chapter09-summary.png) | Prose and elapsed/cache summary render; chapter has no main figure |
| Cleanup | [12](../../logs/colab/12-runtime-deleted.png) | Reconnect button confirms disconnected state after deletion |

Chapter 1's gate truth table has the same raw-HTML display issue as chapters
4 and 8. Among figures actually produced, none was blank. Current Colab theme
was light; no claim is made about dark-theme rendering. Large schematic
viewport crops are not evidence that the source image itself is clipped.

## Final printed summary

```text
Cache stages: [('nany-dc', 'run'), ('adder2-pre', 'run')]
Run time including setup: 422.7 s
Artifacts: /content/tritflow/build/notebook
```

The failed complete-adder/editable stages did not register completed cache
entries. Notebook evidence: [notebook-results-ax.txt](../../logs/colab/notebook-results-ax.txt).

## Cleanup and limits

Selected Runtime → Disconnect and delete runtime, accepted the disposable
runtime reset confirmation, and verified **Reconnect** in the toolbar at
**18:47:55 JST**. Saved [cleanup evidence](../../logs/colab/cleanup-ax.txt).
No runtime remains connected in the tested tab.

No credentials were typed, no sign-in/account creation or OAuth permissions
were requested or granted by this stream, and no notebook was saved to Drive
or GitHub or shared. No paid tier was selected. No notebook code, repository
code, reference material, or git state was changed. Writes were confined to
`docs/status/COLAB.md` and `logs/colab/`; no packages were installed locally.

## Blockers / interface requests / follow-up

The browser-tool blocker is resolved. Verification work is complete with the
failure results above. No further execution is in progress; no code-contract
interface changes are requested.

Integrator follow-up: reproduce/fix the NumPy/SciPy import failure on the latest
free Colab image, then rerun in a fresh runtime. A mixed preloaded/installed
NumPy state is a possible explanation, not established by this run; test
compatible dependencies and whether an explicit post-install restart is
required. Also render `truth_table_html(...)` as HTML rather than displaying
its returned string. Fixes were outside COLAB's owned paths and were not made.
Print tool versions explicitly in setup so future UI-only runs can record them.

## Validation

Real-Colab execution is the validation performed; there is no COLAB-owned
pytest area and no source change requiring a local test run. Every code cell
has a recorded final result, all four errors have screenshots and traceback
excerpts, and screenshot format/dimensions and cleanup were verified. The
install-inclusive successful Run all budget remains unverified.
