# Abstract

TritFlow connects balanced-ternary HDL to physical implementation on the open
OpenSUSI TR-1um PDK. Its standard cells are adapted from the author's taped-out
1-trit multiply-add circuit. A ternary-weight dot product carries the reader
from arithmetic expressions through equivalence-checked synthesis, placement,
routing, GDS, PDK drawing DRC and LVS, and extracted ngspice simulation with
estimated wire capacitance. Interactive schematics, sizing experiments,
layouts and waveforms explain the circuit and each stage of the flow. Ternary
static timing estimates are compared with SPICE settling into the output's
voltage tolerance band. The running dot product maps to 46 cells and passes synthesis equivalence over 6,561 input vectors; post-layout ngspice passes the output-level check for 11 stimulus intervals. Readers can edit HDL and rerun
the same open flow in Colab. Reported checks distinguish logical coverage,
connectivity and nominal analog behavior; parasitics are approximate and
silicon measurements remain future validation. No advantage over binary
implementation is asserted.
