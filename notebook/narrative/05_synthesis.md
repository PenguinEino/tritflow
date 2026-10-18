## 5. Follow an expression into cells

Synthesis expands parameters and hierarchy, simplifies ternary expressions,
then maps them to the library. Follow one signal from the source hierarchy
through the half-adder graph in the preceding figure. Its net colors expose
intermediate trits as well as the final sum and carry.

<!-- figure: ch5 -->
<!-- hero-reuse: fig_synth panels (b,c); caption: captions.md#fig_synth -->

In the [mapped half adder](../../figures/out/fig_synth.png), blue, gray and
red traces carry −1, 0 and +1. Follow the shared intermediate nets before
checking the sum and carry.

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
