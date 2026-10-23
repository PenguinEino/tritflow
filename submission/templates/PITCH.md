# Three-sentence pitch

Ternary-weight neural networks reduce multiplication to sign selection, yet ternary
arithmetic is still built from binary-encoded logic.
TritFlow is an open flow that takes balanced-ternary HDL to DRC/LVS-clean GDS on the
open OpenSUSI TR-1um PDK, using CMOS cells that keep three voltage levels (−5, 0, +5 V)
and are derived from the author's taped-out 1-trit multiply-add circuit.
The notebook walks one ternary-weight dot product through synthesis, place and route,
extraction and SPICE, scales it to 16 terms to quantify area, ternary STA accuracy and
the static-power cost, and lets readers edit the HDL and rerun the whole flow in Colab.
