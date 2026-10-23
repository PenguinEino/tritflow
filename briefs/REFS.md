# REFS stream brief: references for notebook v3

Work in `~/code-a-chip-v3`, writing only `docs/references.md` and `docs/status/REFS.md`. Do not
commit. Use live web search. Goal: an exact, verifiable reference list for the notebook's claims,
for the Code-a-Chip ISSCC 2027 jury (expert circuit designers).

For each item give full citation (authors, title, venue, year, DOI or URL), one line on what it
supports, and where it is used (`notebook/v3/narrative/*.md`, section). Mark anything you could not
verify; never invent a citation.
1. BitNet b1.58 (ternary-weight LLM; matrix products without multiplication).
2. Ternary logic in non-mass-produced devices: representative CNTFET and memristor ternary logic papers
   (2–4 well-cited ones), and simulation-only ternary CMOS work.
3. Ternary RTL / logic synthesis whose output stops at a gate network (no layout/fabrication).
4. Open CMOS tools that implement ternary values by binary encoding (if any are documented).
5. Słupecki 1939 completeness criterion for many-valued logic (original and an accessible secondary
   source); Kleene three-valued logic.
6. OpenSUSI / TR-1um PDK (repository, release, Japanese open PDK announcement), the OpenMPW shuttle,
   luyanaa/TR-1um LibreLane port, the author's taped-out design repository
   (github.com/PenguinEino/opensusi-tr10-balanced-ternary-logic), KLayout, ngspice.
7. Balanced ternary arithmetic background (e.g. Knuth TAOCP vol. 2 §4.1; Setun) if useful.
Also check whether the opening's statement "製造可能なオープンソースPDKの上で、三値のHDLからGDSまでを通す設計
フローは、我々の知る限り報告されていない" is contradicted by anything you find, and report it plainly.
