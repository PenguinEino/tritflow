## 6. Evaluation and Reuse

Chapter 5 verified the four-term dot product dot4 with post-layout simulation and compared it with ternary STA. This chapter evaluates area, delay and static power as the term count changes, then reruns the flow after an HDL change and generates a shuttle top-level layout.

### 6.1 Dot-Product Size and Area

The evaluated circuit is a dot product of one-trit weights and inputs, y = w<sub>0</sub>x<sub>0</sub> + … + w<sub>N−1</sub>x<sub>N−1</sub>. The output uses the minimum number of trits needed to represent −N through +N. Weights remain HDL inputs but are fixed in simulation to repetitions of (+1, −1, +1, +1). Addition uses the same HDL form as section 3.7, without structural changes for different term counts.

The tables present recorded place and route and verification results. Area is measured from the routed die outline.

<!-- code: scale6 -->

### 6.2 Static and Time-Average Power

States that hold 0 V by resistive division draw static current even without input transitions. NANY also has zero-output states in which VMID clamps conduct while the VDD and VSS transistor stacks are cut off. Static power is calculated from DC operating points for states in the recorded input sequence.

Time-average supply power excludes the power from the input voltage sources.

<!-- code: power6 -->

### 6.3 STA and SPICE

Each circuit uses an input sequence that generates and clears positive and negative carries. The four-term sequence differs from chapter 5. STA uses the same fixed weights. STA and SPICE use identical input transitions, output load, input slew and wire capacitance. The reported delay is each output's maximum settling time over that sequence.

The effect of wire capacitance is evaluated by removing only the estimated wire capacitance from the same extracted circuit. STA compares both cases at every size; SPICE compares them for four terms. Both cases retain intrinsic device capacitance and the 100 fF output load.

At N=16, some NANY loads exceed the 2 pF characterization limit, reaching 2.862 pF, so STA linearly extrapolates the delay along the load axis.

<!-- code: timing6 -->

### 6.4 Editing HDL and Rerunning the Flow

Making inference weights HDL constants allows logic synthesis to simplify the corresponding multiplier circuits. The following circuit fixes dot4's weights to (+1, −1, +1, +1). After changes to the expression and port declarations, the same execution cell runs logic synthesis through post-layout simulation.

<!-- code: reuse_source -->

SPICE covers all states when the total is at most 27. Otherwise, it selects 11 states from the zero input, all −1 and all +1 inputs, alternating signs, and single-input ±1 excursions. Expected outputs come from evaluating the HDL, independently of the synthesized netlist.

<!-- code: reuse6 -->

### 6.5 Shuttle Top-Level Layout

The top-level layout adds pads, power routing and the PDK's stock MPW frame to the dot4 routed in chapter 4; it is generated here and verified with DRC, LVS and the organizer's precheck. The frame's electrostatic discharge (ESD) supply shares VSS with the circuit's VSS (−5 V) and takes VDD at +5 V from a separate terminal. The −5 to +5 V ternary signals then stay within the ESD supply range, so the stock pads are used as they are. The taped-out chip uses the same connection.

<!-- code: shuttle6 -->

### 6.6 Conclusion

This notebook demonstrated TritFlow, an automated design flow for ternary integrated circuits, on OpenSUSI TR-1um, an open-source PDK released by a commercial semiconductor fab in Japan.

- **A pipeline from a dedicated ternary HDL to GDS**: from a TritVerilog description, the flow runs logic synthesis with simplification by ternary identities, two-metal place and route, GDS output, DRC/LVS with the PDK's official decks, wire-capacitance estimation and post-layout simulation in one pass.
- **A ternary timing model and STA**: delay is defined from the six state transitions and settling time, and a ternary static timing analysis that estimates delay without SPICE was built and compared with post-layout SPICE.
- **A link to real silicon**: the standard cells keep the circuits and device sizes of the taped-out design, so they can be compared directly with measurements of the chips arriving in January 2027. A full-chip layout for the MPW shuttle is also generated automatically and passes DRC, LVS and the organizer's precheck.

TritFlow is a first step toward learning balanced-ternary logic circuits that may be applied to ternary computation such as BitNet. All source code, the cell library and the design flow are released under Apache-2.0, giving researchers and students interested in ternary circuits a starting point for trying their own designs. We hope that this work, which completes the cycle from design to fabrication and measurement on TR-1um and the OpenSUSI shuttles, Japan's open-source semiconductor infrastructure, helps open-source chip design grow in Japan.
