## 1. First Circuit: `a & ~a` to GDS

This chapter runs a small ternary circuit, `a & ~a`, from HDL through GDS and post-layout simulation to introduce the complete TritFlow flow. Chapters 2 onward examine the stages in detail.

In binary logic, `a & ~a` is false for every value of a. In ternary logic, it is not.

<!-- tables: and -->

The circuit is written in TritFlow's HDL, TritVerilog, as follows.

<!-- code: source -->

Logic synthesis maps the ternary expression directly to ternary cells and checks equivalence to the HDL over all input combinations.

<!-- code: hdl -->

Place and route uses a router developed for ternary cells. It preserves the three power rails through each cell (VDD, VMID and VSS) and routes on the two metal layers of TR-1um, M1 and M2.

<!-- code: pnr -->

DRC and LVS use the official PDK decks.

<!-- code: check -->

Post-layout simulation includes wire capacitance estimated from the GDS. A ternary testbench checks whether the output reaches the band within ±0.5 V of its ideal voltage (−5/0/+5 V) in each interval. Net values and waveforms are shown for each input.

<!-- code: spice -->

The flow is summarized below.

<!-- figure: fig_flow_map -->

This completes the first pass through the flow. The following chapters examine its design, starting in chapter 2 with the most basic cell, INV.
