# Brief: HDL_VERILOG — basic Verilog on trit signals, and synthesis of any function

You work in the git worktree `~/code-a-chip-hdl` (branch `hdl-verilog`). Never touch `~/code-a-chip`
or `~/code-a-chip-rewrite` (other people work there). No git commit, push or tag: the integrator
reviews and commits. Code comments and docs in English; your status note may be Japanese.

## Why

TritVerilog (`tritflow/hdl/parser.py`) only allows `~` (negate), `&` (min), `|` (max) and `nany()` on
trit signals, plus structural instances. `+ - * / %` and comparisons parse but work only on integer
parameters and indices; on signals they raise "arithmetic/comparison on trits is unsupported".
There is no `case`, no `if`, no `? :`, no `always`. A reviewer who writes
`assign {cout, sum} = a + b + cin;` gets an error. That is not acceptable for a tool called an HDL
flow. The goal: everything a student learns as basic combinational Verilog works on trits, and
synthesis can implement any combinational function, using the fact that NANY with the ±1 constants
is functionally complete (`notebook/completeness.py` shows the closure: INV/NAND/NOR + constants reach
11/27 one-input functions, NANY + TIEZ 3/27, NANY + TIEP/TIEN 27/27).

## Part 1 — operators on trit signals and vectors (do this first)

Balanced ternary integers: a vector `trit [N-1:0] x` has value Σ x[i]·3^i (little-endian, as in
`examples/adder.tv`). Logic values follow Kleene's three-valued logic, consistent with the existing
`&` = min, `|` = max, `~` = negation: true = +1, unknown = 0, false = −1.

- Arithmetic on signals: binary `+`, `-`, unary `-` (negation is free: negate every trit), `*`.
  Width rules like Verilog: an expression is evaluated at the width of its context (the assignment
  target, including concatenations such as `{cout, sum}`), operands are sign-extended (in balanced
  ternary, extension is with 0), and results are truncated to the target width. Document the rules.
- Synthesis of `+`/`-`: expand into ripple-carry adders built from the verified half/full-adder
  structures (`examples/half_add.tv`: 5 NANY + 2 INV; full adder: 11 NANY + 5 INV), the way Yosys maps
  `$add` to an adder. Constant operands should simplify (e.g. `x + 0`, adding a constant trit).
  `*`: an array multiplier built from the 1-trit product (`examples/mul1.tv`/`mac1.tv` show the
  existing gate-level structures) and adders.
- Comparisons `== != < <= > >=` on vectors return one trit: +1 true, −1 false. Base them on the sign
  of the difference (`examples/sign.tv` and `compare2.tv` show existing structures).
- Conditional operator `c ? x : y`: selects `x` when `c` is +1 (true), `y` when `c` is −1 (false);
  when `c` is 0 (unknown) the result is `x` where `x == y` trit by trit, otherwise 0 (Kleene). State the
  rule in the docs and check it exhaustively.
- Logical operators if cheap: `!` (= `~`), `&&` (= min), `||` (= max) on single trits.
- `/` and `%` on signals may stay unsupported with a clear error, unless trivial.

## Part 2 — procedural combinational code and any function

- `always @(*)` / `always @*` blocks with `begin … end`, blocking `=` assignments to `wire`/`reg trit`
  declarations (accept `reg trit` as a synonym of `wire trit` for combinational use), `if`/`else if`/
  `else`, `case (expr) … endcase` with `default`, and multiple labels per item. Literals already exist:
  `1'tT` (−1), `1't0`, `1't1`, and wider ones like `2'tT1`. A case on a concatenation
  (`case ({a, b}) 2'tTT: y = 1't1; …`) is how a student writes a truth table.
  Incomplete assignment in a combinational block must be an error (no latches), with file:line.
- Elaborate procedural code into the existing expression IR (multiplexers/selects), so the simulator,
  equivalence checker and writers keep working.
- Synthesis of any function: add a mapping for a general three-way selection / arbitrary truth table
  using only library cells (INV, NAND, NOR, NANY, BUF, TIEP, TIEZ, TIEN). Suggested approach:
  (a) precompute, by closure search over NANY/INV/NAND/NOR and the three ties, a small cell network for
  every one-input function (27) and for the selector/literal functions a three-way multiplexer needs;
  (b) build a three-way multiplexer from them; (c) decompose larger functions by ternary Shannon
  expansion f = MUX3(x, f|x=−1, f|x=0, f|x=+1), sharing identical cofactors; (d) keep the existing
  rewrite/optimize passes. Optionally (time permitting) search small two-input functions exhaustively
  for cheaper networks. Never claim the result is minimal.
- Every synthesized netlist must still pass the existing exhaustive equivalence check against the
  HDL's own semantics (`tritflow/synth`), and the HDL semantics must match an independent integer or
  table reference in the tests.

## Must not break

- Every existing example and test keeps the same synthesized netlist (same cells, same instance
  names) where it does not use the new features. Add a test that compares cell counts/netlist JSON
  of all `examples/*.tv` before/after.
- `tritflow/pnr`, `tritflow/sim`, `tritflow/extract`, `tritflow/cells` are out of scope; do not edit them.
  Do not edit `notebook/` either (the integrator is rewriting it); if the notebook's `broken` example
  (signal `+` rejected) stops being an error, note it in your status file instead.

## Deliverables

1. Parser, elaborator, IR, simulator and synthesis changes, with focused modules and docstrings that
   explain the circuit meaning.
2. New examples: `examples/full_add_rtl.tv` (`assign {cout, sum} = a + b + cin;`),
   `examples/adder4_rtl.tv` (4-trit `+`), a case-statement truth table, a comparator, a `?:` mux, and
   a small ALU selected by a trit opcode (add / subtract / negate / min / max). Each one must
   synthesize, pass the exhaustive equivalence check, and place and route DRC-clean and LVS-matched
   with `tritflow.flow` (run P&R + DRC/LVS on at least the full adder, the 4-trit adder and the ALU;
   the 5090 server `ssh penguin@einosuke-llm-5090`, workspace `~/tritflow-sim`, may be used for heavy
   jobs — rsync excluding build/.git/logs, touch nothing else there, never stop/start its services).
   Report cell counts of `full_add_rtl` vs the hand-written `full_add`.
3. Tests in `tests/hdl` and `tests/synth`: parsing, semantics (exhaustive against independent
   references), width rules, error messages with file:line for unsupported constructs and latches.
   Run `python3 -m pytest tests/hdl tests/synth tests/pnr -q` (and the rest of `tests/` if time allows)
   and report the results.
4. `docs/status/HDL_VERILOG.md`: the supported language (a table a student can read), width and
   Kleene rules, the synthesis method for each construct, cell counts, test results, what remains
   unsupported, and decisions you made.

Constraints: TR1UM_PDK=~/pdk/TR-1um-pinned. Do not publish anything. No sign-in anywhere.

## Round 2 (2026-10-20): shifts and the showcase ALU

The first round is committed (b4ca669) and merged. Continue in the same worktree and branch.

1. Shift operators on trit vectors: `<<` and `>>`. Left shift by k multiplies by 3**k (zeros enter at
   the bottom, the result is truncated to the context width). Right shift by k drops the k lowest
   trits; in balanced ternary this equals division by 3**k rounded to the nearest integer (exact
   halves cannot occur) — state this property in the docs and test it against an independent integer
   reference. Constant shift amounts are pure wiring (no cells). Signal shift amounts (a trit vector
   read as a balanced integer) must also work; choose and document the meaning of a negative amount
   (shifting the other way is natural in balanced ternary) and implement it with multiplexers.
   `<<<`/`>>>` may be aliases. Shift precedence as in Verilog.
2. Replace `examples/alu_rtl.tv` with `examples/alu.tv` (module `alu`): inputs `trit [1:0] a, b`
   (−4..+4) and `trit [1:0] op`; output `trit [3:0] r` (−40..+40) for every operation, written in
   plain student Verilog (`always @*`, `case`). The nine opcodes, in this order:
   `2'tTT` add a+b, `2'tT0` subtract a−b, `2'tT1` negate −a, `2't0T` min (a & b, digit-wise),
   `2't00` max (a | b), `2't01` shift left a<<1 (×3), `2't1T` shift right a>>1 (÷3 rounded),
   `2't10` compare (sign of a−b: −1, 0, +1), `2't11` multiply a*b.
   If digit-wise min/max read oddly against the integer ops, say so in the status note. Check all 729
   input states exhaustively against an independent integer reference, then place and route with
   DRC/LVS (`tritflow.flow`) and run a post-layout SPICE on a representative input sequence that
   exercises every opcode and all three levels on every output trit. Report the cell count, die size,
   and the wall time of synthesis, P&R, DRC, LVS and SPICE separately (it will run on a free Colab
   CPU, roughly 3–5× slower than here).
3. Update tests, `examples/README.md`, `examples/rtl_check.py` and `docs/status/HDL_VERILOG.md`
   (append a Round 2 section). Keep every rule of the first round (no notebook edits, no other
   streams' paths, legacy netlists unchanged, no git commits).

## Round 3 (2026-10-20): cheaper selection logic, and an ALU that fits a shuttle

Round 2 is committed (merged as 5b10012). The nine-operation ALU works but is 423 cells,
4440 × 9366 µm and ~1.8 W static: too large for the 2.5 mm OpenSUSI MPW frame and too slow for a free
Colab run (~8 min locally). Most cells are the `case` selection, not the arithmetic: dropping the
multiplier only saves 57 cells; `r = op ? (a+b) : (a-b)` costs 116 cells while `r = a + op*b` costs 31.

1. **Cheaper multiplexing.** When every selector is crisp (always ±1, never 0) — case-label equality
   detectors, comparisons, `if` conditions that are comparisons — select with Kleene AND–OR instead of
   the general three-way multiplexer: r = MAX_i MIN(s_i, x_i) with exactly one s_i = +1 and the rest
   −1 (MIN = NAND+INV, MAX = NOR+INV, share decoders across output trits). Keep the general MUX3 and the
   Kleene-consensus `?:` wherever a selector can be 0. Prove crispness from the IR (do not assume), and
   check every result exhaustively as before. Look for other large costs (fanout BUF insertion,
   duplicated decoders, constant propagation through selects) and fix what is real. Report before/after
   cell counts for every RTL example and the old nine-op ALU. Never claim minimality.
2. **The showcase ALU, rewritten for a shuttle.** Replace `examples/alu.tv` with a smaller ALU:
   two-trit `a`, `b`; a reduced instruction set chosen by you (the author asked for "two trits, fewer
   instructions"), in plain student Verilog (`always @*`, `case`). It must include add and subtract;
   prefer operations that show ternary character (for example shift ×3 / ÷3-rounded, negate, compare,
   and `a + op*b`-style add/subtract selected by one trit). Constraints: the routed core must fit inside
   the TR-1um MPW frame with room for pads — measure it with `PnrResult.to_chip()` and `signoff()` as
   in `tritflow/pnr/chip.py` (the integrator's local MPW template is `~/TR-1um_MPW_Sanken`); local
   synthesis + P&R + DRC + LVS + post-layout SPICE together within about 2.5 minutes. Give a table of the
   candidates you tried (operations, cells, die, times) and justify the choice in the status note.
   Keep the nine-op version as `examples/alu9.tv` (documented as the large variant).
3. Same rules as before: legacy (pre-Round-1) netlists unchanged; independent references; exhaustive
   checks; tests; `examples/rtl_check.py` and `docs/status/HDL_VERILOG.md` (append Round 3); no notebook
   edits; no git commits.
