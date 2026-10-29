## 2. Cells

The circuit in chapter 1 used two standard-cell types, INV and NAND. This chapter examines the standard cells underlying TritFlow. It starts with INV to explain how CMOS produces three voltage levels, establishes which cells can implement arbitrary ternary logic, and describes how the taped-out circuits become standard cells for place and route.

### 2.1 INV: Generating Three Levels

Unlike a binary inverter, the ternary INV turns on both the upper and lower MOS transistors to generate 0 V by voltage division.

TritFlow's INV connects a PMOS, two diffusion resistors (PDK device RR) and an NMOS in series between VDD and VSS. Output Y is taken between the two resistors.

<!-- tables: inv -->

At an input of ±5 V, only one MOS transistor conducts, pulling Y to its rail. At an input of 0 V, both conduct, and the voltage divider outputs 0 V. No rail supplies 0 V to the output; it is established solely by the balance of the upper and lower resistances, with continuous static current.


#### SPICE Simulation

The DC analysis uses ngspice and the PDK models for 90 sets of dimensions, including the taped-out dimensions.

The taped-out dimensions trade off middle-level accuracy, delay, area and static current. TritFlow's cells keep these dimensions unchanged so that they can be compared with measurements. The grid in the figure also contains dimensions with both smaller error and smaller static current.

- **Target**: as the middle-level noise margin, an output within ±0.5 V for inputs from −1 to +1 V.
- **Gate length**: the minimum 1 µm, for drive strength and area.
- **PMOS and NMOS widths**: at an input of 0 V, the output is 0 V when the upper on-resistance plus RR, r<sub>on,P</sub> + R<sub>RP</sub>, equals the lower r<sub>on,N</sub> + R<sub>RN</sub>. Because hole mobility is lower than electron mobility, the PMOS is wider than the NMOS to bring their on-resistances closer and reduce the output offset.
- **RR width**: the minimum 2.8 µm.
- **RR length**: 30 µm, to keep the static current of the complete taped-out chip within the power-wire and via current limits. The MOS dimensions were retained when RR was lengthened, leaving an offset of several tens of mV at an input of 0 V, well within the ±0.5 V acceptance band.

The adopted PMOS and NMOS widths are 13.5 µm and 5 µm. The PDK's zero-bias resistance equation gives 10.835 kΩ for each RR. A linear MOS resistance approximation using mobility, oxide thickness and threshold voltage gives r<sub>on,P</sub> = 0.492 kΩ and r<sub>on,N</sub> = 0.399 kΩ. The RR-to-on-resistance ratios are 22.0 and 27.2, respectively, so the ratio of the two identically shaped resistors, rather than MOS variation, sets the zero level. With R<sub>u</sub> = r<sub>on,P</sub> + R<sub>RP</sub> above Y and R<sub>d</sub> = r<sub>on,N</sub> + R<sub>RN</sub> below Y, the divider gives

$$V_Y = V_{SS} + (V_{DD}-V_{SS})\frac{R_d}{R_u+R_d} \simeq -0.021\ \mathrm{V},\qquad I = \frac{V_{DD}-V_{SS}}{R_u+R_d} \simeq 0.443\ \mathrm{mA}$$

The difference from SPICE's −0.040 V and 0.407 mA follows from omitting RR voltage/substrate-bias dependence and MOS nonlinearity.

<!-- code: inv -->

### 2.2 Functional Completeness

Logic synthesis replaces HDL logic with combinations of library cells. To implement arbitrary logic, the cell basis must be **functionally complete**: connecting those cells must be sufficient to construct every logic function. In binary logic, NAND alone is complete.

In ternary logic, NANY and the constant cell TIEP, defined below, form a complete basis.

- **NANY**: a two-input cell defined in TritFlow. It clips the sum of its inputs to the range −1 to +1, then negates it. NANY(a, b) = −sat(a + b)
- **sat**: the function that clips to the range −1 to +1. sat(x) = max(−1, min(+1, x))
- **TIEP, TIEZ, TIEN**: constant cells that output +1, 0 and −1, named after the binary tie cells (TIEHI, TIELO). Either TIEP or TIEN suffices for completeness.

Słupecki's criterion (1939) establishes completeness for a ternary function basis satisfying both conditions below.

1. It can construct every unary function. Input a has three values, −1, 0 and +1, and each can map to any of three outputs, giving 3 × 3 × 3 = 27 unary functions.
2. It can construct a binary function f(a, b) that depends on both inputs (changing either input alone can change the output) and takes all three output values, −1, 0 and +1.

NANY itself satisfies condition 2. Since NANY(a, 0) = −a, changing a can change the output, and the same holds for b. Its output also takes all three values. Condition 1 is checked constructively: starting with input a and the +1 constant, repeatedly connect available functions to NANY inputs until no new function appears. The table lists functions constructed in the first few rounds. Depth counts NANY stages from a and the constant.

<!-- code: closure -->

NANY alone is not complete. Since NANY(0, 0) = 0, any network of NANY cells produces 0 when all inputs are 0. It cannot construct a function that produces a nonzero output at a = 0, or a +1 or −1 constant. Adding one nonzero constant removes this restriction. The remaining constants follow from NANY(+1, +1) = −1 and NANY(+1, −1) = 0, so only one constant-cell type is required. TritFlow uses this property to map arbitrary truth tables to cells.

### 2.3 Standard-Cell Library

The TritFlow standard cells are shown below. INV, NAND, NOR and NANY implement the taped-out circuits. INV, NAND and NOR are unnecessary for completeness but reduce the number of cells needed for negation, min and max. BUF distributes an output to many inputs; TIEP, TIEZ and TIEN supply constants. Each cell includes its symbol for subsequent schematics. An output bubble denotes negation; NAND and NOR use the binary symbol shapes. NANY uses Σ for the input sum, which is saturated to −1 through +1 and then negated. TIE symbols carry their constant value above them.

<!-- code: cells -->

### 2.4 Standard-Cell Layout

Cells abut in horizontal rows to connect their power rails. All cells therefore require a common height and aligned power rails. INV, NAND, NOR and NANY retain the circuits and device dimensions of the taped-out designs within this common template. Three rails, VDD, VMID and VSS, cross each cell. Signal pins occupy fixed M1 heights accessible by vias from M2 above. Cells may be mirrored horizontally.

<!-- code: stdcells -->
