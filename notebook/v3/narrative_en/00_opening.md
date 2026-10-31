# TritFlow: Ternary HDL to GDS with the Open-Source TR-1um PDK

Einosuke Okazaki (岡崎 英之介)<br>
Information and Communication Engineering Course, Department of Monozukuri Engineering, Tokyo Metropolitan College of Industrial Technology (KOSEN), Tokyo, Japan

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/PenguinEino/tritflow/blob/notebook-v3/notebook/v3/tritflow_en.ipynb)

**Runtime**

- Run time: 6 to 8 minutes for Run all on a fresh Colab runtime, including setup
- Python: 3.12
- PDK: OpenSUSI TR-1um (commit 5d963db)
- KLayout: 0.30.6
- ngspice: 42
- Python packages: installed at pinned versions by the first cell

TritFlow is a design flow from ternary HDL to GDS on OpenSUSI TR-1um, built on CMOS cells that handle three voltage levels directly. This notebook runs ternary HDL through logic synthesis, two-metal place and route, GDS output, DRC/LVS, post-layout simulation and ternary timing analysis in order.

<!-- figure: fig_flow_v2 -->

TritFlow uses **balanced ternary**. Each digit (trit) takes one of three values, −1, 0 and +1, and the digit weights are powers of 3 (1, 3, 9, …). In the circuit, these values correspond to −5 V, 0 V and +5 V. Balanced ternary is a long-established representation that was also adopted by [Setun](https://doi.org/10.1007/978-3-642-22816-2_10), an early ternary computer built at Moscow State University in 1958. It has recently drawn renewed attention through the large language model [BitNet b1.58](https://doi.org/10.48550/arXiv.2402.17764), whose weights are restricted to these three values (−1, 0, +1). In its linear layers, the product of a weight and an 8-bit input is the input itself, its negation or zero, so the multiply-accumulate (GEMM) can be computed with additions and subtractions alone, without multipliers. Dedicated hardware that processes ternary data directly as ternary voltages, without an intermediate binary conversion, has the potential to achieve high efficiency.

Today, however, almost all hardware that performs ternary arithmetic emulates it on conventional binary logic. At the device level, diverse ternary devices have been studied, including CNTFETs ([Lin et al., 2011](https://doi.org/10.1109/TNANO.2009.2036845)), memristors ([Wang et al., 2021](https://doi.org/10.1109/TCSI.2020.3027693)) and new CMOS structures ([Jeong et al., 2019](https://doi.org/10.1038/s41928-019-0272-8)), yet design tools have either stopped at [generating gate networks](https://doi.org/10.1109/ACCESS.2025.3597293) or encoded each ternary signal on several binary wires and passed it through binary EDA ([MRCS](https://github.com/aiunderstand/MixedRadixCircuitSynthesis/tree/0865cee1f49fe9a803b4910b570f4e96e514c61b), [Takahe](https://github.com/Zaneham/takahe/blob/e7123ea60269922acb283d576678a3aabe51f4f4/designs/setun70_physical.sv), [Ankhdjet](https://doi.org/10.48550/arXiv.2608.26206)). To our knowledge, no physical design flow has taken HDL to GDS fully automatically on a manufacturable open-source PDK from a commercial fab, using CMOS cells that handle three physical voltage levels directly.

This notebook demonstrates such a ternary design flow on [OpenSUSI TR-1um](https://github.com/OpenSUSI/TR-1um/tree/5d963db9d44e192d37a0489c208bfccf2e2f690c) (Tokai Rika), the first open-source PDK released by a commercial semiconductor fab in Japan. TritFlow's cell library turns the circuit topologies and device sizes of [ternary logic circuits designed and taped out by the author](https://github.com/PenguinEino/opensusi-tr10-balanced-ternary-logic/tree/8a60b97868cad008ff21fefca5da13dcd06063f8) (2026, the first OpenSUSI-MPW shuttle, OpenSUSI-TR10) directly into standard cells. A single pipeline takes a description in the dedicated ternary HDL TritVerilog through logic synthesis, place and route, DRC/LVS and post-layout SPICE simulation.

The OpenSUSI-TR10 chips arrive in January 2027; if selected, the author will present TritFlow at ISSCC in February together with the first measurements of its cells. A circuit designed with TritFlow will be fabricated on the next OpenSUSI shuttle. Completing this cycle of design, fabrication, measurement and reporting with TritFlow will demonstrate that TR-1um is capable enough to deliver the three values Code-a-Chip promotes. Through this cycle, the project aims to substantially advance the democratization of chip design in Japan.

**Reproducibility.** Subsequent researchers should be able to understand, reconstruct and explain TritFlow. Its cell circuits, logic synthesis algorithms, and place and route algorithms are kept simple enough to follow while producing core GDS verified by PDK DRC/LVS and post-layout SPICE. This notebook explains each stage and makes it executable in place. Because the cells are based on circuits being fabricated and measured, the explanations can also be checked against silicon measurements.

**Reusability.** That understanding provides a basis for extending TritFlow. Editing the HDL regenerates a verified core through the same flow. For dot4, the notebook also shows the top-level layout in an MPW frame. The simple structure also allows cells to be added and synthesis or place and route algorithms to be replaced. The cells, flow and notebook are released under Apache-2.0 as a starting point for subsequent research and shuttle submissions.

**Education.** The progression from understanding to extension also provides a learning path. Every stage runs interactively in the notebook and presents figures and quantitative results, allowing readers who know basic CMOS logic and an HDL to follow the full path from HDL to GDS. The same flow connects to fabrication and measurement.
