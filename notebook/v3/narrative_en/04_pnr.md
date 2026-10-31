## 4. Place and Route

Place and route turns the netlist synthesized in chapter 3 into GDS: it places the cells under the geometric rules of the TR-1um PDK and connects them with two metal layers. This chapter walks through TritFlow's place-and-route tool on the four-term dot-product circuit synthesized in section 3.7.

### 4.1 Why a Custom Place-and-Route Tool

Place and route is a geometric connection problem that does not depend on signal values, so in principle binary EDA tools such as OpenROAD could be reused. For TR-1um, a port to LibreLane is in fact under way ([luyanaa/TR-1um](https://github.com/luyanaa/TR-1um)).

Using existing binary EDA tools unchanged for ternary design, however, runs into three technical obstacles.

1. **Only two metal layers**: TR-1um is a 1 µm process with just two metal layers for routing, the first (M1) and the second (M2). Power distribution and signal routing must share them.
2. **Three power rails, and the limits of Liberty**: every ternary cell must carry three power rails, VDD (+5 V), VMID (0 V) and VSS (−5 V), continuously without gaps. Liberty, the standard format for cell characteristics, cannot describe ternary logic or ternary transition characteristics.
3. **Static current in ternary cells**: ternary cells draw static current through their resistive dividers while they output 0 V. If high-current cells cluster on one rail, the current exceeds what the power wiring allows.

To solve these problems, TritFlow implements its own lightweight place-and-route tool, which leaves dedicated routing channels between cell rows and routes on two layers.

### 4.2 Placement: Simulated Annealing

Placement alternates rows of cells with routing channels between them.

1. **Initial placement**: following the signal flow from the circuit's inputs to its outputs, each cell goes into whichever row is currently shortest.
2. **Simulated annealing**: starting from the initial placement, 600 annealing steps improve it gradually. Each step randomly performs one of the three moves below. A move that lowers the cost is accepted; one that raises it is accepted with a probability that depends on the temperature, which falls as the steps proceed.
   - **Swap (60%)**: exchange the positions of two cells.
   - **Move (30%)**: move one cell to another row or position.
   - **Mirror (10%)**: flip a cell between its normal orientation (R0) and its left-right mirror (MY) to bring its pins closer to nearby wiring.
3. **Cost function and current constraint**: the cost is the half-perimeter wire length (HPWL), the sum over all nets of the half-perimeter of the box bounding each net's terminals, plus a small weight times the width of the longest row. The static current of the cells is also summed per row, and any candidate placement that exceeds the current limit of a power rail is rejected by giving it infinite cost.

### 4.3 Routing: Maze Search

Once the cells are placed, the signal nets are routed on the routing grid (6 µm pitch). The basic strategy is orthogonal two-layer routing: M1 runs horizontally inside the channels, and M2 runs vertically and may pass over cells.

1. **A\* search**: starting with the nets that have the most terminals and span the widest area, each net is connected along a shortest path through vias (V1) by the A\* algorithm.
2. **Rip-up and retry**: if a later net is blocked by existing wiring and cannot be connected, all wiring is removed and routing restarts from scratch, with the failed net first and the remaining order shuffled. Up to 8 attempts are made, including the first.
3. **Channel expansion**: if routing is still incomplete after 8 attempts, the routing channels get more tracks and routing is tried again (up to 5 times).
4. **Power trunks**: vertical M2 power trunks are added to feed the M1 rails of every row.

Running the code cell below performs place and route. While it runs, the placement and routing are drawn live; when it finishes, the drawing is replaced by a figure with sliders that step through the placement improvement and the order in which the nets were routed.

<!-- code: pnr2 -->

The GDS layout of the finished dot-product circuit is shown below.

<!-- code: gds2 -->
