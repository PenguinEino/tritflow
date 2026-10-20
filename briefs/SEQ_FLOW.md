# Brief: SEQ_FLOW — sequential logic in TritFlow (registers from `always @(posedge clk)`)

You work in the git worktree `~/code-a-chip-seq` (branch `sequential`). Never touch `~/code-a-chip`,
`~/code-a-chip-rewrite`, `~/code-a-chip-hdl` or `~/balanced-ternary-logic`. Read `~/balanced-ternary-seq`
only (another stream designs the flip-flop circuit there and may still be working). No git commit or
push: the integrator reviews and commits. This work is isolated on purpose: if it does not work out,
it is dropped without affecting the main flow, so keep every change additive.

## Goal

TritFlow handles combinational logic only. Add registers: a student writes

```verilog
module counter(input trit clk, output reg trit [1:0] n);
  always @(posedge clk) n <= n + 1;
endmodule
```

and gets a synthesized netlist with flip-flop cells, a cycle-accurate logic simulation, placement and
routing with DRC/LVS, and a post-layout SPICE transient driven by a clock, all checked.

## Contract with the circuit stream (SEQ_CIRCUIT, `~/balanced-ternary-seq/briefs/SEQ_CIRCUIT.md`)

- Cell `TDFF`, pins `D`, `CLK`, `Q` (maybe `QB`), rails VDD/VMID/VSS, the TritFlow cell template.
- The clock takes only −1 and +1 in normal operation. A register captures D when CLK goes from −1 to
  +1 (`posedge`); Q holds until the next rising edge. The value 0 on a clock is not a valid level.
- That stream delivers `reports/tdff_summary.json`, `tdff.gds`, an extracted netlist, setup/hold and
  clock-to-Q numbers. Until it exists, use a provisional circuit of your own (for example the author's
  cross-coupled INV latch `~/balanced-ternary-logic/ternary_latch.sch` plus CMOS transmission gates,
  master–slave) behind the same interface, and keep the swap to the final circuit a one-place change.
  If the final circuit is available before you finish, integrate it and say so.

## What to build

1. **Cell library, additively.** Existing cell files and `cells/out/library.json` bytes must not
   change (recorded results hash them). Put the sequential cell in a separate extension (for example
   `cells/out_seq/` with its own library manifest) that is loaded only when a design contains
   registers. Generate its layout/abstract to the same template and qualify it with the pinned PDK
   decks (DRC, LVS) like the other cells. Characterize setup, hold, clock-to-Q and static current.
2. **HDL.** `always @(posedge clk)` with nonblocking `<=` on `reg trit` scalars and vectors, `if`/`case`
   inside, mixed with the existing combinational constructs. Infer one TDFF per register trit.
   Optional synchronous reset via `if (rst == 1't1) q <= …` is welcome if cheap. Clear errors with
   file:line:column for unsupported forms (negedge, multiple clocks, asynchronous reset, latches).
   Coordinate with the existing parser/elaborator rather than forking it.
3. **Simulation and checking.** A cycle-based simulator: state + next-state functions. Equivalence of
   the synthesized netlist to the RTL by matching registers by name and checking the combinational
   next-state and output functions exhaustively (inputs + state, up to 12 trits), then a seeded
   multi-cycle random co-simulation. An independent reference for each example (e.g. a Python counter).
4. **Place & route.** TDFF is one more cell; the clock is an ordinary net (no clock-tree synthesis;
   report the clock net's fanout and wire capacitance). DRC/LVS as usual.
5. **Post-layout SPICE.** A new module (do not edit `tritflow/sim/runner.py`, `bench.py`, `spice.py`,
   `characterize.py`, `sizing.py`, `tritflow/pnr/verify.py`, `tritflow/extract/lvs.py`: other recorded
   results hash them; build decks in a new module and call the existing public functions) that drives
   a clock and an input sequence, and checks every register output against the cycle simulation within
   ±0.5 V at a sample time before each next edge. Report the maximum clock frequency observed passing.
6. **Examples** (each: synthesize, exhaustive equivalence, P&R, DRC/LVS, post-layout SPICE of several
   cycles): a 3-stage ternary shift register; a 2-trit counter (`n <= n + 1`, counting −4…+4 and
   wrapping); if time allows, an accumulator: the ALU from `examples/alu.tv` (when it exists in your
   tree) feeding a 2-trit register.
7. **Tests** in `tests/` (new files), and `docs/status/SEQ_FLOW.md`: language added, clock rules,
   cell provenance (provisional or final circuit), synthesis/equivalence method, results with cell
   counts, die sizes, timings, what is unsupported. Run `python3 -m pytest tests -q` and report it.

Do not edit `notebook/`. TR1UM_PDK=~/pdk/TR-1um-pinned. The 5090 server
(`ssh penguin@einosuke-llm-5090`, workspace `~/tritflow-sim`, rsync excluding build/.git/logs; touch nothing
else; never stop/start its services) may be used for heavy runs. Do not publish anything; no sign-in.
