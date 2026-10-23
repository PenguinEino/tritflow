# EN stream brief: English edition of notebook v3

Work in `~/code-a-chip-v3-en` (branch `notebook-v3-en`, forked from `notebook-v3`). Do not commit or
push; the integrator merges your branch into `notebook-v3`. Another stream (V3) is still changing
`notebook-v3` in parallel (chapter 6, a fix in 5-3), so keep your edits small and mechanical in shared
files to make the merge easy. Record decisions in `docs/status/EN.md`.

The English notebook is the primary submission for the international Code-a-Chip ISSCC 2027 jury;
the Japanese one is a companion. Same cell structure, same figures, same interactions.

1. Language switch for everything the notebook prints: step logs and error boxes (`notebook/live.py`),
   tables, notes, conditions and widget labels (`notebook/views.py`, `cell_views.py`, `pnr_views.py`,
   `inverter_views.py`, `tritflow/viz`), schematic labels (`tritflow.schematic.set_language` already
   exists — follow that pattern: one module-level language, Japanese default so v2/v3-ja stay byte-
   identical in output). The table pictures under `notebook/assets/tables/` need English variants
   (`notebook/v2/make_tables.py`). Figures in `figures/out/*_ja.png` have English counterparts already
   (`*.png` without `_ja`); check.
2. Builder: `notebook/v3/make_notebook.py --lang en` produces `notebook/v3/tritflow_en.ipynb` from
   `notebook/v3/narrative_en/*.md` and English code cells (the code is identical; only the cell title
   comments and the strings passed to step()/need()/note() are translated — keep one CODE definition
   with the language-dependent strings looked up, not two copies of every cell).
3. Translate chapters 0–5 (`notebook/v3/narrative/00–05`) into `narrative_en/`. Register: concise
   technical English for IC designers (an ISSCC paper's tone), standard terms (place and route, logic
   synthesis, extraction, post-layout simulation, DRC/LVS), no marketing words, no paraphrase of what
   outputs show. Keep every number and claim exactly; keep math as is.
4. Verify: build both languages, execute both locally (see `briefs/V3.md` for the command), no errors;
   the Japanese output must be unchanged apart from what V3 changes. Render a few English outputs to PNG
   with headless Chrome and look at them.
Chapter 6 is translated later, when V3 has finished it.
