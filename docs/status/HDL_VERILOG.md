# HDL_VERILOG status

Updated: 2026-10-20. Round 3 complete: cheaper proved selection, the 64-cell
shuttle ALU, six physical examples, full-chip signoff, post-layout SPICE, and
required plus remaining regression suites passed. No commits, pushes, tags, package installs,
notebook edits, or changes to other streams' implementations.

## Supported language

A trit has values -1 / 0 / +1, corresponding to -5 / 0 / +5 V. It is distinct
from Verilog's x/z states. Numerically, all three are ordinary balanced-ternary
digits; as a condition they mean false / unknown / true.

| Student writes | Meaning / support |
|---|---|
| `module`, named instances, `parameter`, `localparam`, `generate for` | Existing hierarchy, constants and static elaboration remain supported |
| `input trit`, `output trit`, `wire trit` | Scalar or packed vector signals |
| `reg trit`, `output reg trit` | Combinational signal declarations; no storage implied |
| `assign {cout, sum} = a + b + cin;` | Context-sized integer arithmetic with carry |
| `+`, binary `-`, unary `-`, `*` | Balanced-ternary integer addition, subtraction, digit negation, multiplication |
| `~`, `&`, `\|`, `nany(a,b)` | Elementwise negate, min, max, negative saturated sum |
| `== != < <= > >=` | Integer comparisons: +1 true, -1 false |
| `!`, `&&`, `\|\|` | Single-trit Kleene negate, min, max |
| `c ? x : y` | Single-trit condition, vector data, Kleene consensus at c=0 |
| `always @(*)`, `always @*` | Combinational blocks with blocking `=` assignments |
| `begin ... end`, `if / else if / else` | Ordered assignments and conditional branches |
| `case (expr) ... endcase` | Exact matching, multiple labels, optional default; all trits including 0 are matched literally |
| `4'tT01T`, decimal integers, parameter names | Sized balanced literals and integer constants in expressions |
| Concatenation, fixed bit/part selects | MSB-first concatenation; indices remain compile-time integers |
| `inv`, `nand`, `nor`, `nany`, `buf` instances | Existing explicit cell identity and instance names are preserved |

## Width and condition rules

For `trit [N-1:0] a`, the integer is sum(a[i] * 3**i). Expression vectors are
stored MSB first, and the rightmost declared digit has weight one (including
ascending ranges or ranges whose right bound is not zero).

The assignment's full target width supplies context, including all members of
a target concatenation. Arithmetic and bitwise operations evaluate at the larger
of that context and their natural operand widths. Operands extend with **zero**
trits, including negative numbers. Assignment truncation discards high trits,
equivalent to reduction modulo 3**width into the balanced representable range.
Unary `-` and `~` negate each trit; there is no carry chain for negation.

Concatenation members determine their own widths before concatenating. Comparison
operands determine their own widths, extend to the larger operand width and
return one trit; a one-trit comparison target never truncates its operands.
Decimal literals have their shortest balanced width, with zero occupying one
trit. Verilog precedence and left associativity apply, including comparison,
bitwise and logical precedence. Conditional `?:` associates to the right.
Existing primitive and module-port connections retain strict connection widths.

For `c ? x : y`, c=+1 chooses x and c=-1 chooses y. At c=0, every result digit
is the input digit if x and y agree there, otherwise 0. This is checked for all
scalar combinations and all 243 combinations of a condition and two two-trit
operands. The truth value of a comparison is always +/-1, including comparisons
involving zero. Procedural `if` executes its then arm only at +1; zero takes the
else arm, matching Verilog's treatment of an unknown condition.

Blocking assignments see preceding assignments in the same block. Branches
merge current values. Every written bit must have a value on every path; reads
of a block-written bit before a blocking assignment are errors. A prior default
assignment permits partial updates in branches. Full case enumeration needs no
default. The analysis is conservative about separate, correlated if statements;
use an explicit default or an if/else chain. Diagnostics include file:line:column.

## Synthesis

| Construct | Circuit implementation |
|---|---|
| Add / subtract | LSB-first ripple carry; reference HA (5 NANY + 2 INV) and FA (11 NANY + 5 INV); subtraction negates the second operand |
| `(a+b)+c` | Three-operand slice fusion; the scalar full-adder idiom produces the reference FA cell count |
| Constants in arithmetic | Zero operands bypass adder slices; fixed +/-1 carry uses max(x,0) / min(x,0); constant digit products become zero, wire or INV |
| Multiply | Array of reference one-trit MUL networks (2 NAND + 1 NOR + 1 INV), shifted and summed with ripple adders; high products outside the context are omitted |
| Relational comparisons | Saturated digit differences; a nonzero high-digit sign dominates lower digits, without integer overflow |
| Equality / case matching | Per-digit equality, with unary literal detectors for fixed digits, combined using min |
| `?:` | Ternary Shannon MUX3; the middle arm is median(x,y,0), implementing exact Kleene consensus |
| Procedural if/case | SSA current-value maps and crisp +/-1 predicate selects; no latch nodes |
| Arbitrary truth tables | Exact case tables are networks of equality detectors and predicate selects; arbitrary finite tables therefore have a library implementation |
| General unary functions | Deterministic closure search over INV/NAND/NOR/NANY and all three ties reaches all 27 functions; crisp detectors supply MUX3 |

The existing constant folding, CSE, dead-logic removal, ternary identities and
fanout buffering follow lowering. Identical expressions/cofactors share through
CSE; this is not a global minimum-cell mapper. The closure search uses a tree
cost and does not claim minimum networks. No Boolean complement identities are
applied to the unknown trit.

Source IR retains arithmetic and selection operations. Its simulator uses
independent integer arithmetic and table rules, including Python integers for
wide values. Synthesis compares this source result with mapped-cell simulation,
exhaustively through 12 input trits, then with the existing 100,000-vector seeded
sample. `optimize_logic=False` still lowers the new operators. Gate TritVerilog
and SPICE writers consume the unchanged GateNetlist format.

## Examples and physical evidence

All six examples synthesized with exhaustive source/cell equivalence, routed via
`tritflow.flow`, passed the official drawing DRC with zero violations and matched
strict device/port LVS. The physical library is real, not a mock.

PDK: `/home/ishi-kai/pdk/TR-1um-pinned`, commit
`5d963db9d44e192d37a0489c208bfccf2e2f690c`. Local KLayout and ngspice were used;
no remote server was needed.

| Example | Cells (including ties / fanout BUFs) | Total | Exhaustive vectors | DRC / LVS |
|---|---|---:|---:|---|
| `full_add_rtl` | 11 NANY, 5 INV | 16 | 27 | clean / matched |
| Handwritten `full_add` | 11 NANY, 5 INV | 16 | 27 | Existing reference |
| `adder4_rtl` | 38 NANY, 17 INV | 55 | 6,561 | clean / matched |
| `alu_rtl` | 22 NANY, 44 INV, 27 NAND, 13 NOR, 12 BUF, 3 ties | 121 | 81 | clean / matched |
| `case_table` | 8 NANY, 12 INV, 6 NAND, 3 NOR, 3 ties | 32 | 9 | clean / matched |
| `comparator_rtl` | 12 NANY, 8 INV, 3 NAND, 2 NOR, 2 ties | 27 | 81 | clean / matched |
| `mux_rtl` | 6 NANY, 11 INV, 6 NAND, 5 NOR, 3 BUF, 3 ties | 34 | 27 | clean / matched |

The ALU uses scalar data operands and a two-trit result. Five operations require
more than three opcodes, so its **two-trit opcode** encodes -2 add, -1 subtract,
0 negate, +1 min, +2 max; other codes return zero. The four-trit adder has an
explicit fifth output digit for carry and no carry input. Its first slice is a
half adder, followed by three full adders (7 + 3*16 = 55 cells).

Reproduce all six physical checks:

```sh
TR1UM_PDK=~/pdk/TR-1um-pinned python3 -m examples.rtl_check
```

Evidence: `build/hdl_verilog/summary.json`, and per-example GDS, gate JSON,
gate TritVerilog, SPICE, synthesis reports, DRC reports/logs and LVS extraction
reports under `build/hdl_verilog/<example>/`. A final comparison confirmed all six
saved physical references still equal current synthesis JSON.

## Tests

- `tests/synth/fixtures/legacy_netlists.json` captures all 11 original `.tv`
  examples **before** edits. Regression compares their full netlist JSON,
  including instance names, ports, hierarchy and pins, and cell counts. All match.
- Independent integer/table references cover arithmetic width/truncation and
  extension, all comparisons, multiplication, fused vector sums, logical
  precedence, blocking semantics, case coverage and all six example functions.
- Every one-input truth table is tested, plus 32 seeded two-input and eight
  three-input arbitrary tables. Closure networks separately test all 27 unary
  functions. New examples also verify with optimization disabled and after
  gate-writer round trips.
- Tests check file:line:column for division/remainder, sequential syntax,
  nonblocking assignments, invalid conditions, duplicate/nonconstant labels,
  incomplete assignments and reads before writes.
- Old tests that expected newly supported syntax or resizing to fail were
  replaced by valid acceptance/semantics tests and current unsupported cases.
- Required final suite: **306 passed in 96.22 s**.
- Remaining test directories: **392 passed, 2 skipped in 484.86 s**. Together,
  **698 tests passed, 2 skipped**, with no failures. The two skips are STA
  integration checks whose optional `build/adder_scaling/adder6/adder6.json`
  artifact is absent (`test_real_default_midpoint_report_and_source_pattern`
  and `test_real_published_cells_and_six_trit_adder`).
- Additional regressions preserve explicit primitive functional helpers in mixed
  RTL/structural designs, and prevent adder fusion from misreading the width of
  a truncated intermediate signal. `git diff --check` passed.

Commands:

```sh
TR1UM_PDK=~/pdk/TR-1um-pinned python3 -m pytest tests/hdl tests/synth tests/pnr -q
TR1UM_PDK=~/pdk/TR-1um-pinned python3 -m pytest tests/ -q --ignore=tests/hdl --ignore=tests/synth --ignore=tests/pnr
```

## Remaining unsupported / decisions

Signal `/` and `%`, sequential/clocked logic, nonblocking assignments, latches,
x/z, procedural loops, dynamic selects, functions/tasks and wildcard cases are
not supported. Integer parameter/index `/` and `%` retain their existing rules.
This remains a combinational TritVerilog subset, not an IEEE Verilog frontend.

No changes were made to notebook files. The notebook's `broken` example using
signal `+` will now succeed and must be replaced by the integrator (for example,
signal `/` or an incomplete combinational assignment). This is an integration
note, not a remaining implementation blocker.

## In progress / blockers / interface requests

No work in progress, implementation blockers or shared-interface changes
requested. The integrator should update the notebook's obsolete rejected
`+` example and may revise the older HDL limitations in `docs/concept.md`.

## Round 2 — shifts and nine-operation ALU (2026-10-20)

Round 2 is complete: shifts, showcase ALU, all regression suites, fresh physical
qualification of all six RTL examples, and post-layout ALU SPICE. No work in
progress, blockers or new interface requests remain.

### Language additions and sizing decisions

| Student writes | Meaning / circuit |
|---|---|
| `a << k`, `a <<< k` | Shift left k balanced digits, insert low zeros; multiply by 3**k and truncate |
| `a >> k`, `a >>> k` | Drop k low digits, insert high zeros; nearest-integer division by 3**k |
| Negative amount | Reverse direction: `a << -k` equals `a >> k` |
| Constant amount | Pure digit wiring; existing TIE/BUF output drivers remain |
| Signal amount | Self-sized signed balanced integer; three-way selection of wired results |

The data width is max(assignment context, natural width of the **left** operand).
The shift amount never changes that width and never inherits the assignment
context. Assignment truncation still occurs after evaluation, so a narrower
target first shifts at the left operand's natural width, then discards high
digits. Concatenation members remain self determined. Arithmetic in a signal
amount follows the existing self-sized rules; decimal/parameter-only integer
amount expressions evaluate exactly (`1+1` means 2). Sized trit amounts follow
their declared width. Parameter/index/generate expressions also accept ternary
shifts, with the same integer meaning and no signal-width truncation.

For right shifts, the discarded balanced remainder is within
[-(3**k-1)/2, +(3**k-1)/2], so the retained integer is the unique nearest integer
to a/3**k. There are no exact half ties since 3**k is odd. In particular,
`-2 >> 1` is -1, while `-1 >> 1` is 0. Either-direction shifts with magnitude
at least the evaluated data width return zero. All four spellings associate
left to right, with Verilog precedence: addition, then shift, then comparison.

Source IR records the two operand widths separately; its simulator uses Python
integer multiplication and nearest division, independently of the gate mapper.
The mapper applies ternary Shannon expansion to the **whole signed amount**,
sharing cofactors and pruning entire overshift ranges to zero. It must not
cascade digit-controlled opposite shifts: +2 is +3-1, and shifting left three
then right one can lose digits that a shift left two must retain. Constant
amounts reduce directly to the original data nodes/zero, even with optimization
disabled. Boundary buffers and zero ties are identical to authored wiring.

Existing width, arithmetic, Kleene `?:`, procedural-if and case rules from
Round 1 remain unchanged. Signal `/` and `%` and the other previously listed
unsupported constructs remain unsupported.

### Showcase ALU and independent reference

`examples/alu.tv` replaces `alu_rtl.tv`; its module is `alu`. Ports are
two-trit a, b and op (each -4..+4), and four-trit r (-40..+40). All nine cases
assign the entire result in plain `always @*` / `case` code; no default or latch
is needed because every opcode is covered.

| op | Integer code | r |
|---|---:|---|
| `2'tTT` | -4 | a+b |
| `2'tT0` | -3 | a-b |
| `2'tT1` | -2 | -a |
| `2't0T` | -1 | digit-wise min(a,b) |
| `2't00` | 0 | digit-wise max(a,b) |
| `2't01` | +1 | a << 1 = 3a |
| `2't1T` | +2 | a >> 1 = round(a/3) |
| `2't10` | +3 | sign(a-b), -1/0/+1 |
| `2't11` | +4 | a*b |

Digit min/max sit alongside integer operations intentionally. They differ from
integer min/max: -2 (`T1`) and +2 (`1T`) produce -4 (`TT`) and +4 (`11`).
The compare result is a sign trit, unlike a relational operator's +/-1 truth
result. Four output trits preserve every product, including +/-16; reaching
the high digit requires products of magnitude at least 14.

`examples/alu_reference.py` predicts outputs using independent integer operations
and balanced-radix encoding, without IR or mapped gates. All 729 input states
match both source and cell simulation. Synthesis uses 423 cells: 72 NANY,
152 INV, 86 NAND, 49 NOR, 61 BUF, and one each TIEN/TIEP/TIEZ. Max fanout is 4;
logic depth is 66. The reference full adder remains 11 NANY + 5 INV = 16 cells,
identical to `full_add_rtl`.

### Physical decisions and reproducibility

The default near-square plan (22 rows, 8 spans) failed the solved power envelope:
maximum TC utilization 1.373 of the published per-cut limit. Automatic current
density tightening eventually found no legal floorplan. No PNR/cell/extraction
code or safety check was modified. Public API controls suffice: the runner uses
32 rows, seed 0, 600 annealing steps and `current_density_a_per_um=0.000135` for
the ALU, retaining the default 20% current reserve. Narrow automatic channels
then exhausted four routing trials (12 through 18 tracks). Starting with 24
channel tracks and two rip-up passes per floorplan succeeds on the first
floorplan, after one rip-up. The final solved maximum utilization is 0.7682,
below the 0.8 reserve threshold. Other examples retain default floorplanning.

The ALU has **4440 x 9366 um** die dimensions (41.585 mm2), zero official drawing
DRC violations and strict matched device/port LVS. Successful wall times:

| Stage | Local wall time (s) |
|---|---:|
| Source loading, synthesis and exhaustive equivalence | 0.0138 |
| P&R, including physical connectivity/routing checks | 112.38 |
| Official drawing DRC | 7.62 |
| Strict device/port LVS | 1.74 |
| Matched-device/wire-C extraction and testbench setup | 1.60 |
| SPICE + measurements, 2 ns maximum step | 379.21 |

The five retained RTL examples also passed
fresh P&R, official drawing DRC and strict LVS. Their cell counts remain
16 / 55 / 32 / 27 / 34 for full_add_rtl / adder4_rtl / case_table /
comparator_rtl / mux_rtl respectively.

The runner times P&R with `run_pdk_drc=False`, then explicitly runs official
drawing DRC and strict LVS as separate timed stages and asserts both results.
It extracts matched devices plus estimated geometry-based lumped wire C, then
simulates representative transitions with an independent integer oracle,
10 fF/output, 1 us hold, 1 ns edges and 2 ns maximum step. Initial internal
`.nodeset` guesses use the existing SIM/LVS helper; they do not constrain the
transient solution. The sequence covers all nine opcodes and -1/0/+1 on each
of the four outputs; assertions check coverage and every measured level/settling
window against ideal +/-0.5 V bands.

The 2 ns post-layout run passed **all 10 vectors and all 40 output checks**,
with no unsettled windows. Maximum absolute level error was **0.03897 V** and
the worst measured settling time was **455.98 ns**. Per-output maximum settling
times were 447.06 / 432.00 / 455.98 / 421.13 ns for r[3:0]. These are selected
transitions with 10 fF output loads, not an exhaustive analog delay claim.
P&R + DRC + LVS + extraction + this SPICE sequence took about 8.38 minutes
locally. Applying the brief's approximate 3-5x Colab factor gives about
25-42 minutes; the full showcase should not be presented as a ten-minute Colab
exercise. Small examples remain fast. No Colab run or remote server was used.

An optional 10 ns maximum-step comparison used an otherwise byte-identical
testbench. It was deliberately stopped after exceeding the successful 2 ns
run's wall time (over 6.8 minutes); it produced no completed qualification
result and is not counted as a pass or a simulator failure. Increasing the
maximum step did not establish a runtime benefit. The final runner retains
the fully qualified **2 ns default**; `alu_spice(..., step_s=...)` permits
explicit resolution studies. The checked 2 ns result, GDS and waveforms were
preserved. The initial SPICE launcher also needed its LVS argument corrected
from a report dictionary to the `.lvsdb` pathname; fresh strict LVS on the
identical saved GDS/netlist preceded the successful resumed simulation.

```sh
TR1UM_PDK=~/pdk/TR-1um-pinned python3 -m examples.rtl_check
# Just the showcase, or an isolated output directory:
TR1UM_PDK=~/pdk/TR-1um-pinned python3 -m examples.rtl_check --names alu
```

The runner's default root is `build/hdl_verilog_round2`. Evidence for this run
is in `build/hdl_verilog_round2_wide/summary.json` (ALU) and
`build/hdl_verilog_round2/regression/summary.json` (five retained examples).
Reproduce the successful ALU configuration and artifact location with:

```sh
TR1UM_PDK=~/pdk/TR-1um-pinned python3 -m examples.rtl_check --names alu --output-root build/hdl_verilog_round2_wide
```

ALU artifacts include `.gds`, `.pnr.json`, gate JSON/TritVerilog/SPICE, DRC/LVS
reports, `alu.postlayout.spice`, `alu.capacitance.json`,
`alu.measurements.json`, and `spice/{tb.spice,ngspice.log,waveform.txt}`.
PDK remains public pinned commit `5d963db9d44e192d37a0489c208bfccf2e2f690c`.

### Round 2 regression evidence

- Required command: `python3 -m pytest tests/hdl tests/synth tests/pnr -q`:
  **354 passed in 88.01 s**.
- Remaining directories, using the Round 1 command with three `--ignore` flags:
  **392 passed, 2 skipped in 485.25 s**. The same two optional STA artifact
  checks were skipped. Combined: **746 passed, 2 skipped, no failures**.
- A final focused rerun of both new shift test modules: **47 passed in 0.77 s**.
- Shift tests exhaust fixed amounts (including negative, zero and overshift),
  all four spellings, variable signed amounts, narrow/wide output contexts,
  self-sized comparisons/concatenations, precedence, parameter/generate use,
  Python-integer width beyond int64, diagnostics, no-optimize and writer round
  trips. A 42-trit variable amount checks that overshift pruning avoids
  enumerating its astronomical input space.
- All 11 original examples still match their complete legacy netlist JSON and
  cell counts. `round1_netlists.json` additionally preserves the five retained
  first-round RTL examples, copied from their **pre-existing physical artifacts**
  and checked against current synthesis before saving. The obsolete scalar ALU
  is the only deliberately replaced example.
- No packages installed; no remote server, notebook edits, other streams' code
  changes, sign-in, publication or git-state mutations. The pre-existing change
  to `briefs/HDL_VERILOG.md` belongs to the user and is left intact.
- `git diff --check` passed. Round 1's notebook-integration notes still apply;
  no references to the removed `alu_rtl` remain in executable code or notebook
  sources. Historical first-round status evidence is retained above.

## Round 3 — shared selection and a shuttle-size ALU (2026-10-20)

Round 3 is complete: implementation, physical/frame qualification, post-layout
SPICE and all regression suites passed. No work in progress, blockers or new
interface requests remain. The decisions in this section supersede the earlier
ALU interface and mapping counts.

### Selection proofs and mapping decisions

`tritflow/synth/predicates.py` computes a conservative set of possible trit
values from source IR. Constants, comparisons, `is_true`, negation, min/max,
NANY, procedural selects, cases and Kleene muxes have explicit rules; unsupported
or arithmetic result digits conservatively admit all three values. A selector
is crisp only when its proved set excludes zero. The value-set tests compare
these overapproximations against exhaustive simulation, including expressions
whose correlated operands make the proof deliberately conservative.

| Source construct | Round 3 implementation |
|---|---|
| Comparison used by `?:` | Two-arm min/max AND–OR; no unknown/consensus arm |
| Comparison used by procedural `if` | Its existing +/-1 result is reused; no second `is_true` detector |
| General procedural `if` | Still tests exactly +1; zero takes else |
| `case` | IR keeps predicate/data pairs and a fallback; source simulation evaluates ordinary priority matching independently of mapping |
| Proven disjoint literal equalities on one selector | Shared one-hot decoders; result is max(min(predicate, data)) |
| Complete case enumeration | No default decoder or redundant fallback masking |
| Partial case enumeration | One default predicate, negated max of the explicit matches |
| Identical case data | Share one data mask with the OR of its labels; all-identical results bypass the decoder |
| Constant branches | Fold lattice absorbing/identity values while lowering |
| Zero-capable `?:` and general MUX3 | Existing Kleene consensus and all three selection arms remain |
| A case IR without a partition proof | Retain priority selection; never assume one-hot predicates |

A case partition is proved by recovering constant equality labels from the IR,
requiring identical source selector nodes, proving disjoint label sets, and
counting their coverage of all 3**width digit patterns. Multi-label items are
unions of exact equality labels. No correlation between distinct selector
expressions is assumed. Balanced min/max trees reduce selection depth; generated
nodes, literal detectors and the default mask share across result digits.
This is local circuit mapping and sharing, with no minimum-network claim.

The fanout investigation found actual excess: the old balanced splitter buffered
every root child even when some pins could stay directly driven. Inferred RTL
now groups shallow loads first and retains direct loads, using
ceil((pin_loads-limit)/(limit-1)) additional BUFs when a signal exceeds its
limit. This count follows the pin-capacity bound for a BUF tree; it is not a
minimum-circuit claim. Repeated gate pins count separately. The limit remains
four at **every** input, logic output, tie and inserted BUF. Pre-Round-1
structural designs retain the previous algorithm to preserve their exact
netlists, names, ports, hierarchy and pins.

### Before/after cell counts

The before reports were captured before edits in
`build/hdl_verilog_round3/before.json`; current reports are in `after.json`.
Counts include all fanout BUFs and ties.

| RTL example | Round 2 cells | Round 3 cells | Comment |
|---|---:|---:|---|
| `full_add_rtl` | 16 | 16 | Still 11 NANY + 5 INV, identical to authored `full_add` |
| `adder4_rtl` | 55 | 55 | Unchanged reference ripple structure |
| `case_table` | 32 | 32 | Different selection network, same total |
| `comparator_rtl` | 27 | 27 | Already has crisp comparison outputs |
| `mux_rtl` | 34 | 32 | Consensus retained; two redundant fanout BUFs removed |
| Old nine-op `alu`, now `alu9` | 423 | 262 | 38.1% fewer cells; depth 66 to 27 |
| New shuttle `alu` | — | 64 | Three operations, shared signed add/subtract |

`alu9` has 60 NANY, 104 INV, 47 NAND, 38 NOR, 10 BUF and three ties.
Round 2 had 61 fanout BUFs; the intermediate new selection mapping with the old
splitter used 28, and the first compact-tree mapping used 11. Grouping identical
case arms removed the final extra BUF and additional masks. The complete old
nine-operation source is retained in `examples/alu9.tv` (only the module name
changes), with its independent integer specification in `alu9_reference.py`.
All 729 states still pass, including equivalence against the saved Round 2
423-cell physical netlist. No new physical/runtime qualification of `alu9` is
claimed; the old physical evidence above remains historical Round 2 evidence.

For the brief's two-trit a,b / one-trit op / three-trit result example, a
zero-capable `op ? (a+b) : (a-b)` falls from 116 to 114 cells only by
removing excess BUFs; its consensus remains required. Replacing the condition
with `op==1` allows the cheaper crisp circuit, at 69 cells. Writing
`a+op*b` explicitly shares the arithmetic and costs 31 cells. The mapper does
not silently rewrite arbitrary separate add/subtract branches into that form.

### Candidate experiments and choice

All candidates use two-trit a,b, one opcode trit and three result trits. Their
243 states were checked against independent integer references, source
simulation and mapped cells. The final candidate script includes those checks.
The two 90-cell synthesis-only screens were set aside in favor of sharing
arithmetic. All four routed macros passed fresh official drawing DRC and strict
device/port LVS. Default P&R uses seed 0, 600 annealing steps and the unchanged 20% current
reserve; no PNR, cell, extraction or simulator implementation was edited.

| Candidate / operations at op=-1,0,+1 | Cells | Macro µm | Synth / P&R / DRC / LVS (s) | Frame + signoff (s) | Post-layout SPICE (s) |
|---|---:|---|---|---|---|
| Separate subtract / negate / add (synthesis screen) | 90 | Not routed | 0.028 / — / — / — | Not run | Not run |
| Separate subtract / 3a / add (synthesis screen) | 90 | Not routed | 0.008 / — / — / — | Not run | Not run |
| Separate subtract / round(a/3) / add | 88 | 1704 × 2310 | 0.010 / 9.62 / 2.32 / 0.94 | Rejected: too tall | Not run |
| Shared `a+op*b`, zero opcode round(a/3) | 64 | 1692 × 1590 | 0.002 / 1.59 / 1.89 / 0.91 | 9.99, passed | 18.93, selected ALU run below |
| Shared `a+op*b`, zero opcode negate | 66 | 1596 × 1782 | 0.002 / 1.72 / 1.90 / 0.95 | Rejected: too tall | Not run |
| `a+op*b`: subtract / pass a / add | 31 | 1284 × 1038 | 0.001 / 0.57 / 1.46 / 0.83 | 7.60, passed | Not run |

These are measurements of the tested floorplans, not impossibility proofs for
other seeds/row counts. Evidence is in
`build/hdl_verilog_round3/candidates_final/summary.json`; the two synthesis-only
screens are in `build/hdl_verilog_round3/screened/summary.json`. The selected candidate
and pass-through candidate both used actual `PnrResult.to_chip()` and
`ChipResult.signoff()` with the local `~/TR-1um_MPW_Sanken` pre-check. The other
two routed alternatives failed the wrapper's 1850 × 1602 µm macro bound before
chip construction.

The selected design keeps subtract and add and spends the extra area on a
rounded divide-by-three instruction, which demonstrates balanced ternary better
than a pass-through instruction. One signed opcode trit controls the sign of b,
so the two arithmetic labels share `a + op*b` in plain student `always @* case`.
This is an explicit HDL circuit choice, not an optimizer assumption about
opcode correlations.

| New `alu` port / code | Meaning |
|---|---|
| `a[1:0]`, `b[1:0]` | Signed balanced integers -4..+4 |
| `op = 1'tT` | a-b |
| `op = 1't0` | a >> 1 = nearest a/3 |
| `op = 1't1` | a+b |
| `r[2:0]` | Exact result; range -13..+13 can hold every sum/difference -8..+8 |

There are 64 cells: 22 NANY, 20 INV, 10 NAND, 7 NOR, 2 BUF, and one each
TIEN/TIEP/TIEZ; depth is 20, maximum fanout 4. `alu_reference.py` checks every
one of the 243 input states with independent integer arithmetic and radix
encoding. The old nine-op opcode/result interface is now explicitly `alu9`;
notebook/integration code that expects it should select that example.

### Selected ALU physical and SPICE evidence

The fresh final `alu` macro is **1692 × 1590 µm** (2.69028 mm²). Its final
wrapper has the actual **2500 × 2500 µm** bounding box and **17 passive TEG
pads**, with signal and power routing. Checks passed without waivers: official
drawing DRC (zero violations), strict drawing LVS, MDP with metal preservation,
mask DRC (zero violations), connectivity, fixed frame/DBU/top-cell audit, and
the exact local organizer pre-check. The copied pinned seal ring is preserved.

The solved wrapper DC envelope's maximum utilization is **0.78698**, below the
0.8 target; its margin to the published limit is 21.30%. This is the existing
PNR model with its documented current/width assumptions, not lifetime EM
qualification. `submission_ready` remains **false**: the custom 17-pad
probe/bond map, package/substrate/VMID arrangement and ESD/operating conditions
still need shuttle-owner approval. No upload or publication occurred.

| Stage | Local wall time (s) |
|---|---:|
| Source loading, synthesis and exhaustive source/cell equivalence | 0.0098 |
| P&R and native connectivity/routing checks | 1.534 |
| Official macro drawing DRC | 1.872 |
| Strict macro device/port LVS | 0.912 |
| Full-chip construction and all signoff checks | 10.079 |
| Matched-device/wire-C extraction and setup | 0.188 |
| Post-layout SPICE and measurements | 18.928 |
| **Total including full-chip qualification** | **33.523** |

This is comfortably inside the requested ~150 s local budget. The brief's
rough 3–5× Colab factor gives 101–168 s; no actual Colab timing is claimed.

Post-layout SPICE uses the matched **macro** devices, actual-GDS estimated
lumped wire capacitance and 10 fF/output. The full-chip wrapper gets physical
and DC-network qualification; its pads/package parasitics are not included in
the macro transient. Stimuli hold for 1 µs with 1 ns edges and 2 ns maximum
step; existing logical `.nodeset` initialization only guesses the initial state.
The deterministic greedy sequence covers all three instructions and every
-1/0/+1 level on each of the three output trits:

| a | b | op | Expected r |
|---:|---:|---:|---:|
| -4 | -4 | -1 | 0 |
| -4 | -3 | +1 | -7 |
| +3 | -4 | -1 | +7 |
| -4 | -4 | 0 | -1 |

All **4 vectors / 12 output checks passed**, with zero unsettled windows.
Maximum absolute level error: **0.038973 V**. Maximum measured settling:
**221.06 ns**, with per-output maxima r[2:0] = 197.09 / 221.06 / 124.85 ns.
These are representative transitions, not exhaustive analog timing. The
largest settled supply consumption among these four vectors is about 116.65 mW
(ideal supply sources, approximately 11.665 mA rail current); this is not an
exhaustive worst-case power claim.

All five other RTL examples also passed fresh P&R, official drawing DRC and
strict LVS, in `build/hdl_verilog_round3/regression/summary.json`. Macro sizes
are 876 × 702 / 1692 × 1398 / 1212 × 1038 / 1164 × 870 / 1212 × 1038 µm for
full_add_rtl / adder4_rtl / case_table / comparator_rtl / mux_rtl.

### Reproduce and regression status

```sh
TR1UM_PDK=~/pdk/TR-1um-pinned python3 -m examples.rtl_check
# Just the small showcase, including frame signoff and SPICE:
TR1UM_PDK=~/pdk/TR-1um-pinned python3 -m examples.rtl_check --names alu
# All instruction/area experiments (SPICE is in rtl_check):
TR1UM_PDK=~/pdk/TR-1um-pinned python3 -m examples.alu_candidates
# The two extra synthesis-only screens:
python3 -m examples.alu_candidates --names case_add_sub_neg case_add_sub_left --synthesis-only --output-root build/hdl_verilog_round3/screened
# Large variant, explicitly opt in to P&R and SPICE:
TR1UM_PDK=~/pdk/TR-1um-pinned python3 -m examples.rtl_check --names alu9
```

The main evidence is `build/hdl_verilog_round3/summary.json`. Its `alu/`
contains gate JSON/TritVerilog/SPICE, reports, routed macro GDS/JSON, strict LVS
and extracted devices, `alu.capacitance.json`, `alu.measurements.json` and
`spice/{tb.spice,ngspice.log,waveform.txt}`. `alu/chip/` contains the wrapped
GDS, pad map/notes and native signoff reports. Use `--output-root` for isolated
runs and `--mpw-template` to select another organizer checkout.

Focused implementation checks: **139 passed in 1.01 s** before final suites.
New tests cover conservative value sets, crisp conditional/if identity,
zero-capable consensus, explicit partition proof failure, partial/default and
multi-label cases, identical constant outputs, bounded compact BUF trees and
the new 243-state oracle/stimulus coverage. All 27 unary truth tables and
seeded arbitrary two-/three-input tables still pass, including disabled
optimization and gate-writer round trips.

Final regression evidence:

- Required `python3 -m pytest tests/hdl tests/synth tests/pnr -q`:
  **370 passed in 102.53 s**.
- Remaining directories, `python3 -m pytest tests/ -q --ignore=tests/hdl
  --ignore=tests/synth --ignore=tests/pnr`:
  **392 passed, 2 skipped in 730.92 s**. The same optional STA checks skip
  because `build/adder_scaling/adder6/adder6.json` is absent; these are not
  implementation failures.
- Combined: **762 passed, 2 skipped, no failures**. Logs are
  `build/hdl_verilog_round3/{required-tests,remaining-tests}.log`.
- After the final mapper changes, all six saved physical gate JSON files and
  all four saved routed-candidate JSON files still equal current synthesis.
- The two extra synthesis-only screens passed the candidate runner's 243-state
  independent integer checks. The selected 64-cell artifact, full-chip
  signoff and 2 ns SPICE result remain the measured artifacts above.
- `git diff --check` passed.

The 11 pre-Round-1 examples still require exact JSON/cell-count identity against
the unchanged legacy fixture. The retained Round 1 RTL fixture is kept as an
independent functional and no-cell-growth reference: Round 3 intentionally
remaps its inferred selections, so its old physical netlists are no longer
required to have identical generated instance names. No fixture was rewritten.

Remaining unsupported syntax and the earlier notebook `broken` integration
note are unchanged. No notebook files or other streams' implementations were
edited; no packages installed, remote services accessed, sign-ins, publication,
commits, pushes, tags, checkouts, resets or stashes. The user's pre-existing
`briefs/HDL_VERILOG.md` modification is preserved. PDK remains pinned to public
commit `5d963db9d44e192d37a0489c208bfccf2e2f690c`.
