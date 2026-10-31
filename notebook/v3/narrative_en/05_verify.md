## 5. Verification and Timing

This chapter checks the dot-product GDS from chapter 4 with the PDK's official physical-verification decks, then evaluates its function and speed by post-layout simulation that includes wire capacitance. It also compares a ternary static timing analysis (STA), which estimates delay without SPICE, against SPICE.

### 5.1 DRC and LVS

The official KLayout decks of the OpenSUSI TR-1um PDK check whether the finished layout meets the manufacturing rules of Tokai Rika's fab.

1. **DRC (Design Rule Check)**: checks for violations of geometric rules such as minimum wire width, minimum spacing, minimum area and enclosure.
2. **LVS (Layout Versus Schematic)**: extracts the transistor connectivity (netlist) from the GDS and compares it with the netlist from logic synthesis, covering not only the device connections but also the connections to the power rails (VDD/VMID/VSS).

<!-- code: verify5 -->

### 5.2 Extraction and Wire Capacitance

The current OpenSUSI TR-1um PDK has no official deck for parasitic extraction (PEX). TritFlow therefore estimates each net's wire capacitance to the substrate from the wiring geometry of the LVS-matched GDS.

The estimate takes the area and perimeter of the M1 and M2 shapes and computes the wire capacitance from the following assumed values, which are not calibrated against the PDK.

- relative permittivity of the insulator (SiO<sub>2</sub>): 3.9
- height above the substrate: 1 µm for M1, 2 µm for M2
- fringe capacitance at wire edges: 0.02 fF/µm for both layers

Coupling capacitance between wires and wire resistance are ignored, and each net's capacitance is added to the SPICE netlist as a lumped capacitor.

<!-- code: extract5 -->

### 5.3 Ternary Delay

In binary integrated circuits, propagation delay is usually measured at the moment the output crosses half the supply voltage.

**This definition does not work for ternary circuits**, because the midpoint of the supply, 0 V (VMID), is itself the voltage of logic 0. When an output switches from −1 (−5 V) to +1 (+5 V), for example, the waveform always passes near 0 V on the way. Measuring at the midpoint crossing would declare the transition finished while it is still in progress.

TritFlow therefore defines delay as **settling time**.

> **Ternary delay**: the time from when the input starts to change until the output enters the acceptance band (±0.5 V) around its final target voltage (−5 V, 0 V or +5 V) and stays there.

The cell below fixes the dot-product circuit's weights at w = (+1, −1, +1, +1) and runs post-layout simulation while input x steps through a sequence that produces carries. This mirrors inference, in which trained weights are fixed. Arrows on the waveforms mark the settling time of each output's slowest transition.

<!-- code: spice5 -->

### 5.4 Ternary STA

Binary STA has only two transitions to consider, rising and falling. Ternary logic has three states and therefore six transitions (−1 → 0, −1 → +1, 0 → −1, 0 → +1, +1 → −1 and +1 → 0), and a cell's propagation delay differs for each.

TritFlow's ternary STA looks up, for each cell, tables of propagation delay and output slew measured with SPICE and indexed by input transition type, input slew and output load capacitance.

- **Stage propagation delay**: the time between the input's midpoint crossing (halfway between the voltages before and after the transition) and the output's midpoint crossing, summed stage by stage.
- **Settling at the output**: at the final output stage, the time from the midpoint crossing until the output enters the ±0.5 V acceptance band is added, so the result matches the settling time defined in section 5.3.

The INV table for an input slew of 1 ns is shown below.

<!-- code: table5 -->

INV has one input, so its table has six rows. Two-input cells such as NAND and NANY have one table for each value of the other input, plus one for both inputs switching together. STA estimates and SPICE are then compared for the same input sequence as in section 5.3.

<!-- code: sta5 -->
