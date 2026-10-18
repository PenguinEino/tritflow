# FRONTEND status

Updated: 2026-10-18. **Complete.**

Phase 3: **flow API and notebook draft complete**. Clean Colab execution and
publication metadata are explicitly pending, as detailed below.

## Phase 3 handoff

- `tritflow/flow.py` implements the requested chain:
  `flow.load(path, top, params).synthesize().place_and_route()` followed by
  `.drc()`, `.lvs()`, and `.extract().simulate(vectors, load=...)`.
  `Circuit.truth_table()` delegates to the HDL simulator. `flow.loads()` accepts
  editable source; `net.simulate()` uses pre-layout cells; `flow.load_layout()`
  reopens public PNR artifacts without inventing fresh verification evidence.
- The facade calls only public HDL/synth, PNR `Library.load` /
  `place_and_route` / `pdk_drc` / `PnrResult`, extraction `extract_layout` /
  `gds_wire_capacitance` / `append_wire_capacitance`, and SIM `gate_spice` /
  `simulate` functions/classes. It does not modify another stream's code or
  substitute mock cells. Native reports/waveforms remain exposed. Unmatched
  LVS blocks post-layout simulation. A recent in-memory LVS result is reused
  only while GDS/reference/deck and extracted/report hashes remain unchanged.
- `notebook/tritflow_tr1um.ipynb` is a 24-cell, output-free English draft with
  chapters 0–9. Chapter 0 runs a two-trit adder through real-cell synthesis,
  GDS, DRC, LVS, actual-GDS wire C and ngspice, with an independent integer
  oracle. All 243 logical inputs are checked; six analog states are explicitly
  representative, not exhaustive transitions. The draft includes gate graphs,
  KLayout GDS raster, physical net highlighting, placement history, DC curves,
  pre/post waveforms and an editable nine-state circuit experiment.
- The newly delivered public `tritflow.viz.layout` and `tritflow.viz.waves`
  functions are integrated. No missing-visualization placeholders remain.
  Chapter 2 sizing/SVGs and the final N/load/IR result matrix have clearly
  marked TODO cells. These draft gaps are not presented as measured results.
- `notebook/cache.py` caches expensive stage dictionaries as gzip JSON, with
  hashes of code, library GDS/SPICE/characterization, PDK decks/models, package
  and executable versions, stage options and produced artifacts. It restores
  waveform arrays and stimulus tuples without pickle. Changed inputs/artifacts
  invalidate results. Failed producers do not publish a successful cache entry.
- `notebook/make_notebook.py` regenerates the notebook exactly.
  `notebook/validate_notebook.py` validates IDs/chapters/code and can execute
  every cell locally with headless Plotly serialization. No local install is
  performed by that executor. Usage is in `notebook/README.md`.
- `notebook/colab_setup.sh` wraps the tested Python setup planner/installer.
  It detects Ubuntu and amd64, installs ngspice via apt and the matching
  official KLayout 0.30.6 `.deb` via apt, installs pinned direct Python runtime
  dependencies plus this package editably, and unpacks the PDK at commit
  `5d963db9d44e192d37a0489c208bfccf2e2f690c`. It validates binary/archive
  SHA-256, archive paths/links and required source/PDK assets. It runs a real
  Ruby DRC-engine smoke macro and writes environment settings before notebook
  imports. No existing PDK checkout is overwritten. `--plan` is non-mutating;
  Ubuntu/architecture overrides are permitted only in plan mode.

Phase 3 checks:

```sh
python3 -m pytest tests/hdl tests/synth tests/viz notebook/tests -q
python3 notebook/validate_notebook.py
TRITFLOW_NOTEBOOK_BUILD=/tmp/tritflow-notebook-final python3 notebook/validate_notebook.py --execute
bash notebook/colab_setup.sh --plan --ubuntu 22.04 --arch amd64
bash notebook/colab_setup.sh --plan --ubuntu 24.04 --arch amd64
```

- **175 tests passed in 7.71 s**, including a real INV PNR/DRC/LVS/wire-C/
  ngspice facade regression, public-function delegation, mismatch rejection,
  cache invalidation, platform planning, checksum rejection, safe archive
  links/traversal and notebook generation/compilation. Other streams added
  visualization tests concurrently; the selected suite includes them.
- The complete default notebook executed locally in **46.1 s**, excluding
  installation (the local setup cell correctly does not install). All default
  analog checks passed. The two-trit post-layout maximum sampled error was
  **0.04334 V**. Its exported die was **840 × 2022 µm** for the library state
  used in that run. Logs are `/tmp/tritflow-notebook-final-cold.log` and caches/
  physical artifacts are under `/tmp/tritflow-notebook-final/`.
- A repeat run encountered changed library/code files from parallel work and
  correctly invalidated the old context. Cache hit/option/artifact invalidation
  behavior is separately covered by deterministic unit tests. Report runtime
  figures with the library/PDK state; do not freeze stale files to force a hit.
- Separately exercised the actual one-trit/27-vector and two-trit representative
  adder chains. DRC clean, matched LVS and post-layout band checks passed.
- Downloaded both official Ubuntu 22/24 `.deb` files and verified SHA-256 plus
  Debian package/version/architecture metadata. The PDK commit archive was
  downloaded, hashed and extracted with the setup's own safe extractor. Its
  public pinned LVS deck and models passed local two-trit extraction/LVS and
  post-layout simulation. Installed/local PDK `run.lvs` has a different include
  ordering comment; the pinned public deck was tested independently rather
  than assumed identical. The Ruby engine smoke macro also passed locally.
- No packages installed. No git state mutations. PDK and taped-out source
  checkouts were read only. Only authorized FRONTEND/notebook paths were edited.

**Unverified in Colab:** actual apt dependency resolution, pip installation in
the clean Colab interpreter, its ngspice package's convergence, interactive
notebook display, and total download/install-inclusive cold/warm runtime.
The ten-minute Colab goal remains a validation target, not a measured claim.

Phase 2 follow-up: **complete**. Standard CLI builds, notebook gate graphs,
HTML truth tables, expanded mapping docstrings and their tests are delivered.

## Phase 2 handoff

- `python3 examples/build_all.py` now produces the standard synthesis artifacts
  through the public CLI in `build/adder4/`, `build/full_add/`, `build/mac1/`,
  and `build/mul1/`. Each contains `<top>.json`, `<top>.gate.tv`, `<top>.spice`,
  `<top>.report.json` and `<top>.report.txt`. The actual four builds were run
  successfully in the checkout; all source-to-cell equivalence checks passed.
- The script resolves the repository from its own path, so it works from any
  working directory. `--output-root PATH` permits isolated builds. It replaces
  only synthesis outputs and does not delete other streams' artifacts. Tests
  build twice via subprocesses from outside the repo, compare SHA-256 hashes
  for all 20 artifacts, and check that a PNR marker survives.
- `tritflow/viz/graph.py` provides the following direct-import APIs, without
  changes to any other visualization module:
  - `gate_graph(net, inputs=None, *, title=None) -> plotly.graph_objects.Figure`
  - `color_nets(net, inputs, *, title=None) -> Figure`
  - `net_values(net, inputs) -> dict[str, int]`
  - `truth_table_html(design_or_net, *, max_rows=81) -> str` with `_repr_html_`
- Graphs use longest-path logic levels left-to-right, stable barycenter ordering
  within each level, arrows, and distinct port markers. Gates retain cell-type
  fills. Net coloring uses blue/gray/red for -1/0/+1 with a complete three-value
  legend including ideal voltages. Hover includes cell, source hierarchy,
  output value and pin values. Each signal net gets a trace, including unused
  primary input stubs. Plain loaded GateNetlist objects and arbitrary instance
  order work; plotting does not mutate the source netlist or global renderer.
- The pandas-free truth table accepts source or mapped designs, escapes names,
  labels port direction, and displays every input vector. It rejects excessive
  row counts before evaluation (81 rows by default), rather than truncating.
- Added the backward-compatible `evaluate_netlist(..., return_all=True)` option
  for internal nets, so the graph and notebook analysis reuse the cell evaluator.
  Default results still contain only output ports. Graph coloring requires
  scalar trits for all bit-blasted inputs; batched analysis uses the evaluator.
- Expanded package/API docstrings in HDL and synth explain settled trit values,
  vector ordering, the elaboration pipeline, NAND/NOR fusion, positive min/max
  extra inversion, NANY saturation, TIE mapping, primitive preservation, fanout,
  logic depth, and the limits/modes of equivalence checks for an IC reader.
- New notebook examples are in `examples/README.md`. No new packages installed;
  existing Plotly 7.1.0 is used.

Phase 2 validation:

```sh
python3 examples/build_all.py
python3 -m pytest tests/hdl tests/synth tests/viz -q
```

Result: **157 passed in 1.96 s**. Figure trace colors, levels, full internal-net
coverage, hover data, legends, invalid-input rejection, constants, unused inputs,
HTML escaping, size guards, and arithmetic table contents are covered. A
standalone full-adder Plotly HTML preview was exported to
`/tmp/tritflow-full-add-graph.html`. Browser visual inspection could not run
because no connected browser is available; figure schema/HTML export and
semantic checks passed. This does not block the delivered APIs/builds.

Notebook example:

```python
from tritflow.netlist import GateNetlist
from tritflow.viz.graph import color_nets, truth_table_html

net = GateNetlist.load("build/full_add/full_add.json")
color_nets(net, {"a": 1, "b": 1, "cin": -1}).show()
truth_table_html(net)  # notebook rich HTML; 27 complete input vectors
```

## Done

- Lark parser with a source-located AST and `file:line:column` diagnostics.
  ANSI ports, inherited port types/ranges, vectors, selects, concatenation,
  constants, integer parameters/localparams, named connections/overrides,
  generate loops (including nested loops), and all five gate primitives work.
- Hierarchical elaboration resolves parameters, bit-blasts vectors, flattens
  hierarchy, and retains source hierarchy/location on DAG nodes. It detects
  multiple drivers, undriven used nets/outputs, combinational cycles (including
  dead driven logic), recursive hierarchy, invalid widths/indices, and
  nonterminating generate loops.
- `tritflow.hdl.load`, `loads`, `parse`, `elaborate`, `Design.evaluate` /
  `simulate`, and `truth_table` provide the notebook API. NumPy evaluation
  supports scalar values and broadcast input arrays and validates trits before
  casting. The module docstring distinguishes trits from Verilog four-state logic.
- Ternary-safe constant folding, double-negation elimination, idempotence,
  constant bounds/identities, nany-with-zero simplification, structural hashing,
  dead-code removal, and cost-reducing De Morgan transformations. No Boolean
  complementation/excluded-middle rules. Rewrites are exhaustively tested over
  ternary inputs, with a further deterministic corpus of composed expressions.
- INV/NAND/NOR/NANY/TIE mapping; explicit live primitive instances preserve
  their cell identity. Balanced BUF trees enforce the configurable fanout
  bound (default 4) on every cell input pin, including repeated pins.
- Independent cell-level simulation validates the mapped netlist, including
  its drivers and acyclicity. Synthesis automatically compares the original
  unoptimized source DAG against cells: all 3^n vectors for n<=12, otherwise
  100,000 reproducible random vectors. Input vectors stream in batches.
- Shared GateNetlist JSON, parseable gate-level TritVerilog, top-level SPICE,
  and JSON/text reports (cells, cell-stage depth, exclusive per-hierarchy cell
  counts, maximum fanout, equivalence evidence). CLI is implemented.
- HA, FA, parameterized adder, MUL, MAC with taped-out auxiliary AND/OR
  buffers, minmax, and sign examples. Arithmetic tests use integer references
  independent of gate equations. Every small example is exhaustively checked;
  the parameterized adder is exhausted for N=1..5 and N=6 is checked against
  100,000 additional independent arithmetic vectors.
- [Examples and API guide](../../examples/README.md).

## Decisions

- Explicit primitive instances preserve their authored cells, even with constant
  inputs; unused gates are removed. Expression logic is optimized separately.
  This retains the reference HA/FA gate counts and source hierarchy.
- A relative `` `include "file.tv" `` extension allows examples to share the
  reference HA/FA definitions. Source errors retain included file locations.
  `load` can alternatively take a list of source paths.
- Expression/assignment widths must match exactly; gate primitives are scalar.
  There is no implicit width extension or truncation. Vectors and concatenations
  use declared left-to-right/MSB order; arithmetic weights bit i by 3^i.
  Integer division truncates toward zero and remainder follows that quotient.
- Fanout means the number of connected cell input pins. External output
  capacitance belongs to SIM characterization. Limits below 2 are rejected
  because BUF trees cannot split a load with fanout 1.
- Distinct output aliases use BUF cells to preserve public net names while
  satisfying the one-driver shared contract. Source inputs are not renamed.
- Global signal net names VDD/VMID/VSS are rejected, matching the shared power
  contract and PNR validation. SPICE encodes punctuation and case conflicts
  deterministically and records original names in comments. Its signal order
  is A[, B], Y followed by VDD VMID VSS; the testbench supplies cell/model includes.
- De Morgan transformations are deliberately conservative: negative lattice
  expressions already mapping to NAND/NOR are not expanded. Structural hashing
  retains deterministic source operand order for reproducible artifacts.
- `SynthesizedNetlist` subclasses the unchanged integrator-owned GateNetlist to
  supply `report()`. Only top/ports/instances are serialized as shared JSON.
- CLI `-P N=4` appends `4` to the top and artifact name (`adder4`); `--name`
  overrides this. Python synthesis preserves `design.top`. Materialized truth
  tables default to at most 12 inputs; automatic equivalence streams batches.

## Validation and output examples

Run from the repository root:

```sh
python3 -m pytest tests/hdl tests/synth -q
python3 -m tritflow.synth examples/adder.tv --top adder -P N=4 -o /tmp/tritflow-frontend-adder4/
```

Result: **137 passed in 1.11 s** (Python 3.12; no extra packages installed).
The CLI was exercised directly and in subprocess tests, including diagnostic
exit paths. All example gate files are parsed again and compared to the original
netlists. All JSON files are loaded through the shared GateNetlist loader.
SPICE pin order, rail suffixes, TIE cells and case/punctuation encoding are tested.

| Example | Cells | Depth | Exhaustive input vectors |
|---|---|---:|---:|
| half_add | NANY=5, INV=2 | 6 | 9 |
| full_add | NANY=11, INV=5 | 12 | 27 |
| adder, N=4 | NANY=44, INV=20 | 27 | 19,683 |
| mul1 | NAND=2, NOR=1, INV=1 | 3 | 9 |
| mac1 | NANY=11, INV=9, NAND=2, NOR=1 | 15 | 81 |

The direct CLI run produced `adder4.json`, `adder4.gate.tv`, `adder4.spice`,
`adder4.report.json`, and `adder4.report.txt` under the temporary directory above.
Representative `adder4.report.json` fields:

```json
{
  "top": "adder4",
  "cells": {"INV": 20, "NANY": 44},
  "total_cells": 64,
  "logic_depth": 27,
  "max_fanout": 3,
  "fanout_limit": 4,
  "equivalence": {"passed": true, "mode": "exhaustive", "vectors": 19683, "seed": null}
}
```

Frontend validation establishes logical equivalence. Device behavior, timing,
DRC/LVS and parasitics remain the owning streams' checks.

## In progress

None.

## Blockers

None.

## Interface requests

1. **Integrator — publication:** supply a pinned source archive URL and SHA-256
   containing package, cells/out, examples and notebook files. This checkout
   has no origin remote, so no public package URL was invented. The bootstrap
   accepts `TRITFLOW_ARCHIVE_URL` / `TRITFLOW_ARCHIVE_SHA256` or an uploaded
   checkout at `/content/tritflow`. This is the remaining fresh-Colab bootstrap
   configuration, not a request to edit another stream's code.
2. **CELLS/SIM — sizing chapter:** provide a documented public W/L-sweep
   entrypoint with transfer/error/current results, plus the adopted-size marker.
   The notebook currently reads actual characterized cells and leaves this
   experiment as an explicit TODO.
3. **CELLS/integrator — schematic assets:** supply the exported Xschem SVGs
   planned in the concept for the introductory gate/device comparison.

No interface is missing for the core flow method chain. Shared contracts and
other streams' source files were not edited by FRONTEND.

## Extra dependencies installed

None. Existing lark 1.3.1, numpy 2.4.3 and pytest were used.
