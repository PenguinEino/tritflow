## 2. Cells

The circuit in chapter 1 used two standard-cell types, INV and NAND. This chapter examines the standard cells underlying TritFlow. It starts with INV to explain how CMOS produces three voltage levels, establishes which cells can implement arbitrary ternary logic, and describes how the taped-out circuits become standard cells for place and route.

### 2.1 INV: Generating Three Levels

Unlike a binary inverter, the ternary INV turns on both the upper and lower MOS transistors to generate 0 V by voltage division.

TritFlow's INV connects a PMOS, two diffusion resistors (PDK device RR) and an NMOS in series between VDD and VSS. Output Y is taken between the two resistors.

<!-- tables: inv -->

At an input of ±5 V, only one MOS transistor conducts, pulling Y to its rail. At an input of 0 V, both conduct. Approximating each conducting MOS transistor by an on-resistance $r_{on} \propto (W/L)^{-1}$, with $R_u = r_{on,P} + R_{RP}$ above Y and $R_d = r_{on,N} + R_{RN}$ below Y, gives

$$V_Y = V_{SS} + (V_{DD}-V_{SS})\frac{R_d}{R_u+R_d},\qquad I = \frac{V_{DD}-V_{SS}}{R_u+R_d}$$

No rail supplies 0 V to the output; it is established solely by the balance $R_u = R_d$, with continuous static current $I$. With the dimensions below, the resistance of each RR exceeds the approximated MOS on-resistance by a factor of at least 20, so the ratio of the two identically shaped resistors dominates the zero level rather than MOS variation.


#### SPICE Simulation

The DC analysis uses ngspice and the PDK models for 90 sets of dimensions, including the taped-out dimensions.

Sizing trades off middle-level accuracy, delay, area and static current. The MOS gate length is the minimum 1 µm for drive strength and area; the RR width is the minimum 2.8 µm. At an input of 0 V, the output is 0 V when $R_u = R_d$, or $r_{on,P} + R_{RP} = r_{on,N} + R_{RN}$. Because hole mobility is lower than electron mobility, the PMOS is wider than the NMOS to match their on-resistances and cancel the output offset. The middle-level noise-margin target is an output within ±0.5 V for inputs from −1 to +1 V. The RR length is 30 µm to keep the static current of the complete taped-out chip within the power-wire and via current limits. The MOS dimensions were retained when RR was lengthened, leaving an offset of several tens of mV at an input of 0 V, well within the ±0.5 V acceptance band.

The adopted PMOS and NMOS widths are 13.5 µm and 5 µm. The PDK's zero-bias resistance equation gives 10.835 kΩ for each RR. A linear MOS resistance approximation using mobility, oxide thickness and threshold voltage gives $r_{on,P}=0.492$ kΩ and $r_{on,N}=0.399$ kΩ. The RR-to-on-resistance ratios are 22.0 and 27.2, respectively. Substituting into the divider equations gives

$$V_Y=-5+10\frac{11.234}{11.327+11.234}\simeq -0.021\ \mathrm{V},\qquad I=\frac{10}{11.327+11.234}\simeq 0.443\ \mathrm{mA}$$

The difference from SPICE's −0.040 V and 0.407 mA follows from omitting RR voltage/substrate-bias dependence and MOS nonlinearity. These approximations were not fitted to the SPICE current.

<!-- code: inv -->

### 2.2 Functional Completeness

Logic synthesis replaces HDL logic with combinations of library cells. To implement arbitrary logic, the cell basis must be **functionally complete**: connecting those cells must be sufficient to construct every logic function. In binary logic, NAND alone is complete.

In ternary logic, NANY and a +1 constant cell (TIEP) form a complete basis. A −1 constant cell (TIEN) can be used instead. NANY saturates the sum of its two inputs to the range −1 to +1 (sat), then negates it: $\mathrm{NANY}(a, b) = -\mathrm{sat}(a+b)$.

Słupecki's criterion (1939) establishes completeness for a ternary function basis satisfying both conditions below.

1. It can construct every unary function. Input a has three values, −1, 0 and +1, and each can map to any of three outputs, giving 3 × 3 × 3 = 27 unary functions.
2. It can construct a binary function f(a, b) that depends on both inputs (changing either input alone can change the output) and takes all three output values, −1, 0 and +1.

NANY itself satisfies condition 2. Since NANY(a, 0) = −a, changing a can change the output, and the same holds for b. Its output also takes all three values. Condition 1 is checked constructively: starting with input a and the +1 constant, repeatedly connect available functions to NANY inputs until no new function appears. The table lists functions constructed in the first few rounds. Depth counts NANY stages from a and the constant.

<!-- code: closure -->

NANY alone is not complete. Since $\mathrm{NANY}(0, 0) = 0$, any network of NANY cells produces 0 when all inputs are 0. It cannot construct a function that produces a nonzero output at a = 0, or a +1 or −1 constant. Adding one nonzero constant removes this restriction. The remaining constants follow from $\mathrm{NANY}(+1, +1) = -1$ and $\mathrm{NANY}(+1, -1) = 0$, so only one constant-cell type is required. TritFlow uses this property to map arbitrary truth tables to cells (chapter 3).

### 2.3 Standard-Cell Library

The TritFlow standard cells are shown below. INV, NAND, NOR and NANY implement the taped-out circuits. INV, NAND and NOR are unnecessary for completeness but reduce the number of cells needed for negation, min and max. BUF distributes an output to many inputs; TIEP, TIEZ and TIEN supply constants. Each cell includes its symbol for subsequent schematics. An output bubble denotes negation; NAND and NOR use the binary symbol shapes. NANY uses Σ for the input sum, which is saturated to −1 through +1 and then negated. TIE symbols carry their constant value above them.

<!-- code: cells -->

### 2.4 Standard-Cell Layout

Cells abut in horizontal rows to connect their power rails. All cells therefore require a common height and aligned power rails. INV, NAND, NOR and NANY retain the circuits and device dimensions of the taped-out designs within this common template. Three rails, VDD, VMID and VSS, cross each cell. Signal pins occupy fixed M1 heights accessible by vias from M2 above. Cells may be mirrored horizontally.

<!-- code: stdcells -->
