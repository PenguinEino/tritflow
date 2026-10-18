## 5. Follow an expression into cells

Synthesis expands parameters and hierarchy, simplifies ternary expressions,
then maps them to the library. The method cell below draws the mapped half
adder as a schematic: inputs on the left, sum and carry on the right, each
box one library cell (Σ = NANY, triangle = INV). Click an input trit and
every wire recolors to the value it settles to.

<!-- figure: ch5 -->
<!-- hero-reuse: fig_synth panels (b,c); caption: captions.md#fig_synth -->

Blue, gray and red wires carry −1, 0 and +1. Try a = b = +1: the inputs
add to 2, which the cells write as sum = −1 and carry = +1, because
2 = (−1) + 3·(+1). Follow the shared intermediate nets before checking
the outputs.

A negated minimum maps directly to NAND; a positive minimum adds INV.
The analogous rule uses NOR for maximum. Constants map to TIE cells.
Synthesis removes double inversion, shares common expressions and removes
unused logic using identities that hold for trits. Explicit live gate instances
retain their cell type. Buffer trees limit fanout, and the equivalence check
compares the original source with the final cell network.

> **What this shows.** The mapped half adder has {paper_synth.ha_cells} cells:
> {arithmetic.ha_nany} NANY and {arithmetic.ha_inv} INV.
> At the illustrated positive inputs it produces a negative sum digit and
> a positive carry, preserving the integer total.

The same cell network now supplies both the physical placer and the schematic
reference for layout verification.
