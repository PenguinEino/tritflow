## 6. Evaluation and Applications

Chapter 5 verified the four-term dot-product circuit with post-layout simulation and ternary STA. This chapter first evaluates area, delay and static power as the number of terms N changes. It then reruns the same flow after changing the HDL, and finally generates a top-level layout with the MPW frame and I/O pads.

### 6.1 Dot-Product Size and Area

The test circuit is the dot product of ternary weights and inputs, y = w<sub>0</sub>x<sub>0</sub> + … + w<sub>N−1</sub>x<sub>N−1</sub>, with N = 2, 4, 8 and 16 terms.

The output y uses the minimum number of digits that represents −N through +N (2 trits for N = 2 and 4, 3 trits for N = 8, 4 trits for N = 16). The weights remain HDL inputs but are fixed in simulation to repetitions of (+1, −1, +1, +1). Addition is synthesized from the same HDL form as section 3.7, without structural changes for different term counts.

The cell below shows the recorded place-and-route and verification results for each size. Area is computed from the outline of the routed die.

<!-- code: scale6 -->

### 6.2 Static and Time-Average Power

Ternary CMOS logic gates draw static current, even without input transitions, in states where a resistive divider holds 0 V. NANY cells also have states in which the series MOS paths to VDD and VSS are cut off and a clamp to VMID outputs 0 V.

Static power is obtained with SPICE from the DC operating points of the states in the recorded input sequence. The time-average supply power excludes the power from the input voltage sources.

<!-- code: power6 -->

### 6.3 STA and SPICE

For each size, with the weights fixed, an input sequence that creates and clears positive and negative carries is applied, and the delay predicted by ternary STA is compared with the transient delay from SPICE. The four-term sequence differs from chapter 5. STA and SPICE receive the same input transitions, input slew, output load and wire capacitance. The compared delay is each output's maximum settling time over the sequence.

The effect of wire capacitance on delay is also compared. Device parasitics and the 100 fF output load are kept in both cases, and only the estimated wire capacitance is removed. STA is compared at every size and SPICE at four terms.

In the 16-term circuit, some NANY loads exceed the characterization table's upper limit (2 pF), reaching up to 2.862 pF, so STA linearly extrapolates the delay along the load axis.

<!-- code: timing6 -->

### 6.4 Editing HDL and Rerunning the Flow

Writing the inference weights as constants in the HDL lets logic synthesis simplify the multipliers according to the weights. The cell below rewrites the TritVerilog of the dot-product circuit from section 3.7 with its weights fixed to (+1, −1, +1, +1). Even with the expression and the input and output declarations changed, the same cell runs logic synthesis, place and route, DRC/LVS, wire-capacitance estimation and post-layout simulation in sequence.

<!-- code: reuse_source -->

The SPICE transient analysis checks every combination when there are at most 27 states, and otherwise 11 representative states, such as the zero input, all inputs at −1 or +1, alternating signs and single-input ±1 excursions. Expected outputs come from evaluating the HDL, not from the synthesized netlist.

<!-- code: reuse6 -->

### 6.5 Shuttle Top-Level Layout

To manufacture the designed ternary core in a real fab, I/O pads must be placed around the chip, and the design must be combined with the MPW (Multi-Project Wafer) stock frame, which has electrostatic discharge (ESD) protection devices.

This section generates a top-level layout that connects the dot-product circuit routed in chapter 4 to the OpenSUSI TR-1um stock MPW frame, and verifies it with DRC, LVS and the organizer's precheck.

What matters here is matching the ESD protection to the ternary supply voltages. The ESD protection devices of the stock pads conduct when a pad's voltage leaves the range of the ESD supplies (VDD and VSS). Ternary signals, on the other hand, span −5 V to +5 V, a total of 10 V.

TritFlow therefore connects the frame's ESD VSS to the circuit's VSS (−5 V) and supplies the ESD VDD with +5 V from a separate terminal. The −5 V to +5 V ternary signals then stay within the range of the ESD supplies, and the stock pads can be used as they are. This connection is the same as on the chip taped out in 2026, OpenSUSI-TR10.

<!-- code: shuttle6 -->

### 6.6 Conclusion

This notebook demonstrated TritFlow, an automated design flow for ternary integrated circuits, on OpenSUSI TR-1um, an open-source PDK released by a commercial semiconductor fab in Japan.

- **A pipeline from a dedicated ternary HDL to GDS**: from a TritVerilog description, the flow runs logic synthesis with simplification by ternary identities, two-metal place and route, GDS output, DRC/LVS with the PDK's official decks, wire-capacitance estimation and post-layout simulation in one pass.
- **A ternary timing model and STA**: delay is defined from the six state transitions and settling time, and a ternary static timing analysis that estimates delay without SPICE was built and compared with post-layout SPICE.
- **Validation by measurement**: the standard cells keep the circuits and device sizes of the taped-out design, so they can be compared directly with measurements of the chips arriving in January 2027. Because the flow also generates a full-chip layout for the MPW shuttle automatically, a circuit designed with TritFlow can be submitted to a shuttle as is, fabricated and checked by measurement.

TritFlow is a first step toward learning balanced-ternary logic circuits that may be applied to ternary computation such as BitNet. All source code, the cell library and the design flow are released under Apache-2.0, giving researchers and students interested in ternary circuits a starting point for trying their own designs. We hope that this work, which completes the cycle from design to fabrication and measurement on TR-1um and the OpenSUSI shuttles, Japan's open-source semiconductor infrastructure, helps open-source chip design grow in Japan.
