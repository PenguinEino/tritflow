# SHUTTLE status

## 2026-10-23 — scope and decisions

- Read `AGENTS.md`, `docs/concept.md`, `docs/interfaces.md`, both notebook storyboards,
  `briefs/SHUTTLE.md`, `briefs/V3.md`, the v1 chapter 8/9 calls, and the existing chip tooling.
- Work is confined to `notebook/reuse.py`, `notebook/assets/chip/dot4/`, tests for these,
  and this file. No commit/push; no edits to shared views, v3 cells, or narrative.
- The editable default is `dot4_fixed`, with `y = x0 - x1 + x2 + x3` and two output
  trits. The programmable reference is the chapter 3–5 `dot4` with eight inputs.
  Local synthesis proves all 81 / 6561 states, respectively: fixed weights reduce
  **46 cells to 31 (15 fewer, 32.6%)**. Counts include synthesis's fanout treatment.
- The recorded shuttle top will wrap the **programmable 46-cell dot4**, preserving
  the design taught in chapters 3–5. The fixed-weight circuit is the separate
  reuse example. Both definitions will be included with the recorded artifacts.
- Use existing `flow.loads(...).synthesize()`, `Layout` methods, `live.step`,
  `live.LayoutView`, P&R replay, and the GDS viewer; no core flow edits are needed.
- Automatic SPICE policy: all states through four input trits (81 states), then a
  bounded deterministic sample. This is state coverage, not exhaustive transition
  coverage. Expected outputs come directly from the elaborated HDL, independently
  of the mapped gate network. Initial logical guesses are Newton `.nodeset` only.
- The physical top is the existing custom passive TEG/probe allocation. Record
  drawing DRC, strict drawing LVS, MDP, mask DRC, MPW precheck, and DC reserve
  separately from organizer/bond/package/ESD approval (`submission_ready=false`).
- Environment verified: pinned PDK `5d963db9d44e192d37a0489c208bfccf2e2f690c`;
  `NGSPICE_BINARY=~/.local/opt/tritflow-ubuntu-24.04/bin/ngspice` reports ngspice-42.
  KLayout binary and headless Google Chrome are available. No packages installed.

## Completed

- One-call HDL flow, qualified dot4 top and provenance, edited/error-path tests,
  local Jupyter/ngspice-42 execution, and inspected headless Chrome PNGs.

## Blockers

None for the brief's deliverables. The existing adder4 snapshot is untouched.
The custom TEG design still requires the external approvals documented in its
record before a real submission; no upload/submission was performed.

## Interface requests

- None outstanding. V3's integration has adopted `run` and `shuttle_view` using
  the existing notebook module path; the callable contract and snippets follow.

## 2026-10-23 — integration interface

The helper and the programmable-dot4 snapshot are now present. V3 can integrate
the following without waiting for narrative changes from SHUTTLE:

```python
# One separate editable HDL cell (literal source, rather than an import):
reuse_source = """
// Fixed weights: w = (+1, -1, +1, +1).
module dot4_fixed(input trit x0, x1, x2, x3, output trit [1:0] y);
  assign y = x0 - x1 + x2 + x3;
endmodule
"""
```

```python
from reuse import run
reused = run(reuse_source, output_dir=BUILD/"reuse")
```

The return value exposes `.net`, `.layout`, `.extracted`, `.post`, and `.summary`.
It shows live logs, actual-GDS P&R replay, the result/cell-reduction table, the
GDS viewer and a post-layout waveform with conditions. Bad HDL returns `None`
after the existing red `live._box`; physical checks raise on failure. `run()`
without a source uses `need("reuse_source")` to guard the preceding cell.

```python
from reuse import shuttle_view
dot4_chip = shuttle_view()
```

The latter opens the **recorded programmable dot4** and its real pad/pin table.
Assign the return value as above to avoid printing the raw record. It verifies
the GDS SHA-256 before display. Native pinned-deck qualification has passed:
zero drawing DRC items, strict drawing LVS match, zero mask DRC items, unchanged
CO/M1/V1/M2 through MDP, actual organizer precheck pass, 17 pads, DC reserve
26.95%. `submission_ready` remains false for the explicitly listed external
custom TEG/bond/package/ESD approval. The adder4 snapshot is untouched.

Initial local Jupyter execution: the fixed default passed all 81 states (maximum
level error 0.04334 V); a six-input edited min circuit passed its 13-state sample;
malformed HDL produced no error output/traceback. Headless Chrome PNGs were
rendered and inspected. A stimulus-order test caught a multi-input wrap in the
initial zero-rotated Gray order; it is corrected to the reflected 0/−1/+1 Gray
walk, and the final native run/render is being repeated against that sequence.
Current focused pytest result: **18 passed** including a real edited-circuit
DRC/LVS/extraction/ngspice-42 test. Final numbers and commands follow below.

## 2026-10-23 — complete

Both brief items are complete. No core `tritflow/` edits, additional packages,
commits or pushes were needed. All authored files are within this stream's
allowed paths. `git diff --quiet -- notebook/assets/chip/adder4` confirms that
the fallback snapshot is unchanged. Other streams' working files were not edited.

### Reuse implementation and validation

- `notebook/reuse.py` provides `run`, `stimulus_plan`, `summary_view`, and
  `shuttle_view`. The result preserves native circuit/netlist/layout/extraction/
  waveform objects. `summary.json`, `measurements.json`, source, extracted
  device+wire-C SPICE and ngspice's testbench/waveform are written under the
  caller's output directory. A failed edit removes the previous success summary.
- Source parsing/elaboration errors show the **existing** `live._box` and return
  `None`. Native tool failures propagate; unmatched LVS cannot proceed to SPICE;
  analog failures stay `FAIL` in the summary. The electrical oracle evaluates
  the elaborated HDL independently of the mapped cells. Logical initial guesses
  are `.nodeset`, with no `.ic` or `uic` constraint.
- Default state policy is exhaustive through four inputs (81 states), with one
  input changing per step in the reflected 0/−1/+1 Gray walk. Above this, default
  sampling is 27 distinct states, starting with zero, both rail corners,
  alternating signs and single-input excursions, then seeded random fill.
  The emitted summary records the actual vectors, seed, state-space size and
  method. State coverage is explicitly separate from transition coverage.
- The **final real Jupyter execution** used ngspice-42 and the pinned PDK:

  | Circuit | Logic / SPICE states | Cells | DRC / strict LVS | SPICE | Maximum level error | Slowest output settling |
  |---|---:|---:|---|---|---:|---|
  | Fixed dot4 | 81 / 81 | 31 | 0 / match | pass | 0.0433396 V | y[1] 160.279 ns; y[0] 218.613 ns |
  | Edited six-input min | 729 / 13 sampled | 10 | 0 / match | pass | 0.0435575 V | y 45.994 ns |

  Conditions: ±5/0 V rails, nominal PDK models, 27 °C, 100 fF external output
  load, 1 µs holds, 1 ns ramps, 2 ns maximum step, estimated top-net wire C.
  Fixed-dot4 call wall time was **160.625 s**, including 155.4 s in ngspice;
  the edited call was 10.119 s. Maximum settling depends on this stimulus
  sequence; these are not an all-transitions worst-case timing claim.
- Fixed weights are recognized by evaluating all 81 states before showing a
  folding claim. The programmable synthesis reference has 46 cells; this
  fixed expression has 31: **15 removed, 32.6%**. An edited function with the
  same module/port names does not retain the folding claim.
- V3 has chosen the explicit call `run(..., step_s=5e-9,
  exhaustive_limit=27, sample_size=11)` to bound Run-all time. That **exact
  configuration** was separately run through real DRC/LVS/extraction/ngspice-42
  and passes. Its analog coverage is 11/81 states; synthesis still checks all 81.
- Real native tests also pass for a zero-input constant output and for direct
  passthrough with an unused input, including the strict isolated-input proof.

### Recorded programmable-dot4 top

`notebook/assets/chip/dot4/` contains:

- `dot4.tv` / `dot4_fixed.tv`, synthesized `dot4.json`;
- `tr_1um_dot4.gds` (drawing), `.ip62.gds` (mask), `.cir` (LVS reference);
- `signoff.json`, `pad_map.json`, `provenance.json`, and `README.md`;
- `evidence.zip`: native drawing/mask reports and logs, extracted SPICE/LVS
  databases, copied pinned decks/precheck, macro GDS/PNR JSON and chip metadata;
- `build.py` and `verify.py` to reproduce the physical top and local notebook
  checks/renders, respectively;
- inspected headless-Chrome `shuttle.png`, `reuse.png`, `reuse_edited.png`,
  `reuse_error.png`, plus the independent KLayout raster `tr_1um_dot4.png`;
- `reuse_validation.json` with final electrical conditions, stimulus and summaries.

The programmable macro uses **46 cells**, seed 0 / 600 annealing steps, and is
**1692 × 1206 µm** inside the centered **2500 × 2500 µm** frame. There are **17
pads**: 8 inputs, 2 outputs, 3 VDD, 3 VSS and 1 VMID. All supply pads must be
powered, as required by the existing current-reserve calculation. The recorded
top has zero drawing/mask DRC report items (including warnings), strict drawing
LVS match, actual organizer precheck pass, no waivers, and exact zero-area
CO/M1/V1/M2 XOR through MDP. Maximum DC utilization is **0.7305371**, hence
**26.9463% reserve**, meeting the requested 20% reserve.

Drawing GDS SHA-256:
`3eebb7d03dcb7cd82817662b40d2b4f4055fb7fd6742b3f00e5017c6938ae7d4`.
Provenance hashes every published chip artifact, build/helper source, consumed
qualification input and copied PDK rule. The test suite checks these hashes and
the actual native report databases. The view verifies the drawing hash before
display, then shows its real pin/pad table.

The retained `submission_ready=false` is intentional: this is the existing
custom passive TEG allocation, requiring organizer/bond/package/ESD approval.
The inspected MPW flow defines drawing LVS before MDP and **no mask LVS**;
the record says undefined/null rather than claiming a post-MDP LVS check.

### Reproduction and test commands

```bash
export PYTHONDONTWRITEBYTECODE=1
export NGSPICE_BINARY="$HOME/.local/opt/tritflow-ubuntu-24.04/bin/ngspice"
export TR1UM_PDK="$HOME/pdk/TR-1um-pinned"
python3 -B notebook/assets/chip/dot4/build.py --mpw-template "$HOME/TR-1um_MPW_Sanken"
python3 -B notebook/assets/chip/dot4/verify.py
python3 -B -m pytest tests/reuse -q \
  -o cache_dir=tests/reuse/.pytest_cache --basetemp=tests/reuse/.pytest-tmp
```

Final pytest: **22 passed in 28.65 s**. Tests cover bounded/exhaustive stimulus,
independent HDL oracle, actual fixed-weight reduction and changed-function
recognition, malformed/undriven/latch errors, dependency guarding, invalidating
stale success, real edited/constant/unused-input/V3-sampled flows, and archived
physical evidence/hash checks. No errors occurred in the final Jupyter execution.
Chrome rendered the final views at 1200 × 3800 and they were opened for visual
inspection, including the entire waveform and current lane. The executed local
notebook and standalone HTMLs remain in ignored `.work/validation/`; temporary
native/test work is confined to ignored subdirectories of this stream's paths.

No remaining SHUTTLE work or interface requests.
