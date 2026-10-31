## 2. Cells

The circuit in chapter 1 used two standard-cell types, INV and NAND. This chapter describes the standard cells behind TritFlow. It starts with INV to show how CMOS produces three voltage levels, then establishes which cells can build any ternary logic, and finally shows how the taped-out circuits became standard cells for place and route.

### 2.1 INV: Generating Three Levels

What sets the ternary INV apart from a binary inverter is that, to output 0 V, it turns on both the upper and lower MOS transistors and forms the middle level with a voltage divider.

TritFlow's INV places a PMOS, two diffusion resistors (PDK device RR) and an NMOS in series between VDD and VSS. Output Y is taken between the two resistors.

<!-- tables: inv -->

At an input of ±5 V, only one MOS transistor conducts, pulling Y to its rail. At an input of 0 V, both conduct, and the divider outputs 0 V. No rail supplies this 0 V; it comes solely from the balance of the upper and lower resistances, and static current flows the whole time.


#### SPICE Simulation

The figure shows a DC analysis with ngspice and the PDK models over 90 device sizings, including the taped-out one.

The taped-out sizing was chosen as a trade-off among middle-level accuracy, delay, area and static current. TritFlow's cells keep it unchanged so that they can be compared with measurements. The grid in the figure also contains sizings with both smaller error and smaller static current.

- **Target**: as the middle-level noise margin, an output within ±0.5 V for inputs from −1 to +1 V.
- **Gate length**: the minimum, 1 µm, for drive strength and area.
- **PMOS and NMOS widths**: at an input of 0 V, the output is 0 V when the upper on-resistance plus RR, r<sub>on,P</sub> + R<sub>RP</sub>, equals the lower r<sub>on,N</sub> + R<sub>RN</sub>. Holes are less mobile than electrons, so the PMOS is made wider than the NMOS to bring their on-resistances closer and reduce the output offset.
- **RR width**: the minimum, 2.8 µm.
- **RR length**: 30 µm, to keep the static current of the whole taped-out chip within the current limits of the power wires and vias. The MOS dimensions were left as they were before RR was lengthened, so an offset of a few tens of mV remains at an input of 0 V, well within the ±0.5 V acceptance band.

The adopted PMOS and NMOS widths are 13.5 µm and 5 µm. The PDK's zero-bias resistance equation gives 10.835 kΩ for each RR. Approximating each MOS as a linear resistor from its mobility, oxide thickness and threshold voltage gives r<sub>on,P</sub> = 0.492 kΩ and r<sub>on,N</sub> = 0.399 kΩ. Each RR is 22.0 and 27.2 times larger, respectively, so the zero level is set by the ratio of two identically shaped resistors rather than by MOS variation. With R<sub>u</sub> = r<sub>on,P</sub> + R<sub>RP</sub> above Y and R<sub>d</sub> = r<sub>on,N</sub> + R<sub>RN</sub> below it, the divider gives

$$V_Y = V_{SS} + (V_{DD}-V_{SS})\frac{R_d}{R_u+R_d} \simeq -0.021\ \mathrm{V},\qquad I = \frac{V_{DD}-V_{SS}}{R_u+R_d} \simeq 0.443\ \mathrm{mA}$$

SPICE gives −0.040 V and 0.407 mA; the difference comes from the approximation ignoring the voltage and substrate-bias dependence of RR and the nonlinearity of the MOS transistors.

<!-- code: inv -->

### 2.2 Completeness: Which Cells Build Any Ternary Logic

Logic synthesis rewrites the logic written in HDL as a combination of the available cells. For this to work for any logic, the cell set must be **functionally complete**: wiring its cells together must be enough to build every logic function. In binary logic, NAND alone is complete.

In ternary logic, two cells are enough: NANY, below, and the constant cell TIEP.

- **NANY**: a two-input cell defined in TritFlow. It clips the sum of its inputs to the range −1 to +1, then negates it. NANY(a, b) = −sat(a + b)
- **sat**: the function that clips to the range −1 to +1. sat(x) = max(−1, min(+1, x))
- **TIEP, TIEZ, TIEN**: constant cells that output +1, 0 and −1, named after the binary tie cells (TIEHI, TIELO). Either TIEP or TIEN is enough for completeness.

The proof rests on Słupecki's criterion (1939): a set of ternary functions is complete if it satisfies both of the following conditions.

1. It can build every one-input (unary) function. Since the output can be chosen independently for each of the three values of a (−1, 0, +1), there are 3 × 3 × 3 = 27 unary functions, and all 27 must be generated.
2. It can build at least one essential two-input function: a function of a and b that depends on both (with either input fixed, changing the other can change the output) and takes all three output values, −1, 0 and +1.

NANY satisfies condition 2 by itself. Since NANY(a, 0) = −a, any change in a appears directly at the output, and the same holds for b by symmetry. Its output also takes all of −1, 0 and +1.

For condition 1, the code starts from just the input variable a and the constant +1, feeds the outputs of the functions found so far back into NANY inputs, and checks exhaustively that all 27 unary functions appear. The table below shows how the set of generated functions grows with NANY logic depth.

<!-- code: closure -->

Why does NANY need a constant cell? Since NANY(0, 0) = −sat(0 + 0) = 0, when every input is 0 (0 V), any network of NANY cells keeps outputting 0 and can never produce anything else. A single nonzero constant removes this limit. With +1 from TIEP, for example, NANY(+1, +1) = −1 and NANY(+1, −1) = 0 give the other constants, so one constant cell is enough.

### 2.3 Standard-Cell Library

The standard cells TritFlow provides are listed below. The four main logic gates, INV, NAND, NOR and NANY, are exactly the circuits taped out on OpenSUSI-TR10. NAND and NOR are not needed for completeness, but they reduce the logic depth of the netlist and so improve area and delay. The library also has a buffer, BUF (two INV stages in series), for driving high-fanout signals, and the constant cells TIEP, TIEZ and TIEN.

In the schematic symbols, the open circle at an output means negation (NOT), and NAND and NOR keep their familiar binary shapes. NANY has its own symbol, which combines a summing block (Σ) with saturation and negation.

<!-- code: cells -->

### 2.4 Standard-Cell Layout

Automatic place and route (P&R) only works if every cell follows strict geometric rules. All cells in TritFlow's library share a row height (cell height) of **132 µm** and a placement and routing grid pitch of **6 µm**.

Three first-metal (M1) power rails run horizontally through each cell, from the top **VDD (+5 V, 8 µm wide)**, **VMID (0 V, 4 µm wide)** and **VSS (−5 V, 4 µm wide)**. Placing cells side by side without gaps is enough to connect the power rails and the N-well continuously. The input and output pins are M1 landings on the routing grid, so second-metal (M2) wires crossing over them can reach them easily through vias (V1). Cells can be placed in their normal orientation (R0) or mirrored left to right (MY).

<!-- code: stdcells -->
