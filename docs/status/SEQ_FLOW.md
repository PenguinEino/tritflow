# SEQ_FLOW — sequential TritVerilog

Complete: HDL, state simulation/equivalence, final TDFF extension, real P&R,
DRC/LVS, extracted clocked SPICE, timing/current characterization and regression.
No implementation work or blockers remain.
Work is confined to `~/code-a-chip-seq`. No commit/push, notebook edits, reference-tree
writes, packages, server access or publication. The supplied untracked brief is preserved.

## Language and clock rules

The existing parser/elaborator accepts `always @(posedge clk)` and nonblocking
`<=` on scalar/vector `reg trit`, with nested `begin`, `if`/`else`, and exact
`case`. Existing arithmetic, shifts, expressions, parameters, generate loops,
structural hierarchy and combinational blocks remain available together.

Every RHS and branch condition reads old state. All Q values update together;
the last executed nonblocking assignment to a bit wins. A missing clocked
assignment means hold. Synchronous reset and enables are ordinary next-state
logic; no special reset cell is invented. Incomplete combinational assignments
remain latch errors. `reg trit` may still be used in an existing fully assigned
combinational block.

Only one clock is supported, connected by wiring/hierarchy directly to a scalar
top-level input. Settled clock values are -1/+1 (-5/+5 V); only -1→+1 captures.
Zero is invalid as a settled clock level. Clocked blocking assignments, negedge,
multiple clocks/events, asynchronous reset, derived clocks, clock-as-data and
latches produce file:line:column errors. General unsupported HDL constructs from
HDL_VERILOG remain unsupported. This is not an IEEE Verilog frontend.

There is no hardware initialization or implicit reset. Logic simulation requires
an explicit initial state. `tritflow.seq.simulator.Simulator.drive` detects real
clock-level changes; `transition`/`cycles` represent rising-edge captures.

```python
from tritflow import flow
from tritflow.seq.simulator import Simulator
circuit = flow.load("examples/counter2.tv")
net = circuit.synthesize()
sim = Simulator(net, initial={"n[1]": 0, "n[0]": 0})
sim.drive({"clk": 1})   # n = +1
sim.drive({"clk": -1})  # hold
layout = net.place_and_route(output_dir="build/my_counter")
assert layout.drc()["clean"] and layout.lvs()["matched"]
post = layout.extract().simulate([{}]*12,
    initial={"n[1]": 0, "n[0]": 0}, workdir="build/my_counter/spice")
assert post["measurements"]["passed"]
```

## Synthesis and equivalence

`tritflow.seq` cuts feedback at every Q and reuses the existing combinational
mapper for D functions and outputs. It then reconnects one TDFF per written
register trit. GateNetlist JSON schema is unchanged; instances explicitly carry
`TDFF` with `D/CLK/Q`. Q net names equal bit-blasted RTL register names, including
hierarchy. All state/D logic is retained, including non-public register bits.

Next-state/output functions are checked exhaustively through 12 total data and
state trits (clock excluded), otherwise with the existing seeded 100,000-vector
sample. A separate seeded 256-cycle RTL/cell co-simulation checks simultaneous
state updates and outputs. Independent Python shift/radix integer oracles check
each example sequence; they do not evaluate the IR or mapped cells. Explicit
cell netlist validation and writer round trips are tested. The clock is an
ordinary routed net; no CTS or clock buffering is silently added. Data fanout
buffering retains the existing four-load default.

## Final cell delivery and immutable extension

The final SEQ_CIRCUIT delivery became available during this work and was integrated.
`cells/out_seq/` is an opt-in extension with its own manifest; the original
`cells/out/library.json` and all original cells remain byte-identical.
`tritflow.seq.library.import_tdff` is the single delivery adapter. It checks the
final summary/artifact hashes and snapshots read-only source files. Later flow
runs consume the snapshot, not a live reference checkout. No provisional circuit
is used in the final flow.

TDFF is 1260 × 132 um, with 16 PMOS, 16 NMOS and 16 F_RR devices. Its pins are
D CLK Q VDD VMID VSS. It uses master/slave cross-coupled ternary INV storage,
CMOS transmission gates, clock dead-band controls and an input buffer. VMID is
an unloaded physical pass-through. The full-height free M2 columns are only
x=3 and 1257 um. Source and pin/obstruction abstracts, GDS, schematic SPICE,
extracted SPICE, qualification reports, final summary and provenance are included.

Pinned PDK: `5d963db9d44e192d37a0489c208bfccf2e2f690c` at
`~/pdk/TR-1um-pinned`. A fresh independent official drawing DRC and strict
schematic/device LVS passed on the copied cell. Evidence:
`build/seq_qualified/cell/qualification.json` and its KLayout logs/database.
This is drawing DRC/LVS qualification, not a full-chip fabrication claim.
The delivery's standalone mask warnings for external floating inputs remain
explicit in its copied reports; no DRC waiver was added.

The delivery characterizes setup/hold at 10/100 fF: at 1 ns clock slew,
setup=14.5 ns and conservative hold=0 ns; at 50 ns slew, setup=30 ns and
hold=0 ns. Nominal extracted settling clock-to-Q is 16.15/17.90 ns for
10/100 fF at 1 ns slew, and 31.25/32.75 ns at 50 ns slew. These are 27 C
nominal results with 0.5 ns search resolution, not PVT constraints.
`tritflow.seq.characterize` independently checks six extracted-device transitions
and searches setup/hold, plus all stored Q/D combinations in both clock phases.
The independent extracted-device results are complete:

| Output load | Setup (ns) | Conservative hold (ns) | Worst settled clock-to-Q (ns) |
|---|---:|---:|---:|
| 10 fF | 14.0 | 0.0 | 15.9473 |
| 100 fF | 14.0 | 0.0 | 17.7688 |

Both searches bracket setup between 13.6719 and 13.9648 ns and hold between
-3.6133 and -3.3203 ns; nonnegative conservative constraints are rounded to
0.5 ns. The independent setup criterion limits settled-band clock-to-Q growth
to max(10%, 0.5 ns); the delivered 14.5-ns constraint instead limits midpoint
delay growth to max(10%, 0.2 ns). These different definitions explain the small
difference; neither is a PVT timing model. Every one of 18 Q/D/clock-phase
static cases passed. Worst current is 0.003257134722 A (32.57 mW across 10 V).
All per-transition waveforms, decks and search trials are retained under
`build/seq_flow/characterize/`; final machine data is
`cells/out_seq/TDFF/TDFF.char.json`.

The existing public runner pins **Ubuntu ngspice-42**, despite the older
interfaces document mentioning 46. Its resolver/identity code was used unchanged.
The published binary/runtime identities are recorded in characterization and
collected experiment summaries. No simulator was installed or substituted.

## Supply geometry and P&R

The final buffered TDFF draws **3.257 mA** at the middle trit, above the 1.6 mA
reserved capacity of the original 4 um rail with two end feeds. No current limit
was relaxed. Sequential P&R opts into real M1 rail reinforcement into adjacent
channels: VSS [-8,4] and VDD [124,136] um (12 um each), VMID unchanged [6,10].
The accumulator uses the explicit 18 um option: VSS [-14,4], VDD [124,142].
Channel tracks that cannot clear the widened rails are removed. Supply banks
start at 32 um per trunk and have real labeled pads at both top and bottom die
boundaries. The ordinary solved rail/via-current check must meet the existing
20% reserve before routing; geometric connectivity, routing DRC and official
PDK DRC/LVS follow. Default combinational power geometry is unchanged.

Early trials with narrow banks/top-only feeds failed the solved per-cut current
reserve for the accumulator. They were rejected. The final two-ended trunk
geometry fixes the supply distribution rather than suppressing that check.
Delivery currents are converted to the existing raw SPICE source-current sign
(negative VDD); final qualification uses the corrected signed envelope.
The simplified legacy IR-drop summary remains conservative/top-fed; the actual
power `dc_current_check` uses all drawn top/bottom pads and via/rail centerlines.
Internal-cell/contact/transient EM and calibrated signal-wire R are not qualified.

Final physical evidence is under `build/seq_qualified/<example>/`:

| Example | Cells | Total | Exhaustive data+state vectors | Die (um) | Max DC utilization | DRC/LVS |
|---|---|---:|---:|---|---:|---|
| shift3 | 3 TDFF, 3 BUF | 6 | 81 | 1512 × 1302 | 0.5834 | zero / matched |
| counter2 | 2 TDFF, 8 NANY, 4 INV, 1 NOR, 2 ties | 17 | 9 | 1500 × 1230 | 0.6020 | zero / matched |
| accumulator2 | 2 TDFF, 19 NANY, 14 INV, 3 NAND, 2 NOR, 2 ties | 42 | 243 | 1632 × 1374 | 0.6934 | zero / matched |

A fresh power-network reassessment with the completed independent characterization
also meets the reserve for all three saved layouts; see
`build/seq_qualified/power_recheck.json`.

The counter adds one and wraps modulo nine through -4…+4. The additional small
accumulator has synchronous reset and wraps a two-trit sum. It is an extra
example; the optional large nine-operation ALU feeding a register was not added.

## Clocked extracted SPICE

New `tritflow.seq.spice` builds device-level clocked decks and calls the existing
public ngspice runner. Strict LVS is mandatory before post-layout extraction.
Actual-GDS top-net metal C is appended through the existing extraction API.
Every Q is observed through LVS logical/physical mappings, even when it is not
an output port. The explicit initial state provides Newton `.nodeset` guesses
for mapped nets, real TDFF latch nodes and published gate divider nodes; no .ic/UIC, behavioral storage or
forcing data source replaces the memory circuit. Initial Q values are checked
before the first edge, then every register and public output is sampled at 90%
of each cycle, before the next rising edge, after falling clock/data changes.
All tests require ideal ±0.5 V. The pre-layout deck builder uses the delivered
schematic hierarchy under the same interface.

Final runs use 12 cycles per example, 1 ns clock/data edges, 10 fF per public
output, 2 ns maximum timestep, 27 C, and tested periods 1000/500/250/125 ns.
The final sweeps also test 62.5 and 31.25 ns (16/32 MHz). They report
clock fanout, estimated wire C and maximum observed passing tested frequency. A passing frequency applies to this sequence/load and is not a PVT,
minimum-pulse-width, skew, clock-driver or calibrated-PEX fmax guarantee.

| Example | Passing tested clocks (MHz) | Failing tested clocks (MHz) | Max observed pass | Largest sampled error on passing clocks | Clock fanout / estimated metal C |
|---|---|---|---:|---:|---|
| shift3 | 1, 2, 4, 8, 16 | 32 | 16 MHz | 0.035660 V | 3 / 206.85 fF |
| counter2 | 1, 2, 4, 8 | 16, 32 | 8 MHz | 0.036988 V | 2 / 120.50 fF |
| accumulator2 | 1, 2 | 4, 8, 16, 32 | 2 MHz | 0.035737 V | 2 / 243.44 fF |

The accumulator's original strict Gear/reltol=1e-5 decks encountered simulator
convergence failures (initially at the first edge, then at the eighth edge after
better Newton guesses). Those attempts are not passes. The completed accumulator
qualification uses `.options rshunt=1e12`, the existing combinational bench's
normal convergence option, with default trapezoidal integration/tolerances.
The 1-TΩ numerical shunts are disclosed; no state/output is forced. Required
shift/counter results use Gear2, reltol=1e-5, abstol=1e-13. Solver options and actual
waveforms are preserved. Faster completed trials that miss the ±0.5 V band remain
explicit FAIL results rather than being hidden as simulator errors.

`examples.sequential_report` independently re-reads every saved waveform,
rechecks sampled voltages against each Python oracle, and collects all six
clocks even when run in separate invocations. It records deck/waveform/GDS/netlist
hashes, simulator identity, clock capacitance and passing/failing trials in
`build/seq_qualified/summary.json` and each example's summary.

Recorded local wall times (host load affects them):

| Example | Original P&R incl drawing DRC (s) | Latest separate strict LVS (s) | Six SPICE trials combined (s, approx) |
|---|---:|---:|---:|
| shift3 | 3.143 | 2.468 | 640.9 |
| counter2 | 4.094 | 1.366 | 614.1 |
| accumulator2 | 4.444 | 0.893 | 197.3 |

Older batch wall times use deck/log timestamps; new runs record a monotonic timer.
This is local evidence, not a Colab runtime claim. Initial exploratory layouts and
failed numerical trials remain under `build/seq_flow` for diagnosis; only
`build/seq_qualified` is the final example evidence.

## Reproduce / tests

```sh
TR1UM_PDK=~/pdk/TR-1um-pinned python3 -m examples.sequential_check --output-root build/seq_qualified
# Split long runs while preserving geometry:
TR1UM_PDK=~/pdk/TR-1um-pinned python3 -m examples.sequential_check --physical-only --output-root build/seq_qualified
TR1UM_PDK=~/pdk/TR-1um-pinned python3 -m examples.sequential_check --resume --output-root build/seq_qualified
python3 -m examples.sequential_report --root build/seq_qualified
TR1UM_PDK=~/pdk/TR-1um-pinned python3 -m tritflow.seq.characterize
TR1UM_PDK=~/pdk/TR-1um-pinned python3 -m pytest tests -q
```

Required full command completed: **768 passed, 2 skipped in 959.86 s**.
The two skips are the existing optional STA integration tests missing the
`build/adder_scaling/adder6/adder6.json` artifact. Full log:
`build/seq_flow/tests_all.log`. Two final tests were then added: an actual
single-register extracted ngspice transient and narrow-VMID packing despite
widened VDD/VSS. Final focused command:

```sh
TR1UM_PDK=~/pdk/TR-1um-pinned python3 -m pytest tests/seq tests/synth/test_flow_api.py tests/pnr/test_constraints.py -q
```

**36 passed in 19.68 s**, including the actual extracted ngspice write and both
post-full-suite tests. The final sequential language/state-only check also
passed all 18 cases after simplifying the clock-free equivalence cut.
`build/seq_flow/tests_final.log` contains the focused run. `git diff --check`
and Python compilation passed.

New sequential tests cover old-state nonblocking semantics,
independent arithmetic, hold/reset/case, edge-level simulation, hierarchy,
diagnostics, corrupted register connections, real cell and routed DRC/LVS, and
clock-deck initialization/sample rules, an actual three-value post-layout write,
and preservation of VMID current limits during floorplan selection.

## Protected paths and interface requests

A pre-edit hash inventory covers 2227 files: every original `cells/out` file,
the template, and every Python file forbidden by the brief. The final
comparison reports **zero changed files** (`build/seq_qualified/protected_audit.json`). No edits to `docs/interfaces.md`.

Additive integration changes are limited to HDL parser/elaborator dispatch,
synthesis/writer dispatch, flow wrapper selection, PNR state-boundary ordering,
and optional reinforced sequential power geometry. All sequential machinery is
in new `tritflow/seq/` modules. The integrator should document TDFF as an optional
extension and the `D CLK Q VDD VMID VSS` interface after review. The original
GateNetlist JSON and base cell manifest stay unchanged.
