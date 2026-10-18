# Abstract

TritFlow is an open-source, notebook-driven flow that makes balanced-ternary
circuit design inspectable from a Verilog-like description to physical layout
and extracted transistor simulation. Using the OpenSUSI TR-1um PDK, it connects
ternary-safe synthesis, a three-rail standard-cell library, placement and
two-layer routing, official design-rule and connectivity checks, and ngspice
verification against independent arithmetic references. The notebook begins
with a complete adder, then connects gate truth tables and historical
schematics to cell characterization, measured self-loading, mapping decisions,
physical geometry, and device-only versus wire-loaded settling. Published experiments expose
adder scaling and an output-load failure boundary, while editable examples
let readers test their own circuits through the same interfaces. Saved figures
and generated tables support review without execution; pinned source/runtime
setup and content-checked caches support reproduction. Coverage, operating
conditions, convergence aids, static-current costs and parasitic-model limits
are stated explicitly. The project teaches a reproducible design methodology
without claiming a performance advantage over binary CMOS or measured silicon.
