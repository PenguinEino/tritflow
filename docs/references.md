# TritFlow v3: references and claim audit

Live literature and source check: **2026-10-23 (JST)**. Citation keys below are stable
labels for the notebook editors. All online sources were checked on this date. Paper
years refer to the published issue or proceedings, except explicitly identified preprints.
Software citations identify a release or source snapshot where one was verified.

**Finding:** no verified counterexample was found to the specific combination of a
ternary HDL, native three-voltage CMOS cells, automatic placement/routing to GDS,
and verification with a fabricable open PDK. This is a bounded search result, not
proof of priority. Earlier open tools already take **binary-encoded ternary designs**
to physical implementation, and fabricated native ternary circuits also exist.
The opening should state its narrower scope explicitly; see the novelty audit below.

“Use” means a proposed citation insertion point, **not** a citation already inserted.
The seven files currently present are `notebook/v3/narrative/00_opening.md` through
`notebook/v3/narrative/06_results.md`. Chapter 6 was added by another stream during
this audit. Its “参考文献” section is the insertion point for the final bibliography;
include each retained citation there as well as at the claim location below.

## Editorial changes supported by this check

| Current claim / location | Evidence and recommended treatment |
|---|---|
| BitNet removes multiplication; opening paragraph 1 and §3.7 | [BITNET2024] supports replacing multiplication by ternary **weights** in linear products with add/subtract/skip. Activations are 8-bit, and other model operations and scaling remain. Restrict the statement to these products. TritFlow's trit-by-trit `dot4` is an educational analogue, not an implementation or performance evaluation of BitNet. |
| Prior ternary work uses non-mass-produced devices or simulation; opening paragraph 1 | [LIN2011], [KHALID2016], and [WU1990] give specific simulation examples. [WANG2021] and [JEONG2019] report physical experiments. These references do not establish a literature-wide majority or the absence of commercial production. Prefer specific examples and “experimental device technologies.” |
| Ternary RTL synthesis stops at a gate network; opening paragraph 1 | Attribute this to [PARK2025] and [TLSYS2026], whose stated deliverable is RTL-to-gate-level synthesis. Do not extend that scope statement to all ternary EDA. [MRCS2023] documents a CMOS path onward through OpenLane. |
| Open CMOS tools encode ternary values in binary; opening paragraph 1 | A documented example is [MRCS2023], with a concrete two-bits-per-trit design in [BOSCALC2023]. Say “MRCS's CMOS backend,” rather than making a claim about every open CMOS tool. |
| No open-PDK ternary HDL-to-GDS flow; opening paragraph 1 | Keep any novelty statement specific to **native three-voltage signals throughout the logic network**. [MRCS2023], [TAKAHE2026], and [ANKHDJET2026] require explicit discussion; see the comparison below. |
| Japan's first commercial-fab open PDK; opening paragraph 2 | [JPANN2025] explicitly makes this statement. Attribute the historical priority to that announcement, or use the factual description “Tokai Rika's NDA-free 1 µm CMOS PDK, released through OpenSUSI.” |
| Japan's first OpenMPW service; opening paragraph 3 | The checked sources establish the **first OpenSUSI-MPW run**, not this broader national priority. Use that name and scope [OPENMPW2026, SHUTTLE2026]. |
| Chips arrive in January 2027; opening paragraph 3 | **Conflicting public evidence:** OpenSUSI's 2026-10-16 announcement says delivery around **February 2027** [OPENMPW2026]. Use the latest public estimate unless the author has newer project-specific confirmation; measurement availability before ISSCC must remain conditional. |

## 1. Ternary-weight LLM motivation

### [BITNET2024]

Shuming Ma, Hongyu Wang, Lingxiao Ma, Lei Wang, Wenhui Wang, Shaohan Huang,
Li Dong, Ruiping Wang, Jilong Xue, and Furu Wei. “The Era of 1-bit LLMs:
All Large Language Models are in 1.58 Bits.” **arXiv:2402.17764**, 2024.
DOI: [10.48550/arXiv.2402.17764](https://doi.org/10.48550/arXiv.2402.17764).
[Paper](https://arxiv.org/abs/2402.17764);
[full text, §§1–2](https://arxiv.org/html/2402.17764v1).

- **Supports:** BitNet b1.58 has ternary quantized weights; weight products can use addition, subtraction, and zero skipping instead of general multipliers.
- **Use:** `notebook/v3/narrative/00_opening.md`, paragraph 1; `notebook/v3/narrative/03_hdl.md`, §3.7 “三値重みの積和”.
- **Verification / limits:** Authors, date, DOI, and full text checked. This is a preprint, not a verified conference publication. §2 specifies 8-bit activations. Do not claim that all LLM computation is ternary, that all multiplications disappear, or that the paper demonstrates native three-voltage silicon.

## 2. Device-level ternary circuits

The following three papers are the selected representative CNTFET/memristor references.
They include simulation and experimental work; citation counts are deliberately not used
as an engineering maturity metric.

### [LIN2011]

Sheng Lin, Yong-Bin Kim, and Fabrizio Lombardi. “CNTFET-Based Design of Ternary
Logic Gates and Arithmetic Circuits.” **IEEE Transactions on Nanotechnology**,
10(2), 217–225, March 2011.
DOI: [10.1109/TNANO.2009.2036845](https://doi.org/10.1109/TNANO.2009.2036845).
[Publisher record](https://ieeexplore.ieee.org/document/5340626).

- **Supports:** Representative multi-threshold CNTFET ternary gates, adders, and multipliers evaluated with SPICE.
- **Use:** `notebook/v3/narrative/00_opening.md`, paragraph 1, CNTFET example; optional context in `notebook/v3/narrative/02_cells.md`, §2.1.
- **Verification / limits:** IEEE-deposited Crossref metadata checked; original paper text was available through indexed facsimile text, while direct IEEE access was bot-blocked. Use the journal year **2011**, not the DOI's 2009 or the incorrect 2012 found in some reference lists. No fabrication or open-PDK layout-flow claim is supported by this source.

### [KHALID2016]

Muhammad Khalid and Jawar Singh. “Memristor based unbalanced ternary logic gates.”
**Analog Integrated Circuits and Signal Processing**, 87(3), 399–406, June 2016
(online 12 April 2016).
DOI: [10.1007/s10470-016-0733-1](https://doi.org/10.1007/s10470-016-0733-1).
[Publisher page and abstract](https://link.springer.com/article/10.1007/s10470-016-0733-1).

- **Supports:** Memristors used as active loads for unbalanced ternary gates, demonstrated by SPICE simulation.
- **Use:** `notebook/v3/narrative/00_opening.md`, paragraph 1, memristor simulation example.
- **Verification / limits:** Publisher metadata and abstract checked; full paper is subscription-only in this session. Its abstract explicitly identifies SPICE as the validation. Unbalanced 0/1/2 logic is not automatically the same cell family or voltage convention as TritFlow.

### [WANG2021]

Xiaoyuan Wang, Pengfei Zhou, Jason K. Eshraghian, Chih-Yang Lin,
Herbert Ho-Ching Iu, Ting-Chang Chang, and Sung-Mo Kang. “High-Density
Memristor-CMOS Ternary Logic Family.” **IEEE Transactions on Circuits and Systems I:
Regular Papers**, 68(1), 264–274, January 2021 (early access 2020).
DOI: [10.1109/TCSI.2020.3027693](https://doi.org/10.1109/TCSI.2020.3027693).
[Author-hosted manuscript](https://www.jasoneshraghian.com/_files/ugd/74f1fb_a74c8dcb15254df7a2b74d138eb29ad2.pdf);
[authors' SPICE repository](https://github.com/jeshraghian/mr-ternary).

- **Supports:** Ternary memristor-CMOS gates with simulations and experimental verification using in-house fabricated ITO memristors.
- **Use:** `notebook/v3/narrative/00_opening.md`, paragraph 1, qualification of the related-work statement.
- **Verification / limits:** Author-hosted full text and companion repository checked. Cite **2021** for the volume/page version; the repository's 2020 BibTeX describes early access. This is evidence against calling memristor ternary work universally simulation-only, but does not establish mass production or a general HDL-to-GDS tool.

### [WU1990] — simulation-based CMOS example

X. W. Wu and F. P. Prosser. “CMOS ternary logic circuits.” **IEE Proceedings G:
Circuits, Devices and Systems**, 137(1), 21–27, February 1990.
DOI: [10.1049/ip-g-2.1990.0005](https://doi.org/10.1049/ip-g-2.1990.0005).
[Publisher record](https://digital-library.theiet.org/doi/10.1049/ip-g-2.1990.0005).

- **Supports:** CMOS ternary circuit design and computer-simulated transfer characteristics, including alternatives to resistor-based circuits.
- **Use:** `notebook/v3/narrative/00_opening.md`, paragraph 1, CMOS simulation example; optional context in `notebook/v3/narrative/02_cells.md`, §2.1.
- **Verification / limits:** DOI/title/authors/year verified against publisher-deposited metadata; pagination and abstract corroborated by the original paper's indexed facsimile. Direct IET/Wiley access returned 403, so full-text review is incomplete. This supports a specific simulation study, not the claim that CMOS ternary logic has never been fabricated. Author initials are retained without guessing their expansion.

### [JEONG2019] — fabricated CMOS exception that should be acknowledged

Jae Won Jeong, Young-Eun Choi, Woo-Seok Kim, Jee-Ho Park, Sunmean Kim,
Sunhae Shin, Kyuho Lee, Jiwon Chang, Seong-Jin Kim, and Kyung Rok Kim.
“Tunnelling-based ternary metal–oxide–semiconductor technology.”
**Nature Electronics**, 2(7), 307–312, 2019.
DOI: [10.1038/s41928-019-0272-8](https://doi.org/10.1038/s41928-019-0272-8).
[Publisher](https://www.nature.com/articles/s41928-019-0272-8);
[authors' institutional record and abstract](https://research.knu.ac.kr/en/publications/tunnelling-based-ternary-metaloxidesemiconductor-technology/).

- **Supports:** Wafer-scale T-CMOS device technology and demonstrated ternary logic/memory functions using a tunnelling-based intermediate state.
- **Use:** `notebook/v3/narrative/00_opening.md`, paragraph 1, related-work qualification.
- **Verification / limits:** Full author list and issue metadata checked against Crossref; abstract checked at the authors' institution. Publisher access required cookies and the company-hosted PDF could not be fetched reliably. No open PDK or HDL-to-GDS flow was verified. Fabricated experimental CMOS is distinct from a commercially offered native ternary standard-cell process.

## 3. Ternary RTL and logic synthesis

### [PARK2025]

Hanmok Park, Seonghoon Kim, Sunmean Kim, and Taigon Song. “An RTL-Based General
Synthesis Methodology for Device-Independent Ternary Logic Circuits.”
**IEEE Access**, 13, 163648–163660, 2025.
DOI: [10.1109/ACCESS.2025.3597293](https://doi.org/10.1109/ACCESS.2025.3597293).
[Institutional abstract](https://research.knu.ac.kr/en/publications/an-rtl-based-general-synthesis-methodology-for-device-independent/);
[authors' laboratory record](https://ice.knu.ac.kr/2571e1cd-a4b8-80a4-b3fa-f29c5b999ac7).

- **Supports:** Verilog-based ternary RTL-to-gate-level synthesis, a GT-LOGIC library, and mappings to several ternary device technologies.
- **Use:** `notebook/v3/narrative/00_opening.md`, paragraph 1, RTL synthesis comparison; optional related work for `notebook/v3/narrative/03_hdl.md`, §3.3.
- **Verification / limits:** Full citation and stated scope checked using the authors' institutional abstract and IEEE-deposited metadata. Indexed paper text also describes the gate-network endpoint. A full publisher PDF could not be independently retrieved. Say “this work targets gate-level netlists”; absence of fabrication in an abstract is not proof about all work by these authors.

### [TLSYS2026]

Jiayi Li, Yao Wang, Yunxia Chen, Yimin Wei, Ziteng Li, Zhijie Yang, Shi Xu,
Lei Wang, and Yuhua Tang. “Tlsys: A Synthesis Framework for Ternary Logic from
RTL to CNFET-Based Gate-Level Netlist.” **Chinese Journal of Electronics**,
35(2), 434–443, March 2026.
DOI: [10.23919/cje.2025.00.418](https://doi.org/10.23919/cje.2025.00.418).
[Publisher record](https://ieeexplore.ieee.org/document/11554546/);
[journal record](https://cje.ejournal.org.cn/article/doi/10.23919/cje.2025.00.418).

- **Supports:** A second, recent RTL synthesis reference whose explicitly named output is a CNFET-based gate-level netlist.
- **Use:** `notebook/v3/narrative/00_opening.md`, paragraph 1; related work for `notebook/v3/narrative/03_hdl.md`, §3.3.
- **Verification / limits:** **Bibliography verified; full-text review incomplete.** All nine authors, DOI, issue, pages, and year were obtained from IEEE-deposited Crossref metadata. IEEE was inaccessible and the journal returned 403. The title verifies the advertised endpoint; do not rely on unreviewed performance or “first” claims from third-party abstracts. The DOI contains 2025, but the issue is 2026.

### [RISTO2021]

Halvor Nybø Risto, Steven Bos, and Henning Gundersen. “Automated synthesis of
netlists for ternary-valued n-ary logic functions in CNTFET circuits.”
In **Proceedings of the 61st SIMS Conference on Simulation and Modelling,
SIMS 2020**, Linköping Electronic Conference Proceedings 176, 483–485,
published 3 March 2021 (conference 22–24 September 2020).
DOI: [10.3384/ecp20176483](https://doi.org/10.3384/ecp20176483).
[Publisher record](https://ep.liu.se/en/conference-article.aspx?Article_No=68&issue=176&series=ecp);
[open full text](https://ep.liu.se/ecp/176/068/SIMS2020_article_ecp20176483.pdf).

- **Supports:** Earlier open-source truth-table-to-CNTFET-SPICE synthesis and HSPICE evaluation of balanced ternary full-adder structures.
- **Use:** `notebook/v3/narrative/00_opening.md`, paragraph 1; optional background in `notebook/v3/narrative/03_hdl.md`, §3.3.
- **Verification / limits:** Publisher metadata and all three pages checked. This is logic-function/netlist synthesis, not an RTL frontend or a physical-design flow. Distinguish the 2020 conference name from the 2021 proceedings publication date.

### [BOS2022]

Steven Bos, Halvor Nybø Risto, and Henning Gundersen. “Beyond CMOS: Ternary and
mixed radix CNTFET circuit design, simulation and verification.” In **2022 IEEE
International Symposium on Circuits and Systems (ISCAS)**, 80–85, 2022.
DOI: [10.1109/ISCAS48785.2022.9937259](https://doi.org/10.1109/ISCAS48785.2022.9937259).
[Conference manuscript](https://confcats-event-sessions.s3.amazonaws.com/iscas22/papers/1613.pdf);
[authors' university publication listing](https://www.usn.no/english/research/our-research-centres-and-groups/technology/ternary-research/).

- **Supports:** Open MRCS design, simulation, and HSPICE-netlist export for ternary/mixed-radix CNTFET circuits.
- **Use:** `notebook/v3/narrative/00_opening.md`, paragraph 1, alongside the actual CMOS-backend software [MRCS2023].
- **Verification / limits:** Authors, DOI, pages, and original manuscript's indexed abstract checked. The former USN Open Archive links now redirect to an archive-migration notice; use the DOI, university listing, and repository, rather than presenting the old archive URL as a working full-text link. CMOS binary encoding is documented more directly in the repository below.

## 4. Open tools and binary-encoded ternary implementations

### [MRCS2023]

Steven Bos and contributors. **MixedRadixCircuitSynthesis (Mixed Radix Circuit
Synthesizer, MRCS)**. GitHub software, source snapshot
`0865cee1f49fe9a803b4910b570f4e96e514c61b`, 26 October 2023.
[Repository](https://github.com/aiunderstand/MixedRadixCircuitSynthesis);
[snapshot README](https://github.com/aiunderstand/MixedRadixCircuitSynthesis/blob/0865cee1f49fe9a803b4910b570f4e96e514c61b/README.md).

- **Supports:** MRCS explicitly converts ternary logic to binary for traditional CMOS, exports Verilog/HSPICE, and documents OpenLane as the route to foundry masks; its native ternary CNTFET backend is separate.
- **Use:** `notebook/v3/narrative/00_opening.md`, paragraph 1, the claim about open CMOS tools.
- **Verification / limits:** README and source-snapshot date checked directly. This is a specific, sufficient example; it does not justify “all CMOS tools binary-encode ternary.” Input is graphical/truth-table circuit design, not a native ternary HDL. Do not import the README's promotional priority claims.

### [BOSCALC2023]

Steven Bos. **Async Balanced Ternary Calculator (tt03-balanced-ternary-calculator)**.
Tiny Tapeout 03 / GitHub hardware design, source snapshot
`3e508e1076355d03bf26db7306de685f191b3dcf`, 7 May 2023.
[Repository](https://github.com/aiunderstand/tt03-balanced-ternary-calculator);
[snapshot README](https://github.com/aiunderstand/tt03-balanced-ternary-calculator/blob/3e508e1076355d03bf26db7306de685f191b3dcf/README.md).

- **Supports:** A concrete MRCS balanced-ternary arithmetic design using two binary bits per trit, with Verilog, verification, and ASIC-submission collateral.
- **Use:** `notebook/v3/narrative/00_opening.md`, paragraph 1, an example accompanying [MRCS2023].
- **Verification / limits:** Project description, encoding, and dated snapshot checked. Submission collateral alone is not evidence of measured silicon. Do not repeat its explanation that CMOS transistors force every ternary implementation to be binary-encoded; TritFlow and [JEONG2019] illustrate why that generalization is unsound.

### [TAKAHE2026] — additional source-code comparison

Zane Hambly. **Takahe**, including `designs/setun70_physical.sv`. GitHub software,
source snapshot `e7123ea60269922acb283d576678a3aabe51f4f4`, 25 August 2026.
[Repository](https://github.com/Zaneham/takahe);
[physical-design example](https://github.com/Zaneham/takahe/blob/e7123ea60269922acb283d576678a3aabe51f4f4/designs/setun70_physical.sv).

- **Supports:** Another open synthesis project with ternary semantics and an explicitly two-bits-per-trit SKY130 implementation example.
- **Use:** `notebook/v3/narrative/00_opening.md`, paragraph 1, novelty audit; optional rather than required notebook bibliography.
- **Verification / limits:** README and the pinned RTL were read directly; the encoding is explicit. Native radix-aware intermediate logic does not establish native three-voltage physical cells. No GDS or silicon verification was reproduced. The example contains unverified broader claims and comments; cite only the inspected encoding and synthesis example.

## 5. Completeness and three-valued logical semantics

### [SLUPECKI1939] — original

Jerzy Słupecki. “Kryterium pełności wielowartościowych systemów logiki zdań.”
**Comptes Rendus des Séances de la Société des Sciences et des Lettres de Varsovie,
Classe III**, 32, 102–109, 1939. Presented by J. Łukasiewicz on 21 February 1939.
[Digitized original volume, article begins at PDF page 110](https://rcin.org.pl/Content/50652/PDF/WA35_4821_cz167-r1939-t32_Spraw-TNW-wIII-art1.pdf#page=110).

- **Supports:** Original source of the functional-completeness criterion used in the notebook.
- **Use:** `notebook/v3/narrative/02_cells.md`, §2.2 “完全性：三値の論理は何から作れるか”.
- **Verification / limits:** Original scan's author/title/opening on printed p.102 and presentation date checked. The 1972 publisher's editorial note confirms volume 32 and pp.102–109. The Polish proof was not fully translated in this audit; the theorem's operational statement was checked in [BUTLER1960]. No DOI for the 1939 original was verified. Do not attach the 1972 translation's DOI to the 1939 publication as if it were the original DOI.

### [SLUPECKI1972] — English translation

Jerzy Słupecki. “A criterion of fullness of many-valued systems of propositional
logic.” **Studia Logica**, 30, 153–157, December 1972. English translation of
[SLUPECKI1939].
DOI: [10.1007/BF02120845](https://doi.org/10.1007/BF02120845).
[Publisher page, including original-publication note](https://link.springer.com/article/10.1007/BF02120845).

- **Supports:** An English citation to the original criterion, with authoritative bibliographic provenance.
- **Use:** `notebook/v3/narrative/02_cells.md`, §2.2, next to [SLUPECKI1939].
- **Verification / limits:** Publisher metadata and editorial note checked; the translated full text was subscription-only. This is not the accessible proof used for checking the criterion. Some older secondary citations give volume 33 or pp.102–110 for the original; follow the scan and translation editor's note above.

### [BUTLER1960] — accessible proof and secondary account

Jean W. Butler. “On complete and independent sets of operations in finite algebras.”
**Pacific Journal of Mathematics**, 10(4), 1169–1179, 1960.
[Open publisher PDF](https://msp.org/pjm/1960/10-4/pjm-v10-n4-p10-s.pdf).

- **Supports:** All unary functions together with a surjective operation depending essentially on at least two arguments generate all operations on a finite set of size at least three; the binary case is sufficient for TritFlow.
- **Use:** `notebook/v3/narrative/02_cells.md`, §2.2, accessible explanation/proof alongside the original citation.
- **Verification / limits:** Full text checked: Lemma 6 on p.1175 and the added-in-proof attribution to Słupecki on p.1179. Butler is a later proof/generalization and secondary account of Słupecki's result, not the 1939 original. Its historical volume-number typo should not be copied.

**Application to TritFlow (project derivation, not a claim made by Słupecki):** on
`{-1,0,+1}`, `NANY(a,b) = -clamp(a+b,-1,+1)` is surjective and depends on both
inputs. Independent finite closure enumeration from the identity and constant +1
produced **2, 5, 11, 18, 25, 27** unary functions at maximum depths 0 through 5.
Together these satisfy the criterion. NANY alone preserves zero and its unary
closure contains only three functions. The original theorem does not refer to
TritFlow, NANY, CMOS, or a physical TIE cell; cite the theorem for the implication
and retain the notebook's own construction for the 27-function premise.

### [KLEENE1952]

Stephen Cole Kleene. **Introduction to Metamathematics**. Bibliotheca Mathematica,
vol.1. Amsterdam: North-Holland; Groningen: P. Noordhoff, 1952, §64.
[Library bibliographic record](https://cir.nii.ac.jp/crid/1971712334708500134).

- **Supports:** The historical source for strong and weak three-valued connective tables arising from partial recursive predicates.
- **Use:** `notebook/v3/narrative/01_first.md`, the `a & ~a` discussion; `notebook/v3/narrative/03_hdl.md`, §§3.1 and 3.3.
- **Verification / limits:** Original-edition authorship/publishers/year checked in the library record; §64 and the tables cross-checked in [PAOLI2024]. The original book's §64 was not directly read, and no original-edition DOI was verified. Use the accessible account below for the actual truth tables.

### [PAOLI2024] — accessible strong/weak Kleene distinction

Francesco Paoli and Gavin St. John. “Editorial Introduction.” **Studia Logica**,
112, 1201–1214, 2024, special issue “Strong and Weak Kleene Logics.”
DOI: [10.1007/s11225-024-10147-9](https://doi.org/10.1007/s11225-024-10147-9).
[Publisher](https://link.springer.com/article/10.1007/s11225-024-10147-9);
[open full text](https://d-nb.info/1355549221/34).

- **Supports:** Strong Kleene NOT/AND/OR tables, distinguished from weak Kleene's propagation of the undefined value.
- **Use:** `notebook/v3/narrative/01_first.md`, truth-table discussion; `notebook/v3/narrative/03_hdl.md`, §§3.1 and 3.3.
- **Verification / limits:** Full text, especially pp.1201–1202, checked. Relabeling false/undefined/true as −1/0/+1 gives negation/min/max. This correspondence concerns these connectives; it does not make every TritVerilog operation part of Kleene's original logic. The circuit's 0 V is a valid stable logic level, even where the HDL gives its middle value an “undefined” interpretation.

## 6. PDK, shuttle, source design, and tools

### [TR1UM2026] — actual notebook PDK snapshot

OpenSUSI, Tokai Rika, and contributors. **TR-1um Open Source PDK project
(NDA-free 1um CMOS PDK)**. GitHub PDK, commit
`5d963db9d44e192d37a0489c208bfccf2e2f690c`, 12 October 2026.
[Repository](https://github.com/OpenSUSI/TR-1um);
[pinned source](https://github.com/OpenSUSI/TR-1um/tree/5d963db9d44e192d37a0489c208bfccf2e2f690c).

- **Supports:** The public TR-1um process collateral, PCells, models, DRC/LVS decks, and Apache-2.0 PDK source used by this notebook.
- **Use:** `notebook/v3/narrative/00_opening.md`, paragraph 2; `01_first.md`, DRC/LVS step; `02_cells.md`, §§2.1 and 2.4; `04_pnr.md`, process layers; `05_verify.md`, §§5.1–5.2, all under `notebook/v3/narrative/`.
- **Verification / limits:** README/license and live commit identity checked; full SHA matches `notebook/setup_pins.json`. This is a pinned development snapshot, **not** release v1.2609.0. Repository availability alone does not prove a particular generated design is accepted by the foundry; use TritFlow's own DRC/LVS results for that design.

### [TR1UMREL2026] — public release provenance

OpenSUSI and contributors. **TR-1um PDK v1.2609.0**. GitHub release,
30 June 2026, tag `v1.2609.0`, commit
`c5bcc378c1c3d041fef6cc15e70d173bb80dcedb`.
[Release page](https://github.com/OpenSUSI/TR-1um/releases/tag/v1.2609.0).

- **Supports:** An identified public PDK release intended for the September 2026 OpenSUSI MPW shuttle.
- **Use:** `notebook/v3/narrative/00_opening.md`, PDK/shuttle background; final bibliography.
- **Verification / limits:** GitHub release timestamp, tag target, and release text checked through the live GitHub API. The release name's “2609” is not its publication date. Distinguish this release from [TR1UM2026] when documenting reproducibility.

### [JPANN2025] — contemporary Japanese open-PDK announcement

ISHI会 (ISHI-KAI). “2025年12月イベント「東海理化シャトルのオープンPDK解説会」の参加者募集.”
**ISHI-KAI's Homepage**, 30 October 2025.
[Announcement](https://ishi-kai.org/information/seminar/2025/10/30/DecEvent_1213.html).

- **Supports:** A contemporary Japanese announcement explicitly identifying the PDK as Japan's first open PDK from a commercial fab and describing OpenSUSI's release.
- **Use:** `notebook/v3/narrative/00_opening.md`, paragraph 2.
- **Verification / limits:** Organizer's original announcement checked. This verifies what the announcement says, not an exhaustive historical priority search. OpenSUSI's own later statement [OPENMPW2026] independently dates the joint PDK-opening announcement to October 2025. A separate original October 2025 corporate press release was not located; do not invent its title or date.

### [OPENMPW2026] — manufacturing and current delivery estimate

一般社団法人OpenSUSI. “OpenSUSI-MPW第1回募集を完了 — 企業・大学・高専・高校・個人から49枠の申し込み.”
**OpenSUSI press release / PR TIMES**, 16 October 2026, 12:00 JST.
[Official press release](https://prtimes.jp/main/html/rd/p/000000014.000182004.html).

- **Supports:** The first OpenSUSI-MPW call, September 18 close, manufacturing commission to Tokai Rika, 1 µm/two-metal process, and expected delivery around February 2027.
- **Use:** `notebook/v3/narrative/00_opening.md`, paragraphs 2–3 and the conditional measurement plan.
- **Verification / limits:** Full issuer-authored release checked. It dates the service start to June 2026 and the PDK-opening announcement to October 2025. Its February delivery estimate conflicts with the notebook's January claim; neither a future delivery date nor measurement before ISSCC is guaranteed.

### [MPWSERVICE] — shuttle service reference

OpenSUSI. **OpenSUSI-MPW Service**. OpenSUSI service website, undated,
accessed 23 October 2026.
[Service page](https://www.opensusi.org/mpw-service).

- **Supports:** Public availability and submission conditions of the TR-1um MPW service, including public design repositories.
- **Use:** `notebook/v3/narrative/00_opening.md`, paragraph 3 and reuse paragraph; `notebook/v3/narrative/06_results.md`, §6.5 “シャトル用の最上位レイアウト”.
- **Verification / limits:** Live service page checked. Use [OPENMPW2026] for dated manufacturing/delivery statements. Do not confuse the ISHI-KAI sponsored participant slots with the commercial shuttle's total applications, or a dry run with a manufacturing order.

### [SHUTTLE2026] — public evidence connecting this design to the submission

ISHI会 (ISHI-KAI). “ISHI会版OpenMPW OpenSUSI-TR10-1投稿完了！！！～2026年OpenSUSI-TR10-1（OpenSUSI-TR10シャトル）.”
**ISHI-KAI's Homepage**, 25 September 2026, with the linked
**ISHI-KAI_Multiple_Projects_OpenMPW_OpenSUSI-TR10-1** GitHub project index.
[Completion announcement](https://ishi-kai.org/openmpw/shuttle/opensusi-tr10/2026/09/25/shuttle_ISHI-Kai_OpenMPW-OpenSUSI-TR10-1_submitted.html);
[project index](https://github.com/ishi-kai/ISHI-KAI_Multiple_Projects_OpenMPW_OpenSUSI-TR10-1);
[PenguinEino balanced-ternary submission](https://github.com/ishi-kai/ISHI-KAI_Multiple_Projects_OpenMPW_OpenSUSI-TR10-1/tree/main/member_project/balanced-ternary-logic/PenguinEino/).

- **Supports:** ISHI-KAI reports completing its shuttle submissions, and its public index identifies PenguinEino's balanced-ternary circuit among them.
- **Use:** `notebook/v3/narrative/00_opening.md`, paragraph 3, alongside [OKAZAKI2026] and [OPENMPW2026].
- **Verification / limits:** Announcement and linked index checked directly, including the named balanced-ternary entry. This is public submission/manufacturing provenance, not evidence that silicon has arrived or works. The original full-custom circuit is the submitted design; TritFlow's reworked standard-cell library and `dot4` are not thereby already taped out.

### [LU2026] — existing binary TR-1um physical-design flow

Robin Lu (GitHub: luyanaa) and contributors. **TR-1um: an experiment to port TR-1um
and OpenSUSI MPW template to LibreLane + ALIGN**. GitHub software/PDK fork,
source snapshot `b14b3f5cca671fd86804e3cca434a0a728c73642`, 20 September 2026.
[Repository](https://github.com/luyanaa/TR-1um);
[pinned flow documentation](https://github.com/luyanaa/TR-1um/blob/b14b3f5cca671fd86804e3cca434a0a728c73642/flow/README.md).

- **Supports:** Existing open LibreLane/OpenROAD digital-design integration and ALIGN work for TR-1um; examples use conventional binary standard cells.
- **Use:** `notebook/v3/narrative/00_opening.md`, PDK ecosystem/related work; `notebook/v3/narrative/04_pnr.md`, introduction if positioning the custom ternary router.
- **Verification / limits:** README, flow documentation, and snapshot date checked. The repository reports DRC/LVS-tested binary examples but also qualification limits. Credit its actual progress; do not call it a native ternary backend or imply this audit reproduced its signoff results.

### [OKAZAKI2026] — source circuits, not TritFlow's new flow

Einosuke Okazaki (岡崎 英之介; GitHub: PenguinEino). **平衡3値論理回路 — OpenSUSI TR-1um
(opensusi-tr10-balanced-ternary-logic)**. GitHub hardware design,
source snapshot `8a60b97868cad008ff21fefca5da13dcd06063f8`, 24 September 2026 (UTC).
[Repository](https://github.com/PenguinEino/opensusi-tr10-balanced-ternary-logic);
[pinned submission description](https://github.com/PenguinEino/opensusi-tr10-balanced-ternary-logic/blob/8a60b97868cad008ff21fefca5da13dcd06063f8/submission/README.md).

- **Supports:** Original ±5 V balanced-ternary gates and the one-trit multiply-add slice, with Xschem schematics, KLayout layouts, extraction, and simulation collateral.
- **Use:** `notebook/v3/narrative/00_opening.md`, paragraphs 2–3; `02_cells.md`, §§2.1, 2.3–2.4; `03_hdl.md`, §§3.4 and 3.7, all under `notebook/v3/narrative/`.
- **Verification / limits:** Public README/submission contents and snapshot checked; author identity follows `docs/author.md`. That design cites PDK dev `9ef2ac3`, whereas the notebook uses [TR1UM2026]. Do not erase this provenance difference or treat submitted SPICE results as measured silicon.

### [KLAYOUT2026]

Matthias Köfferlein and the KLayout contributors. **KLayout Layout Viewer and
Editor**, version 0.30.6, 2026. KLayout software.
[Official project description](https://www.klayout.de/intro.html);
[official release notes](https://www.klayout.de/development.html);
[source release](https://github.com/KLayout/klayout/releases/tag/v0.30.6).

- **Supports:** Scriptable GDS/PCell layout generation and the DRC/LVS engine used with the PDK's own rule decks.
- **Use:** `notebook/v3/narrative/01_first.md`, GDS/verification steps; `02_cells.md`, §2.4; `04_pnr.md`; `05_verify.md`, §§5.1–5.2, all under `notebook/v3/narrative/`.
- **Verification / limits:** Official features and version checked against `notebook/setup_pins.json`. Release notes give 7 February 2026; GitHub's release publication timestamp is 10 February 2026. KLayout is GPL-2.0-or-later, separate from TritFlow's Apache-2.0 code. A tool citation does not independently validate generated layouts or extraction.

### [NGSPICE42]

Holger Vogt, Giles Atkinson, and Paolo Nenzi. **Ngspice User's Manual**, version 42,
27 December 2023. ngspice project, 2023.
[Official release archive](https://sourceforge.net/projects/ngspice/files/ng-spice-rework/old-releases/42/);
[release manual](https://sourceforge.net/projects/ngspice/files/ng-spice-rework/old-releases/42/ngspice-42-manual.pdf/download).

- **Supports:** The ngspice circuit simulator's device-model, operating-point, DC, and transient-analysis facilities.
- **Use:** `notebook/v3/narrative/01_first.md`, SPICE step; `02_cells.md`, §2.1; `05_verify.md`, simulation/timing discussion, all under `notebook/v3/narrative/`.
- **Verification / limits:** Version-42 PDF title page, author list, and date checked directly. Cite **42**, matching `notebook/setup_pins.json` (`42+ds-3build1` package), rather than the older development environment's 46 or the current latest release. TritFlow's ±0.5 V settling-band definition and geometric wire-capacitance estimate are project methods, not ngspice-standard signoff definitions.

## 7. Balanced ternary arithmetic and historical context

### [KNUTH1997]

Donald E. Knuth. **The Art of Computer Programming, Volume 2: Seminumerical
Algorithms**, 3rd ed. Reading, MA: Addison-Wesley, 1997, §4.1 “Positional Number
Systems,” balanced-ternary discussion. ISBN 978-0-201-89684-8.
[Author's edition listing](https://cs.stanford.edu/~knuth/taocp.html);
[publisher's openly accessible §4.1 excerpt](https://www.informit.com/articles/article.aspx?p=2221791).

- **Supports:** Balanced ternary's −1/0/+1 digits and positional arithmetic background.
- **Use:** `notebook/v3/narrative/00_opening.md`, paragraph 2; `notebook/v3/narrative/03_hdl.md`, §3.1 “値と数”.
- **Verification / limits:** Edition metadata and the publisher's §4.1 excerpt, including balanced ternary, checked. The excerpt was posted in 2014; the cited book edition is 1997. Avoid mixing second-edition page numbers into this citation. Digit symmetry is not evidence of area, power, or performance superiority.

### [SETUN2011]

Nikolay Petrovich Brusentsov and José Ramil Alvarez. “Ternary Computers: The Setun
and the Setun 70.” In John Impagliazzo and Eduard Proydakov (eds.),
**Perspectives on Soviet and Russian Computing (SoRuCom 2006)**, IFIP Advances
in Information and Communication Technology 357, 74–80. Berlin/Heidelberg:
Springer, 2011.
DOI: [10.1007/978-3-642-22816-2_10](https://doi.org/10.1007/978-3-642-22816-2_10).
[Publisher](https://link.springer.com/chapter/10.1007/978-3-642-22816-2_10);
[open IFIP full text](https://dl.ifip.org/db/conf/ifip9/sorucom2006/BrusentsovA06.pdf).

- **Supports:** Historical built ternary computers, balanced-ternary arithmetic, and practical Setun development/use.
- **Use:** Optional historical sentence in `notebook/v3/narrative/00_opening.md`, paragraph 2, or `notebook/v3/narrative/03_hdl.md`, §3.1. No Setun sentence currently needs a citation.
- **Verification / limits:** Publisher record and open chapter checked. The conference was 2006, the book publication 2011; do not cite the archive's 2017 upload as the paper year. Setun is not evidence for an open CMOS PDK, modern HDL, or a GDS flow.

## 8. Close prior art found during the novelty search

### [ANKHDJET2026]

Mohnish Pai. “Ankhdjet: An Open-Source Compiler for Mask-Programmed Ternary
Compute-in-ROM on an Open PDK.” **arXiv:2608.26206**, 26 August 2026.
DOI: [10.48550/arXiv.2608.26206](https://doi.org/10.48550/arXiv.2608.26206).
[Paper](https://arxiv.org/abs/2608.26206);
[full text](https://arxiv.org/html/2608.26206v1).

- **Supports:** A reported open ternary-weight-checkpoint-to-mask compiler and SKY130 physical implementation with open verification tools.
- **Use:** `notebook/v3/narrative/00_opening.md`, paragraph 1, novelty/related-work qualification; include if retaining an open-PDK priority claim.
- **Verification / limits:** Full text checked, especially §§III-B–III-D and the digital-readout distinction. It generates structural SystemVerilog and mask programs for a fixed compute-in-ROM architecture; the digital path uses full-swing sensing and bit-serial accumulation. It is not a general ternary-HDL mapper onto native three-voltage standard cells. Its signoff and submission claims are the preprint author's reports, not reproduced results or measured silicon.

### [HAZZAZI2026] — verified bibliography, unresolved technical scope

Fawwaz Hazzazi. “Unified Mixed-Signal Design: Integrating Memristor-Based Ternary
Logic with an Open-Source Sky130 CMOS Non-Inverting Op-AMP.” In **2026 IEEE 5th
International Conference on Computing and Machine Intelligence (ICMI)**, 1–3, 2026.
DOI: [10.1109/ICMI68585.2026.11539888](https://doi.org/10.1109/ICMI68585.2026.11539888).
[Publisher record](https://ieeexplore.ieee.org/document/11539888/).

- **Supports:** Bibliographic evidence that ternary memristor logic and an open SKY130 mixed-signal flow have been discussed together.
- **Use:** `notebook/v3/narrative/00_opening.md`, paragraph 1, novelty-search record only; not a required notebook citation without full-text review.
- **Verification / limits:** **Technical scope unverified.** Author/title/venue/pages/year/DOI checked against IEEE-deposited Crossref metadata. Only a third-party abstract was accessible; no technical conclusion here relies on it. No ternary HDL frontend, native-CMOS-only cell library, or general HDL-to-GDS flow was verified. This lead prevents treating this search as exhaustive.

## Novelty audit: what the opening can and cannot claim

The sentence under review is:

> 製造可能なオープンソースPDKの上で、三値のHDLからGDSまでを通す設計フローは、我々の知る限り報告されていない。

The surrounding paragraph implies native ternary voltage signals, but this sentence
does not state that restriction. **A general claim that ternary designs have not
reached masks on open PDKs is contradicted by the prior work above.** The narrower
native-three-voltage HDL-to-GDS combination was not contradicted by any source whose
technical scope could be verified in this audit.

| Work | Input / ternary representation | Verified reported endpoint | Relation to the proposed distinction |
|---|---|---|---|
| [PARK2025] | Verilog-based ternary RTL; generic ternary gate mapping | Gate-level netlist | Direct synthesis prior art; no fabricable-open-PDK physical flow verified. |
| [TLSYS2026] | Ternary RTL; CNFET target | Gate-level netlist, as stated in title | Direct synthesis prior art; full-text physical scope remains unreviewed. |
| [RISTO2021], [BOS2022] | Truth tables / graphical circuits; native CNTFET models | SPICE/HSPICE netlists and simulation | Earlier open native-ternary circuit synthesis, without the claimed CMOS physical flow. |
| [MRCS2023], [BOSCALC2023] | Graphical/truth-table ternary design; CMOS backend uses binary encoding | Verilog and documented OpenLane-to-mask path; Tiny Tapeout design collateral | Contradicts a broad “open ternary tools stop at gates” claim; physical CMOS logic is binary-encoded. |
| [TAKAHE2026] | HDL; radix-aware logic and a two-bit-encoded SKY130 example | Mapped binary foundry-cell netlist; README reports OpenROAD use | Requires explicit native-voltage qualification. This audit did not verify a ternary GDS result. |
| [WANG2021], [JEONG2019] | Experimental native ternary devices/circuits | Fabricated devices and demonstrated functions | Contradict an implication that all native ternary work is simulation-only; no open-PDK HDL-to-GDS flow verified. |
| [LU2026] | Conventional binary RTL and TR-1um cells | Repository reports physical GDS and DRC/LVS examples | Establishes an existing open TR-1um flow; ternary-specific integration remains distinct. |
| [OKAZAKI2026], [SHUTTLE2026] | Full-custom native balanced-ternary schematics | GDS and public shuttle submission | Author's prior physical circuits, without an HDL synthesis frontend; disclose this foundation. |
| [ANKHDJET2026] | Ternary-weight checkpoint; fixed ROM macro plus structural RTL | Reported open SKY130 masks, checks, and shuttle submission | Close open-PDK compiler prior art; architecture and physical signal representation differ from a general native three-voltage cell flow. |
| [HAZZAZI2026] | Ternary memristor / SKY130 mixed-signal topic | Not independently verified | An unresolved related lead, not a confirmed exact counterexample or a dismissed one. |

A defensible replacement should describe the demonstrated contribution directly:
TritFlow integrates native three-voltage CMOS cells, a combinational ternary HDL,
synthesis, placement/routing, GDS, PDK-deck DRC/LVS, and post-layout simulation on
TR-1um. If a priority sentence is retained, qualify it with **native three-voltage
signals**, the **combined flow**, and the **2026-10-23 search cutoff**. The phrase
“to our knowledge” does not remove the need to cite close prior art.

The search included general and exact-title combinations of `ternary`, `balanced
ternary`, `RTL synthesis`, `HDL`, `GDS`, `GDSII`, `layout`, `fabrication`, `open-source`,
`open PDK`, `SKY130`, `CNTFET`, and `memristor`, plus targeted checks of MRCS,
Tiny Tapeout ternary designs, Takahe, Ankhdjet, and the TR-1um ecosystem. This was
not a systematic review, exhaustive patent search, or reproduction of outside flows.

## Remaining verification limits and integration notes

- Primary paper text or an author/institutional source supports technical claims wherever available. Publisher-deposited Crossref metadata was used to resolve exact author lists, DOI/year differences, and pages; it does not substitute for reading technical results.
- [TLSYS2026] and [HAZZAZI2026] have verified bibliographies but incomplete primary-text access. [KHALID2016], [JEONG2019], and [PARK2025] have verified primary abstracts but incomplete full-text access. [WU1990] has a verified bibliography and indexed original text but incomplete direct access. These limits are explicit above.
- Słupecki's original scan was located and its opening checked; the original proof was not fully translated. Kleene's original book metadata and §64 attribution were checked, but the actual connective tables were verified through the open scholarly account [PAOLI2024].
- No independently sourced guarantee of January 2027 delivery, measurement before ISSCC, or “Japan's first OpenMPW service” was found. The current issuer announcement instead gives a February delivery estimate.
- Citations do not establish TritFlow's benchmark counts, ±0.5 V criterion, STA error, layout area, timing, power, or silicon behavior. Those claims require the notebook's generated data and clearly distinguished simulation/submission/measurement status.
- No narrative, notebook generator, setup pin, shared interface, or other stream's file was edited by REFS. Editors should insert the chosen references at the locations above and assemble the final bibliography in `notebook/v3/narrative/06_results.md`, “参考文献”.
