# Brief: REWRITE_JA stream — rewrite the notebook from the top, Japanese first

You work in the git worktree `~/code-a-chip-rewrite` (branch `rewrite-ja`, forked from the released
`main` = 181206b). Never touch `~/code-a-chip` (the live release). No git commit/push/tag; the
integrator reviews and commits. Write everything reader-facing in Japanese; the English version follows
later from your Japanese, so keep structure and placeholders language-neutral.

## Why
The author received an external review: the technology is strong and has no precedent in past
Code-a-Chip submissions, but the presentation and the first screen are weak. Read the full review in
`~/rewrite-inputs/review.md` first (private input: never quote it, never quote the judge's DM, never
copy it into the repo). The author's goal is acceptance: make the notebook interesting, novel and
aligned with Code-a-Chip's founding goals (reproducibility, reuse, open silicon) and the judges' taste —
concept and purpose easy to grasp, GDS output prominent. Technical depth stays, but it serves the story.

## What to change (from the review; all mandatory)
1. **Opening = why it is interesting.** First paragraph poses the problem or contests an assumption,
   in 3–4 sentences: most ternary-logic research sits on new devices or simulation, and open tools
   convert ternary to binary for CMOS; TritFlow takes ternary HDL to DRC/LVS-clean GDS on a public,
   tape-out-able PDK, from cells that were actually taped out. A short historical hook (Setun) is
   allowed. Never claim "first"/"世界初"/"初めて" (prior work such as GT-LOGIC, IEEE Access 2025, is unchecked).
2. **Lead with "HDL→GDS, and you can rewrite it yourself"**, not with power. Remove the
   "6トリットで0.4 W" standing-power figure from the opening; present standing power in the sizing
   chapter as the ternary-specific finding (the tug-of-war that holds the middle level).
3. **Main claim = a new open ternary design flow plus a tape-out-able library; education is secondary.**
   Keep the title meaning "HDL to GDS on OpenSUSI TR-1um". Keep predict-then-SPICE, but do not brand
   the notebook as an educational simulation.
4. **GDS is the payoff:** make the routed, DRC/LVS-checked GDS (live viewer + download) visibly the
   climax early and again at the end.
5. **Silicon plan:** the chip arrives January 2027; ISSCC is 14–18 February 2027. In the opening and
   the next-steps chapter state, as a plan not a promise, that if accepted the poster will put the first
   measurements of these cells next to the notebook's predictions. Silicon is not measured yet; say so.
6. **Why NANY (−sat):** in chapter 1 add a short paragraph and a new runnable check cell (~15 lines,
   instant) that proves by closure (Słupecki's criterion) that INV/NAND/NOR plus all three constants
   reach only 11 of 27 one-input functions, NANY with TIEZ only 3/27, and NANY with TIEP/TIEN 27/27
   (functionally complete); explain why ±1 ties are needed (NANY is odd: f(−a,−b)=−f(a,b)) and that a
   half adder is five NANY + two INV (verify that count from the synthesized netlist, not by assertion).
   The integrator verified 27/3/11 independently. Wording limits: completeness is a property of the
   cell set, not of the flow (synthesis maps expressions; it does not synthesize arbitrary truth tables);
   never say a cell count is minimal.
7. **One consistent Colab record:** every place that cites a Colab run uses the same single record from
   `notebook/colab_verified.json` via placeholders (no typed numbers).
8. **Cut audit-log tone** from reader text: no internal process words, no "disclosed compatibility
   proof", no defensive hedging chains. Verification detail lives in Appendix B. The competitors sell
   carefulness ("auditable", "honestly"); TritFlow wins on its subject, so lead with the subject.
9. Reading time ≤ 25 minutes. Fewer, stronger chapters are welcome: you may merge, reorder, shorten or
   drop chapters and move material into appendices.

## How
- Reader text comes from `notebook/narrative/*.md` through `notebook/make_notebook.py` (placeholders
  like `{adder.die_um}` rendered by `notebook/editorial.py`; numbers are never typed). Create
  `notebook/narrative_ja/` with the complete Japanese narrative for your new structure, and give
  `make_notebook.py` a language option that builds `notebook/tritflow_tr1um_ja.ipynb` from it. The
  cell structure is shared by both languages; the English narrative will be rewritten to it later, so
  on this branch the English build may lag, but the Japanese build must be complete and pass.
- Code cells: keep the existing method/check cells working; restructure their order as the story needs;
  add the completeness cell (method + check, in the same style as `notebook/methods.py`/`stages.py`).
  Code comments and identifiers stay English. Japanese titles for every `#@title`.
- **Write and polish every Japanese text with the yomiyasu skill** (installed as a Codex user skill:
  `$yomiyasu:yomiyasu`, "yomiyasu で推敲"). Run it on each narrative file and on the cell titles; also run
  its lint/check scripts (`~/.codex/skills/yomiyasu/scripts/`) and fix what is real. Record the runs.
- Execute the Japanese notebook end to end locally (the setup cell handles non-Colab;
  `notebook/validate_notebook.py` style or nbclient with `TRITFLOW_ROOT` set; the integrator's last
  local JA run took ~66 s with warm caches). Zero errors required. Add/adjust tests for the new cell and
  the language option, and run `pytest notebook/tests submission tests/schematic tests/viz`.
- Heavy jobs may use the amd64 server `ssh penguin@einosuke-llm-5090` (workspace `~/tritflow-sim`;
  rsync excluding build/.git/logs; never touch anything else there, never stop/start its services).

## Deliverables
1. `notebook/narrative_ja/*.md`, the language option in `make_notebook.py`, the completeness cell,
   tests, and the built `notebook/tritflow_tr1um_ja.ipynb` (unexecuted, as generated).
2. `docs/status/REWRITE_JA.md` (Japanese): the new chapter outline with one line per chapter on its job
   in the story; for each of review points 1–9 what you changed and where; yomiyasu runs; test and
   execution results; open questions for the author.

Constraints: do not publish the author's phone number anywhere; keep the existing author block; no
sign-in or OAuth anywhere; do not touch `~/code-a-chip`.
