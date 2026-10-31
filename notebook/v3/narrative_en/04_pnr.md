## 4. Place and Route

From the cell connectivity (netlist) synthesized in chapter 3, the cells are placed following the geometric rules of the TR-1um PDK and connected with two metal layers to generate GDS. This chapter looks at TritFlow's place-and-route tool, using the four-term dot-product circuit synthesized in section 3.7.

### 4.1 Why a Custom Place and Route Tool

Place and route is a geometric connection problem that does not depend on signal values, so in principle binary EDA tools (such as OpenROAD) could be reused. For TR-1um, a port to LibreLane is in fact being attempted ([luyanaa/TR-1um](https://github.com/luyanaa/TR-1um)).

Applying existing binary EDA tools to ternary design as they are, however, faces three technical obstacles.

1. **Routing layers (two metals)**: TR-1um is a 1 µm process, and only two metal layers, the first (M1) and second (M2), are available for routing. With two layers, power distribution and signal routing compete for the same layers.
2. **Three power rails and the limits of Liberty**: every ternary cell must carry three power rails, VDD (+5 V), VMID (0 V) and VSS (−5 V), continuously without gaps. Liberty, the standard format for describing cell characteristics, cannot describe ternary logic or transition characteristics.
3. **Static current specific to ternary cells**: ternary cells draw static current through their resistive dividers while outputting 0 V. If high-current cells gather on one rail, the allowed current of the power wiring is exceeded.

To solve these problems, TritFlow implements its own lightweight place-and-route tool that leaves dedicated routing channels between cell rows and routes on two layers.

### 4.2 Placement: Simulated Annealing

Placement uses rows, in which cells line up horizontally, alternating with channels, the routing passages.

1. **Initial placement**: from the circuit's inputs toward its outputs, following signal flow, each cell is packed into the currently shortest row.
2. **Improvement by simulated annealing**: starting from the initial placement, 600 annealing steps improve the placement gradually. Each step randomly performs one of the following three moves. A move that lowers the cost is accepted, and one that raises it is accepted with a temperature-dependent probability; the temperature decreases as the steps proceed.
   - **Swap (60%)**: exchange the positions of two cells.
   - **Move (30%)**: move one cell to another row or position.
   - **Mirror (10%)**: switch a cell between its normal orientation (R0) and its left-right mirror (MY), bringing its pins closer to nearby wiring.
3. **Cost function and current constraint**: the cost is the sum of the half-perimeters of the bounding boxes around each net's terminals (HPWL: half-perimeter wire length) plus a small weight times the longest row width. In addition, the static current of the cells is summed per row, and any placement candidate that exceeds the allowed current of a power rail gets infinite cost and is rejected.

### 4.3 Routing: Maze Search

Once placement is complete, the signal nets are routed on the routing grid (6 µm pitch). The basic strategy is orthogonal two-layer routing, with M1 running horizontally (inside the channels) and M2 vertically (allowed to pass over cells).

1. **A\* search**: starting with nets that have many terminals and spread widely over the circuit, each net is connected along a shortest path through vias (V1) by the A\* algorithm.
2. **Rip-up and retry**: if a later net is blocked by existing wiring and cannot be connected, all wiring is removed, and routing restarts from the beginning with the failed net first and the remaining order permuted. This retry is performed up to 8 times, including the first attempt.
3. **Channel expansion**: if routing is still incomplete after 8 attempts, the number of tracks in the routing channels is increased to widen the routing space, and routing is tried again (up to 5 times).
4. **Power trunks**: vertical M2 power trunks are placed, feeding the M1 rails of each row.

Running the code cell below performs place and route. While it runs, the placement and routing are drawn; afterwards, the figure is replaced by one whose sliders step through the placement improvement and the order in which nets were routed.

<!-- code: pnr2 -->

The GDS layout of the finished dot-product circuit is shown below.

<!-- code: gds2 -->
