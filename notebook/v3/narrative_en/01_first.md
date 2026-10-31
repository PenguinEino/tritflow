## 1. First Circuit: `a & ~a` to GDS

This chapter takes `a & ~a`, a compact logic circuit that still shows what is characteristic of ternary logic, through TritFlow's whole flow (from the HDL description through logic synthesis, place and route, DRC/LVS and post-layout SPICE simulation) in one pass. Later chapters explain each stage in detail, one by one.

In binary logic, the AND of an input a and its inverse, `a & ~a`, is always false (0), and the circuit degenerates into a constant tied to ground. In balanced ternary logic, it does not.

As the table below shows, balanced-ternary AND is defined as the smaller of two values (min), and negation (NOT, `~`) swaps the sign (+1 ↔ −1, 0 ↔ 0). When a is +1 or −1, the output is the minimum, −1. When a = 0 (0 V), ~a is also 0, so 0 & 0 outputs **0 (0 V)**. `a & ~a` is therefore not a constant: it is a real ternary circuit that outputs its own middle voltage for the input a = 0.

<!-- tables: and -->

### 1.1 HDL description (TritVerilog)

First, the circuit is described in TritVerilog, TritFlow's dedicated HDL. Ternary signals are declared with the type `trit`, and the assignment `assign` describes the AND `&` and the negation `~`.

<!-- code: source -->

### 1.2 Logic synthesis

The HDL description is parsed and converted into a netlist of ternary standard cells. TritFlow's logic synthesizer maps the ternary expression directly onto ternary cells (here, INV for negation and NAND for negated AND). At the same time, it evaluates every input pattern (here the three values a = −1, 0, +1) and automatically checks that the synthesized netlist matches the original HDL exactly.

<!-- code: hdl -->

### 1.3 Place and route

From the synthesized gate netlist, the cells are placed automatically following the TR-1um PDK design rules and connected on two routing layers (M1/M2). The cells are lined up so that the three power rails running horizontally through them (from the top, VDD = +5 V, VMID = 0 V, VSS = −5 V) abut without gaps, and the signal wires are routed over short distances.

<!-- code: pnr -->

### 1.4 DRC and LVS

The PDK's official KLayout decks check whether the finished layout meets the fab's manufacturing rules. DRC (Design Rule Check) looks for design-rule violations, and LVS (Layout Versus Schematic) checks that the transistor connections extracted from the layout match the synthesized netlist. Both run automatically; check that both pass with zero errors.

<!-- code: check -->

### 1.5 Post-layout simulation

Wire capacitance is estimated from the layout geometry, a SPICE netlist written with the actual transistor dimensions is generated, and ngspice runs a transient analysis. As input a steps through −5 V → 0 V → +5 V → 0 V → −5 V, the interactive waveforms show the output settling into the acceptance band (±0.5 V) around its target level (−5 V, 0 V, +5 V), together with the voltage of each internal node.

<!-- code: spice -->

This completes one pass from ternary HDL to manufacturable GDS and its functional check. The figure below summarizes the whole pipeline and the inputs and outputs of each stage.

<!-- figure: fig_flow_map -->
