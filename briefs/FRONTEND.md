# Brief: FRONTEND stream — TritVerilog parser, logic simulation, synthesis

You own `tritflow/hdl/`, `tritflow/synth/`, `examples/`, `tests/hdl/`, `tests/synth/`,
`docs/status/FRONTEND.md`. Read `AGENTS.md`, `docs/concept.md` (sections HDL, 合成),
`docs/interfaces.md` first.

## Language (TritVerilog, `.tv`) — combinational only
- `module name #(parameter N = 4) (input trit a, b, input trit [N-1:0] x, output trit y); ... endmodule`
  (ANSI port lists; also allow non-ANSI is NOT required).
- `wire trit [msb:lsb] w;`, `assign lhs = expr;`, bit select `a[i]`, part select `a[3:1]`,
  concatenation `{a, b}`, named-port instances `m #(.N(3)) u (.a(x), .y(z));`.
- `parameter`/`localparam`, `genvar`, `generate for (...) begin : label ... end endgenerate`,
  integer constant expressions in widths/indices/loops (+ − * / % comparisons).
- Operators on trits: `~a` negation, `a & b` min, `a | b` max, parentheses; builtin
  `nany(a, b)` = −clamp(a+b). Constants `1't0`, `4'tT01T` (T = −1, MSB first).
- Gate primitives (output first, like Verilog): `inv g (y, a); nand g (y, a, b); nor g (y, a, b);
  nany g (y, a, b); buf g (y, a);`.
- Not supported (clear error): always, reg, `+ - *` on trits, x/z, sequential logic.
- Errors carry file:line:col and a readable message. Use `lark` (installed).
- `trit` is not Verilog's 4-state logic; say so in the module docstring.

## Pipeline
1. Parse → AST. 2. Elaborate (parameters, generate, vectors bit-blasted, hierarchy flattened while
   keeping each node's hierarchy path). 3. IR = DAG of ops {neg, min, max, nany, const, input}.
4. Logic simulation: vectorized numpy evaluation of IR for many input vectors; `truth_table()`.
5. Rewrites valid in Kleene/balanced-ternary logic only: constant folding, double-negation removal,
   CSE/structural hashing, dead-code removal, De Morgan pushes only where they reduce cells.
   Never use excluded middle / complementation laws. Each rewrite is unit-tested by exhaustive check.
6. Tech mapping to cells (pins per interfaces.md): neg→INV, ~(a&b)→NAND, a&b→NAND+INV,
   ~(a|b)→NOR, a|b→NOR+INV, nany→NANY, consts→TIEP/TIEZ/TIEN, explicit gate primitives map 1:1.
   Fanout limit (default 4, parameter) → insert BUF trees.
7. Equivalence check: exhaustive when inputs ≤ 12 trits, else 100 000 random vectors; compare
   source IR vs mapped netlist (simulate the netlist with cell functions).
8. Writers: GateNetlist JSON (`tritflow/netlist.py`), gate-level TritVerilog using primitives,
   SPICE netlist (`X<inst> <signal nets...> VDD VMID VSS <CELL>`, top as a subckt), synthesis report
   (cells by type, logic depth, per-hierarchy counts) as JSON + text.

## CLI and API
- `python3 -m tritflow.synth examples/adder.tv --top adder -P N=4 -o build/adder4/`
  → `adder4.json`, `adder4.gate.tv`, `adder4.spice`, `adder4.report.json`.
- Python API usable from a notebook: `design = tritflow.hdl.load("x.tv", top=..., params=...)`,
  `design.truth_table()`, `net = tritflow.synth.synthesize(design)`, `net.report()`.

## Examples (in `examples/`, each with exhaustive tests)
half_add, full_add (from NANY/INV exactly as `~/balanced-ternary-logic/HALF_ADDER_SIMULATION.md`
and `FULL_ADDER.md` describe), adder #(N), mul1 (`MUL.md`: t1=NAND, t2=NOR, t3=INV(t2), p=NAND(t1,t3)),
mac1 (x + a·b + cin = sum + 3·cout as in `~/balanced-ternary-logic/MAC.md`), minmax demo, sign.
Check against an independent Python arithmetic reference (balanced-ternary integers), not against
the circuit itself. Report gate counts for full_add (taped-out design: 11 NANY + 5 INV).

Definition of done: all of the above, tests pass, status updated with examples of output.
