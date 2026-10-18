# Editorial plan for the submission notebook (integrator-owned, binding)

## Why this exists (2026-10-18 plan review)

The engineering is ahead of the story. The draft notebook reads like an audit log: the intro
talks about caches, fingerprints and release TODOs; every chapter opens with caveats; the
headline results are never stated; and there is no interactive element at all, although the
concept is "change it and watch what happens". The evaluator advice we got is the opposite:
make the purpose and concept easy to grasp, and show off that it reaches GDS.

Rule of thumb: **story and figures in the chapters, evidence and limits in the appendices.**

## Code-a-Chip fit (what the call and its reviewers reward)

| What they reward (source: call text, FAQ, founders' statements, past winners, reviewer PRs) | Where we stand | Change |
|---|---|---|
| Reuse: others can build on it | library + flow, Apache-2.0, 100 random designs route clean | say it in the intro; ch8 + shuttle-ready top make "build your own ternary circuit for the next OpenSUSI shuttle" concrete |
| Reproducibility: runs and gives the same evidence | strong locally; **real Colab Run all currently fails** | fixing Colab is the top priority; state the cold Run-all time |
| Education: theory → hand estimate → realistic model → compare (Murmann's COCOA style; Tsuchiya checks prediction vs SPICE) | **missing**: no hand analysis, no interaction | add "predict first" hand estimates in ch1, ch2, ch7 and compare with SPICE; add the interactive controls in the storyboard |
| Clear purpose/concept; "interesting" is enough (evaluator advice) | concept buried under process text | intro = pitch + context in ≤ 150 words; process notes to Appendix B |
| Reaching GDS is valued (evaluator advice) | yes, DRC-clean and LVS-matched | lead with it in ch0 and the teaser figure |
| Self-contained, few files (reviewer PR history) | 7 files, 1.85 MB, code fetched from the public repo | keep |
| Honest scope (winners state what is not done) | honest but scattered everywhere | one Appendix A |

Two things should stick in a reviewer's memory:
1. **"30 lines of ternary HDL became a DRC-clean, LVS-matched layout on Japan's open PDK, built
   from cells I already taped out — and you can change it."** (teaser figure at the top)
2. **One ternary-specific insight with numbers**: the middle level is a tug-of-war between pull-up
   and pull-down through resistors, so every gate burns ~4 mW standing still; sizing trades
   level accuracy against that current (ch2 slider), and a 6-trit adder idles at ~0.4 W, close
   to the metal current limit (ch7). Predict it by hand, confirm it in SPICE.

## Audience and voice

- Readers are IC designers (ISSCC reviewers). They know CMOS, synthesis, P&R, SPICE. They do
  not know ternary logic, TR-1um or this flow. They skim first, then run what interests them.
- Plain, confident, technical English. Short sentences. Active voice.
- Never use internal process words in reader-facing text: content-keyed, fingerprint,
  publication identity, producer, campaign, stream, integrator, TODO, cache hit.
- Total reading time for the main chapters ≤ 25 minutes.

## Chapter template

1. Title that states the point (e.g. "The middle level is a tug-of-war").
2. One short paragraph (≤ 80 words): why this step matters and what to look at.
3. One hero figure (large, labelled axes, legend; readable on light and dark Colab themes).
4. One interactive control where listed below. Prefer Plotly sliders/dropdowns over
   precomputed frames (they work on GitHub/nbviewer without a kernel); use ipywidgets only
   for live computation, and always render a static fallback.
5. Where listed, a "Predict first" step before the simulation: a hand estimate in two or three
   lines of math (e.g. resistive-divider output and static current from R and device on-resistance;
   ripple-carry delay as stages × per-stage settling), computed in code, then compared with the
   SPICE result in the figure ("hand estimate 4.0 mW, SPICE 4.17 mW").
6. A "What this shows" box: 1–3 sentences with numbers generated from data (f-strings).
7. At most one limitation sentence in the chapter; everything else goes to Appendix A.
8. Optional collapsed "Details" block (HTML `<details>`) for provenance tables.

## Storyboard

| # | Title idea | Hero figure | Interaction | Headline (generated) |
|---|---|---|---|---|
| Intro | TritFlow | flow diagram HDL → cells → GDS → SPICE | — | pitch; context below |
| 0 | From 30 lines of HDL to a DRC-clean layout | GDS of the adder + DRC/LVS badges + post-layout waveform | choose N (precomputed N=1..6, live N=2) | cells, area, DRC 0, LVS match, all vectors pass |
| 1 | Three levels from ordinary CMOS | truth tables + taped-out schematics; transfer curve with operating point | input-voltage slider: which devices conduct, output, supply current | predict-first: divider output and static current by hand vs SPICE |
| 2 | Sizing sets the middle level | transfer curve / level error / static current vs W/L | W/L (and RR length) slider over the precomputed grid; taped-out size marked | predict-first: how W/L moves the 0 level; error vs current trade-off with numbers |
| 3 | Taped-out cells become a standard-cell library | layer view + device mapping + abutted row with three rails | cell dropdown, layer toggles | area vs original, settling within x % of taped-out cells |
| 4 | Describe arithmetic in TritVerilog | HDL + exhaustive truth table | pick inputs → outputs | FA = 11 NANY + 5 INV; exhaustive check |
| 5 | Synthesis into cells | gate graph coloured by trit value | input-vector dropdown (precomputed frames) recolours nets | equivalence mode, cell counts |
| 6 | Place and route on two metals | placement animation + routed GDS | net/instance highlight dropdown; optional rows/anneal knob | die size, utilisation, wirelength, DRC/LVS |
| 7 | Does the layout still work? | pre vs post waveform with ±0.5 V bands; load-sweep; scaling | load slider (precomputed sweep, failure boundary visible); N slider on scaling | predict-first: carry delay = N × stage settling, idle power = cells × per-cell current; vs SPICE: ~49 ns/trit, ~4.2 mW/cell, load boundary; STA comparison if clean |
| 8 | Your circuit | GDS + waveform of the chosen/edited design | catalog dropdown + editable HDL cell | passes oracle, DRC, LVS, post-layout |
| 9 | Next: silicon | measurement plan; shuttle-ready top if available | — | chip from the OpenSUSI shuttle expected January 2027 |
| A | Scope and limits | consolidated list | — | — |
| B | Verification evidence and how to rerun | tables: tests, DRC/LVS, fuzz, hashes, caching, forced rerun | — | — |

## Context that belongs in the intro (facts, keep short)

- OpenSUSI TR-1um: an NDA-free 1 µm CMOS PDK from Japan (Tokai Rika process, opened 2025),
  Apache-2.0.
- The ternary cells were designed by the author and taped out on an OpenSUSI TR-1um shuttle in
  2026; the chip is expected in January 2027 (not yet measured — never say silicon-proven).
- What TritFlow adds: a standard-cell library built from those taped-out cells, a Verilog-like
  ternary HDL, synthesis, two-metal P&R, PDK DRC/LVS and post-layout ngspice, all in Colab.

## Limits to state once (Appendix A), not in every chapter

Nominal corner unless stated; wire C coefficients assumed (not calibrated PEX); no signal-wire R
or coupling; poly R is a sensitivity estimate; representative (not exhaustive) analog vectors for
larger designs; static power of resistive-divider cells; macro is not padframed/ESD-qualified
unless the shuttle-ready top is shown; no silicon measurement yet.

## Schedule (submission deadline 2026-10-31 11:59 PT = 11-01 03:59 JST)

| Date (JST) | Milestone |
|---|---|
| 10-19/20 | Pinned-PDK requalification cascade done (CELLS → PNR → SIM); Colab fixes; new `colab-v0`; real-Colab Run all passes |
| 10-21/24 | Narrative rewrite + interactive layer integrated; figure polish |
| 10-25 | **Feature freeze**: no new experiments; STA / shuttle-ready top / corners go in only if already clean |
| 10-26/28 | Real-Colab verification loops; reader-focused review; user read-through |
| 10-29 | Submission package final; user approval |
| 10-30 | User opens the PR to the official repository (one day of buffer) |

## Plan review 2026-10-19 (Code-a-Chip fit, second pass)

Content fits the call; two drifts to fix before the freeze:
1. **Code as method, not audit plumbing.** Each chapter's visible code shows the 3–12 lines of
   public TritFlow API a reader would copy (`flow.load → synthesize → schematic → place_and_route →
   drc/lvs → extract → simulate`). Guards, caching, hash checks and evidence tables live in helper
   modules and Colab `#@title` (collapsed) helper cells; verification assertions are gathered in
   Appendix B. Behaviour and checks stay the same.
2. **Reuse story.** Add (a) ch7 "Predict with static timing, confirm with SPICE" using the validated
   STA (matched transitions, ±20 %; bound is conservative but ~2× loose — say so in one line);
   (b) ch9 "From your HDL to a shuttle-ready top" using `PnrResult.to_chip()` / `signoff()` cached
   results (mask DRC 0) plus the honest remaining steps (allocation, bond map, ESD approval, shuttle
   CI); (c) Appendix C "Use and extend TritFlow" (pip install, CLI, add a cell / an operator).
Release discipline: figures are regenerated only by the release step, before hashes are captured.
