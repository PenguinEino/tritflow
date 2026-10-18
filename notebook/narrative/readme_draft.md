# TritFlow: balanced-ternary HDL to GDS

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)]({release.colab_url})

TritFlow turns a Verilog-like description of balanced-ternary arithmetic into
a routed layout, drawing-DRC and LVS results, and extracted ngspice waveforms
on [OpenSUSI TR-1um](https://github.com/OpenSUSI/TR-1um). Follow an adder from
signed digits to transistors, then edit the HDL and run the same flow on
your circuit.

![Ternary HDL mapped to cells, routed GDS and extracted waveforms.](figures/out/fig_flow.png)

The illustrated {paper_adder.width}-trit adder uses {paper_adder.cells} cells
in a {paper_adder.die_um} µm layout, with {paper_adder.drc_items} drawing-DRC
markers and LVS {paper_adder.lvs_status}. The top-level HDL contains
{paper_adder.hdl_lines} lines and reuses the included half-adder and
full-adder modules.

## Run and explore

Open the notebook in Colab and select **Runtime → Run all**. Setup installs
the tools, fetches the pinned public PDK and prints the resolved source
revision. The notebook builds an opening adder and an editable example;
larger characterization and width/load studies use explicitly labelled
recorded results.

**Clean-Colab verification:** {evidence.colab_status}

Start with the [notebook](notebook/tritflow_tr1um.ipynb), or read the
[local setup and rerun instructions](notebook/README.md). The
[example circuits](examples/README.md) include adders, multipliers,
comparison, sign detection and a min/max sorter. The
[paper figures](figures/README.md) connect the device behavior to the physical
and electrical results.

## What the notebook teaches

A trit represents a negative, zero or positive digit. In this implementation
the ideal voltages are {levels.negative_v}, {levels.zero_v} and
{levels.positive_v} V. The gate functions are sign inversion, negative minimum,
negative maximum and negative saturated addition. Synthesis uses identities
that hold for these trits and checks the mapped cells against the source.

The middle voltage has an electrical cost. The inverter's conducting resistor
branches draw current with constant inputs; sizing changes level accuracy and
that current together. A divider estimate explains the device behavior, and
a single-adder-slice estimate predicts how carry settling grows with width.
The measured adder series gives {scaling.power_per_cell_mw} mW per mapped cell
for its tested-state DC-power maxima, reaching {scaling.max_power_mw} mW at
{scaling.selected_n} trits.

## What you can reuse

- A ternary HDL with parameters, vectors, module instances and generate loops,
  plus synthesis to a checked cell netlist and SPICE.
- A standard-cell library with GDS, physical abstracts, source and extracted
  circuits, truth tables and characterization.
- Placement and two-metal routing with three-rail power delivery, PDK drawing
  DRC and strict device/connectivity LVS.
- Extracted-device simulation, estimated wire capacitance, independent
  arithmetic checks and native reports for each generated design.

The core API follows the physical flow:

```python
from tritflow import flow

design = flow.load("examples/adder.tv", "adder", {"N": 2})
net = design.synthesize()
layout = net.place_and_route()
assert layout.drc()["clean"]
assert layout.lvs()["matched"]
```

The notebook supplies the input order, integer reference and stimulus for
`layout.extract().simulate(...)` so the analog result checks the intended
arithmetic as well as its voltage levels.

## Physical basis and scope

The author designed and taped out the
[reference ternary cells](https://github.com/PenguinEino/opensusi-tr10-balanced-ternary-logic)
in {history.tapeout_year}. Their expected return in {history.delivery_month}
provides the next experiment: measured DC levels, rail currents and settling
under matched bias and loading. Silicon has not yet been measured.

Reported electrical results use nominal models and their stated input
sequences. Added wire capacitance is an uncalibrated geometry estimate;
signal-wire resistance and coupling are omitted. Drawing DRC and LVS do not
establish pad, ESD, package or lifetime qualification. The notebook's scope
appendix and evidence tables give the full conditions and rerun instructions.

## Author

- Name: Einosuke Okazaki (岡崎 英之介)
- Affiliation: Information and Communication Engineering Course, Department of Monozukuri
  Engineering, Tokyo Metropolitan College of Industrial Technology (KOSEN), Tokyo, Japan
- Status: Fifth-year student (final year of the five-year KOSEN engineering programme, which
  combines upper-secondary and the first two years of tertiary education)
- Email: einosukeokazaki@gmail.com
- GitHub: PenguinEino

Prepared for the IEEE SSCS Code-a-Chip Travel Grant, ISSCC 2027.

## License

TritFlow and the author's derived schematic illustrations are released under
[Apache-2.0](LICENSE). See [NOTICE](NOTICE) for attribution. OpenSUSI TR-1um
retains its own Apache-2.0 license and notices.
