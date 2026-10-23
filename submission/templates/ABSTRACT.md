# Abstract

Ternary-weight neural networks such as BitNet b1.58 turn the products of their linear
layers into additions, subtractions and skips, but open design flows implement ternary
values by binary encoding. TritFlow is an open, notebook-driven flow from balanced-ternary
HDL to GDS in which every signal stays a single three-level wire (−5, 0, +5 V). Its standard
cells are adapted from the author's taped-out 1-trit multiply-add circuit on the open
OpenSUSI TR-1um PDK; the notebook derives their functional completeness (Słupecki's
criterion) and checks the resistive-divider zero level against SPICE. A ternary-weight dot
product then carries the reader through equivalence-checked synthesis, a two-metal placer
and router written for three power rails, PDK drawing DRC and LVS, extraction with estimated
wire capacitance, post-layout ngspice, and a ternary static timing analysis that
distinguishes six level transitions. {{RESULTS_SENTENCE}} Recorded runs up to 16 terms
quantify how area, delay and wire load grow, how closely ternary STA tracks SPICE, and the
static power the divider-based zero level costs. Readers can edit the HDL and rerun the
whole flow in Colab, and the dot product is also delivered as an MPW-framed top. Wire
capacitance is estimated, not calibrated, and silicon measurement of the taped-out cells
is the next step; no advantage over binary implementation is claimed.
