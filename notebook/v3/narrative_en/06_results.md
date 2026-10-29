## 6. Evaluation and Reuse

Chapter 5 verified the four-term dot product dot4 with post-layout simulation and compared it with ternary STA. This chapter evaluates area, delay and static power as the term count changes, then reruns the flow after an HDL change and presents a shuttle top-level layout.

### 6.1 Dot-Product Size and Area

The evaluated circuit is a dot product of one-trit weights and inputs, y = w<sub>0</sub>x<sub>0</sub> + … + w<sub>N−1</sub>x<sub>N−1</sub>. The output uses the minimum number of trits needed to represent −N through +N. Weights remain HDL inputs but are fixed in simulation to repetitions of (+1, −1, +1, +1). Addition uses the same HDL form as section 3.7, without structural changes for different term counts.

The tables present recorded place and route and verification results. Area is measured from the routed die outline.

<!-- code: scale6 -->

### 6.2 Static and Time-Average Power

States that hold 0 V by resistive division draw static current even without input transitions. NANY also has zero-output states in which VMID clamps conduct while the VDD and VSS transistor stacks are cut off. Static power is calculated from DC operating points for states in the recorded input sequence.

Time-average supply power excludes the power from the input voltage sources.

<!-- code: power6 -->

### 6.3 STA and SPICE

Each circuit uses an input sequence that generates and clears positive and negative carries. The four-term sequence differs from chapter 5. STA uses the same fixed weights. STA and SPICE use identical input transitions, output load, input slew and wire capacitance. The reported delay is each output's maximum settling time over that sequence.

The effect of wire capacitance is evaluated by removing only the estimated wire capacitance from the same extracted circuit. STA compares both cases at every size; SPICE compares them for four terms. Both cases retain intrinsic device capacitance and the 100 fF output load.

At N=16, some NANY loads exceed the 2 pF characterization limit, reaching 2.862 pF. For loads beyond the table, the delay is read from the straight line through the table's two largest-load points.

<!-- code: timing6 -->

### 6.4 Editing HDL and Rerunning the Flow

Making inference weights HDL constants allows logic synthesis to simplify the corresponding multiplier circuits. The following circuit fixes dot4's weights to (+1, −1, +1, +1). After changes to the expression and port declarations, the same execution cell runs logic synthesis through post-layout simulation.

<!-- code: reuse_source -->

SPICE covers all states when the total is at most 27. Otherwise, it selects 11 states from the zero input, all −1 and all +1 inputs, alternating signs, and single-input ±1 excursions. Expected outputs come from evaluating the HDL, independently of the synthesized netlist.

<!-- code: reuse6 -->

### 6.5 Shuttle Top-Level Layout

The top-level layout adds pads, power routing and the PDK's stock MPW frame to dot4. The frame's electrostatic discharge (ESD) supply shares VSS with the circuit's VSS (−5 V) and takes VDD at +5 V from a separate terminal. The −5 to +5 V ternary signals then stay within the ESD supply range, so the stock pads are used as they are. The taped-out chip uses the same connection.

<!-- code: shuttle6 -->

### 6.6 Conclusion

### References

1. Shuming Ma et al., “The Era of 1-bit LLMs: All Large Language Models are in 1.58 Bits,” arXiv:2402.17764, 2024. [doi:10.48550/arXiv.2402.17764](https://doi.org/10.48550/arXiv.2402.17764).
2. Sheng Lin, Yong-Bin Kim, and Fabrizio Lombardi, “CNTFET-Based Design of Ternary Logic Gates and Arithmetic Circuits,” *IEEE Transactions on Nanotechnology*, 10(2), pp. 217–225, 2011. [doi:10.1109/TNANO.2009.2036845](https://doi.org/10.1109/TNANO.2009.2036845).
3. Xiao-Yuan Wang et al., “High-Density Memristor-CMOS Ternary Logic Family,” *IEEE Transactions on Circuits and Systems I: Regular Papers*, 68(1), pp. 264–274, 2021. [doi:10.1109/TCSI.2020.3027693](https://doi.org/10.1109/TCSI.2020.3027693).
4. Jae Won Jeong et al., “Tunnelling-based ternary metal–oxide–semiconductor technology,” *Nature Electronics*, 2(7), pp. 307–312, 2019. [doi:10.1038/s41928-019-0272-8](https://doi.org/10.1038/s41928-019-0272-8).
5. Hanmok Park, Seonghoon Kim, Sunmean Kim, and Taigon Song, “An RTL-Based General Synthesis Methodology for Device-Independent Ternary Logic Circuits,” *IEEE Access*, 13, pp. 163648–163660, 2025. [doi:10.1109/ACCESS.2025.3597293](https://doi.org/10.1109/ACCESS.2025.3597293).
6. Steven Bos and contributors, *MixedRadixCircuitSynthesis (MRCS)*, source snapshot `0865cee`, 2023. [Repository](https://github.com/aiunderstand/MixedRadixCircuitSynthesis/tree/0865cee1f49fe9a803b4910b570f4e96e514c61b).
7. Mohnish Pai, “Ankhdjet: An Open-Source Compiler for Mask-Programmed Ternary Compute-in-ROM on an Open PDK,” arXiv:2608.26206, 2026. [doi:10.48550/arXiv.2608.26206](https://doi.org/10.48550/arXiv.2608.26206).
8. Jerzy Słupecki, “Kryterium pełności wielowartościowych systemów logiki zdań,” *Comptes Rendus des Séances de la Société des Sciences et des Lettres de Varsovie, Classe III*, 32, pp. 102–109, 1939. [Original text](https://rcin.org.pl/Content/50652/PDF/WA35_4821_cz167-r1939-t32_Spraw-TNW-wIII-art1.pdf#page=110).
9. Jean W. Butler, “On complete and independent sets of operations in finite algebras,” *Pacific Journal of Mathematics*, 10(4), pp. 1169–1179, 1960. [Full text](https://msp.org/pjm/1960/10-4/pjm-v10-n4-p10-s.pdf).
10. Stephen Cole Kleene, *Introduction to Metamathematics*, North-Holland / P. Noordhoff, 1952, §64. [Bibliographic record](https://cir.nii.ac.jp/crid/1971712334708500134).
11. Francesco Paoli and Gavin St. John, “Editorial Introduction,” *Studia Logica*, 112, pp. 1201–1214, 2024. [doi:10.1007/s11225-024-10147-9](https://doi.org/10.1007/s11225-024-10147-9).
12. OpenSUSI, Tokai Rika, and contributors, *TR-1um Open Source PDK project*, commit `5d963db`, 2026. [PDK used](https://github.com/OpenSUSI/TR-1um/tree/5d963db9d44e192d37a0489c208bfccf2e2f690c).
13. Robin Lu and contributors, *TR-1um: an experiment to port TR-1um and OpenSUSI MPW template to LibreLane + ALIGN*, source snapshot `b14b3f5`, 2026. [Repository](https://github.com/luyanaa/TR-1um/tree/b14b3f5cca671fd86804e3cca434a0a728c73642).
14. Einosuke Okazaki, *平衡3値論理回路 — OpenSUSI TR-1um (opensusi-tr10-balanced-ternary-logic)*, source snapshot `8a60b97`, 2026. [Source circuits and submission](https://github.com/PenguinEino/opensusi-tr10-balanced-ternary-logic/tree/8a60b97868cad008ff21fefca5da13dcd06063f8).
15. 一般社団法人OpenSUSI, “OpenSUSI-MPW第1回募集を完了 — 企業・大学・高専・高校・個人から49枠の申し込み,” 2026年10月16日. [Announcement](https://prtimes.jp/main/html/rd/p/000000014.000182004.html).
16. Matthias Köfferlein and the KLayout contributors, *KLayout Layout Viewer and Editor*, version 0.30.6, 2026. [Release](https://github.com/KLayout/klayout/releases/tag/v0.30.6).
17. Holger Vogt, Giles Atkinson, and Paolo Nenzi, *Ngspice User's Manual*, version 42, 2023. [Manual](https://sourceforge.net/projects/ngspice/files/ng-spice-rework/old-releases/42/ngspice-42-manual.pdf/download).
18. ISHI会, “2025年12月イベント「東海理化シャトルのオープンPDK解説会」の参加者募集,” 2025年10月30日. [Announcement](https://ishi-kai.org/information/seminar/2025/10/30/DecEvent_1213.html).
19. Zane Hambly, *Takahe*, source snapshot `e7123ea`, 2026. [Binary-encoded SKY130 example](https://github.com/Zaneham/takahe/blob/e7123ea60269922acb283d576678a3aabe51f4f4/designs/setun70_physical.sv).
20. Nikolay P. Brusentsov and José Ramil Alvarez, “Ternary Computers: The Setun and the Setun 70,” in *Perspectives on Soviet and Russian Computing (SoRuCom 2011)*, IFIP AICT 357, Springer, pp. 74–80, 2011. [doi:10.1007/978-3-642-22816-2_10](https://doi.org/10.1007/978-3-642-22816-2_10)
