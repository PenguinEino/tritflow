## 5. Follow an expression into cells

Synthesis expands parameters and hierarchy, simplifies ternary expressions,
then maps them to the library. Follow one signal from the source hierarchy
through the cell graph. Choosing an input vector recolors every net, so you
can check intermediate values as well as the final answer.

<!-- figure: ch5 -->

*Choose an input vector. Blue, gray and red traces carry −1, 0 and +1;
hover shows the value and the originating HDL instance.*

A negated minimum maps directly to NAND; a positive minimum adds INV.
The analogous rule uses NOR for maximum. Constants map to TIE cells.
Synthesis removes double inversion, shares common expressions and removes
unused logic using identities that hold for trits. Explicit live gate instances
retain their cell type. Buffer trees limit fanout, and the equivalence check
compares the original source with the final cell network.

> **What this shows.** {synth.top} maps to {synth.cells} cells with
> {synth.depth} cell stages on its longest logical path. Its source-to-cell
> equivalence check uses {synth.equivalence_mode} testing over
> {synth.equivalence_vectors} input vectors and {synth.equivalence_status}.

The same cell network now supplies both the physical placer and the schematic
reference for layout verification.
