# Abstract

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
