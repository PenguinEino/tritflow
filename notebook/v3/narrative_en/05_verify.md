## 5. Verification and Timing

This chapter verifies the GDS from chapter 4 against PDK rules and checks function and delay with post-layout simulation. It then compares ternary static timing analysis, which estimates delay without simulating the circuit in SPICE, against SPICE. The circuit remains the dot4 dot product.

### 5.1 DRC and LVS

Verification uses the official PDK DRC and LVS decks. For LVS, KLayout extracts devices and connectivity from the GDS and compares them with the synthesized netlist.

<!-- code: verify5 -->

### 5.2 Extraction and Wire Capacitance

The TR-1um PDK has no parasitic extraction (PEX) rules. TritFlow therefore extracts a device netlist from the LVS-matched GDS, then estimates each net's wire-to-substrate capacitance from its M1 and M2 area and perimeter. The coefficients are not calibrated to the PDK. They assume an oxide relative permittivity of 3.9, heights above the substrate of 1 µm for M1 and 2 µm for M2, and a perimeter fringe capacitance of 0.02 fF/µm. Wire-to-wire coupling capacitance and wire resistance are excluded.

<!-- code: extract5 -->

### 5.3 Ternary Delay

Binary delay is often measured at the output crossing of half the supply voltage. For ternary logic, this midpoint is the 0 level itself, and a transition from −1 to +1 also passes through it, so this definition is unsuitable. TritFlow defines delay as the time from the start of an input transition until the output enters and remains within ±0.5 V of its new target level.

The weights are fixed at w = (+1, −1, +1, +1), and x follows a sequence that produces carries in the sum. This corresponds to inference with fixed trained weights and changing inputs. Simulation uses the netlist with wire capacitance added. An arrow marks the delay of the slowest transition at each output.

<!-- code: spice5 -->

### 5.4 Ternary STA

Binary STA distinguishes two transitions, rising and falling. Ternary logic has six directed transitions between −1, 0 and +1, with different cell delays for each.

TritFlow's ternary STA uses SPICE-characterized tables of propagation delay and output slew for each cell, indexed by input transition type, input slew and load capacitance. Propagation delay is the time difference between input and output crossings of the midpoints between their respective initial and final levels. At circuit outputs, the time from the midpoint crossing to entry into the ±0.5 V band is added, matching the delay definition in section 5.3. The INV table below uses an input slew of 1 ns.

<!-- code: table5 -->

INV has one input, so its table has six transition rows. Two-input cells have tables for each value of the other input and for simultaneous transitions on both inputs. STA and SPICE are compared using the input sequence from section 5.3.

<!-- code: sta5 -->
