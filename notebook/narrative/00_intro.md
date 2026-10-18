# TritFlow: balanced-ternary HDL to GDS on OpenSUSI TR-1um

TritFlow turns a Verilog-like description of balanced-ternary arithmetic into
cells, routed GDS, DRC/LVS results and transistor-level waveforms. Start with
an adder, follow its middle voltage back to the devices, then change the HDL
and run the same flow on your circuit.

[OpenSUSI TR-1um](https://github.com/OpenSUSI/TR-1um) is an NDA-free
{history.node_um} µm CMOS PDK from Japan, opened in {history.pdk_opened_year},
based on Tokai Rika's process and distributed under Apache-2.0.
The author designed the [reference ternary cells](https://github.com/PenguinEino/opensusi-tr10-balanced-ternary-logic)
and taped them out in {history.tapeout_year}; silicon is expected in
{history.delivery_month} and has not yet been measured. TritFlow adapts those
designs into a reusable standard-cell library and a Colab design flow.

<!-- figure: teaser; caption comes from teaser.md -->

## 0. From HDL to a checked adder layout

The {adder.width}-trit ripple adder below starts from {adder.hdl_lines} lines
of top-level HDL plus shared half-adder and full-adder modules. Run the cell to
synthesize it, place and route real cells, compare layout connectivity with the
schematic, and simulate the extracted circuit. Watch the carry and the most
significant sum digit as the inputs change.

<!-- figure: ch0 -->

*Choose an adder width to inspect its layout and results. The default width
also runs through the flow in this session.*

A trit takes the values −1, 0 and +1. Here their voltages are
{levels.negative_v}, {levels.zero_v} and {levels.positive_v} V. A trit is a
signal type of its own; Verilog's `x` and `z` are not extra trit values.
The waveform's shaded bands show the allowed error around each target level.

> **What this shows.** The selected adder uses {adder.cells} cells in a
> {adder.die_um} µm layout: {adder.drc_items} drawing-DRC markers and LVS
> {adder.lvs_status}. Logic passes {adder.logic_mode} testing over
> {adder.logic_vectors} input vectors;
> {adder.analog_states} distinct states are visited in the analog sequence,
> whose output checks {adder.analog_status} at {adder.load_ff} fF per output.

Next, we open one of those cells and explain how it makes the middle voltage.
