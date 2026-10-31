## 4. Place and Route

This chapter places and routes the cell netlist from chapter 3 on TR-1um to produce GDS. The circuit is the four-term dot-product circuit from section 3.7.

### 4.1 Why a Custom Place and Route Tool

Place and route does not depend on whether signals are binary or ternary, so in principle binary EDA such as OpenROAD can be used. A port of TR-1um to LibreLane is also being attempted ([luyanaa/TR-1um](https://github.com/luyanaa/TR-1um), experimental). Applying binary EDA to ternary cells as they are, however, meets three obstacles.

1. **Two metal layers**: TR-1um has only two routing metals, M1 and M2, so power and signals compete for the same two layers.
2. **Three power rails and Liberty**: every ternary cell must carry three power rails, VDD (+5 V), VMID (0 V) and VSS (−5 V). Liberty, the standard format for cell characteristics, cannot represent ternary logic and transitions.
3. **Static current**: ternary cells draw static current through their resistive dividers while outputting 0. If high-current cells gather on one rail, the rail's allowed current is exceeded.

TritFlow therefore has its own small place-and-route tool that leaves routing channels between cell rows and routes on two layers.

### 4.2 Placement: Simulated Annealing

Cells are placed in horizontal rows, with routing channels left between rows.

1. **Initial placement**: following signal flow from the cells nearest the inputs, each cell is packed into the currently shortest row.
2. **Simulated annealing**: 600 annealing steps improve the initial placement. Each trial performs one of the following moves. A move that lowers the cost is accepted, and one that raises it is accepted with a temperature-dependent probability; the temperature decreases as the steps proceed.
   - swap two cells (60%)
   - move one cell to another position or row (30%)
   - mirror one cell left to right (10%)
3. **Cost and current constraint**: the cost is the sum of the half-perimeters of each net's terminal bounding box (HPWL, a wire-length estimate) plus a small weight times the longest row width. Because ternary cells draw current while outputting 0, a placement that exceeds the allowed current on any power rail gets infinite cost and is never chosen.

### 4.3 Routing: Maze Search

Routing runs on the routing grid (6 µm pitch) on two layers: M1 running horizontally in the channels and M2 running vertically over the cells.

1. **A\* search**: nets with many terminals and a large spread are routed first, each connecting its terminals by A\* search. M1 and M2 connect through vias (V1).
2. **Rip-up and retry**: if a net cannot be routed, all routes are removed and routing restarts with that net first and the remaining order permuted, up to 8 attempts including the first.
3. **Channel expansion**: if 8 attempts fail, the routing channels are widened and routing starts again (up to 5 times).
4. **Power**: vertical M2 trunks feed the rails of each row.

The cell below runs place and route. The figure shows placement and routing while they run; afterwards it is replaced by a figure whose sliders step through the recorded placement history and net routing order.

<!-- code: pnr2 -->

The resulting GDS is shown below.

<!-- code: gds2 -->
