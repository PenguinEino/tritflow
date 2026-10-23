# ACCEPTED stream brief: learn from every accepted Code-a-Chip notebook, then review TritFlow v3

Review only. Do not edit any TritFlow file except `docs/status/ACCEPTED.md` (your report). Clone and
work under `~/code-a-chip-accepted/` (create it). Do not commit or push anything anywhere.

## 1. Collect every accepted submission
- Clone `https://github.com/sscs-ose/sscs-ose-code-a-chip.github.io` (all years: VLSI23, ISSCC24,
  VLSI24, ISSCC25, VLSI25, ISSCC26 and any later folders; include the `submitted_notebooks` trees and the
  call/README/template files that state the rules and judging criteria).
- For every accepted notebook, also clone the external repositories it depends on or links as its
  source (shallow clones are fine). Record a table: event, title, authors' affiliation type
  (student/academic/industry), PDK, topic, notebook size (cells, code/markdown ratio, runtime class),
  what it builds, whether it reaches GDS / DRC / LVS / post-layout simulation, what the reader edits,
  and anything that stands out (figures, interactivity, tests, pinned versions, tutorial style).
- Note which notebooks received awards or special mention if the site or SSCS pages say so (search the
  web; cite URLs).

## 2. Extract what acceptance looks like
From the rules, judging criteria and the accepted set: what do accepted notebooks consistently have,
what do the strongest ones add, how long are they, how do they open (first screen), how do they
handle setup time, reproducibility, pinning, failures, and how do they present results and novelty.
Back each pattern with concrete examples (repo path + cell or file).

## 3. Review TritFlow v3 against that
TritFlow v3: `~/code-a-chip-v3`, branch `notebook-v3`. Read `notebook/v3/tritflow_en.ipynb` and
`tritflow_ja.ipynb` (with outputs: `notebook/v3/*_output.ipynb` if present, else the payload
`submission/ISSCC27/submitted_notebooks/TritFlow/`), `README.md`, `submission/templates/*`,
`docs/notebook-v3/STORYBOARD.md`. Do not run Colab; you may run small local checks.

Report what TritFlow lacks or should fix to be accepted, ranked by expected effect on acceptance.
For each finding: what is wrong or missing, the accepted-notebook evidence that it matters, the
concrete change (file/cell, a few lines), cost in hours, and risk to what already works.

## Discipline (binding)
- The author rejects overdone fixes: caveats sprinkled everywhere, extra table columns, folded or
  split tables, more boxes, restated outputs, defensive wording. Do not propose those. Prefer cuts and
  clarifications to additions. A finding without accepted-notebook evidence or a concrete acceptance
  reason does not go in the main list.
- Fixed decisions you must not reopen: structure (ch. 1–2 `a & ~a`, ch. 3–5 dot4, ch. 6 results),
  Japanese + English editions, chip delivery stated as January 2027, shuttle named "OpenSUSI-MPW's
  first shuttle", the dot4 top in the stock OSS_FRAME (just done), freeze 2026-10-25, PR on 10-30.
- At most 12 findings in the main list; anything else goes in a short "considered, not recommended"
  list with one line each.
- Write `docs/status/ACCEPTED.md` with: the table from §1 (or a link to a CSV you place next to it),
  the patterns from §2, the ranked findings from §3, and the not-recommended list.
