## 3. Taped-out circuits become placeable cells

A router needs a cell boundary, legal pin landings and obstacles as well as
a circuit. These cells share a height and carry VDD, VMID and VSS horizontally
across the row. Select a device to connect its schematic name with its actual
layout geometry. Then inspect the abutted row to see how the rails continue.

<!-- figure: ch3 -->

*Choose a cell and toggle layers. Select a device in the table to outline it
in the layout; the initial NANY view highlights the path from Y to VMID.*

Internal M2 and vias appear in the routing obstacles. Signal pins sit on M1
where a vertical M2 route can reach them through a via. Cells may face forward
or reflect left to right while preserving the rail order. TIE cells supply
constants through finite resistance; FILL continues rails and wells through gaps.

> **What this shows.** {cell.name} occupies {cell.width_um} × {cell.height_um}
> µm, {cell.area_ratio} times its reference-layout area. Under the same
> estimated metal-capacitance model and {cell.compare_load_ff} fF load,
> reference and adapted worst settling are {cell.original_settling_ns} and
> {cell.compact_settling_ns} ns, a {cell.settling_change_pct}% change.

The cell checks and row-abutment results are available in Appendix B.
