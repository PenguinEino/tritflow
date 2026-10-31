## 5. Verification and Timing

This chapter verifies the GDS from chapter 4 against PDK rules and checks function and delay with post-layout simulation. It then compares ternary static timing analysis, which estimates delay without simulating the circuit in SPICE, against SPICE. The circuit remains the same dot-product circuit.

### 5.1 DRC and LVS

The GDS is verified with the PDK's official DRC and LVS decks (KLayout).

1. **DRC**: checks for violations of design rules such as minimum width, spacing, area and enclosure.
2. **LVS**: KLayout extracts devices and their connections from the GDS and compares them with the synthesized netlist, including the connections to the power rails (VDD, VMID and VSS).

<!-- code: verify5 -->

### 5.2 Extraction and Wire Capacitance

The TR-1um PDK has no parasitic extraction (PEX) rules. TritFlow therefore extracts the device netlist from the LVS-matched GDS and adds wire-to-substrate capacitance estimated from the M1 and M2 area and perimeter of each net. The coefficients are not calibrated against the PDK; they assume the following values.

- oxide relative permittivity: 3.9
- height above the substrate: 1 µm for M1, 2 µm for M2
- fringe capacitance per perimeter length: 0.02 fF/µm

Wire-to-wire coupling capacitance and wire resistance are not included; each net's capacitance is added to the SPICE netlist as a lumped capacitor.

<!-- code: extract5 -->

### 5.3 Ternary Delay

Binary delay is usually measured when the output crosses half the supply voltage. This does not work for ternary logic. The midpoint of the supply, 0 V (VMID), is itself the voltage of logic 0, and an output going from −1 (−5 V) to +1 (+5 V) always passes near 0 V on the way. When it crosses the midpoint, the transition is still in progress.

TritFlow therefore defines delay as settling time.

> **Ternary delay**: the time from the start of the input change until the output enters the ±0.5 V acceptance band of its new value and stays there.

The weights are fixed to w = (+1, −1, +1, +1), and input x follows a sequence that generates carries in the sum. This matches inference with trained weights fixed while inputs stream through. The netlist with wire capacitance is simulated, and arrows mark the delay of the slowest transition for each output.

<!-- code: spice5 -->

### 5.4 Ternary STA

Binary STA distinguishes two transitions, rising and falling. Ternary logic has six transitions, −1 → 0, −1 → +1, 0 → −1, 0 → +1, +1 → −1 and +1 → 0, and cell delay differs for each.

TritFlow's ternary STA uses, for each cell, SPICE-characterized tables of propagation delay and output slew indexed by input transition type, input slew and load capacitance.

- **Stage propagation delay**: the time between the input and output crossing the midpoints between their initial and final levels.
- **Settling at outputs**: at circuit outputs, the time from the midpoint crossing to entering the ±0.5 V band is added, matching the delay definition in section 5.3.

The INV table below uses an input slew of 1 ns.

<!-- code: table5 -->

INV has one input, so its table rows are the six transitions. Two-input cells have a table for each value of the other input and a table for both inputs switching together. STA estimates and SPICE are compared for the same input sequence as in section 5.3.

<!-- code: sta5 -->
