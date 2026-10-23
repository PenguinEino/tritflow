# REFS status

Last updated: 2026-10-23 (JST). **Brief complete.**

## Done

- Read `AGENTS.md`, `docs/concept.md`, `docs/interfaces.md`, and `briefs/REFS.md`.
- Created [the reference catalogue and claim audit](../references.md): **32 citation entries** covering all seven requested groups, each with authors/title/venue/year/DOI or URL, supported claim, v3 narrative insertion point, and verification limits.
- Used live web search, original papers, author/institutional sources, official project/release pages, and read-only GitHub/Crossref requests to resolve bibliographic details. No citations were invented to fill inaccessible sources.
- Located Słupecki's **1939 original scan** (article starts on printed p.102 / PDF page 110), the 1972 English translation, and Butler's open 1960 proof. Distinguished strong from weak Kleene tables using an open 2024 scholarly account.
- Checked native ternary circuit literature, ternary RTL/netlist tools, binary-encoded CMOS tools, OpenSUSI/TR-1um provenance, the public shuttle index, the author's source design, KLayout, ngspice, Knuth, and Setun.
- Recorded a comparison against MRCS, Takahe, Ankhdjet, and other close work. No verified exact counterexample to the combined **native three-voltage HDL-to-GDS flow on a fabricable open PDK** was found. Broader claims about ternary-to-masks or earlier work stopping at simulation/gates are not defensible as written.
- Independently enumerated the unary closure for the notebook's completeness argument: NANY + TIEP reaches **27** functions; NANY alone reaches **3**. This validates the project-specific premise without attributing the NANY construction to Słupecki.
- Rechecked narrative paths after the concurrent addition of `notebook/v3/narrative/06_results.md`; its “参考文献” section is now the bibliography destination.

## In progress

- None. Citation insertion and narrative changes belong to the notebook/editorial owners and were not part of the two-path REFS scope.

## Decisions

- Wrote only `docs/references.md` and this file. Did not edit other streams' files, shared interfaces, setup pins, or reference repositories.
- Kept native three-voltage logic separate from binary-encoded ternary arithmetic, and individual layouts/submissions separate from a reusable HDL-to-GDS flow.
- Treated no discovered counterexample as a bounded literature check, not proof of worldwide priority; recorded the 2026-10-23 search cutoff and inaccessible-paper limits.
- Selected three established representative CNTFET/memristor papers: Lin et al. (2011), Khalid and Singh (2016), and Wang et al. (2021). Added Wu and Prosser (1990) for simulated CMOS and Jeong et al. (2019) for fabricated CMOS; did not infer production maturity from citation counts.
- Cited the notebook's actual simulator **ngspice 42** and KLayout **0.30.6** from `notebook/setup_pins.json`. The version-42 manual's verified authors are **Holger Vogt, Giles Atkinson, Paolo Nenzi**. Kept the PDK's public release separate from the notebook's pinned development commit and the original design's older PDK reference.

## Blockers / verification limits

- No execution blocker remains. The brief explicitly allows unverifiable items to be marked; those limits are recorded rather than hidden.
- Tlsys (2026) and Hazzazi (2026): full citations verified through IEEE-deposited Crossref records, but primary full texts inaccessible. Tlsys's title identifies the gate-network endpoint. Hazzazi remains a technical-scope lead, not a confirmed counterexample.
- Other subscription/bot-blocked papers have specific access limits in the catalogue. The original Polish proof was not fully translated; the criterion was checked against Butler. Kleene's original book edition and §64 attribution were verified, with tables checked in the accessible later account.
- Former USN Open Archive links now redirect to an archive-migration notice. The catalogue supplies alternative DOI, author/university, conference, and repository references.

## Interface requests / editorial handoff

No change to `docs/interfaces.md` is requested. The notebook/editorial owners should:

1. Insert citations using the catalogue's “Use” fields and populate `notebook/v3/narrative/06_results.md`, “参考文献”. The catalogue includes optional comparison sources; it need not all be copied into the notebook.
2. Narrow the opening's novelty wording to the combined native three-voltage flow and acknowledge MRCS / close open-PDK prior art. Avoid generalizing the endpoints of particular synthesis papers to all ternary EDA.
3. Qualify BitNet's multiplication claim to ternary-weight linear products. Its activations are 8-bit; `dot4` is an educational arithmetic example.
4. Acknowledge fabricated ternary CMOS/memristor work. The selected simulation papers do not establish that most prior work is simulation-only or that no devices are mass-produced.
5. Resolve the delivery-date discrepancy: [OpenSUSI's 2026-10-16 release](https://prtimes.jp/main/html/rd/p/000000014.000182004.html) expects **February 2027**, while `00_opening.md` says January. Keep pre-ISSCC measurement conditional unless newer project-specific evidence supersedes the public estimate.
6. Use “first OpenSUSI-MPW run” instead of unsupported “Japan's first OpenMPW service.” Attribute the national commercial-fab open-PDK priority statement to the contemporary Japanese announcement.

## Validation / how to rerun

- `git diff --check -- docs/references.md docs/status/REFS.md` passes. Also check these new, unstaged files directly for trailing whitespace, since Git does not include untracked contents in a normal diff.
- Documentation structure check: 32 unique citation headings, no undefined citation keys, every entry has **Supports / Use / Verification** fields, 69 distinct well-formed external URLs, seven full source SHA identifiers, and no TODO/TBD/FIXME placeholders. Explicit narrative-path references were checked against the workspace.
- Source links were opened or checked through primary metadata/content requests. A well-formed URL is not a promise of unauthenticated access; bot blocks, subscription limits, archive migration, and large-PDF handling are recorded in the catalogue.
- No pytest area is assigned to REFS and no executable code changed, so unrelated code suites were not run.
- Reproduce the small independent completeness check with this filesystem-free command from the project directory:

```bash
python3 - <<'PY'
from itertools import product
values = (-1, 0, 1)
def nany(a, b):
    return -max(-1, min(1, a + b))
for label, functions in (
    ("NANY + TIEP", {values, (1, 1, 1)}),
    ("NANY only", {values}),
):
    counts = [len(functions)]
    while True:
        expanded = functions | {
            tuple(nany(a, b) for a, b in zip(f, g))
            for f in functions for g in functions
        }
        if expanded == functions:
            break
        functions = expanded
        counts.append(len(functions))
    print(label, counts, len(functions))
    if label == "NANY + TIEP":
        assert functions == set(product(values, repeat=3))
    else:
        assert len(functions) == 3
PY
```

- No packages installed, no subagents used, no commits or pushes. Other streams' concurrent workspace changes were left untouched.
