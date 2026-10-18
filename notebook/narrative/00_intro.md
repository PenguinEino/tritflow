# TritFlow: balanced-ternary HDL to GDS on OpenSUSI TR-1um

TritFlow turns balanced-ternary HDL into checked GDS and extracted SPICE
waveforms on Japan's [OpenSUSI TR-1um](https://github.com/OpenSUSI/TR-1um).
Its library adapts the [author's taped-out ternary cells](https://github.com/PenguinEino/opensusi-tr10-balanced-ternary-logic).
**Choose Runtime → Run all** to follow an adder from its middle-voltage
divider to layout, then edit your own circuit.

The reference cells were taped out in {history.tapeout_year}; silicon is
expected in {history.delivery_month} and has not yet been measured.

<!-- teaser caption: teaser.md; use the opening static hero once -->

## 0. From HDL to a checked adder layout

The paper figure shows a {paper_adder.width}-trit ripple adder; the executable
example builds a {adder.width}-trit version. Run the short API chain, then
inspect the generated layout and the most significant sum digit and carry.

<!-- figure: ch0 -->
<!-- hero: fig_flow; caption: captions.md#fig_flow -->

![TritVerilog, mapped cells, three-rail NANY, routed adder and extracted waveforms.](../../figures/out/fig_flow.png)

A trit takes the values −1, 0 and +1. Here their voltages are
{levels.negative_v}, {levels.zero_v} and {levels.positive_v} V. A trit is a
signal type of its own; Verilog's `x` and `z` are not extra trit values.
The waveform's shaded bands show the allowed error around each target level.

> **What this shows.** The HDL, mapped cells, extracted connections and
> waveforms describe the same arithmetic. The shaded voltage bands connect
> each signed output trit to its physical acceptance check.

Next, we open one of those cells and explain how it makes the middle voltage.
