# Title options

1. **TritFlow: Balanced-Ternary HDL to GDS on OpenSUSI TR-1um**
2. **Build a Ternary Adder: From CMOS Devices to Checked GDS**
3. **Where the Middle Voltage Comes From: A Ternary Design Flow**

# Three-sentence pitch

TritFlow turns a Verilog-like description of balanced-ternary arithmetic into
a routed layout, drawing-DRC and LVS results, and extracted transistor-level
waveforms on OpenSUSI TR-1um. Starting from the author's taped-out cell
designs, the notebook connects hand estimates of the middle voltage, static
power and carry delay with interactive SPICE results. Readers can change
cell dimensions, inspect routing, edit a circuit and run the same open flow
on their own design.

# Abstract — 100 words

TritFlow connects balanced-ternary circuit design to physical implementation
on OpenSUSI TR-1um. A Verilog-like language describes signed arithmetic using
ternary gates. Synthesis maps those descriptions to a library adapted from
the author's taped-out cells, followed by placement, routing, drawing DRC,
LVS and extracted ngspice simulation. Interactive figures connect schematics,
transfer curves, layouts and waveforms. Hand estimates explain how resistor
and transistor sizing establish the middle voltage, consume static power
and shape ripple-carry delay. Readers can edit a circuit and repeat the flow
in Colab. Reported results distinguish logic coverage, connectivity and
nominal analog behavior; silicon measurements remain future work for validation.

# Why ternary, why this PDK, why now

Balanced ternary makes signed digits, carry behavior and the physical meaning
of a middle voltage visible in one circuit. OpenSUSI TR-1um supplies an
[NDA-free CMOS PDK from Japan](https://github.com/OpenSUSI/TR-1um), allowing
readers to inspect devices, models and layout checks together. The author's
ternary cells have already been taped out, and their expected return in
{history.delivery_month} gives this work a concrete next experiment. TritFlow
turns those designs into a reusable library and an editable route to GDS;
its immediate contribution is a working design method with explicit electrical
costs and testable predictions.
