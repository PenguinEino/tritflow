# Brief: REVIEW stream — independent skeptical review

You own only `docs/status/REVIEW.md` and `logs/review/`. You edit no code and no notebook; you
report. Do not run git write commands.

Act as a demanding ISSCC Code-a-Chip reviewer and as a careful IC-design engineer.

1. Reproduce from scratch: clone the local repository into a temp dir (`git clone ~/code-a-chip`),
   use a fresh copy of the PDK at the commit pinned in `notebook/setup_pins.json`, install the
   package in a fresh venv, run the whole test suite and execute the notebook top to bottom
   (nbconvert / jupyter execute; install those in the venv). Record time, failures, warnings.
2. Claims audit: for every quantitative or qualitative claim in the notebook and in
   `docs/status/*.md`, find the evidence (test, assert, generated file). List claims that are
   unsupported, overstated, inconsistent between files, or hand-typed rather than generated.
3. Technical audit: look for real engineering problems — e.g. DRC/LVS decks or options used in a
   way that hides errors, measurement definitions that flatter results, extraction scope that is
   misrepresented, cells whose layout differs from what the docs say, test oracles that compare a
   circuit with itself, nondeterminism, licence/attribution gaps (PDK Apache-2.0, original design).
4. Reader audit: is the notebook clear to an expert in 20–30 minutes? Where does it drag, where is
   the key idea buried, which figures are unreadable?

Write findings to `docs/status/REVIEW.md` ranked by severity (blocker / major / minor), each with
file:line or cell index, evidence, and a concrete fix suggestion naming the owning stream
(see docs/interfaces.md). Be specific; no generic advice.
