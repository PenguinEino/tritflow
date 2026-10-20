# HDL_VERILOG status

Updated: 2026-10-20. Complete: implementation, six physical examples and the
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
