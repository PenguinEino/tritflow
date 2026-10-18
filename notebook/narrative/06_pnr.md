## 6. Route signals and feed the standing current

Placement arranges cells in rows with routing channels between them. A seeded
annealing search reduces estimated connection length; a grid router connects
the pins on two metals. M1 signal routes stay in channels, while M2 can cross
cells through unobstructed tracks. The three supplies need enough metal and
feed points to carry the cells' static current.

<!-- figure: ch6 -->

*Play the placement history, then select a net or instance in the routed
layout. The highlighted route includes its vias and pin landings.*

The router checks connectivity, spacing and via enclosure, then runs the PDK
drawing-DRC deck. LVS compares the extracted devices and connections with
the mapped schematic. The power-network view uses characterized cell currents
to show where the rail voltage changes along the drawn metal.

> **What this shows.** The layout measures {pnr.die_um} µm, with
> {pnr.utilization_pct}% utilization and {pnr.wirelength_um} µm of signal
> wiring. Estimated cell-terminal connection length changes from
> {pnr.initial_hpwl_um} to {pnr.final_hpwl_um} µm during placement;
> drawing DRC reports {pnr.drc_items} markers and LVS is {pnr.lvs_status}.

The layout is now the source of both device extraction and wire geometry for
the electrical comparison.
