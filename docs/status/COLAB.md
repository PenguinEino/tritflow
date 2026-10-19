# COLAB — round 11

Verified 2026-10-19 on real Google Colab through the extension-backed Chrome browser surface. Target: `colab-v0 = 134dfe7`.

## Result

**FAIL / first Run all incomplete. Exactly one Run all, no retry.** Setup printed the expected source and tool versions. Subsequently all 35 code-cell execution counts were blank (`[ ]`), setup output was retained, and no later code outputs or final summary were present. No Python traceback was displayed. The new live chapter-1 Fig. 2 was absent. This reproduces a failure to complete a fresh Colab run, but does **not** establish that the new `fig_gates`/`style` imports failed.

The runtime log records a Jupyter server starting at 10:53:55 JST and a kernel starting at 10:53:59, after setup's version output at 10:53:33. This is consistent with a runtime/server restart during setup; the initiating cause is unconfirmed. No deliberate retry, restart, second Run all, or individual code-cell execution was performed. Blank execution records cannot distinguish cells that never ran from cells whose execution state was lost. They are recorded as unverified, not passed or definitely unexecuted.

The notebook was opened fresh from the GitHub URL. Initially Connect was shown and runtime deletion was unavailable; a new standard free CPU runtime was used. The GitHub warning was accepted. Runtime → Disconnect and delete runtime was completed and **Reconnect** was verified afterward. No credentials, sign-in, OAuth, notebook saving/sharing, or paid runtime was used. Only COLAB reports/evidence were written; existing implementation changes in the workspace were left untouched.

## Source, versions and timing

Printed source:

```text
Source: https://github.com/PenguinEino/tritflow.git ref=colab-v0 commit=134dfe793d8170a1547decbca76e558cbb7ca9a6
Scientific Python (host versions preserved): numpy=2.1.3, scipy=1.16.3, matplotlib=3.10.0, plotly=5.24.1
KLayout executable: /usr/bin/klayout
KLayout 0.30.6
ngspice executable: /usr/bin/ngspice
** ngspice-42 : Circuit level simulation program
** Compiled with KLU Direct Linear Solver
```

- Run all clicked: **10:52:00.373 JST**; GitHub warning accepted: **10:52:22.288 JST**.
- Final stopped/reset state recorded: **11:41:49.093 JST**. This is an observation timestamp, not a measured stopping time or run duration.
- Runtime deletion verified: **11:43:32.296 JST**.
- Setup wall time: **unavailable**; execution gutter had reset. Run all completion/runtime: **unavailable**; no completed final timer.
- The bottom status tooltip showed `実行時間: 1.391 秒` and a last-execution time of 10:53. Its jump target was the final cell. This is not evidence of setup duration or successful Run all completion, and is not used as either.
- Machine record: [round11-timing.json](../../logs/colab/round11-timing.json). Missing completion/timing values are JSON `null`.

## Failure investigation and requested Fig. 2 check

Setup was expanded and its output/source inspected; the changed chapter-1 method cell, later cells and final cells were inspected; the runtime log was opened and its newest 100 of 669 entries captured through the accessibility tree. There was no traceback to expand or copy. Red run controls were visible on final cells, but no exception text or output accompanied them. A specific Python failing line cannot be assigned from this run. The log excerpt supports investigation of setup/runtime interruption before attributing the failure to the new figure import.

**Fig. 2 visual comparison: unverified.** Chapter 1 contains the highlighted Verilog definition, the new Python method cell, and the printed figure caption/explanation, but no regenerated plot between method and caption. Fonts, colours, plots and agreement with the published figure could therefore not be assessed. The visible code and prose were readable in the captured light theme; the missing figure is the material display problem. No comparison is inferred from an older figure or a local rendering.

### Verbatim failure evidence

**Python traceback: none displayed.** No exception name, traceback header, expandable traceback or exception body was available in the notebook accessibility tree. Consequently there is no complete Python traceback to transcribe. This is a failed/incomplete Run all, not a captured Python exception in the chapter-1 import.

The changed chapter-1 method cell was copied in full from Colab's editor via Select all / Copy, without changing or executing it:

```python
from fig_gates import simulate, draw                      # the paper's own Fig. 2 script
from style import save as save_figure
gates = flow.load(ROOT/"examples/gates.tv", "gates")       # the definition shown above
t = gates.truth_table()                                    # all nine input pairs, ideal trits
curves = simulate(CELLS_DIR/"out")                         # ten ngspice DC sweeps of the extracted layouts
png = save_figure(draw(curves), "fig_gates", out=BUILD/"figures")
display(Image(filename=str(png), width=1000))              # Fig. 2, regenerated from your own run
v_a, v_y, i_ma = curves["INV"][0]
i0 = int(np.argmin(abs(v_a)))
print(f"A = 0 V:  Y = {1e3*v_y[i0]:.1f} mV,  supply current = {i_ma[i0]:.3f} mA")
```

The setup cell, where output remained after execution records reset, was likewise copied in full:

```python
#@title Setup: clone TritFlow at the release tag, install KLayout and ngspice, fetch the pinned TR-1um PDK { display-mode: "form" }
_TRITFLOW_SETUP_READY = False
globals().pop("_tf_cells", None)
import os, sys, json, time, hashlib, subprocess, importlib.util
from pathlib import Path
started = time.monotonic()
try:
    IN_COLAB = importlib.util.find_spec("google.colab") is not None
except ModuleNotFoundError:
    IN_COLAB = False
SOURCE_URL = "https://github.com/PenguinEino/tritflow.git"
SOURCE_REF = os.environ.get("TRITFLOW_REF", "colab-v0")
def source_git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()
if IN_COLAB:
    ROOT = Path("/content/tritflow")
    if not SOURCE_REF or SOURCE_REF.startswith("-") or any(c.isspace() for c in SOURCE_REF):
        raise ValueError("TRITFLOW_REF must name a Git tag or branch")
    if not ROOT.exists():
        subprocess.run(["git", "clone", "--depth", "1", "--single-branch", "--branch", SOURCE_REF,
                        SOURCE_URL, str(ROOT)], check=True)
    if not (ROOT/".git").is_dir():
        raise RuntimeError("/content/tritflow must be a git clone; use a fresh Colab runtime")
    if source_git("remote", "get-url", "origin").removesuffix(".git") != SOURCE_URL.removesuffix(".git"):
        raise RuntimeError("existing checkout has a different origin; use a fresh Colab runtime")
    SOURCE_COMMIT = source_git("rev-parse", "--verify", "HEAD^{commit}")
    requested_commit = source_git("rev-parse", "--verify", SOURCE_REF+"^{commit}")
    if SOURCE_COMMIT != requested_commit or source_git("status", "--porcelain", "--untracked-files=no"):
        raise RuntimeError("existing checkout differs from TRITFLOW_REF; use a fresh Colab runtime")
    print(f"Source: {SOURCE_URL} ref={SOURCE_REF} commit={SOURCE_COMMIT}", flush=True)
    if not (ROOT/"notebook/runtime_support.py").is_file():
        raise RuntimeError("TRITFLOW_REF predates this notebook's setup. Select its matching immutable release with TRITFLOW_REF in a fresh runtime.")
    sys.path.insert(0, str(ROOT/"notebook"))
    from runtime_support import SETUP_SCHEMA
    runtime = ROOT/"notebook/runtime.json"
    if not runtime.is_file() or json.loads(runtime.read_text()).get("TRITFLOW_SETUP_SCHEMA") != SETUP_SCHEMA:
        subprocess.run(["bash", str(ROOT/"notebook/colab_setup.sh"), "--source", str(ROOT)], check=True)
    os.environ.update(json.loads(runtime.read_text()))
else:
    candidates = [Path(os.environ.get("TRITFLOW_ROOT", ".")), Path.cwd(), Path.cwd().parent]
    ROOT = next((p.resolve() for p in candidates if (p/"pyproject.toml").is_file()
                 and (p/"tritflow").is_dir()), None)
    if ROOT is None:
        raise RuntimeError("run locally from the full checkout or set TRITFLOW_ROOT")
    SOURCE_COMMIT = source_git("rev-parse", "--verify", "HEAD^{commit}") if (ROOT/".git").exists() else "tracked-tree export (no .git)"
    print(f"Source: {ROOT} commit={SOURCE_COMMIT}")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT/"notebook"))
sys.path.append(str(ROOT/"figures"))   # the paper's figure scripts, reused by method cells
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from runtime_support import check_runtime, print_tool_versions
check_runtime()
print_tool_versions()
_TRITFLOW_SETUP_READY = True
```

Selected runtime-log entries copied from the accessibility tree, newest first (timestamps are the displayed local time, JST):

```text
Oct 19, 2026, 11:00:01 AM
Got events for closed stream <zmq.eventloop.zmqstream.ZMQStream object at 0x7df7470a56d0>

Oct 19, 2026, 10:54:01 AM
Setting websocket_ping_timeout=30000

Oct 19, 2026, 10:54:01 AM
The websocket_ping_timeout (90000) cannot be longer than the websocket_ping_interval (30000).

Oct 19, 2026, 10:53:59 AM
Kernel started: 7efbd07a-2758-4f28-86f9-6dc113765d8c

Oct 19, 2026, 10:53:55 AM
Jupyter Server 2.20.0 is running at:

Oct 19, 2026, 10:53:55 AM
Serving notebooks from local directory: /
```

## Every cell

Notebook order below uses zero-based cell indices, matching previous JSON records. 57 cells: **35 code / 22 text**. Text rendering does not imply code execution. No code cell has a retained execution count or wall time. `null` records unavailable measurements, not zero duration. Setup has retained version output; all other code cells have no retained execution evidence. No traceback was displayed in any cell.

| Cell | Type | Purpose | Status | Execution | Wall time | Traceback |
|---:|---|---|---|---|---|---|
| 0 | text | TritFlow: balanced-ternary HDL to GDS on OpenSUSI TR-1um | rendered | — | — | none displayed |
| 1 | code | Setup (collapsed form) | output retained; execution reset | — | — | none displayed |
| 2 | code | Imports and run bookkeeping | unverified; no execution record | — | — | none displayed |
| 3 | text | From HDL to a checked adder layout; highlighted adder.tv definition | rendered | — | — | none displayed |
| 4 | code | Chapter 0 inputs: test conditions and an independent integer oracle | unverified; no execution record | — | — | none displayed |
| 5 | code | Chapter 0 public API: HDL → GDS → extracted SPICE | unverified; no execution record | — | — | none displayed |
| 6 | code | Chapter 0 checks | unverified; no execution record | — | — | none displayed |
| 7 | text | Three levels from ordinary CMOS | rendered | — | — | none displayed |
| 8 | code | Chapter 1 public API: gates and DC | unverified; no execution record | — | — | none displayed |
| 9 | text |  | rendered | — | — | none displayed |
| 10 | code | Chapter 1 checks and the taped-out INV schematic | unverified; no execution record | — | — | none displayed |
| 11 | text | Sizing sets the middle level | rendered | — | — | none displayed |
| 12 | code | Chapter 2 public API: sizing slider | unverified; no execution record | — | — | none displayed |
| 13 | code | Chapter 2 details: resistor-length candidates at the taped-out MOS sizes | unverified; no execution record | — | — | none displayed |
| 14 | text | Taped-out circuits become placeable cells | rendered | — | — | none displayed |
| 15 | code | Chapter 3 public API: cell view | unverified; no execution record | — | — | none displayed |
| 16 | code | Chapter 3 checks: template, clamp devices and cell qualification | unverified; no execution record | — | — | none displayed |
| 17 | text | Describe signed arithmetic in TritVerilog | rendered | — | — | none displayed |
| 18 | text | Chapter 4 highlighted half_add.tv and full_add.tv definitions | rendered | — | — | none displayed |
| 19 | code | Chapter 4 public API: arithmetic | unverified; no execution record | — | — | none displayed |
| 20 | code | Chapter 4 checks: cell counts against the taped-out schematics | unverified; no execution record | — | — | none displayed |
| 21 | text | Follow an expression into cells | rendered | — | — | none displayed |
| 22 | code | Chapter 5 public API: synthesis and interactive half-adder schematic | unverified; no execution record | — | — | none displayed |
| 23 | code | Chapter 5 checks: mapping rules and gate-level TritVerilog | unverified; no execution record | — | — | none displayed |
| 24 | code | Chapter 5 public API: two-trit adder hierarchy schematic | unverified; no execution record | — | — | none displayed |
| 25 | text | Route signals and feed the standing current | rendered | — | — | none displayed |
| 26 | code | Chapter 6 public API: P&R view | unverified; no execution record | — | — | none displayed |
| 27 | code | Chapter 6 details and an optional floorplan experiment | unverified; no execution record | — | — | none displayed |
| 28 | text | Does the layout still work? | rendered | — | — | none displayed |
| 29 | code | Chapter 7 public API: device-only SPICE and wire overlay | unverified; no execution record | — | — | none displayed |
| 30 | code | Chapter 7 checks: identical devices with and without wire C | unverified; no execution record | — | — | none displayed |
| 31 | text | Chapter 7 scaling and power evidence | rendered | — | — | none displayed |
| 32 | code | Chapter 7 recorded width and load campaigns | unverified; no execution record | — | — | none displayed |
| 33 | text | Predict with static timing, confirm with SPICE | rendered | — | — | none displayed |
| 34 | code | Chapter 7 public API: STA vs SPICE | unverified; no execution record | — | — | none displayed |
| 35 | code | Chapter 7 STA comparison table and critical path | unverified; no execution record | — | — | none displayed |
| 36 | text | STA validation figure and scope | rendered | — | — | none displayed |
| 37 | text | Change the circuit and close the loop | rendered | — | — | none displayed |
| 38 | code | Chapter 8 editable formatted TritVerilog source definition | unverified; no execution record | — | — | none displayed |
| 39 | code | Chapter 8 circuit selection and independent reference setup | unverified; no execution record | — | — | none displayed |
| 40 | code | Chapter 8 synthesis / truth table | unverified; no execution record | — | — | none displayed |
| 41 | code | Chapter 8 check: every input state against the independent arithmetic reference | unverified; no execution record | — | — | none displayed |
| 42 | code | Chapter 8 public API: layout | unverified; no execution record | — | — | none displayed |
| 43 | code | Chapter 8: extracted SPICE of your layout and its waveform | unverified; no execution record | — | — | none displayed |
| 44 | text | Expected diagnostic introduction | rendered | — | — | none displayed |
| 45 | code | Chapter 8 expected caught HDL error | unverified; no execution record | — | — | none displayed |
| 46 | text | Next: compare the model with silicon | rendered | — | — | none displayed |
| 47 | text | From your HDL to a shuttle-ready top | rendered | — | — | none displayed |
| 48 | code | Chapter 9 recorded chip image and signoff table | unverified; no execution record | — | — | none displayed |
| 49 | code | Chapter 9 checks: recorded signoff snapshot and pad map | unverified; no execution record | — | — | none displayed |
| 50 | text | Chip results and remaining submission requirements | rendered | — | — | none displayed |
| 51 | text | Appendix A. What the results establish | rendered | — | — | none displayed |
| 52 | text | Appendix B. Verification evidence and how to rerun | rendered | — | — | none displayed |
| 53 | code | Appendix B: cell characterization and fanout evidence | unverified; no execution record | — | — | none displayed |
| 54 | code | Appendix B: four-design physical and timing campaign | unverified; no execution record | — | — | none displayed |
| 55 | code | Appendix B: evidence tables, provenance and run time | unverified; no execution record | — | — | none displayed |
| 56 | text | Appendix C. Use and extend TritFlow | rendered | — | — | none displayed |

Full per-cell record: [round11-cells.json](../../logs/colab/round11-cells.json), retaining the round-10 keys (`cell`, `type`, `id`, `title`, `execution`, `wallTime`, `status`, `traceback`, `purpose`). `traceback: false` means none displayed; it does not mark the cell successful.

## Evidence

Screenshots are actual PNG files. Browser dimensions changed during the session; no fixed-size comparison is claimed. The historical filename `ch1-unexecuted` names the screenshot, not a conclusion that execution never started.

- [round11-00-first-screen.png](../../logs/colab/round11-00-first-screen.png) — 2396 × 1723.
- [round11-01-setup-stop.png](../../logs/colab/round11-01-setup-stop.png) — 1348 × 969.
- [round11-02-ch1-unexecuted.png](../../logs/colab/round11-02-ch1-unexecuted.png) — 1348 × 969.
- [round11-03-setup-source.png](../../logs/colab/round11-03-setup-source.png) — 2396 × 1723.
- [round11-04-status.png](../../logs/colab/round11-04-status.png) — 2396 × 1723.
- [round11-05-runtime-deleted.png](../../logs/colab/round11-05-runtime-deleted.png) — 2396 × 1723.

Accessibility captures and exact copied source:

- [round11-progress-01-ax.txt](../../logs/colab/round11-progress-01-ax.txt)
- [round11-results-ax.txt](../../logs/colab/round11-results-ax.txt)
- [round11-runtime-log-ax.txt](../../logs/colab/round11-runtime-log-ax.txt)
- [round11-ch1-source.py](../../logs/colab/round11-ch1-source.py)
- [round11-setup-source.py](../../logs/colab/round11-setup-source.py)
- [round11-cleanup-ax.txt](../../logs/colab/round11-cleanup-ax.txt)

Saved full notebook accessibility captures redact the Google account identifier. Runtime-log capture contains only the inspected 100-row view; no claim is made about uninspected log entries. Failure evidence and copied cells above are also recorded verbatim in `logs/COLAB.last.md`.

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

## Status and interface requests

Round-11 verification and cleanup complete; **the notebook remains blocked for first-run release verification**. Investigate the setup/runtime interruption and lost execution state, then request another fresh-runtime verification. The reported chapter-1 import failure and regenerated figure appearance remain unverified in this one-run attempt. No implementation fix was attempted.

Validation: printed source and tool versions, all 57 cell records, exact copied setup/chapter-1 source, inspected runtime logs, screenshots, JSON consistency, PNG decoding, report links and runtime deletion. No local tests were run because this stream changed only reports/evidence; no local test substitutes for the failed real-Colab run.
