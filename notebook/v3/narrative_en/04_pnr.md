## 4. Place and Route

This chapter places and routes the cell netlist from chapter 3 on TR-1um to produce GDS. The circuit is the dot4 dot product from section 3.7.

### 4.1 Why a Custom Place and Route Tool

Place and route is independent of whether signals are binary or ternary, so OpenROAD is applicable in principle. An experimental LibreLane port for TR-1um is also under development ([luyanaa/TR-1um](https://github.com/luyanaa/TR-1um)). However, TR-1um offers only two routing layers, M1 and M2; Liberty cannot represent the ternary cells, and three power rails must cross every cell. TritFlow therefore uses a small place and route tool with channels between cell rows for two-layer routing.

### 4.2 Placement: Simulated Annealing

Cells occupy horizontal rows separated by routing channels. Initial placement follows signal-flow order from the inputs, packing each cell into the shortest row. Simulated annealing then improves the placement. Each trial swaps two cells (60%), moves a cell to another position or row (30%), or mirrors a cell horizontally (10%). A lower cost is accepted; a higher cost is accepted with a temperature-dependent probability. The temperature decreases over 600 steps.

The cost is the sum of the half-perimeter lengths of the bounding boxes around each net's terminals (an estimate of wire length), plus a small weight on the longest row width. Because ternary cells draw continuous current while outputting 0, a placement that exceeds a power rail's current limit receives infinite cost and is rejected.

### 4.3 Routing: Maze Search

Routing uses horizontal M1 in the channels and vertical M2 over cells. A* search connects each net's terminals on the routing grid. Nets with more terminals and greater extent are routed first. If a net fails, all routing is removed, the failed net is moved to the front, and the remaining order is changed before retrying (up to 3 times). Vertical M2 power trunks supply the rails in each row.

During execution, the figure shows placement and routing progress. At completion, a slider replays recorded placement snapshots followed by nets in routing order.

<!-- code: pnr2 -->

The resulting GDS is shown below.

<!-- code: gds2 -->

This completes the path from a cell netlist to GDS. The next chapter verifies the GDS against PDK rules and evaluates its delay with post-layout simulation.
