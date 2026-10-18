# Extraction, LVS and estimates

```python
from tritflow.extract import extract_layout, gds_wire_capacitance, append_wire_capacitance
from pathlib import Path

report = extract_layout('design.gds', 'design', 'build/lvs', reference='design.spice')
assert report['matched'], report['errors']
spice = Path(report['extracted']).read_text()
caps = gds_wire_capacitance('design.gds', report['report'], top='design')
with_wire_c = append_wire_capacitance(spice, 'design', caps)
```

The wrapper runs the installed TR-1um KLayout LVS deck. `reference` is a SPICE
file; alternatively pass `gate_netlist=GateNetlist(...)` and `cell_subckts=text`.
The reference generator enforces contracted signal/rail port order. The PDK's
X MOS model wrappers are translated to M devices for comparison; simulation
translates them back to the model-wrapper convention without changing geometry.

LVS success requires every circuit pair to match, no database errors, the deck's
success message, and an explicit case-insensitive equality check of top-level
port names. This additional check is needed because the installed deck accepts
some missing top-level ports despite its strict-port message. Mismatch returns
`matched=False` with diagnostics; process failures/timeouts raise ExtractionError.
Without a reference, device extraction alone returns `matched=None` and
`report=None`: the PDK does not write a connectivity database in netlist-only mode.

`gds_wire_capacitance` uses LVS connectivity and actual M1/M2 polygons. It
identifies anonymous database layers by exact equality to the corresponding GDS
metal, then merges each top net's polygons before measuring area and perimeter.
It includes recursively connected cell-pin metal. Child-only internal nets in
hierarchical circuits are outside this top-level estimate. For synthesized flat
gate netlists, all routed gate-to-gate nets belong to the top circuit.
`wire_capacitance(pnr_json)` instead measures routed wire and pin geometry,
excluding cell interiors. Do not add both estimates together.

No calibrated interconnect extraction coefficients were found in the installed
PDK; the OS00 manual explicitly marks parasitic extraction unavailable. Defaults
are **assumptions**: SiO2 relative permittivity 3.9 and effective metal heights
1 um (M1), 2 um (M2), yielding area coefficients 0.03453 and 0.01727 fF/um²;
fringe is assumed 0.02 fF/um of perimeter for both layers. Coefficients can be
replaced. There is no coupling/shielding/via C or signal wire resistance model.
This is an educational lumped substrate-capacitance estimate, not signoff PEX.

Capacitors are inserted inside the selected top subcircuit and rejected if their
nets are absent. To append capacitances named by a schematic or PNR netlist to
renamed extracted nets, use `reference_net_map(report_path, top)` and supply that
mapping to `append_wire_capacitance(..., net_map=...)`. KLayout escaped-dollar
nodes are retained for LVS and normalized safely by the simulation harness.

`estimate_ir_drop(pnr, template, abstracts, characterizations)` consumes cell
placements and the power object's `rails`, `straps`, `vias`, and `pins` (same
wire/via/pin dictionaries as PNR). Abstracts and characterizations map cell names
to JSON objects. It builds sparse nodal resistor networks, attaches cells at
cell-center x / template rail-center y, and holds supply pins ideal. Multiple
vias act in parallel; pad/via positions are projected to conductor centerlines.
The model assumes Manhattan conductors; finite-width current spreading and
parallel overlapping centerlines are not modeled.

Signed currents come from `dc[*].rail_current_a`. Pass
`instance_vectors={instance: input_trits}` for one realized bias; without it,
each rail independently uses its largest-magnitude characterized current (an
envelope that may not correspond to any common input pattern). Floating power
islands are errors. Results give per-cell rail voltages/deviations, signed pad
currents and estimated equal-divider zero shift for INV/NAND/NOR; NANY reports
its local VMID shift. Constant nominal-bias currents are not iterated against
the calculated local voltage. No package or thermal model is included.

Default sheet resistance is an assumed 0.05 ohm/square on both layers, roughly
the value obtained with assumed 0.5 um aluminum thickness and bulk resistivity
2.5e-8 ohm*m. Default via resistance is an assumed 0.05 ohm. Override these with
`sheet_ohm={'M1': ..., 'M2': ...}` and `via_ohm=...` when calibrated data exist.
`solve_resistive_network(edges, fixed_v, injection_a)` exposes the underlying
solver: positive injection enters a node, positive pad current supplies the net.

The installed deck also purges unloaded physical rails and their saved metal
polygons. For a missing power formal, the wrapper recursively proves the
reference pin reaches no device terminal before restoring it in the emitted
SPICE. The raw extraction is retained separately, and the result lists restored
formals. Signal ports are never restored this way. LVS database geometry may
therefore be a strict subset of the GDS metal. Layer matching first uses exact
geometry; if unloaded metal was purged, it accepts the unique largest registered
layer wholly contained in that metal and reports excluded area in
`excluded_unconnected_metal_um2`. Only nets retained by the device extractor
receive capacitors; this does not invent capacitance connections for floating
rails. Signal/connected rail metal remains measured from actual geometry.
