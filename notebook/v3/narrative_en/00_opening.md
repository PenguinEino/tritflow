# TritFlow: Balanced-Ternary HDL to GDS on Japan's First Commercial Open-Source PDK

Einosuke Okazaki<br>
Tokyo Metropolitan College of Industrial Technology (KOSEN), Tokyo, Japan

**Runtime**

- Run time: about 13 to 15 minutes for Run all on a fresh Colab runtime, including setup
- Python: 3.13 on Colab (also checked locally with 3.12)
- PDK: OpenSUSI TR-1um (commit 5d963db)
- KLayout: 0.30.6
- ngspice: 42
- Python packages: installed at pinned versions by the first cell

TritFlow is a design flow that takes ternary HDL to GDS on OpenSUSI TR-1um, using CMOS cells that work with three voltage levels directly. This notebook walks through each step in order: logic synthesis, two-metal place and route, GDS output, DRC/LVS, post-layout simulation and ternary timing analysis.

**Highlights**

- **To our knowledge, the first ternary physical design flow from HDL to GDS**: a single automated pipeline runs a dedicated ternary HDL (TritVerilog) → logic synthesis → two-metal place and route → GDS → DRC/LVS → post-layout SPICE → ternary timing analysis.
- **Physical balanced ternary**: no binary encoding; CMOS cells carry −1, 0 and +1 as three voltages, −5 V, 0 V and +5 V.
- **Manufacturable GDS**: the layouts pass the PDK's official DRC/LVS decks, and the flow builds a full-chip GDS with the MPW shuttle's frame and pads.
- **Standard cells from a taped-out design**: the cells are based on balanced-ternary logic circuits the author taped out on OpenSUSI-TR10 in 2026. The chips are due in January 2027, so the simulations can be checked directly against measurements.
- **Every step interactive on Colab**: Run all takes about 13 to 15 minutes. Schematics, layouts and waveforms appear at each step, and the HDL can be edited and rerun. Apache-2.0.
- **A flow on Japan's first commercial open-source PDK**: built on OpenSUSI TR-1um, TritFlow pushes forward the democratization of chip design in Japan.

<!-- figure: fig_flow_v2 -->

TritFlow works in **balanced ternary**. Each digit, or trit, takes one of three values, −1, 0 or +1, and the digit weights are powers of 3 (1, 3, 9, …). In the circuit, these values are −5 V, 0 V and +5 V. Balanced ternary has a long history: [Setun](https://doi.org/10.1007/978-3-642-22816-2_10), an early ternary computer built at Moscow State University in 1958, used it. It has recently drawn renewed attention through the large language model [BitNet b1.58](https://doi.org/10.48550/arXiv.2402.17764), whose weights are restricted to −1, 0 and +1. In its linear layers, multiplying an 8-bit input by such a weight yields the input, its negation or zero, so the matrix product (GEMM) needs only additions and subtractions, with no multipliers. Hardware that computes on ternary voltages directly, with no binary encoding in between, could therefore be highly efficient.

Today, however, ternary arithmetic runs on conventional binary logic, with each ternary value encoded in bits. Many ternary devices have been studied, including CNTFETs ([Lin et al., 2011](https://doi.org/10.1109/TNANO.2009.2036845)), memristors ([Wang et al., 2021](https://doi.org/10.1109/TCSI.2020.3027693)) and new CMOS structures ([Jeong et al., 2019](https://doi.org/10.1038/s41928-019-0272-8)). The design tools, though, have either stopped at [generating gate networks](https://doi.org/10.1109/ACCESS.2025.3597293) or encoded each ternary signal on several binary wires and run it through binary EDA ([MRCS](https://github.com/aiunderstand/MixedRadixCircuitSynthesis/tree/0865cee1f49fe9a803b4910b570f4e96e514c61b), [Takahe](https://github.com/Zaneham/takahe/blob/e7123ea60269922acb283d576678a3aabe51f4f4/designs/setun70_physical.sv), [Ankhdjet](https://doi.org/10.48550/arXiv.2608.26206)). To our knowledge, no physical design flow has taken HDL to GDS fully automatically on a manufacturable open-source PDK from a commercial fab, using CMOS cells that handle three physical voltage levels directly.

This notebook demonstrates such a flow on [OpenSUSI TR-1um](https://github.com/OpenSUSI/TR-1um/tree/5d963db9d44e192d37a0489c208bfccf2e2f690c) (Tokai Rika), the first open-source PDK released by a commercial semiconductor fab in Japan. TritFlow's standard cells reuse the circuit topologies and device sizes of [ternary logic circuits the author designed and taped out](https://github.com/PenguinEino/opensusi-tr10-balanced-ternary-logic/tree/8a60b97868cad008ff21fefca5da13dcd06063f8) in 2026 on OpenSUSI-TR10, the first OpenSUSI-MPW shuttle. A single pipeline takes a design written in TritVerilog, a dedicated ternary HDL, through logic synthesis, place and route, DRC/LVS and post-layout SPICE simulation.

The OpenSUSI-TR10 chips are due in January 2027. If this submission is selected, the author will present measurements of the ternary cells, together with a TritFlow demonstration, at ISSCC in February. A ternary circuit designed with TritFlow will then be fabricated on the next OpenSUSI shuttle. By closing the full loop of design, fabrication, measurement and conference presentation, this work aims to show that TR-1um, Japan's first commercial open-source PDK, has the potential to deliver the values that IEEE SSCS Code-a-Chip promotes, and to push forward Japan's open semiconductor ecosystem and the democratization of chip design.

**Reproducibility.** TritFlow is built so that the researchers, engineers and students who come after can understand how it works in detail, then rebuild and verify it themselves. The cell circuits, synthesis algorithms and place-and-route methods are kept simple enough to follow by reading the code. At the same time, the flow produces manufacturable GDS that passes the PDK's official DRC/LVS decks and is checked by post-layout simulation. Each notebook cell explains why its stage behaves as it does, with the physical and theoretical background, and readers can change parameters and see the effect immediately. Because the cells keep the circuits and device sizes of the taped-out design, simulation results can be compared directly with future measurements.

**Reusability.** Building on what they learn here, readers can extend TritFlow into their own research and designs. Editing a TritVerilog description is enough to regenerate a new, verified ternary core layout through the same automated flow. Later chapters go as far as a full-chip layout, generated automatically, that combines the four-term dot-product circuit with the MPW shuttle's stock frame and I/O pads. Because every algorithm lives in a clear Python module, new ternary gates can be added and the synthesis and place-and-route algorithms extended freely. The cell library, the EDA pipeline and this notebook are all open source (Apache-2.0) and can serve as a starting point for ternary logic research.

**Educational value.** This path from understanding to extension also makes TritFlow an excellent teaching resource for the next generation of students and engineers. Every step runs interactively on Google Colab, and rich visualizations (schematics, layouts, waveforms) and detailed numbers show how the netlist, layout and voltage waveforms change at each stage. Readers who know basic binary CMOS and introductory Verilog can follow, hands-on, the whole path from one line of HDL to GDS ready for fabrication. They do not stop at simulation: they finish with manufacturable GDS, in a design flow tied directly to measurement.
