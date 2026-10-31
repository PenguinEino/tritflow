## 1. First Circuit: `a & ~a` to GDS

This chapter runs `a & ~a`, a small circuit that already behaves in a distinctly ternary way, through the whole TritFlow flow in one pass: HDL description, logic synthesis, place and route, DRC/LVS and post-layout SPICE simulation. Later chapters explain each stage in turn.

In binary logic, ANDing an input a with its inverse, `a & ~a`, always gives false (0), so the circuit collapses into a constant tied to ground. Balanced ternary logic behaves differently.

As the table below shows, balanced-ternary AND takes the smaller of its two inputs (min), and negation (NOT, `~`) flips the sign (+1 ↔ −1, 0 ↔ 0). When a is +1 or −1, the output is the minimum, −1. When a = 0 (0 V), ~a is also 0, so 0 & 0 gives **0 (0 V)**. `a & ~a` is therefore not a constant but a genuine ternary circuit, with its own middle-level output for a = 0.

<!-- tables: and -->

### 1.1 HDL Description (TritVerilog)

First, the circuit is written in TritVerilog, TritFlow's dedicated HDL. Ternary signals are declared with the type `trit`, and an `assign` statement describes the AND `&` and the negation `~`.

<!-- code: source -->

### 1.2 Logic Synthesis

The synthesizer parses the HDL and converts it into a netlist of ternary standard cells. It maps the ternary expression directly onto ternary cells, here INV for negation and NAND for negated AND. At the same time, it evaluates every input pattern (here the three values a = −1, 0, +1) and checks automatically that the netlist matches the original HDL exactly.

<!-- code: hdl -->

### 1.3 Place and Route

The placer arranges the cells of the synthesized netlist according to the TR-1um design rules, and the router connects them on two metal layers (M1/M2). The cells sit side by side so that the three power rails running through them (from the top, VDD = +5 V, VMID = 0 V, VSS = −5 V) abut without gaps, and the signal wires stay short.

<!-- code: pnr -->

### 1.4 DRC and LVS

The PDK's official KLayout decks check whether the finished layout meets the fab's manufacturing rules. DRC (Design Rule Check) looks for design-rule violations, and LVS (Layout Versus Schematic) checks that the transistor connections extracted from the layout match the synthesized netlist. Both run automatically; check that both pass with zero errors.

<!-- code: check -->

### 1.5 Post-Layout Simulation

The flow estimates wire capacitance from the layout geometry, writes a SPICE netlist with the actual transistor dimensions and runs a transient analysis in ngspice. As input a steps through −5 V → 0 V → +5 V → 0 V → −5 V, the interactive waveforms show the output settling into the ±0.5 V acceptance band around its target level (−5 V, 0 V or +5 V), along with the voltage of each internal node.

<!-- code: spice -->

That completes one pass from ternary HDL to manufacturable GDS, with a functional check. The figure below summarizes the whole pipeline and the inputs and outputs of each stage.

<!-- figure: fig_flow_map -->
