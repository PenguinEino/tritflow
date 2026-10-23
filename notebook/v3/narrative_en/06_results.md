## 6. Evaluation and Reuse

Chapter 5 verified the four-term dot product dot4 with post-layout simulation and compared it with ternary STA. This chapter evaluates area, delay and static power as the term count changes, then reruns the flow after an HDL change and presents a shuttle top-level layout.

### 6.1 Dot-Product Size and Area

The evaluated circuit is a dot product of one-trit weights and inputs, $y = \sum_{i=0}^{N-1} w_i x_i$. The output uses the minimum number of trits needed to represent $-N$ through $+N$. Weights remain HDL inputs but are fixed in simulation to repetitions of $(+1, -1, +1, +1)$. Addition uses the same HDL form as section 3.7, without structural changes for different term counts.

The tables present recorded place and route and verification results. Area is measured from the routed die outline. Wire capacitance uses the estimate in section 5.2, rather than PDK-calibrated parasitic extraction. Loading verifies the identities of the source, cells, PDK and simulator. Recalculation requires an explicit switch.

<!-- code: scale6 -->

Increasing the term count adds multiplier circuits and adder circuits for the required sum width. Die area also includes power and signal routing, so it does not grow in direct proportion to term count.

### 6.2 Static and Time-Average Power

States that hold 0 V by resistive division draw static current even without input transitions. NANY also has zero-output states in which VMID clamps conduct while the VDD and VSS transistor stacks are cut off. Static power is calculated from DC operating points for states in the recorded input sequence. With current defined as positive into each SPICE voltage source, circuit power is $P = -\sum_r V_r I_r$, including both positive and negative supply contributions.

Time-average supply power is the integral of instantaneous power over all hold intervals, divided by the total duration. It includes state-dependent static consumption and transition consumption; switching-only energy is not separated. Power from the input voltage sources is excluded.

<!-- code: power6 -->

The number of conducting divider paths depends on the input state, so static power varies even at a fixed term count. Time-average power depends on the hold time and input sequence. These area, delay and power measurements characterize this ternary implementation; they do not establish an advantage over a binary implementation.

### 6.3 STA and SPICE

Each circuit uses an input sequence that generates and clears positive and negative carries. The four-term sequence differs from chapter 5. STA conditions on the fixed weights. STA and SPICE use identical input transitions, output load, input slew and wire capacitance. The reported delay is each output's maximum settling time over that sequence, not a guaranteed worst case over all input transitions.

The effect of wire capacitance is evaluated by removing only the estimated wire capacitance from the same extracted circuit. STA compares both cases at every size; SPICE compares them for four terms. Both cases retain intrinsic device capacitance and the 100 fF output load.

At N=16, some NANY loads exceed the 2 pF characterization limit, reaching 2.862 pF, so STA extrapolates linearly in load capacitance.

<!-- code: timing6 -->

For dot4 in chapter 5, STA underestimates SPICE by about 10% at y[1] and 3% at y[0]. Across sizes, the error sign varies with circuit size and output. STA uses cell tables for the specified input transitions and does not resolve the complete analog waveform, including intermediate glitches. SPICE settling time includes the time needed to re-enter the acceptance band after a glitch, so STA cannot be treated as an upper bound on delay.

### 6.4 Editing HDL and Rerunning the Flow

Making inference weights HDL constants allows logic synthesis to simplify the corresponding multiplier circuits. The following circuit fixes dot4's weights to $(+1, -1, +1, +1)$. After changes to the expression and port declarations, the same execution cell runs logic synthesis through post-layout simulation.

<!-- code: reuse_source -->

SPICE covers all states when the total is at most 27. Otherwise, it selects 11 states from the zero input, all −1 and all +1 inputs, alternating signs, and single-input ±1 excursions. Sampled verification does not cover every input state or transition. Expected outputs come from evaluating the HDL, independently of the synthesized netlist.

<!-- code: reuse6 -->

### 6.5 Shuttle Top-Level Layout

The top-level layout adds probe pads, power routing and the PDK MPW frame to dot4. It is the circuit with weight inputs used in chapters 3–5, distinct from the fixed-weight circuit in section 6.4. Its custom probe-pad arrangement requires shuttle-operator approval of the pad map, package, electrostatic discharge (ESD) provisions and supply conditions.

<!-- code: shuttle6 -->

### 6.6 Conclusion

TritFlow connects balanced-ternary HDL to a native three-voltage cell netlist, place and route, PDK DRC/LVS and post-layout simulation. In this implementation with two routing metal layers, area and settling time grow faster than the number of terms. Static power is set by resistive division used to hold 0 V, so practical efficiency requires a different way to maintain that level. Future work will compare measurements of the taped-out cells with the models and incorporate the results into the cells and design flow.

### References

1. Shuming Ma et al., “The Era of 1-bit LLMs: All Large Language Models are in 1.58 Bits,” arXiv:2402.17764, 2024. [doi:10.48550/arXiv.2402.17764](https://doi.org/10.48550/arXiv.2402.17764).
2. Sheng Lin, Yong-Bin Kim, and Fabrizio Lombardi, “CNTFET-Based Design of Ternary Logic Gates and Arithmetic Circuits,” *IEEE Transactions on Nanotechnology*, 10(2), pp. 217–225, 2011. [doi:10.1109/TNANO.2009.2036845](https://doi.org/10.1109/TNANO.2009.2036845).
3. Muhammad Khalid and Jawar Singh, “Memristor based unbalanced ternary logic gates,” *Analog Integrated Circuits and Signal Processing*, 87(3), pp. 399–406, 2016. [doi:10.1007/s10470-016-0733-1](https://doi.org/10.1007/s10470-016-0733-1).
4. Xiaoyuan Wang et al., “High-Density Memristor-CMOS Ternary Logic Family,” *IEEE Transactions on Circuits and Systems I: Regular Papers*, 68(1), pp. 264–274, 2021. [doi:10.1109/TCSI.2020.3027693](https://doi.org/10.1109/TCSI.2020.3027693).
5. Jae Won Jeong et al., “Tunnelling-based ternary metal–oxide–semiconductor technology,” *Nature Electronics*, 2(7), pp. 307–312, 2019. [doi:10.1038/s41928-019-0272-8](https://doi.org/10.1038/s41928-019-0272-8).
6. Hanmok Park, Seonghoon Kim, Sunmean Kim, and Taigon Song, “An RTL-Based General Synthesis Methodology for Device-Independent Ternary Logic Circuits,” *IEEE Access*, 13, pp. 163648–163660, 2025. [doi:10.1109/ACCESS.2025.3597293](https://doi.org/10.1109/ACCESS.2025.3597293).
7. Steven Bos and contributors, *MixedRadixCircuitSynthesis (MRCS)*, source snapshot `0865cee`, 2023. [Repository](https://github.com/aiunderstand/MixedRadixCircuitSynthesis/tree/0865cee1f49fe9a803b4910b570f4e96e514c61b).
8. Mohnish Pai, “Ankhdjet: An Open-Source Compiler for Mask-Programmed Ternary Compute-in-ROM on an Open PDK,” arXiv:2608.26206, 2026. [doi:10.48550/arXiv.2608.26206](https://doi.org/10.48550/arXiv.2608.26206).
9. Jerzy Słupecki, “Kryterium pełności wielowartościowych systemów logiki zdań,” *Comptes Rendus des Séances de la Société des Sciences et des Lettres de Varsovie, Classe III*, 32, pp. 102–109, 1939. [Original text](https://rcin.org.pl/Content/50652/PDF/WA35_4821_cz167-r1939-t32_Spraw-TNW-wIII-art1.pdf#page=110).
10. Jean W. Butler, “On complete and independent sets of operations in finite algebras,” *Pacific Journal of Mathematics*, 10(4), pp. 1169–1179, 1960. [Full text](https://msp.org/pjm/1960/10-4/pjm-v10-n4-p10-s.pdf).
11. Stephen Cole Kleene, *Introduction to Metamathematics*, North-Holland / P. Noordhoff, 1952, §64. [Bibliographic record](https://cir.nii.ac.jp/crid/1971712334708500134).
12. Francesco Paoli and Gavin St. John, “Editorial Introduction,” *Studia Logica*, 112, pp. 1201–1214, 2024. [doi:10.1007/s11225-024-10147-9](https://doi.org/10.1007/s11225-024-10147-9).
13. OpenSUSI, Tokai Rika, and contributors, *TR-1um Open Source PDK project*, commit `5d963db`, 2026. [PDK used](https://github.com/OpenSUSI/TR-1um/tree/5d963db9d44e192d37a0489c208bfccf2e2f690c).
14. Robin Lu and contributors, *TR-1um: an experiment to port TR-1um and OpenSUSI MPW template to LibreLane + ALIGN*, source snapshot `b14b3f5`, 2026. [Repository](https://github.com/luyanaa/TR-1um/tree/b14b3f5cca671fd86804e3cca434a0a728c73642).
15. Einosuke Okazaki, *平衡3値論理回路 — OpenSUSI TR-1um (opensusi-tr10-balanced-ternary-logic)*, source snapshot `8a60b97`, 2026. [Source circuits and submission](https://github.com/PenguinEino/opensusi-tr10-balanced-ternary-logic/tree/8a60b97868cad008ff21fefca5da13dcd06063f8).
16. 一般社団法人OpenSUSI, “OpenSUSI-MPW第1回募集を完了 — 企業・大学・高専・高校・個人から49枠の申し込み,” 2026年10月16日. [Announcement](https://prtimes.jp/main/html/rd/p/000000014.000182004.html).
17. Matthias Köfferlein and the KLayout contributors, *KLayout Layout Viewer and Editor*, version 0.30.6, 2026. [Release](https://github.com/KLayout/klayout/releases/tag/v0.30.6).
18. Holger Vogt, Giles Atkinson, and Paolo Nenzi, *Ngspice User's Manual*, version 42, 2023. [Manual](https://sourceforge.net/projects/ngspice/files/ng-spice-rework/old-releases/42/ngspice-42-manual.pdf/download).
19. ISHI会, “2025年12月イベント「東海理化シャトルのオープンPDK解説会」の参加者募集,” 2025年10月30日. [Announcement](https://ishi-kai.org/information/seminar/2025/10/30/DecEvent_1213.html).
20. Zane Hambly, *Takahe*, source snapshot `e7123ea`, 2026. [Binary-encoded SKY130 example](https://github.com/Zaneham/takahe/blob/e7123ea60269922acb283d576678a3aabe51f4f4/designs/setun70_physical.sv).
