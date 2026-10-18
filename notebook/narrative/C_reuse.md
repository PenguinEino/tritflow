## Appendix C. Use and extend TritFlow

Start in Colab for the installed EDA environment, or keep an editable source
checkout locally. The repository contains the example HDL, generated cell
views and notebook assets needed by the flow; installing the Python package
alone does not supply those files.

### Install from GitHub

From an empty working directory, install the selected source revision:

```sh
python3 -m pip install --src ./src -e "git+https://github.com/PenguinEino/tritflow.git@{reuse.source_ref}#egg=tritflow"
cd src/tritflow
```

The full flow also needs native KLayout with its Ruby DRC/LVS engine, ngspice
and the pinned OpenSUSI PDK. On the supported Ubuntu amd64 releases, use the
repository's setup script:

```sh
bash notebook/colab_setup.sh --source "$PWD"
```

For an existing tool installation, set `TR1UM_PDK` to the qualified PDK tree
and, if needed, `KLAYOUT_BINARY` to the native executable. The exact source,
PDK and tool pins live in `notebook/setup_pins.json`; setup details and supported
platforms are in `notebook/README.md`.

### The seven-line API

Run from the source root after setup:

```python
from tritflow import flow
design = flow.load("examples/adder.tv", "adder", {"N": 2})
net = design.synthesize(name="adder2")
layout = net.place_and_route(output_dir="build/adder2")
assert layout.drc()["clean"] and layout.lvs()["matched"]
vectors = [tuple(0 for p in net.ports if p.dir == "input")]
post = layout.extract().simulate(vectors, load=100e-15)
```

This is a zero-input smoke simulation. `load` is in farads; each vector follows
the bit-blasted input-port order in `net.ports`. The default expected outputs
come from the mapped logic. For an arithmetic result, supply an independent
integer oracle with `expected=` and a transition plan that exercises the
intended paths, as the notebook does. Inspect `post["measurements"]` for level
and settling results; completing a simulation alone does not assert a pass.
`layout.extract(wire_c=False)` selects extracted devices alone; the default
adds the geometry-based wire-capacitance estimate.

Inspect the circuit before routing with `net.schematic(expand="*").show()`;
use `.save("build/adder2.svg")` to retain the same schematic. Chapter 7 shows
`tritflow.sta.analyze`, and chapter 9 shows the separate full-chip wrapper.
Use `flow.loads(source, top=..., params=...)` for HDL supplied as a string.

### Command-line entry points

These commands run from the same source root. They write under `build/` and
retain the native reports beside their outputs.

```sh
python3 -m tritflow.synth examples/adder.tv --top adder -P N=2 --name adder2 -o build/adder2
python3 -m tritflow.pnr build/adder2/adder2.json -o build/adder2 --seed 7
```

The synthesis command writes gate JSON, mapped TritVerilog, SPICE and its
equivalence report. P&R writes GDS and the placement/routing record and runs
physical checks. Use the Python API above for extracted simulation and chip
wrapping; there is no generic `tritflow` executable or `tritflow.sta` module CLI.

For library development, build and check a private output directory:

```sh
python3 -m tritflow.cells build --out build/cell_trial
python3 -m tritflow.cells verify --out build/cell_trial
python3 -m tritflow.sim.characterize INV --spice build/cell_trial/INV/INV.ext.spice --destination build/INV.char.json
```

The private `build` command generates views; `verify` performs the physical
and DC checks. `python3 -m tritflow.sta.characterize --help` describes midpoint
timing characterization, and `python3 -m tritflow.sta.validate` repeats the
STA-to-SPICE comparison against existing native simulation evidence. Appendix B
lists the separate larger electrical experiments and their rerun commands.

### Add a cell

Define the circuit, ports and truth function in
`tritflow/cells/circuits.py`. Add its geometry in `tritflow/cells/compact.py`
(`WIDTHS` and drawing dispatch), using the PDK primitives in
`tritflow/cells/primitives.py`; `tritflow/cells/layout.py:build_cell` emits
the GDS, source SPICE, abstract and truth table. Preserve the common row height,
grid, rail order and legal pin access, and describe every internal routing
obstruction in the abstract.

A new logical cell also needs its pin order and evaluation in
`tritflow/synth/simulate.py` (`CELL_INPUTS`, `evaluate_netlist`), its SPICE pin
order in `tritflow/sim/spice.py:CELL_PINS`, its characterization reference in
`tritflow/sim/characterize.py:logic_value`, and a mapping rule in
`tritflow/synth/mapping.py:Mapper`. If exposed as an HDL primitive, extend
`tritflow/hdl/parser.py:GRAMMAR` and `tritflow/hdl/elaborate.py:Elaborator.items`.
Add its function to `tritflow/sta/logic.py` and characterize its transition
classes before using STA; add a schematic symbol in `tritflow/schematic/render.py`
when the cell needs a new drawing.

Check the truth function independently, then drawing DRC, strict LVS, DC
levels, loaded transients and row abutment. Use the private library for trial
routing and extracted simulation before replacing the distributed cell views.
Existing-device assumptions in the extraction decks need review if a new cell
introduces a different device type.

### Add an operator

First consider a reusable HDL module composed of the existing trit operations.
For new syntax, extend `tritflow/hdl/parser.py:GRAMMAR` and
`tritflow/hdl/elaborate.py:Elaborator.expression`, define evaluation in
`tritflow/hdl/ir.py:Design.evaluate`, and add explicit constant-folding and
rewrite behavior in `tritflow/synth/optimize.py`. Map the operator to existing
cells in `tritflow/synth/mapping.py:Mapper.map`; a new physical cell requires
the additional steps above.

Exhaust all trit combinations for the small operator and check the source,
optimized graph and mapped cells against an independent definition. Add
diagnostic tests for invalid uses and test each rewrite over the ternary
domain before enabling it. Boolean identities do not automatically hold for
the middle level.

Run the affected regressions, then the relevant native checks:

```sh
python3 -m pytest tests/hdl tests/synth -q
python3 -m pytest tests/cells tests/pnr tests/sim tests/extract -q
python3 -m pytest tests/sta tests/schematic -q
```

Keep the input plan, tool/PDK revisions and failed as well as passing results
with a new example so another designer can repeat the comparison.
