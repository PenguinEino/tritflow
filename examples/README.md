# TritVerilog examples

TritVerilog describes combinational circuits over **−1, 0, +1**. A `trit` is
separate from Verilog's four-state logic: there are no `x` or `z` states.
At the circuit boundary these values correspond to −5, 0, +5 V.

Run synthesis from the repository root:

```sh
python3 -m tritflow.synth examples/adder.tv --top adder -P N=4 -o build/adder4/
python3 examples/build_all.py
python3 -m pytest tests/hdl tests/synth tests/viz
```

`build_all.py` regenerates `build/adder4/` (N=4), `build/full_add/`,
`build/mac1/`, and `build/mul1/` through the CLI. It works from any current
directory and leaves other streams' files in those directories intact.
Use `--output-root /tmp/tritflow-build` for an isolated, reproducible rebuild.

The command writes `adder4.json` (the shared GateNetlist), `adder4.gate.tv`,
`adder4.spice`, `adder4.report.json`, and `adder4.report.txt`. It runs an automatic
source-to-cell equivalence check before writing the files. The explicit `N`
override is appended to the output top name; `--name` selects another name.
The SPICE file defines the top subcircuit; a testbench must also include
`cells/out/all.spice`, the PDK models, and the three supplies. SPICE signal
ports follow the JSON port list, then `VDD VMID VSS`. Instance ports follow
`A [B] Y VDD VMID VSS` (TIE cells have only `Y` before the rails).

In a notebook:

```python
from tritflow.hdl import load, loads
from tritflow.synth import synthesize, evaluate_netlist, write_artifacts

design = load("examples/adder.tv", top="adder", params={"N": 2})
table = design.truth_table()          # dict of numpy columns, including inputs
inputs = {name: table[name] for name in design.inputs}
logic_outputs = design.evaluate(inputs)
net = synthesize(design, fanout_limit=4)
cell_outputs = evaluate_netlist(net, inputs)
report = net.report()                # JSON-serializable dict
paths = write_artifacts(net, "build/adder2")
```

For a gate graph and a small HTML truth table:

```python
from tritflow.netlist import GateNetlist
from tritflow.viz.graph import gate_graph, color_nets, net_values, truth_table_html

fa = GateNetlist.load("build/full_add/full_add.json")
gate_graph(fa).show()
color_nets(fa, {"a": 1, "b": 1, "cin": -1}).show()
signals = net_values(fa, {"a": 1, "b": 1, "cin": -1})
assert signals["sum"] == 1 and signals["cout"] == 0
truth_table_html(fa)  # final expression in a notebook cell; no pandas needed
```

The graph runs left-to-right by longest logic path. Cell fills keep their type
colors; input/output markers use distinct shapes. Colored wires indicate
−1/0/+1 with a blue/gray/red legend that also shows −5/0/+5 V. Hover shows cell,
source hierarchy, net and pin values. All signal nets, including unused input
stubs, receive a color. Supply a scalar trit for every input bit; vector ports
use names such as `a[0]`. `gate_graph(fa, inputs=...)` is equivalent to
`color_nets(fa, ...)`. Both return ordinary Plotly figures without changing
the netlist or the notebook's renderer; their layout can be customized with
`fig.update_layout(...)` or exported with `fig.write_html(...)`.

`truth_table_html()` accepts either a source `Design` or a `GateNetlist`. It
returns an HTML string with a notebook rich representation, preserves port
order/direction, and escapes all names. The default limit is 81 rows (enough
for MAC); increase `max_rows` explicitly to display a larger complete table.
It rejects oversized tables before simulation rather than truncating them.
`evaluate_netlist(net, inputs, return_all=True)` exposes internal signal arrays
for batched notebook analysis; its default return still contains only outputs.

`loads(source, top=..., params=..., filename="notebook.tv")` accepts an in-memory
string. `parse()` returns a source-located AST; `elaborate()` converts the AST
to the bit-level DAG. `load()` also accepts a list of source paths. Relative
`` `include "file.tv" `` directives share the HA and FA definitions and preserve
the included file's diagnostic locations.

| File / top | Meaning | Authored logic cells |
|---|---|---|
| `half_add.tv` / `half_add` | a + b = sum + 3·carry | 5 NANY, 2 INV |
| `full_add.tv` / `full_add` | a + b + cin = sum + 3·cout | 11 NANY, 5 INV |
| `adder.tv` / `adder` | A + B + cin = SUM + 3ᴺ·cout | N full adders |
| `mul1.tv` / `mul1` | p = a·b | 2 NAND, 1 NOR, 1 INV |
| `mac1.tv` / `mac1` | x + a·b + cin = sum + 3·cout; auxiliary min/max outputs | 2 NAND, 1 NOR, 11 NANY, 9 INV |
| `minmax.tv` / `minmax` | lo = min(a,b), hi = max(a,b) | inferred from expressions |
| `sign.tv` / `sign` | s = sign(a), opposite = −a | inferred wire and INV |

The HA, FA, MUL and MAC connections follow the reference project's
`HALF_ADDER_SIMULATION.md`, `FULL_ADDER.md`, `MUL.md` and `MAC.md` respectively.
Explicit live primitive instances retain their identities through optimization.
`mac1` exposes the taped-out AND/OR buffering as well as its arithmetic result.

Vectors retain their declared indices; expressions and concatenations use
left-to-right/MSB order. For arithmetic, `a[i]` has weight 3ⁱ. Parameterized
adders require `N >= 1`. The tests exhaust all inputs for N=1 through N=5;
N=6 additionally uses 100,000 independent arithmetic reference vectors.

Supported signal operators are `~a` (−a), `a & b` (min), `a | b` (max), and
`nany(a,b)` (negative saturated sum), applied elementwise to equally sized
vectors. `4'tT01T` is a four-trit constant (T=−1). Assignments require equal
widths, with no implicit extension or truncation. Gate primitives are scalar,
with output first. Parameters, indices and generate loops support integer
`+ - * / %` and comparisons; division truncates toward zero. Trit arithmetic,
`always`, `reg`, sequential logic and `x/z` are rejected with file:line:column
diagnostics. Global net names `VDD`, `VMID`, and `VSS` are reserved.

Synthesis folds constants, removes double negation and dead logic, shares
expressions and applies De Morgan transformations when they remove single-use
inversions. It never treats `a & ~a` or `a | ~a` as Boolean constants.
Independent cell simulation checks every input vector up to 12 input trits;
larger designs use 100,000 reproducible random vectors. `truth_table()` limits
materialized tables to 12 inputs by default; synthesis streams batches.

The fanout limit counts **cell input pins**, including repeated connections to
the same gate. It applies to primary inputs, TIE cells and inserted BUFs as well
as logic outputs. External port capacitances belong to SPICE characterization;
they do not add an assumed cell load. Limits must be integers >=2. A wire to a
distinct output name uses a BUF so every JSON net has one physical driver.
Reports count cell stages for logic depth, and count hierarchy cells exclusively
at their source module/generate scope. SPICE encodes unsafe or case-conflicting
signal names and records the original names in comments.
## Notebook circuit catalog

Chapter 8 selects `sign`, `compare2`, `mul2` or `minmax` from
`examples.curated.DESIGNS`. The existing scalar sign/min-max examples join two
new arithmetic designs:

- `compare2.tv` compares signed two-trit integers (a₀+3a₁ versus b₀+3b₁),
  returning −1/0/+1. Two saturated additions let a nonzero high-digit
  comparison dominate the low digit.
- `mul2.tv` combines four `mul1` partial products with two `half_add` slices.
  Its four-trit output preserves the exact signed integer product.

The catalog's independent Python specifications use integer comparison,
multiplication, balanced-radix encoding and sorting, never mapped cell logic.
Every choice is exhaustively checked, synthesized and physically routed through
official PDK DRC and strict device-level LVS:

```sh
python3 -m pytest tests/synth/test_curated.py -q
TRITFLOW_CIRCUIT=compare2 python3 notebook/validate_notebook.py --execute
```

The notebook stages editable HDL and shared include files under its build
directory, so edits preserve the committed examples. Change the mathematical
reference deliberately when changing a design's specification.

